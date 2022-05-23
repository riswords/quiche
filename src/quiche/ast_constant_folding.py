from platform import python_version
from typing import Optional, List
from ast import operator, Num, Constant, BinOp, Add, Sub, Mult, Div

from quiche.ast_quiche_tree import ASTQuicheTree
from quiche.egraph import ENode, EClassID, EGraph, EClassAnalysis
from quiche.pal.pal_block import PALLeaf


class ASTConstantFolding(EClassAnalysis[Optional[int]]):
    binops: List[operator] = [Add, Sub, Mult, Div]

    def lookup_binop(self, egraph: EGraph, eclass: EClassID) -> Optional[operator]:
        eclass_nodes = egraph.lookup_eclass(eclass)
        # We really shouldn't have more than one unless we somehow stated
        # that + and - are the same...
        if len(eclass_nodes) == 1:
            enode = eclass_nodes[0]
            if enode.key in ASTConstantFolding.binops:
                return enode.key
        return None

    def make(self, egraph: EGraph, enode: ENode) -> Optional[int]:
        # return number if we have an int
        if type(enode.key) == tuple and enode.key[0] == 'int':
            return enode.key[2]
        # if we have a BinOp and a foldable op, check to see if we have ints to fold
        elif enode.key == BinOp:
            binop = self.lookup_binop(egraph, enode.args[1])
            operands = [enode.args[0].data, enode.args[2].data]
            if binop is not None and all(operands):
                if binop == Add:
                    return operands[0] + operands[1]
                elif binop == Sub:
                    return operands[0] - operands[1]
                elif binop == Mult:
                    return operands[0] * operands[1]
                elif binop == Div:
                    return operands[0] / operands[1]
        return None

    def join(self, n1: Optional[int], n2: Optional[int]) -> Optional[int]:
        if n1 is None:
            return n2
        if n2 is None:
            return n1
        if n1 != n2:
            raise ValueError("Constant folding error: {} != {}".format(n1, n2))
        return n1

    def modify(self, egraph: EGraph, eclass: EClassID) -> EClassID:
        if eclass.data is not None:
            from sys import version_info
            if version_info[:2] <= (3, 7):
                new_node = PALLeaf('int', Num, eclass.data)
            else:
                new_node = PALLeaf('int', Constant, eclass.data, None)
            ecid = egraph.add(ASTQuicheTree(root=new_node))
            egraph.merge(eclass, ecid)
        return eclass
