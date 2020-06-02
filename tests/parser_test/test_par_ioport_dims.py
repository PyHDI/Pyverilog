from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.vparser.parser import VerilogCodeParser

try:
    from StringIO import StringIO
except:
    from io import StringIO

codedir = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
Source:  (at 1)
  Description:  (at 1)
    Module: TOP, None (at 1)
      Ioport:  (at 3)
        Input: inval, False (at 3)
          Width:  (at 3)
            IntConst: 7 (at 3)
            IntConst: 0 (at 3)
          Dims:  (at 3)
            Width:  (at 3)
              IntConst: 3 (at 3)
              IntConst: 0 (at 3)
        Logic: inval, False (at 3)
          Width:  (at 3)
            IntConst: 7 (at 3)
            IntConst: 0 (at 3)
          Dims:  (at 3)
            Width:  (at 3)
              IntConst: 3 (at 3)
              IntConst: 0 (at 3)
      Ioport:  (at 4)
        Output: outval, False (at 4)
          Width:  (at 4)
            IntConst: 7 (at 4)
            IntConst: 0 (at 4)
          Dims:  (at 4)
            Width:  (at 4)
              IntConst: 3 (at 4)
              IntConst: 0 (at 4)
        Logic: outval, False (at 4)
          Width:  (at 4)
            IntConst: 7 (at 4)
            IntConst: 0 (at 4)
          Dims:  (at 4)
            Width:  (at 4)
              IntConst: 3 (at 4)
              IntConst: 0 (at 4)
      Decl:  (at 7)
        Instance: SUB, inst_sub (at 7)
          PortArg: None (at 7)
            Identifier: inval (at 7)
          PortArg: None (at 7)
            Identifier: outval (at 7)
    Module: SUB, None (at 11)
      Ioport:  (at 13)
        Input: inval, False (at 13)
          Width:  (at 13)
            IntConst: 7 (at 13)
            IntConst: 0 (at 13)
          Dims:  (at 13)
            Width:  (at 13)
              IntConst: 3 (at 13)
              IntConst: 0 (at 13)
        Logic: inval, False (at 13)
          Width:  (at 13)
            IntConst: 7 (at 13)
            IntConst: 0 (at 13)
          Dims:  (at 13)
            Width:  (at 13)
              IntConst: 3 (at 13)
              IntConst: 0 (at 13)
      Ioport:  (at 14)
        Output: outval, False (at 14)
          Width:  (at 14)
            IntConst: 7 (at 14)
            IntConst: 0 (at 14)
          Dims:  (at 14)
            Width:  (at 14)
              IntConst: 3 (at 14)
              IntConst: 0 (at 14)
        Logic: outval, False (at 14)
          Width:  (at 14)
            IntConst: 7 (at 14)
            IntConst: 0 (at 14)
          Dims:  (at 14)
            Width:  (at 14)
              IntConst: 3 (at 14)
              IntConst: 0 (at 14)
      Assign:  (at 17)
        Lvalue:  (at 17)
          Identifier: outval (at 17)
        Rvalue:  (at 17)
          Identifier: inval (at 17)
"""


def test():
    filelist = [codedir + 'ioport_dims.sv']
    output = 'preprocess.out'
    include = None
    define = None

    parser = VerilogCodeParser(filelist,
                               preprocess_include=include,
                               preprocess_define=define)
    ast = parser.parse()
    directives = parser.get_directives()

    output = StringIO()
    ast.show(buf=output)

    for lineno, directive in directives:
        output.write('Line %d : %s' % (lineno, directive))

    rslt = output.getvalue()

    print(rslt)
    assert(expected == rslt)


if __name__ == '__main__':
    test()
