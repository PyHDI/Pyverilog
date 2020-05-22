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


def main():
    INFO = "Verilog dataflow optimizer with Pyverilog"
    VERSION = pyverilog.__version__
    USAGE = "Usage: python example_optimizer.py -t TOPMODULE file ..."

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
    (options, args) = optparser.parse_args()

    filelist = args
    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f):
            raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()

    analyzer = VerilogDataflowAnalyzer(filelist, options.topmodule)
    analyzer.generate()

    directives = analyzer.get_directives()
    terms = analyzer.getTerms()
    binddict = analyzer.getBinddict()

    optimizer = VerilogDataflowOptimizer(terms, binddict)
    optimizer.resolveConstant()

    resolved_terms = optimizer.getResolvedTerms()
    resolved_binddict = optimizer.getResolvedBinddict()
    constlist = optimizer.getConstlist()

    print('Directive:')
    for dr in directives:
        print(dr)

    print('Term:')
    for tk, tv in sorted(resolved_terms.items(), key=lambda x: len(x[0])):
        print(tv.tostr())

    print('Bind:')
    for bk, bv in sorted(resolved_binddict.items(), key=lambda x: len(x[0])):
        for bvi in bv:
            print(bvi.tostr())

    print('Const:')
    for ck, cv in sorted(constlist.items(), key=lambda x: len(x[0])):
        print(ck, cv)


if __name__ == '__main__':
    main()
