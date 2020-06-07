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
        Input: CLK, None (at 3)
        Logic: CLK, None (at 3)
      Ioport:  (at 4)
        Input: RST_X, None (at 4)
        Logic: RST_X, None (at 4)
      Decl:  (at 7)
        Logic: cnt, None (at 7)
          Width:  (at 7)
            IntConst: 7 (at 7)
            IntConst: 0 (at 7)
      AlwaysFF:  (at 9)
        SensList:  (at 9)
          Sens: posedge (at 9)
            Identifier: CLK (at 9)
        Block: None (at 9)
          IfStatement:  (at 10)
            Ulnot:  (at 10)
              Identifier: RST_X (at 10)
            Block: None (at 10)
              NonblockingSubstitution:  (at 11)
                Lvalue:  (at 11)
                  Identifier: cnt (at 11)
                Rvalue:  (at 11)
                  IntConst: 0 (at 11)
            Block: None (at 12)
              NonblockingSubstitution:  (at 13)
                Lvalue:  (at 13)
                  Identifier: cnt (at 13)
                Rvalue:  (at 13)
                  Plus:  (at 13)
                    Minus:  (at 13)
                      IntConst: 1 (at 13)
                      IntConst: 1 (at 13)
                    StaticCast:  (at 13)
                      IntConst: 8 (at 13)
                      Plus:  (at 13)
                        Identifier: cnt (at 13)
                        IntConst: 1 (at 13)
"""


def test():
    filelist = [codedir + 'static_cast_width.sv']
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
