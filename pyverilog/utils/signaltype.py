# -------------------------------------------------------------------------------
# signaltype.py
#
# Signal type checker to create precise assignment tree
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import re


# Verilog Signal Type Checker
def isType(termtype, matchtype):
    for t in termtype:
        if t == matchtype:
            return True
    return False


def isInput(termtype):
    return isType(termtype, 'Input')


def isOutput(termtype):
    return isType(termtype, 'Output')


def isInout(termtype):
    return isType(termtype, 'Inout')


def isWire(termtype):
    return isType(termtype, 'Wire')


def isReg(termtype):
    return isType(termtype, 'Reg')


def isInteger(termtype):
    return isType(termtype, 'Integer')


def isGenvar(termtype):
    return isType(termtype, 'Genvar')


def isParameter(termtype):
    return isType(termtype, 'Parameter')


def isLocalparam(termtype):
    return isType(termtype, 'Localparam')


def isFunction(termtype):
    return isType(termtype, 'Function')


def isRename(termtype):
    return isType(termtype, 'Rename')


# Clock/Reset
regex_clock = ['clk', 'clock', ]
regex_reset = ['reset', 'rst', ]


def isClock(search_str):
    lower_str = search_str.lower()
    for rc in regex_clock:
        if re.search(rc, lower_str):
            return True
    return False


def isReset(search_str):
    lower_str = search_str.lower()
    for rr in regex_reset:
        if re.search(rr, lower_str):
            return True
    return False


# Operator
compare_ops = ('LessThan', 'GreaterThan', 'LassEq', 'GreaterEq', 'Eq', 'NotEq', 'Eql', 'NotEql')
not_ops = ('Ulnot', 'Unot')
split_and_ops = ('And', 'Land')
split_or_ops = ('Or', 'Lor')
non_condition_ops = compare_ops + not_ops + split_and_ops + split_or_ops


def isCompare(op):
    if op in compare_ops:
        return True
    return False


def isNot(op):
    if op in not_ops:
        return True
    return False


def isAnd(op):
    if op in split_and_ops:
        return True
    return False


def isOr(op):
    if op in split_or_ops:
        return True
    return False


def isNonConditionOp(op):
    if op in non_condition_ops:
        return False
    return True
