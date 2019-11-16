# -------------------------------------------------------------------------------
# reorder.py
#
# Reorders DFNode trees in order of DFBranch, DFOperator, and DFTerminal
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import copy

from pyverilog.dataflow.dataflow import *


def reorder(tree):
    if tree is None:
        return None
    if isinstance(tree, DFConstant):
        return tree
    if isinstance(tree, DFTerminal):
        return tree
    if isinstance(tree, DFEvalValue):
        return tree
    if isinstance(tree, DFUndefined):
        return tree
    if isinstance(tree, DFHighImpedance):
        return tree

    if isinstance(tree, DFBranch):
        truenode = reorder(tree.truenode)
        falsenode = reorder(tree.falsenode)
        condnode = reorder(tree.condnode)
        if isinstance(condnode, DFBranch):
            return insertBranch(condnode, truenode, falsenode)
        return DFBranch(condnode, truenode, falsenode)

    if isinstance(tree, DFOperator):
        resolvednodes = []
        for n in tree.nextnodes:
            resolvednodes.append(reorder(n))
        for r in resolvednodes:
            if isinstance(r, DFBranch):
                return insertOpList(resolvednodes, tree.operator)
        return DFOperator(tuple(resolvednodes), tree.operator)

    if isinstance(tree, DFConcat):
        resolvednodes = []
        for n in tree.nextnodes:
            resolvednodes.append(reorder(n))
        for r in resolvednodes:
            if isinstance(r, DFBranch):
                return insertConcat(resolvednodes)
        return DFConcat(tuple(resolvednodes))

    if isinstance(tree, DFPartselect):
        resolved_msb = reorder(tree.msb)
        resolved_lsb = reorder(tree.lsb)
        resolved_var = reorder(tree.var)
        if isinstance(resolved_msb, DFBranch) or isinstance(resolved_lsb, DFBranch):
            raise FormatError('MSB and LSB should not be DFBranch')
        if isinstance(resolved_var, DFBranch):
            return insertPartselect(resolved_var, resolved_msb, resolved_lsb)
        return DFPartselect(resolved_var, resolved_msb, resolved_lsb)

    if isinstance(tree, DFPointer):
        resolved_ptr = reorder(tree.ptr)
        resolved_var = reorder(tree.var)
        if isinstance(resolved_ptr, DFBranch):
            # raise FormatError('PTR should not be DFBranch')n
            return DFBranch(resolved_ptr.condnode,
                            reorder(DFPointer(resolved_var, resolved_ptr.truenode)),
                            reorder(DFPointer(resolved_var, resolved_ptr.falsenode)))
        if isinstance(resolved_var, DFBranch):
            return insertPointer(resolved_var, resolved_ptr)
        return DFPointer(resolved_var, resolved_ptr)

    if isinstance(tree, DFDelay):
        return DFDelay(reorder(tree.nextnode))

    raise DefinitionError('Undefined DFNode type: %s %s' % (str(type(tree)), str(tree)))

############################################################################


def insertBranch(base, truenode, falsenode):
    if isinstance(base, DFBranch):
        return DFBranch(base.condnode, insertBranch(base.truenode, truenode, falsenode), insertBranch(base.falsenode, truenode, falsenode))
    return DFBranch(base, truenode, falsenode)


def insertUnaryOp(base, op):
    if isinstance(base, DFBranch):
        return DFBranch(base.condnode, insertUnaryOp(base.truenode, op), insertUnaryOp(base.falsenode, op))
    return DFOperator((base,), op)


def insertOp(left, right, op):
    if isinstance(left, DFBranch):
        return DFBranch(left.condnode, insertOp(left.truenode, right, op), insertOp(left.falsenode, right, op))
    elif isinstance(right, DFBranch):
        return DFBranch(right.condnode, insertOp(left, right.truenode, op), insertOp(left, right.falsenode, op))
    return DFOperator((left, right), op)


def insertOpList(nextnodes, op):
    donenodes = []
    restnodes = list(nextnodes)
    for n in nextnodes:
        restnodes.pop(0)
        if isinstance(n, DFBranch):
            return DFBranch(n.condnode, insertOpList(tuple(donenodes + [n.truenode, ] + restnodes), op), insertOpList(tuple(donenodes + [n.falsenode, ] + restnodes), op))
        donenodes.append(n)
    return DFOperator(nextnodes, op)


def insertConcat(nextnodes):
    donenodes = []
    restnodes = list(nextnodes)
    for n in nextnodes:
        restnodes.pop(0)
        if isinstance(n, DFBranch):
            return DFBranch(n.condnode, insertConcat(tuple(donenodes + [n.truenode, ] + restnodes)), insertConcat(tuple(donenodes + [n.falsenode, ] + restnodes)))
        donenodes.append(n)
    return DFConcat(nextnodes)


def insertPartselect(var, msb, lsb):
    if isinstance(var, DFBranch):
        return DFBranch(var.condnode, insertPartselect(var.truenode, msb, lsb), insertPartselect(var.falsenode, msb, lsb))
    if var is None:
        return None
    return DFPartselect(var, msb, lsb)


def insertPointer(var, ptr):
    if isinstance(var, DFBranch):
        return DFBranch(var.condnode, insertPointer(var.truenode, ptr), insertPointer(var.falsenode, ptr))
    if var is None:
        return None
    return DFPointer(var, ptr)
