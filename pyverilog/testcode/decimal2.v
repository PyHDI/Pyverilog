//`default_nettype none

module TOP(CLK, RST);
  input CLK, RST;
  reg [7:0] cnt2;


  always @(posedge CLK or negedge RST) begin
    if(RST) begin
      cnt2 <= 'd0;
    end else begin
      cnt2 <= cnt2 + 'd1;
    end
  end


endmodule

