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
        super().__init__(data)
        self._default = default

    def __missing__(self, key: str) -> object:
        return self._default


class Rule:
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
        condition_result = self.check_condition(params, set_default_arg=set_default_arg, default_arg=default_arg)
        if not self.status:
            return condition_result, []
        action_results = self.run_action(params, set_default_arg=set_default_arg, default_arg=default_arg)
        return condition_result, action_results
