from typing import Dict, Tuple, Union
import math

from quiche.egraph import ENode, EGraph, EClassID
from quiche.rewrite import Rule


class ExprNode(ENode):
    key: "Union[str, int]"  # use int to represent int literals,
    args: "Tuple[ExprNode,...]"

    # overload some operators to allow us to easily construct these
    def _mk_op(key):
        return lambda *args: ExprNode(
            key,
            tuple(
                arg if isinstance(arg, ExprNode) else ExprNode(arg, ()) for arg in args
            ),
        )

    __add__ = _mk_op("+")
    __mul__ = _mk_op("*")
    __lshift__ = _mk_op("<<")
    __truediv__ = _mk_op("/")

    # print it out like an s-expr
    def __repr__(self):
        if self.args:
            return f'({self.key} {" ".join(str(arg) for arg in self.args)})'
        else:
            return str(self.key)

    @staticmethod
    def exp(fn):
        c = fn.__code__
        args = [ExprNode(c.co_varnames[i], ()) for i in range(c.co_argcount)]
        return fn(*args)

    @staticmethod
    def make_rule(fn):
        lhs, rhs = ExprNode.exp(fn)
        return Rule(lhs, rhs)


class ExprNodeCost:
    """
    Simple cost model for ExprNodes:

    +, << cost 1
    * costs 2
    / costs 3
    """

    def __init__(self):
        self.expr_costs = {
            "+": 1,
            "<<": 1,
            "*": 2,
            "/": 3,
        }

    def enode_cost(self, node: ExprNode, costs: Dict[EClassID, int]) -> int:
        """
        Calculate the cost of a node based solely on its key (not its children)
        """
        if node.key == "+" or node.key == "<<":
            return 1
        elif node.key == "*":
            return 2
        elif node.key == "/":
            return 3
        else:
            return 0

    def enode_cost_rec(
        self, enode: ExprNode, costs: Dict[EClassID, Tuple[int, ExprNode]]
    ) -> ExprNode:
        """
        Calculate the cost of a node based on its key and its children

        :param enode: the node to calculate the cost of
        :param costs: dictionary containing costs of children
        """
        return self.enode_cost(enode, costs) + sum(costs[eid][0] for eid in enode.args)

    def extract(
        self, eclassid: EClassID, costs: Dict[EClassID, Tuple[int, ExprNode]]
    ) -> ExprNode:
        enode = costs[eclassid][1]
        return ExprNode(
            enode.key, tuple(self.extract(eid, costs) for eid in enode.args)
        )


class ExprNodeExtractor:
    def __init__(self, cost_model: ExprNodeCost):
        self.cost_model = cost_model

    def schedule(self, egraph: EGraph, result: EClassID) -> ExprNode:
        """
        Extract lowest cost ENode from EGraph.
        Calculate lowest cost for each node using `expr_costs` to weight each
        operation.

        :returns: lowest cost node
        """
        result = result.find()
        eclasses = egraph.eclasses()
        costs = {eid: (math.inf, None) for eid in eclasses.keys()}
        changed = True

        # iterate until saturation, taking lowest cost option
        while changed:
            changed = False
            for eclass, enodes in eclasses.items():
                new_cost = min(
                    (self.cost_model.enode_cost_rec(enode, costs), enode)
                    for enode in enodes
                )
                if costs[eclass][0] != new_cost[0]:
                    changed = True
                costs[eclass] = new_cost

        return self.cost_model.extract(result, costs)
