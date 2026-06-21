"""Data containers for rule execution results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RuleResult:
    """Result of evaluating a single rule.

    :param rule_name: Name of the evaluated rule.
    :param triggered: Whether the rule condition was satisfied.
    :param condition_result: Boolean result of the condition expression.
    :param action_result: Return values from each executed action, in order.
    """

    rule_name: str
    triggered: bool
    condition_result: bool
    action_result: list[object]


class ExecutionResult:
    """Aggregated result of running a rule set via :class:`~business_rule_engine.RuleParser`.

    Evaluates as ``True`` in a boolean context when at least one rule was triggered.
    """

    def __init__(self, results: list[RuleResult]) -> None:
        """Initialize the execution result.

        :param results: Per-rule results in evaluation order.
        """
        self.results = results

    def __bool__(self) -> bool:
        """Return ``True`` if at least one rule was triggered."""
        return any(r.triggered for r in self.results)
