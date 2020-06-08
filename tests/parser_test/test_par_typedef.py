from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.parser.parser import VerilogCodeParser

try:
    from StringIO import StringIO
except:
    from io import StringIO

codedir = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
Source:  (at 1)
  Description:  (at 1)
    TypeDef: counter, logic (at 1)
      Width:  (at 1)
        IntConst: 7 (at 1)
        IntConst: 0 (at 1)
    Module: TOP, None (at 3)
      DeclVars:  (at 5)
        Var:  (at 5)
          Input: CLK, None (at 5)
          Logic: CLK, None (at 5)
      DeclVars:  (at 6)
        Var:  (at 6)
          Input: RST_X, None (at 6)
          Logic: RST_X, None (at 6)
      DeclVars:  (at 9)
        Var:  (at 9)
          CustomType: cnt, c, None (at 9)
      AlwaysFF:  (at 11)
        SensList:  (at 11)
          Sens: posedge (at 11)
            Identifier: CLK (at 11)
        Block: None (at 11)
          IfStatement:  (at 12)
            Ulnot:  (at 12)
              Identifier: RST_X (at 12)
            Block: None (at 12)
              NonblockingSubstitution:  (at 13)
                Lvalue:  (at 13)
                  Identifier: cnt (at 13)
                Rvalue:  (at 13)
                  IntConst: 0 (at 13)
            Block: None (at 14)
              NonblockingSubstitution:  (at 15)
                Lvalue:  (at 15)
                  Identifier: cnt (at 15)
                Rvalue:  (at 15)
                  Plus:  (at 15)
                    Identifier: cnt (at 15)
                    IntConst: 1 (at 15)
"""


def test():
    filelist = [codedir + 'typedef.sv']
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
