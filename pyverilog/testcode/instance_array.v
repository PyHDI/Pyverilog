module TOP
  (
   input [3:0] VAL,
   input [3:0] in0, in1, in2,
   input in3, in4, in5,
   output [3:0] LED0, LED1, LED2, LED3,
   output LED4, LED5
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

  and U0[3:0] (LED3, in0, in1, in2);
  and (LED4, in3, in4, in5), (LED5, in3, in4, in5);
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

