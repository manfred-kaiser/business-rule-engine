import logging
from collections import OrderedDict
import formulas

from typing import (
    Any,
    Dict,
    List,
    Text,
    Tuple,
    Optional
)

from business_rule_engine.exceptions import DuplicateRuleName


class Rule():

    def __init__(self, rulename, codition_requires_bool: bool = True) -> None:
        self.codition_requires_bool = codition_requires_bool
        self.rulename: Text = rulename
        self.conditions: List[Text] = []
        self.actions: List[Text] = []
        self.status = None

    @staticmethod
    def _compile_condition(condition_lines: List[Text]) -> Any:
        condition = "".join(condition_lines)
        if not condition.startswith("="):
            condition = "={}".format(condition)
        return formulas.Parser().ast(condition)[1].compile()  # type: ignore

    @staticmethod
    def _get_params(params: Dict[Text, Any], condition_compiled: Any, set_default_arg: bool = False, default_arg: Optional[Any] = None) -> Dict[Text, Any]:
        params_dict: Dict[Text, Any] = {k.upper(): v for k, v in params.items()}
        param_names = set(params_dict.keys())

        condition_args: List[Text] = list(condition_compiled.inputs.keys())

        if not set(condition_args).issubset(param_names):
            missing_args = set(condition_args).difference(param_names)
            if not set_default_arg:
                raise ValueError("Missing arguments {}".format(missing_args))

            for missing_arg in missing_args:
                params_dict[missing_arg] = default_arg

        params_condition = {k: v for k, v in params_dict.items() if k in condition_args}
        return params_condition

    def check_condition(self, params, *, set_default_arg=False, default_arg=None):
        condition_compiled = self._compile_condition(self.conditions)
        params_condition = self._get_params(params, condition_compiled, set_default_arg, default_arg)
        rvalue_condition = condition_compiled(**params_condition).tolist()
        if self.codition_requires_bool and not isinstance(rvalue_condition, bool):
            raise ValueError('rule: {} - condition does not return a boolean value!'.format(self.rulename))
        self.status = bool(rvalue_condition)
        return rvalue_condition

    def run_action(self, params, *, set_default_arg=False, default_arg=None):
        action_compiled = self._compile_condition(self.actions)
        params_actions = self._get_params(params, action_compiled, set_default_arg, default_arg)
        return action_compiled(**params_actions)

    def execute(self, params, *, set_default_arg=False, default_arg=None) -> Tuple[bool, Any]:
        rvalue_condition = self.check_condition(params, set_default_arg=set_default_arg, default_arg=default_arg)
        if not self.status:
            return rvalue_condition, None
        rvalue_action = self.run_action(params, set_default_arg=set_default_arg, default_arg=default_arg)
        return rvalue_condition, rvalue_action


class RuleParser():

    CUSTOM_FUNCTIONS: List[Text] = []

    def __init__(self, codition_requires_bool: bool = True) -> None:
        self.rules: Dict[Text, Rule] = OrderedDict()
        self.codition_requires_bool = codition_requires_bool

    def parsestr(self, text: Text) -> None:
        rulename = None
        is_condition = False
        is_action = False
        ignore_line = False

        for line in text.split('\n'):
            ignore_line = False
            if line.lower().strip().startswith('rule'):
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
                ignore_line = True
                is_condition = False
                is_action = True
            if line.lower().strip().startswith('end'):
                ignore_line = True
                is_condition = False
                is_action = False
            if rulename and is_condition and not ignore_line:
                self.rules[rulename].conditions.append(line.strip())
            if rulename and is_action and not ignore_line:
                self.rules[rulename].actions.append(line.strip())

    @classmethod
    def register_function(cls, function: Any, function_name: Optional[Text] = None) -> None:
        cls.CUSTOM_FUNCTIONS.append(function_name or function.__name__.upper())
        formulas.get_functions()[function_name or function.__name__.upper()] = function  # type: ignore

    def __iter__(self):
        return self.rules.values().__iter__()

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
