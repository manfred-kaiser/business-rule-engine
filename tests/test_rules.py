from pathlib import Path

import pytest

from business_rule_engine import Rule, RuleParser
from business_rule_engine.exceptions import (
    ConditionReturnValueError,
    DuplicateRuleNameError,
    DuplicateThenError,
    MissingArgumentError,
    RuleParserError,
    RuleParserSyntaxError,
)


def order_more(items_to_order):
    return "you ordered {} new items".format(items_to_order)


# --- parsestr ---


def test_parsestr():
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
    assert parser.execute({'products_in_stock': 10})


# --- parsefile ---


def test_parsefile(rules_dir):
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsefile(rules_dir / "order_items.rule")
    assert parser.execute({'products_in_stock': 10})


def test_parsefile_missing_file():
    parser = RuleParser()
    with pytest.raises(FileNotFoundError):
        parser.parsefile("/nonexistent/path/rules.rule")


def test_parsefile_from_string_path(rules_dir):
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsefile(str(rules_dir / "order_items.rule"))
    assert parser.execute({'products_in_stock': 10})


# --- execution results ---


def test_execution_result(rules_dir):
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsefile(rules_dir / "order_items.rule")
    result = parser.execute({'products_in_stock': 10})
    assert result
    assert len(result.results) == 1
    assert result.results[0].rule_name == "order new items"
    assert result.results[0].triggered is True
    assert result.results[0].action_result == ["you ordered 50 new items"]


def test_execution_result_no_trigger(rules_dir):
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsefile(rules_dir / "order_items.rule")
    result = parser.execute({'products_in_stock': 100})
    assert not result
    assert result.results[0].triggered is False
    assert result.results[0].action_result == []


# --- multiple conditions / actions ---


def test_multiple_conditions(rules_dir):
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsefile(rules_dir / "multi_condition.rule")

    assert parser.execute({'products_in_stock': 10, 'margin': 0.5})
    assert not parser.execute({'products_in_stock': 10, 'margin': 0.1})
    assert not parser.execute({'products_in_stock': 30, 'margin': 0.5})


def test_multiple_actions(rules_dir):
    log = []

    def action_a():
        log.append('a')
        return 'a'

    def action_b():
        log.append('b')
        return 'b'

    parser = RuleParser()
    parser.register_function(action_a)
    parser.register_function(action_b)
    parser.parsefile(rules_dir / "multi_action.rule")

    result = parser.execute({'trigger': True})
    assert result
    assert result.results[0].action_result == ['a', 'b']
    assert log == ['a', 'b']


def test_inline_boolean(rules_dir):
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsefile(rules_dir / "inline_boolean.rule")

    assert parser.execute({'products_in_stock': 3, 'category': 'normal'})
    assert parser.execute({'products_in_stock': 50, 'category': 'priority'})
    assert not parser.execute({'products_in_stock': 50, 'category': 'normal'})


# --- priority ---


def test_priority(rules_dir):
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsefile(rules_dir / "priority.rule")
    result = parser.execute({'products_in_stock': 5})
    assert result
    assert result.results[0].rule_name == "high priority"


def test_priority_as_own_line(rules_dir):
    parser = RuleParser()
    parser.parsefile(rules_dir / "priority_own_line.rule")
    assert parser.rules["order new items"].priority == 5


# --- stop_on_first_trigger ---


def test_stop_on_first_trigger_true(rules_dir):
    parser = RuleParser()
    parser.parsefile(rules_dir / "stop_on_trigger.rule")
    result = parser.execute({'x': 5})
    assert result
    assert len(result.results) == 1
    assert result.results[0].rule_name == "rule A"


def test_stop_on_first_trigger_false(rules_dir):
    parser = RuleParser()
    parser.parsefile(rules_dir / "stop_on_trigger.rule")
    result = parser.execute({'x': 5}, stop_on_first_trigger=False)
    assert result
    assert len(result.results) == 2
    assert all(r.triggered for r in result.results)
    assert result.results[0].rule_name == "rule A"
    assert result.results[1].rule_name == "rule B"


# --- rule metadata ---


def test_disabled_rule(rules_dir):
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsefile(rules_dir / "order_items.rule")
    parser.rules["order new items"].enabled = False
    result = parser.execute({'products_in_stock': 10})
    assert not result
    assert len(result.results) == 0


def test_description(rules_dir):
    parser = RuleParser()
    parser.parsefile(rules_dir / "description.rule")
    assert parser.rules["order new items"].description == "Orders new items when stock is low"


# --- missing arguments ---


def test_missing_args(rules_dir):
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsefile(rules_dir / "order_items.rule")
    assert parser.execute({}, set_default_arg=True, default_arg=0)


def test_missing_argument_error(rules_dir):
    params = {'produtcs_in_stock': 30}  # intentional typo
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsefile(rules_dir / "order_items.rule")
    with pytest.raises(MissingArgumentError):
        parser.execute(params)


# --- condition_requires_bool ---


def test_condition_return_value_error():
    rule = Rule("testrule")
    rule.conditions.append("1 + 1")
    with pytest.raises(ConditionReturnValueError):
        rule.check_condition({})


def test_condition_requires_bool_false():
    rule = Rule("testrule", condition_requires_bool=False)
    rule.conditions.append("1 + 1")
    assert rule.check_condition({}) is True


# --- duplicate errors ---


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


def test_duplicate_then_error_type():
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
    with pytest.raises(DuplicateThenError):
        parser.parsestr(rules_invalid)


def test_duplicate_rule_name_parsestr():
    rules_dup = """
rule "my rule"
when
    x > 0
then
    x
end

rule "my rule"
when
    x > 1
then
    x
end
"""
    parser = RuleParser()
    with pytest.raises(DuplicateRuleNameError):
        parser.parsestr(rules_dup)


def test_duplicate_rule_name_add_rule():
    parser = RuleParser()
    parser.add_rule("my rule", "x > 0", "x")
    with pytest.raises(DuplicateRuleNameError):
        parser.add_rule("my rule", "x > 1", "x")


def test_duplicate_rule_name_is_rule_parser_error():
    parser = RuleParser()
    parser.add_rule("r", "x > 0", "x")
    with pytest.raises(RuleParserError):
        parser.add_rule("r", "x > 1", "x")


# --- programmatic API ---


def test_rule():
    params = {'products_in_stock': 10}
    rule = Rule('testrule')
    rule.conditions.append('products_in_stock < 20')
    rule.actions.append('2 + 3')

    assert rule.check_condition(params) is True
    assert rule.run_action(params) == [5]


def test_iterate_rules(rules_dir):
    params = {'products_in_stock': 10}
    parser = RuleParser()
    parser.register_function(order_more)
    parser.parsefile(rules_dir / "order_items.rule")
    for rule in parser:
        condition_result, action_results = rule.execute(params)
        if rule.status:
            assert action_results[0] == "you ordered 50 new items"
            break


def test_add_rule():
    parser = RuleParser()
    parser.add_rule('testrule', 'products_in_stock < 20', '2 + 3')
    params = {'products_in_stock': 10}
    parser.execute(params)


def test_register_function_with_custom_name():
    def double(x):
        return x * 2

    parser = RuleParser()
    parser.register_function(double, "times_two")
    parser.add_rule("test", "x > 0", "times_two(x)")
    result = parser.execute({'x': 5})
    assert result.results[0].action_result == [10]


# --- rule management ---


def test_len_parser(rules_dir):
    parser = RuleParser()
    assert len(parser) == 0
    parser.parsefile(rules_dir / "order_items.rule")
    assert len(parser) == 1
    parser.parsefile(rules_dir / "stop_on_trigger.rule")
    assert len(parser) == 3


def test_contains_parser(rules_dir):
    parser = RuleParser()
    parser.parsefile(rules_dir / "order_items.rule")
    assert "order new items" in parser
    assert "nonexistent rule" not in parser
