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
    Interface: WriteReq, None (at 1)
      DeclVars:  (at 6)
        Var:  (at 6)
          Logic: address, None (at 6)
            Width:  (at 6)
              IntConst: 31 (at 6)
              IntConst: 0 (at 6)
      DeclVars:  (at 7)
        Var:  (at 7)
          Logic: data, None (at 7)
            Width:  (at 7)
              IntConst: 7 (at 7)
              IntConst: 0 (at 7)
      DeclVars:  (at 8)
        Var:  (at 8)
          Logic: valid, None (at 8)
      Modport: master (at 10)
        DeclVars:  (at 12)
          Var:  (at 12)
            Output: address, None (at 12)
        DeclVars:  (at 13)
          Var:  (at 13)
            Output: data, None (at 13)
        DeclVars:  (at 14)
          Var:  (at 14)
            Output: valid, None (at 14)
      Modport: slave (at 17)
        DeclVars:  (at 19)
          Var:  (at 19)
            Input: address, None (at 19)
        DeclVars:  (at 20)
          Var:  (at 20)
            Input: data, None (at 20)
        DeclVars:  (at 21)
          Var:  (at 21)
            Input: valid, None (at 21)
    Module: top, None (at 28)
      DeclVars:  (at 30)
        Var:  (at 30)
          Input: CLK, None (at 30)
      DeclVars:  (at 31)
        Var:  (at 31)
          Input: RST, None (at 31)
      DeclVars:  (at 34)
        Var:  (at 34)
          CustomType: a, WriteReq, None (at 34)
      DeclVars:  (at 35)
        Var:  (at 35)
          CustomType: b, WriteReq, None (at 35)
      DeclInstances:  (at 37)
        Instance: sub, inst_sub (at 37)
          PortArg: CLK (at 40)
            Identifier: CLK (at 40)
          PortArg: RST (at 41)
            Identifier: RST (at 41)
          PortArg: req_in (at 42)
            Identifier: a (at 42)
          PortArg: req_out (at 43)
            Identifier: b (at 43)
    Module: sub, None (at 51)
      DeclVars:  (at 53)
        Var:  (at 53)
          Input: CLK, None (at 53)
      DeclVars:  (at 54)
        Var:  (at 54)
          Input: RST, None (at 54)
      DeclVars:  (at 55)
        Var:  (at 55)
          CustomType: req_in, WriteReq, slave (at 55)
      DeclVars:  (at 56)
        Var:  (at 56)
          CustomType: req_out, WriteReq, master (at 56)
      Assign:  (at 59)
        Lvalue:  (at 59)
          Identifier: address (at 59)
            IdentifierScope: req_out, None (at 59)
        Rvalue:  (at 59)
          Identifier: address (at 59)
            IdentifierScope: req_in, None (at 59)
      Assign:  (at 60)
        Lvalue:  (at 60)
          Identifier: data (at 60)
            IdentifierScope: req_out, None (at 60)
        Rvalue:  (at 60)
          Identifier: data (at 60)
            IdentifierScope: req_in, None (at 60)
      Assign:  (at 61)
        Lvalue:  (at 61)
          Identifier: valid (at 61)
            IdentifierScope: req_out, None (at 61)
        Rvalue:  (at 61)
          Identifier: valid (at 61)
            IdentifierScope: req_in, None (at 61)
"""


def test():
    filelist = [codedir + 'interface.sv']
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
