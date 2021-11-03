import logging
from collections import OrderedDict
from collections.abc import Iterator
import formulas  # type: ignore

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Text,
    Tuple,
    Optional
)
from typeguard import typechecked
from schedula.utils.dsp import DispatchPipe  # type: ignore

from business_rule_engine.exceptions import (
    DuplicateRuleName,
    MissingArgumentError,
    ConditionReturnValueError,
    RuleParserSyntaxError,
)


class Rule():

    @typechecked
    def __init__(self, rulename: Text, condition_requires_bool: bool = True) -> None:
        self.condition_requires_bool = condition_requires_bool
        self.rulename: Text = rulename
        self.conditions: List[Text] = []
        self.actions: List[Text] = []
        self.status: Optional[bool] = None

    @staticmethod
    @typechecked
    def _compile_condition(condition_lines: List[Text]) -> DispatchPipe:
        condition = " ".join(condition_lines)
        if not condition.startswith("="):
            condition = "={}".format(condition)
        return formulas.Parser().ast(condition)[1].compile()  # type: ignore

    @staticmethod
    @typechecked
    def _get_params(params: Dict[Text, Any], condition_compiled: DispatchPipe, set_default_arg: bool = False, default_arg: Optional[Any] = None) -> Dict[Text, Any]:
        params_dict: Dict[Text, Any] = {k.upper(): v for k, v in params.items()}
        param_names = set(params_dict.keys())

        condition_args: List[Text] = list(condition_compiled.inputs.keys())

        if not set(condition_args).issubset(param_names):
            missing_args = set(condition_args).difference(param_names)
            if not set_default_arg:
                raise MissingArgumentError("Missing arguments {}".format(missing_args))

            for missing_arg in missing_args:
                params_dict[missing_arg] = default_arg

        params_condition = {k: v for k, v in params_dict.items() if k in condition_args}
        return params_condition

    @typechecked
    def check_condition(self, params: Dict[Text, Any], *, set_default_arg: bool = False, default_arg: Any = None) -> Any:
        condition_compiled = self._compile_condition(self.conditions)
        params_condition = self._get_params(params, condition_compiled, set_default_arg, default_arg)
        rvalue_condition = condition_compiled(**params_condition).tolist()
        if self.condition_requires_bool and not isinstance(rvalue_condition, bool):
            raise ConditionReturnValueError('rule: {} - condition does not return a boolean value!'.format(self.rulename))
        self.status = bool(rvalue_condition)
        return rvalue_condition

    @typechecked
    def run_action(self, params: Dict[Text, Any], *, set_default_arg: bool = False, default_arg: Any = None) -> Any:
        action_compiled = self._compile_condition(self.actions)
        params_actions = self._get_params(params, action_compiled, set_default_arg, default_arg)
        return action_compiled(**params_actions)

    @typechecked
    def execute(self, params: Dict[Text, Any], *, set_default_arg: bool = False, default_arg: Any = None) -> Tuple[Any, Any]:
        rvalue_condition = self.check_condition(params, set_default_arg=set_default_arg, default_arg=default_arg)
        if not self.status:
            return rvalue_condition, None
        rvalue_action = self.run_action(params, set_default_arg=set_default_arg, default_arg=default_arg)
        return rvalue_condition, rvalue_action


class RuleParser():

    CUSTOM_FUNCTIONS: List[Text] = []

    @typechecked
    def __init__(self, condition_requires_bool: bool = True) -> None:
        self.rules: Dict[Text, Rule] = OrderedDict()
        self.condition_requires_bool = condition_requires_bool

    @typechecked
    def parsestr(self, text: Text) -> None:
        rulename: Optional[Text] = None
        is_condition: bool = False
        is_action: bool = False
        is_then: bool = False
        ignore_line: bool = False

        for line in text.split('\n'):
            ignore_line = False
            line = line.strip()  # The split on rule name doesn't work for multi-line w/o
            if line.lower().startswith('rule'):
                is_condition = False
                is_action = False
                rulename = line.split(' ', 1)[1].strip("\"")
                if rulename in self.rules:
                    raise DuplicateRuleName("Rule '{}' already exists!".format(rulename))
                self.rules[rulename] = Rule(rulename)
            if line.lower().strip().startswith('when'):
                ignore_line = True
                is_condition = True
                is_action = False
            if line.lower().strip().startswith('then'):
                if is_then:
                    raise RuleParserSyntaxError('using multiple "then" in one rule is not allowed')
                is_then = True
                ignore_line = True
                is_condition = False
                is_action = True
            if line.lower().strip().startswith('end'):
                ignore_line = True
                is_condition = False
                is_action = False
                is_then = False
            if rulename and is_condition and not ignore_line:
                self.rules[rulename].conditions.append(line.strip())
            if rulename and is_action and not ignore_line:
                self.rules[rulename].actions.append(line.strip())

    @typechecked
    def add_rule(self, rulename: Text, condition: Text, action: Text) -> None:
        if rulename in self.rules:
            raise DuplicateRuleName("Rule '{}' already exists!".format(rulename))
        rule = Rule(rulename)
        rule.conditions.append(condition)
        rule.actions.append(action)
        self.rules[rulename] = rule

    @classmethod
    @typechecked
    def register_function(cls, function: Callable, function_name: Optional[Text] = None) -> None:
        custom_function_name = function_name or function.__name__
        cls.CUSTOM_FUNCTIONS.append(custom_function_name.upper())
        formulas.get_functions()[custom_function_name.upper()] = function  # type: ignore

    @typechecked
    def __iter__(self) -> Iterator:
        return self.rules.values().__iter__()

    @typechecked
    def execute(
        self,
        params: Dict[Text, Any],
        stop_on_first_trigger: bool = True,
        *,
        set_default_arg: bool = False,
        default_arg: Optional[Any] = None
    ) -> bool:
        rule_was_triggered = False
        for rule in self:
            logging.debug("Rule name: %s", rule.rulename)
            logging.debug("Condition: %s", "".join(rule.conditions))
            logging.debug("Action: %s", "".join(rule.actions))

            rvalue_conditon, rvalue_action = rule.execute(params, set_default_arg=set_default_arg, default_arg=default_arg)

            if rule.status:
                rule_was_triggered = True
                if stop_on_first_trigger:
                    logging.debug("Stop on first trigger")
                    break
                logging.debug("continue with next rule")
        return rule_was_triggered
