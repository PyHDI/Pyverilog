`default_nettype none
  
module TOP(CLK, RST_X, MEM_A, MEM_RE, MEM_WE, MEM_D, MEM_Q, MEM_BUSY, MEM_DONE);
  input CLK;
  input RST_X;

  parameter WA = 32;
  parameter WD = 32;
  
  output reg [WA-1:0] MEM_A;
  output reg MEM_RE;
  output reg MEM_WE;
  output reg [WD-1:0] MEM_D;
  input [WD-1:0] MEM_Q;
  input MEM_DONE;
  input MEM_BUSY;

  reg [3:0] state;
  reg [3:0] cnt;

  wire [3:0] wire_cnt0;
  assign wire_cnt0 = cnt + 1;
  wire [3:0] wire_cnt1;
  assign wire_cnt1 = wire_cnt0 + 1;

  always @(posedge CLK or negedge RST_X) begin
    if(!RST_X) begin
      MEM_RE <= 0;
    end else begin
      MEM_RE <= 0;
    end
  end
  
  always @(posedge CLK or negedge RST_X) begin
    if(!RST_X) begin
      state <= 0;
      cnt <= 0;
    end else begin
      if(state == 0) begin
        cnt <= cnt + 1;
        if(cnt == 8) begin
          state <= 1;
          cnt <= 0;
        end
      end else if(state == 1) begin
        cnt <= cnt + 1;
        if(cnt == 8) begin
          state <= 0;
          cnt <= 0;
        end
      end
    end
  end
endmodule
