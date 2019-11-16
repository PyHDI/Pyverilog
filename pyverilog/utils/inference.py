# -------------------------------------------------------------------------------
# inference.py
#
# Value inference
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os

from pyverilog.dataflow.dataflow import *
import pyverilog.utils.verror as verror

this = sys.modules[__name__]


def infer(op, node):
    # if not isinstance(node, DFEvalValue): return None
    if not isinstance(node, DFEvalValue):
        raise verror.FormatError('Can not infer the value from non DFEvalValue object')
    val = node.value
    funcname = 'op_' + op
    opfunc = getattr(this, funcname, op_None)
    return opfunc(val)


def op_LessThan(val):
    minval = 0
    maxval = val - 1
    if maxval < 0:
        minval = None
        maxval = None
    return InferredValue(minval, maxval)


def op_GreaterThan(val):
    minval = val + 1
    maxval = None
    return InferredValue(minval, maxval)


def op_LassEq(val):
    minval = 0
    maxval = val
    return InferredValue(minval, maxval)


def op_GreaterEq(val):
    minval = val
    maxval = None
    return InferredValue(minval, maxval)


def op_Eq(val):
    minval = val
    maxval = val
    return InferredValue(minval, maxval)


def op_NotEq(val):
    minval = val
    maxval = val
    return InferredValue(minval, maxval, inv=True)


def op_Eql(val):
    minval = val
    maxval = val
    return InferredValue(minval, maxval)


def op_NotEql(val):
    minval = val
    maxval = val
    return InferredValue(minval, maxval, inv=True)


def op_None(val):
    raise verror.FormatError('Unsupported Comparator')


class InferredValue(object):
    def __init__(self, minval, maxval, inv=False):
        self.minval = minval
        self.maxval = maxval
        self.inv = inv

    def __repr__(self):
        ret = ''
        if self.inv:
            ret += '(INV '
        ret += 'min:' + str(self.minval)
        ret += ' max:' + str(self.maxval)
        if self.inv:
            ret += ')'
        return ret

    def invert(self):
        self.inv = not self.inv
