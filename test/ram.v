module TOP(CLK, RST_X, ADDR, WE, D, Q);
  input CLK;
  input RST_X;

  input [7:0] ADDR;
  input WE;
  input [7:0] D;
  output [7:0] Q;

  reg [7:0] mem [0:255];
  reg [7:0] d_ADDR;
  
  always @(posedge CLK) begin
    if(WE) mem[ADDR] <= D;
    d_ADDR <= ADDR;
  end
  assign Q = mem[d_ADDR];
  
endmodule
