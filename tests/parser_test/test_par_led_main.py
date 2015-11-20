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
    ModuleDef: led
      Paramlist: 
        Decl: 
          Parameter: STEP, False
            Rvalue: 
              IntConst: 10
      Portlist: 
        Ioport: 
          Input: CLK, False
        Ioport: 
          Input: RST, False
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
                Block: None
                  NonblockingSubstitution: 
                    Lvalue: 
                      Identifier: count
                    Rvalue: 
                      Plus: 
                        Identifier: count
                        IntConst: 1
    ModuleDef: main
      Paramlist: 
      Portlist: 
        Ioport: 
          Input: CLK, False
        Ioport: 
          Input: RST, False
        Ioport: 
          Output: LED, False
            Width: 
              IntConst: 7
              IntConst: 0
      InstanceList: led
        ParamArg: STEP
          IntConst: 100
        Instance: inst_led, led
          ParamArg: STEP
            IntConst: 100
          PortArg: CLK
            Identifier: CLK
          PortArg: RST
            Identifier: RST
          PortArg: LED
            Identifier: LED
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
