# -------------------------------------------------------------------------------
# merge.py
#
# Merging multiple dataflow definitions into a single dataflow definition
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os

import pyverilog.utils.verror as verror
import pyverilog.utils.signaltype as signaltype
import pyverilog.dataflow.reorder as reorder
from pyverilog.dataflow.dataflow import *
from pyverilog.dataflow.visit import *
from pyverilog.dataflow.optimizer import VerilogOptimizer


class VerilogDataflowMerge(object):
    def __init__(self, topmodule, terms, binddict, resolved_terms, resolved_binddict, constlist):
        self.topmodule = topmodule
        self.terms = terms
        self.binddict = binddict
        self.resolved_terms = resolved_terms
        self.resolved_binddict = resolved_binddict
        self.constlist = constlist
        self.optimizer = VerilogOptimizer(terms, constlist)

    def getTerm(self, termname):
        if isinstance(termname, str):
            for scope in self.terms.keys():
                if termname == str(scope):
                    return self.terms[scope]
        if not termname in self.terms:
            return None
        return self.terms[termname]

    def getBindlist(self, termname):
        if not termname in self.binddict:
            return ()
        return self.binddict[termname]

    def getResolvedTerm(self, termname):
        if not termname in self.resolved_terms:
            return None
        return self.resolved_terms[termname]

    def getResolvedBindlist(self, termname):
        if not termname in self.resolved_binddict:
            return ()
        return self.resolved_binddict[termname]

    def getTermtype(self, termname):
        term = self.getTerm(termname)
        if term is None:
            raise verror.DefinitionError('No such Term: %s' % termname)
        return term.termtype

    def getTermDims(self, termname):
        term = self.getTerm(termname)
        if term is None:
            raise verror.DefinitionError('No such Term: %s' % termname)
        return term.dims

    def getAssignType(self, termname, bind):
        termtype = self.getTermtype(termname)
        if signaltype.isWire(termtype):
            return 'assign'
        if signaltype.isWireArray(termtype):
            return 'assign'
        if signaltype.isReg(termtype):
            if bind.isClockEdge():
                return 'clockedge'
            return 'combination'
        if signaltype.isInteger(termtype):
            if bind.isClockEdge():
                return 'clockedge'
            return 'combination'
        if signaltype.isParameter(termtype):
            return 'parameter'
        if signaltype.isLocalparam(termtype):
            return 'localparam'
        if signaltype.isOutput(termtype):
            return 'assign'
        if signaltype.isInout(termtype):
            return 'assign'
        if signaltype.isInput(termtype):
            return 'assign'
        if signaltype.isFunction(termtype):
            return 'assign'
        if signaltype.isRename(termtype):
            return 'assign'
        if signaltype.isGenvar(termtype):
            return 'genvar'
        raise verror.DefinitionError('Unexpected Assignment Type: %s : %s' %
                                     (str(termname), str(termtype)))

    def isCombination(self, termname):
        bindlist = self.getBindlist(termname)
        if bindlist is None:
            return False
        for bind in bindlist:
            if bind.isCombination():
                return True
        return False

    def getTree(self, termname, ptr=None):
        bindlist = self.getResolvedBindlist(termname)
        bindlist = self.getOptimizedBindlist(bindlist)
        if bindlist is None:
            return None
        if len(bindlist) == 0:
            return None

        if self.getTermDims(termname) is not None:
            discretebinds = {}
            for bind in bindlist:
                if isinstance(bind.ptr, DFEvalValue):
                    ptrval = bind.ptr.value
                    if not ptrval in discretebinds:
                        discretebinds[ptrval] = []
                    discretebinds[ptrval] += [bind]
                else:
                    if not 'any' in discretebinds:
                        discretebinds['any'] = []
                    discretebinds['any'] += [bind]

            if 'any' in discretebinds:
                return DFTerminal(termname)

            if isinstance(ptr, DFEvalValue):
                if len(discretebinds[ptr.value]) == 0:
                    return None
                if len(discretebinds[ptr.value]) == 1:
                    return discretebinds[ptr.value][0].tree
                return self.getMergedTree(discretebinds[ptr.value])

            minptr = min(list(discretebinds.keys()))
            maxptr = max(list(discretebinds.keys()))
            ret = None
            for c in range(minptr, maxptr + 1):
                truetree = None
                if len(discretebinds[c]) == 0:
                    continue
                if len(discretebinds[c]) == 1:
                    truetree = discretebinds[c][0].tree
                else:
                    truetree = self.getMergedTree(discretebinds[c])
                ret = DFBranch(DFOperator((DFEvalValue(c), ptr), 'Eq'), truetree, ret)
            return ret

        if len(bindlist) == 1:
            return bindlist[0].tree
        new_tree = self.getMergedTree(bindlist)
        return self.optimizer.optimize(new_tree)

    def getResolvedTree(self, termname, ptr=None):
        raise verror.ImplementationError()

    def isClockEdge(self, termname, msb=None, lsb=None, ptr=None):
        bind = self.binddict[termname]
        return bind[0].isClockEdge()

    def getSources(self, tree):
        if tree is None:
            return set()
        if isinstance(tree, DFConstant):
            return set()
        if isinstance(tree, DFUndefined):
            return set()
        if isinstance(tree, DFEvalValue):
            return set()
        if isinstance(tree, DFTerminal):
            return set([tree.name, ])
        if isinstance(tree, DFBranch):
            ret = set()
            ret |= self.getSources(tree.condnode)
            ret |= self.getSources(tree.truenode)
            ret |= self.getSources(tree.falsenode)
            return ret
        if isinstance(tree, DFOperator):
            nextnodes = []
            for n in tree.nextnodes:
                nextnodes.extend(self.getSources(n))
            return set(nextnodes)
        if isinstance(tree, DFPartselect):
            ret = set()
            ret |= self.getSources(tree.var)
            ret |= self.getSources(tree.msb)
            ret |= self.getSources(tree.lsb)
            return ret
        if isinstance(tree, DFPointer):
            ret = set()
            ret |= self.getSources(tree.var)
            ret |= self.getSources(tree.ptr)
            return ret
        if isinstance(tree, DFConcat):
            nextnodes = []
            for n in tree.nextnodes:
                nextnodes.extend(self.getSources(n))
            return set(nextnodes)
        if isinstance(tree, DFDelay):
            ret = set()
            ret |= self.getSources(tree.nextnode)
            return ret
        raise verror.DefinitionError('Undefined Node Type: %s : %s' % (str(type(tree)), str(tree)))

    def getBindSources(self, termname):
        sources = set()
        sources |= self.getTermSources(termname)
        sources |= self.getBindinfoSources(termname)
        return sources

    def getTermSources(self, termname):
        term = self.getTerm(termname)
        if term is None:
            return set()
        sources = set()
        sources |= self.getTreeSources(term.msb)
        sources |= self.getTreeSources(term.lsb)
        if term.dims is not None:
            for l, r in term.dims:
                sources |= self.getTreeSources(l)
                sources |= self.getTreeSources(r)
        return sources

    def getBindinfoSources(self, termname):
        bindlist = self.getBindlist(termname)
        sources = set()
        for bind in bindlist:
            sources |= self.getTreeSources(bind.msb)
            sources |= self.getTreeSources(bind.lsb)
            sources |= self.getTreeSources(bind.ptr)
            sources |= self.getTreeSources(bind.tree)
        return sources

    def getTreeSources(self, tree):
        if tree is None:
            return set()
        if isinstance(tree, DFConstant):
            return set()
        if isinstance(tree, DFUndefined):
            return set()
        if isinstance(tree, DFEvalValue):
            return set()
        if isinstance(tree, DFTerminal):
            return set([tree.name, ])
        if isinstance(tree, DFBranch):
            ret = set()
            ret |= self.getTreeSources(tree.condnode)
            ret |= self.getTreeSources(tree.truenode)
            ret |= self.getTreeSources(tree.falsenode)
            return ret
        if isinstance(tree, DFOperator):
            ret = set()
            for n in tree.nextnodes:
                ret |= self.getTreeSources(n)
            return ret
        if isinstance(tree, DFPartselect):
            ret = set()
            ret |= self.getTreeSources(tree.var)
            ret |= self.getTreeSources(tree.msb)
            ret |= self.getTreeSources(tree.lsb)
            return ret
        if isinstance(tree, DFPointer):
            ret = set()
            ret |= self.getTreeSources(tree.var)
            ret |= self.getTreeSources(tree.ptr)
            return ret
        if isinstance(tree, DFConcat):
            ret = set()
            for n in tree.nextnodes:
                ret |= self.getTreeSources(n)
            return ret
        raise verror.DefinitionError('Undefined Node Type: %s : %s' % (str(type(tree)), str(tree)))

    def getMergedTree(self, optimized_bindlist):
        concatlist = []
        last_msb = -1
        last_ptr = -1

        def bindkey(x):
            lsb = 0 if x.lsb is None else x.lsb.value
            ptr = 0 if not isinstance(x.ptr, DFEvalValue) else x.ptr.value
            term = self.getTerm(x.dest)
            length = abs(self.optimizer.optimize(term.msb).value -
                         self.optimizer.optimize(term.lsb).value) + 1
            return ptr * length + lsb
        for bind in sorted(optimized_bindlist, key=bindkey):
            lsb = 0 if bind.lsb is None else bind.lsb.value
            if last_ptr != (-1 if not isinstance(bind.ptr, DFEvalValue) else bind.ptr.value):
                continue
            if last_msb + 1 < lsb:
                concatlist.append(DFUndefined(last_msb - lsb - 1))
            concatlist.append(bind.tree)
            last_msb = -1 if bind.msb is None else bind.msb.value
            last_ptr = -1 if not isinstance(bind.ptr, DFEvalValue) else bind.ptr.value
        return DFConcat(tuple(reversed(concatlist)))

    def getOptimizedBindlist(self, bindlist):
        if len(bindlist) == 0:
            return ()
        new_bindlist = []
        for bind in bindlist:
            tree = self.optimizer.optimize(bind.tree)
            msb = self.optimizer.optimize(bind.msb)
            lsb = self.optimizer.optimize(bind.lsb)
            ptr = self.optimizer.optimize(bind.ptr)
            new_bind = copy.deepcopy(bind)
            new_bind.tree = tree
            new_bind.msb = msb
            new_bind.lsb = lsb
            new_bind.ptr = ptr
            new_bindlist.append(new_bind)
        if len(new_bindlist) == 1:
            return (new_bindlist[0],)
        split_positions = self.splitPositions(tuple(new_bindlist))
        new_bindlist = self.splitBindlist(tuple(new_bindlist), split_positions)
        return self.mergeBindlist(tuple(new_bindlist))

    def mergeBindlist(self, bindlist):
        merged_bindlist = []
        last_bind = None

        def bindkey(x):
            lsb = 0 if x.lsb is None else x.lsb.value
            ptr = 0 if not isinstance(x.ptr, DFEvalValue) else x.ptr.value
            term = self.getTerm(x.dest)
            length = abs(self.optimizer.optimize(term.msb).value -
                         self.optimizer.optimize(term.lsb).value) + 1
            return ptr * length + lsb

        for bind in sorted(bindlist, key=bindkey):
            if last_bind is None:
                merged_bindlist.append(copy.deepcopy(bind))
                last_bind = copy.deepcopy(bind)
            elif isinstance(last_bind.ptr, DFEvalValue) and isinstance(bind.ptr, DFEvalValue) and last_bind.ptr.value != bind.ptr.value:
                merged_bindlist.append(copy.deepcopy(bind))
                last_bind = copy.deepcopy(bind)
            elif last_bind.lsb is None or bind.lsb is None or last_bind is None or bind.msb is None:
                merged_bindlist.append(copy.deepcopy(bind))
                last_bind = copy.deepcopy(bind)
            elif last_bind.lsb.value == bind.lsb.value and last_bind.msb.value == bind.msb.value:
                new_tree = self.mergeTree(last_bind.tree, bind.tree)
                new_tree = self.optimizer.optimize(new_tree)
                merged_bindlist.pop()
                new_bind = copy.deepcopy(bind)
                new_bind.tree = new_tree
                merged_bindlist.append(new_bind)
                last_bind = copy.deepcopy(new_bind)
            else:
                merged_bindlist.append(copy.deepcopy(bind))
                last_bind = copy.deepcopy(bind)
        return tuple(merged_bindlist)

    def mergeTree(self, first, second):
        if isinstance(first, DFBranch) and isinstance(second, DFBranch):
            cond_fst = self.optimizer.optimize(first.condnode)
            cond_snd = self.optimizer.optimize(second.condnode)
            if cond_fst == cond_snd:
                return DFBranch(cond_fst, self.mergeTree(first.truenode, second.truenode), self.mergeTree(first.falsenode, second.falsenode))
            appended = copy.deepcopy(first)
            return DFBranch(cond_snd, self.appendTail(appended, second.truenode), self.appendTail(appended, second.falsenode))

        if first is not None and second is None:
            return first
        if first is None and second is not None:
            return second

        if isinstance(first, DFBranch) and second is None:
            return first
        if first is None and isinstance(second, DFBranch):
            return second

        if isinstance(first, DFBranch) and not isinstance(second, DFBranch):
            cond_fst = self.optimizer.optimize(first.condnode)
            appended = copy.deepcopy(second)
            return DFBranch(cond_fst, self.appendTail(appended, first.truenode), self.appendTail(appended, first.falsenode))
        if not isinstance(first, DFBranch) and isinstance(second, DFBranch):
            cond_snd = self.optimizer.optimize(second.condnode)
            appended = copy.deepcopy(first)
            return DFBranch(cond_snd, self.appendTail(appended, second.truenode), self.appendTail(appended, second.falsenode))

        if not isinstance(first, DFBranch) and not isinstance(second, DFBranch):
            return second

        raise verror.FormatError('Can not merge trees.')

    def appendTail(self, appended, target):
        if target is None:
            return copy.deepcopy(appended)
        if isinstance(target, DFBranch):
            return DFBranch(target.condnode, self.appendTail(appended, target.truenode), self.appendTail(appended, target.falsenode))
        return target

    def splitBindlist(self, bindlist, split_positions):
        if len(bindlist) == 0:
            return ()
        return self.splitBindPositions(bindlist[0], split_positions) + self.splitBindlist(bindlist[1:], split_positions)

    def splitBindPositions(self, bind, split_positions):
        if len(split_positions) == 0:
            return (copy.deepcopy(bind),)
        if bind is None:
            return (copy.deepcopy(bind),)
        bind_left, bind_right = self.splitBind(bind, split_positions[0])
        ret = () if bind_right is None else (bind_right,)
        return ret + self.splitBindPositions(bind_left, split_positions[1:])

    def splitBind(self, bind, splitpos):
        tree = bind.tree
        msb = self.optimizer.optimizeConstant(bind.msb)
        lsb = self.optimizer.optimizeConstant(bind.lsb)
        ptr = self.optimizer.optimizeConstant(bind.ptr)
        if ptr is not None and msb is None or lsb is None:
            if self.getTermDims(bind.dest) is not None:
                msb = self.optimizer.optimizeConstant(copy.deepcopy(term.msb))
                lsb = self.optimizer.optimizeConstant(copy.deepcopy(term.lsb))
            else:
                msb = copy.deepcopy(ptr)
                lsb = copy.deepcopy(ptr)
        if ptr is None and msb is None or lsb is None:
            term = self.getTerm(bind.dest)
            msb = self.optimizer.optimizeConstant(copy.deepcopy(term.msb))
            lsb = self.optimizer.optimizeConstant(copy.deepcopy(term.lsb))
        if splitpos > lsb.value and splitpos <= msb.value:  # split
            right_lsb = lsb.value
            right_msb = splitpos - 1
            right_width = splitpos - lsb.value
            left_lsb = splitpos
            left_msb = msb.value
            left_width = msb.value - splitpos + 1
            right_tree = reorder.reorder(DFPartselect(copy.deepcopy(
                tree), DFEvalValue(right_width - 1), DFEvalValue(0)))
            left_tree = reorder.reorder(DFPartselect(copy.deepcopy(tree), DFEvalValue(
                msb.value), DFEvalValue(msb.value - left_width + 1)))
            right_tree = self.optimizer.optimize(right_tree)
            left_tree = self.optimizer.optimize(left_tree)
            left_bind = copy.deepcopy(bind)
            left_bind.tree = left_tree
            left_bind.msb = DFEvalValue(left_msb)
            left_bind.lsb = DFEvalValue(left_lsb)
            right_bind = copy.deepcopy(bind)
            right_bind.tree = right_tree
            right_bind.msb = DFEvalValue(right_msb)
            right_bind.lsb = DFEvalValue(right_lsb)
            return left_bind, right_bind
        return bind, None

    def splitPositions(self, bindlist):
        split_positions = set([])
        assigned_range = []  # (msb, lsb, ptr)

        for bind in bindlist:
            ptr = self.optimizer.optimizeConstant(bind.ptr)
            msb = self.optimizer.optimizeConstant(bind.msb)
            lsb = self.optimizer.optimizeConstant(bind.lsb)
            if msb is None and lsb is None:
                term = self.getTerm(bind.dest)
                msb = self.optimizer.optimizeConstant(term.msb)
                lsb = self.optimizer.optimizeConstant(term.lsb)
            elif not isinstance(msb, DFEvalValue) or not isinstance(lsb, DFEvalValue):
                raise FormatError('MSB and LSB should be constant.')

            if ptr is None or isinstance(ptr, DFEvalValue):
                ptrval = None if ptr is None else ptr.value
                matched_range = self.matchedRange(
                    tuple(assigned_range), msb.value, lsb.value, ptrval)
                unmatched_range = self.unmatchedRange(
                    tuple(matched_range), msb.value, lsb.value, ptrval)
                split_positions |= self.getPositionsFromRange(matched_range, ptrval)
                assigned_range += matched_range + unmatched_range

        return tuple(sorted(list(split_positions)))

    def getPositionsFromRange(self, matched_range, search_ptr):
        positions = set([])
        for msb, lsb, ptr in matched_range:
            if search_ptr is not None and search != ptr:
                continue
            positions.add(lsb)
            positions.add(msb + 1)
        return positions

    def matchedRange(self, assigned_range, search_msb, search_lsb, search_ptr):
        matched_range = []
        for msb, lsb, ptr in assigned_range:
            match = False
            if search_ptr is not None and ptr != search_ptr:
                continue
            if lsb <= search_lsb and search_lsb <= msb:
                match = True
                match_lsb = search_lsb
            else:
                match_lsb = lsb
            if lsb <= search_msb and search_msb <= msb:
                match = True
                match_msb = search_msb
            else:
                match_msb = msb
            if match:
                matched_range.append((match_msb, match_lsb, search_ptr))
        return tuple(matched_range)

    def unmatchedRange(self, matched_range, search_msb, search_lsb, search_ptr):
        unmatched_range = []
        minval = None
        maxval = None
        last_msb = None
        for msb, lsb, ptr in sorted(matched_range, key=lambda x: x[0]):
            if search_ptr is not None and ptr != search_ptr:
                continue
            if minval is None or lsb < minval:
                minval = lsb
            if maxval is None or msb > maxval:
                maxval = msb
            if last_msb is not None and last_msb + 1 > lsb:
                unmatched_range.append((last_msb + 1, lsb - 1, ptr))
            last_msb = msb
        if minval is None and maxval is None:
            return ((search_msb, search_lsb, search_ptr), )
        if search_lsb < minval:
            unmatched_range.append((search_lsb, minval - 1, search_ptr))
        if maxval < search_msb:
            unmatched_range.append((maxval + 1, search_msb, search_ptr))
        return tuple(unmatched_range)
