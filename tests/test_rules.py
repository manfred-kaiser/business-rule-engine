import pytest  # type: ignore
from business_rule_engine import RuleParser, Rule
from business_rule_engine.exceptions import RuleParserSyntaxError
from formulas.errors import FormulaError


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


def test_rules():
    params = {
        'products_in_stock': 10
    }

    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsestr(rules)
    assert parser.execute(params) is True


def test_missing_args():
    params = {}
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsestr(rules)
    assert parser.execute(params, set_default_arg=True, default_arg=0) is True


def test_iterate_rules():
    params = {
        'products_in_stock': 10
    }
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsestr(rules)
    for rule in parser:
        rvalue_condition, rvalue_action = rule.execute(params)
        if rule.status:
            assert rvalue_action == "you ordered 50 new items"
            break


def test_duplicate_then():
    rules_invalid = """
    rule "order new items"
    when
        products_in_stock < 20
    then
        order_more(50)
    then
        order_more(10)
    end
    """
    parser = RuleParser()
    with pytest.raises(RuleParserSyntaxError):
        parser.parsestr(rules_invalid)


def test_multiple_lines_invalid():
    rules_invalid = """
    rule "order new items"
    when
        1 = 1
    then
        1 + 1
        2 + 2
    end
    """

    parser = RuleParser()
    parser.parsestr(rules_invalid)
    with pytest.raises(FormulaError):
        parser.execute({})


def test_rule():
    params = {
        'products_in_stock': 10
    }
    rule = Rule('testrule')
    rule.conditions.append('products_in_stock < 20')
    rule.actions.append('2 + 3')

    assert rule.check_condition(params) == True
    assert rule.run_action(params) == 5
