from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer
from pyverilog.dataflow.optimizer import VerilogDataflowOptimizer
from pyverilog.controlflow.controlflow_analyzer import VerilogControlflowAnalyzer

codedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
TOP.IN1: TOP_IN1
TOP.SEL: TOP_SEL
TOP.bit: (((TOP_SEL=='d0))? TOP_IN1 : 1'd0)
TOP.md_always0.al_block0.al_functioncall0._rn0_func1: TOP_IN1
TOP.md_always0.al_block0.al_functioncall0._rn1_func1: 1'd0
TOP.md_always0.al_block0.al_functioncall0.func1: (((TOP_SEL=='d0))? TOP_IN1 : 1'd0)
TOP.md_always0.al_block0.al_functioncall0.in1: TOP_IN1
TOP.md_always0.al_block0.al_functioncall0.sel: TOP_SEL
"""

def test():
    filelist = [codedir + 'case_in_func.v']
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
