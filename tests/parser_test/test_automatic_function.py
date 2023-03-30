from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.vparser.parser import VerilogCodeParser

try:
    from StringIO import StringIO
except:
    from io import StringIO

codedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
Source:  (at 1)
  Description:  (at 1)
    ModuleDef: TOP (from 1 to 25)
      Paramlist:  (at 0)
      Portlist:  (at 1)
        Port: CLK, None (at 1)
        Port: RST_X, None (at 1)
      Decl:  (at 2)
        Input: CLK, False (at 2)
      Decl:  (at 3)
        Input: RST_X, False (at 3)
      Decl:  (at 4)
        Reg: cnt, False (at 4)
          Width:  (at 4)
            IntConst: 3 (at 4)
            IntConst: 0 (at 4)
      Function: inc (at 6)
        Width:  (at 6)
          IntConst: 3 (at 6)
          IntConst: 0 (at 6)
        Decl:  (at 7)
          Input: in, False (at 7)
            Width:  (at 7)
              IntConst: 3 (at 7)
              IntConst: 0 (at 7)
        Block: None (from 8 to 14)
          IfStatement:  (from 9 to 13)
            Uand:  (at 9)
              Identifier: inc (at 9)
            Block: None (from 9 to 11)
              BlockingSubstitution:  (from 10 to 10)
                Lvalue:  (at 10)
                  Identifier: inc (at 10)
                Rvalue:  (at 10)
                  IntConst: 0 (at 10)
            Block: None (from 11 to 13)
              BlockingSubstitution:  (from 12 to 12)
                Lvalue:  (at 12)
                  Identifier: inc (at 12)
                Rvalue:  (at 12)
                  Plus:  (at 12)
                    Identifier: in (at 12)
                    IntConst: 1 (at 12)
      Always:  (from 17 to 23)
        SensList:  (at 17)
          Sens: posedge (at 17)
            Identifier: CLK (at 17)
          Sens: negedge (at 17)
            Identifier: RST_X (at 17)
        Block: None (from 17 to 23)
          IfStatement:  (from 18 to 22)
            Ulnot:  (at 18)
              Identifier: RST_X (at 18)
            Block: None (from 18 to 20)
              NonblockingSubstitution:  (from 19 to 19)
                Lvalue:  (at 19)
                  Identifier: cnt (at 19)
                Rvalue:  (at 19)
                  IntConst: 0 (at 19)
            Block: None (from 20 to 22)
              NonblockingSubstitution:  (from 21 to 21)
                Lvalue:  (at 21)
                  Identifier: cnt (at 21)
                Rvalue:  (at 21)
                  FunctionCall:  (at 21)
                    Identifier: inc (at 21)
                    Identifier: cnt (at 21)
"""

def test():
    filelist = [codedir + 'automatic_function.v']
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
