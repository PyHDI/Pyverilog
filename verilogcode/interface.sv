interface WriteReq
  (
   input logic CLK,
   input logic RST
   );

  logic [31:0] address;
  logic [7:0] data;
  logic valid;

  modport master (output address, output data, output valid);
  modport slave (input address, input data, input valid);
endinterface


module TOP
  (
   input CLK,
   input RST,
   WriteReq.master req_in,
   WriteReq.slave req_out
   );

  assign req_out.address = req_in.address;
  assign req_out.data = req_in.data;
  assign req_out.valid = req_in.valid;

endmodule
