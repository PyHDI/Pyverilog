module TOP(CLK, RST);
  input CLK, RST;
  reg [31:0] cnt;
  always @(posedge CLK) begin
    if(RST) begin
      cnt <= 0;
    end else begin
      case(cnt)
        0 : begin
          cnt <= 0 + 1;
        end
        1 : begin
          cnt <= 1 + 1;
        end
        2 : begin
          cnt <= 2 + 1;
        end
        3 : begin
          cnt <= 3 + 1;
        end
        4 : begin
          cnt <= 4 + 1;
        end
        5 : begin
          cnt <= 5 + 1;
        end
        6 : begin
          cnt <= 6 + 1;
        end
        7 : begin
          cnt <= 7 + 1;
        end
        8 : begin
          cnt <= 8 + 1;
        end
        9 : begin
          cnt <= 9 + 1;
        end
        10 : begin
          cnt <= 10 + 1;
        end
        11 : begin
          cnt <= 11 + 1;
        end
        12 : begin
          cnt <= 12 + 1;
        end
        13 : begin
          cnt <= 13 + 1;
        end
        14 : begin
          cnt <= 14 + 1;
        end
        15 : begin
          cnt <= 15 + 1;
        end
        16 : begin
          cnt <= 16 + 1;
        end
        17 : begin
          cnt <= 17 + 1;
        end
        18 : begin
          cnt <= 18 + 1;
        end
        19 : begin
          cnt <= 19 + 1;
        end
        20 : begin
          cnt <= 20 + 1;
        end
        21 : begin
          cnt <= 21 + 1;
        end
        22 : begin
          cnt <= 22 + 1;
        end
        23 : begin
          cnt <= 23 + 1;
        end
        24 : begin
          cnt <= 24 + 1;
        end
        25 : begin
          cnt <= 25 + 1;
        end
        26 : begin
          cnt <= 26 + 1;
        end
        27 : begin
          cnt <= 27 + 1;
        end
        28 : begin
          cnt <= 28 + 1;
        end
        29 : begin
          cnt <= 29 + 1;
        end
        30 : begin
          cnt <= 30 + 1;
        end
        31 : begin
          cnt <= 31 + 1;
        end
        default: begin
          cnt <= cnt + 1;
        end
      endcase
    end
  end
endmodule

