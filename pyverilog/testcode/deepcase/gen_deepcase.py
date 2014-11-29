N = 32

header = """\
module TOP(CLK, RST, LED);
  input CLK, RST;
  output [7:0] LED;
  reg [31:0] cnt;
  always @(posedge CLK) begin
    if(RST) begin
      cnt <= 0;
    end else begin
"""

footer = """\
    end
  end
  assign LED = cnt;
endmodule
"""

case_header = """\
      case(cnt)
"""

case_default = """\
        default: begin
          cnt <= cnt + 1;
        end
"""

case_footer = """\
      endcase
"""

print(header)
print(case_header)

for i in range(N):
    print(i, ': begin')
    print("cnt <= %d + 1;" % i)
    print('end')

print(case_default)
print(case_footer)
print(footer)

