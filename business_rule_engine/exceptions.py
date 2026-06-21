class RuleParserError(Exception):
    pass


class RuleParserSyntaxError(RuleParserError):
    pass


class DuplicateThenError(RuleParserSyntaxError):
    def __init__(self) -> None:
        super().__init__('using multiple "then" in one rule is not allowed')


class DuplicateRuleNameError(RuleParserError):
    def __init__(self, rulename: str) -> None:
        super().__init__(f"Rule '{rulename}' already exists!")


class MissingArgumentError(RuleParserError):
    pass


class ConditionReturnValueError(RuleParserError):
    def __init__(self, rulename: str) -> None:
        super().__init__(f"rule: {rulename} - condition does not return a boolean value!")
