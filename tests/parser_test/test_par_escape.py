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
    ModuleDef: \\1234 (from 1 to 22)
      Paramlist:  (at 0)
      Portlist:  (at 2)
        Port: \\CLK~, None (at 3)
        Port: LE$D, None (at 3)
        Port: \\1234RST*%&, None (at 3)
      Decl:  (at 8)
        Input: \\CLK~, False (at 8)
        Input: \\1234RST*%&, False (at 8)
      Decl:  (at 9)
        Output: LE$D, False (at 9)
      Decl:  (at 11)
        Genvar: i, False (at 11)
          Width:  (at 11)
            IntConst: 31 (at 11)
            IntConst: 0 (at 11)
        Genvar: j, False (at 11)
          Width:  (at 11)
            IntConst: 31 (at 11)
            IntConst: 0 (at 11)
      GenerateStatement:  (from 12 to 17)
        ForStatement:  (at 12)
          BlockingSubstitution:  (from 12 to 12)
            Lvalue:  (at 12)
              Identifier: i (at 12)
            Rvalue:  (at 12)
              IntConst: 0 (at 12)
          LessThan:  (at 12)
            Identifier: i (at 12)
            IntConst: 4 (at 12)
          BlockingSubstitution:  (at 12)
            Lvalue:  (at 12)
              Identifier: i (at 12)
            Rvalue:  (at 12)
              Plus:  (at 12)
                Identifier: i (at 12)
                IntConst: 1 (at 12)
          Block: \\1stLoop (from 12 to 17)
            ForStatement:  (at 13)
              BlockingSubstitution:  (from 13 to 13)
                Lvalue:  (at 13)
                  Identifier: j (at 13)
                Rvalue:  (at 13)
                  IntConst: 0 (at 13)
              LessThan:  (at 13)
                Identifier: j (at 13)
                IntConst: 4 (at 13)
              BlockingSubstitution:  (at 13)
                Lvalue:  (at 13)
                  Identifier: j (at 13)
                Rvalue:  (at 13)
                  Plus:  (at 13)
                    Identifier: j (at 13)
                    IntConst: 1 (at 13)
              Block: \\2ndLoop (from 13 to 16)
                Decl:  (at 14)
                  Wire: tmp, False (at 14)
                    Width:  (at 14)
                      IntConst: 7 (at 14)
                      IntConst: 0 (at 14)
                Assign:  (from 15 to 15)
                  Lvalue:  (at 15)
                    Identifier: tmp (at 15)
                  Rvalue:  (at 15)
                    Times:  (at 15)
                      Identifier: i (at 15)
                      Identifier: j (at 15)
      Decl:  (at 19)
        Wire: rslt, False (at 19)
          Width:  (at 19)
            IntConst: 7 (at 19)
            IntConst: 0 (at 19)
      Assign:  (from 20 to 20)
        Lvalue:  (at 20)
          Identifier: rslt (at 20)
        Rvalue:  (at 20)
          Identifier: tmp (at 20)
            IdentifierScope:  (at 20)
              IdentifierScopeLabel: \\1stLoop, 0 (at 20)
              IdentifierScopeLabel: \\2ndLoop, 1 (at 20)
"""

def test():
    filelist = [codedir + 'escape.v']
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
