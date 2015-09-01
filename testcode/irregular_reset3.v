module TOP3(CLK, RST);
  input CLK, RST;
  reg [7:0] cnt6;
  parameter zero = 0;

  //no reset because variable is loaded.
  always @(posedge CLK or posedge RST) begin
    if(RST) begin
      cnt6 <= 7'd0 + cnt1[1:0];
    end else begin
      cnt6 <= 8'd1;
    end
  end

endmodule
