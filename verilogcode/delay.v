`timescale 1ns / 1ps

module main #
(
 parameter STEP = 10
)
(
 input CLK,
 input RST,
 output reg [7:0] LED
 );

  localparam DELAY = 10;
  
  always @(posedge CLK) begin
    if(RST) begin
      LED <= 0;
    end else begin
      LED <= #DELAY LED + 1;
    end
  end
endmodule
