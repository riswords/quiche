from typing import Optional, List

from quiche.egraph import EGraph, EClassID, ENode, EClassAnalysis
from quiche.lang.expr_lang import ExprNode, ExprTree


class ExprConstantFolding(EClassAnalysis[Optional[int]]):
    binops: List[str] = ["+", "-", "*", "/", "<<"]

    def make(self, egraph: "EGraph", enode: ENode) -> Optional[int]:
        """
        Create a new analysis value in the domain.

        :param n: enode
        :returns: dval value in the domain
        """
        # return number if we have an int
        if type(enode.key) == int:
            return enode.key
        # if we have a supported operator and numeric operands,
        # perform the operation
        elif enode.key in self.binops:
            operands = [enode.args[0].data, enode.args[1].data]
            if all(operands):
                if enode.key == "+":
                    return operands[0] + operands[1]
                elif enode.key == "-":
                    return operands[0] - operands[1]
                elif enode.key == "*":
                    return operands[0] * operands[1]
                elif enode.key == "/" and operands[1] != 0:
                    return operands[0] // operands[1]
                elif enode.key == "<<" and operands[1] >= 0:
                    return operands[0] << operands[1]
                elif enode.key == ">>" and operands[1] >= 0:
                    return operands[0] >> operands[1]
        return None

    def join(self, dval1: Optional[int],
             dval2: Optional[int]) -> Optional[int]:
        """Combine two analysis values, respecting semilattice laws
        :returns: dval value in the domain
        """
        if dval1 is None:
            return dval2
        if dval2 is None:
            return dval1
        if dval1 != dval2:
            raise ValueError(
                "Constant folding error: {} != {}".format(dval1, dval2))
        return dval1

    def modify(self, egraph: "EGraph", eclass: EClassID) -> EClassID:
        """(Optional) modify the eclass when its associated analysis value
        changes.
        :returns: modified eclass
        """
        if eclass.data is not None:
            new_node = ExprNode(eclass.data, ())
            ecid = egraph.add(ExprTree(new_node))
            egraph.merge(eclass, ecid)
        return eclass.find()
