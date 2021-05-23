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

Business rule engine uses Excel like functions (thanks to [formulas](https://github.com/vinci1it2000/formulas). So it is possible to use most of them in rules.


## Multiple conditions and multiple actions

You can make multiple checks on the same params, and call multiple actions as needed:

```python
rules = """
rule "order new items"
when
    AND(products_in_stock < 20,
    products_in_stock >= 5)
then
    order_more(50)
end

rule "order new items urgent"
when
    products_in_stock < 5,
then
    AND(order_more(10, true),
    order_more(50))
end
"""
```

## Custom functions

You can also write your own functions to validate conditions and use other libraries functions as actions:

```python
from business_rule_engine import RuleParser

def is_even(num):
   if (num % 2) == 0:
      return True
   return False

params = {
    'number': 10
}

rules = """
rule "check even number"
when
    is_even(number) = True
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

## Handle missing rule parameters

If some argruments are missing, the rule engine will raise a ValueError.

There are some use cases, when you have to work with incomplete data. In such cases, you can define
default arguments.

You enable default rule arguments with the parameter `set_defaule_arg`. The default argument will have the Value `None`. To provide another value you can use `default_arg`.

```python
params = {}

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
parser.execute(params, set_default_arg=True, default_arg=0)
```

## More control of the RulePraser

if you need more control, how the rule parser handles rules, you can iterate over the parser and execute each rule in your script.

This gives you more control on how to handle missing arguments, rules with errors and you have access to the return values of the conditions and the actions.

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

params = {
    'products_in_stock': 10
}

parser = RuleParser()
parser.register_function(order_more)
parser.parsestr(rules)
for rule in parser:
    try:
        rvalue_condition, rvalue_action = rule.execute(params)
        if rule.status:
            print(rvalue_action)
            break
    except MissingArgumentError:
        pass
```


## Error Handling

Most of the errors are caused by missing parameters, you can handle the errors and interpret the results handling ValueError:

```python
from business_rule_engine import RuleParser

# proposital typo
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
    ret = parser.execute(params)
    if ret is False:
        print("No conditions matched")
except ValueError as e:
    print(e)
```

## Debug

To debug the rules processing, use the logging lib.

You can insert in your Python script to log to stdout:
```
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
```
