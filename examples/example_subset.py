from __future__ import absolute_import
from __future__ import print_function
import sys
import os
from optparse import OptionParser

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyverilog
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer
from pyverilog.dataflow.optimizer import VerilogDataflowOptimizer
from pyverilog.dataflow.subset import VerilogSubset


def main():
    INFO = "Subset generator from Verilog dataflow definitions"
    VERSION = pyverilog.__version__
    USAGE = "Usage: python example_subset.py -t TOPMODULE file ..."

    def showVersion():
        print(INFO)
        print(VERSION)
        print(USAGE)
        sys.exit()

    optparser = OptionParser()
    optparser.add_option("-v", "--version", action="store_true", dest="showversion",
                         default=False, help="Show the version")
    optparser.add_option("-I", "--include", dest="include", action="append",
                         default=[], help="Include path")
    optparser.add_option("-D", dest="define", action="append",
                         default=[], help="Macro Definition")
    optparser.add_option("-t", "--top", dest="topmodule",
                         default="TOP", help="Top module, Default=TOP")
    optparser.add_option("--nobind", action="store_true", dest="nobind",
                         default=False, help="No binding traversal, Default=False")
    optparser.add_option("--noreorder", action="store_true", dest="noreorder",
                         default=False, help="No reordering of binding dataflow, Default=False")
    optparser.add_option("-s", "--search", dest="searchtarget", action="append",
                         default=[], help="Search Target Signal")
    optparser.add_option("--clockname", dest="clockname",
                         default="CLK", help="Clock signal name")
    optparser.add_option("--resetname", dest="resetname",
                         default="RST_X", help="Reset signal name")
    optparser.add_option("--clockedge", dest="clockedge",
                         default="posedge", help="Clock signal edge")
    optparser.add_option("--resetedge", dest="resetedge",
                         default="negedge", help="Reset signal edge")
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
    terms, parameter, assign, always_clockedge, always_combination = subset.getSubset(
        options.searchtarget)

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


if __name__ == '__main__':
    main()
