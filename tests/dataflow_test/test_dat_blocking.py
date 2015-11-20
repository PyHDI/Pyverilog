from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer

codedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
Directive:
Instance:
(TOP, 'TOP')
Term:
(Term name:TOP.CLK type:['Input'] msb:(IntConst 0) lsb:(IntConst 0))
(Term name:TOP.IN type:['Input'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:TOP.OUT type:['Output'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:TOP.RST_X type:['Input'] msb:(IntConst 0) lsb:(IntConst 0))
(Term name:TOP._rn0_ncnt type:['Rename'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:TOP._rn10_OUT type:['Rename'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:TOP._rn11_nstate type:['Rename'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:TOP._rn1_ctrljump type:['Rename'] msb:(IntConst 0) lsb:(IntConst 0))
(Term name:TOP._rn2_OUT type:['Rename'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:TOP._rn3_nstate type:['Rename'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:TOP._rn4_ncnt type:['Rename'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:TOP._rn5_ctrljump type:['Rename'] msb:(IntConst 0) lsb:(IntConst 0))
(Term name:TOP._rn6_OUT type:['Rename'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:TOP._rn7_nstate type:['Rename'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:TOP._rn8_ncnt type:['Rename'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:TOP._rn9_ctrljump type:['Rename'] msb:(IntConst 0) lsb:(IntConst 0))
(Term name:TOP.cnt type:['Reg'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:TOP.ctrljump type:['Reg'] msb:(IntConst 0) lsb:(IntConst 0))
(Term name:TOP.ncnt type:['Reg'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:TOP.nstate type:['Reg'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:TOP.state type:['Reg'] msb:(IntConst 7) lsb:(IntConst 0))
Bind:
(Bind dest:TOP.OUT \
tree:(Branch Cond:(Operator Eq Next:(Terminal TOP.state),(IntConst 0)) \
True:(Branch Cond:(Terminal TOP._rn1_ctrljump) \
True:(Terminal TOP._rn2_OUT)) \
False:(Branch Cond:(Operator Eq Next:(Terminal TOP.state),(IntConst 1)) \
True:(Branch Cond:(Terminal TOP._rn5_ctrljump) \
True:(Terminal TOP._rn6_OUT)) \
False:(Branch Cond:(Operator Eq Next:(Terminal TOP.state),(IntConst 2)) \
True:(Branch Cond:(Terminal TOP._rn9_ctrljump) \
True:(Terminal TOP._rn10_OUT))))))
(Bind dest:TOP._rn0_ncnt tree:(IntConst 0))
(Bind dest:TOP._rn10_OUT tree:(Operator Minus Next:(Terminal TOP.cnt),(IntConst 8)))
(Bind dest:TOP._rn11_nstate tree:(IntConst 0))
(Bind dest:TOP._rn1_ctrljump tree:(IntConst 1))
(Bind dest:TOP._rn2_OUT tree:(IntConst 8'h0))
(Bind dest:TOP._rn3_nstate tree:(IntConst 1))
(Bind dest:TOP._rn4_ncnt tree:(Operator Plus Next:(Terminal TOP.cnt),(IntConst 1)))
(Bind dest:TOP._rn5_ctrljump tree:(Operator GreaterThan Next:(Terminal TOP.cnt),(IntConst 7)))
(Bind dest:TOP._rn6_OUT tree:(Terminal TOP.cnt))
(Bind dest:TOP._rn7_nstate tree:(IntConst 2))
(Bind dest:TOP._rn8_ncnt tree:(Operator Plus Next:(Terminal TOP.cnt),(IntConst 2)))
(Bind dest:TOP._rn9_ctrljump tree:(Operator GreaterThan Next:(Terminal TOP.cnt),(IntConst 20)))
(Bind dest:TOP.cnt tree:(Branch Cond:(Operator Ulnot Next:(Terminal TOP.RST_X)) False:(Terminal TOP.ncnt)))
(Bind dest:TOP.ctrljump \
tree:(Branch Cond:(Operator Eq Next:(Terminal TOP.state),(IntConst 0)) \
True:(Terminal TOP._rn1_ctrljump) \
False:(Branch Cond:(Operator Eq Next:(Terminal TOP.state),(IntConst 1)) \
True:(Terminal TOP._rn5_ctrljump) \
False:(Branch Cond:(Operator Eq Next:(Terminal TOP.state),(IntConst 2)) \
True:(Terminal TOP._rn9_ctrljump)))))
(Bind dest:TOP.ncnt \
tree:(Branch Cond:(Operator Ulnot Next:(Terminal TOP.RST_X)) \
True:(IntConst 0) \
False:(Branch Cond:(Operator Eq Next:(Terminal TOP.state),(IntConst 0)) \
True:(Terminal TOP._rn0_ncnt) \
False:(Branch Cond:(Operator Eq Next:(Terminal TOP.state),(IntConst 1)) \
True:(Terminal TOP._rn4_ncnt) \
False:(Branch Cond:(Operator Eq Next:(Terminal TOP.state),(IntConst 2)) \
True:(Terminal TOP._rn8_ncnt))))))
(Bind dest:TOP.nstate \
tree:(Branch Cond:(Operator Eq Next:(Terminal TOP.state),(IntConst 0)) \
True:(Branch Cond:(Terminal TOP._rn1_ctrljump) \
True:(Terminal TOP._rn3_nstate)) \
False:(Branch Cond:(Operator Eq Next:(Terminal TOP.state),(IntConst 1)) \
True:(Branch Cond:(Terminal TOP._rn5_ctrljump) \
True:(Terminal TOP._rn7_nstate)) \
False:(Branch Cond:(Operator Eq Next:(Terminal TOP.state),(IntConst 2)) \
True:(Branch Cond:(Terminal TOP._rn9_ctrljump) \
True:(Terminal TOP._rn11_nstate))))))
(Bind dest:TOP.state \
tree:(Branch Cond:(Operator Ulnot Next:(Terminal TOP.RST_X)) \
True:(IntConst 0) \
False:(Terminal TOP.nstate)))
"""

def test():
    filelist = [codedir + 'blocking.v']
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
    
    output.append('Directive:\n')
    for dr in sorted(directives, key=lambda x:str(x)):
        output.append(str(dr))
        output.append('\n')

    output.append('Instance:\n')
    for module, instname in sorted(instances, key=lambda x:str(x[1])):
        output.append(str((module, instname)))
        output.append('\n')

    output.append('Term:\n')
    for tk, tv in sorted(terms.items(), key=lambda x:str(x[0])):
        output.append(tv.tostr())
        output.append('\n')
        
    output.append('Bind:\n')
    for bk, bv in sorted(binddict.items(), key=lambda x:str(x[0])):
        for bvi in bv:
            output.append(bvi.tostr())
            output.append('\n')
            
    rslt = ''.join(output)

    print(rslt)
    assert(expected == rslt)

if __name__ == '__main__':
    test()
