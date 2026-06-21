# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Added

- `RuleParser.__len__()`: `len(parser)` returns the number of registered rules
- `RuleParser.__contains__()`: `"name" in parser` checks whether a rule is registered


## [1.0.0] - 2026-06-21

### Breaking Changes

- Replaced `formulas` with `simpleeval`: rule expressions now use Python syntax (`and`/`or`/`not`/`==`) instead of Excel syntax (`AND()`/`OR()`/`=`)
- Multiple `when` lines are concatenated into a single Python expression — logical operators (`and`/`or`) must be written explicitly
- Multiple `then` lines are now executed sequentially — `action_result` in `RuleResult` is `list[object]` instead of a single value
- `Rule.execute()` now returns `tuple[bool, list[object]]` instead of `tuple[Any, Any]`
- `RuleParser.CUSTOM_FUNCTIONS` is now a class-level `dict[str, Callable]` (name → callable) instead of a `list[str]`
- Exception renames: `RuleParserException` → `RuleParserError`, `DuplicateRuleName` → `DuplicateRuleNameError`
- All boolean and optional parameters are now keyword-only (e.g. `parser.execute(params, stop_on_first_trigger=False)`)
- Package restructured into separate modules (`exceptions`, `results`, `rule`, `parser`) — top-level imports via `business_rule_engine` still work
- Minimum Python version raised to 3.11

### Added

- New exception `DuplicateThenError` (subclass of `RuleParserSyntaxError`) when a rule block contains more than one `then` section
- `RuleResult` dataclass with fields `rule_name`, `triggered`, `condition_result`, `action_result`
- `ExecutionResult` class with `.results` list and `bool` coercion (True if at least one rule triggered)
- `Rule.description` and `Rule.enabled` attributes for runtime rule control
- `py.typed` marker file for PEP 561 compliance
- License changed from GPL v3 to MIT
- PyPI publishing via Trusted Publisher (OIDC) — no more token secrets required

### Changed

- Migrated build system from `setup.py` to `pyproject.toml` with hatchling
- CI matrix now covers Python 3.11, 3.12, 3.13
- Replaced deprecated `typing.Dict`, `List`, `Text`, `Tuple`, `Optional` with built-in generics and `X | None`
- Replaced `OrderedDict` with plain `dict` (ordered since Python 3.7)

### Fixed

- Parser bug: `is_then` was not reset when a new `rule` block started, causing a spurious `RuleParserSyntaxError` if a preceding rule was missing its `end` keyword
- `register_function` no longer registers the same function multiple times when called repeatedly across instances


## [0.2.0] - 2021-11-02

### Added

- added add_rule method to RuleParser


## [0.1.3] - 2021-06-15

### Fixed

- fixed optional function name for custom function
- added some syntax checks


## [0.1.2] - 2021-05-23

### Fixed

- Fix typo in variable  condition_requires_bool
- Fix parsing rule name with whitespaces before rule definition


## [0.1.1] - 2021-05-19

### Fixed

- Fix typo in initialize parameter  condition_requires_bool


## [0.1.0] - 2021-05-19

### Added

- created rule class
- made rule parser iterable
- added better exceptions


## [0.0.5] - 2021-05-18

### Added

- add option to handle missing/unknown rule arguments


## [0.0.4] - 2021-05-18

### Changed

- better error messages


## [0.0.3] - 2021-05-03

### Fixed

- Fix error "Logging TypeError: not all arguments converted during string formatting" when enable debug by @ferulisses


## [0.0.2] - 2020-08-27

### Added

- Readme

### Fixed

- various fixes


## [0.0.1] - 2020-08-26

Initial release


[Unreleased]: https://github.com/manfred-kaiser/business-rule-engine/compare/1.0.0...master
[1.0.0]: https://github.com/manfred-kaiser/business-rule-engine/compare/0.2.0...1.0.0
[0.2.0]: https://github.com/manfred-kaiser/business-rule-engine/compare/0.1.3...0.2.0
[0.1.3]: https://github.com/manfred-kaiser/business-rule-engine/compare/0.1.2...0.1.3
[0.1.2]: https://github.com/manfred-kaiser/business-rule-engine/compare/0.1.1...0.1.2
[0.1.1]: https://github.com/manfred-kaiser/business-rule-engine/compare/0.1.0...0.1.1
[0.1.0]: https://github.com/manfred-kaiser/business-rule-engine/compare/0.0.5...0.1.0
[0.0.5]: https://github.com/manfred-kaiser/business-rule-engine/compare/0.0.4...0.0.5
[0.0.4]: https://github.com/manfred-kaiser/business-rule-engine/compare/0.0.3...0.0.4
[0.0.3]: https://github.com/manfred-kaiser/business-rule-engine/compare/v0.0.2...0.0.3
[0.0.2]: https://github.com/manfred-kaiser/business-rule-engine/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/manfred-kaiser/business-rule-engine/releases/tag/v0.0.1
