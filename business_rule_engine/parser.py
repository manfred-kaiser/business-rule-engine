"""Parser for the business rule DSL."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from business_rule_engine.exceptions import (
    DuplicateRuleNameError,
    DuplicateThenError,
)
from business_rule_engine.results import ExecutionResult, RuleResult
from business_rule_engine.rule import Rule

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

logger = logging.getLogger(__name__)


class RuleParser:
    """Parse and execute a collection of business rules.

    Rules are loaded from the DSL text format or added programmatically via
    :meth:`add_rule`.  On execution, enabled rules are evaluated in descending
    priority order.

    Example DSL::

        rule "reorder"
        when
            stock < 10
        then
            order(50)
        end
    """

    CUSTOM_FUNCTIONS: ClassVar[dict[str, Callable[..., object]]] = {}
    """Callables registered via :meth:`register_function` and shared across all instances."""

    _RULE_PATTERN = re.compile(r'^rule\s+"([^"]+)"(?:\s+priority\s+(-?\d+))?', re.IGNORECASE)
    _DESCRIPTION_PATTERN = re.compile(r'^description\s+"([^"]*)"', re.IGNORECASE)
    _PRIORITY_PATTERN = re.compile(r"^priority\s+(-?\d+)$", re.IGNORECASE)

    def __init__(self, *, condition_requires_bool: bool = True) -> None:
        """Initialize the rule parser.

        :param condition_requires_bool: Require all rule conditions to return a boolean value.
        """
        self.rules: dict[str, Rule] = {}
        self.condition_requires_bool = condition_requires_bool

    def _make_rule(self, rulename: str, priority: int = 0) -> Rule:
        return Rule(
            rulename,
            condition_requires_bool=self.condition_requires_bool,
            priority=priority,
            functions=RuleParser.CUSTOM_FUNCTIONS,
        )

    def _parse_rule_header(self, line: str) -> tuple[str, int] | None:
        rule_match = self._RULE_PATTERN.match(line)
        if not rule_match:
            return None
        rulename = rule_match.group(1)
        priority = int(rule_match.group(2)) if rule_match.group(2) else 0
        if rulename in self.rules:
            raise DuplicateRuleNameError(rulename)
        return rulename, priority

    def _parse_metadata_line(self, line: str, rulename: str) -> bool:
        desc_match = self._DESCRIPTION_PATTERN.match(line)
        if desc_match:
            self.rules[rulename].description = desc_match.group(1)
            return True
        prio_match = self._PRIORITY_PATTERN.match(line)
        if prio_match:
            self.rules[rulename].priority = int(prio_match.group(1))
            return True
        return False

    def _handle_keyword(self, line: str, *, is_then: bool) -> tuple[bool, bool, bool] | None:
        ll = line.lower()
        if ll.startswith("when"):
            return True, False, is_then
        if ll.startswith("then"):
            if is_then:
                raise DuplicateThenError
            return False, True, True
        if ll.startswith("end"):
            return False, False, False
        return None

    def parsestr(self, text: str) -> None:
        """Parse rules from a DSL string and add them to the parser.

        :param text: DSL text containing one or more rule definitions.
        :raises DuplicateRuleNameError: If a rule name appears more than once.
        :raises DuplicateThenError: If a rule block contains more than one ``then`` section.
        """
        rulename: str | None = None
        is_condition: bool = False
        is_action: bool = False
        is_then: bool = False

        for raw_line in text.split("\n"):
            line = raw_line.strip()
            if not line:
                continue

            header = self._parse_rule_header(line)
            if header is not None:
                rulename, priority = header
                self.rules[rulename] = self._make_rule(rulename, priority)
                is_condition = is_action = is_then = False
                continue

            if rulename and not is_condition and not is_action and self._parse_metadata_line(line, rulename):
                continue

            keyword_state = self._handle_keyword(line, is_then=is_then)
            if keyword_state is not None:
                is_condition, is_action, is_then = keyword_state
                continue

            if rulename and is_condition:
                self.rules[rulename].conditions.append(line)
            elif rulename and is_action:
                self.rules[rulename].actions.append(line)

    def parsefile(self, filepath: str | Path) -> None:
        """Parse rules from a DSL file and add them to the parser.

        :param filepath: Path to the file containing rule definitions.
        :raises DuplicateRuleNameError: If a rule name appears more than once.
        :raises DuplicateThenError: If a rule block contains more than one ``then`` section.
        """
        with Path(filepath).open(encoding="utf-8") as f:
            self.parsestr(f.read())

    def add_rule(
        self,
        rulename: str,
        condition: str,
        action: str,
        *,
        priority: int = 0,
        enabled: bool = True,
        description: str = "",
    ) -> None:
        """Register a rule programmatically without parsing DSL text.

        :param rulename: Unique name for the rule.
        :param condition: Expression evaluated as the rule condition.
        :param action: Expression executed when the condition is satisfied.
        :param priority: Execution priority; higher values run first.
        :param enabled: Whether the rule participates in execution.
        :param description: Human-readable description of the rule.
        :raises DuplicateRuleNameError: If *rulename* is already registered.
        """
        if rulename in self.rules:
            raise DuplicateRuleNameError(rulename)
        rule = self._make_rule(rulename, priority)
        rule.enabled = enabled
        rule.description = description
        rule.conditions.append(condition)
        rule.actions.append(action)
        self.rules[rulename] = rule

    @classmethod
    def register_function(cls, function: Callable[..., object], function_name: str | None = None) -> None:
        """Register a callable for use inside rule expressions.

        :param function: Callable to make available in expressions.
        :param function_name: Name to use inside expressions; defaults to ``function.__name__``.
        """
        name = function_name or function.__name__
        cls.CUSTOM_FUNCTIONS[name] = function

    @classmethod
    def unregister_function(cls, function_name: str) -> None:
        """Remove a previously registered callable from rule expressions.

        :param function_name: Name under which the function was registered.
        :raises KeyError: If no function with *function_name* is registered.
        """
        del cls.CUSTOM_FUNCTIONS[function_name]

    @classmethod
    def clear_functions(cls) -> None:
        """Remove all registered custom functions."""
        cls.CUSTOM_FUNCTIONS.clear()

    def remove_rule(self, rulename: str) -> None:
        """Remove a registered rule by name.

        :param rulename: Name of the rule to remove.
        :raises KeyError: If no rule with *rulename* is registered.
        """
        del self.rules[rulename]

    def clear_rules(self) -> None:
        """Remove all registered rules from this parser instance."""
        self.rules.clear()

    def __len__(self) -> int:
        """Return the number of registered rules."""
        return len(self.rules)

    def __contains__(self, rulename: object) -> bool:
        """Return ``True`` if a rule with the given name is registered."""
        return rulename in self.rules

    def __iter__(self) -> Iterator[Rule]:
        """Iterate over registered rules in insertion order."""
        return iter(self.rules.values())

    def execute(
        self,
        params: Mapping[str, object],
        *,
        stop_on_first_trigger: bool = True,
        set_default_arg: bool = False,
        default_arg: object = None,
    ) -> ExecutionResult:
        """Evaluate all enabled rules against the given parameters.

        Rules are sorted by descending priority before evaluation.

        :param params: Named values available to all rule expressions.
        :param stop_on_first_trigger: Stop after the first rule whose condition is satisfied.
        :param set_default_arg: Substitute *default_arg* for missing keys instead of raising.
        :param default_arg: Value used for missing keys when *set_default_arg* is ``True``.
        :returns: :class:`~business_rule_engine.ExecutionResult` containing per-rule results.
            Evaluates as ``True`` when at least one rule was triggered.
        :raises MissingArgumentError: If a referenced name is absent and *set_default_arg* is ``False``.
        :raises ConditionReturnValueError: If a condition does not return a boolean value.
        """
        results: list[RuleResult] = []
        sorted_rules = sorted(self.rules.values(), key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            if not rule.enabled:
                continue

            logger.debug("Rule name: %s", rule.rulename)
            logger.debug("Conditions: %s", rule.conditions)
            logger.debug("Actions: %s", rule.actions)

            condition_result, action_results = rule.execute(
                params,
                set_default_arg=set_default_arg,
                default_arg=default_arg,
            )

            results.append(RuleResult(
                rule_name=rule.rulename,
                triggered=bool(rule.status),
                condition_result=condition_result,
                action_result=action_results,
            ))

            if rule.status:
                if stop_on_first_trigger:
                    logger.debug("Stop on first trigger")
                    break
                logger.debug("continue with next rule")

        return ExecutionResult(results)
