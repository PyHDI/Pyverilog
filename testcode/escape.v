module \1234 
  (
   \CLK~ , // "\CLK~"
   LE$D, // LE$D
   \1234RST*%&  // "\1234RST*%&"
   );
  
  input \CLK~ , \1234RST*%& ;
  output LE$D;

  genvar i, j;
  generate for(i=0; i<4; i=i+1) begin: \1stLoop
    for(j=0; j<4; j=j+1) begin: \2ndLoop
      wire [7:0] tmp;
      assign tmp = i * j;
    end
  end endgenerate

  wire [7:0] rslt;
  assign rslt = \1stLoop [0].\2ndLoop [1].tmp;
  
endmodule
