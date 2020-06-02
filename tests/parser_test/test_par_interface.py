from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.vparser.parser import VerilogCodeParser

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
      Ioport:  (at 3)
        Input: CLK, False (at 3)
        Logic: CLK, False (at 3)
      Ioport:  (at 4)
        Input: RST, False (at 4)
        Logic: RST, False (at 4)
      Decl:  (at 7)
        Logic: address, False (at 7)
          Width:  (at 7)
            IntConst: 31 (at 7)
            IntConst: 0 (at 7)
      Decl:  (at 8)
        Logic: data, False (at 8)
          Width:  (at 8)
            IntConst: 7 (at 8)
            IntConst: 0 (at 8)
      Decl:  (at 9)
        Logic: valid, False (at 9)
      Modport: master (at 11)
        Ioport:  (at 11)
          Output: address, False (at 11)
        Ioport:  (at 11)
          Output: data, False (at 11)
        Ioport:  (at 11)
          Output: valid, False (at 11)
      Modport: slave (at 12)
        Ioport:  (at 12)
          Input: address, False (at 12)
        Ioport:  (at 12)
          Input: data, False (at 12)
        Ioport:  (at 12)
          Input: valid, False (at 12)
    Module: TOP, None (at 16)
      Ioport:  (at 18)
        Input: CLK, False (at 18)
      Ioport:  (at 19)
        Input: RST, False (at 19)
      Ioport:  (at 20)
        CustomVariable: req_in, WriteReq, master (at 20)
      Ioport:  (at 21)
        CustomVariable: req_out, WriteReq, slave (at 21)
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
