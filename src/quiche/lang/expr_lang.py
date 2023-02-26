from typing import Dict, NamedTuple, Tuple, Union

from quiche import EClassID, ENode, QuicheTree, Rule, CostModel


class ExprNode(NamedTuple):
    key: Union[str, int]  # use int to represent int literals,
    args: Tuple["ExprNode", ...]

    # overload some operators to allow us to easily construct these
    @staticmethod
    def _mk_op(key: str):
        return lambda *args: ExprNode(
            key,
            tuple(
                arg if isinstance(arg, ExprNode) else ExprNode(arg, ()) for arg in args
            ),
        )

    def __add__(self, other):
        return ExprNode._mk_op("+")(self, other)

    def __sub__(self, other):
        return ExprNode._mk_op("-")(self, other)

    def __mul__(self, other):
        return ExprNode._mk_op("*")(self, other)

    def __lshift__(self, other):
        return ExprNode._mk_op("<<")(self, other)

    def __rshift__(self, other):
        return ExprNode._mk_op(">>")(self, other)

    def __truediv__(self, other):
        return ExprNode._mk_op("/")(self, other)

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


class ExprTree(QuicheTree):
    def __init__(self, root: ExprNode):
        # self.root = root
        self._value = root.key
        self._children = [ExprTree(arg) for arg in root.args]

    def value(self):
        # return self.root.key
        return self._value

    def children(self):
        # if self.root.args:
        #     return [ExprTree(arg) for arg in self.root.args]
        # return []
        return self._children

    def is_pattern_symbol(self):
        return not self.children() and not isinstance(self.value(), int)

    @staticmethod
    def make_node(key: Union[str, int], children: Tuple["ExprTree", ...]) -> "ExprTree":
        tree = ExprTree(ExprNode(key, ()))
        tree._children = list(children)
        return tree

    @staticmethod
    def make_rule(fn):
        lhs, rhs = ExprNode.exp(fn)
        return Rule(ExprTree(lhs), ExprTree(rhs))


class ExprNodeCost(CostModel):
    """
    Simple cost model for ExprNodes:
    +, -, <<, >> cost 1
    * costs 2
    / costs 3
    everything else costs 0
    """

    def __init__(self):
        self.expr_costs = {
            "+": 1,
            "-": 1,
            "<<": 1,
            ">>": 1,
            "*": 2,
            "/": 3,
        }

    def enode_cost(self, node: ENode) -> int:
        """
        Calculate the cost of a node based solely on its key (not its children)
        """
        return self.expr_costs.get(node.key, 0)

    def enode_cost_rec(
        self, enode: ENode, costs: Dict[EClassID, Tuple[int, ENode]]
    ) -> int:
        """
        Calculate the cost of a node based on its key and its children

        :param enode: the node to calculate the cost of
        :param costs: dictionary containing costs of children
        """
        return self.enode_cost(enode) + sum(costs[eid][0] for eid in enode.args)
