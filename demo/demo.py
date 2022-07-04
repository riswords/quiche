from quiche.pyast import ASTQuicheTree
from quiche import EGraph

## Construction
quiche_tree = ASTQuicheTree("newton_sqrt.py")

egraph = EGraph(quiche_tree)
root = egraph.root


## Term extraction
from quiche import MinimumCostExtractor
from quiche.pyast import ASTSizeCostModel

model = ASTSizeCostModel()
extractor = MinimumCostExtractor()

term = extractor.extract(model, egraph, root, ASTQuicheTree.make_node)
term.to_file("newton_sqrt_unchanged.py")
print(str(term))


## Rewrite rule
rewrite = ASTQuicheTree.make_rule(
  "while True:\n\t__quiche__body",
  "while 1:\n\t__quiche__body"
)

egraph.apply_rules([rewrite])


## Term extraction again
from quiche.pyast import ASTHeuristicCostModel

model = ASTHeuristicCostModel()
extractor = MinimumCostExtractor()

term = extractor.extract(model, egraph, root, ASTQuicheTree.make_node)
term.to_file("newton_sqrt_while_1.py")
