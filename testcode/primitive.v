module TOP 
  (
   CLK, RST,
   in1, in2, in3, in4,
   out0, out1, out2, out3, out4, out5, out6, out7
   );
  
  input CLK, RST;
  input in1, in2, in3, in4;
  output out0, out1, out2, out3, out4, out5, out6, out7;
 
  and  U0 (out0, in1, in2, in3, in4);
  nand U1 (out1, in1, in2, in3, in4);
  or   U2 (out2, in1, in2, in3, in4);
  nor  U3 (out3, in1, in2, in3, in4);
  xor  U4 (out4, in1, in2, in3, in4);
  xnor U5 (out5, in1, in2, in3, in4);
  not  U6 (out6, in1);
  buf  U7 (out7, in1);
endmodule

