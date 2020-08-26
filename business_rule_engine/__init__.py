from collections import OrderedDict
import formulas


class RuleParser():

    CUSTOM_FUNCTIONS = {}

    def __init__(self) -> None:
        self.rules = OrderedDict()

    def parsestr(self, text):
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
    def register_function(cls, function, function_name=None):
        if not function_name:
            function_name = function.__name__.upper()
        cls.CUSTOM_FUNCTIONS[function_name] = function
        formulas.get_functions()[function_name] = function

    @staticmethod
    def _compile_condition(condition_lines):
        condition = "".join(condition_lines)
        if not condition.startswith("="):
            condition = "={}".format(condition)
        return formulas.Parser().ast(condition)[1].compile()

    @staticmethod
    def get_params(params, condition_compiled):
        params_dict = {k.upper(): v for k, v in params.items()}
        param_names = set(params_dict.keys())

        condition_args = list(condition_compiled.inputs.keys())

        if not set(condition_args).issubset(param_names):
            raise ValueError("Missing arguments")

        params_condition = {k: v for k,v in params_dict.items() if k in condition_args}
        return params_condition

    def execute(self, params, stop_on_first_trigger=True):
        rule_was_triggered = False
        for rule_name, rule in self.rules.items():
            print("Rule name: {}".format(rule_name))
            print("Condition: {}".format("".join(rule['condition'])))
            print("Action: {}".format("".join(rule['action'])))

            condition_compiled = self._compile_condition(rule['condition'])
            params_condition = self.get_params(params, condition_compiled)
            rvalue_conditions = condition_compiled(**params_condition)

            if rvalue_conditions:
                rule_was_triggered = True

                action_compiled = self._compile_condition(rule['action'])
                params_actions = self.get_params(params, action_compiled)
                rvalue_action = action_compiled(**params_actions)
                print("rule '{}' executed with result {}".format(rule_name, rvalue_action))

                if stop_on_first_trigger:
                    print("Stop on first trigger")
                    break
                print("continue")
        return rule_was_triggered
