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
