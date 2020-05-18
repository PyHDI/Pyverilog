module TOP
  (
   input logic [3:0][7:0] inval,
   output logic [3:0][7:0] outval
   );

  SUB inst_sub(inval, outval);

endmodule

module SUB
  (
   input logic [3:0][7:0] inval,
   output logic [3:0][7:0] outval
   );

  assign outval = inval;

endmodule

