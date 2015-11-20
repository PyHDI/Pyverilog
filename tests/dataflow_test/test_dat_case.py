from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer

codedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
(Bind dest:TOP.cnt \
tree:(Branch Cond:(Terminal TOP.RST) \
True:(IntConst 0) \
False:(Branch Cond:(Operator Lor Next:(Operator Lor Next:(Operator Eq Next:(Terminal TOP.cnt),(IntConst 'h0)),\
(Operator Eq Next:(Terminal TOP.cnt),(IntConst 'h1))),(Operator Eq Next:(Terminal TOP.cnt),(IntConst 'h2))) \
True:(Operator Plus Next:(Terminal TOP.cnt),(IntConst 1)) \
False:(Branch Cond:(Operator Eq Next:(Terminal TOP.cnt),(IntConst 'hff)) \
True:(IntConst 0) False:(Branch Cond:(IntConst 1) \
True:(Operator Plus Next:(Terminal TOP.cnt),(IntConst 1)))))))
"""

def test():
    filelist = [codedir + 'case.v']
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

    directives = analyzer.get_directives()
    instances = analyzer.getInstances()
    terms = analyzer.getTerms()
    binddict = analyzer.getBinddict()

    output = []
    output.append(list(binddict.values())[0][0].tostr())
    output.append('\n')
            
    rslt = ''.join(output)

    print(rslt)
    assert(expected == rslt)

if __name__ == '__main__':
    test()
