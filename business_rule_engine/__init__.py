"""Business rule engine — evaluate named rules against runtime parameters."""

__version__ = "1.0.0"

from business_rule_engine.exceptions import (
    ConditionReturnValueError,
    DuplicateRuleNameError,
    DuplicateThenError,
    MissingArgumentError,
    RuleParserError,
    RuleParserSyntaxError,
)
from business_rule_engine.parser import RuleParser
from business_rule_engine.results import ExecutionResult, RuleResult
from business_rule_engine.rule import Rule

__all__ = [
    "ConditionReturnValueError",
    "DuplicateRuleNameError",
    "DuplicateThenError",
    "ExecutionResult",
    "MissingArgumentError",
    "Rule",
    "RuleParser",
    "RuleParserError",
    "RuleParserSyntaxError",
    "RuleResult",
]
