import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer

codedir = '../../testcode/'

expected = """\
TOP.cnt1: sync TOP.RST[0]posedge TOP.CLK[0]
TOP.cnt10: sync TOP.RST[0]posedge TOP.CLK[0]
TOP.cnt2: posedge TOP.RST[0]posedge TOP.CLK[0]
TOP.cnt5: posedge TOP.RST[0]posedge TOP.CLK[0]
TOP.cnt7: sync TOP.RST[0]posedge TOP.CLK[0]
TOP.sub.CLK:  [] []
TOP.sub.RST:  [] []
TOP.sub.cnt9: sync TOP.sub.RST[0]posedge TOP.sub.CLK[0]
TOP.sub.zero:  [] []
TOP.zero:  [] []
"""

def test():
    filelist = [codedir + 'reset.v']
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

    sens_info = []
    for tk in sorted(binddict.keys(), key=lambda x:str(x)):
        sens_info.append(str(tk) + ': ')
        sens_info.append(binddict[tk][0].getResetEdge() + ' ' +
                        str(binddict[tk][0].getResetName())+
                        '[' + str(binddict[tk][0].getResetBit()) +']' +
                        binddict[tk][0].getClockEdge() + ' ' +
                        str(binddict[tk][0].getClockName()) +
                        '[' + str(binddict[tk][0].getClockBit()) + ']')
        sens_info.append('\n')

    rslt = ''.join(sens_info)

    print(rslt)
    assert(expected == rslt)


if __name__ == '__main__':
    test()
