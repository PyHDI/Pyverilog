module TOP
  (
   input logic CLK,
   input logic RST_X
   );

  logic [7:0] cnt;

  always_ff @(posedge CLK) begin
    if(!RST_X) begin
      cnt <= 0;
    end else begin
      cnt <= 1 - 1 + 8'(cnt + 1);
    end
  end

endmodule
