from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer

codedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
(Bind dest:TOP.LEN tree:(IntConst 8))
(Bind dest:TOP.OUT0 tree:(Pointer Var:(Terminal TOP.out) PTR:(IntConst 0)))
(Bind dest:TOP.OUT1 tree:(Pointer Var:(Terminal TOP.out) PTR:(IntConst 1)))
(Bind dest:TOP.OUT2 tree:(Pointer Var:(Terminal TOP.out) PTR:(IntConst 2)))
(Bind dest:TOP.OUT3 tree:(Pointer Var:(Terminal TOP.out) PTR:(IntConst 3)))
(Bind dest:TOP.OUT4 tree:(Pointer Var:(Terminal TOP.out) PTR:(IntConst 4)))
(Bind dest:TOP.WA tree:(IntConst 32))
(Bind dest:TOP.WD tree:(IntConst 4))
(Bind dest:TOP._rn0_i tree:(IntConst 0))
(Bind dest:TOP._rn12_i tree:(Operator Plus Next:'d1,(IntConst 1)))
(Bind dest:TOP._rn18_i tree:(Operator Plus Next:'d2,(IntConst 1)))
(Bind dest:TOP._rn24_i tree:(Operator Plus Next:'d3,(IntConst 1)))
(Bind dest:TOP._rn30_i tree:(Operator Plus Next:'d4,(IntConst 1)))
(Bind dest:TOP._rn6_i tree:(Operator Plus Next:'d0,(IntConst 1)))
(Bind dest:TOP.cnt tree:(Branch Cond:(Operator Ulnot Next:(Terminal TOP.RST_X)) True:(IntConst 0) False:(Branch Cond:(Operator LessThan Next:(Terminal TOP.cnt),(IntConst 4)) True:(Operator Plus Next:(Terminal TOP.cnt),(IntConst 1)) False:(IntConst 0))))
(Bind dest:TOP.i tree:(Terminal TOP._rn30_i))
(Bind dest:TOP.in ptr:'d0 tree:(Terminal TOP.IN0))
(Bind dest:TOP.in ptr:'d1 tree:(Terminal TOP.IN1))
(Bind dest:TOP.in ptr:'d2 tree:(Terminal TOP.IN2))
(Bind dest:TOP.in ptr:'d3 tree:(Terminal TOP.IN3))
(Bind dest:TOP.in ptr:'d4 tree:(Terminal TOP.IN4))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub.CLK tree:(Terminal TOP.CLK))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub.RST_X tree:(Terminal TOP.RST_X))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub.WD tree:(Terminal TOP.WD))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub._rn1_j tree:(IntConst 0))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub._rn2_j tree:(Operator Plus Next:'d0,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub._rn3_j tree:(Operator Plus Next:'d1,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub._rn4_j tree:(Operator Plus Next:'d2,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub._rn5_j tree:(Operator Plus Next:'d3,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub.j tree:(Terminal TOP.md_generate0.ge_for0[0].loop.sub._rn5_j))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub.md_generate1.ge_for1[0].subloop.ge_if0._subt.tmp tree:(Branch Cond:(Operator Eq Next:'d0,(IntConst 0)) True:(Operator Unot Next:(Partselect Var:(Terminal TOP.md_generate0.ge_for0[0].loop.sub.subin) MSB:'d0 LSB:'d0))))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub.subin tree:(Pointer Var:(Terminal TOP.in) PTR:(Terminal TOP.cnt)))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub.subout msb:'d0 lsb:'d0 tree:(Branch Cond:(Operator Eq Next:'d0,(IntConst 0)) True:(Partselect Var:(Terminal TOP.md_generate0.ge_for0[0].loop.sub.subin) MSB:'d0 LSB:'d0)))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub.subout msb:'d1 lsb:'d1 tree:(Branch Cond:(Operator Eq Next:'d1,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d1,(IntConst 1)) True:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[0].loop.sub.md_generate1.ge_for1[0].subloop.ge_if0._subt.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[0].loop.sub.subin) MSB:'d1 LSB:'d1)))))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub.subout msb:'d2 lsb:'d2 tree:(Branch Cond:(Operator Eq Next:'d2,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d2,(IntConst 1)) False:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[0].loop.sub.md_generate1.ge_for1[1].subloop.ge_if1_ELSE._subf.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[0].loop.sub.subin) MSB:'d2 LSB:'d2)))))
(Bind dest:TOP.md_generate0.ge_for0[0].loop.sub.subout msb:'d3 lsb:'d3 tree:(Branch Cond:(Operator Eq Next:'d3,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d3,(IntConst 1)) False:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[0].loop.sub.md_generate1.ge_for1[2].subloop.ge_if3_ELSE._subf.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[0].loop.sub.subin) MSB:'d3 LSB:'d3)))))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub.CLK tree:(Terminal TOP.CLK))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub.RST_X tree:(Terminal TOP.RST_X))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub.WD tree:(Terminal TOP.WD))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub._rn10_j tree:(Operator Plus Next:'d2,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub._rn11_j tree:(Operator Plus Next:'d3,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub._rn7_j tree:(IntConst 0))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub._rn8_j tree:(Operator Plus Next:'d0,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub._rn9_j tree:(Operator Plus Next:'d1,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub.j tree:(Terminal TOP.md_generate0.ge_for0[1].loop.sub._rn11_j))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub.md_generate2.ge_for2[0].subloop.ge_if7._subt.tmp tree:(Branch Cond:(Operator Eq Next:'d0,(IntConst 0)) True:(Operator Unot Next:(Partselect Var:(Terminal TOP.md_generate0.ge_for0[1].loop.sub.subin) MSB:'d0 LSB:'d0))))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub.subin tree:(Pointer Var:(Terminal TOP.in) PTR:(Terminal TOP.cnt)))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub.subout msb:'d0 lsb:'d0 tree:(Branch Cond:(Operator Eq Next:'d0,(IntConst 0)) True:(Partselect Var:(Terminal TOP.md_generate0.ge_for0[1].loop.sub.subin) MSB:'d0 LSB:'d0)))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub.subout msb:'d1 lsb:'d1 tree:(Branch Cond:(Operator Eq Next:'d1,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d1,(IntConst 1)) True:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[1].loop.sub.md_generate2.ge_for2[0].subloop.ge_if7._subt.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[1].loop.sub.subin) MSB:'d1 LSB:'d1)))))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub.subout msb:'d2 lsb:'d2 tree:(Branch Cond:(Operator Eq Next:'d2,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d2,(IntConst 1)) False:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[1].loop.sub.md_generate2.ge_for2[1].subloop.ge_if8_ELSE._subf.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[1].loop.sub.subin) MSB:'d2 LSB:'d2)))))
(Bind dest:TOP.md_generate0.ge_for0[1].loop.sub.subout msb:'d3 lsb:'d3 tree:(Branch Cond:(Operator Eq Next:'d3,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d3,(IntConst 1)) False:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[1].loop.sub.md_generate2.ge_for2[2].subloop.ge_if10_ELSE._subf.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[1].loop.sub.subin) MSB:'d3 LSB:'d3)))))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub.CLK tree:(Terminal TOP.CLK))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub.RST_X tree:(Terminal TOP.RST_X))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub.WD tree:(Terminal TOP.WD))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub._rn13_j tree:(IntConst 0))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub._rn14_j tree:(Operator Plus Next:'d0,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub._rn15_j tree:(Operator Plus Next:'d1,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub._rn16_j tree:(Operator Plus Next:'d2,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub._rn17_j tree:(Operator Plus Next:'d3,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub.j tree:(Terminal TOP.md_generate0.ge_for0[2].loop.sub._rn17_j))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub.md_generate3.ge_for3[0].subloop.ge_if14._subt.tmp tree:(Branch Cond:(Operator Eq Next:'d0,(IntConst 0)) True:(Operator Unot Next:(Partselect Var:(Terminal TOP.md_generate0.ge_for0[2].loop.sub.subin) MSB:'d0 LSB:'d0))))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub.subin tree:(Pointer Var:(Terminal TOP.in) PTR:(Terminal TOP.cnt)))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub.subout msb:'d0 lsb:'d0 tree:(Branch Cond:(Operator Eq Next:'d0,(IntConst 0)) True:(Partselect Var:(Terminal TOP.md_generate0.ge_for0[2].loop.sub.subin) MSB:'d0 LSB:'d0)))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub.subout msb:'d1 lsb:'d1 tree:(Branch Cond:(Operator Eq Next:'d1,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d1,(IntConst 1)) True:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[2].loop.sub.md_generate3.ge_for3[0].subloop.ge_if14._subt.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[2].loop.sub.subin) MSB:'d1 LSB:'d1)))))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub.subout msb:'d2 lsb:'d2 tree:(Branch Cond:(Operator Eq Next:'d2,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d2,(IntConst 1)) False:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[2].loop.sub.md_generate3.ge_for3[1].subloop.ge_if15_ELSE._subf.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[2].loop.sub.subin) MSB:'d2 LSB:'d2)))))
(Bind dest:TOP.md_generate0.ge_for0[2].loop.sub.subout msb:'d3 lsb:'d3 tree:(Branch Cond:(Operator Eq Next:'d3,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d3,(IntConst 1)) False:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[2].loop.sub.md_generate3.ge_for3[2].subloop.ge_if17_ELSE._subf.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[2].loop.sub.subin) MSB:'d3 LSB:'d3)))))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub.CLK tree:(Terminal TOP.CLK))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub.RST_X tree:(Terminal TOP.RST_X))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub.WD tree:(Terminal TOP.WD))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub._rn19_j tree:(IntConst 0))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub._rn20_j tree:(Operator Plus Next:'d0,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub._rn21_j tree:(Operator Plus Next:'d1,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub._rn22_j tree:(Operator Plus Next:'d2,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub._rn23_j tree:(Operator Plus Next:'d3,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub.j tree:(Terminal TOP.md_generate0.ge_for0[3].loop.sub._rn23_j))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub.md_generate4.ge_for4[0].subloop.ge_if21._subt.tmp tree:(Branch Cond:(Operator Eq Next:'d0,(IntConst 0)) True:(Operator Unot Next:(Partselect Var:(Terminal TOP.md_generate0.ge_for0[3].loop.sub.subin) MSB:'d0 LSB:'d0))))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub.subin tree:(Pointer Var:(Terminal TOP.in) PTR:(Terminal TOP.cnt)))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub.subout msb:'d0 lsb:'d0 tree:(Branch Cond:(Operator Eq Next:'d0,(IntConst 0)) True:(Partselect Var:(Terminal TOP.md_generate0.ge_for0[3].loop.sub.subin) MSB:'d0 LSB:'d0)))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub.subout msb:'d1 lsb:'d1 tree:(Branch Cond:(Operator Eq Next:'d1,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d1,(IntConst 1)) True:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[3].loop.sub.md_generate4.ge_for4[0].subloop.ge_if21._subt.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[3].loop.sub.subin) MSB:'d1 LSB:'d1)))))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub.subout msb:'d2 lsb:'d2 tree:(Branch Cond:(Operator Eq Next:'d2,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d2,(IntConst 1)) False:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[3].loop.sub.md_generate4.ge_for4[1].subloop.ge_if22_ELSE._subf.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[3].loop.sub.subin) MSB:'d2 LSB:'d2)))))
(Bind dest:TOP.md_generate0.ge_for0[3].loop.sub.subout msb:'d3 lsb:'d3 tree:(Branch Cond:(Operator Eq Next:'d3,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d3,(IntConst 1)) False:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[3].loop.sub.md_generate4.ge_for4[2].subloop.ge_if24_ELSE._subf.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[3].loop.sub.subin) MSB:'d3 LSB:'d3)))))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub.CLK tree:(Terminal TOP.CLK))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub.RST_X tree:(Terminal TOP.RST_X))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub.WD tree:(Terminal TOP.WD))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub._rn25_j tree:(IntConst 0))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub._rn26_j tree:(Operator Plus Next:'d0,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub._rn27_j tree:(Operator Plus Next:'d1,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub._rn28_j tree:(Operator Plus Next:'d2,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub._rn29_j tree:(Operator Plus Next:'d3,(IntConst 1)))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub.j tree:(Terminal TOP.md_generate0.ge_for0[4].loop.sub._rn29_j))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub.md_generate5.ge_for5[0].subloop.ge_if28._subt.tmp tree:(Branch Cond:(Operator Eq Next:'d0,(IntConst 0)) True:(Operator Unot Next:(Partselect Var:(Terminal TOP.md_generate0.ge_for0[4].loop.sub.subin) MSB:'d0 LSB:'d0))))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub.subin tree:(Pointer Var:(Terminal TOP.in) PTR:(Terminal TOP.cnt)))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub.subout msb:'d0 lsb:'d0 tree:(Branch Cond:(Operator Eq Next:'d0,(IntConst 0)) True:(Partselect Var:(Terminal TOP.md_generate0.ge_for0[4].loop.sub.subin) MSB:'d0 LSB:'d0)))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub.subout msb:'d1 lsb:'d1 tree:(Branch Cond:(Operator Eq Next:'d1,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d1,(IntConst 1)) True:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[4].loop.sub.md_generate5.ge_for5[0].subloop.ge_if28._subt.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[4].loop.sub.subin) MSB:'d1 LSB:'d1)))))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub.subout msb:'d2 lsb:'d2 tree:(Branch Cond:(Operator Eq Next:'d2,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d2,(IntConst 1)) False:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[4].loop.sub.md_generate5.ge_for5[1].subloop.ge_if29_ELSE._subf.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[4].loop.sub.subin) MSB:'d2 LSB:'d2)))))
(Bind dest:TOP.md_generate0.ge_for0[4].loop.sub.subout msb:'d3 lsb:'d3 tree:(Branch Cond:(Operator Eq Next:'d3,(IntConst 0)) False:(Branch Cond:(Operator Eq Next:'d3,(IntConst 1)) False:(Operator Xor Next:(Terminal TOP.md_generate0.ge_for0[4].loop.sub.md_generate5.ge_for5[2].subloop.ge_if31_ELSE._subf.tmp),(Partselect Var:(Terminal TOP.md_generate0.ge_for0[4].loop.sub.subin) MSB:'d3 LSB:'d3)))))
(Bind dest:TOP.out ptr:'d0 tree:(Terminal TOP.md_generate0.ge_for0[0].loop.sub.subout))
(Bind dest:TOP.out ptr:'d1 tree:(Terminal TOP.md_generate0.ge_for0[1].loop.sub.subout))
(Bind dest:TOP.out ptr:'d2 tree:(Terminal TOP.md_generate0.ge_for0[2].loop.sub.subout))
(Bind dest:TOP.out ptr:'d3 tree:(Terminal TOP.md_generate0.ge_for0[3].loop.sub.subout))
(Bind dest:TOP.out ptr:'d4 tree:(Terminal TOP.md_generate0.ge_for0[4].loop.sub.subout))
"""

def test():
    filelist = [codedir + 'generate_instance.v']
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
