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
      DeclVars:  (at 3)
        Var:  (at 3)
          Input: CLK, None (at 3)
          Logic: CLK, None (at 3)
      DeclVars:  (at 4)
        Var:  (at 4)
          Input: RST, None (at 4)
          Logic: RST, None (at 4)
      DeclVars:  (at 7)
        Var:  (at 7)
          Logic: address, None (at 7)
            Width:  (at 7)
              IntConst: 31 (at 7)
              IntConst: 0 (at 7)
      DeclVars:  (at 8)
        Var:  (at 8)
          Logic: data, None (at 8)
            Width:  (at 8)
              IntConst: 7 (at 8)
              IntConst: 0 (at 8)
      DeclVars:  (at 9)
        Var:  (at 9)
          Logic: valid, None (at 9)
      Modport: master (at 11)
        DeclVars:  (at 11)
          Var:  (at 11)
            Output: address, None (at 11)
        DeclVars:  (at 11)
          Var:  (at 11)
            Output: data, None (at 11)
        DeclVars:  (at 11)
          Var:  (at 11)
            Output: valid, None (at 11)
      Modport: slave (at 12)
        DeclVars:  (at 12)
          Var:  (at 12)
            Input: address, None (at 12)
        DeclVars:  (at 12)
          Var:  (at 12)
            Input: data, None (at 12)
        DeclVars:  (at 12)
          Var:  (at 12)
            Input: valid, None (at 12)
    Module: TOP, None (at 16)
      DeclVars:  (at 18)
        Var:  (at 18)
          Input: CLK, None (at 18)
      DeclVars:  (at 19)
        Var:  (at 19)
          Input: RST, None (at 19)
      DeclVars:  (at 20)
        Var:  (at 20)
          CustomType: req_in, WriteReq, master (at 20)
      DeclVars:  (at 21)
        Var:  (at 21)
          CustomType: req_out, WriteReq, slave (at 21)
      Assign:  (at 24)
        Lvalue:  (at 24)
          Identifier: address (at 24)
            IdentifierScope: req_out, None (at 24)
        Rvalue:  (at 24)
          Identifier: address (at 24)
            IdentifierScope: req_in, None (at 24)
      Assign:  (at 25)
        Lvalue:  (at 25)
          Identifier: data (at 25)
            IdentifierScope: req_out, None (at 25)
        Rvalue:  (at 25)
          Identifier: data (at 25)
            IdentifierScope: req_in, None (at 25)
      Assign:  (at 26)
        Lvalue:  (at 26)
          Identifier: valid (at 26)
            IdentifierScope: req_out, None (at 26)
        Rvalue:  (at 26)
          Identifier: valid (at 26)
            IdentifierScope: req_in, None (at 26)
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
