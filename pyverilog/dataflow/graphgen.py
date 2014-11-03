#-------------------------------------------------------------------------------
# graphgen.py
#
# Dataflow graph generator (Only Python 2.7)
#
# pygraphviz and graphviz are required
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------

import sys
import os
import pygraphviz as pgv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

import pyverilog.utils.version
import pyverilog.utils.util as util
import pyverilog.utils.verror as verror

if sys.version_info[0] >= 3:
    from pyverilog.dataflow.dataflow import *
    from pyverilog.dataflow.optimizer import VerilogOptimizer
    from pyverilog.dataflow.walker import VerilogDataflowWalker
    import pyverilog.dataflow.reorder as reorder
    import pyverilog.dataflow.replace as replace
else:
    from dataflow import *
    from optimizer import VerilogOptimizer
    from walker import VerilogDataflowWalker
    import reorder
    import replace

class VerilogGraphGenerator(object):
    def visit(self, node, parent, color='black', edge_label=None):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node, parent, color=color, edge_label=edge_label)

    def generic_visit(self, node, parent, color='black', edge_label=None):
        if node is None: return
        for c in node.children():
            self.visit(c, parent, color=color, edge_label=edge_label)

    def __init__(self, topmodule,
                 terms, binddict, resolved_terms, resolved_binddict, constlist, 
                 filename, withcolor=False):
        self.topmodule = topmodule
        self.terms = terms
        self.binddict = binddict
        self.resolved_terms = resolved_terms
        self.resolved_binddict = resolved_binddict
        self.graph = pgv.AGraph(directed=True) #pgv.AGraph(strict=False, directed=True)
        self.filename = filename
        self.withcolor = withcolor

        self.renamecounter = 0
        self.identical = False
        self.treewalker = VerilogDataflowWalker(self.topmodule, self.terms, 
                                                self.binddict, self.resolved_terms,
                                                self.resolved_binddict, constlist)
        self.optimizer = VerilogOptimizer(terms, constlist)

    def generate(self, signalname, identical=False, walk=True, step=1, reorder=False, delay=False):
        termname = util.toTermname(signalname)
        tree = self.treewalker.getTree(termname)
        if tree is None:
            raise verror.DefinitionError('No such signals: %s' % str(signalname))
        if walk: 
            tree = self.treewalker.walkTree(tree, visited=set(), step=step, delay=delay)
            if reorder: tree = reorder.reorder(tree)            

        tree = self.optimizer.optimize(tree)
        if reorder: tree = reorder.reorder(tree)

        tree = replace.replaceUndefined(tree, termname)

        name = self.rename(signalname)
        self.identical = identical
        self.add_node(name, label=signalname)
        self.visit(tree, name)

    def draw(self, filename=None):
        fn = filename
        if fn is None: fn = self.filename
        self.graph.write('file.dot')
        self.graph.layout(prog='dot')
        self.graph.draw(fn)

    ############################################################################
    def visit_DFOperator(self, node, parent, color='black', edge_label=None):
        name = self.add_RenamedDF(node, parent, color=color, edge_label=edge_label)
        self.generic_visit(node, name, color=color, edge_label=None)

    def visit_DFPartselect(self, node, parent, color='black', edge_label=None):
        name = self.add_RenamedDF(node, parent, color=color, edge_label=edge_label)
        if node.var is not None: self.visit(node.var, name, color=color, edge_label='VAR')
        if node.msb is not None: self.visit(node.msb, name, color='orange', edge_label='MSB')
        if node.lsb is not None: self.visit(node.lsb, name, color='orange', edge_label='LSB')

    def visit_DFPointer(self, node, parent, color='black', edge_label=None):
        name = self.add_RenamedDF(node, parent, color=color, edge_label=edge_label)
        if node.var is not None: self.visit(node.var, name, color=color, edge_label='VAR')
        if node.ptr is not None: self.visit(node.ptr, name, color='orange', edge_label='PTR')

    def visit_DFConcat(self, node, parent, color='black', edge_label=None):
        name = self.add_RenamedDF(node, parent, color=color, edge_label=edge_label)
        self.generic_visit(node, name, color=color)

    def visit_DFBranch(self, node, parent, color='black', edge_label=None):
        name = self.add_RenamedDF(node, parent, color=color, edge_label=edge_label)
        if node.condnode is not None: self.visit(node.condnode, name, color='blue', edge_label='COND')
        if node.truenode is not None: self.visit(node.truenode, name, color='green', edge_label='TRUE')
        if node.falsenode is not None: self.visit(node.falsenode, name, color='red', edge_label='FALSE')

    def visit_DFTerminal(self, node, parent, color='black', edge_label=None):
        if self.identical:
            self.add_RenamedDF(node, parent, color=color, edge_label=edge_label)
        else:
            self.add_DF(node, parent, color=color, edge_label=edge_label)

    def visit_DFIntConst(self, node, parent, color='black', edge_label=None):
        self.add_RenamedDF(node, parent, color=color, edge_label=edge_label)

    def visit_DFFloatConst(self, node, parent, color='black', edge_label=None):
        self.add_RenamedDF(node, parent, color=color, edge_label=edge_label)

    def visit_DFStringConst(self, node, parent, color='black', edge_label=None):
        self.add_RenamedDF(node, parent, color=color, edge_label=edge_label)

    def visit_DFEvalValue(self, node, parent, color='black', edge_label=None):
        self.add_RenamedDF(node, parent, color=color, edge_label=edge_label)

    def visit_DFUndefined(self, node, parent, color='black', edge_label=None):
        self.add_RenamedDF(node, parent, color=color, edge_label=edge_label)

    def visit_DFHighImpedance(self, node, parent, color='black', edge_label=None):
        self.add_RenamedDF(node, parent, color=color, edge_label=edge_label)

    def visit_DFDelay(self, node, parent, color='black', edge_label=None):
        name = self.add_RenamedDF(node, parent, color=color, edge_label=edge_label)
        if node.nextnode is not None: self.visit(node.nextnode, name, color=color)

    ############################################################################        
    def add_DF(self, node, parent, color='black', edge_label=None):
        #name = node.__repr__()
        name = node.tolabel()
        self.add_node(name, color=color)
        if edge_label:
            self.add_edge(parent, name, color=color, label=edge_label)
        else:
            self.add_edge(parent, name, color=color)
        return name

    def add_RenamedDF(self, node, parent, color='black', edge_label=None):
        #mylabel = node.__repr__()
        mylabel = node.tolabel()
        name = self.rename(mylabel)
        self.add_node(name, label=mylabel, color=color)
        if edge_label:
            self.add_edge(parent, name, color=color, label=edge_label)
        else:
            self.add_edge(parent, name, color=color)
        return name

    ############################################################################        
    def rename(self, name):
        ret = name + '_graphrename_' + str(self.renamecounter)
        self.renamecounter += 1
        return ret

    ############################################################################        
    def add_node(self, node, label=None, color='black'):
        if not self.withcolor: color='black'
        if label is None: self.graph.add_node(str(node), color=color)
        else: self.graph.add_node(str(node), label=label, color=color)

    def add_edge(self, start, end, color='black', label=None):
        if not self.withcolor: color='black'
        if label:
            self.graph.add_edge(str(start), str(end), color=color, label=label)
        else:
            self.graph.add_edge(str(start), str(end), color=color)

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
    INFO = "Graph generator from dataflow"
    VERSION = pyverilog.utils.version.VERSION
    USAGE = "Usage: python graphgen.py -t TOPMODULE -s TARGETSIGNAL file ..."

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
    optparser.add_option("-o","--output",dest="outputfile",
                         default="out.png",help="Graph file name, Default=out.png")
    optparser.add_option("--identical",action="store_true",dest="identical",
                         default=False,help="# Identical Laef, Default=False")
    optparser.add_option("--walk",action="store_true",dest="walk",
                         default=False,help="Walk contineous signals, Default=False")
    optparser.add_option("--step",dest="step",type='int', 
                         default=1,help="# Search Steps, Default=1")
    optparser.add_option("--reorder",action="store_true",dest="reorder",
                         default=False,help="Reorder the contineous tree, Default=False")
    optparser.add_option("--delay",action="store_true",dest="delay",
                         default=False,help="Inset Delay Node to walk Regs, Default=False")
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

    graphgen = VerilogGraphGenerator(options.topmodule, terms, binddict, 
                                     resolved_terms, resolved_binddict, constlist, options.outputfile)

    for target in options.searchtarget:
        graphgen.generate(target, walk=options.walk, identical=options.identical, 
                          step=options.step, reorder=options.reorder, delay=options.delay)

    graphgen.draw()
