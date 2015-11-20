from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer

codedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
Directive:
Instance:
(led, 'led')
Term:
(Term name:led.CLK type:['Input'] msb:(IntConst 0) lsb:(IntConst 0))
(Term name:led.LED type:['Output', 'Reg'] msb:(IntConst 7) lsb:(IntConst 0))
(Term name:led.RST type:['Input'] msb:(IntConst 0) lsb:(IntConst 0))
(Term name:led.STEP type:['Parameter'] msb:(IntConst 31) lsb:(IntConst 0))
(Term name:led.count type:['Reg'] msb:(IntConst 31) lsb:(IntConst 0))
Bind:
(Bind dest:led.LED \
tree:(Branch Cond:(Terminal led.RST) \
True:(IntConst 0) \
False:(Branch Cond:(Operator Eq Next:(Terminal led.count),(Operator Minus Next:(Terminal led.STEP),(IntConst 1))) True:(Operator Plus Next:(Terminal led.LED),(IntConst 1)))))
(Bind dest:led.STEP tree:(IntConst 10))
(Bind dest:led.count \
tree:(Branch Cond:(Terminal led.RST) \
True:(IntConst 0) \
False:(Branch Cond:(Operator Eq Next:(Terminal led.count),(Operator Minus Next:(Terminal led.STEP),(IntConst 1))) True:(IntConst 0) False:(Operator Plus Next:(Terminal led.count),(IntConst 1)))))
"""

def test():
    filelist = [codedir + 'led.v']
    topmodule = 'led'
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
