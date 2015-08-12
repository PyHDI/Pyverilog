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
  
  reg [31:0] count;
  
  always @(posedge CLK) begin
    if(RST) begin
      count <= 0;
      LED <= 0;
    end else begin
      if(count == STEP - 1) begin
        count <= 0;
        LED <= #DELAY LED + 1;
      end else begin
        count <= count + 1;
      end
    end
  end
endmodule
