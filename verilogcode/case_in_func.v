module TOP(IN1,SEL);
  input IN1,SEL;
  reg b;

  always @* begin
      b <= func1(IN1,SEL);
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
          b = IN1;
        default:
          b = 1'b0;
    endcase
  end
*/

endmodule
