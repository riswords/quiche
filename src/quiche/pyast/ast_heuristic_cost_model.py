from typing import Dict, Tuple

from quiche.analysis import CostModel
from quiche.egraph import ENode, EClassID


class ASTHeuristicCostModel(CostModel):
    """
    Cost model for AST nodes, based on "size", i.e., number of children
    and also a relative weighting for AST nodes. The default weighting
    may optionally be altered by users.
    """

    def __init__(self, node_weights: Dict[str, int] = None):
        self.node_weights = {
            "Module": 1,
            "Interactive": 1,
            "Expression": 1,
            "Suite": 1,
            "FunctionDef": 1,
            "AsyncFunctionDef": 1,
            "ClassDef": 1,
            "Return": 1,
            "Delete": 1,
            "Assign": 1,
            "AugAssign": 1,
            "AnnAssign": 1,
            "For": 1,
            "AsyncFor": 1,
            "While": 1,
            "If": 1,
            "With": 1,
            "AsyncWith": 1,
            "Raise": 1,
            "Try": 1,
            "Assert": 1,
            "Import": 1,
            "ImportFrom": 1,
            "Global": 1,
            "Nonlocal": 1,
            "Expr": 1,
            "Pass": 1,
            "Break": 1,
            "Continue": 1,
            "BoolOp": 1,
            "BinOp": 1,
            "UnaryOp": 1,
            "Lambda": 1,
            "IfExp": 1,
            "Dict": 1,
            "Set": 1,
            "ListComp": 1,
            "SetComp": 1,
            "DictComp": 1,
            "GeneratorExp": 1,
            "Yield": 1,
            "YieldFrom": 1,
            "Compare": 1,
            "Call": 1,
            "Num": 1,
            "Str": 1,
            "FormattedValue": 1,
            "JoinedStr": 1,
            "Bytes": 1,
            "NameConstant": 5,
            "Ellipsis": 1,
            "Constant": 1,
            "Attribute": 1,
            "Subscript": 1,
            "Starred": 1,
            "Name": 1,
            "List": 1,
            "Tuple": 1,
            "Load": 1,
            "Store": 1,
            "Del": 1,
            "AugLoad": 1,
            "AugStore": 1,
            "Param": 1,
            "Slice": 1,
            "ExtSlice": 1,
            "Index": 1,
            "And": 1,
            "Or": 1,
            "Add": 1,
            "Sub": 1,
            "Mult": 1,
            "MatMult": 1,
            "Div": 1,
            "Mod": 1,
            "Pow": 1,
            "LShift": 1,
            "RShift": 1,
            "BitOr": 1,
            "BitXor": 1,
            "BitAnd": 1,
            "FloorDiv": 1,
            "Invert": 1,
            "Not": 1,
            "UAdd": 1,
            "USub": 1,
            "Eq": 1,
            "NotEq": 1,
            "Lt": 1,
            "LtE": 1,
            "Gt": 1,
            "GtE": 1,
            "Is": 1,
            "IsNot": 1,
            "In": 1,
            "NotIn": 1,
            "ExceptHandler": 1,
            # special leaf kinds:
            "int": 0,
            "float": 1,
            "bool": 2,
            "complex": 3,
            "str": 4,
        }
        if node_weights:
            self.node_weights.update(node_weights)

    def enode_cost(self, node: ENode) -> int:
        """
        Calculate the cost of a node based solely on its key (not its children)
        """
        key = node.key
        if hasattr(node.key, "__name__"):
            key = node.key.__name__
        elif isinstance(node.key, tuple):
            key = node.key[0]

        if key in self.node_weights:
            return self.node_weights[key]
        elif node.key in self.node_weights:
            return self.node_weights[node.key]
        return 1

    def enode_cost_rec(
        self, enode: ENode, costs: Dict[EClassID, Tuple[int, ENode]]
    ) -> int:
        """
        Calculate the cost of a node based on its key and its children

        :param enode: the node to calculate the cost of
        :param costs: dictionary containing costs of children
        """
        child_costs = sum(costs[eid][0] for eid in enode.args)
        return self.enode_cost(enode) + child_costs
