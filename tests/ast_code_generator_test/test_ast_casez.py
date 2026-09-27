from io import StringIO

import pytest

from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
from pyverilog.vparser.parser import VerilogParser


@pytest.mark.parametrize("keyword", ["case", "casex", "casez"])
def test_case_statement_roundtrip(tmp_path, keyword):
    source = """
module top(input [3:0] selector, output reg [3:0] result);
  always @* begin
    %s(selector)
      4'b1???, 4'b0zzz: result = selector;
      default: begin
        result = 4'bxxxx;
      end
    endcase
  end
endmodule
""" % keyword
    parser = VerilogParser(outputdir=str(tmp_path), debug=False)
    original = parser.parse(source)
    generated = ASTCodeGenerator().visit(original)

    reparsed = parser.parse(generated)
    original_tree = StringIO()
    reparsed_tree = StringIO()
    original.show(original_tree, showlineno=False)
    reparsed.show(reparsed_tree, showlineno=False)
    assert original_tree.getvalue() == reparsed_tree.getvalue()
