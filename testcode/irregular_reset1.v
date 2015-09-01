module TOP1(CLK, RST);
  input CLK, RST;
  reg [7:0] cnt3,cnt1;


  //no reset because variable is loaded
  always @(posedge CLK or posedge RST) begin
    if(RST) begin
      cnt3 <= cnt1[0];
    end else begin
      cnt3 <= 8'd1;
    end
  end


endmodule
