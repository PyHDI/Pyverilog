#-------------------------------------------------------------------------------
# tree_walker.py
#
# Verilog definition tree walker with Pyverilog
#
# Creating unified definition tree by traverling multiple tree definitions
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

import pyverilog.utils.version
import pyverilog.utils.util as util
import pyverilog.utils.verror as verror
import pyverilog.utils.signaltype as signaltype
import pyverilog.utils.tree_replace as tree_replace
from pyverilog.utils.dataflow import *

from pyverilog.tree_constructor.tree_constructor import VerilogTreeConstructor

class VerilogTreeWalker(VerilogTreeConstructor):
    def __init__(self, topmodule, terms, binddict, resolved_terms, resolved_binddict, constlist):
        VerilogTreeConstructor.__init__(
            self, topmodule, terms, binddict, resolved_terms, resolved_binddict, constlist)

    ############################################################################
    def walkBind(self, name, step=0):
        termname = util.toTermname(name)
        if not termname in self.terms: raise verror.DefinitionError('No such signals: %s' % str(name))
        tree = self.getTree(termname)
        walked_tree = self.walkTree(tree, visited=set(), step=step)
        return tree_replace.replaceUndefined(walked_tree, termname)

    ############################################################################
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
            if termname in visited: return tree

            termtype = self.getTermtype(termname)
            if util.isTopmodule(scope) and signaltype.isInput(termtype):
                return tree

            nptr = None
            if signaltype.isRegArray(termtype) or signaltype.isWireArray(termtype):
                if ptr is None:
                    raise verror.FormatError('Array variable requires an pointer.')
                if msb is not None and lsb is not None: return tree
                nptr = ptr

            nextstep = step
            if signaltype.isReg(termtype) or signaltype.isRegArray(termtype):
                if (not self.isCombination(termname) and
                    not signaltype.isRename(termtype) and 
                    nextstep == 0):
                    return tree
                if (not self.isCombination(termname) and
                    not signaltype.isRename(termtype)):
                    nextstep -= 1

            return self.walkTree(self.getTree(termname, nptr),
                                 visited|set([termname,]), nextstep, delay)

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
            return DFPartselect(var, msb, lsb)

        if isinstance(tree, DFPointer):
            ptr = self.walkTree(tree.ptr, visited, step, delay)
            var = self.walkTree(tree.var, visited, step, delay, ptr=ptr)
            if isinstance(tree.var, DFTerminal):
                termtype = self.getTermtype(tree.var.name)
                if ((signaltype.isRegArray(termtype) or 
                     signaltype.isWireArray(termtype)) and 
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

################################################################################
if __name__ == '__main__':
    from optparse import OptionParser
    from pyverilog.definition_analyzer.definition_analyzer import VerilogDefinitionAnalyzer
    from pyverilog.definition_resolver.definition_resolver import VerilogDefinitionResolver
    INFO = "Verilog tree walker with Pyverilog"
    VERSION = pyverilog.utils.version.VERSION
    USAGE = "Usage: python tree_walker.py -t TOPMODULE -s TARGETSIGNAL file ..."

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
    optparser.add_option("-s","--search",dest="searchtarget",action="append",
                         default=[],help="Search Target Signal")
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

    verilogtreewalker = VerilogTreeWalker(options.topmodule, terms, binddict, resolved_terms, resolved_binddict, constlist)

    for target in options.searchtarget:
        tree = verilogtreewalker.walkBind(target)
        print('target: %s' % target)
        print(tree.tostr())
