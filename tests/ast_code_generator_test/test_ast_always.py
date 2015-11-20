from __future__ import absolute_import
from __future__ import print_function
import os
import sys

import pyverilog.vparser.ast as vast
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

expected = """\

module top #
(
  parameter DATAWID = 32
)
(
  input CLK,
  input RST,
  output [7:0] led
);

  reg [DATAWID-1:0] count;
  assign led = count[DATAWID-1:DATAWID-8];

  always @(posedge CLK) begin
    if(RST) begin
      count <= 0;
    end else begin
      count <= (count + 1) * 2 + 1;
    end
  end


endmodule
"""

def test():
    datawid = vast.Parameter( 'DATAWID', vast.Rvalue(vast.IntConst('32')) )
    params = vast.Paramlist( [datawid] )
    clk = vast.Ioport( vast.Input('CLK') )
    rst = vast.Ioport( vast.Input('RST') )
    width = vast.Width( vast.IntConst('7'), vast.IntConst('0') )
    led = vast.Ioport( vast.Output('led', width=width) )
    ports = vast.Portlist( [clk, rst, led] )

    width = vast.Width( vast.Minus(vast.Identifier('DATAWID'), vast.IntConst('1')), vast.IntConst('0') )
    count = vast.Reg('count', width=width)

    assign = vast.Assign(
        vast.Lvalue(vast.Identifier('led')), 
        vast.Rvalue(
            vast.Partselect(
                vast.Identifier('count'), # count
                vast.Minus(vast.Identifier('DATAWID'), vast.IntConst('1')), # [DATAWID-1:
                vast.Minus(vast.Identifier('DATAWID'), vast.IntConst('8'))))) # :DATAWID-8]

    sens = vast.Sens(vast.Identifier('CLK'), type='posedge')
    senslist = vast.SensList([ sens ])

    assign_count_true = vast.NonblockingSubstitution(
        vast.Lvalue(vast.Identifier('count')),
        vast.Rvalue(vast.IntConst('0')))
    if0_true = vast.Block([ assign_count_true ])

    # (count + 1) * 2
    count_plus_1 = vast.Plus(vast.Identifier('count'), vast.IntConst('1'))
    cp1_times_2 = vast.Times(count_plus_1, vast.IntConst('2'))
    cp1t2_plus_1 = vast.Plus(cp1_times_2, vast.IntConst('1'))
    assign_count_false = vast.NonblockingSubstitution(
        vast.Lvalue(vast.Identifier('count')),
        vast.Rvalue(cp1t2_plus_1))
    if0_false = vast.Block([ assign_count_false ])

    if0 = vast.IfStatement(vast.Identifier('RST'), if0_true, if0_false)
    statement = vast.Block([ if0 ])

    always = vast.Always(senslist, statement)

    items = []
    items.append(count)
    items.append(assign)
    items.append(always)

    ast = vast.ModuleDef("top", params, ports, items)
    
    codegen = ASTCodeGenerator()
    rslt = codegen.visit(ast)
    print(rslt)
    
    assert(expected == rslt)

if __name__ == '__main__':
    test()
