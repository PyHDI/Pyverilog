from __future__ import absolute_import
from __future__ import print_function
import sys
import os
from optparse import OptionParser

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyverilog
import pyverilog.utils.util as util
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer
from pyverilog.dataflow.optimizer import VerilogDataflowOptimizer
from pyverilog.controlflow.controlflow_analyzer import VerilogControlflowAnalyzer


def main():
    INFO = "Control-flow analyzer for Verilog definitions"
    VERSION = pyverilog.__version__
    USAGE = "Usage: python example_controlflow_analyzer.py -t TOPMODULE file ..."

    def showVersion():
        print(INFO)
        print(VERSION)
        print(USAGE)
        sys.exit()

    optparser = OptionParser()
    optparser.add_option("-v", "--version", action="store_true", dest="showversion",
                         default=False, help="Show the version")
    optparser.add_option("-t", "--top", dest="topmodule",
                         default="TOP", help="Top module, Default=TOP")
    optparser.add_option("-s", "--search", dest="searchtarget", action="append",
                         default=[], help="Search Target Signal")
    optparser.add_option("--graphformat", dest="graphformat",
                         default="png", help="Graph file format, Default=png")
    optparser.add_option("--nograph", action="store_true", dest="nograph",
                         default=False, help="Non graph generation")
    optparser.add_option("--nolabel", action="store_true", dest="nolabel",
                         default=False, help="State Machine Graph without Labels")
    optparser.add_option("-I", "--include", dest="include", action="append",
                         default=[], help="Include path")
    optparser.add_option("-D", dest="define", action="append",
                         default=[], help="Macro Definition")
    (options, args) = optparser.parse_args()

    filelist = args
    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f):
            raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()

    analyzer = VerilogDataflowAnalyzer(filelist, options.topmodule,
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
    fsm_vars = tuple(['fsm', 'state', 'count', 'cnt', 'step', 'mode'] + options.searchtarget)

    canalyzer = VerilogControlflowAnalyzer(options.topmodule, terms, binddict,
                                           resolved_terms, resolved_binddict, constlist, fsm_vars)
    fsms = canalyzer.getFiniteStateMachines()

    for signame, fsm in fsms.items():
        print('# SIGNAL NAME: %s' % signame)
        print('# DELAY CNT: %d' % fsm.delaycnt)
        fsm.view()
        if not options.nograph:
            fsm.tograph(filename=util.toFlatname(signame) + '.' +
                        options.graphformat, nolabel=options.nolabel)
        loops = fsm.get_loop()
        print('Loop')
        for loop in loops:
            print(loop)


if __name__ == '__main__':
    main()
