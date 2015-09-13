module TOP4(CLK, RST);
  input CLK, RST;
  reg [7:0] reg1,reg2;
  parameter zero = 0;

  //Illegal! not reset for reg2.
  always @(posedge CLK or posedge RST) begin
    if(RST) begin
      reg1 <= 8'd0;
    end else begin
      reg1 <= 8'd0;
      reg2 <= 8'd1;
    end
  end

endmodule
