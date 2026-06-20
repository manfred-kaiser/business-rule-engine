__version__ = "1.0.0"

import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from simpleeval import EvalWithCompoundTypes, NameNotDefined

from business_rule_engine.exceptions import (
    DuplicateRuleName,
    MissingArgumentError,
    ConditionReturnValueError,
    RuleParserSyntaxError,
)


class _DefaultNames(dict):
    """Returns a default value for any missing key (used for set_default_arg)."""

    def __init__(self, data: dict[str, Any], default: Any) -> None:
        super().__init__(data)
        self._default = default

    def __missing__(self, key: str) -> Any:
        return self._default


@dataclass
class RuleResult:
    rule_name: str
    triggered: bool
    condition_result: bool
    action_result: list[Any]


class ExecutionResult:
    def __init__(self, results: list[RuleResult]) -> None:
        self.results = results

    def __bool__(self) -> bool:
        return any(r.triggered for r in self.results)


class Rule:

    def __init__(
        self,
        rulename: str,
        condition_requires_bool: bool = True,
        priority: int = 0,
        enabled: bool = True,
        description: str = "",
        functions: dict[str, Any] | None = None,
    ) -> None:
        self.rulename = rulename
        self.condition_requires_bool = condition_requires_bool
        self.priority = priority
        self.enabled = enabled
        self.description = description
        self.conditions: list[str] = []
        self.actions: list[str] = []
        self.status: bool | None = None
        self._functions: dict[str, Any] = functions if functions is not None else {}

    def _build_names(self, params: dict[str, Any], set_default_arg: bool, default_arg: Any) -> dict[str, Any]:
        if set_default_arg:
            return _DefaultNames(params, default_arg)
        return dict(params)

    def _evaluate(self, expression: str, names: dict[str, Any]) -> Any:
        return EvalWithCompoundTypes(names=names, functions=self._functions).eval(expression)

    def check_condition(self, params: dict[str, Any], *, set_default_arg: bool = False, default_arg: Any = None) -> bool:
        names = self._build_names(params, set_default_arg, default_arg)
        condition = " ".join(self.conditions)
        try:
            result = self._evaluate(condition, names)
        except NameNotDefined as e:
            raise MissingArgumentError(str(e)) from e
        if self.condition_requires_bool and not isinstance(result, bool):
            raise ConditionReturnValueError(
                f"rule: {self.rulename} - condition does not return a boolean value!"
            )
        self.status = bool(result)
        return self.status

    def run_action(self, params: dict[str, Any], *, set_default_arg: bool = False, default_arg: Any = None) -> list[Any]:
        names = self._build_names(params, set_default_arg, default_arg)
        results = []
        for action in self.actions:
            try:
                result = self._evaluate(action, names)
            except NameNotDefined as e:
                raise MissingArgumentError(str(e)) from e
            results.append(result)
        return results

    def execute(self, params: dict[str, Any], *, set_default_arg: bool = False, default_arg: Any = None) -> tuple[bool, list[Any]]:
        condition_result = self.check_condition(params, set_default_arg=set_default_arg, default_arg=default_arg)
        if not self.status:
            return condition_result, []
        action_results = self.run_action(params, set_default_arg=set_default_arg, default_arg=default_arg)
        return condition_result, action_results


class RuleParser:

    CUSTOM_FUNCTIONS: dict[str, Any] = {}

    _RULE_PATTERN = re.compile(r'^rule\s+"([^"]+)"(?:\s+priority\s+(-?\d+))?', re.IGNORECASE)
    _DESCRIPTION_PATTERN = re.compile(r'^description\s+"([^"]*)"', re.IGNORECASE)
    _PRIORITY_PATTERN = re.compile(r'^priority\s+(-?\d+)$', re.IGNORECASE)

    def __init__(self, condition_requires_bool: bool = True) -> None:
        self.rules: dict[str, Rule] = {}
        self.condition_requires_bool = condition_requires_bool

    def _make_rule(self, rulename: str, priority: int = 0) -> Rule:
        return Rule(
            rulename,
            condition_requires_bool=self.condition_requires_bool,
            priority=priority,
            functions=RuleParser.CUSTOM_FUNCTIONS,
        )

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
                    raise DuplicateRuleName(f"Rule '{rulename}' already exists!")
                self.rules[rulename] = self._make_rule(rulename, priority)
                ignore_line = True

            if rulename and not is_condition and not is_action and not rule_match:
                desc_match = self._DESCRIPTION_PATTERN.match(line)
                if desc_match:
                    self.rules[rulename].description = desc_match.group(1)
                    ignore_line = True

                prio_match = self._PRIORITY_PATTERN.match(line)
                if prio_match:
                    self.rules[rulename].priority = int(prio_match.group(1))
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
            if rulename and is_condition and not ignore_line and line:
                self.rules[rulename].conditions.append(line)
            if rulename and is_action and not ignore_line and line:
                self.rules[rulename].actions.append(line)

    def parsefile(self, filepath: str | Path) -> None:
        with open(filepath, encoding="utf-8") as f:
            self.parsestr(f.read())

    def add_rule(
        self,
        rulename: str,
        condition: str,
        action: str,
        priority: int = 0,
        enabled: bool = True,
        description: str = "",
    ) -> None:
        if rulename in self.rules:
            raise DuplicateRuleName(f"Rule '{rulename}' already exists!")
        rule = self._make_rule(rulename, priority)
        rule.enabled = enabled
        rule.description = description
        rule.conditions.append(condition)
        rule.actions.append(action)
        self.rules[rulename] = rule

    @classmethod
    def register_function(cls, function: Any, function_name: str | None = None) -> None:
        name = function_name or function.__name__
        cls.CUSTOM_FUNCTIONS[name] = function

    def __iter__(self) -> Iterator[Rule]:
        return iter(self.rules.values())

    def execute(
        self,
        params: dict[str, Any],
        stop_on_first_trigger: bool = True,
        *,
        set_default_arg: bool = False,
        default_arg: Any = None,
    ) -> ExecutionResult:
        results: list[RuleResult] = []
        sorted_rules = sorted(self.rules.values(), key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            if not rule.enabled:
                continue

            logging.debug("Rule name: %s", rule.rulename)
            logging.debug("Conditions: %s", rule.conditions)
            logging.debug("Actions: %s", rule.actions)

            condition_result, action_results = rule.execute(
                params,
                set_default_arg=set_default_arg,
                default_arg=default_arg,
            )

            results.append(RuleResult(
                rule_name=rule.rulename,
                triggered=bool(rule.status),
                condition_result=condition_result,
                action_result=action_results,
            ))

            if rule.status:
                if stop_on_first_trigger:
                    logging.debug("Stop on first trigger")
                    break
                logging.debug("continue with next rule")

        return ExecutionResult(results)
