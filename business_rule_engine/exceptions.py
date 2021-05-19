class RuleParserException(Exception):
    pass


class DuplicateRuleName(RuleParserException):
    pass


class MissingArgumentError(RuleParserException):
    pass


class ConditionReturnValueError(RuleParserException):
    pass
