from __future__ import absolute_import
from __future__ import print_function
import sys
import os
from optparse import OptionParser

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyverilog
from pyverilog.vparser.parser import VerilogCodeParser
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator


def main():
    INFO = "Code converter from AST"
    VERSION = pyverilog.__version__
    USAGE = "Usage: python example_codegen.py file ..."

    def showVersion():
        print(INFO)
        print(VERSION)
        print(USAGE)
        sys.exit()

    optparser = OptionParser()
    optparser.add_option("-v", "--version", action="store_true", dest="showversion",
                         default=False, help="Show the version")
    optparser.add_option("-I", "--include", dest="include", action="append",
                         default=[], help="Include path")
    optparser.add_option("-D", dest="define", action="append",
                         default=[], help="Macro Definition")
    (options, args) = optparser.parse_args()

    filelist = args
    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f):
            raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()

    codeparser = VerilogCodeParser(filelist,
                                   preprocess_include=options.include,
                                   preprocess_define=options.define)

    ast = codeparser.parse()
    directives = codeparser.get_directives()

    codegen = ASTCodeGenerator()
    rslt = codegen.visit(ast)
    print(rslt)


if __name__ == '__main__':
    main()
