from quiche import EGraph, MinimumCostExtractor
from quiche.rewrite import Rule
from quiche.lang.expr_lang import ExprNode, ExprNodeCost, ExprTree
from quiche.lang.expr_constant_folding import ExprConstantFolding


def egraph_intro_slide_8():
    expr = (ExprNode('a', ()) * 2) / 2
    quiche_tree = ExprTree(expr)
    egraph = EGraph(quiche_tree)


def egraph_add_shift_term_slide_9():
    # setup
    expr = (ExprNode('a', ()) * 2) / 2
    quiche_tree = ExprTree(expr)
    egraph = EGraph(quiche_tree)

    # on slide
    shift_expr = ExprNode('a', ()) << 1
    egraph.add(ExprTree(shift_expr))


def eclass_merge_example_slide_11():
    # setup
    expr = (ExprNode('a', ()) * 2) / 2
    quiche_tree = ExprTree(expr)
    egraph = EGraph(quiche_tree)
    shift_expr = ExprNode('a', ()) << 1

    # on slide
    shift_eclass = egraph.add(ExprTree(shift_expr))
    times_node = ExprNode('a', ()) * 2
    times_eclass = egraph.add(ExprTree(times_node))

    egraph.merge(times_eclass, shift_eclass)

    egraph.rebuild()


def ematching_example_slide_15():
    # setup
    expr = (ExprNode('a', ()) * 2) / 2
    quiche_tree = ExprTree(expr)
    egraph = EGraph(quiche_tree)
    shift_expr = ExprNode('a', ()) << 1
    egraph.add(ExprTree(shift_expr))

    # on slide
    pattern = ExprTree(ExprNode('x', ()) * 2)
    matches = egraph.ematch(pattern, egraph.eclasses())
    print(matches)


def apply_a_rule_slide_16():
    # setup
    expr = (ExprNode('a', ()) * 2) / 2
    quiche_tree = ExprTree(expr)
    egraph = EGraph(quiche_tree)
    shift_expr = ExprNode('a', ()) << 1

    # on slide
    shift_eclass = egraph.add(ExprTree(shift_expr))
    rule = ExprTree.make_rule(lambda x: (x * 2, x << 1))
    Rule.apply_rules([rule], egraph)
    print("Shift e-class: ", shift_eclass)
    print("Shift e-class.find(): ", shift_eclass.find())


def apply_rules_to_eqsat_slide_22():
    # setup
    expr = (ExprNode('a', ()) * 2) / 2
    quiche_tree = ExprTree(expr)
    egraph = EGraph(quiche_tree)
    shift_expr = ExprNode('a', ()) << 1
    egraph.add(ExprTree(shift_expr))
    rule = ExprTree.make_rule(lambda x: (x * 2, x << 1))
    Rule.apply_rules([rule], egraph)

    # on slide
    rules = [
        ExprTree.make_rule(lambda x, y, z: ((x * y) / z, x * (y / z))),
        ExprTree.make_rule(lambda x: (x / x, ExprNode(1, ()))),
        ExprTree.make_rule(lambda x: (x * 1, x))
    ]
    while not egraph.is_saturated():
        Rule.apply_rules(rules, egraph)
    aeclass = egraph.add(ExprTree(ExprNode('a', ())))
    assert aeclass.find() == egraph.root.find()
    # print("a eclass: ", aeclass.find())
    # print("root eclass: ", egraph.root.find())


def constant_folding_usage_slide_28():
    expr = (ExprNode('a', ()) * 2) / 2
    quiche_tree = ExprTree(expr)
    egraph = EGraph(quiche_tree, ExprConstantFolding())
    four_eclass = egraph.add(ExprTree(ExprNode(4, ())))
    a_eclass = egraph.add(ExprTree(ExprNode("a", ())))
    egraph.merge(a_eclass, four_eclass)
    egraph.rebuild()
    assert egraph.root.data == 4


def term_extraction_example_slide_31():
    # setup
    expr = (ExprNode('a', ()) * 2) / 2
    quiche_tree = ExprTree(expr)
    egraph = EGraph(quiche_tree)
    rules = [
        # Multiply x by 2 === shift x left by 1
        ExprTree.make_rule(lambda x: (x * 2, x << 1)),
        # Reassociate *,/
        ExprTree.make_rule(lambda x, y, z: ((x * y) / z, x * (y / z))),
        # x/x = 1
        ExprTree.make_rule(lambda x: (x / x, ExprNode(1, ()))),
        # Simplify x * 1 === x
        ExprTree.make_rule(lambda x: (x * 1, x)),
    ]
    while not egraph.is_saturated():
        Rule.apply_rules(rules, egraph)

    # Verify extracted term is correct
    cost_model = ExprNodeCost()
    extractor = MinimumCostExtractor()
    extracted = extractor.extract(

        cost_model, egraph, egraph.root.find(), ExprTree.make_node
    )
    assert str(extracted) == "a"


def main():
    egraph_intro_slide_8()
    egraph_add_shift_term_slide_9()
    eclass_merge_example_slide_11()
    ematching_example_slide_15()
    apply_a_rule_slide_16()
    apply_rules_to_eqsat_slide_22()
    constant_folding_usage_slide_28()
    term_extraction_example_slide_31()


def test_main():
    main()


if __name__ == "__main__":
    main()
