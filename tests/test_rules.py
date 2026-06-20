import pytest
from business_rule_engine import RuleParser, Rule
from business_rule_engine.exceptions import RuleParserSyntaxError, MissingArgumentError
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
    assert parser.execute(params)


def test_missing_args():
    params = {}
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsestr(rules)
    assert parser.execute(params, set_default_arg=True, default_arg=0)


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

    assert rule.check_condition(params) is True
    assert rule.run_action(params) == 5


def test_add_rule():
    parser = RuleParser()
    parser.add_rule('testrule', 'products_in_stock < 20', '2 + 3')
    params = {
        'products_in_stock': 10
    }
    parser.execute(params)


def test_execution_result():
    params = {'products_in_stock': 10}
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsestr(rules)
    result = parser.execute(params)
    assert result
    assert len(result.results) == 1
    assert result.results[0].rule_name == "order new items"
    assert result.results[0].triggered is True
    assert result.results[0].action_result == "you ordered 50 new items"


def test_execution_result_no_trigger():
    params = {'products_in_stock': 100}
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsestr(rules)
    result = parser.execute(params)
    assert not result
    assert result.results[0].triggered is False
    assert result.results[0].action_result is None


def test_priority():
    rules_priority = """
rule "low priority"
when
    products_in_stock < 20
then
    order_more(10)
end

rule "high priority" priority 10
when
    products_in_stock < 20
then
    order_more(50)
end
"""
    params = {'products_in_stock': 5}
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsestr(rules_priority)
    result = parser.execute(params)
    assert result
    assert result.results[0].rule_name == "high priority"


def test_disabled_rule():
    params = {'products_in_stock': 10}
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsestr(rules)
    parser.rules["order new items"].enabled = False
    result = parser.execute(params)
    assert not result
    assert len(result.results) == 0


def test_description():
    rules_with_desc = """
rule "order new items"
description "Orders new items when stock is low"
when
    products_in_stock < 20
then
    order_more(50)
end
"""
    parser = RuleParser()
    parser.parsestr(rules_with_desc)
    assert parser.rules["order new items"].description == "Orders new items when stock is low"


def test_parsefile(tmp_path):
    rules_file = tmp_path / "rules.txt"
    rules_file.write_text(rules)
    params = {'products_in_stock': 10}
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsefile(rules_file)
    assert parser.execute(params)


def test_missing_argument_error():
    params = {'produtcs_in_stock': 30}  # intentional typo
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsestr(rules)
    with pytest.raises(MissingArgumentError):
        parser.execute(params)
