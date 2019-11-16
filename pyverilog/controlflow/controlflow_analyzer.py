# -------------------------------------------------------------------------------
# controlflow_analyzer.py
#
# Controlflow analyzer
#
# for visualization, graphviz and pygraphviz are required
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os

import pyverilog.utils.util as util
import pyverilog.utils.signaltype as signaltype
import pyverilog.dataflow.reorder as reorder
import pyverilog.dataflow.replace as replace
from pyverilog.dataflow.subset import VerilogSubset
from pyverilog.dataflow.walker import VerilogDataflowWalker
from pyverilog.dataflow.dataflow import *
import pyverilog.controlflow.splitter as splitter
import pyverilog.controlflow.transition as transition


class VerilogControlflowAnalyzer(VerilogSubset):
    def __init__(self, topmodule, terms, binddict,
                 resolved_terms, resolved_binddict,
                 constlist, fsm_vars=('fsm', 'state', 'count', 'cnt', 'step', 'mode')):
        VerilogSubset.__init__(self, topmodule, terms, binddict,
                               resolved_terms, resolved_binddict, constlist)
        self.treewalker = VerilogDataflowWalker(topmodule, terms, binddict,
                                                resolved_terms, resolved_binddict, constlist)
        self.fsm_vars = fsm_vars

    def getLoops(self):
        fsms = self.getFiniteStateMachines()
        loops = {}
        for signame, fsm in fsms.items():
            loop_set = fsm.get_loop()
            if len(loop_set) == 0:
                continue
            if not signame in loops:
                loops[signame] = set([])
            loops[signame].update(loop_set)
        return loops, fsms

    def getFiniteStateMachines(self):
        statemachines = {}
        for termname, bindlist in self.resolved_binddict.items():
            if not self.isFsmVar(termname):
                continue
            funcdict, delaycnt = self.getFuncdict(termname)
            if len(funcdict) > 0:
                print("FSM signal: %s, Condition list length: %d" % (str(termname), len(funcdict)))
            fsm = self.getFiniteStateMachine(termname, funcdict)
            if fsm.size() > 0:
                fsm.set_delaycnt(delaycnt)
                fsm.resolve(self.optimizer)
                statemachines[termname] = fsm
        return statemachines

    def getFiniteStateMachine(self, termname, funcdict):
        fsm = FiniteStateMachine(util.toFlatname(termname))
        if len(funcdict) == 0:
            return fsm
        width = self.getWidth(termname)
        for condlist, func in sorted(funcdict.items(), key=lambda x: len(x[0])):
            if not isinstance(func, DFEvalValue):
                continue
            print("Condition: %s, Inferring transition condition" % str(condlist))
            node = transition.walkCondlist(condlist, termname, width)
            if node is None:
                continue
            statenode_list = node.nodelist if isinstance(
                node, transition.StateNodeList) else [node, ]
            for statenode in statenode_list:
                fsm.construct(func.value, statenode)
        return fsm

    def getFuncdict(self, termname, delaycnt=0):
        termtype = self.getTermtype(termname)
        if not self.isClockEdge(termname):
            return {}, 0
        if signaltype.isRename(termtype):
            return {}, 0
        tree = self.makeTree(termname)
        funcdict = splitter.split(tree)
        funcdict = splitter.remove_reset_condition(funcdict)
        if len(funcdict) == 1 and len(list(funcdict.keys())[0]) == 0:
            next_term = list(funcdict.values())[0]
            if isinstance(next_term, DFTerminal):
                return self.getFuncdict(next_term.name, delaycnt + 1)
        return funcdict, delaycnt

    def isFsmVar(self, termname):
        for v in self.fsm_vars:
            if re.search(v.lower(), str(termname).lower()):
                return True
        return False

    def getWidth(self, termname):
        term = self.getTerm(termname)
        msb = self.optimizer.optimizeConstant(term.msb)
        lsb = self.optimizer.optimizeConstant(term.lsb)
        width = DFIntConst('32')
        if msb is not None and lsb is not None:
            return abs(self.optimizer.optimizeConstant(DFOperator((msb, lsb), 'Minus')).value) + 1
        return self.optimizer.optimizeConstant(width).value

    def makeTree(self, termname):
        tree = self.getTree(termname)
        tree = self.treewalker.walkTree(tree)
        tree = reorder.reorder(tree)
        tree = self.optimizer.optimize(tree)
        tree = replace.replaceUndefined(tree, termname)
        return tree


class FiniteStateMachine(object):
    def __init__(self, name):
        self.name = name
        self.fsm = {}  # key:src, value: dict[cond]=dst
        self.any = {}  # key:cond, value:dst
        self.delaycnt = 0

    def set_delaycnt(self, delaycnt):
        self.delaycnt = delaycnt

    def size(self):
        dstlen = 0
        for src, dstdict in self.fsm.items():
            dstlen += len(dstdict)
        srcs = self.fsm.keys()
        dstlen += len(srcs) * len(self.any)
        return dstlen

    def label_range(self):
        minval = None
        maxval = None
        for src, dstdict in self.fsm.items():
            if minval is None:
                minval = src
            elif src < minval:
                minval = src
            if maxval is None:
                maxval = src
            elif src > maxval:
                maxval = src
            for cond, dst in dstdict.items():
                if minval is None:
                    minval = dst
                elif dst < minval:
                    minval = dst
                if maxval is None:
                    maxval = dst
                elif dst > maxval:
                    maxval = dst
        return (minval, maxval)

    def construct(self, dst, node):
        if node is None:
            return
        if node.isany:
            transcond = node.transcond
            self.add_any(dst, transcond)
        for rp in node.range_pairs:
            transcond = node.transcond
            self.add(rp, dst, transcond)

    def add_any(self, dst, cond):
        self.any[cond] = dst

    def add(self, srcs, dst, cond):
        sb, se = srcs
        for src in range(sb, se + 1):
            if not src in self.fsm:
                self.fsm[src] = {}
            self.fsm[src][cond] = dst

    def resolve(self, evaluate):
        new_fsm = {}
        for src, dstdict in sorted(self.fsm.items(), key=lambda x: x[0]):
            dst_cond_dict = {}
            for cond, dst in sorted(dstdict.items(), key=lambda x: x[1]):
                if not dst in dst_cond_dict:
                    dst_cond_dict[dst] = cond
                else:
                    cur_cond = dst_cond_dict[dst]
                    if cur_cond is None:
                        pass
                    elif cond is None:
                        dst_cond_dict[dst] = None
                    else:
                        dst_cond_dict[dst] = evaluate.optimize(DFOperator((cur_cond, cond), 'Lor'))
            new_dstdict = {}
            for dst, cond in dst_cond_dict.items():
                if isinstance(cond, DFEvalValue) and cond.value > 0:
                    new_dstdict[None] = dst
                else:
                    new_dstdict[cond] = dst
            new_fsm[src] = new_dstdict
        self.fsm = new_fsm

    def view(self):
        for cond, dst in self.any.items():
            s = []
            s.append('any -- ')
            if cond is not None:
                s.append(cond.tocode())
            else:
                s.append('None')
            s.append('--> %d' % dst)
            print(''.join(s))
        for src, dstdict in self.fsm.items():
            for cond, dst in dstdict.items():
                s = []
                s.append('%d --' % src)
                if cond is not None:
                    s.append(cond.tocode())
                else:
                    s.append('None')
                s.append('--> %d' % dst)
                print(''.join(s))

    def tograph(self, filename='fsm.png', nolabel=False):
        import pygraphviz as pgv
        #graph = pgv.AGraph(strict=False, directed=True)
        graph = pgv.AGraph(directed=True)
        for src, dstdict in self.fsm.items():
            graph.add_node(str(src), label=str(src))
            for cond, dst in dstdict.items():
                graph.add_node(str(dst), label=str(dst))
                if nolabel:
                    graph.add_edge(str(src), str(dst), label='')
                else:
                    graph.add_edge(str(src), str(dst), label=str(cond))
        srcs = self.fsm.keys()
        for src in srcs:
            for cond, dst in self.any.items():
                graph.add_node(str(dst), label=str(dst))
                if nolabel:
                    graph.add_edge(str(src), str(dst), label='')
                else:
                    graph.add_edge(str(src), str(dst), label=str(cond))

        graph.write('file.dot')
        graph.layout(prog='dot')
        graph.draw(filename)

    def get_loop(self):
        loops = set([])
        loop_node_cnt = {}
        for k in sorted(self.fsm.keys()):
            if not k in self.fsm:
                continue
            if not k in loop_node_cnt:
                loop_node_cnt[k] = 0
            if loop_node_cnt[k] >= len(self.fsm[k].values()):
                continue
            paths = self.get_looppath(k)
            for path in paths:
                rotated = self.rotate(path)
                if rotated not in loops:
                    loops.add(rotated)
                    for r in rotated:
                        if not r in loop_node_cnt:
                            loop_node_cnt[r] = 0
                        loop_node_cnt[r] += 1
        return loops

    def rotate(self, path):
        minval = min(path)
        minval_pos = path.index(minval)
        return path[minval_pos:] + path[:minval_pos]

    def get_looppath(self, src):
        paths = set([])
        if not src in self.fsm:
            return paths
        nextnodes = set(self.fsm[src].values())
        for n in nextnodes:
            r = self._looppath(src, n, visited=set([n]))
            if len(r) > 0:
                paths |= r
        return paths

    def _looppath(self, src, node, visited, cnt=0):
        paths = set([])
        if cnt > 50:
            return paths
        if src == node:
            paths.add((src,))
            return paths
        if not node in self.fsm:
            return paths
        nextnodes = set(self.fsm[node].values()) - visited
        for n in nextnodes:
            r = self._looppath(src, n, visited=visited | set([node]), cnt=cnt + 1)
            if len(r) > 0:
                for np in r:
                    paths.add((node,) + np)
        return paths
