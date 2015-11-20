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
Source: 
  Description: 
    ModuleDef: \\1234
      Paramlist: 
      Portlist: 
        Port: \\CLK~, None
        Port: LE$D, None
        Port: \\1234RST*%&, None
      Decl: 
        Input: \\CLK~, False
        Input: \\1234RST*%&, False
      Decl: 
        Output: LE$D, False
      Decl: 
        Genvar: i, False
          Width: 
            IntConst: 31
            IntConst: 0
        Genvar: j, False
          Width: 
            IntConst: 31
            IntConst: 0
      GenerateStatement: 
        ForStatement: 
          BlockingSubstitution: 
            Lvalue: 
              Identifier: i
            Rvalue: 
              IntConst: 0
          LessThan: 
            Identifier: i
            IntConst: 4
          BlockingSubstitution: 
            Lvalue: 
              Identifier: i
            Rvalue: 
              Plus: 
                Identifier: i
                IntConst: 1
          Block: \\1stLoop
            ForStatement: 
              BlockingSubstitution: 
                Lvalue: 
                  Identifier: j
                Rvalue: 
                  IntConst: 0
              LessThan: 
                Identifier: j
                IntConst: 4
              BlockingSubstitution: 
                Lvalue: 
                  Identifier: j
                Rvalue: 
                  Plus: 
                    Identifier: j
                    IntConst: 1
              Block: \\2ndLoop
                Decl: 
                  Wire: tmp, False
                    Width: 
                      IntConst: 7
                      IntConst: 0
                Assign: 
                  Lvalue: 
                    Identifier: tmp
                  Rvalue: 
                    Times: 
                      Identifier: i
                      Identifier: j
      Decl: 
        Wire: rslt, False
          Width: 
            IntConst: 7
            IntConst: 0
      Assign: 
        Lvalue: 
          Identifier: rslt
        Rvalue: 
          Identifier: tmp
            IdentifierScope: 
              IdentifierScopeLabel: \\1stLoop, 0
              IdentifierScopeLabel: \\2ndLoop, 1
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
