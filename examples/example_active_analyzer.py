from __future__ import absolute_import
from __future__ import print_function
import sys
import os
from optparse import OptionParser

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyverilog
import pyverilog.utils.util as util
import pyverilog.controlflow.splitter as splitter
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer
from pyverilog.dataflow.optimizer import VerilogDataflowOptimizer
from pyverilog.controlflow.active_analyzer import VerilogActiveConditionAnalyzer


def main():
    INFO = "Active condition analyzer"
    VERSION = pyverilog.__version__
    USAGE = "Usage: python example_active_analyzer.py -t TOPMODULE file ..."

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

    canalyzer = VerilogActiveConditionAnalyzer(options.topmodule, terms, binddict,
                                               resolved_terms, resolved_binddict, constlist)

    for target in options.searchtarget:
        signal = util.toTermname(target)

        active_conditions = canalyzer.getActiveConditions(signal)
        #active_conditions = canalyzer.getActiveConditions( signal, condition=splitter.active_modify )
        #active_conditions = canalyzer.getActiveConditions( signal, condition=splitter.active_unmodify )

        print('Active Cases: %s' % signal)
        for fsm_sig, active_conditions in sorted(active_conditions.items(), key=lambda x: str(x[0])):
            print('FSM: %s' % fsm_sig)
            for state, active_condition in sorted(active_conditions, key=lambda x: str(x[0])):
                s = []
                s.append('state: %d -> ' % state)
                if active_condition:
                    s.append(active_condition.tocode())
                else:
                    s.append('empty')
                print(''.join(s))


if __name__ == '__main__':
    main()
