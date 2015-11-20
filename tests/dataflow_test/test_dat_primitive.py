from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer

codedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
(Bind dest:TOP.out0 \
tree:(Operator Uand Next:(Concat Next:(Partselect Var:(Terminal TOP.in1) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in2) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in3) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in4) MSB:(IntConst 0) LSB:(IntConst 0)))))
(Bind dest:TOP.out1 \
tree:(Operator Unand Next:(Concat Next:(Partselect Var:(Terminal TOP.in1) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in2) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in3) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in4) MSB:(IntConst 0) LSB:(IntConst 0)))))
(Bind dest:TOP.out2 \
tree:(Operator Uor Next:(Concat Next:(Partselect Var:(Terminal TOP.in1) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in2) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in3) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in4) MSB:(IntConst 0) LSB:(IntConst 0)))))
(Bind dest:TOP.out3 \
tree:(Operator Unor Next:(Concat Next:(Partselect Var:(Terminal TOP.in1) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in2) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in3) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in4) MSB:(IntConst 0) LSB:(IntConst 0)))))
(Bind dest:TOP.out4 \
tree:(Operator Uxor Next:(Concat Next:(Partselect Var:(Terminal TOP.in1) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in2) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in3) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in4) MSB:(IntConst 0) LSB:(IntConst 0)))))
(Bind dest:TOP.out5 \
tree:(Operator Uxnor Next:(Concat Next:(Partselect Var:(Terminal TOP.in1) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in2) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in3) MSB:(IntConst 0) LSB:(IntConst 0)),(Partselect Var:(Terminal TOP.in4) MSB:(IntConst 0) LSB:(IntConst 0)))))
(Bind dest:TOP.out6 \
tree:(Operator Ulnot Next:(Partselect Var:(Terminal TOP.in1) MSB:(IntConst 0) LSB:(IntConst 0))))
(Bind dest:TOP.out7 \
tree:(Partselect Var:(Terminal TOP.in1) MSB:(IntConst 0) LSB:(IntConst 0)))
"""

def test():
    filelist = [codedir + 'primitive.v']
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
