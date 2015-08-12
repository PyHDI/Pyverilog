module TOP(CLK, RST);
  input CLK, RST;
  reg [7:0] cnt;
  always @(posedge CLK) begin
    if(RST) begin
      cnt <= 0;
    end else begin
      case(cnt)
        'h0, 'h1, 'h2: begin
          cnt <= cnt + 1;
        end
        'hff: begin
          cnt <= 0;
        end
        default: begin
          cnt <= cnt + 1;
        end
      endcase
    end
  end
endmodule
