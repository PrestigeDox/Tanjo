import math
import operator
from pyparsing import (Literal, CaselessLiteral, Word, Combine, Group, Optional, OneOrMore,
                       ZeroOrMore, Forward, nums, alphas, oneOf)


class NumericStringParserForPython3(object):
    # So, this is the whole code for calculator
    # It converts the input into something that can give some
    # sort of result, or at least tries to do so
    def push_first(self, strg, loc, toks):
        self.expr_stack.append(toks[0])

    def push_uminus(self, strg, loc, toks):
        if toks and toks[0] == '-':
            self.expr_stack.append('unary -')

    def __init__(self):
        point = Literal(".")
        e = CaselessLiteral("E")
        fnumber = Combine(Word("+-" + nums, nums) +
                          Optional(point + Optional(Word(nums))) +
                          Optional(e + Word("+-" + nums, nums)))
        ident = Word(alphas, alphas + nums + "_$")
        plus = Literal("+")
        minus = Literal("-")
        mult = Literal("*")
        div = Literal("/")
        lpar = Literal("(").suppress()
        rpar = Literal(")").suppress()
        addop = plus | minus
        multop = mult | div
        expop = Literal("^")
        pi = CaselessLiteral("PI")
        expr = Forward()
        atom = ((Optional(oneOf("- +")) +
                 (pi | e | fnumber | ident + lpar + expr + rpar).setParseAction(self.push_first))
                | Optional(oneOf("- +")) + Group(lpar + expr + rpar)
                ).setParseAction(self.push_uminus)
        # By defining exp as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...",
        # the exponents are parsed right-to-left exponents, instead of left-to-right
        # that is, 2^3^2 = 2^(3^2), instead of (2^3)^2.
        factor = Forward()
        factor << atom + ZeroOrMore((expop + factor).setParseAction(self.push_first))
        term = factor + ZeroOrMore((multop + factor).setParseAction(self.push_first))
        expr << term + ZeroOrMore((addop + term).setParseAction(self.push_first))
        addop_term = (addop + term).setParseAction(self.push_first)
        general_term = term + ZeroOrMore(addop_term) | OneOrMore(addop_term)
        expr << general_term
        self.bnf = expr
        # Here the code maps operator symbols to their corresponding arithmetic operations
        # decided to go for * instead of x to be used in multiplications, for obvious reasons:
        # it is commonly used that way with computer keypads that have numbers using one hand
        # And yeah, I know where you keep the other hand... lewd!
        epsilon = 1e-12
        self.opn = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
            "^": operator.pow}
        # After getting the correct operators, now to make use of strings for more advanced
        # mathematical calculations, haven't tried them all intensively, so they might break,
        # if that happens, use your phone's calculator instead, kthx.
        self.fn = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "abs": abs,
            "trunc": lambda a: int(a),
            "round": round,
            "sgn": lambda a: abs(a) > epsilon and (a>0)-(a<0) or 0}

    def evaluate_stack(self, s):
        op = s.pop()
        if op == 'unary -':
            return -self.evaluate_stack(s)
        if op in "+-*/^":
            op2 = self.evaluate_stack(s)
            op1 = self.evaluate_stack(s)
            return self.opn[op](op1, op2)
        elif op == "PI":
            return math.pi  # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in self.fn:
            return self.fn[op](self.evaluate_stack(s))
        elif op[0].isalpha():
            return 0
        else:
            return float(op)

    def eval(self, num_string, parse_all=True):
        self.expr_stack = []
        results = self.bnf.parseString(num_string, parse_all)
        val = self.evaluate_stack(self.expr_stack[:])
        return val