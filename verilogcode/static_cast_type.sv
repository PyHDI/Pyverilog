typedef logic [7:0] counter;

module TOP
  (
   input logic CLK,
   input logic RST_X
   );

  counter cnt;

  always_ff @(posedge CLK) begin
    if(!RST_X) begin
      cnt <= 0;
    end else begin
      cnt <= 1 - 1 + counter'(cnt + 1);
    end
  end

endmodule
