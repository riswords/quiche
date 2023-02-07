from quiche import EGraph, MinimumCostExtractor
from quiche.pyast import ASTQuicheTree, ASTConstantFolding, ASTSizeCostModel
from quiche.rewrite import Rule


def main():
    quiche_tree = ASTQuicheTree("time_conversion.py")
    egraph = EGraph(quiche_tree, ASTConstantFolding())

    mul_assoc = ASTQuicheTree.make_rule(
        "__quiche__x * __quiche__y * __quiche__z",
        "__quiche__x * (__quiche__y * __quiche__z)")

    mul_div = ASTQuicheTree.make_rule(
        "__quiche__x / __quiche__y / __quiche__z",
        "__quiche__x / (__quiche__y * __quiche__z)")

    rules = [mul_assoc, mul_div]
    while not egraph.is_saturated():
        Rule.apply_rules(rules, egraph)

    extracted = MinimumCostExtractor().extract(
        ASTSizeCostModel(), egraph, egraph.root,
        ASTQuicheTree.make_node
    )
    extracted.to_file("time_folding.py")


def test_main():
    main()


if __name__ == "__main__":
    main()
