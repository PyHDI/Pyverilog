#-------------------------------------------------------------------------------
# definition_analyzer.py
# 
# Verilog module signal/module definition analyzer with Pyverilog
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------

import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

import pyverilog.utils.version
from pyverilog.vparser.parser import VerilogCodeParser

if sys.version_info[0] >= 3:
    from pyverilog.definition_analyzer.modulevisitor import ModuleVisitor
    from pyverilog.definition_analyzer.signalvisitor import SignalVisitor
    from pyverilog.definition_analyzer.bindvisitor import BindVisitor
else:
    from modulevisitor import ModuleVisitor
    from signalvisitor import SignalVisitor
    from bindvisitor import BindVisitor

class VerilogDefinitionAnalyzer(VerilogCodeParser):
    def __init__(self, filelist, topmodule='TOP', noreorder=False, nobind=False):
        self.topmodule = topmodule
        self.terms = {}
        self.binddict = {}
        self.frametable = None
        VerilogCodeParser.__init__(self, filelist)
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
    INFO = "Verilog module signal/module definition analyzer with Pyverilog"
    VERSION = pyverilog.utils.version.VERSION
    USAGE = "Usage: python definition_analyzer.py -t TOPMODULE file ..."

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
    optparser.add_option("--nobind",action="store_true",dest="nobind",
                         default=False,help="No binding traversal, Default=False")
    optparser.add_option("--noreorder",action="store_true",dest="noreorder",
                         default=False,help="No reordering of binding definition, Default=False")
    (options, args) = optparser.parse_args()

    filelist = args
    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f): raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()

    verilogdefinitionanalyzer = VerilogDefinitionAnalyzer(filelist, options.topmodule,
                                                          noreorder=options.noreorder,
                                                          nobind=options.nobind)
    verilogdefinitionanalyzer.generate()

    directives = verilogdefinitionanalyzer.get_directives()
    print('Directive:')
    for dr in directives:
        print(dr)

    instances = verilogdefinitionanalyzer.getInstances()
    print('Instance:')
    for ins in instances:
        print(ins)

    if options.nobind:
        print('Signal:')
        signals = verilogdefinitionanalyzer.getSignals()
        for sig in signals:
            print(sig)

        print('Const:')
        consts = verilogdefinitionanalyzer.getConsts()
        for con in consts:
            print(con)

    else:
        terms = verilogdefinitionanalyzer.getTerms()
        print('Term:')
        for tk, tv in sorted(terms.items(), key=lambda x:len(x[0])):
            print(tv.tostr())
   
        binddict = verilogdefinitionanalyzer.getBinddict()
        print('Bind:')
        for bk, bv in sorted(binddict.items(), key=lambda x:len(x[0])):
            for bvi in bv:
                print(bvi.tostr())
