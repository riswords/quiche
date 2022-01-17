from typing import Dict, Tuple, Union
import math

from quiche.rewrite import Rule
from quiche.egraph import ENode, EClassID, EGraph
from quiche.quiche_tree import QuicheTree

from .prop_test_lexer import PropLexer

import ply.yacc as yacc


class PropTree(QuicheTree):
    def __init__(self, value: Union[str, int], children: Tuple["PropTree", ...]):
        self._value = value
        self._children = children

    @classmethod
    def parse(cls, data):
        parser = PropParser()
        parser.build()
        result = parser.parse(data)
        return result

    def value(self):
        return self._value

    def children(self):
        return self._children

    @staticmethod
    def make_rule(lhs, rhs):
        return Rule(PropTree.parse(lhs), PropTree.parse(rhs))


class PropTreeCost:
    """
    Simple cost model for PropTree nodes:

    ~ costs 1
    &, | cost 2
    -> costs 3
    """

    def __init__(self):
        self.prop_costs = {
            "~": 2,
            "&": 2,
            "|": 2,
            "->": 3,
        }

    def enode_cost(self, node: ENode, costs: Dict[EClassID, int]) -> int:
        """
        Calculate the cost of a node based solely on its key (not its children)
        """
        return self.prop_costs.get(node.key, 0)

    def enode_cost_rec(
        self, enode: ENode, costs: Dict[EClassID, Tuple[int, ENode]]
    ) -> int:
        """
        Calculate the cost of a node based on its key and its children

        :param enode: the node to calculate the cost of
        :param costs: dictionary containing costs of children
        """
        return self.enode_cost(enode, costs) + sum(costs[eid][0] for eid in enode.args)

    def extract(
        self, eclassid: EClassID, costs: Dict[EClassID, Tuple[int, ENode]]
    ) -> ENode:
        enode = costs[eclassid][1]
        return ENode(
            enode.key, tuple(self.extract(eid, costs) for eid in enode.args)
        )


class PropTreeExtractor:
    def __init__(self, cost_model: PropTreeCost):
        self.cost_model = cost_model

    def schedule(self, egraph: EGraph, result: EClassID) -> ENode:
        """
        Extract lowest cost ENode from EGraph.
        Calculate lowest cost for each node using `prop_costs` to weight each
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


class PropParser(object):
    tokens = PropLexer.tokens
    """
        id: bool | symbol | ( prop )
        term : id
        prop: term
            | (AND prop prop)
            | (OR prop prop)
            | (IMPLIES prop prop)
            | (NOT prop)
    """
    # Parsing rules
    precedence = (
        ("left", "AND"),
        ("left", "OR"),
        ("left", "IMPLIES"),
        ("right", "NOT"),
    )

    def __init__(self):
        self.lexer = PropLexer()
        self.lexer.build()

    def p_prop_term(self, p):
        "prop : term"
        # print("PROP TERM: {}: {}".format(p[1], type(p[1])))
        p[0] = p[1]

    def p_prop_and(self, p):
        "prop : AND prop prop"
        # print("PROP AND: [{}: {}] [{}: {}]".format(p[2], type(p[2]), p[3], type(p[3])))
        p[0] = PropTree("&", (p[2], p[3]))

    def p_prop_or(self, p):
        "prop : OR prop prop"
        # print("PROP OR: [{}: {}] [{}: {}]".format(p[2], type(p[2]), p[3], type(p[3])))
        p[0] = PropTree("|", (p[2], p[3]))

    def p_prop_implies(self, p):
        "prop : IMPLIES prop prop"
        # print("PROP IMPLIES: [{}: {}], [{}: {}]".format(p[2], type(p[2]), p[3], type(p[3])))
        p[0] = PropTree("->", (p[2], p[3]))

    def p_prop_not(self, p):
        "prop : NOT prop"
        # print("NOT PROP: {}: {}".format(p[2], type(p[2])))
        p[0] = PropTree("~", (p[2],))

    def p_term_id(self, p):
        "term : id"
        # print("TERM ID: {}: {}".format(p[1], type(p[1])))
        p[0] = p[1]

    def p_id_symbol(self, p):
        "id : SYMBOL"
        # print("ID SYMBOL: {}: {}".format(p[1], type(p[1])))
        p[0] = PropTree(p[1], ())

    def p_id_bool(self, p):
        "id : BOOL"
        # print("ID BOOL: {}: {}".format(p[1], type(p[1])))
        p[0] = PropTree(p[1], ())

    def p_id_paren(self, p):
        "prop : LPAREN prop RPAREN"
        # print("PAREN: {}: {}".format(p[2], type(p[2])))
        p[0] = p[2]

    def p_error(self, p):
        print("Syntax error at '%s'" % p)

    def build(self, **kwargs):
        self.parser = yacc.yacc(module=self, **kwargs)

    def parse(self, data):
        self.lexer.input(data)
        return self.parser.parse(data, lexer=self.lexer.lexer)
