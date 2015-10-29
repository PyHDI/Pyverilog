module TOP(IN1,SEL);
  input IN1,SEL;
  reg bit;


  always @* begin
      bit <= func1(IN1,SEL);
  end

  function func1;
    input in1;
    input sel;
    case(sel)
        'h0:
          func1 = in1;
        default:
          func1 = 1'b0;
    endcase
  endfunction

/*
  always @* begin
    case(SEL)
        'h0:
          bit = IN1;
        default:
          bit = 1'b0;
    endcase
  end
*/

endmodule
