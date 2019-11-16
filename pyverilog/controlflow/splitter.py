# -------------------------------------------------------------------------------
# splitter.py
#
# Splitting a definition tree into condition part and function part
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os

import pyverilog.utils.signaltype as signaltype
from pyverilog.dataflow.dataflow import *


def split(tree):
    funcdict = {}  # key:condition list, value:function
    if isinstance(tree, DFBranch):
        truefuncs = split(tree.truenode)
        truecond = tree.condnode
        if len(truefuncs) > 0:
            for cond, func in truefuncs.items():
                funcdict[(truecond,) + cond] = func
        else:
            if tree.truenode is not None:
                funcdict[(truecond,)] = tree.truenode
        falsefuncs = split(tree.falsenode)
        falsecond = DFOperator((tree.condnode,), 'Ulnot')
        if len(falsefuncs) > 0:
            for cond, func in falsefuncs.items():
                funcdict[(falsecond,) + cond] = func
        else:
            if tree.falsenode is not None:
                funcdict[(falsecond,)] = tree.falsenode
    return funcdict


def remove_reset_condition(funcdict):
    new_funcdict = {}
    for _condlist, func in funcdict.items():
        condlist = remove_reset_condlist(_condlist)
        new_funcdict[condlist] = func
    if () in new_funcdict and len(new_funcdict) > 1:
        del new_funcdict[()]
    return new_funcdict


def remove_reset_condlist(condlist):
    new_condlist = []
    for cond in condlist:
        r = _remove_reset_cond(cond)
        if r:
            new_condlist.append(r)
    return tuple(new_condlist)


def _remove_reset_cond(cond):
    condstr = cond.tostr()
    if signaltype.isReset(condstr):
        return None
    return cond


def active_constant(termname, node, op='>', value=0):
    if not isinstance(node, DFEvalValue):
        return False
    if not eval(str(node.value) + op + str(value)):
        return False
    return True


def active_modify(termname, node):
    if isinstance(node, DFTerminal) and node.name == termname:
        return False
    return True


def active_unmodify(termname, node):
    if isinstance(node, DFTerminal) and node.name == termname:
        return True
    return False


def filter(funcdict, termname, condition=active_constant):
    ret_funcdict = {}
    for condlist, func in funcdict.items():
        if not condition(termname, func):
            continue
        ret_funcdict[condlist] = func
    return ret_funcdict
