from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer
from pyverilog.dataflow.optimizer import VerilogDataflowOptimizer
from pyverilog.controlflow.controlflow_analyzer import VerilogControlflowAnalyzer

codedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
TOP.CLK: TOP_CLK
TOP.RST: TOP_RST
TOP.in1: TOP_reg3['d6:'d5]
TOP.in2: TOP_in2
TOP.reg1: TOP_reg3['d6:'d5]
TOP.reg3: ((TOP_RST)? 3'd0 : 3'd1)
"""

def test():
    filelist = [codedir + 'partselect_assign.v']
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

    optimizer = VerilogDataflowOptimizer(terms, binddict)
    optimizer.resolveConstant()

    c_analyzer = VerilogControlflowAnalyzer(topmodule, terms,
                                            binddict,
                                            resolved_terms=optimizer.getResolvedTerms(),
                                            resolved_binddict=optimizer.getResolvedBinddict(),
                                            constlist=optimizer.getConstlist()
                                            )

    output = []
    for tk in sorted(c_analyzer.resolved_terms.keys(), key=lambda x:str(x)):
        tree = c_analyzer.makeTree(tk)
        output.append(str(tk) + ': ' + tree.tocode())

    rslt = '\n'.join(output) + '\n'

    print(rslt)
    
    assert(expected == rslt)

if __name__ == '__main__':
    test()
