from .prop_test_lexer import PropLexer
from .prop_test_node import PropNode

import ply.yacc as yacc

class PropParser(object):
    tokens = PropLexer.tokens
    """
        id: bool | symbol | ( prop )
        term : id
            | NOT term
        prop: term
            | (AND prop prop)
            | (OR prop prop)
            | (IMPLIES prop prop)
    """
    # Parsing rules
    precedence = (
        ('left', 'AND'),
        ('left', 'OR'),
        ('left', 'IMPLIES'),
        ('right', 'NOT'),
    )

    def __init__(self):
        self.lexer = PropLexer()
        self.lexer.build()

    def p_prop_term(self, p):
        'prop : term'
        #print("PROP TERM: {}: {}".format(p[1], type(p[1])))
        p[0] = p[1]

    def p_prop_and(self, p):
        'prop : AND prop prop'
        #print("PROP AND: [{}: {}] [{}: {}]".format(p[2], type(p[2]), p[3], type(p[3])))
        p[0] = PropNode('&', (p[2], p[3]))
    
    def p_prop_or(self, p):
        'prop : OR prop prop'
        #print("PROP OR: [{}: {}] [{}: {}]".format(p[2], type(p[2]), p[3], type(p[3])))
        p[0] = PropNode('|', (p[2], p[3]))

    def p_prop_implies(self, p):
        'prop : IMPLIES prop prop'
        #print("PROP IMPLIES: [{}: {}], [{}: {}]".format(p[2], type(p[2]), p[3], type(p[3])))
        p[0] = PropNode('->', (p[2], p[3]))
        
    def p_term_not(self, p):
        'term : NOT term'
        #print("NOT TERM: {}: {}".format(p[2], type(p[2])))
        p[0] = PropNode('~', (p[2],))
    
    def p_term_id(self, p):
        'term : id'
        #print("TERM ID: {}: {}".format(p[1], type(p[1])))
        p[0] = p[1]

    def p_id_symbol(self, p):
        'id : SYMBOL'
        #print("ID SYMBOL: {}: {}".format(p[1], type(p[1])))
        p[0] = PropNode(p[1], ())
    
    def p_id_bool(self, p):
        'id : BOOL'
        #print("ID BOOL: {}: {}".format(p[1], type(p[1])))
        p[0] = PropNode(p[1], ())
    
    def p_id_paren(self, p):
        'prop : LPAREN prop RPAREN'
        #print("PAREN: {}: {}".format(p[2], type(p[2])))
        p[0] = p[2]

    def p_error(self, p):
        print("Syntax error at '%s'" % p)
    
    def build(self, **kwargs):
        self.parser = yacc.yacc(module=self, **kwargs)
    
    def parse(self, data):
        self.lexer.input(data)
        return self.parser.parse(data, lexer=self.lexer.lexer)