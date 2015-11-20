from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.vparser.preprocessor import VerilogPreprocessor

codedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
`default_nettype none
module led #
  (
   parameter STEP = 10
   )
  (
   input CLK,
   input RST,
   output reg [7:0] LED
   );
  
  reg [31:0] count;
  
  always @(posedge CLK) begin
    if(RST) begin
      count <= 0;
      LED <= 0;
    end else begin
      if(count == STEP - 1) begin
        count <= 0;
        LED <= LED + 1;
      end else begin
        count <= count + 1;
      end
    end
  end
endmodule

module main
(
 input CLK,
 input RST,
 output [7:0] LED
 );
  
  led #
    (
     .STEP(100)
     )
  inst_led
    (
     .CLK(CLK),
     .RST(RST),
     .LED(LED)
     );
  
endmodule
"""

def test():
    filelist = [codedir + 'led_main.v']
    output = 'preprocess.out'
    include = [codedir]
    define = ['STEP=100']
    
    pre = VerilogPreprocessor(filelist, output, include, define)
    pre.preprocess()
    rslt = open(output).read()
    os.remove(output)
    
    print(rslt)
    assert(expected == rslt)

if __name__ == '__main__':
    test()
