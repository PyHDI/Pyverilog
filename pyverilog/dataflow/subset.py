# -------------------------------------------------------------------------------
# subset.py
#
# Generating Subset of dataflow graph
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import collections

import pyverilog.utils.util as util
import pyverilog.utils.verror as verror
import pyverilog.utils.signaltype as signaltype
from pyverilog.dataflow.merge import VerilogDataflowMerge


class VerilogSubset(VerilogDataflowMerge):
    def __init__(self, topmodule, terms, binddict,
                 resolved_terms, resolved_binddict, constlist):
        VerilogDataflowMerge.__init__(self, topmodule, terms, binddict,
                                      resolved_terms, resolved_binddict, constlist)
        self.clock_name = 'CLK'
        self.clock_edge = 'posedge'
        self.reset_name = 'RST_X'
        self.reset_edge = 'negedge'

    def set_clock_info(self, clock_name, clock_edge):
        self.clock_name = clock_name
        self.clock_edge = clock_edge

    def set_reset_info(self, reset_name, reset_edge):
        self.reset_name = reset_name
        self.reset_edge = reset_edge

    def getBindSubset(self, termname, visited_sources=set()):
        term = self.getTerm(termname)
        if term is None:
            raise verror.DefinitionError('No such signal')
        bindlist = self.getBindlist(termname)
        nextsources = visited_sources.copy()
        ret_binds = collections.OrderedDict()
        for bind in bindlist:
            if not termname in ret_binds:
                ret_binds[termname] = []
            ret_binds[termname].append(bind)
            if bind.isClockEdge():
                clock_name = bind.getClockName()
                if clock_name != util.toTermname((self.topmodule, self.clock_name)):
                    r_binds, r_sources = self.getBindSubset(clock_name, nextsources)
                    nextsources |= r_sources
                    ret_binds = util.dictlistmerge(ret_binds, r_binds)

        sources = self.getBindSources(termname)
        for source in sources:
            if source in visited_sources:
                continue
            nextsources.add(source)
            r_binds, r_sources = self.getBindSubset(source, nextsources)
            ret_binds = util.dictlistmerge(ret_binds, r_binds)
            nextsources |= r_sources
        return ret_binds, nextsources

    def getBindSourceSubset(self, targets):
        visited_binddict = collections.OrderedDict()
        visited_sources = set()
        for target in targets:
            termname = util.toTermname(target)
            r_binds, r_sources = self.getBindSubset(termname, visited_sources)
            visited_sources |= r_sources
            visited_binddict = util.dictlistmerge(visited_binddict, r_binds)
        return visited_binddict, visited_sources

    def getEntire(self):
        visited_binddict = self.resolved_binddict
        visited_sources = self.terms.keys()
        return self._discretion(visited_binddict, visited_sources)

    def getSubset(self, targets):
        visited_binddict, visited_sources = self.getBindSourceSubset(targets)
        return self._discretion(visited_binddict, visited_sources)

    def _discretion(self, visited_binddict, visited_sources):
        terms = collections.OrderedDict()
        parameter = collections.OrderedDict()
        assign = collections.OrderedDict()
        always_clockedge = collections.OrderedDict()
        always_combination = collections.OrderedDict()

        # discretion the signal desclaration
        for source in visited_sources:
            termtype = self.getTermtype(source)
            if signaltype.isParameter(termtype):
                continue
            if signaltype.isLocalparam(termtype):
                continue
            terms[source] = self.terms[source]

        for left, rights in visited_binddict.items():
            for right in rights:
                assign_type = self.getAssignType(left, right)
                if assign_type == 'clockedge':
                    if not left in always_clockedge:
                        always_clockedge[left] = set([])
                    always_clockedge[left].add(right)
                elif assign_type == 'combination':
                    if not left in always_combination:
                        always_combination[left] = set([])
                    always_combination[left].add(right)
                elif assign_type == 'assign':
                    if not left in assign:
                        assign[left] = set([])
                    assign[left].add(right)
                elif assign_type == 'parameter':
                    parameter[left] = right
                    continue
                elif assign_type == 'localparam':
                    parameter[left] = right
                    continue
                if not left in terms:
                    terms[left] = self.terms[left]
        return terms, parameter, assign, always_clockedge, always_combination
