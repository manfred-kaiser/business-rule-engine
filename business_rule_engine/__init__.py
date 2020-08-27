import logging
from collections import OrderedDict
import formulas

from typing import (
    Any,
    Dict,
    List,
    Text,
    Optional
)


class RuleParser():

    CUSTOM_FUNCTIONS: List[Text] = []

    def __init__(self, codition_requires_bool: bool = True) -> None:
        self.rules: Dict[Text, Dict[Text, List[Text]]] = OrderedDict()
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
                self.rules[rulename] = {
                    'condition': [],
                    'action': []
                }
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
                self.rules[rulename]['condition'].append(line.strip())
            if rulename and is_action and not ignore_line:
                self.rules[rulename]['action'].append(line.strip())

    @classmethod
    def register_function(cls, function: Any, function_name: Optional[Text] = None) -> None:
        cls.CUSTOM_FUNCTIONS.append(function_name or function.__name__.upper())
        formulas.get_functions()[function_name or function.__name__.upper()] = function  # type: ignore

    @staticmethod
    def _compile_condition(condition_lines: List[Text]) -> Any:
        condition = "".join(condition_lines)
        if not condition.startswith("="):
            condition = "={}".format(condition)
        return formulas.Parser().ast(condition)[1].compile()  # type: ignore

    @staticmethod
    def _get_params(params: Dict[Text, Any], condition_compiled: Any) -> Dict[Text, Any]:
        params_dict: Dict[Text, Any] = {k.upper(): v for k, v in params.items()}
        param_names = set(params_dict.keys())

        condition_args: List[Text] = list(condition_compiled.inputs.keys())

        if not set(condition_args).issubset(param_names):
            raise ValueError("Missing arguments")

        params_condition = {k: v for k, v in params_dict.items() if k in condition_args}
        return params_condition

    def execute(self, params: Dict[Text, Any], stop_on_first_trigger: bool = True) -> bool:
        rule_was_triggered = False
        for rule_name, rule in self.rules.items():
            logging.debug("Rule name: %s", rule_name)
            logging.debug("Condition: %s", "".join(rule['condition']))
            logging.debug("Action: {}", "".join(rule['action']))

            condition_compiled = self._compile_condition(rule['condition'])
            params_condition = self._get_params(params, condition_compiled)
            rvalue_conditions = condition_compiled(**params_condition).tolist()
            if self.codition_requires_bool and not isinstance(rvalue_conditions, bool):
                raise ValueError('rule: {} - condition does not return a boolean value!'.format(rule_name))

            if rvalue_conditions:
                rule_was_triggered = True

                action_compiled = self._compile_condition(rule['action'])
                params_actions = self._get_params(params, action_compiled)
                rvalue_action = action_compiled(**params_actions)
                logging.debug("rule '%s' executed with result %s", rule_name, rvalue_action)

                if stop_on_first_trigger:
                    logging.debug("Stop on first trigger")
                    break
                logging.debug("continue with next rule")
        return rule_was_triggered
