from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer

codedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
(Bind dest:TOP._rn0_i tree:(IntConst 0))
(Bind dest:TOP._rn1_i tree:(Operator Plus Next:'d0,(IntConst 1)))
(Bind dest:TOP._rn2_i tree:(Operator Plus Next:'d1,(IntConst 1)))
(Bind dest:TOP._rn3_i tree:(Operator Plus Next:'d2,(IntConst 1)))
(Bind dest:TOP._rn4_i tree:(Operator Plus Next:'d3,(IntConst 1)))
(Bind dest:TOP.i tree:(Terminal TOP._rn4_i))
(Bind dest:TOP.mem msb:'d1 lsb:'d0 ptr:(Terminal TOP.IN) \
tree:(Operator Plus Next:(Partselect Var:(Pointer Var:(Terminal TOP.mem) PTR:(Terminal TOP.IN)) MSB:(Operator Minus Next:(Operator Times Next:(IntConst 2),(Operator Plus Next:'d0,(IntConst 1))),(IntConst 1)) LSB:(Operator Times Next:(IntConst 2),'d0)),(IntConst 2'b1)))
(Bind dest:TOP.mem msb:'d3 lsb:'d2 ptr:(Terminal TOP.IN) \
tree:(Operator Plus Next:(Partselect Var:(Pointer Var:(Terminal TOP.mem) PTR:(Terminal TOP.IN)) MSB:(Operator Minus Next:(Operator Times Next:(IntConst 2),(Operator Plus Next:'d1,(IntConst 1))),(IntConst 1)) LSB:(Operator Times Next:(IntConst 2),'d1)),(IntConst 2'b1)))
(Bind dest:TOP.mem msb:'d5 lsb:'d4 ptr:(Terminal TOP.IN) \
tree:(Operator Plus Next:(Partselect Var:(Pointer Var:(Terminal TOP.mem) PTR:(Terminal TOP.IN)) MSB:(Operator Minus Next:(Operator Times Next:(IntConst 2),(Operator Plus Next:'d2,(IntConst 1))),(IntConst 1)) LSB:(Operator Times Next:(IntConst 2),'d2)),(IntConst 2'b1)))
(Bind dest:TOP.mem msb:'d7 lsb:'d6 ptr:(Terminal TOP.IN) \
tree:(Operator Plus Next:(Partselect Var:(Pointer Var:(Terminal TOP.mem) PTR:(Terminal TOP.IN)) MSB:(Operator Minus Next:(Operator Times Next:(IntConst 2),(Operator Plus Next:'d3,(IntConst 1))),(IntConst 1)) LSB:(Operator Times Next:(IntConst 2),'d3)),(IntConst 2'b1)))
"""

def test():
    filelist = [codedir + 'partial.v']
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
