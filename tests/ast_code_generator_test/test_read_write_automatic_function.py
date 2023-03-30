from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.vparser.parser import VerilogCodeParser
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

try:
    from StringIO import StringIO
except:
    from io import StringIO

codedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\


module TOP
(
  CLK,
  RST_X
);

  input CLK;
  input RST_X;
  reg [3:0] cnt;

  function automatic [3:0] inc;
    input [3:0] in;
    begin
      if(&inc) begin
        inc = 0;
      end else begin
        inc = in + 1;
      end
    end
  endfunction


  always @(posedge CLK or negedge RST_X) begin
    if(!RST_X) begin
      cnt <= 0;
    end else begin
      cnt <= inc(cnt);
    end
  end


endmodule

"""

def test():
    filelist = [codedir + 'automatic_function.v']
    output = 'preprocess.out'
    include = None
    define = None
    
    parser = VerilogCodeParser(filelist,
                               preprocess_include=include,
                               preprocess_define=define)
    ast = parser.parse()
    directives = parser.get_directives()

    codegen = ASTCodeGenerator()
    rslt = codegen.visit(ast)
    print(rslt)
    assert(expected == rslt)

if __name__ == '__main__':
    test()
