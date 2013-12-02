module TOP(CLK, RST_X, IN, OUT);
  input CLK, RST_X;
  input [7:0] IN;
  output [7:0] OUT;
  reg [7:0] OUT;

  reg [7:0] mem [0:255];
  
  genvar i;
  generate for(i=0; i<4; i=i+1) begin
    always @(posedge CLK) begin
      mem[IN][2*(i+1)-1:2*i] <= mem[IN][2*(i+1)-1:2*i] + 2'b1;
    end
  end endgenerate
  
endmodule

