from typing import Callable, Dict, Sequence

from quiche.quiche_tree import QuicheTree
from quiche.egraph import (
    EGraph,
    EClassID,
    EMatch,
    ENode,
    EGraphRewriter,
    Subst,
    EGraphSearcher,
)


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

        version = egraph.version
        for (rule, rule_matches) in matches:
            egraph.apply_rewrite(rule, rule_matches)

        egraph.rebuild()
        if version != egraph.version:
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


class ConditionalRule(Rule):
    """
    Base class for conditional rewrite rules.

    Conditional rules should either:
    1. Be initialized with a `checker` function (EGraph, EClassID, Subst) -> bool; or
    2. Extend the `ConditionalRule` class and override the `check_condition` method

    Otherwise, the ConditionalRule will never be applied.
    (Note: it might make logical sense for a ConditionalRule without a checker to
    always apply the rewrite; however, we choose to assume that a conditional rule
    without a checker is the result of a client error and decline to apply the rule.)
    """

    def __init__(
        self,
        lhs: QuicheTree,
        rhs: QuicheTree,
        checker: Callable[[EGraph, EClassID, Subst], bool] = None,
    ):
        super().__init__(lhs, rhs)
        self._checker = checker

    def check_condition(self, egraph: EGraph, eid: EClassID, env: Subst) -> bool:
        if self._checker:
            return self._checker(egraph, eid, env)
        else:
            return False

    def apply_to_eclass(self, egraph: EGraph, eid: EClassID, env: Subst) -> EClassID:
        if self.check_condition(egraph, eid, env):
            return super().apply_to_eclass(egraph, eid, env)
        return eid
