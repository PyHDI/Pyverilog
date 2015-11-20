from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer

codedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
(Bind dest:TOP.WD tree:(IntConst 4))
(Bind dest:TOP._rn0_j tree:(IntConst 0))
(Bind dest:TOP._rn1_j tree:(Operator Plus Next:'d0,(IntConst 1)))
(Bind dest:TOP._rn2_j tree:(Operator Plus Next:'d1,(IntConst 1)))
(Bind dest:TOP._rn3_j tree:(Operator Plus Next:'d2,(IntConst 1)))
(Bind dest:TOP._rn4_j tree:(Operator Plus Next:'d3,(IntConst 1)))
(Bind dest:TOP.j tree:(Terminal TOP._rn4_j))
(Bind dest:TOP.md_generate0.ge_for0[0].subloop.ge_if0._subt.tmp \
tree:(Branch Cond:(Operator Eq Next:'d0,(IntConst 0)) \
True:(Operator Unot Next:(Partselect Var:(Terminal TOP.subin) MSB:'d0 LSB:'d0))))
(Bind dest:TOP.subout msb:'d0 lsb:'d0 \
tree:(Branch Cond:(Operator Eq Next:'d0,(IntConst 0)) \
True:(Partselect Var:(Terminal TOP.subin) MSB:'d0 LSB:'d0)))
(Bind dest:TOP.subout msb:'d1 lsb:'d1 \
tree:(Branch Cond:(Operator Eq Next:'d1,(IntConst 0)) \
False:(Branch Cond:(Operator Eq Next:'d1,(IntConst 1)) \
True:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[0].subloop.ge_if0._subt.tmp),(Partselect Var:(Terminal TOP.subin) MSB:'d1 LSB:'d1)))))
(Bind dest:TOP.subout msb:'d2 lsb:'d2 \
tree:(Branch Cond:(Operator Eq Next:'d2,(IntConst 0)) \
False:(Branch Cond:(Operator Eq Next:'d2,(IntConst 1)) \
False:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[1].subloop.ge_if1_ELSE._subf.tmp),(Partselect Var:(Terminal TOP.subin) MSB:'d2 LSB:'d2)))))
(Bind dest:TOP.subout msb:'d3 lsb:'d3 \
tree:(Branch Cond:(Operator Eq Next:'d3,(IntConst 0)) \
False:(Branch Cond:(Operator Eq Next:'d3,(IntConst 1)) \
False:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[2].subloop.ge_if3_ELSE._subf.tmp),(Partselect Var:(Terminal TOP.subin) MSB:'d3 LSB:'d3)))))
"""

def test():
    filelist = [codedir + 'generate.v']
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
            
    for bk, bv in sorted(binddict.items(), key=lambda x:str(x[0])):
        for bvi in bv:
            output.append(bvi.tostr())
            output.append('\n')
            
    rslt = ''.join(output)

    print(rslt)
    assert(expected == rslt)

if __name__ == '__main__':
    test()
