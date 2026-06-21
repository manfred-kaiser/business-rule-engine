"""Exception hierarchy for the business rule engine."""


class RuleParserError(Exception):
    """Base exception raised by all rule parser errors."""


class RuleParserSyntaxError(RuleParserError):
    """Raised when a rule definition violates the rule DSL syntax."""


class DuplicateThenError(RuleParserSyntaxError):
    """Raised when a rule block contains more than one ``then`` section."""

    def __init__(self) -> None:
        """Initialize with a fixed error message."""
        super().__init__('using multiple "then" in one rule is not allowed')


class DuplicateRuleNameError(RuleParserError):
    """Raised when a rule with the given name has already been registered."""

    def __init__(self, rulename: str) -> None:
        """Initialize the exception.

        :param rulename: Name of the rule that already exists.
        """
        super().__init__(f"Rule '{rulename}' already exists!")


class MissingArgumentError(RuleParserError):
    """Raised when a rule expression references a parameter that was not provided."""


class ConditionReturnValueError(RuleParserError):
    """Raised when a condition expression does not evaluate to a boolean."""

    def __init__(self, rulename: str) -> None:
        """Initialize the exception.

        :param rulename: Name of the rule whose condition returned a non-boolean.
        """
        super().__init__(f"rule: {rulename} - condition does not return a boolean value!")
