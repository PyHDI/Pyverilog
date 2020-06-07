# -------------------------------------------------------------------------------
# op2mark.py
#
# converting an operator to its mark
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------

operator_mark = {
    'Uminus': '-', 'Ulnot': '!', 'Unot': '~', 'Uand': '&', 'Unand': '~&',
    'Uor': '|', 'Unor': '~|', 'Uxor': '^', 'Uxnor': '~^',
    'Power': '**', 'Times': '*', 'Divide': '/', 'Mod': '%',
    'Plus': '+', 'Minus': '-',
    'Sll': '<<', 'Srl': '>>', 'Sla': '<<<', 'Sra': '>>>',
    'LessThan': '<', 'GreaterThan': '>', 'LessEq': '<=', 'GreaterEq': '>=',
    'Eq': '==', 'NotEq': '!=', 'Eql': '===', 'NotEql': '!==',
    'And': '&', 'Xor': '^', 'Xnor': '~^',
    'Or': '|', 'Land': '&&', 'Lor': '||',
    'PlusEquals': '+=', 'MinusEquals': '-=', 'TimesEquals': '*=', 'DivideEquals': '/=', 'ModEquals': '%=',
    'OrEquals': '|=', 'AndEquals': '&=', 'XorEquals': '^=',
    'SllEquals': '<<=', 'SrlEquals': '>>=', 'SlaEquals': '<<<=', 'SraEquals': '>>>=',
    'Increment': '++', 'Decrement': '--',
}


def op2mark(op):
    if op not in operator_mark:
        return None
    return operator_mark[op]


operator_order = {
    'StaticCast': 0,
    'Uminus': 1, 'Ulnot': 1, 'Unot': 1, 'Uand': 1, 'Unand': 1,
    'Uor': 1, 'Unor': 1, 'Uxor': 1, 'Uxnor': 1,
    'Power': 2,
    'Times': 3, 'Divide': 3, 'Mod': 3,
    'Plus': 4, 'Minus': 4,
    'Sll': 5, 'Srl': 5, 'Sla': 5, 'Sra': 5,
    'LessThan': 6, 'GreaterThan': 6, 'LessEq': 6, 'GreaterEq': 6,
    'Eq': 7, 'NotEq': 7, 'Eql': 7, 'NotEql': 7,
    'And': 8,
    'Xor': 9, 'Xnor': 9,
    'Or': 10,
    'Land': 11,
    'Lor': 12
}


def op2order(op):
    if op not in operator_order:
        return None
    return operator_order[op]
