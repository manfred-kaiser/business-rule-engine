business-rule-engine
====================

[![CodeFactor](https://www.codefactor.io/repository/github/manfred-kaiser/business-rule-engine/badge)](https://www.codefactor.io/repository/github/manfred-kaiser/business-rule-engine)
[![Github version](https://img.shields.io/github/v/release/manfred-kaiser/business-rule-engine?label=github&logo=github)](https://github.com/manfred-kaiser/business-rule-engine/releases)
[![PyPI version](https://img.shields.io/pypi/v/business-rule-engine.svg?logo=pypi&logoColor=FFE873)](https://pypi.org/project/business-rule-engine/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/business-rule-engine.svg?logo=python&logoColor=FFE873)](https://pypi.org/project/business-rule-engine/)
[![PyPI downloads](https://pepy.tech/badge/business-rule-engine/month)](https://pepy.tech/project/business-rule-engine/month)
[![GitHub](https://img.shields.io/github/license/manfred-kaiser/business-rule-engine.svg)](LICENSE)

As a software system grows in complexity and usage, it can become burdensome if every change to the logic/behavior of the system also requires you to write and deploy new code. The goal of this business rules engine is to provide a simple interface allowing anyone to capture new rules and logic defining the behavior of a system, and a way to then process those rules on the backend.

You might, for example, find this is a useful way for analysts to define marketing logic around when certain customers or items are eligible for a discount, or to automate emails after users enter a certain state or go through a particular sequence of events.

## Usage

### 1. Define your variables

Variables represent values in your system, usually the value of some particular object. You create rules by setting threshold conditions such that when a variable is computed that triggers the condition, some action is taken.

```python
params = {
    'products_in_stock': 10
}
```

### 2. Define custom functions

```python
def order_more(items_to_order):
    print("you ordered {} new items".format(items_to_order))
    return items_to_order
```

### 3. Write the rules

Rules use standard Python expression syntax. The `when` block supports multi-line expressions with `and`/`or` — lines are joined and evaluated as a single Python expression. Each `then` line is an action executed in order.

```python
rules = """
rule "order new items"
when
    products_in_stock < 20
then
    order_more(50)
end
"""
```

### 4. Create the parser and execute

```python
from business_rule_engine import RuleParser

parser = RuleParser()
parser.register_function(order_more)
parser.parsestr(rules)

result = parser.execute(params)
if result:
    print("A rule was triggered")
```

## Multiple conditions and multiple actions

The `when` block uses standard Python boolean syntax. Multiple lines are joined into a single expression, so `and`/`or` work exactly as in Python. Each line in the `then` block is a separate action executed in order.

```python
rules = """
rule "standard reorder"
when
    products_in_stock < 20
    and margin > 0.3
then
    order_more(50)
    notify_purchasing()
end

rule "urgent reorder"
when
    products_in_stock < 5
    or products_reserved > 100
then
    order_more(200)
    notify_manager()
end
"""
```

## Custom functions

You can register your own functions to use in conditions and actions:

```python
from business_rule_engine import RuleParser

def is_even(num):
    return (num % 2) == 0

params = {
    'number': 10
}

rules = """
rule "check even number"
when
    is_even(number) == True
then
    print("is even")
end
"""

parser = RuleParser()
parser.register_function(is_even)
parser.register_function(print)
parser.parsestr(rules)
parser.execute(params)
```

You can also register a function under a different name for use in rules:

```python
parser.register_function(is_even, "even")  # use as even(number) in rules
```
```

## Rule options

### Priority

Rules with a higher priority are evaluated first. The default priority is `0`. Rules with equal priority are evaluated in the order they were added.

Priority can be set on the rule line or as a separate keyword:

```
rule "urgent reorder" priority 10
when
    products_in_stock < 5
then
    order_more(200)
end

rule "standard reorder"
priority 5
when
    products_in_stock < 20
then
    order_more(50)
end
```

Priority can also be set when using `add_rule()`:

```python
parser.add_rule("urgent reorder", "products_in_stock < 5", "order_more(200)", priority=10)
```

### Description

Rules can carry a human-readable description:

```
rule "standard reorder"
description "Triggers a standard reorder when stock falls below 20 units"
when
    products_in_stock < 20
then
    order_more(50)
end
```

### Allowing non-boolean conditions

By default, the parser raises `ConditionReturnValueError` if a `when` expression does not evaluate to a `bool`. Set `condition_requires_bool=False` to accept any truthy/falsy value instead:

```python
parser = RuleParser(condition_requires_bool=False)
```

This can also be set per rule:

```python
rule = Rule("my rule", condition_requires_bool=False)
```

### Enabling and disabling rules

Rules can be disabled at runtime without removing them from the parser:

```python
parser.rules["standard reorder"].enabled = False
```

Disabled rules are skipped during `execute()` and do not appear in the execution results.

### Removing and counting rules

Check whether a rule exists and how many rules are loaded:

```python
"standard reorder" in parser  # True / False
len(parser)                    # number of registered rules
```

Remove a single rule or all rules at once:

```python
parser.remove_rule("standard reorder")  # raises KeyError if not found
parser.clear_rules()                    # removes all rules
```

### Managing custom functions

Remove a previously registered function or clear all of them:

```python
RuleParser.unregister_function("order_more")  # raises KeyError if not found
RuleParser.clear_functions()                  # removes all custom functions
```

Note: `CUSTOM_FUNCTIONS` is shared across all parser instances, so `clear_functions()` affects every instance.

## Processing all matching rules

By default, `execute()` stops after the first rule whose condition is satisfied (`stop_on_first_trigger=True`). Set it to `False` to evaluate every enabled rule regardless:

```python
result = parser.execute(params, stop_on_first_trigger=False)

for r in result.results:
    if r.triggered:
        print(f"{r.rule_name}: {r.action_result}")
```

This is useful when multiple independent rules may apply to the same input.

## Loading rules from a file

Use `parsefile()` to load rules directly from a file:

```python
parser = RuleParser()
parser.register_function(order_more)
parser.parsefile("rules/reorder.rules")
parser.execute(params)
```

## Accessing execution results

`execute()` returns an `ExecutionResult` object that behaves like a `bool` but also gives you access to the result of each rule:

```python
from business_rule_engine import RuleParser

def order_more(items_to_order):
    return "you ordered {} new items".format(items_to_order)

def notify_purchasing():
    return "purchasing notified"

rules = """
rule "standard reorder"
when
    products_in_stock < 20
then
    order_more(50)
    notify_purchasing()
end
"""

parser = RuleParser()
parser.register_function(order_more)
parser.register_function(notify_purchasing)
parser.parsestr(rules)

result = parser.execute({'products_in_stock': 10})

for r in result.results:
    if r.triggered:
        print(f"{r.rule_name}: {r.action_result}")
        # → standard reorder: ['you ordered 50 new items', 'purchasing notified']
```

Each entry in `result.results` is a `RuleResult` with these fields:

| Field | Type | Description |
|---|---|---|
| `rule_name` | `str` | Name of the rule |
| `triggered` | `bool` | Whether all conditions evaluated to `True` |
| `condition_result` | `bool` | Result of the condition evaluation |
| `action_result` | `list[object]` | Return values of each action, or `[]` if not triggered |

## Handle missing rule parameters

If a required argument is missing, the rule engine raises a `MissingArgumentError`.

For cases where you work with incomplete data, you can provide a default value:

```python
params = {}

parser = RuleParser()
parser.register_function(order_more)
parser.parsestr(rules)
parser.execute(params, set_default_arg=True, default_arg=0)
```

## More control of the RuleParser

If you need full control over rule execution, you can iterate over the parser and execute each rule individually:

```python
from business_rule_engine import RuleParser
from business_rule_engine.exceptions import MissingArgumentError

def order_more(items_to_order):
    return "you ordered {} new items".format(items_to_order)

rules = """
rule "order new items"
when
    products_in_stock < 20
then
    order_more(50)
end
"""

params = {'products_in_stock': 10}

parser = RuleParser()
parser.register_function(order_more)
parser.parsestr(rules)

for rule in parser:
    try:
        condition_result, action_results = rule.execute(params)
        if rule.status:
            print(action_results[0])
            break
    except MissingArgumentError:
        pass
```

## Error Handling

```python
from business_rule_engine import RuleParser
from business_rule_engine.exceptions import MissingArgumentError

def order_more(items_to_order):
    return "you ordered {} new items".format(items_to_order)

# intentional typo
params = {
    'produtcs_in_stock': 30
}

rules = """
rule "order new items"
when
    products_in_stock < 20
then
    order_more(50)
end
"""

parser = RuleParser()
parser.register_function(order_more)
parser.parsestr(rules)

try:
    result = parser.execute(params)
    if not result:
        print("No conditions matched")
except MissingArgumentError as e:
    print(e)
```

## Debug

To debug the rules processing, use the logging module:

```python
import sys
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
```

---

## Migration Guide

### From 0.x to 1.x

Version 1.0 is a major rewrite with several breaking changes.

#### Rule expression syntax

Rules no longer use Excel-style syntax. All expressions are plain Python:

| 0.x (Excel syntax) | 1.x (Python syntax) |
|---|---|
| `AND(a, b)` | `a and b` |
| `OR(a, b)` | `a or b` |
| `NOT(a)` | `not a` |
| `a = b` | `a == b` |

#### Multiple `when` lines

Multiple `when` lines are no longer treated as independent conditions joined with AND.
They are concatenated into a single Python expression, so you must write the operators explicitly:

```
# 0.x — implicit AND between lines
when
    products_in_stock < 20
    margin > 0.3

# 1.x — explicit operator required
when
    products_in_stock < 20
    and margin > 0.3
```

#### `action_result` is now a list

Each `then` line is a separate action. `action_result` is now `list[object]` instead of a single value:

```python
# 0.x
condition_result, action_result = rule.execute(params)
print(action_result)          # single value

# 1.x
condition_result, action_results = rule.execute(params)
print(action_results[0])      # first action result
print(action_results)         # all action results
```

#### Renamed and restructured exceptions

The exception base class and one exception were renamed for consistency with Python naming conventions:

| 0.x | 1.x |
|---|---|
| `RuleParserException` | `RuleParserError` |
| `DuplicateRuleName` | `DuplicateRuleNameError` |

A new exception `DuplicateThenError` (subclass of `RuleParserSyntaxError`) is raised when a rule block contains more than one `then` section.

#### Boolean parameters are now keyword-only

All boolean and optional parameters must be passed as keyword arguments:

```python
# 0.x
parser = RuleParser(False)
rule = Rule("name", False, 10, False)
parser.execute(params, False)

# 1.x
parser = RuleParser(condition_requires_bool=False)
rule = Rule("name", condition_requires_bool=False, priority=10, enabled=False)
parser.execute(params, stop_on_first_trigger=False)
```

This also applies to `add_rule()`:

```python
# 0.x
parser.add_rule("name", "cond", "action", 10, False, "desc")

# 1.x
parser.add_rule("name", "cond", "action", priority=10, enabled=False, description="desc")
```

#### `CUSTOM_FUNCTIONS` is now a class-level dict

In 0.x, functions were registered as a list of strings. In 1.x, `CUSTOM_FUNCTIONS` is a
`dict[str, Callable]` (name → callable) and is shared across all parser instances.
Use `register_function()` to add functions — do not modify `CUSTOM_FUNCTIONS` directly.
