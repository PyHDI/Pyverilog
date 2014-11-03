#-------------------------------------------------------------------------------
# codegen.py
#
# Code generator from dataflow
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

import pyverilog.utils.version
import pyverilog.utils.util as util
import pyverilog.utils.verror as verror
import pyverilog.utils.signaltype as signaltype
from pyverilog.utils.scope import ScopeLabel, ScopeChain

if sys.version_info[0] >= 3:
    from pyverilog.dataflow.subset import VerilogSubset
else:
    from subset import VerilogSubset

class VerilogCodeGenerator(VerilogSubset):
    def __init__(self, topmodule, terms, binddict, 
                 resolved_terms, resolved_binddict, constlist,
                 modulename='Subset', enable_name='HT_enable', num_indent=2, flat=True):
        VerilogSubset.__init__(self, topmodule, terms, binddict, 
                               resolved_terms, resolved_binddict, constlist)
        self.modulename = modulename
        self.enable_name = enable_name
        self.num_indent = num_indent
        self.flat = flat

    ############################################################################
    def addBind(self, name, bind):
        if name in self.binddict:
            self.binddict[name] += (bind,)
        else:
            self.binddict[name] = (bind,)
        if name in self.resolved_binddict:
            self.resolved_binddict[name] += (bind,)
        else:
            self.resolved_binddict[name] = (bind,)

    def addTerm(self, name, term):
        self.terms[name] = term
        self.resolved_terms[name] = term

    ############################################################################
    def _input(self, name):
        return 'input ' + name + ';\n'
    def _output(self, name):
        return 'output ' + name + ';\n'
    def _inout(self, name):
        return 'inout ' + name + ';\n'
    def _wire(self, name):
        return 'wire ' + name + ';\n'

    ############################################################################
    def _modulehead(self, terms):
        modulehead = ''
        modulehead += '`default_nettype none\n'
        modulehead += 'module ' + self.modulename + '('
        modulehead += '\n' + (' ' * self.num_indent)
        modulehead += self.clock_name + ', '
        modulehead += self.reset_name + ', '
        modulehead += self.enable_name + ', '
        modulehead += '\n' + (' ' * self.num_indent)
        
        for tk, tv in terms.items():
            scope = util.getScope(tk)
            if util.isTopmodule(scope):
                termtype = self.getTermtype(tk)
                if signaltype.isInput(termtype) and tk == util.toTermname((self.topmodule, self.reset_name)): continue
                if signaltype.isInput(termtype) and tk == util.toTermname((self.topmodule, self.clock_name)): continue
                if signaltype.isInput(termtype): modulehead += util.toFlatname(tk) + ', '
                elif signaltype.isInout(termtype): modulehead += util.toFlatname(tk) + ', '
                elif signaltype.isOutput(termtype): modulehead += util.toFlatname(tk) + ', '
        modulehead = modulehead[:-2] + ');\n\n'
        return modulehead

    ############################################################################
    def _system_io(self, clock_name, reset_name, enable_name):
        flat_clock_name = util.toFlatname( util.toTermname((self.topmodule, clock_name)) )
        flat_reset_name = util.toFlatname( util.toTermname((self.topmodule, reset_name)) )
        flat_enable_name = util.toFlatname( util.toTermname((self.topmodule, enable_name)) )
        code = ''
        code += self._input(clock_name)
        code += self._input(reset_name)
        code += self._input(enable_name)
        code += self._wire(flat_clock_name)
        code += self._wire(flat_reset_name)
        code += self._assign(flat_clock_name, clock_name)
        code += self._assign(flat_reset_name, reset_name)
        code += '\n'
        return code

    ############################################################################
    def _assign(self, left, right, msb=None, lsb=None):
        code = 'assign ' + left 
        if msb is not None and lsb is not None:
            code += '[' + msb.tocode(None)  + ':' + lsb.tocode(None) + ']'
        elif msb is not None:
            code += '[' + msb.tocode(None)  + ']'
        elif lsb is not None:
            code += '[' + lsb.tocode(None)  + ']'
        code += ' = ' + right + ';\n'
        return code

    ############################################################################
    def generateCode(self, targets=()):
        if len(targets) > 0:
            return self.generateSubsetCode(targets)
        return self.generateEntireCode()

    def generateSubsetCode(self, targets):
        terms, parameter, assign, always_clockedge, always_combination = self.getSubset(targets)
        return self._toCode(terms, parameter, assign, always_clockedge, always_combination)

    def generateEntireCode(self):
        terms, parameter, assign, always_clockedge, always_combination = self.getEntire()
        return self._toCode(terms, parameter, assign, always_clockedge, always_combination)

    def _toCode(self, terms, parameter, assign, always_clockedge, always_combination):
        # module header
        modulehead = self._modulehead(terms)

        code = ''
        # clock, reset, control input definition
        code += self._system_io(self.clock_name, self.reset_name, self.enable_name)

        # general signal definition
        for tk, tv in terms.items():
            termtype = self.getTermtype(tk)
            if signaltype.isInput(termtype) and tk == util.toTermname((self.topmodule, self.reset_name)): continue
            if signaltype.isInput(termtype) and tk == util.toTermname((self.topmodule, self.clock_name)): continue
            code += tv.tocode()

        for pk, pv in parameter.items():
            code += pv.tocode()

        # assign
        for ak, avv in assign.items():
            cnt = 0
            for av in avv:
                code += av.tocode()

        # always (clock edge)
        for ck, cvv in always_clockedge.items():
            for cv in cvv:
                code += cv.tocode()

        # always (combination)
        for ck, cvv in always_combination.items():
            for cv in cvv:
                code += cv.tocode()
            
        # module tail
        moduletail = '\nendmodule\n'

        ret = modulehead + code + moduletail
        
        if self.flat:
            ret = re.sub('\.', '_', ret)

        return ret

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
    INFO = "Code generator from Verilog dataflow definitions"
    VERSION = pyverilog.utils.version.VERSION
    USAGE = "Usage: python codegen.py -t TOPMODULE file ..."

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
                         default="helperthread.v",help="Output File name, Default=helperthread.v")
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

    codegen = VerilogCodeGenerator(options.topmodule, terms, binddict,
                                   resolved_terms, resolved_binddict, constlist)
    codegen.set_clock_info(options.clockname, options.clockedge)
    codegen.set_reset_info(options.resetname, options.resetedge)
    code = codegen.generateCode(options.searchtarget)

    f = open(options.outputfile, 'w')
    f.write(code)
    f.close()
