module TOP
  (
   input [3:0] VAL,
   output [3:0] LED0,
   output [3:0] LED1,
   output [3:0] LED2
   );

  SUB 
    # (.MODE(0))
    inst_sub0 (VAL[0], LED0[0]),
    inst_sub1 (VAL[1], LED0[1]),
    inst_sub2 (VAL[2], LED0[2]),
    inst_sub3 (VAL[3], LED0[3]);
  
  SUB 
    # (.MODE(0))
    inst_sub4[3:0] (VAL, LED1),
    inst_sub5[3:0] (VAL, LED2);
    
endmodule

module SUB #
  (
   parameter MODE = 0
   )
  (
   input VAL,
   output LED
   );
  assign LED = ~VAL & MODE;
endmodule

