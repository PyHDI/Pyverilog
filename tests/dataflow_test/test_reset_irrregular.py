import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer
import pyverilog.utils.verror as verror

codedir = '../../testcode/'


def test():
    filelist = [(codedir + 'irregular_reset0.v'),
                (codedir + 'irregular_reset1.v'),
                (codedir + 'irregular_reset2.v'),
                (codedir + 'irregular_reset3.v')]
##    filelist = [(codedir + 'irregular_reset4.v')]
    topmodule = 'TOP'
    noreorder = False
    nobind = False
    include = None
    define = None

    for i, file in enumerate(filelist):
        topmodule = 'TOP' + str(i)
        analyzer = VerilogDataflowAnalyzer(filelist, topmodule,
                                           noreorder=noreorder,
                                           nobind=nobind,
                                           preprocess_include=include,
                                           preprocess_define=define)
        try:
            analyzer.generate()
        except verror.FormatError:
            del analyzer
        else:
            raise Exception('Irregal reset code is passed.')


if __name__ == '__main__':
    test()
