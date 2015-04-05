//`default_nettype none

module TOP(CLK, RST);
  input CLK, RST;
  reg [7:0] cnt1;


  always @(posedge CLK or negedge RST) begin
    if(RST) begin
      cnt1 <= 'd0;
    end else begin
      cnt1 <= cnt1 + 8'd1;
    end
  end



endmodule

