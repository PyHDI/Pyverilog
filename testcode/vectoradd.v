module TOP(CLK, RST_X,
           MEM_A, MEM_RE, MEM_WE, MEM_D, MEM_Q, MEM_BUSY, MEM_DONE);
  input CLK;
  input RST_X;
  
  parameter WA = 32;
  parameter WD = 32;
  parameter SIZE = 1024 * 32;

  localparam OFFSET0 = 0;
  localparam OFFSET1 = SIZE * 1;
  localparam OFFSET2 = SIZE * 2;
  
  output reg [WA-1:0] MEM_A;
  output reg MEM_RE;
  output reg MEM_WE;
  output reg [WD-1:0] MEM_D;
  input [WD-1:0] MEM_Q;
  input MEM_DONE;
  input MEM_BUSY;

  reg [WA-1:0] cnt0;
  reg [WA-1:0] cnt1;
  reg [WA-1:0] cnt2;
  reg [WD-1:0] readdata0;
  reg [WD-1:0] readdata1;
  reg [WD-1:0] writedata;
  reg [3:0] state;

  localparam ST_INIT = 0;
  localparam ST_READ0 = 1;
  localparam ST_READWAIT0 = 2;
  localparam ST_INTERVAL = 3;
  localparam ST_READ1 = 4;
  localparam ST_READWAIT1 = 5;
  localparam ST_CALC = 6;
  localparam ST_WRITE = 7;
  localparam ST_WRITEWAIT = 8;
  localparam ST_DONE = 9;

  always @(posedge CLK or negedge RST_X) begin
    if(!RST_X) begin
      state <= ST_INIT;
      cnt0 <= 0;
      cnt1 <= 0;
      cnt2 <= 0;
    end else begin
      if(state == ST_INIT) begin
        MEM_WE <= 0;
        MEM_RE <= 0;
        if(!MEM_BUSY) state <= ST_READ0;
      end else if(state == ST_READ0) begin
        MEM_RE <= 1;
        MEM_A <= cnt0 + OFFSET0;
        if(MEM_BUSY) state <= ST_READWAIT0;
      end else if(state == ST_READWAIT0) begin
        MEM_RE <= 0;
        readdata0 <= MEM_Q;
        if(MEM_DONE) state <= ST_INTERVAL;
      end else if(state == ST_INTERVAL) begin
        if(!MEM_BUSY) state <= ST_READ1;
      end else if(state == ST_READ1) begin
        MEM_RE <= 1;
        MEM_A <= cnt1 + OFFSET1;
        if(MEM_BUSY) state <= ST_READWAIT1;
      end else if(state == ST_READWAIT1) begin
        MEM_RE <= 0;
        readdata1 <= MEM_Q;
        if(MEM_DONE) state <= ST_CALC;
      end else if(state == ST_CALC) begin
        writedata <= readdata0 + readdata1;
        if(!MEM_BUSY) state <= ST_WRITE;
      end else if(state == ST_WRITE) begin
        MEM_WE <= 1;
        MEM_D <= writedata;
        MEM_A <= cnt2 + OFFSET2;
        if(MEM_BUSY) state <= ST_WRITEWAIT;
      end else if(state == ST_WRITEWAIT) begin
        MEM_WE <= 0;
        if(MEM_DONE) begin
          cnt0 <= cnt0 + 32;
          cnt1 <= cnt1 + 32;
          cnt2 <= cnt2 + 32;
          if(cnt0 < SIZE) state <= ST_INIT;
          else state <= ST_DONE;
        end
      end else if(state == ST_DONE) begin
        $display("Done");
        //do nothing
      end
    end
  end
endmodule
