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
Source:  (at 2)
  Description:  (at 2)
    Module: led, none (at 2)
      DeclParameters:  (at 4)
        Parameter: STEP, None, None (at 4)
          Rvalue:  (at 4)
            IntConst: 10 (at 4)
      DeclVars:  (at 7)
        Var:  (at 7)
          Input: CLK, None (at 7)
      DeclVars:  (at 8)
        Var:  (at 8)
          Input: RST, None (at 8)
      DeclVars:  (at 9)
        Var:  (at 9)
          Output: LED, None (at 9)
            Width:  (at 9)
              IntConst: 7 (at 9)
              IntConst: 0 (at 9)
          Reg: LED, None (at 9)
            Width:  (at 9)
              IntConst: 7 (at 9)
              IntConst: 0 (at 9)
      DeclVars:  (at 12)
        Var:  (at 12)
          Reg: count, None (at 12)
            Width:  (at 12)
              IntConst: 31 (at 12)
              IntConst: 0 (at 12)
      Always:  (at 14)
        SensList:  (at 14)
          Sens: posedge (at 14)
            Identifier: CLK (at 14)
        Block: None (at 14)
          IfStatement:  (at 15)
            Identifier: RST (at 15)
            Block: None (at 15)
              NonblockingSubstitution:  (at 16)
                Lvalue:  (at 16)
                  Identifier: count (at 16)
                Rvalue:  (at 16)
                  IntConst: 0 (at 16)
              NonblockingSubstitution:  (at 17)
                Lvalue:  (at 17)
                  Identifier: LED (at 17)
                Rvalue:  (at 17)
                  IntConst: 0 (at 17)
            Block: None (at 18)
              IfStatement:  (at 19)
                Eq:  (at 19)
                  Identifier: count (at 19)
                  Minus:  (at 19)
                    Identifier: STEP (at 19)
                    IntConst: 1 (at 19)
                Block: None (at 19)
                  NonblockingSubstitution:  (at 20)
                    Lvalue:  (at 20)
                      Identifier: count (at 20)
                    Rvalue:  (at 20)
                      IntConst: 0 (at 20)
                  NonblockingSubstitution:  (at 21)
                    Lvalue:  (at 21)
                      Identifier: LED (at 21)
                    Rvalue:  (at 21)
                      Plus:  (at 21)
                        Identifier: LED (at 21)
                        IntConst: 1 (at 21)
                Block: None (at 22)
                  NonblockingSubstitution:  (at 23)
                    Lvalue:  (at 23)
                      Identifier: count (at 23)
                    Rvalue:  (at 23)
                      Plus:  (at 23)
                        Identifier: count (at 23)
                        IntConst: 1 (at 23)
    Module: main, none (at 29)
      DeclVars:  (at 31)
        Var:  (at 31)
          Input: CLK, None (at 31)
      DeclVars:  (at 32)
        Var:  (at 32)
          Input: RST, None (at 32)
      DeclVars:  (at 33)
        Var:  (at 33)
          Output: LED, None (at 33)
            Width:  (at 33)
              IntConst: 7 (at 33)
              IntConst: 0 (at 33)
      DeclInstances:  (at 36)
        Instance: led, inst_led (at 36)
          ParamArg: STEP (at 38)
            IntConst: 100 (at 38)
          PortArg: CLK (at 42)
            Identifier: CLK (at 42)
          PortArg: RST (at 43)
            Identifier: RST (at 43)
          PortArg: LED (at 44)
            Identifier: LED (at 44)
Line 1 : `default_nettype none
"""


def test():
    filelist = [codedir + 'led_main.v']
    output = 'preprocess.out'
    include = [codedir]
    define = ['STEP=100']

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
