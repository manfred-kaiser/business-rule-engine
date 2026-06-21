"""Single rule: condition evaluation and action execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from simpleeval import EvalWithCompoundTypes, NameNotDefined

from business_rule_engine.exceptions import (
    ConditionReturnValueError,
    MissingArgumentError,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


class _DefaultNames(dict[str, object]):
    def __init__(self, data: dict[str, object], default: object) -> None:
        """Initialize with data and a fallback value for missing keys."""
        super().__init__(data)
        self._default = default

    def __missing__(self, key: str) -> object:
        """Return the default value for any missing key."""
        return self._default


class Rule:
    """Represent a single named business rule with a condition and one or more actions.

    A rule is satisfied when its condition expression evaluates to ``True``.
    When satisfied, all registered action expressions are executed in order.
    """

    def __init__(
        self,
        rulename: str,
        *,
        condition_requires_bool: bool = True,
        priority: int = 0,
        enabled: bool = True,
        description: str = "",
        functions: dict[str, Callable[..., object]] | None = None,
    ) -> None:
        """Initialize a rule.

        :param rulename: Unique name identifying the rule.
        :param condition_requires_bool: Raise :exc:`~business_rule_engine.ConditionReturnValueError`
            when the condition does not return a boolean value.
        :param priority: Execution priority; higher values are evaluated first.
        :param enabled: Whether this rule participates in execution.
        :param description: Human-readable description of the rule.
        :param functions: Mapping of callables available inside rule expressions.
        """
        self.rulename = rulename
        self.condition_requires_bool = condition_requires_bool
        self.priority = priority
        self.enabled = enabled
        self.description = description
        self.conditions: list[str] = []
        self.actions: list[str] = []
        self.status: bool | None = None
        self._functions: dict[str, Callable[..., object]] = functions if functions is not None else {}

    def _build_names(self, params: Mapping[str, object], *, set_default_arg: bool, default_arg: object) -> dict[str, object]:
        if set_default_arg:
            return _DefaultNames(dict(params), default_arg)
        return dict(params)

    def _evaluate(self, expression: str, names: dict[str, object]) -> object:
        return EvalWithCompoundTypes(names=names, functions=self._functions).eval(expression)

    def check_condition(
        self,
        params: Mapping[str, object],
        *,
        set_default_arg: bool = False,
        default_arg: object = None,
    ) -> bool:
        """Evaluate the rule condition against the provided parameters.

        :param params: Named values available to the condition expression.
        :param set_default_arg: Substitute *default_arg* for missing keys instead of raising.
        :param default_arg: Value used for missing keys when *set_default_arg* is ``True``.
        :returns: ``True`` if the condition is satisfied.
        :raises MissingArgumentError: If a referenced name is absent and *set_default_arg* is ``False``.
        :raises ConditionReturnValueError: If the condition does not return a boolean value.
        """
        names = self._build_names(params, set_default_arg=set_default_arg, default_arg=default_arg)
        condition = " ".join(self.conditions)
        try:
            result = self._evaluate(condition, names)
        except NameNotDefined as e:
            raise MissingArgumentError(str(e)) from e
        if self.condition_requires_bool and not isinstance(result, bool):
            raise ConditionReturnValueError(self.rulename)
        self.status = bool(result)
        return self.status

    def run_action(
        self,
        params: Mapping[str, object],
        *,
        set_default_arg: bool = False,
        default_arg: object = None,
    ) -> list[object]:
        """Execute all registered action expressions and return their results.

        :param params: Named values available to each action expression.
        :param set_default_arg: Substitute *default_arg* for missing keys instead of raising.
        :param default_arg: Value used for missing keys when *set_default_arg* is ``True``.
        :returns: List of return values, one per action expression, in order.
        :raises MissingArgumentError: If a referenced name is absent and *set_default_arg* is ``False``.
        """
        names = self._build_names(params, set_default_arg=set_default_arg, default_arg=default_arg)
        results: list[object] = []
        for action in self.actions:
            try:
                result = self._evaluate(action, names)
            except NameNotDefined as e:
                raise MissingArgumentError(str(e)) from e
            results.append(result)
        return results

    def execute(
        self,
        params: Mapping[str, object],
        *,
        set_default_arg: bool = False,
        default_arg: object = None,
    ) -> tuple[bool, list[object]]:
        """Evaluate the condition and, if satisfied, execute all actions.

        :param params: Named values available to condition and action expressions.
        :param set_default_arg: Substitute *default_arg* for missing keys instead of raising.
        :param default_arg: Value used for missing keys when *set_default_arg* is ``True``.
        :returns: A tuple of ``(condition_result, action_results)``.
            The action list is empty when the condition is not satisfied.
        :raises MissingArgumentError: If a referenced name is absent and *set_default_arg* is ``False``.
        :raises ConditionReturnValueError: If the condition does not return a boolean value.
        """
        condition_result = self.check_condition(params, set_default_arg=set_default_arg, default_arg=default_arg)
        if not self.status:
            return condition_result, []
        action_results = self.run_action(params, set_default_arg=set_default_arg, default_arg=default_arg)
        return condition_result, action_results
