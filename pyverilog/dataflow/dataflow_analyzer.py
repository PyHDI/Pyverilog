#-------------------------------------------------------------------------------
# dataflow_analyzer.py
# 
# Verilog module signal/module dataflow analyzer
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------

import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )
sys.setrecursionlimit(16 * 1024)

import pyverilog
import pyverilog.utils
import pyverilog.utils.version
from pyverilog.vparser.parser import VerilogCodeParser

if sys.version_info[0] >= 3:
    from pyverilog.dataflow.modulevisitor import ModuleVisitor
    from pyverilog.dataflow.signalvisitor import SignalVisitor
    from pyverilog.dataflow.bindvisitor import BindVisitor
else:
    from modulevisitor import ModuleVisitor
    from signalvisitor import SignalVisitor
    from bindvisitor import BindVisitor

class VerilogDataflowAnalyzer(VerilogCodeParser):
    def __init__(self, filelist, topmodule='TOP', noreorder=False, nobind=False,
                 preprocess_include=None,
                 preprocess_define=None):
        self.topmodule = topmodule
        self.terms = {}
        self.binddict = {}
        self.frametable = None
        VerilogCodeParser.__init__(self, filelist,
                                   preprocess_include=preprocess_include,
                                   preprocess_define=preprocess_define)
        self.noreorder = noreorder
        self.nobind = nobind
        
    def generate(self):
        ast = self.parse()

        module_visitor = ModuleVisitor()
        module_visitor.visit(ast)
        modulenames = module_visitor.get_modulenames()
        moduleinfotable = module_visitor.get_moduleinfotable()
        
        signal_visitor = SignalVisitor(moduleinfotable, self.topmodule)
        signal_visitor.start_visit()
        frametable = signal_visitor.getFrameTable()

        if self.nobind:
            self.frametable = frametable
            return

        bind_visitor = BindVisitor(moduleinfotable, self.topmodule, frametable,
                                   noreorder=self.noreorder)

        bind_visitor.start_visit()
        dataflow = bind_visitor.getDataflows()

        self.frametable = bind_visitor.getFrameTable()
        self.terms = dataflow.getTerms()
        self.binddict = dataflow.getBinddict()

    def getFrameTable(self):
        return self.frametable

    #-------------------------------------------------------------------------
    def getInstances(self):
        if self.frametable is None: return ()
        return self.frametable.getAllInstances()

    def getSignals(self):
        if self.frametable is None: return ()
        return self.frametable.getAllSignals()

    def getConsts(self):
        if self.frametable is None: return ()
        return self.frametable.getAllConsts()

    def getTerms(self):
        return self.terms

    def getBinddict(self):
        return self.binddict

if __name__ == '__main__':
    from optparse import OptionParser
    INFO = "Verilog module signal/module dataflow analyzer"
    VERSION = pyverilog.utils.version.VERSION
    USAGE = "Usage: python dataflow_analyzer.py -t TOPMODULE file ..."

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
    (options, args) = optparser.parse_args()

    filelist = args
    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f): raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()

    verilogdataflowanalyzer = VerilogDataflowAnalyzer(filelist, options.topmodule,
                                                      noreorder=options.noreorder,
                                                      nobind=options.nobind,
                                                      preprocess_include=options.include,
                                                      preprocess_define=options.define)
    verilogdataflowanalyzer.generate()

    directives = verilogdataflowanalyzer.get_directives()
    print('Directive:')
    for dr in directives:
        print(dr)

    instances = verilogdataflowanalyzer.getInstances()
    print('Instance:')
    for ins in instances:
        print(ins)

    if options.nobind:
        print('Signal:')
        signals = verilogdataflowanalyzer.getSignals()
        for sig in signals:
            print(sig)

        print('Const:')
        consts = verilogdataflowanalyzer.getConsts()
        for con in consts:
            print(con)

    else:
        terms = verilogdataflowanalyzer.getTerms()
        print('Term:')
        for tk, tv in sorted(terms.items(), key=lambda x:len(x[0])):
            print(tv.tostr())
   
        binddict = verilogdataflowanalyzer.getBinddict()
        print('Bind:')
        for bk, bv in sorted(binddict.items(), key=lambda x:len(x[0])):
            for bvi in bv:
                print(bvi.tostr())
