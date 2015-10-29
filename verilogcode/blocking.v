module TOP(CLK, RST_X, IN, OUT);
  input CLK, RST_X;
  input [7:0] IN;
  output [7:0] OUT;

  reg [7:0] state;
  reg [7:0] cnt;
  
  reg [7:0] ncnt;
  reg [7:0] nstate;
  reg ctrljump;

  always @* begin

    case(state)
      0: begin
        ncnt = 0;
        ctrljump = 1;
        if(ctrljump) begin
          OUT = 8'h0;
          nstate = 1;
        end
      end
      
      1: begin
        ncnt = cnt + 1;
        ctrljump = cnt > 7;
        if(ctrljump) begin
          OUT = cnt;
          nstate = 2;
        end
      end
      
      2: begin
        ncnt = cnt + 2;
        ctrljump = cnt > 20;
        if(ctrljump) begin
          OUT = cnt - 8;
          nstate = 0;
        end
      end
    endcase
  end
  
  always @(posedge CLK) begin
    if(!RST_X) begin
      state <= 0;
      ncnt <= 0;
    end else begin
      state <= nstate;
      cnt <= ncnt;
    end
  end
  
endmodule

