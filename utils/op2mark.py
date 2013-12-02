#-------------------------------------------------------------------------------
# op2mark.py
# 
# converting an operator to its mark
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------

operator_dict = {
    'Uminus':'-', 'Ulnot':'!', 'Unot':'~', 'Uand':'&', 'Unand':'~&',
    'Uor':'|', 'Unor':'~|', 'Uxor':'^', 'Uxnor':'~^',
    'Power':'**', 'Times':'*', 'Divide':'/', 'Mod':'%', 
    'Plus':'+', 'Minus':'-',
    'Sll':'<<', 'Srl':'>>', 'Sra':'>>>',
    'LessThan':'<', 'GreaterThan':'>', 'LessEq':'<=', 'GreaterEq':'>=',
    'Eq':'==', 'NotEq':'!=', 'Eql':'===', 'NotEql':'!==',
    'And':'&', 'Xor':'^', 'Xnor':'~^',
    'Or':'|', 'Land':'&&', 'Lor':'||'
    }

def op2mark(op):
    return operator_dict[op]
