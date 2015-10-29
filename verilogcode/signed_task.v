module TOP(CLK, RST);
  input CLK, RST;
  reg [7:0] cnt;

  always @(posedge CLK or negedge RST) begin
    if(RST) begin
      cnt <= $signed(cnt);
    end else begin
      cnt <= $unsigned(cnt);
    end
  end

endmodule
