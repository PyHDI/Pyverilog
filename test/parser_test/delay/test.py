import os
import sys
from pyverilog.vparser.parser import VerilogCodeParser

try:
    from StringIO import StringIO
except:
    from io import StringIO

expected = """\
Source: 
  Description: 
    ModuleDef: main
      Paramlist: 
        Decl: 
          Parameter: STEP, False
            Rvalue: 
              IntConst: 10
      Portlist: 
        Ioport: 
          Input: CLK, False
            Width: 
              IntConst: 0
              IntConst: 0
        Ioport: 
          Input: RST, False
            Width: 
              IntConst: 0
              IntConst: 0
        Ioport: 
          Output: LED, False
            Width: 
              IntConst: 7
              IntConst: 0
          Reg: LED, False
            Width: 
              IntConst: 7
              IntConst: 0
      Decl: 
        Localparam: DELAY, False
          Rvalue: 
            IntConst: 10
      Decl: 
        Reg: count, False
          Width: 
            IntConst: 31
            IntConst: 0
      Always: 
        SensList: 
          Sens: posedge
            Identifier: CLK
        Block: None
          IfStatement: 
            Identifier: RST
            Block: None
              NonblockingSubstitution: 
                Lvalue: 
                  Identifier: count
                Rvalue: 
                  IntConst: 0
              NonblockingSubstitution: 
                Lvalue: 
                  Identifier: LED
                Rvalue: 
                  IntConst: 0
            Block: None
              IfStatement: 
                Eq: 
                  Identifier: count
                  Minus: 
                    Identifier: STEP
                    IntConst: 1
                Block: None
                  NonblockingSubstitution: 
                    Lvalue: 
                      Identifier: count
                    Rvalue: 
                      IntConst: 0
                  NonblockingSubstitution: 
                    Lvalue: 
                      Identifier: LED
                    Rvalue: 
                      Plus: 
                        Identifier: LED
                        IntConst: 1
                    DelayStatement: 
                      Identifier: DELAY
                Block: None
                  NonblockingSubstitution: 
                    Lvalue: 
                      Identifier: count
                    Rvalue: 
                      Plus: 
                        Identifier: count
                        IntConst: 1
Line 1 : `timescale 1ns / 1ps
"""

def test():
    filelist = ['main.v']
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

    assert(rslt == expected)
