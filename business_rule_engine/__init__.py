__version__ = "0.3.0"

import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import formulas  # type: ignore

from business_rule_engine.exceptions import (
    DuplicateRuleName,
    MissingArgumentError,
    ConditionReturnValueError,
    RuleParserSyntaxError,
)


@dataclass
class RuleResult:
    rule_name: str
    triggered: bool
    condition_result: Any
    action_result: Any


class ExecutionResult:
    def __init__(self, results: list[RuleResult]) -> None:
        self.results = results

    def __bool__(self) -> bool:
        return any(r.triggered for r in self.results)


class Rule():

    def __init__(
        self,
        rulename: str,
        condition_requires_bool: bool = True,
        priority: int = 0,
        enabled: bool = True,
        description: str = "",
    ) -> None:
        self.condition_requires_bool = condition_requires_bool
        self.rulename: str = rulename
        self.priority: int = priority
        self.enabled: bool = enabled
        self.description: str = description
        self.conditions: list[str] = []
        self.actions: list[str] = []
        self.status: bool | None = None
        self.condition_compiled = None
        self.action_compiled = None

    @staticmethod
    def _compile_condition(condition_lines: list[str]) -> Any:
        condition = " ".join(condition_lines)
        if not condition.startswith("="):
            condition = "={}".format(condition)
        return formulas.Parser().ast(condition)[1].compile()  # type: ignore

    @staticmethod
    def _get_params(params: dict[str, Any], condition_compiled: Any, set_default_arg: bool = False, default_arg: Any = None) -> dict[str, Any]:
        params_dict: dict[str, Any] = {k.upper(): v for k, v in params.items()}
        param_names = set(params_dict.keys())

        condition_args: list[str] = list(condition_compiled.inputs.keys())

        if not set(condition_args).issubset(param_names):
            missing_args = set(condition_args).difference(param_names)
            if not set_default_arg:
                raise MissingArgumentError("Missing arguments {}".format(missing_args))

            for missing_arg in missing_args:
                params_dict[missing_arg] = default_arg

        params_condition = {k: v for k, v in params_dict.items() if k in condition_args}
        return params_condition

    def check_condition(self, params: dict[str, Any], *, set_default_arg: bool = False, default_arg: Any = None) -> Any:
        if not self.condition_compiled:
            self.condition_compiled = self._compile_condition(self.conditions)
        condition_compiled = self.condition_compiled
        params_condition = self._get_params(params, condition_compiled, set_default_arg, default_arg)
        rvalue_condition = condition_compiled(**params_condition).tolist()
        if self.condition_requires_bool and not isinstance(rvalue_condition, bool):
            raise ConditionReturnValueError('rule: {} - condition does not return a boolean value!'.format(self.rulename))
        self.status = bool(rvalue_condition)
        return rvalue_condition

    def run_action(self, params: dict[str, Any], *, set_default_arg: bool = False, default_arg: Any = None) -> Any:
        if not self.action_compiled:
            self.action_compiled = self._compile_condition(self.actions)
        action_compiled = self.action_compiled
        params_actions = self._get_params(params, action_compiled, set_default_arg, default_arg)
        return action_compiled(**params_actions)

    def execute(self, params: dict[str, Any], *, set_default_arg: bool = False, default_arg: Any = None) -> tuple[Any, Any]:
        rvalue_condition = self.check_condition(params, set_default_arg=set_default_arg, default_arg=default_arg)
        if not self.status:
            return rvalue_condition, None
        rvalue_action = self.run_action(params, set_default_arg=set_default_arg, default_arg=default_arg)
        return rvalue_condition, rvalue_action


class RuleParser():

    CUSTOM_FUNCTIONS: list[str] = []

    _RULE_PATTERN = re.compile(r'^rule\s+"([^"]+)"(?:\s+priority\s+(-?\d+))?', re.IGNORECASE)
    _DESCRIPTION_PATTERN = re.compile(r'^description\s+"([^"]*)"', re.IGNORECASE)

    def __init__(self, condition_requires_bool: bool = True) -> None:
        self.rules: dict[str, Rule] = {}
        self.condition_requires_bool = condition_requires_bool

    def parsestr(self, text: str) -> None:
        rulename: str | None = None
        is_condition: bool = False
        is_action: bool = False
        is_then: bool = False
        ignore_line: bool = False

        for line in text.split('\n'):
            ignore_line = False
            line = line.strip()

            rule_match = self._RULE_PATTERN.match(line)
            if rule_match:
                is_condition = False
                is_action = False
                is_then = False
                rulename = rule_match.group(1)
                priority = int(rule_match.group(2)) if rule_match.group(2) else 0
                if rulename in self.rules:
                    raise DuplicateRuleName("Rule '{}' already exists!".format(rulename))
                self.rules[rulename] = Rule(rulename, condition_requires_bool=self.condition_requires_bool, priority=priority)
                ignore_line = True

            desc_match = self._DESCRIPTION_PATTERN.match(line)
            if desc_match and rulename and not is_condition and not is_action:
                self.rules[rulename].description = desc_match.group(1)
                ignore_line = True

            if line.lower().startswith('when'):
                ignore_line = True
                is_condition = True
                is_action = False
            if line.lower().startswith('then'):
                if is_then:
                    raise RuleParserSyntaxError('using multiple "then" in one rule is not allowed')
                is_then = True
                ignore_line = True
                is_condition = False
                is_action = True
            if line.lower().startswith('end'):
                ignore_line = True
                is_condition = False
                is_action = False
                is_then = False
            if rulename and is_condition and not ignore_line:
                self.rules[rulename].conditions.append(line.strip())
            if rulename and is_action and not ignore_line:
                self.rules[rulename].actions.append(line.strip())

    def parsefile(self, filepath: str | Path) -> None:
        with open(filepath, encoding="utf-8") as f:
            self.parsestr(f.read())

    def add_rule(self, rulename: str, condition: str, action: str, priority: int = 0, enabled: bool = True, description: str = "") -> None:
        if rulename in self.rules:
            raise DuplicateRuleName("Rule '{}' already exists!".format(rulename))
        rule = Rule(rulename, condition_requires_bool=self.condition_requires_bool, priority=priority, enabled=enabled, description=description)
        rule.conditions.append(condition)
        rule.actions.append(action)
        self.rules[rulename] = rule

    @classmethod
    def register_function(cls, function: Any, function_name: str | None = None) -> None:
        custom_function_name = function_name or function.__name__
        if custom_function_name.upper() not in cls.CUSTOM_FUNCTIONS:
            cls.CUSTOM_FUNCTIONS.append(custom_function_name.upper())
            formulas.get_functions()[custom_function_name.upper()] = function  # type: ignore

    def __iter__(self) -> Iterator[Rule]:
        return iter(self.rules.values())

    def execute(
        self,
        params: dict[str, Any],
        stop_on_first_trigger: bool = True,
        *,
        set_default_arg: bool = False,
        default_arg: Any = None
    ) -> ExecutionResult:
        results: list[RuleResult] = []
        sorted_rules = sorted(self.rules.values(), key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            if not rule.enabled:
                continue

            logging.debug("Rule name: %s", rule.rulename)
            logging.debug("Condition: %s", "".join(rule.conditions))
            logging.debug("Action: %s", "".join(rule.actions))

            rvalue_condition, rvalue_action = rule.execute(params, set_default_arg=set_default_arg, default_arg=default_arg)

            results.append(RuleResult(
                rule_name=rule.rulename,
                triggered=bool(rule.status),
                condition_result=rvalue_condition,
                action_result=rvalue_action,
            ))

            if rule.status:
                if stop_on_first_trigger:
                    logging.debug("Stop on first trigger")
                    break
                logging.debug("continue with next rule")

        return ExecutionResult(results)
