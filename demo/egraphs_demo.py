from quiche.analysis import MinimumCostExtractor
from quiche.ast_quiche_tree import ASTQuicheTree
from quiche.ast_constant_folding import ASTConstantFolding
from quiche.ast_size_cost_model import ASTSizeCostModel
from quiche.egraph import EGraph


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
        egraph.apply_rules(rules)

    extracted = MinimumCostExtractor().extract(
        ASTSizeCostModel(), egraph, egraph.root,
        ASTQuicheTree.make_node
    )
    extracted.to_file("time_folding.py")


def test_main():
    main()


if __name__ == "__main__":
    main()