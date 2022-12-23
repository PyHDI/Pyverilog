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
Source:  (at 3)
  Description:  (at 3)
    ModuleDef: main (from 3 to 22)
      Paramlist:  (at 3)
        Decl:  (at 5)
          Parameter: STEP, False (at 5)
            Rvalue:  (at 5)
              IntConst: 10 (at 5)
      Portlist:  (at 7)
        Ioport:  (at 8)
          Input: CLK, False (at 8)
        Ioport:  (at 9)
          Input: RST, False (at 9)
        Ioport:  (at 10)
          Output: LED, False (at 10)
            Width:  (at 10)
              IntConst: 7 (at 10)
              IntConst: 0 (at 10)
          Reg: LED, False (at 10)
            Width:  (at 10)
              IntConst: 7 (at 10)
              IntConst: 0 (at 10)
      Decl:  (at 13)
        Localparam: DELAY, False (at 13)
          Rvalue:  (at 13)
            IntConst: 10 (at 13)
      Always:  (from 15 to 21)
        SensList:  (at 15)
          Sens: posedge (at 15)
            Identifier: CLK (at 15)
        Block: None (from 15 to 21)
          IfStatement:  (from 16 to 20)
            Identifier: RST (at 16)
            Block: None (from 16 to 18)
              NonblockingSubstitution:  (from 17 to 17)
                Lvalue:  (at 17)
                  Identifier: LED (at 17)
                Rvalue:  (at 17)
                  IntConst: 0 (at 17)
            Block: None (from 18 to 20)
              NonblockingSubstitution:  (from 19 to 19)
                Lvalue:  (at 19)
                  Identifier: LED (at 19)
                Rvalue:  (at 19)
                  Plus:  (at 19)
                    Identifier: LED (at 19)
                    IntConst: 1 (at 19)
                DelayStatement:  (at 19)
                  Identifier: DELAY (at 19)
Line 1 : `timescale 1ns / 1ps
"""

def test():
    filelist = [codedir + 'delay.v']
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
