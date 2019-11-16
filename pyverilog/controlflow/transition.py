# -------------------------------------------------------------------------------
# transition.py
#
# Splitting a tree into state part and transition condition part
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os

from pyverilog.dataflow.dataflow import *
import pyverilog.utils.util as util
import pyverilog.utils.signaltype as signaltype
import pyverilog.utils.inference as inference


def walkCondlist(condlist, termname, termwidth=32):
    node = None
    if len(condlist) == 0:
        maxvalue = util.maxValue(termwidth)
        return StateNode(maxvalue=maxvalue, isany=True)
    for cond in condlist:
        rslt = walkCond(cond, termname, termwidth)
        if node and rslt:
            node = andStateNodeList(node, rslt)
        elif rslt:
            node = rslt
    return node


def walkCond(cond, termname, termwidth=32):
    if isinstance(cond, DFOperator):
        if len(cond.nextnodes) == 1:
            return _walkCond_DFOperator_unary(cond, termname, termwidth)
        if len(cond.nextnodes) == 2:
            return _walkCond_DFOperator_dual(cond, termname, termwidth)
    if isinstance(cond, DFTerminal):
        comp_cond = DFOperator((cond, DFEvalValue(0)), 'GreaterThan')
        return _walkCond_DFOperator_dual(comp_cond, termname, termwidth)
    maxvalue = util.maxValue(termwidth)
    return StateNode(transcond=cond, maxvalue=maxvalue, isany=True)


def _walkCond_DFOperator_unary(cond, termname, termwidth=32):
    node = walkCond(cond.nextnodes[0], termname, termwidth)
    if signaltype.isNot(cond.operator):
        node = notStateNodeList(node)
    return node


def _walkCond_DFOperator_dual(cond, termname, termwidth=32):
    maxvalue = util.maxValue(termwidth)
    if signaltype.isNonConditionOp(cond.operator):
        return StateNode(transcond=cond, maxvalue=maxvalue, isany=True)

    if not signaltype.isCompare(cond.operator) and signaltype.isOr(cond.operator):
        lnode = walkCond(cond.nextnodes[0], termname, termwidth)
        rnode = walkCond(cond.nextnodes[1], termname, termwidth)
        ret = orStateNodeList(lnode, rnode)
        if ret:
            return ret
    if not signaltype.isCompare(cond.operator) and signaltype.isAnd(cond.operator):
        lnode = walkCond(cond.nextnodes[0], termname, termwidth)
        rnode = walkCond(cond.nextnodes[1], termname, termwidth)
        ret = andStateNodeList(lnode, rnode)
        if ret:
            return ret

    l = cond.nextnodes[0]
    r = cond.nextnodes[1]

    if isinstance(l, DFTerminal) and l.name == termname:
        infval = inference.infer(cond.operator, r)
        return createStateNode(infval, termwidth)
    if isinstance(r, DFTerminal) and r.name == termname:
        new_op = re.sub('Greater', 'TMP', cond.operator)
        new_op = re.sub('Less', 'Greater', new_op)
        new_op = re.sub('TMP', 'Less', new_op)
        infval = inference.infer(new_op, l)
        return createStateNode(infval, termwidth)

    maxvalue = util.maxValue(termwidth)
    return StateNode(transcond=cond, maxvalue=maxvalue, isany=True)


def notStateNodeList(node):
    if isStateNode(node):
        return notStateNode(node)
    if isStateNodeList(node):
        new_nodes = []
        for n in node.nodelist:
            new_nodes.append(notStateNode(n))
        ret_node = None
        for n in new_nodes:
            if ret_node is None:
                ret_node = n
            else:
                ret_node = andStateNodeList(ret_node, n)
        return ret_node
    return None


def orStateNodeList(lnode, rnode):
    if isStateNode(lnode) and isStateNode(rnode):
        return StateNodeList((lnode, rnode))
    if isStateNodeList(lnode) and isStateNodeList(rnode):
        new_list = []
        new_list.extend(lnode.nodelist)
        new_list.extend(rnode.nodelist)
        return StateNodeList(tuple(new_list))
    if isStateNodeList(lnode) and isStateNode(rnode):
        new_list = []
        new_list.extend(lnode.nodelist)
        new_list.append(rnode)
        return StateNodeList(tuple(new_list))
    if isStateNode(lnode) and isStateNodeList(rnode):
        new_list = []
        new_list.append(lnode)
        new_list.extend(rnode.nodelist)
        return StateNodeList(tuple(new_list))
    return None


def andStateNodeList(lnode, rnode):
    if lnode is None and rnode is None:
        return None
    if lnode is None:
        return rnode
    if rnode is None:
        return lnode

    if isStateNode(lnode) and isStateNode(rnode):
        return andStateNode(lnode, rnode)
    if isStateNodeList(lnode) and isStateNodeList(rnode):
        new_list = []
        for l in lnode.nodelist:
            for r in rnode.nodelist:
                val = andStateNode(l, r)
                if val:
                    new_list.append(val)
        if len(new_list) == 0:
            return None
        return StateNodeList(tuple(new_list))
    if isStateNodeList(lnode) and isStateNode(rnode):
        new_list = []
        for l in lnode.nodelist:
            val = andStateNode(l, rnode)
            if val:
                new_list.append(val)
        if len(new_list) == 0:
            return None
        return StateNodeList(tuple(new_list))
    if isStateNode(lnode) and isStateNodeList(rnode):
        new_list = []
        for r in rnode.nodelist:
            val = andStateNode(lnode, r)
            if val:
                new_list.append(val)
        if len(new_list) == 0:
            return None
        return StateNodeList(tuple(new_list))
    return None


def notStateNode(node):
    if node.isany:
        new_transcond = _not_transcond(node.transcond)
        return StateNode(transcond=new_transcond, maxvalue=node.maxvalue, isany=True)
    new_range_pairs = _not_range_pairs(node)
    a = StateNode(range_pairs=new_range_pairs, maxvalue=node.maxvalue)
    if node.transcond is None:
        return a
    new_transcond = _not_transcond(node.transcond)
    b = StateNode(range_pairs=node.range_pairs, transcond=new_transcond, maxvalue=node.maxvalue)
    return StateNodeList((a, b))


def andStateNode(sna, snb):
    if sna is None and snb is None:
        return None
    if sna is None:
        return snb
    if snb is None:
        return sna

    isany = False
    range_pairs = []
    if sna.isany and snb.isany:
        isany = True
    elif sna.isany:
        range_pairs = snb.range_pairs
    elif snb.isany:
        range_pairs = sna.range_pairs
    elif len(sna.range_pairs) > 0 and len(snb.range_pairs) > 0:
        range_pairs = _and_range_pairs(sna, snb)

    if (not isany) and len(range_pairs) == 0:
        return None

    transcond = None
    if isinstance(sna.transcond, DFNode) and isinstance(snb.transcond, DFNode):
        transcond = DFOperator((sna.transcond, snb.transcond), 'Land')
    elif isinstance(sna.transcond, DFNode):
        transcond = sna.transcond
    elif isinstance(snb.transcond, DFNode):
        transcond = snb.transcond

    maxvalue = max(sna.maxvalue, snb.maxvalue)
    return StateNode(tuple(range_pairs), maxvalue=maxvalue, transcond=transcond, isany=isany)


def _and_range_pairs(sna, snb):
    range_pairs = []
    a_ptr = 0
    b_ptr = 0
    sorted_sna = sorted(sna.range_pairs, key=lambda x: x[0])
    sorted_snb = sorted(snb.range_pairs, key=lambda x: x[0])
    amin, amax = sorted_sna[a_ptr]
    bmin, bmax = sorted_snb[b_ptr]
    last_a_ptr = -1
    last_b_ptr = -1
    while True:
        next_min = max(amin, bmin)
        next_max = min(amax, bmax)
        if bmax < amin or bmin > amax:
            pass
        else:
            range_pairs.append((next_min, next_max))
        if amax >= bmax and b_ptr < len(sorted_snb) - 1:
            b_ptr += 1
            bmin, bmax = sorted_snb[b_ptr]
        elif amax <= bmax and a_ptr < len(sorted_sna) - 1:
            a_ptr += 1
            amin, amax = sorted_sna[a_ptr]
        if a_ptr == last_a_ptr and b_ptr == last_b_ptr:
            break
        last_a_ptr = a_ptr
        last_b_ptr = b_ptr
    ret_set = set(range_pairs)
    ret_list = list(ret_set)
    return ret_list


def _not_range_pairs(node):
    new_range_pairs = []
    cur_min = node.minvalue
    for rmin, rmax in sorted(node.range_pairs, key=lambda x: x[0]):
        if rmin - 1 >= cur_min:
            new_range_pairs.append((cur_min, rmin - 1))
        cur_min = max(rmax + 1, cur_min)
    if cur_min <= node.maxvalue:
        new_range_pairs.append((cur_min, node.maxvalue))
    return new_range_pairs


def _not_transcond(transcond):
    if transcond is None:
        return None
    elif isinstance(transcond, DFOperator) and transcond.operator == 'Ulnot':
        return transcond.nextnodes[0]
    elif isinstance(transcond, DFOperator) and transcond.operator == 'Unot':
        return transcond.nextnodes[0]
    return DFOperator((transcond,), 'Ulnot')


def createStateNode(infval, width):
    statelabels = []
    minval = infval.minval
    maxval = infval.maxval
    if minval is None:
        minval = 0
    if maxval is None:
        maxval = util.maxValue(width)
    ret = StateNode(((minval, maxval),), 0, util.maxValue(width), None)
    if infval.inv:
        ret = notStateNodeList(ret)
    return ret


def isStateNode(node):
    return isinstance(node, StateNode)


def isStateNodeList(node):
    return isinstance(node, StateNodeList)


class StateNode(object):
    def __init__(self, range_pairs=(), minvalue=0, maxvalue=0, transcond=None, isany=False):
        self.range_pairs = range_pairs
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        self.transcond = transcond
        self.isany = isany

    def __repr__(self):
        ret = 'state:'
        for r in self.range_pairs:
            ret += str(r) + ' '
        if self.isany:
            ret += 'any '
        ret = ret[:-1]
        ret += ', cond:'
        if isinstance(self.transcond, DFNode):
            ret += self.transcond.tocode()
        else:
            ret += str(self.transcond)
        return ret


class StateNodeList(object):
    def __init__(self, nodelist=()):
        self.nodelist = nodelist

    def __repr__(self):
        ret = '('
        for n in self.nodelist:
            ret += n.__repr__() + ' '
        return ret[:-1] + ')'
