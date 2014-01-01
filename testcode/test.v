module TOP(CLK, RST_X, IN, OUT);
  input CLK, RST_X;
  input [7:0] IN;
  output [7:0] OUT;

  reg [7:0] state;
  reg [7:0] nstate;
  reg [7:0] cnt;

  integer i;

  parameter W_DIR = 5;
  parameter W_FLIT = 8;

  function isvalid;
    input [W_FLIT-1:0] in;
    isvalid = in[W_FLIT-1];
  endfunction
  
  always @* begin
    nstate = 0;
    if( !(isvalid(nstate)) )
      nstate = nstate + 1;
  end
  
  always @(posedge CLK) begin
    if(!RST_X) begin
      state <= 0;
      cnt <= 0;
    end else begin
      state <= nstate;
      cnt <= cnt + 1;
    end
  end
  
endmodule

