business-rule-engine
====================

[![CodeFactor](https://www.codefactor.io/repository/github/manfred-kaiser/business-rule-engine/badge)](https://www.codefactor.io/repository/github/manfred-kaiser/business-rule-engine)
[![Github version](https://img.shields.io/github/v/release/manfred-kaiser/business-rule-engine?label=github&logo=github)](https://github.com/manfred-kaiser/business-rule-engine/releases)
[![PyPI version](https://img.shields.io/pypi/v/business-rule-engine.svg?logo=pypi&logoColor=FFE873)](https://pypi.org/project/business-rule-engine/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/business-rule-engine.svg?logo=python&logoColor=FFE873)](https://pypi.org/project/business-rule-engine/)
[![PyPI downloads](https://pepy.tech/badge/business-rule-engine/month)](https://pepy.tech/project/business-rule-engine/month)
[![GitHub](https://img.shields.io/github/license/manfred-kaiser/business-rule-engine.svg)](LICENSE)

As a software system grows in complexity and usage, it can become burdensome if every change to the logic/behavior of the system also requires you to write and deploy new code. The goal of this business rules engine is to provide a simple interface allowing anyone to capture new rules and logic defining the behavior of a system, and a way to then process those rules on the backend.

You might, for example, find this is a useful way for analysts to define marketing logic around when certain customers or items are eligible for a discount or to automate emails after users enter a certain state or go through a particular sequence of events.

## Usage

### 1. Define Your set of variables

Variables represent values in your system, usually the value of some particular object.  You create rules by setting threshold conditions such that when a variable is computed that triggers the condition some action is taken.

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

### 3. Create the parser and parse the rule

```python
from business_rule_engine import RuleParser

parser = RuleParser()
parser.register_function(order_more)
parser.parsestr(rules)
parser.execute(params)
```

## Supported functions

Business rule engine uses Excel like functions. So it is possible to use most of them in the rules.
