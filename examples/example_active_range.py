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
from pyverilog.controlflow.active_range import VerilogActiveAnalyzer


def main():
    INFO = "Active condition analyzer (Obsoluted)"
    VERSION = pyverilog.__version__
    USAGE = "Usage: python example_active_range.py -t TOPMODULE file ..."

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

    aanalyzer = VerilogActiveAnalyzer(options.topmodule, terms, binddict,
                                      resolved_terms, resolved_binddict, constlist)

    for target in options.searchtarget:
        signal = util.toTermname(target)

        print('Active Conditions: %s' % signal)
        active_conditions = aanalyzer.getActiveConditions(signal)
        print(sorted(active_conditions, key=lambda x: str(x)))

        print('Changed Conditions')
        changed_conditions = aanalyzer.getChangedConditions(signal)
        print(sorted(changed_conditions, key=lambda x: str(x)))

        print('Changed Condition Dict')
        changed_conditiondict = aanalyzer.getChangedConditionsWithAssignments(signal)
        print(sorted(changed_conditiondict.items(), key=lambda x: str(x[0])))

        print('Unchanged Conditions')
        unchanged_conditions = aanalyzer.getUnchangedConditions(signal)
        print(sorted(unchanged_conditions, key=lambda x: str(x)))


if __name__ == '__main__':
    main()
