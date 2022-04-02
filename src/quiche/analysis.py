from abc import ABC, abstractmethod
from math import inf
from typing import Dict, Tuple

from quiche.egraph import EGraph, EClassID, ENode
from quiche.quiche_tree import QuicheTree


class CostModel(ABC):
    @abstractmethod
    def enode_cost(self, enode, costs):
        """
        Calculate the cost of a node, not taking its children into account.

        :param enode: enode whose cost is to be calculated
        :param costs: dictionary of costs for eclasses
        :returns: cost of the node
        """
        pass

    @abstractmethod
    def enode_cost_rec(
        self, enode: ENode, costs: Dict[EClassID, Tuple[int, ENode]]
    ) -> int:
        """
        Calculate the cost of a node based on its key and its children

        :param enode: the node to calculate the cost of
        :param costs: dictionary containing costs of children
        """
        pass

    @abstractmethod
    def lookup(
        self, eclassid: EClassID, costs: Dict[EClassID, Tuple[int, ENode]]
    ) -> QuicheTree:
        """
        Look up a QuicheTree corresponding to the lowest cost ENode from the EClassID.

        :param eclassid: eclassid to look up
        :param costs: dictionary from EClassID to a (cost, ENode) tuple
        :returns: QuicheTree corresponding to the lowest cost ENode
        """
        pass


class CostExtractor(ABC):
    @abstractmethod
    def extract(
        self, cost_model: CostModel, egraph: EGraph, result: EClassID
    ) -> QuicheTree:
        """
        Extract the QuicheTree for the "best" ENode from the  EGraph,
        based on a cost model.

        :param cost_model: CostModel to use for cost calculations
        :param egraph: EGraph from which to extract
        :param result: EClassID to extract
        :returns: tree of the "best" ENodes, based on the CostModel
        """
        pass


class MinimumCostExtractor(CostExtractor):
    def extract(
        self, cost_model: CostModel, egraph: EGraph, result: EClassID
    ) -> QuicheTree:
        """
        Extract lowest cost ENode from EGraph.
        Calculate lowest cost for each node using `costs` to weight each
        operation.

        :returns: lowest cost node
        """
        result = result.find()
        eclasses = egraph.eclasses()
        # TODO: initializing costs like this doesn't typecheck because inf is a
        # float, and there is no maxint in python3. Rework so that
        # uninitialized costs can be absent from `costs`. (NOTE: this might
        # also help with the issue of eclasses containing enodes with the same
        # key).
        costs = {eid: (inf, None) for eid in eclasses.keys()}
        changed = True

        # iterate until saturation, taking lowest cost option
        while changed:
            changed = False
            for eclass, enodes in eclasses.items():
                new_cost = min(
                    (cost_model.enode_cost_rec(enode, costs), enode) for enode in enodes
                )
                if costs[eclass][0] != new_cost[0]:
                    changed = True
                costs[eclass] = new_cost

        return cost_model.lookup(result, costs)


# class EClassAnalysis(ABC):
#     """
#     EClass Analysis

#     `join` must respect semilattice laws

#     1. Must maintain the invariant that:

#     for every eclass in the graph,
#         the analysis data for that eclass, dc, is the (lattice) LUB of the
#         `make` of all nodes in that eclass

#     In other words, the data in the eclass is the same as if you called
#     `make` on all nodes of the eclass and then `join`ed them together

#     2. `modify` is at a fixed point
#     """

#     def make(self, n):
#         """Create a new analysis value in the domain
#         :returns: dval value in the domain
#         """
#         pass

#     def join(self, dval1, dval2):
#         """Combine two analysis values, respecting semilattice laws
#         :returns: dval value in the domain
#         """
#         pass

#     def modify(self, eclass: EClassID):
#         """(Optional) modify the eclass when its associated analysis value
#         changes.
#         :returns: modified eclass
#         """
#         pass
