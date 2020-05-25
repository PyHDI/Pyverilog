
module TOP
  (
   input logic CLK,
   input logic RST_X
   );

  typedef logic [7:0] counter;
  counter cnt;

  always_ff @(posedge CLK) begin
    if(!RST_X) begin
      cnt <= 0;
    end else begin
      cnt <= cnt + 1;
    end
  end

endmodule
