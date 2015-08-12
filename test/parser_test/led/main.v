`default_nettype none
`include "led.v"

module main
(
 input CLK,
 input RST,
 output [7:0] LED
 );
  
  led #
    (
     .STEP(`STEP)
     )
  inst_led
    (
     .CLK(CLK),
     .RST(RST),
     .LED(LED)
     );
  
endmodule
