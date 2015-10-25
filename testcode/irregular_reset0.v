module TOP0(CLK, RST);
  input CLK, RST;
  reg [7:0] cnt8;

  //no reset because condition is too complex
  always @(posedge CLK or posedge RST) begin
    if(RST && RST) begin
      cnt8 <= 0;
    end else begin
      cnt8 <= 8'd1;
    end
  end

endmodule

