from typing import Callable, Dict, Sequence

from quiche.quiche_tree import QuicheTree
from quiche.egraph import EGraph, EClassID, EMatch, ENode, EGraphRewriter, Subst, EGraphSearcher


class Rule(EGraphSearcher, EGraphRewriter):
    def __init__(self, lhs: QuicheTree, rhs: QuicheTree):
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return "{} -> {}".format(self.lhs, self.rhs)

    @staticmethod
    def apply_rules(rules: Sequence["Rule"], egraph: EGraph):
        """
        :param egraph: e-graph in which rule is being applied
        :returns: modified e-graph
        """
        matches = []
        for rule in rules:
            matches.append((rule, egraph.search(rule)))

        changed = False
        for (rule, rule_matches) in matches:
            new_changes = egraph.apply_rewrite(rule, rule_matches)
            if new_changes:
                changed = True

        egraph.rebuild()
        if changed:
            egraph._is_saturated = False
        return egraph

    def search(self, egraph: EGraph) -> Sequence[EMatch]:
        canonical_eclasses = egraph.eclasses()
        return egraph.ematch(self.lhs, canonical_eclasses)

    def apply_to_eclass(self, egraph: EGraph, eid: EClassID, env: Subst) -> EClassID:
        return self._subst(egraph, self.rhs, env)

    def _subst(self, egraph: EGraph, pattern: QuicheTree, env: Dict[str, EClassID]):
        """
        :param pattern: QuicheTree
        :param env: Dict[str, EClassID]
        :returns: EClassID
        """
        if pattern.is_pattern_symbol():
            return env[pattern.value()]
        else:
            enode = ENode(
                pattern.value(),
                tuple(self._subst(egraph, child, env) for child in pattern.children()),
            )
            return egraph.add_enode(enode)
