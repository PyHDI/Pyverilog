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
TOP.RST_X: TOP_RST_X
TOP.cnt: (((!TOP_RST_X))? 'd0 : (((!TOP_RST_X))? TOP_cnt : (((&TOP_al_block0_al_block2_al_functioncall0_inc))? 'd0 : (((!TOP_RST_X))? (TOP_cnt+'d1) : (TOP_cnt+'d1)))))
TOP.md_always0.al_block0.al_if0_ELSE.al_block2.al_functioncall0._rn0_inc: 'd0
TOP.md_always0.al_block0.al_if0_ELSE.al_block2.al_functioncall0._rn1_inc: (((!TOP_RST_X))? (TOP_al_block0_al_block2_al_functioncall0__rn1_inc+'d1) : (TOP_cnt+'d1))
TOP.md_always0.al_block0.al_if0_ELSE.al_block2.al_functioncall0.in: (((!TOP_RST_X))? TOP_al_block0_al_block2_al_functioncall0_in : TOP_cnt)
TOP.md_always0.al_block0.al_if0_ELSE.al_block2.al_functioncall0.inc: (((!TOP_RST_X))? TOP_al_block0_al_block2_al_functioncall0_inc : (((!TOP_RST_X))? (((&TOP_al_block0_al_block2_al_functioncall0_inc))? 'd0 : (((!TOP_RST_X))? (TOP_al_block0_al_block2_al_functioncall0_inc+'d1) : (TOP_cnt+'d1))) : (((&TOP_al_block0_al_block2_al_functioncall0_inc))? (((!TOP_RST_X))? (TOP_al_block0_al_block2_al_functioncall0_inc+'d1) : (TOP_cnt+'d1)) : (((!TOP_RST_X))? (((&(TOP_al_block0_al_block2_al_functioncall0_inc+'d1)))? 'd0 : (((!TOP_RST_X))? (TOP_al_block0_al_block2_al_functioncall0_inc+'d1) : (TOP_cnt+'d1))) : (((&(TOP_cnt+'d1)))? 'd0 : (((!TOP_RST_X))? (TOP_al_block0_al_block2_al_functioncall0_inc+'d1) : (TOP_cnt+'d1)))))))
"""

def test():
    filelist = [codedir + 'function.v']
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
