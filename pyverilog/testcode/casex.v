module TOP(CLK, RST, LED);
  input CLK, RST;
  output [7:0] LED;
  reg [7:0] cnt;
  always @(posedge CLK) begin
    if(RST) begin
      cnt <= 0;
    end else begin
      casex(cnt)
        'b00: begin
          cnt <= cnt + 1;
        end
        'b1x: begin
          cnt <= 0;
        end
        default: begin
          cnt <= cnt + 1;
        end
      endcase
    end
  end
  assign LED = cnt;
endmodule

