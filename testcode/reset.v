module TOP(CLK, RST);
  input CLK, RST;
  reg [7:0] cnt1,cnt2,cnt3,cnt4,cnt5,cnt6,cnt7,cnt8,cnt9,cnt10;
  parameter zero = 0;

  //reset
  always @(posedge CLK) begin
    if(RST[0]) begin
      cnt1 <= 0;
    end else begin
      cnt1 <= 8'd1;
    end
  end

  //reset
  always @(posedge CLK or posedge RST)
    if(RST)
      cnt2 <= 0;
    else
      cnt2 <= 8'd1;

  //not reset
  always @(posedge CLK or posedge RST) begin
    if(RST) begin
      cnt3 <= cnt1[0];
    end else begin
      cnt3 <= 8'd1;
    end
  end

  //not reset
  always @(posedge CLK or posedge RST) begin
    cnt4 <= 0;
  end

  //reset
  always @(posedge CLK or posedge RST) begin
    if(RST) begin
      cnt5 <= {2'd0,6'd0};
    end else begin
      cnt5 <= 8'd1;
    end
  end

  //not reset
  always @(posedge CLK or posedge RST) begin
    if(RST) begin
      cnt6 <= 7'd0 + cnt1[1:0];
    end else begin
      cnt6 <= 8'd1;
    end
  end

  //reset
  always @(posedge CLK) begin
    if(!RST) begin
      cnt7 <= 0;
    end else begin
      cnt7 <= 8'd1;
    end
  end

  //not reset
  always @(posedge CLK) begin
    if(RST && RST) begin
      cnt8 <= 0;
    end else begin
      cnt8 <= 8'd1;
    end
  end

  always @(posedge CLK) begin
    if(RST[zero]) begin
      cnt10 <= 0;
    end else begin
      cnt10 <= 8'd1;
    end
  end

  SUB sub(CLK,RST);

endmodule

module SUB(CLK, RST);
  input CLK, RST;
  reg [7:0] cnt9;
  parameter zero = 0;

  always @(posedge CLK) begin
    if(RST) begin
      cnt9 <= zero;
    end else begin
      cnt9 <= 8'd1;
    end
  end
endmodule