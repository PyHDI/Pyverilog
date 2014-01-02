
module TOP(CLK, RST, LED);
  input CLK, RST;
  output [7:0] LED;
  reg [7:0] cnt;
  localparam DELAYSIZE = 5;
  always @(posedge CLK) begin
    if(RST) begin
      cnt <= 0;
    end else begin
      cnt <= #DELAYSIZE cnt==255? 0 : cnt + 1;
    end
  end
  assign LED = cnt;
endmodule

