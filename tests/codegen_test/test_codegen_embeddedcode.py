from __future__ import absolute_import
from __future__ import print_function
import os
import sys

import pyverilog.parser.ast as vast
from pyverilog.codegen.codegen import ASTCodeGenerator

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
    params = None
    clk = vast.DeclVars([vast.Var([vast.Input('CLK')])])
    rst = vast.DeclVars([vast.Var([vast.Input('RST')])])
    width = vast.Width(vast.IntConst('7'), vast.IntConst('0'))
    led = vast.DeclVars(
        [vast.Var([vast.Output('led', width=width), vast.Reg('led', width=width)])])
    ports = [clk, rst, led]
    items = [vast.EmbeddedCode("""
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
""")]

    ast = vast.Module("top", params, ports, items)

    codegen = ASTCodeGenerator()
    rslt = codegen.visit(ast)

    print(rslt)
    assert(expected == rslt)


if __name__ == '__main__':
    test()
