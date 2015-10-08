import sys
from modgrammar import *

grammar_whitespace_mode = 'optional'

"""
ParenExpr := (Expr)
P0Term := ParenExpr | Number
P0Expr := P0Term (/P0Term)*
P1Term := P0Expr | ParenExpr | Number
P1Expr := P1Term (*times*P1Term)*
P2Term := P0Expr | P1Expr | ParenExpr | Number
P2Expr := P2Term (+|- P2Term)*
Expr := P2Expr | P1Expr | P0Expr | ParenExpr | Number
"""

"""
\frac{2}{2^{8}}
\frac{2}{9}^{5}

Number := 
ParenExpr := (Expr)
BracketExpr := {Expr}
ParsedExpr := \frac{Expr}{Expr}
P0Term := ParenExpr | ParsedExpr | Number 
P0Expr := P0Term ^ BracketExpr
Expr := P0Expr | ParsedExpr | ParenExpr | Number
"""


"""
Number := 0-9
Var := a-z, A-Z
ParsedExpr := \frac{Expr}{Expr} | \sum_{Expr}^{Expr}{Expr} ....
ParenExpr := (Expr)
P0Term := ParsedExpr | ParenExpr | Var | Number
P0Expr := P0Term^{P0Term}
P1Term := P0Expr | P0Term
P1Expr := P1Term (*|/ P1Term)k*
P2Term := P1Expr | P1Term
P2Expr := P2Term (+|- P2Term)k*
Expr := P2Expr | P1Expr | P0Expr | P0Term
"""

"""
Items that need to be parsed using brackets
"""
class Frac (Grammar):
    #frac{}{}
    grammar = (L('\\frac'), REF('BracketExpr'), REF('BracketExpr'))

    def value(self):
        return self[1].value() + "/" + self[2].value()

class Sum (Grammar):
    #sum_{}^{}{}
    grammar = (L('\\sum_{'), REF('Var'), L('='), REF('Number'), L('}^{'), REF('Number'), L('}'), REF('BracketExpr'))

    def value(self):
        return "nsum(lambda {}: {}, [{},{}])".format(self[7].value(), self[1].value(), self[3].value(), self[5].value())

class Integral (Grammar):
    #integral_{a}^{b}{func dx}
    #integral(func, (x,a,b))
    grammar = (L('\\integral_{'), REF('Expr'), L('}^{'), REF('Expr'), L('}{'), REF('Expr'), L('d'), REF('Var'), L('}'))
    
    def value(self):
        return "integral({},({},{},{}))".format(self[5].value(), self[7].value(), self[1].value(), self[3].value())

class ParsedExpr (Grammar):
    grammar = Frac | Integral | Sum

    def value(self):
        return self[0].value()

"""
Items that don't need to be parsed, really
"""

class ParenExpr (Grammar):
    grammar = (L('('), REF('Expr'), L(')'))

    def value(self):
        return self.string

class BracketExpr (Grammar):
    grammar = (L('{'), REF('Expr'), L('}'))

    def value(self):
        return "(" + self[1].value() + ")"


"""
Single Items
"""
class Number (Grammar):
    """ 
    Pulls out a number in the form num.num
    num
    """
    grammar = (OPTIONAL('-'), WORD('0-9'), OPTIONAL('.', ONE_OR_MORE(WORD('0-9'))))

    def value(self):
        return self.string

class Var (Grammar):
    grammar = (OPTIONAL('-'), WORD('a-z') | WORD('A-Z'))

    def value(self):
        return self.string

class SingleTon (Grammar):
    grammar = (Number | Var)

    def value(self):
        return self[0].value()

"""
Ordering
"""
# P0Term := ParsedExpr | ParenExpr | Var | Number
# P0Expr := P0Term^{P0Term}
# P1Term := P0Expr | P0Term
# P1Expr := P1Term (*|/ P1Term)k*
# P2Term := P1Expr | P1Term
# P2Expr := P2Term (+|- P2Term)k*
# Expr := P2Expr | P1Expr | P0Expr | P0Term

class P0Term (Grammar):
    #P0Term := ParsedExpr | ParenExpr | Var | Number
    grammar = ParsedExpr | ParenExpr | Var | Number

    def value(self):
        return self[0].value()

class P0Expr (Grammar):
    #P0Expr := P0Term^{P0Term}
    grammar = (REF('P0Term'), L('^'), REF('BracketExpr'))

    def value(self):
        return "{}**{}".format(self[0].value(), self[2].value())

class P1TermSub1 (Grammar):
    grammar = (REF('Number'), REF('Var'))

    def value(self):
        return "{}*{}".format(self[0].value(), self[1].value())

class P1Term (Grammar):
    # P1Term := P0Expr | P0Term
    grammar = (P1TermSub1 | P0Expr | P0Term)

    def value(self):
        return self[0].value()

class P1Expr (Grammar):
    # P1Expr := P1Term (*|/ P1Term)k*
    grammar = (REF('P1Term'), ONE_OR_MORE(L('*') | L('/'), REF('P1Term')))

    def value(self):
        string = self[0].value()
        if len(self) > 2:
            for expr in self[1]:
                if (expr[0].string == "*"):
                    string += "*{}".format(expr[1].value())
                else:
                    string += "/{}".format(expr[1].value())
        return string

class P2Term (Grammar):
    # P2Term := P1Expr | P1Term
    grammar = (P1Expr | P1Term)

    def value(self):
        return self[0].value()

class P2Expr (Grammar):
    # P2Expr := P2Term (+|- P2Term)k*
    grammar = (REF('P2Term'), ONE_OR_MORE(L('+') | L('-'), REF('P2Term')))

    def value(self):
        string = self[0].value()
        for expr in self[1]:
            if (expr[0].string == "+"):
                string += "+{}".format(expr[1].value())
            else:
                string += "-{}".format(expr[1].value())
        return string

class Expr (Grammar):
    # Expr := P2Expr | P1Expr | P0Expr | P0Term
    grammar = (OPTIONAL('-'), P2Expr | P1Expr | P0Expr | P0Term)

    def value(self):
        if self[0]:
            return "-{}".format(self[1].value())
        return self[1].value()


if __name__ == '__main__':
    parser = Expr.parser()
    result = parser.parse_text(sys.argv[1], eof=True)
    remainder = parser.remainder()
    print("Parsed Text: {}".format(result))
    print("Unparsed Text: {}".format(remainder))
    print("Value: {}".format(result.value()))


