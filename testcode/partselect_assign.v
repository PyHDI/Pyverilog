module TOP(CLK, RST, reg1, OUT);
  input CLK, RST;
  reg [1:0] reg1;
  reg [6:4] reg3;
  wire [2:1] in1;
  wire [11:10] in2;


  assign in1[2:1] = reg3[6:5];

  always @(posedge CLK or negedge RST) begin
    reg1 <= in1[2:1];
  end

  always @(posedge CLK or negedge RST) begin
    if(RST) begin
      reg3 <= 3'd0;
    end else begin
      reg3 <= 3'd1;
    end
  end

endmodule


