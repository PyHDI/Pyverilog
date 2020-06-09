from __future__ import absolute_import
from __future__ import print_function
import os
import sys

import pyverilog.parser.ast as vast
from pyverilog.codegen.codegen import ASTCodeGenerator

expected = """\


interface WriteReq
(

);

  logic [31:0] address;
  logic [7:0] data;
  logic valid;

  modport master
  (
    output address,
    output data,
    output valid
  );

  modport slave
  (
    input address,
    input data,
    input valid
  );

endinterface



module top
(
  input CLK,
  input RST
);

  WriteReq a;
  WriteReq b;

  sub
  inst_sub
  (
    .CLK(CLK),
    .RST(RST),
    .req_in(a),
    .req_out(b)
  );


endmodule



module sub
(
  input CLK,
  input RST,
  WriteReq.slave req_in,
  WriteReq.master req_out
);

  assign req_out.address = req_in.address;
  assign req_out.data = req_in.data;
  assign req_out.valid = req_in.valid;

endmodule

"""


def test():
    params = ()
    ports = ()
    width = vast.Width(vast.IntConst('31'), vast.IntConst('0'))
    address = vast.DeclVars([vast.Var([vast.Logic('address', width=width)])])
    width = vast.Width(vast.IntConst('7'), vast.IntConst('0'))
    data = vast.DeclVars([vast.Var([vast.Logic('data', width=width)])])
    valid = vast.DeclVars([vast.Var([vast.Logic('valid')])])
    master = vast.Modport('master',
                          [vast.DeclVars([vast.Var([vast.Output('address')])]),
                           vast.DeclVars([vast.Var([vast.Output('data')])]),
                           vast.DeclVars([vast.Var([vast.Output('valid')])])])
    slave = vast.Modport('slave',
                         [vast.DeclVars([vast.Var([vast.Input('address')])]),
                          vast.DeclVars([vast.Var([vast.Input('data')])]),
                          vast.DeclVars([vast.Var([vast.Input('valid')])])])
    items = [address, data, valid, master, slave]
    interface = vast.Interface('WriteReq', params, ports, items)

    params = ()
    clk = vast.DeclVars([vast.Var([vast.Input('CLK')])])
    rst = vast.DeclVars([vast.Var([vast.Input('RST')])])
    ports = [clk, rst]
    a = vast.DeclVars([vast.Var([vast.CustomType('WriteReq', 'a')])])
    b = vast.DeclVars([vast.Var([vast.CustomType('WriteReq', 'b')])])
    paramlist = ()
    portlist = (vast.PortArg('CLK', vast.Identifier('CLK')),
                vast.PortArg('RST', vast.Identifier('RST')),
                vast.PortArg('req_in', vast.Identifier('a')),
                vast.PortArg('req_out', vast.Identifier('b')))
    sub = vast.DeclInstances([vast.Instance('sub', 'inst_sub', paramlist, portlist)])
    items = [a, b, sub]
    top = vast.Module('top', params, ports, items)

    params = ()
    clk = vast.DeclVars([vast.Var([vast.Input('CLK')])])
    rst = vast.DeclVars([vast.Var([vast.Input('RST')])])
    req_in = vast.DeclVars([vast.Var([vast.CustomType('WriteReq', 'req_in',
                                                      modportname='slave')])])
    req_out = vast.DeclVars([vast.Var([vast.CustomType('WriteReq', 'req_out',
                                                       modportname='master')])])
    ports = [clk, rst, req_in, req_out]
    a0 = vast.Assign(vast.Lvalue(vast.Identifier('address', [vast.IdentifierScope('req_out')])),
                     vast.Rvalue(vast.Identifier('address', [vast.IdentifierScope('req_in')])))
    a1 = vast.Assign(vast.Lvalue(vast.Identifier('data', [vast.IdentifierScope('req_out')])),
                     vast.Rvalue(vast.Identifier('data', [vast.IdentifierScope('req_in')])))
    a2 = vast.Assign(vast.Lvalue(vast.Identifier('valid', [vast.IdentifierScope('req_out')])),
                     vast.Rvalue(vast.Identifier('valid', [vast.IdentifierScope('req_in')])))
    items = [a0, a1, a2]
    sub = vast.Module('sub', params, ports, items)
    description = vast.Description([interface, top, sub])

    codegen = ASTCodeGenerator()
    rslt = codegen.visit(description)
    print(rslt)

    assert(expected == rslt)


if __name__ == '__main__':
    test()
