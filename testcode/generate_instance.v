module TOP(CLK, RST_X,
           IN0, IN1, IN2, IN3, IN4,
           OUT0, OUT1, OUT2, OUT3, OUT4);

  parameter WA = 32;
  parameter WD = 4;
  parameter LEN = 8;
  
  input CLK, RST_X;
  
  input [WD-1:0] IN0;
  input [WD-1:0] IN1;
  input [WD-1:0] IN2;
  input [WD-1:0] IN3;
  input [WD-1:0] IN4;
  
  output [WD-1:0] OUT0;
  output [WD-1:0] OUT1;
  output [WD-1:0] OUT2;
  output [WD-1:0] OUT3;
  output [WD-1:0] OUT4;

  wire [WD-1:0] in [0:4];
  wire [WD-1:0] out [0:4];

  assign in[0] = IN0;
  assign in[1] = IN1;
  assign in[2] = IN2;
  assign in[3] = IN3;
  assign in[4] = IN4;

  assign OUT0 = out[0];
  assign OUT1 = out[1];
  assign OUT2 = out[2];
  assign OUT3 = out[3];
  assign OUT4 = out[4];

  reg [2:0] cnt;
  always @(posedge CLK or negedge RST_X) begin
    if(!RST_X) begin
      cnt <= 0;
    end else begin
      cnt <= (cnt < 4)? cnt + 1 : 0;
    end
  end
  
  genvar i;
  generate for(i=0; i<5; i=i+1) begin: loop
    SUB #(WD)
    sub (CLK, RST_X, in[cnt], out[i]);
  end endgenerate
  
endmodule

module SUB(CLK, RST_X, subin, subout);
  parameter WD = 8;
  input CLK;
  input RST_X;
  input [WD-1:0] subin;
  output [WD-1:0] subout;
  
  genvar j;
  generate for(j=0; j<WD; j=j+1) begin: subloop
    if(j == 0) begin: _subt
      wire tmp;
      assign subout[j] = subin[j];
      assign tmp = ~subin[j];
    end else begin: _subf
      wire tmp;
      if(j == 1) begin
        assign subout[j] = subloop[j-1]._subt.tmp ^ subin[j];
      end else begin
        assign subout[j] = subloop[j-1]._subf.tmp ^ subin[j];
      end
    end
  end endgenerate
    
endmodule
