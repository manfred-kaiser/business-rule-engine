import pytest  # type: ignore
from business_rule_engine import RuleParser


def order_more(items_to_order, urgent=False):
    print("you ordered {} new items".format(items_to_order))
    return items_to_order


rules = """
rule "order new items"
when
    products_in_stock < 20
then
    order_more(50)
end
"""


def test_rules():
    params = {
        'products_in_stock': 10
    }

    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsestr(rules)
    parser.execute(params)


def test_missing_args():
    params = {}
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsestr(rules)
    parser.execute(params, set_default_arg=True, default_arg=0)
