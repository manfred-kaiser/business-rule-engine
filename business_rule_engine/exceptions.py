class RuleParserException(Exception):
    pass


class RuleParserSyntaxError(RuleParserException):
    pass


class DuplicateRuleName(RuleParserException):
    pass


class MissingArgumentError(RuleParserException):
    pass


class ConditionReturnValueError(RuleParserException):
    pass
