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
  output reg [7:0] led
);


  // Embedded code
  reg [31:0] count;
  always @(posedge CLK) begin
    if(RST) begin
      count <= 0;
      led <= 0;
    end else begin
      if(count == 1024 - 1) begin
        count <= 0;
        led <= led + 1;
      end else begin
        count <= count + 1;
      end 
    end
  end


endmodule
"""

def test():
    params = vast.Paramlist( [] )
    clk = vast.Ioport( vast.Input('CLK') )
    rst = vast.Ioport( vast.Input('RST') )
    width = vast.Width( vast.IntConst('7'), vast.IntConst('0') )
    led = vast.Ioport( vast.Output('led', width=width), vast.Reg('led', width=width) )
    ports = vast.Portlist( (clk, rst, led) )
    items = [ vast.EmbeddedCode("""
// Embedded code
reg [31:0] count;
always @(posedge CLK) begin
  if(RST) begin
    count <= 0;
    led <= 0;
  end else begin
    if(count == 1024 - 1) begin
      count <= 0;
      led <= led + 1;
    end else begin
      count <= count + 1;
    end 
  end
end
""") ]
    ast = vast.ModuleDef("top", params, ports, items)
    
    codegen = ASTCodeGenerator()
    rslt = codegen.visit(ast)
    
    print(rslt)
    assert(expected == rslt)

if __name__ == '__main__':
    test()
