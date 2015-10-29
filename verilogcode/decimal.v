module TOP(CLK, RST);
  input CLK, RST;
  reg [7:0] cnt;

  always @(posedge CLK or negedge RST) begin
    if(RST) begin
      cnt <= 'd0;
    end else begin
      cnt <= cnt + 'd1;
    end
  end

endmodule
