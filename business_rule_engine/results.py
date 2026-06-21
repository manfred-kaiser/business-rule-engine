from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RuleResult:
    rule_name: str
    triggered: bool
    condition_result: bool
    action_result: list[object]


class ExecutionResult:
    def __init__(self, results: list[RuleResult]) -> None:
        self.results = results

    def __bool__(self) -> bool:
        return any(r.triggered for r in self.results)
