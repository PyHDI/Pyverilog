module TOP(CLK, RST_X, subin, subout);
  parameter WD = 4;
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
