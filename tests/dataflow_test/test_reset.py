import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer

codedir = '../../testcode/'

expected = """\
"""

def test():
    filelist = [codedir + 'reset.v']
    topmodule = 'TOP'
    noreorder = False
    nobind = False
    include = None
    define = None

    analyzer = VerilogDataflowAnalyzer(filelist, topmodule,
                                       noreorder=noreorder,
                                       nobind=nobind,
                                       preprocess_include=include,
                                       preprocess_define=define)
    analyzer.generate()
    #TODO Current version is for only display.
##    directives = analyzer.get_directives()
##    instances = analyzer.getInstances()
##    terms = analyzer.getTerms()
##    binddict = analyzer.getBinddict()
##
##    output = []
##    output.append(list(binddict.values())[0][0].tostr())
##    output.append('\n')
##
##    rslt = ''.join(output)
##
##    print(rslt)
##    for key, verb in binddict.items():
##        if verb[0].getResetName() is None:
##            print(str(key) + ': None')
##        else:
##            print(str(key) + ': ' + verb[0].getResetEdge() + str(verb[0].getResetName()) +
##              '[' + str(verb[0].getResetBit()) + ']')



if __name__ == '__main__':
    test()
