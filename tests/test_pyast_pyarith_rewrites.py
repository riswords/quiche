import os
from sys import version_info

from quiche import EGraph, MinimumCostExtractor, Rule
from quiche.pyast import ASTQuicheTree, ASTSizeCostModel
from quiche.pyast.pyarith_rewrites import mul_zero_rule, mul_div_distributive_rule, div_self_rule, mul_one_rule


def input_directory():
    return os.path.join(os.path.dirname(__file__), "input")


def setup_constant_folding_tree():
    fname = os.path.join(input_directory(), "constant_folding.py")
    tree_root = ASTQuicheTree(fname)
    return tree_root


def test_some_arith_rules_1():
    tree = setup_constant_folding_tree()
    rules = [mul_zero_rule, mul_div_distributive_rule, div_self_rule, mul_one_rule]
    actual = EGraph(tree)

    # Apply rules until saturation
    assert not actual.is_saturated()
    if version_info[:2] <= (3, 7):
        versions = [186, 201, 205, 209, 213, 217]
    else:
        versions = [187, 202, 206, 210, 214, 218]
    for version in versions:
        assert actual.version == version
        Rule.apply_rules(rules, actual)
    assert actual.is_saturated()

    # Verify rewrites
    cost_model = ASTSizeCostModel()
    extractor = MinimumCostExtractor()
    extracted = extractor.extract(cost_model, actual, actual.root, ASTQuicheTree.make_node)
    actual_lines = extracted.to_source_string().splitlines()

    fname = os.path.join(input_directory(), "constant_folding.py")
    with open(fname, "r") as f:
        original_lines = f.read().splitlines()

    for idx, (res, pre) in enumerate(zip(actual_lines, original_lines)):
        if idx in [17, 54]:
            # These two lines have extra parens removed; we keep them for clarity
            continue
        elif idx == 74:
            assert pre == "    y = x * 0"
            assert res == "    y = 0"
        elif idx == 79:
            assert pre == "    y = 5 * 4 * 3 * x * 0"
            assert res == "    y = 0"
        elif idx == 84:
            assert pre == "    y = 4 / 4"
            assert res == "    y = 1"
        elif idx == 89:
            assert pre == "    y = x * 2 / 2"
            assert res == "    y = x / 2"
        elif idx == 99: 
            assert pre == "    y = x * 0 / 0"
            assert res == "    y = 0 / 0"
        else:
            assert res == pre, "Line {}: {} != {}".format(idx, res, pre)


# def test_all_arith_rules_1():
#     tree = setup_constant_folding_tree()
#     # rules = get_all_arith_rules()
#     rules = [mul_div_distributive_rule, div_self_rule, mul_one_rule, mul_zero_rule]
#     actual = EGraph(tree)

#     # Apply rules until saturation
#     assert not actual.is_saturated()
#     # versions = [187, 269, 431, 1916, 58925, 218]
#     versions = [187, 202, 206, 210, 214, 218]
#     for version in versions:
#         assert actual.version == version
#         Rule.apply_rules(rules, actual)
#     assert actual.is_saturated()

#     # Verify rewrites
#     cost_model = ASTSizeCostModel()
#     extractor = MinimumCostExtractor()
#     extracted = extractor.extract(cost_model, actual, actual.root, ASTQuicheTree.make_node)
#     actual_lines = extracted.to_source_string().splitlines()

#     fname = os.path.join(input_directory(), "constant_folding.py")
#     with open(fname, "r") as f:
#         original_lines = f.read().splitlines()

#     for idx, (res, pre) in enumerate(zip(actual_lines, original_lines)):
#         if idx in [17, 54]:
#             # These two lines have extra parens removed; we keep them for clarity
#             continue
#         elif idx == 74:
#             assert pre == "    y = x * 0"
#             assert res == "    y = 0"
#         elif idx == 79:
#             assert pre == "    y = 5 * 4 * 3 * x * 0"
#             assert res == "    y = 0"
#         elif idx == 84:
#             assert pre == "    y = 4 / 4"
#             assert res == "    y = 1"
#         elif idx == 89:
#             assert pre == "    y = x * 2 / 2"
#             assert res == "    y = x / 2"
#         elif idx == 99:
#             assert pre == "    y = x * 0 / 0"
#             assert res == "    y = 0 / 0"
#         else:
#             assert res == pre, "Line {}: {} != {}".format(idx, res, pre)
