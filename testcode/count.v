module TOP(CLK, RST_X);
  input CLK;
  input RST_X;
  reg [3:0] cnt;

  always @(posedge CLK or negedge RST_X) begin
    if(!RST_X) begin
      cnt <= 0;
    end else begin
      cnt <= cnt + 1;
    end
  end
  
endmodule
