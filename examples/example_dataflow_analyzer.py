from __future__ import absolute_import
from __future__ import print_function
import sys
import os
from optparse import OptionParser

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyverilog
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer


def main():
    INFO = "Verilog module signal/module dataflow analyzer"
    VERSION = pyverilog.__version__
    USAGE = "Usage: python example_dataflow_analyzer.py -t TOPMODULE file ..."

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
    print('Directive:')
    for dr in sorted(directives, key=lambda x: str(x)):
        print(dr)

    instances = analyzer.getInstances()
    print('Instance:')
    for module, instname in sorted(instances, key=lambda x: str(x[1])):
        print((module, instname))

    if options.nobind:
        print('Signal:')
        signals = analyzer.getSignals()
        for sig in signals:
            print(sig)

        print('Const:')
        consts = analyzer.getConsts()
        for con in consts:
            print(con)

    else:
        terms = analyzer.getTerms()
        print('Term:')
        for tk, tv in sorted(terms.items(), key=lambda x: str(x[0])):
            print(tv.tostr())

        binddict = analyzer.getBinddict()
        print('Bind:')
        for bk, bv in sorted(binddict.items(), key=lambda x: str(x[0])):
            for bvi in bv:
                print(bvi.tostr())


if __name__ == '__main__':
    main()
