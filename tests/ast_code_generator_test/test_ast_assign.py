from __future__ import absolute_import
from __future__ import print_function
import os
import sys

import pyverilog.vparser.ast as vast
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

expected = """\

module top
(
  input CLK,
  input RST,
  output [7:0] led
);

  assign led = 8;

endmodule
"""

def test():
    params = vast.Paramlist( [] )
    clk = vast.Ioport( vast.Input('CLK') )
    rst = vast.Ioport( vast.Input('RST') )
    width = vast.Width( vast.IntConst('7'), vast.IntConst('0') )
    led = vast.Ioport( vast.Output('led', width=width) )
    ports = vast.Portlist( (clk, rst, led) )
    items = [ vast.Assign( vast.Lvalue(vast.Identifier('led')),
                           vast.Rvalue(vast.IntConst('8'))) ]
    ast = vast.ModuleDef("top", params, ports, items)
    
    codegen = ASTCodeGenerator()
    rslt = codegen.visit(ast)
    
    print(rslt)
    assert(expected == rslt)

if __name__ == '__main__':
    test()
