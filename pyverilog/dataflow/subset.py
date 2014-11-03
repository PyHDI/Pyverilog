#-------------------------------------------------------------------------------
# subset.py
#
# Generating Subset of dataflow graph
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------

import sys
import os
import collections

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

import pyverilog.utils.version
import pyverilog.utils.util as util
import pyverilog.utils.verror as verror
import pyverilog.utils.signaltype as signaltype

if sys.version_info[0] >= 3:
    from pyverilog.dataflow.merge import VerilogDataflowMerge
else:
    from merge import VerilogDataflowMerge

class VerilogSubset(VerilogDataflowMerge):
    def __init__(self, topmodule, terms, binddict,
                 resolved_terms, resolved_binddict, constlist):
        VerilogDataflowMerge.__init__(self, topmodule, terms, binddict,
                                      resolved_terms, resolved_binddict, constlist)
        self.clock_name = 'CLK'
        self.clock_edge = 'posedge'
        self.reset_name = 'RST_X'
        self.reset_edge = 'negedge'

    ############################################################################
    def set_clock_info(self, clock_name, clock_edge):
        self.clock_name = clock_name
        self.clock_edge = clock_edge

    def set_reset_info(self, reset_name, reset_edge):
        self.reset_name = reset_name
        self.reset_edge = reset_edge

    ############################################################################
    def getBindSubset(self, termname, visited_sources=set()):
        term = self.getTerm(termname)
        if term is None: raise verror.DefinitionError('No such signal')
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
            if source in visited_sources: continue
            nextsources.add(source)
            r_binds, r_sources = self.getBindSubset(source, nextsources)
            ret_binds = util.dictlistmerge(ret_binds, r_binds)
            nextsources |= r_sources
        return ret_binds, nextsources

    ############################################################################
    def getBindSourceSubset(self, targets):
        visited_binddict = collections.OrderedDict()
        visited_sources = set()
        for target in targets:
            termname = util.toTermname(target)
            r_binds, r_sources = self.getBindSubset(termname, visited_sources)
            visited_sources |= r_sources
            visited_binddict = util.dictlistmerge(visited_binddict, r_binds)
        return visited_binddict, visited_sources

    ############################################################################
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
            if signaltype.isParameter(termtype): continue
            if signaltype.isLocalparam(termtype): continue
            terms[source] = self.terms[source]

        for left, rights in visited_binddict.items():
            for right in rights:
                assign_type = self.getAssignType(left, right)
                if assign_type == 'clockedge':
                    if not left in always_clockedge: always_clockedge[left] = set([])
                    always_clockedge[left].add(right)
                elif assign_type == 'combination':
                    if not left in always_combination: always_combination[left] = set([])
                    always_combination[left].add(right)
                elif assign_type == 'assign':
                    if not left in assign: assign[left] = set([])
                    assign[left].add(right)
                elif assign_type == 'parameter':
                    parameter[left] = right
                    continue
                elif assign_type == 'localparam':
                    parameter[left] = right
                    continue
                if not left in terms: terms[left] = self.terms[left]
        return terms, parameter, assign, always_clockedge, always_combination

################################################################################
if __name__ == '__main__':
    from optparse import OptionParser
    import pyverilog.utils.util as util
    if sys.version_info[0] >= 3:
        from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer
        from pyverilog.dataflow.optimizer import VerilogDataflowOptimizer
    else:
        from dataflow_analyzer import VerilogDataflowAnalyzer
        from optimizer import VerilogDataflowOptimizer
    INFO = "Subset generator from Verilog dataflow definitions"
    VERSION = pyverilog.utils.version.VERSION
    USAGE = "Usage: python subset.py -t TOPMODULE file ..."

    def showVersion():
        print(INFO)
        print(VERSION)
        print(USAGE)
        sys.exit()
    
    optparser = OptionParser()
    optparser.add_option("-v","--version",action="store_true",dest="showversion",
                         default=False,help="Show the version")
    optparser.add_option("-I","--include",dest="include",action="append",
                         default=[],help="Include path")
    optparser.add_option("-D",dest="define",action="append",
                         default=[],help="Macro Definition")
    optparser.add_option("-t","--top",dest="topmodule",
                         default="TOP",help="Top module, Default=TOP")
    optparser.add_option("--nobind",action="store_true",dest="nobind",
                         default=False,help="No binding traversal, Default=False")
    optparser.add_option("--noreorder",action="store_true",dest="noreorder",
                         default=False,help="No reordering of binding dataflow, Default=False")
    optparser.add_option("-s","--search",dest="searchtarget",action="append",
                         default=[],help="Search Target Signal")
    optparser.add_option("--clockname",dest="clockname",
                         default="CLK",help="Clock signal name")
    optparser.add_option("--resetname",dest="resetname",
                         default="RST_X",help="Reset signal name")
    optparser.add_option("--clockedge",dest="clockedge",
                         default="posedge",help="Clock signal edge")
    optparser.add_option("--resetedge",dest="resetedge",
                         default="negedge",help="Reset signal edge")
    (options, args) = optparser.parse_args()

    filelist = args
    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f): raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()

    analyzer = VerilogDataflowAnalyzer(filelist, options.topmodule,
                                       noreorder=options.noreorder,
                                       nobind=options.nobind,
                                       preprocess_include=options.include,
                                       preprocess_define=options.define)
    analyzer.generate()

    directives = analyzer.get_directives()
    terms = analyzer.getTerms()
    binddict = analyzer.getBinddict()

    optimizer = VerilogDataflowOptimizer(terms, binddict)

    optimizer.resolveConstant()
    resolved_terms = optimizer.getResolvedTerms()
    resolved_binddict = optimizer.getResolvedBinddict()
    constlist = optimizer.getConstlist()

    subset = VerilogSubset(options.topmodule, terms, binddict, 
                           resolved_terms, resolved_binddict, constlist)

    subset.set_clock_info(options.clockname, options.clockedge)
    subset.set_reset_info(options.resetname, options.resetedge)

    sub_binds, sub_terms = subset.getBindSourceSubset(options.searchtarget)
    terms, parameter, assign, always_clockedge, always_combination = subset.getSubset(options.searchtarget)

    for k, v in terms.items():
        print(v.tocode())
    for k, v in parameter.items():
        print(v.tocode())
    for k, v in assign.items():
        for vv in v:
            print(vv.tocode())
    for k, v in always_clockedge.items():
        for vv in v:
            print(vv.tocode())
    for k, v in always_combination.items():
        for vv in v:
            print(vv.tocode())
