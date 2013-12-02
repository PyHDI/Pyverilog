module TOP(CLK, RST_X, LED);
  input CLK;
  input RST_X;
  output LED;

  reg [3:0] cnt;

  assign LED = cnt[3];

  always @(posedge CLK or negedge RST_X) begin
    if(!RST_X) begin
      cnt <= 0;
    end else begin
      cnt <= cnt + 1;
    end
  end

endmodule
