# -------------------------------------------------------------------------------
# walker.py
#
# Dataflow graph walker
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os

import pyverilog.utils.util as util
import pyverilog.utils.verror as verror
import pyverilog.utils.signaltype as signaltype
import pyverilog.dataflow.replace as replace
from pyverilog.dataflow.dataflow import *
from pyverilog.dataflow.visit import *
from pyverilog.dataflow.merge import VerilogDataflowMerge


class VerilogDataflowWalker(VerilogDataflowMerge):
    def __init__(self, topmodule, terms, binddict, resolved_terms, resolved_binddict, constlist):
        VerilogDataflowMerge.__init__(self, topmodule, terms, binddict,
                                      resolved_terms, resolved_binddict, constlist)

    def walkBind(self, name, step=0):
        termname = util.toTermname(name)
        if not termname in self.terms:
            raise verror.DefinitionError('No such signals: %s' % str(name))
        tree = self.getTree(termname)
        walked_tree = self.walkTree(tree, visited=set(), step=step)
        return replace.replaceUndefined(walked_tree, termname)

    def walkTree(self, tree, visited=set([]), step=0, delay=False, msb=None, lsb=None, ptr=None):
        if tree is None:
            return DFUndefined(32)

        if isinstance(tree, DFUndefined):
            return tree

        if isinstance(tree, DFHighImpedance):
            return tree

        if isinstance(tree, DFConstant):
            return tree

        if isinstance(tree, DFEvalValue):
            return tree

        if isinstance(tree, DFTerminal):
            scope = util.getScope(tree.name)
            termname = tree.name
            if termname in visited:
                return tree

            termtype = self.getTermtype(termname)
            if util.isTopmodule(scope) and signaltype.isInput(termtype):
                return tree

            nptr = None
            if self.getTermDims(termname) is not None:
                if ptr is None:
                    raise verror.FormatError('Array variable requires an pointer.')
                if msb is not None and lsb is not None:
                    return tree
                nptr = ptr

            nextstep = step
            if signaltype.isReg(termtype):
                if (not self.isCombination(termname) and
                    not signaltype.isRename(termtype) and
                        nextstep == 0):
                    return tree
                if (not self.isCombination(termname)
                        and not signaltype.isRename(termtype)):
                    nextstep -= 1

            return self.walkTree(self.getTree(termname, nptr),
                                 visited | set([termname, ]), nextstep, delay)

        if isinstance(tree, DFBranch):
            condnode = self.walkTree(tree.condnode, visited, step, delay)
            truenode = self.walkTree(tree.truenode, visited, step, delay)
            falsenode = self.walkTree(tree.falsenode, visited, step, delay)
            return DFBranch(condnode, truenode, falsenode)

        if isinstance(tree, DFOperator):
            nextnodes = []
            for n in tree.nextnodes:
                nextnodes.append(self.walkTree(n, visited, step, delay))
            return DFOperator(tuple(nextnodes), tree.operator)

        if isinstance(tree, DFPartselect):
            msb = self.walkTree(tree.msb, visited, step, delay)
            lsb = self.walkTree(tree.lsb, visited, step, delay)
            var = self.walkTree(tree.var, visited, step, delay, msb=msb, lsb=lsb)
            if isinstance(var, DFPartselect):
                child_lsb = self.getTerm(str(tree.var)).lsb.eval()
                return DFPartselect(var.var, DFIntConst(str(msb.eval() + var.lsb.eval() - child_lsb)),
                                    DFIntConst(str(lsb.eval() + var.lsb.eval() - child_lsb)))
            return DFPartselect(var, msb, lsb)

        if isinstance(tree, DFPointer):
            ptr = self.walkTree(tree.ptr, visited, step, delay)
            var = self.walkTree(tree.var, visited, step, delay, ptr=ptr)
            if isinstance(tree.var, DFTerminal):
                if (self.getTermDims(tree.var.name) is not None and
                        not (isinstance(var, DFTerminal) and var.name == tree.var.name)):
                    return var
            return DFPointer(var, ptr)

        if isinstance(tree, DFConcat):
            nextnodes = []
            for n in tree.nextnodes:
                nextnodes.append(self.walkTree(n, visited, step, delay))
            return DFConcat(tuple(nextnodes))

        raise verror.DefinitionError(
            'Undefined Node Type: %s : %s' % (str(type(tree)), str(tree)))
