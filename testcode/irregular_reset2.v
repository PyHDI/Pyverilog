module TOP2(CLK, RST);
  input CLK, RST;
  reg [7:0] cnt4;
  parameter zero = 0;

  // no reset because it has no if branch.
  always @(posedge CLK or posedge RST) begin
    cnt4 <= 0;
  end

endmodule

