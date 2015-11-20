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
    ModuleDef: TOP
      Paramlist: 
      Portlist: 
        Ioport: 
          Input: VAL, False
            Width: 
              IntConst: 3
              IntConst: 0
        Ioport: 
          Input: in0, False
            Width: 
              IntConst: 3
              IntConst: 0
        Ioport: 
          Input: in1, False
            Width: 
              IntConst: 3
              IntConst: 0
        Ioport: 
          Input: in2, False
            Width: 
              IntConst: 3
              IntConst: 0
        Ioport: 
          Input: in3, False
        Ioport: 
          Input: in4, False
        Ioport: 
          Input: in5, False
        Ioport: 
          Output: LED0, False
            Width: 
              IntConst: 3
              IntConst: 0
        Ioport: 
          Output: LED1, False
            Width: 
              IntConst: 3
              IntConst: 0
        Ioport: 
          Output: LED2, False
            Width: 
              IntConst: 3
              IntConst: 0
        Ioport: 
          Output: LED3, False
            Width: 
              IntConst: 3
              IntConst: 0
        Ioport: 
          Output: LED4, False
        Ioport: 
          Output: LED5, False
      InstanceList: SUB
        ParamArg: MODE
          IntConst: 0
        Instance: inst_sub0, SUB
          ParamArg: MODE
            IntConst: 0
          PortArg: None
            Pointer: 
              Identifier: VAL
              IntConst: 0
          PortArg: None
            Pointer: 
              Identifier: LED0
              IntConst: 0
        Instance: inst_sub1, SUB
          ParamArg: MODE
            IntConst: 0
          PortArg: None
            Pointer: 
              Identifier: VAL
              IntConst: 1
          PortArg: None
            Pointer: 
              Identifier: LED0
              IntConst: 1
        Instance: inst_sub2, SUB
          ParamArg: MODE
            IntConst: 0
          PortArg: None
            Pointer: 
              Identifier: VAL
              IntConst: 2
          PortArg: None
            Pointer: 
              Identifier: LED0
              IntConst: 2
        Instance: inst_sub3, SUB
          ParamArg: MODE
            IntConst: 0
          PortArg: None
            Pointer: 
              Identifier: VAL
              IntConst: 3
          PortArg: None
            Pointer: 
              Identifier: LED0
              IntConst: 3
      InstanceList: SUB
        ParamArg: MODE
          IntConst: 0
        Instance: inst_sub4, SUB
          Width: 
            IntConst: 3
            IntConst: 0
          ParamArg: MODE
            IntConst: 0
          PortArg: None
            Identifier: VAL
          PortArg: None
            Identifier: LED1
        Instance: inst_sub5, SUB
          Width: 
            IntConst: 3
            IntConst: 0
          ParamArg: MODE
            IntConst: 0
          PortArg: None
            Identifier: VAL
          PortArg: None
            Identifier: LED2
      InstanceList: and
        Instance: U0, and
          Width: 
            IntConst: 3
            IntConst: 0
          PortArg: None
            Identifier: LED3
          PortArg: None
            Identifier: in0
          PortArg: None
            Identifier: in1
          PortArg: None
            Identifier: in2
      InstanceList: and
        Instance: , and
          PortArg: None
            Identifier: LED4
          PortArg: None
            Identifier: in3
          PortArg: None
            Identifier: in4
          PortArg: None
            Identifier: in5
        Instance: , and
          PortArg: None
            Identifier: LED5
          PortArg: None
            Identifier: in3
          PortArg: None
            Identifier: in4
          PortArg: None
            Identifier: in5
    ModuleDef: SUB
      Paramlist: 
        Decl: 
          Parameter: MODE, False
            Rvalue: 
              IntConst: 0
      Portlist: 
        Ioport: 
          Input: VAL, False
        Ioport: 
          Output: LED, False
      Assign: 
        Lvalue: 
          Identifier: LED
        Rvalue: 
          And: 
            Unot: 
              Identifier: VAL
            Identifier: MODE
"""

def test():
    filelist = [codedir + 'instance_array.v']
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
