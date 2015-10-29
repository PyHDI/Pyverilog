module TOP(CLK,RST);
  input [3:1] CLK;
  input [1:0] RST;
  reg cnt;
  
  always @(posedge CLK[2] or posedge RST[0]) begin
    if(RST[0]) begin
      cnt <= 'd0;
    end
  end

endmodule
