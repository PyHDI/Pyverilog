#-------------------------------------------------------------------------------
# definition_resolver.py
#
# Verilog definition optimizer with Pyverilog
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

import pyverilog.utils.version
import pyverilog.utils.signaltype as signaltype
from pyverilog.utils.dataflow import *
from pyverilog.optimizer.optimizer import VerilogOptimizer

class VerilogDefinitionResolver(VerilogOptimizer):
    def __init__(self, terms, binddict):
        VerilogOptimizer.__init__(self, terms, {})
        self.binddict = binddict
        self.resolved_terms = {}
        self.resolved_binddict = {}

    def getResolvedTerms(self):
        return self.resolved_terms
    def getResolvedBinddict(self):
        return self.resolved_binddict
    def getConstlist(self):
        return self.constlist

    def getTerm(self, name):
        return self.terms[name]

    ############################################################################
    def resolveConstant(self):
        #2-pass resolving
        for bk, bv in sorted(self.binddict.items(), key=lambda x:len(x[0])):
            termtype = self.getTerm(bk).termtype
            if signaltype.isParameter(termtype) or signaltype.isLocalparam(termtype):
                rslt = self.optimizeConstant(bv[0].tree)
                if isinstance(rslt, DFEvalValue):
                    self.constlist[bk] = rslt

        for bk, bv in sorted(self.binddict.items(), key=lambda x:len(x[0])):
            termtype = self.getTerm(bk).termtype
            if signaltype.isParameter(termtype) or signaltype.isLocalparam(termtype):
                rslt = self.optimizeConstant(bv[0].tree)
                if isinstance(rslt, DFEvalValue):
                    self.constlist[bk] = rslt

        self.resolved_binddict = copy.deepcopy(self.binddict)
        for bk, bv in sorted(self.binddict.items(), key=lambda x:len(x[0])):
            new_bindlist = []
            for bind in bv:
                new_bind = copy.deepcopy(bind)
                if bk in self.constlist:
                    new_bind.tree = self.constlist[bk]
                new_bindlist.append(new_bind)
            self.resolved_binddict[bk] = new_bindlist

        self.resolved_terms = copy.deepcopy(self.terms)
        for tk, tv in sorted(self.resolved_terms.items(), key=lambda x:len(x[0])):
            if tv.msb is not None: 
                rslt = self.optimizeConstant(tv.msb)
                self.resolved_terms[tk].msb = rslt
            if tv.lsb is not None: 
                rslt = self.optimizeConstant(tv.lsb)
                self.resolved_terms[tk].lsb = rslt
            if tv.lenmsb is not None: 
                rslt = self.optimizeConstant(tv.lenmsb)
                self.resolved_terms[tk].lenmsb = rslt
            if tv.lenlsb is not None: 
                rslt = self.optimizeConstant(tv.lenlsb)
                self.resolved_terms[tk].lenlsb = rslt

################################################################################
if __name__ == '__main__':
    from optparse import OptionParser
    from pyverilog.definition_analyzer.definition_analyzer import VerilogDefinitionAnalyzer
    INFO = "Verilog definition optimizer with Pyverilog"
    VERSION = pyverilog.utils.version.VERSION
    USAGE = "Usage: python definition_resolver.py -t TOPMODULE file ..."

    def showVersion():
        print(INFO)
        print(VERSION)
        print(USAGE)
        sys.exit()
    
    optparser = OptionParser()
    optparser.add_option("-v","--version",action="store_true",dest="showversion",
                         default=False,help="Show the version")
    optparser.add_option("-t","--top",dest="topmodule",
                         default="TOP",help="Top module, Default=TOP")
    (options, args) = optparser.parse_args()

    filelist = args
    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f): raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()

    verilogdefinitionanalyzer = VerilogDefinitionAnalyzer(filelist, options.topmodule)
    verilogdefinitionanalyzer.generate()

    directives = verilogdefinitionanalyzer.get_directives()
    terms = verilogdefinitionanalyzer.getTerms()
    binddict = verilogdefinitionanalyzer.getBinddict()

    verilogdefinitionresolver = VerilogDefinitionResolver(terms, binddict)
    verilogdefinitionresolver.resolveConstant()

    resolved_terms = verilogdefinitionresolver.getResolvedTerms()
    resolved_binddict = verilogdefinitionresolver.getResolvedBinddict()
    constlist = verilogdefinitionresolver.getConstlist()

    print('Directive:')
    for dr in directives:
        print(dr)

    print('Term:')
    for tk, tv in sorted(resolved_terms.items(), key=lambda x:len(x[0])):
        print(tv.tostr())

    print('Bind:')
    for bk, bv in sorted(resolved_binddict.items(), key=lambda x:len(x[0])):
        for bvi in bv:
            print(bvi.tostr())

    print('Const:')
    for ck, cv in sorted(constlist.items(), key=lambda x:len(x[0])):
        print(ck, cv)
