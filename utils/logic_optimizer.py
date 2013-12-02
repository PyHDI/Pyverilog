#-------------------------------------------------------------------------------
# logic_optimizer.py
#
# logic optimizer by Quine-McCluskey algorithm
# the input tree is converted into Disjunctive Normal Form (DNF)
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

if sys.version_info[0] >= 3:
    import pyverilog.utils.signaltype as signaltype
    from pyverilog.utils.dataflow import *
else:
    import signaltype
    from dataflow import *

def logic_optimize(tree):
    if not isinstance(tree, DFOperator): return tree
    if not signaltype.isOr(tree.operator): return tree
    dnf = toDNF(tree)

def toDNF(tree):
    # ( ((True, n0), (False, n1), ... ), ((True, n10), (False, n11), ... ), ... )
    dnf = []
    orlist = toOrList(tree)
    for item in orlist:
        andlist = toAndList(item)
        dnf.append(andlist)
    return tuple(dnf)

def toOrList(tree):
    # ( n0, n1, ... )
    if not isinstance(tree, DFOperator): return (tree,)
    if not signaltype.isOr(tree.operator): return (tree,)
    return toOrList(tree.nextnodes[0]) + toOrList(tree.nextnodes[1])

def toAndList(item):
    # ((True, n0), (False, n1), ... )
    if not isinstance(item, DFOperator):
        return ((True, item),)
    if signaltype.isAnd(item.operator):
        ret = []
        for n in sorted(item.nextnodes, key=lambda x:str(x)):
            ret.extend(toAndList(n))
        return tuple(sorted(ret, key=lambda x:str(x[1])))
    if signaltype.isNot(item.operator):
        terms = toAndList(item.nextnodes[0])
        ret = []
        for nbool, node in terms:
            ret.append( (not nbool, node) )
        return tuple(ret)
    return ((True, item),)

def reduce(left, right):
    left_term_set = set(map(lambda x:x[1], left))
    right_term_set = set(map(lambda x:x[1], right))
    left_bool_set = set(map(lambda x:x[0], left))
    right_bool_set = set(map(lambda x:x[0], right))
    if left_term_set == right_term_set:
        if left_bool_set == right_bool_set: return left
        ret_term_set = set([])
        ret_bool_set = set([])
        for p in range(len(left_bool_set)):
            if left_bool_set[p] == rigth_bool_set[p]:
                ret_bool_set.add( left_bool_set[p] )
                ret_term_set.add( left_term_set[p] )
