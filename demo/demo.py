from quiche.pyast.ast_quiche_tree import ASTQuicheTree
from quiche.egraph import EGraph

## Construction
quiche_tree = ASTQuicheTree("newton_sqrt.py")

egraph = EGraph(quiche_tree)
root = egraph.root


## Term extraction
from quiche.analysis import MinimumCostExtractor
from quiche.pyast.ast_size_cost_model import ASTSizeCostModel

model = ASTSizeCostModel()
extractor = MinimumCostExtractor()

term = extractor.extract(model, egraph, root)
term.to_file("newton_sqrt_unchanged.py")
print(str(term))


## Rewrite rule
rewrite = ASTQuicheTree.make_rule(
  "while True:\n\t__quiche__body",
  "while 1:\n\t__quiche__body"
)

egraph.apply_rules([rewrite])


## Term extraction again
from quiche.pyast.ast_heuristic_cost_model import ASTHeuristicCostModel

model = ASTHeuristicCostModel()
extractor = MinimumCostExtractor()

term = extractor.extract(model, egraph, root)
term.to_file("newton_sqrt_while_1.py")
