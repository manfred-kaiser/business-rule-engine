import time
import sys
import os
sys.path.insert(0, os.getcwd())
from business_rule_engine import RuleParser


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

parser = RuleParser()
parser.register_function(order_more)
parser.parsestr(rules)

params_list = [{'products_in_stock': 10}] * 10_000

start_time = time.time()

for params in params_list:
    assert parser.execute(params) is True

end_time = time.time()
execution_time = end_time - start_time
print(f"Execution time: {execution_time:.3f} seconds")
