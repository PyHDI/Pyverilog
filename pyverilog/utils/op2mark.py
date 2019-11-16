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
    'Or': '|', 'Land': '&&', 'Lor': '||'
}


def op2mark(op):
    if op not in operator_mark:
        return None
    return operator_mark[op]


operator_order = {
    'Uminus': 0, 'Ulnot': 0, 'Unot': 0, 'Uand': 0, 'Unand': 0,
    'Uor': 0, 'Unor': 0, 'Uxor': 0, 'Uxnor': 0,
    'Power': 1,
    'Times': 2, 'Divide': 2, 'Mod': 2,
    'Plus': 3, 'Minus': 3,
    'Sll': 4, 'Srl': 4, 'Sla': 4, 'Sra': 4,
    'LessThan': 5, 'GreaterThan': 5, 'LessEq': 5, 'GreaterEq': 5,
    'Eq': 6, 'NotEq': 6, 'Eql': 6, 'NotEql': 6,
    'And': 7,
    'Xor': 8, 'Xnor': 8,
    'Or': 9,
    'Land': 10,
    'Lor': 11
}


def op2order(op):
    if op not in operator_order:
        return None
    return operator_order[op]
