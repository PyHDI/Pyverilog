"""
   Copyright 2013, Shinya Takamaeda-Yamazaki and Contributors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import pathlib

from pyverilog.vparser.ply.yacc import yacc
from pyverilog.vparser.plyparser import PLYParser, Coord, ParseError
from pyverilog.vparser.preprocessor import VerilogPreprocessor
from pyverilog.vparser.lexer import VerilogLexer
from pyverilog.vparser.ast import *


class VerilogParser(PLYParser):
    'Verilog HDL / SystemVerilog Parser'

    # Expression Precedence
    # Reference: http://hp.vector.co.jp/authors/VA016670/verilog/index.html
    precedence = (
        # <- Weak
        ('left', 'LOR'),
        ('left', 'LAND'),
        ('left', 'OR'),
        ('left', 'XOR', 'XNOR'),
        ('left', 'AND'),
        ('left', 'EQ', 'NE', 'EQL', 'NEL'),
        ('left', 'LT', 'GT', 'LE', 'GE'),
        ('left', 'LSHIFT', 'RSHIFT', 'LSHIFTA', 'RSHIFTA'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE', 'MOD'),
        ('left', 'POWER'),
        ('left', 'CAST'),
        ('right', 'UMINUS', 'UPLUS', 'ULNOT', 'UNOT',
         'UAND', 'UNAND', 'UOR', 'UNOR', 'UXOR', 'UXNOR'),
        # -> Strong
    )

    def __init__(self, outputdir=".", debug=False):
        self.lexer = VerilogLexer(error_func=self._lexer_error_func)
        self.lexer.build()

        self.tokens = self.lexer.tokens
        pathlib.Path(outputdir).mkdir(parents=True, exist_ok=True)
        self.parser = yacc(
            module=self,
            method="LALR",
            outputdir=outputdir,
            debug=debug
        )

    def _lexer_error_func(self, msg, line, column):
        self._parse_error(msg, self._coord(line, column))

    def get_directives(self):
        return self.lexer.get_directives()

    def get_default_nettype(self):
        return self.lexer.get_default_nettype()

    # Returns AST
    def parse(self, text, debug=False):
        return self.parser.parse(text, lexer=self.lexer, debug=debug)

    # --------------------------------------------------------------------------
    # Parse Rule Definition
    # --------------------------------------------------------------------------
    def p_source_text(self, p):
        'source_text : description'
        p[0] = Source(name='', description=p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_description(self, p):
        'description : definitions'
        p[0] = Description(definitions=p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_definitions(self, p):
        'definitions : definitions definition'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_definitions_one(self, p):
        'definitions : definition'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_definition(self, p):
        """definition : moduledef
        | interface
        | struct
        | union
        | enum
        | pragma
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_pragma_assign(self, p):
        'pragma : LPAREN TIMES ID EQUALS expression TIMES RPAREN'
        p[0] = Pragma(PragmaEntry(p[3], p[5], lineno=p.lineno(1)),
                      lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_pragma(self, p):
        'pragma : LPAREN TIMES ID TIMES RPAREN'
        p[0] = Pragma(PragmaEntry(p[3], lineno=p.lineno(1)),
                      lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_moduledef(self, p):
        'moduledef : MODULE modulename paramlist portlist items ENDMODULE'
        p[0] = ModuleDef(name=p[2], paramlist=p[3], portlist=p[4], items=p[5],
                         default_nettype=self.get_default_nettype(), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))
        p[0].end_lineno = p.lineno(6)

    def p_modulename(self, p):
        'modulename : ID'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_modulename_or(self, p):
        'modulename : SENS_OR'  # or primitive
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_paramlist(self, p):
        'paramlist : DELAY LPAREN params RPAREN'
        p[0] = Paramlist(params=p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_paramlist_empty(self, p):
        'paramlist : empty'
        p[0] = Paramlist(params=())

    def p_params(self, p):
        'params : params_begin param_end'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_params_begin(self, p):
        'params_begin : params_begin param'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_params_begin_one(self, p):
        'params_begin : param'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_params_one(self, p):
        'params : param_end'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_param(self, p):
        'param : PARAMETER param_substitution_list COMMA'
        paramlist = [Parameter(rname, rvalue, lineno=p.lineno(2))
                     for rname, rvalue in p[2]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_signed(self, p):
        'param : PARAMETER SIGNED param_substitution_list COMMA'
        paramlist = [Parameter(rname, rvalue, signed=True, lineno=p.lineno(2))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_unsigned(self, p):
        'param : PARAMETER UNSIGNED param_substitution_list COMMA'
        paramlist = [Parameter(rname, rvalue, signed=False, lineno=p.lineno(2))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_width(self, p):
        'param : PARAMETER width param_substitution_list COMMA'
        paramlist = [Parameter(rname, rvalue, p[2], lineno=p.lineno(3))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_signed_width(self, p):
        'param : PARAMETER SIGNED width param_substitution_list COMMA'
        paramlist = [Parameter(rname, rvalue, p[3], signed=True, lineno=p.lineno(3))
                     for rname, rvalue in p[4]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_unsigned_width(self, p):
        'param : PARAMETER UNSIGNED width param_substitution_list COMMA'
        paramlist = [Parameter(rname, rvalue, p[3], signed=False, lineno=p.lineno(3))
                     for rname, rvalue in p[4]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_integer(self, p):
        'param : PARAMETER INTEGER param_substitution_list COMMA'
        paramlist = [Parameter(rname, rvalue, lineno=p.lineno(3))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_end(self, p):
        'param_end : PARAMETER param_substitution_list'
        paramlist = [Parameter(rname, rvalue, lineno=p.lineno(2))
                     for rname, rvalue in p[2]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_end_signed(self, p):
        'param_end : PARAMETER SIGNED param_substitution_list'
        paramlist = [Parameter(rname, rvalue, signed=True, lineno=p.lineno(2))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_end_unsigned(self, p):
        'param_end : PARAMETER UNSIGNED param_substitution_list'
        paramlist = [Parameter(rname, rvalue, signed=False, lineno=p.lineno(2))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_end_width(self, p):
        'param_end : PARAMETER width param_substitution_list'
        paramlist = [Parameter(rname, rvalue, p[2], lineno=p.lineno(3))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_end_signed_width(self, p):
        'param_end : PARAMETER SIGNED width param_substitution_list'
        paramlist = [Parameter(rname, rvalue, p[3], signed=True, lineno=p.lineno(3))
                     for rname, rvalue in p[4]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_end_unsigned_width(self, p):
        'param_end : PARAMETER UNSIGNED width param_substitution_list'
        paramlist = [Parameter(rname, rvalue, p[3], signed=False, lineno=p.lineno(3))
                     for rname, rvalue in p[4]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_end_integer(self, p):
        'param_end : PARAMETER INTEGER param_substitution_list'
        paramlist = [Parameter(rname, rvalue, lineno=p.lineno(3))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_portlist(self, p):
        'portlist : LPAREN ports RPAREN SEMICOLON'
        p[0] = Portlist(ports=p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_portlist_io(self, p):
        'portlist : LPAREN ioports RPAREN SEMICOLON'
        p[0] = Portlist(ports=p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_portlist_paren_empty(self, p):
        'portlist : LPAREN RPAREN SEMICOLON'
        p[0] = Portlist(ports=(), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_portlist_empty(self, p):
        'portlist : SEMICOLON'
        p[0] = Portlist(ports=(), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_ports(self, p):
        'ports : ports COMMA portname'
        port = Port(name=p[3], width=None, pdims=None, udims=None, type=None, lineno=p.lineno(1))
        p[0] = p[1] + (port,)
        p.set_lineno(0, p.lineno(1))

    def p_ports_one(self, p):
        'ports : portname'
        port = Port(name=p[1], width=None, pdims=None, udims=None, type=None, lineno=p.lineno(1))
        p[0] = (port,)
        p.set_lineno(0, p.lineno(1))

    def p_portname(self, p):
        'portname : ID'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_sigtypes(self, p):
        'sigtypes : sigtypes sigtype'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_sigtypes_one(self, p):
        'sigtypes : sigtype'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_sigtype_input(self, p):
        'sigtype : INPUT'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_sigtype_output(self, p):
        'sigtype : OUTPUT'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_sigtype_inout(self, p):
        'sigtype : INOUT'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_sigtype_tri(self, p):
        'sigtype : TRI'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_sigtype_reg(self, p):
        'sigtype : REG'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_sigtype_wire(self, p):
        'sigtype : WIRE'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_sigtype_signed(self, p):
        'sigtype : SIGNED'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_sigtype_unsigned(self, p):
        'sigtype : UNSIGNED'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_sigtype_logic(self, p):
        'sigtype : LOGIC'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_sigtype_supply0(self, p):
        'sigtype : SUPPLY0'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_sigtype_supply1(self, p):
        'sigtype : SUPPLY1'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_sigtype_custom(self, p):
        'sigtype : ID'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_sigtype_custom_modport(self, p):
        'sigtype : ID DOT ID'
        p[0] = (p[1], p[3])
        p.set_lineno(0, p.lineno(1))

    def p_ioports(self, p):
        'ioports : ioports COMMA ioport'
        if isinstance(p[3], str):
            t = None
            for r in reversed(p[1]):
                if isinstance(r.first, Input):
                    t = Ioport(Input(name=p[3], width=r.first.width, lineno=p.lineno(3)),
                               lineno=p.lineno(3))
                    break
                if isinstance(r.first, Output) and r.second is None:
                    t = Ioport(Output(name=p[3], width=r.first.width, lineno=p.lineno(3)),
                               lineno=p.lineno(3))
                    break
                if isinstance(r.first, Output) and isinstance(r.second, Reg):
                    t = Ioport(Output(name=p[3], width=r.first.width, lineno=p.lineno(3)),
                               Reg(name=p[3], width=r.first.width,
                                   lineno=p.lineno(3)),
                               lineno=p.lineno(3))
                    break
                if isinstance(r.first, Inout):
                    t = Ioport(Inout(name=p[3], width=r.first.width, lineno=p.lineno(3)),
                               lineno=p.lineno(3))
                    break
            p[0] = p[1] + (t,)
        else:
            p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_ioports_one(self, p):
        'ioports : ioport_head'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def create_ioport(self, sigtypes, name, width=None, pdims=None, udims=None, lineno=0):
        signed = False
        first = None
        second = None

        self.typecheck_ioport(sigtypes)

        sigtypes = list(sigtypes)

        if 'signed' in sigtypes:
            signed = True
            sigtypes.remove('signed')

        elif 'unsigned' in sigtypes:
            signed = False
            sigtypes.remove('unsigned')

        if len(sigtypes) > 2:
            raise ParseError("Syntax Error")

        if 'input' in sigtypes:
            first = Input(name=name, width=width, signed=signed,
                          pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('input')

        elif 'output' in sigtypes:
            first = Output(name=name, width=width, signed=signed,
                           pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('output')

        elif 'inout' in sigtypes:
            first = Inout(name=name, width=width, signed=signed,
                          pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('inout')

        if len(sigtypes) > 1:
            raise ParseError("Syntax Error")

        if 'wire' in sigtypes:
            second = Wire(name=name, width=width, signed=signed,
                          pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('wire')

        elif 'reg' in sigtypes:
            second = Reg(name=name, width=width, signed=signed,
                         pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('reg')

        elif 'tri' in sigtypes:
            second = Tri(name=name, width=width, signed=signed,
                         pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('tri')

        elif 'logic' in sigtypes:
            second = Logic(name=name, width=width, signed=signed,
                           pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('logic')

        if len(sigtypes) > 0:
            if isinstance(sigtypes[0], tuple):
                typename = sigtypes[0][0]
                modportname = sigtypes[0][1]
            else:
                typename = sigtypes[0][0]
                modportname = None
            second = CustomVariable(typename=typename, name=name, modportname=modportname,
                                    width=width, signed=signed,
                                    pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove(sigtypes[0])

        if len(sigtypes) > 0:
            raise ParseError("Syntax Error")

        return Ioport(first, second, lineno=lineno)

    def typecheck_ioport(self, sigtypes):
        if len(sigtypes) > 3:
            raise ParseError("Syntax Error")

        if len(sigtypes) != len(set(sigtypes)):
            raise ParseError("Syntax Error")

        if 'signed' not in sigtypes and 'unsigned' not in sigtypes and len(sigtypes) > 2:
            raise ParseError("Syntax Error")

        if 'signed' in sigtypes and len(sigtypes) == 1:
            raise ParseError("Syntax Error")

        if 'unsigned' in sigtypes and len(sigtypes) == 1:
            raise ParseError("Syntax Error")

        if 'signed' in sigtypes and 'unsigned' in sigtypes:
            raise ParseError("Syntax Error")

        # if 'input' not in sigtypes and 'output' not in sigtypes and 'inout' not in sigtypes:
        #     raise ParseError("Syntax Error")

        if 'input' in sigtypes and 'output' in sigtypes:
            raise ParseError("Syntax Error")

        if 'inout' in sigtypes and 'output' in sigtypes:
            raise ParseError("Syntax Error")

        if 'inout' in sigtypes and 'input' in sigtypes:
            raise ParseError("Syntax Error")

        if 'input' in sigtypes and 'reg' in sigtypes:
            raise ParseError("Syntax Error")

        if 'inout' in sigtypes and 'reg' in sigtypes:
            raise ParseError("Syntax Error")

        if 'input' in sigtypes and 'tri' in sigtypes:
            raise ParseError("Syntax Error")

        if 'output' in sigtypes and 'tri' in sigtypes:
            raise ParseError("Syntax Error")

    def p_ioport(self, p):
        'ioport : sigtypes portname'
        p[0] = self.create_ioport(p[1], p[2], lineno=p.lineno(2))
        p.set_lineno(0, p.lineno(1))

    def p_ioport_pdims_width(self, p):
        'ioport : sigtypes pdims_width portname'
        pdims, width = p[2]
        p[0] = self.create_ioport(p[1], p[3], width=width, pdims=pdims, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_ioport_pdims_width_udims(self, p):
        'ioport : sigtypes pdims_width portname udims'
        pdims, width = p[2]
        p[0] = self.create_ioport(p[1], p[3], width=width, pdims=pdims, udims=p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_ioport_head(self, p):
        'ioport_head : sigtypes portname'
        p[0] = self.create_ioport(p[1], p[2], lineno=p.lineno(2))
        p.set_lineno(0, p.lineno(1))

    def p_ioport_head_pdims_width(self, p):
        'ioport_head : sigtypes pdims_width portname'
        pdims, width = p[2]
        p[0] = self.create_ioport(p[1], p[3], width=width, pdims=pdims, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_ioport_head_pdims_width_udims(self, p):
        'ioport_head : sigtypes pdims_width portname udims'
        pdims, width = p[2]
        p[0] = self.create_ioport(p[1], p[3], width=width, pdims=pdims, udims=p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_ioport_portname(self, p):
        'ioport : portname'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_width_vector(self, p):
        'width : LBRACKET expression COLON expression RBRACKET'
        p[0] = Width(p[2], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_length_vector(self, p):
        'length : LBRACKET expression COLON expression RBRACKET'
        p[0] = Length(p[2], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_length(self, p):
        'length : LBRACKET expression RBRACKET'
        p[0] = Length(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def _separate_pdims_width(self, dims):
        if dims[-1].msb is None:
            raise ParseError("Syntax Error")
        if dims[-1].lsb is None:
            raise ParseError("Syntax Error")

        width = Width(dims[-1].msb, dims[-1].lsb, lineno=dims[-1].lineno)

        if len(dims[:-1]) == 0:
            pdims = None
        else:
            pdims = Dims(dims[:-1], lineno=dims[0].lineno)

        return pdims, width

    def p_pdims_width(self, p):
        'pdims_width : dims'
        pdims, width = self._separate_pdims_width(p[1])
        p[0] = (pdims, width)
        p.set_lineno(0, p.lineno(1))

    def p_udims(self, p):
        'udims : dims'
        p[0] = Dims(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_dims(self, p):
        'dims : dims length'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_dims_one(self, p):
        'dims : length'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_items(self, p):
        'items : items item'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_items_one(self, p):
        'items : item'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_items_empty(self, p):
        'items : empty'
        p[0] = ()

    def p_item(self, p):
        """item : standard_item
        | generate
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_standard_item(self, p):
        """standard_item : decl
        | integerdecl
        | timedecl
        | realdecl
        | realtimedecl
        | shortintdecl
        | intdecl
        | longintdecl
        | bytedecl
        | bitdecl
        | shortrealdecl
        | declassign
        | typedef
        | parameterdecl
        | localparamdecl
        | genvardecl
        | assignment
        | always
        | always_ff
        | always_comb
        | always_latch
        | initial
        | instance
        | function
        | task
        | pragma
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # Signal Decl
    def create_decl(self, sigtypes, name, width=None, pdims=None, udims=None, lineno=0):
        signed = False
        decls = []

        self.typecheck_decl(sigtypes, pdims, udims)

        sigtypes = list(sigtypes)

        if 'signed' in sigtypes:
            signed = True
            sigtypes.remove('signed')

        elif 'unsigned' in sigtypes:
            signed = False
            sigtypes.remove('unsigned')

        if len(sigtypes) > 2:
            raise ParseError("Syntax Error")

        if 'input' in sigtypes:
            decls.append(Input(name=name, width=width,
                               signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('input')

        elif 'output' in sigtypes:
            decls.append(Output(name=name, width=width,
                                signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('output')

        elif 'inout' in sigtypes:
            decls.append(Inout(name=name, width=width,
                               signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('inout')

        if len(sigtypes) > 1:
            raise ParseError("Syntax Error")

        if 'wire' in sigtypes:
            decls.append(Wire(name=name, width=width,
                              signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('wire')

        elif 'reg' in sigtypes:
            decls.append(Reg(name=name, width=width,
                             signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('reg')

        elif 'tri' in sigtypes:
            decls.append(Tri(name=name, width=width,
                             signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('tri')

        elif 'logic' in sigtypes:
            decls.append(Logic(name=name, width=width,
                               signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('logic')

        elif 'supply0' in sigtypes:
            decls.append(Supply(name=name, value=IntConst('0', lineno=lineno),
                                width=width, signed=signed, lineno=lineno))
            sigtypes.remove('supply0')

        elif 'supply1' in sigtypes:
            decls.append(Supply(name=name, value=IntConst('1', lineno=lineno),
                                width=width, signed=signed, lineno=lineno))
            sigtypes.remove('supply1')

        if len(sigtypes) > 0:
            if isinstance(sigtypes[0], tuple):
                typename = sigtypes[0][0]
                modportname = sigtypes[0][1]
            else:
                typename = sigtypes[0][0]
                modportname = None
            delcs.append(CustomVariable(typename=typename, name=name, modportname=modportname,
                                        width=width, signed=signed,
                                        pdims=pdims, udims=udims, lineno=lineno))
            sigtypes.remove(sigtypes[0])

        if len(sigtypes) > 0:
            raise ParseError("Syntax Error")

        return decls

    def typecheck_decl(self, sigtypes, pdims=None, udims=None):
        if len(sigtypes) > 3:
            raise ParseError("Syntax Error")

        if len(sigtypes) != len(set(sigtypes)):
            raise ParseError("Syntax Error")

        if 'signed' not in sigtypes and 'unsigned' not in sigtypes and len(sigtypes) > 2:
            raise ParseError("Syntax Error")

        if 'signed' in sigtypes and len(sigtypes) == 1:
            raise ParseError("Syntax Error")

        if 'unsigned' in sigtypes and len(sigtypes) == 1:
            raise ParseError("Syntax Error")

        if 'signed' in sigtypes and 'unsigned' in sigtypes:
            raise ParseError("Syntax Error")

        if ('supply0' in sigtypes or 'supply1' in sigtypes) and pdims is not None:
            raise ParseError("SyntaxError")

        if ('supply0' in sigtypes or 'supply1' in sigtypes) and udims is not None:
            raise ParseError("SyntaxError")

        if 'input' in sigtypes and 'output' in sigtypes:
            raise ParseError("Syntax Error")

        if 'inout' in sigtypes and 'output' in sigtypes:
            raise ParseError("Syntax Error")

        if 'inout' in sigtypes and 'input' in sigtypes:
            raise ParseError("Syntax Error")

        if 'input' in sigtypes and 'reg' in sigtypes:
            raise ParseError("Syntax Error")

        if 'inout' in sigtypes and 'reg' in sigtypes:
            raise ParseError("Syntax Error")

        if 'input' in sigtypes and 'tri' in sigtypes:
            raise ParseError("Syntax Error")

        if 'output' in sigtypes and 'tri' in sigtypes:
            raise ParseError("Syntax Error")

    def p_decl(self, p):
        'decl : sigtypes declnamelist SEMICOLON'
        decllist = []
        for rname, rudims in p[2]:
            decllist.extend(self.create_decl(p[1], rname, pdims=None, udims=rudims,
                                             lineno=p.lineno(2)))
        p[0] = Decl(tuple(decllist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_decl_pdims_width(self, p):
        'decl : sigtypes pdims_width declnamelist SEMICOLON'
        decllist = []
        pdims, width = p[2]
        for rname, rudims in p[3]:
            decllist.extend(self.create_decl(p[1], rname, width=width, pdims=pdims, udims=rudims,
                                             lineno=p.lineno(1)))
        p[0] = Decl(tuple(decllist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_declnamelist(self, p):
        'declnamelist : declnamelist COMMA declname'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_declnamelist_one(self, p):
        'declnamelist : declname'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_declname(self, p):
        'declname : ID'
        p[0] = (p[1], None)
        p.set_lineno(0, p.lineno(1))

    def p_declarray(self, p):
        'declname : ID udims'
        p[0] = (p[1], p[2])
        p.set_lineno(0, p.lineno(1))

    # Decl and Assign
    def create_declassign(self, sigtypes, name, assign, width=None, pdims=None, udims=None, lineno=0):
        signed = False
        decls = []

        self.typecheck_declassign(sigtypes)

        sigtypes = list(sigtypes)

        if 'signed' in sigtypes:
            signed = True
            sigtypes.remove('signed')

        elif 'unsigned' in sigtypes:
            signed = False
            sigtypes.remove('unsigned')

        if len(sigtypes) > 2:
            raise ParseError("Syntax Error")

        if 'input' in sigtypes:
            decls.append(Input(name=name, width=width,
                               signed=signed, lineno=lineno))
            sigtypes.remove('input')

        elif 'output' in sigtypes:
            decls.append(Output(name=name, width=width,
                                signed=signed, lineno=lineno))
            sigtypes.remove('output')

        elif 'inout' in sigtypes:
            decls.append(Inout(name=name, width=width,
                               signed=signed, lineno=lineno))
            sigtypes.remove('inout')

        if len(sigtypes) > 1:
            raise ParseError("Syntax Error")

        if 'wire' in sigtypes:
            decls.append(Wire(name=name, width=width,
                              signed=signed, lineno=lineno))
            sigtypes.remove('wire')

        elif 'reg' in sigtypes:
            decls.append(Reg(name=name, width=width,
                             signed=signed, lineno=lineno))
            sigtypes.remove('reg')

        elif 'logic' in sigtypes:
            decls.append(Logic(name=name, width=width,
                               signed=signed, lineno=lineno))
            sigtypes.remove('logic')

        if len(sigtypes) > 0:
            if isinstance(sigtypes[0], tuple):
                typename = sigtypes[0][0]
                modportname = sigtypes[0][1]
            else:
                typename = sigtypes[0][0]
                modportname = None
            delcs.append(CustomVariable(typename=typename, name=name, modportname=modportname,
                                        width=width, signed=signed,
                                        pdims=pdims, udims=udims, lineno=lineno))
            sigtypes.remove(sigtypes[0])

        if len(sigtypes) > 0:
            raise ParseError("Syntax Error")

        decls.append(assign)
        return decls

    def typecheck_declassign(self, sigtypes):
        if len(sigtypes) > 3:
            raise ParseError("Syntax Error")

        if len(sigtypes) != len(set(sigtypes)):
            raise ParseError("Syntax Error")

        if 'signed' not in sigtypes and 'unsigned' not in sigtypes and len(sigtypes) > 2:
            raise ParseError("Syntax Error")

        if 'signed' in sigtypes and len(sigtypes) == 1:
            raise ParseError("Syntax Error")

        if 'unsigned' in sigtypes and len(sigtypes) == 1:
            raise ParseError("Syntax Error")

        if 'signed' in sigtypes and 'unsigned' in sigtypes:
            raise ParseError("Syntax Error")

        if 'input' in sigtypes and 'output' in sigtypes:
            raise ParseError("Syntax Error")

        if 'inout' in sigtypes and 'output' in sigtypes:
            raise ParseError("Syntax Error")

        if 'inout' in sigtypes and 'input' in sigtypes:
            raise ParseError("Syntax Error")

        if 'input' in sigtypes and 'reg' in sigtypes:
            raise ParseError("Syntax Error")

        if 'inout' in sigtypes and 'reg' in sigtypes:
            raise ParseError("Syntax Error")

        if 'reg' not in sigtypes and 'wire' not in sigtypes:
            raise ParseError("Syntax Error")

        if 'supply0' in sigtypes and len(sigtypes) != 1:
            raise ParseError("Syntax Error")

        if 'supply1' in sigtypes and len(sigtypes) != 1:
            raise ParseError("Syntax Error")

    def p_declassign(self, p):
        'declassign : sigtypes declassign_element SEMICOLON'
        decllist = self.create_declassign(
            p[1], p[2][0], p[2][1], lineno=p.lineno(2))
        p[0] = Decl(decllist, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_declassign_pdims_width(self, p):
        'declassign : sigtypes pdims_width declassign_element SEMICOLON'
        pdims, width = p[2]
        decllist = self.create_declassign(
            p[1], p[3][0], p[3][1], width=width, pdims=pdims, lineno=p.lineno(3))
        p[0] = Decl(tuple(decllist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_declassign_element(self, p):
        'declassign_element : ID EQUALS rvalue'
        assign = Assign(Lvalue(Identifier(p[1], lineno=p.lineno(1)), lineno=p.lineno(1)),
                        p[3], lineno=p.lineno(1))
        p[0] = (p[1], assign)
        p.set_lineno(0, p.lineno(1))

    def p_declassign_element_nodelay_delay(self, p):
        'declassign_element : ID EQUALS delay rvalue'
        assign = Assign(Lvalue(Identifier(p[1], lineno=p.lineno(1)), lineno=p.lineno(1)),
                        p[4], None, p[3], lineno=p.lineno(1))
        p[0] = (p[1], assign)
        p.set_lineno(0, p.lineno(1))

    def p_declassign_element_delay_nodelay(self, p):
        'declassign_element : delay ID EQUALS rvalue'
        assign = Assign(Lvalue(Identifier(p[2], lineno=p.lineno(2)), lineno=p.lineno(2)),
                        p[4], p[1], None, lineno=p.lineno(2))
        p[0] = (p[2], assign)
        p.set_lineno(0, p.lineno(2))

    def p_declassign_element_delay_delay(self, p):
        'declassign_element : delay ID EQUALS delay rvalue'
        assign = Assign(Lvalue(Identifier(p[2], lineno=p.lineno(2)), lineno=p.lineno(2)),
                        p[5], p[1], p[4], lineno=p.lineno(2))
        p[0] = (p[2], assign)
        p.set_lineno(0, p.lineno(2))

    # Integer
    def p_integerdecl(self, p):
        'integerdecl : INTEGER integernamelist SEMICOLON'
        intlist = [Integer(rname,
                           signed=True,
                           value=rvalue,
                           lineno=p.lineno(2)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_integerdecl_signed(self, p):
        'integerdecl : INTEGER SIGNED integernamelist SEMICOLON'
        intlist = [Integer(rname,
                           signed=True,
                           value=rvalue,
                           lineno=p.lineno(3)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_integerdecl_unsigned(self, p):
        'integerdecl : INTEGER UNSIGNED integernamelist SEMICOLON'
        intlist = [Integer(rname,
                           signed=False,
                           value=rvalue,
                           lineno=p.lineno(3)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_integernamelist(self, p):
        'integernamelist : integernamelist COMMA integername'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_integernamelist_one(self, p):
        'integernamelist : integername'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_integername_init(self, p):
        'integername : ID EQUALS rvalue'
        p[0] = (p[1], p[3])
        p.set_lineno(0, p.lineno(1))

    def p_integername(self, p):
        'integername : ID'
        p[0] = (p[1], None)
        p.set_lineno(0, p.lineno(1))

    # Time
    def p_timedecl(self, p):
        'timedecl : TIME timenamelist SEMICOLON'
        intlist = [Time(rname,
                        signed=True,
                        value=rvalue,
                        lineno=p.lineno(2)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_timedecl_signed(self, p):
        'timedecl : TIME SIGNED timenamelist SEMICOLON'
        intlist = [Time(rname,
                        signed=True,
                        value=rvalue,
                        lineno=p.lineno(3)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_timedecl_unsigned(self, p):
        'timedecl : TIME UNSIGNED timenamelist SEMICOLON'
        intlist = [Time(rname,
                        signed=False,
                        value=rvalue,
                        lineno=p.lineno(3)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_timenamelist(self, p):
        'timenamelist : timenamelist COMMA timename'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_timenamelist_one(self, p):
        'timenamelist : timename'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_timename_init(self, p):
        'timename : ID EQUALS rvalue'
        p[0] = (p[1], p[3])
        p.set_lineno(0, p.lineno(1))

    def p_timename(self, p):
        'timename : ID'
        p[0] = (p[1], None)
        p.set_lineno(0, p.lineno(1))

    # Real
    def p_realdecl(self, p):
        'realdecl : REAL realnamelist SEMICOLON'
        reallist = [Real(p[1],
                         lineno=p.lineno(2)) for r in p[2]]
        p[0] = Decl(tuple(reallist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_realnamelist(self, p):
        'realnamelist : realnamelist COMMA realname'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_realnamelist_one(self, p):
        'realnamelist : realname'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_realname(self, p):
        'realname : ID'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # Realtime
    def p_realtimedecl(self, p):
        'realtimedecl : REALTIME realtimenamelist SEMICOLON'
        realtimelist = [Realtime(p[1],
                                 lineno=p.lineno(2)) for r in p[2]]
        p[0] = Decl(tuple(realtimelist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_realtimenamelist(self, p):
        'realtimenamelist : realtimenamelist COMMA realtimename'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_realtimenamelist_one(self, p):
        'realtimenamelist : realtimename'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_realtimename(self, p):
        'realtimename : ID'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # ShortInt
    def p_shortintdecl(self, p):
        'shortintdecl : SHORTINT shortintnamelist SEMICOLON'
        intlist = [ShortInt(rname,
                            signed=True,
                            value=rvalue,
                            lineno=p.lineno(2)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_shortintdecl_signed(self, p):
        'shortintdecl : SHORTINT SIGNED shortintnamelist SEMICOLON'
        intlist = [ShortInt(rname,
                            signed=True,
                            value=rvalue,
                            lineno=p.lineno(3)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_shortintdecl_unsigned(self, p):
        'shortintdecl : SHORTINT UNSIGNED shortintnamelist SEMICOLON'
        intlist = [ShortInt(rname,
                            signed=False,
                            value=rvalue,
                            lineno=p.lineno(3)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_shortintnamelist(self, p):
        'shortintnamelist : shortintnamelist COMMA shortintname'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_shortintnamelist_one(self, p):
        'shortintnamelist : shortintname'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_shortintname_init(self, p):
        'shortintname : ID EQUALS rvalue'
        p[0] = (p[1], p[3])
        p.set_lineno(0, p.lineno(1))

    def p_shortintname(self, p):
        'shortintname : ID'
        p[0] = (p[1], None)
        p.set_lineno(0, p.lineno(1))

    # Int
    def p_intdecl(self, p):
        'intdecl : INT intnamelist SEMICOLON'
        intlist = [Int(rname,
                       signed=True,
                       value=rvalue,
                       lineno=p.lineno(2)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_intdecl_signed(self, p):
        'intdecl : INT SIGNED intnamelist SEMICOLON'
        intlist = [Int(rname,
                       signed=True,
                       value=rvalue,
                       lineno=p.lineno(3)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_intdecl_unsigned(self, p):
        'intdecl : INT UNSIGNED intnamelist SEMICOLON'
        intlist = [Int(rname,
                       signed=False,
                       value=rvalue,
                       lineno=p.lineno(3)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_intnamelist(self, p):
        'intnamelist : intnamelist COMMA intname'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_intnamelist_one(self, p):
        'intnamelist : intname'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_intname_init(self, p):
        'intname : ID EQUALS rvalue'
        p[0] = (p[1], p[3])
        p.set_lineno(0, p.lineno(1))

    def p_intname(self, p):
        'intname : ID'
        p[0] = (p[1], None)
        p.set_lineno(0, p.lineno(1))

    # LongInt
    def p_longintdecl(self, p):
        'longintdecl : LONGINT longintnamelist SEMICOLON'
        intlist = [LongInt(rname,
                           signed=True,
                           value=rvalue,
                           lineno=p.lineno(2)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_longintdecl_signed(self, p):
        'longintdecl : LONGINT SIGNED longintnamelist SEMICOLON'
        intlist = [LongInt(rname,
                           signed=True,
                           value=rvalue,
                           lineno=p.lineno(3)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_longintdecl_unsigned(self, p):
        'longintdecl : LONGINT UNSIGNED longintnamelist SEMICOLON'
        intlist = [LongInt(rname,
                           signed=False,
                           value=rvalue,
                           lineno=p.lineno(3)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(intlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_longintnamelist(self, p):
        'longintnamelist : longintnamelist COMMA longintname'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_longintnamelist_one(self, p):
        'longintnamelist : longintname'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_longintname_init(self, p):
        'longintname : ID EQUALS rvalue'
        p[0] = (p[1], p[3])
        p.set_lineno(0, p.lineno(1))

    def p_longintname(self, p):
        'longintname : ID'
        p[0] = (p[1], None)
        p.set_lineno(0, p.lineno(1))

    # Byte
    def p_bytedecl(self, p):
        'bytedecl : BYTE bytenamelist SEMICOLON'
        bytelist = [Byte(rname,
                         signed=True,
                         value=rvalue,
                         lineno=p.lineno(2)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(bytelist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_bytedecl_signed(self, p):
        'bytedecl : BYTE SIGNED bytenamelist SEMICOLON'
        bytelist = [Byte(rname,
                         signed=True,
                         value=rvalue,
                         lineno=p.lineno(3)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(bytelist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_bytedecl_unsigned(self, p):
        'bytedecl : BYTE UNSIGNED bytenamelist SEMICOLON'
        bytelist = [Byte(rname,
                         signed=False,
                         value=rvalue,
                         lineno=p.lineno(3)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(bytelist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_bytenamelist(self, p):
        'bytenamelist : bytenamelist COMMA bytename'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_bytenamelist_one(self, p):
        'bytenamelist : bytename'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_bytename_init(self, p):
        'bytename : ID EQUALS rvalue'
        p[0] = (p[1], p[3])
        p.set_lineno(0, p.lineno(1))

    def p_bytename(self, p):
        'bytename : ID'
        p[0] = (p[1], None)
        p.set_lineno(0, p.lineno(1))

    # Bit
    def p_bitdecl(self, p):
        'bitdecl : BIT bitnamelist SEMICOLON'
        bitlist = [Bit(rname,
                       width=None,
                       signed=True,
                       value=rvalue,
                       lineno=p.lineno(2)) for rname, rvalue in p[2]]
        p[0] = Decl(tuple(bitlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_bitdecl_width(self, p):
        'bitdecl : BIT width bitnamelist SEMICOLON'
        bitlist = [Bit(rname,
                       width=p[2],
                       signed=True,
                       value=rvalue,
                       lineno=p.lineno(3)) for rname, rvalue in p[3]]
        p[0] = Decl(tuple(bitlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_bitdecl_signed(self, p):
        'bitdecl : BIT SIGNED bitnamelist SEMICOLON'
        bitlist = [Bit(rname,
                       width=None,
                       signed=True,
                       value=rvalue,
                       lineno=p.lineno(3)) for rname, rvalue in p[3]]
        p[0] = Decl(tuple(bitlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_bitdecl_signed_width(self, p):
        'bitdecl : BIT SIGNED width bitnamelist SEMICOLON'
        bitlist = [Bit(rname,
                       width=p[3],
                       signed=True,
                       value=rvalue,
                       lineno=p.lineno(4)) for rname, rvalue in p[4]]
        p[0] = Decl(tuple(bitlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_bitdecl_unsigned(self, p):
        'bitdecl : BIT UNSIGNED bitnamelist SEMICOLON'
        bitlist = [Bit(rname,
                       width=None,
                       signed=False,
                       value=rvalue,
                       lineno=p.lineno(3)) for rname, rvalue in p[3]]
        p[0] = Decl(tuple(bitlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_bitdecl_unsigned_width(self, p):
        'bitdecl : BIT UNSIGNED width bitnamelist SEMICOLON'
        bitlist = [Bit(rname,
                       width=p[3],
                       signed=False,
                       value=rvalue,
                       lineno=p.lineno(4)) for rname, rvalue in p[4]]
        p[0] = Decl(tuple(bitlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_bitnamelist(self, p):
        'bitnamelist : bitnamelist COMMA bitname'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_bitnamelist_one(self, p):
        'bitnamelist : bitname'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_bitname_init(self, p):
        'bitname : ID EQUALS rvalue'
        p[0] = (p[1], p[3])
        p.set_lineno(0, p.lineno(1))

    def p_bitname(self, p):
        'bitname : ID'
        p[0] = (p[1], None)
        p.set_lineno(0, p.lineno(1))

    # ShortReal
    def p_shortrealdecl(self, p):
        'shortrealdecl : SHORTREAL shortrealnamelist SEMICOLON'
        shortreallist = [ShortReal(p[1],
                                   lineno=p.lineno(2)) for r in p[2]]
        p[0] = Decl(tuple(shortreallist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_shortrealnamelist(self, p):
        'shortrealnamelist : shortrealnamelist COMMA shortrealname'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_shortrealnamelist_one(self, p):
        'shortrealnamelist : shortrealname'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_shortrealname(self, p):
        'shortrealname : ID'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # Parameter
    def p_parameterdecl(self, p):
        'parameterdecl : PARAMETER param_substitution_list SEMICOLON'
        paramlist = [Parameter(rname, rvalue, lineno=p.lineno(2))
                     for rname, rvalue in p[2]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_parameterdecl_signed(self, p):
        'parameterdecl : PARAMETER SIGNED param_substitution_list SEMICOLON'
        paramlist = [Parameter(rname, rvalue, signed=True, lineno=p.lineno(2))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_parameterdecl_unsigned(self, p):
        'parameterdecl : PARAMETER UNSIGNED param_substitution_list SEMICOLON'
        paramlist = [Parameter(rname, rvalue, signed=False, lineno=p.lineno(2))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_parameterdecl_width(self, p):
        'parameterdecl : PARAMETER width param_substitution_list SEMICOLON'
        paramlist = [Parameter(rname, rvalue, p[2], lineno=p.lineno(3))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_parameterdecl_signed_width(self, p):
        'parameterdecl : PARAMETER SIGNED width param_substitution_list SEMICOLON'
        paramlist = [Parameter(rname, rvalue, p[3], signed=True, lineno=p.lineno(3))
                     for rname, rvalue in p[4]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_parameterdecl_unsigned_width(self, p):
        'parameterdecl : PARAMETER UNSIGNED width param_substitution_list SEMICOLON'
        paramlist = [Parameter(rname, rvalue, p[3], signed=False, lineno=p.lineno(3))
                     for rname, rvalue in p[4]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_parameterdecl_integer(self, p):
        'parameterdecl : PARAMETER INTEGER param_substitution_list SEMICOLON'
        paramlist = [Parameter(rname, rvalue, lineno=p.lineno(3))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_localparamdecl(self, p):
        'localparamdecl : LOCALPARAM param_substitution_list SEMICOLON'
        paramlist = [Localparam(rname, rvalue, lineno=p.lineno(2))
                     for rname, rvalue in p[2]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_localparamdecl_signed(self, p):
        'localparamdecl : LOCALPARAM SIGNED param_substitution_list SEMICOLON'
        paramlist = [Localparam(rname, rvalue, signed=True, lineno=p.lineno(2))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_localparamdecl_unsigned(self, p):
        'localparamdecl : LOCALPARAM UNSIGNED param_substitution_list SEMICOLON'
        paramlist = [Localparam(rname, rvalue, signed=False, lineno=p.lineno(2))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_localparamdecl_width(self, p):
        'localparamdecl : LOCALPARAM width param_substitution_list SEMICOLON'
        paramlist = [Localparam(rname, rvalue, p[2], lineno=p.lineno(3))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_localparamdecl_signed_width(self, p):
        'localparamdecl : LOCALPARAM SIGNED width param_substitution_list SEMICOLON'
        paramlist = [Localparam(rname, rvalue, p[3], signed=True, lineno=p.lineno(3))
                     for rname, rvalue in p[4]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_localparamdecl_unsigned_width(self, p):
        'localparamdecl : LOCALPARAM UNSIGNED width param_substitution_list SEMICOLON'
        paramlist = [Localparam(rname, rvalue, p[3], signed=False, lineno=p.lineno(3))
                     for rname, rvalue in p[4]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_localparamdecl_integer(self, p):
        'localparamdecl : LOCALPARAM INTEGER param_substitution_list SEMICOLON'
        paramlist = [Localparam(rname, rvalue, lineno=p.lineno(3))
                     for rname, rvalue in p[3]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_substitution_list(self, p):
        'param_substitution_list : param_substitution_list COMMA param_substitution'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_param_substitution_list_one(self, p):
        'param_substitution_list : param_substitution'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_param_substitution(self, p):
        'param_substitution : ID EQUALS rvalue'
        p[0] = (p[1], p[3])
        p.set_lineno(0, p.lineno(1))

    def p_assignment(self, p):
        'assignment : ASSIGN lvalue EQUALS rvalue SEMICOLON'
        p[0] = Assign(p[2], p[4], None, None, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_assignment_nodelay_delay(self, p):
        'assignment : ASSIGN lvalue EQUALS delay rvalue SEMICOLON'
        p[0] = Assign(p[2], p[5], None, p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_assignment_delay_nodelay(self, p):
        'assignment : ASSIGN delay lvalue EQUALS rvalue SEMICOLON'
        p[0] = Assign(p[3], p[5], p[2], None, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_assignment_delay_delay(self, p):
        'assignment : ASSIGN delay lvalue EQUALS delay rvalue SEMICOLON'
        p[0] = Assign(p[3], p[6], p[2], p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_lpartselect_lpointer(self, p):
        'lpartselect : pointer LBRACKET expression COLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_lpartselect_lpointer_plus(self, p):
        'lpartselect : pointer LBRACKET expression PLUSCOLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], Plus(p[3], p[5]), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_lpartselect_lpointer_minus(self, p):
        'lpartselect : pointer LBRACKET expression MINUSCOLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], Minus(p[3], p[5]), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_lpartselect(self, p):
        'lpartselect : identifier LBRACKET expression COLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_lpartselect_plus(self, p):
        'lpartselect : identifier LBRACKET expression PLUSCOLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], Plus(p[3], p[5]), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_lpartselect_minus(self, p):
        'lpartselect : identifier LBRACKET expression MINUSCOLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], Minus(p[3], p[5]), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_lpointer(self, p):
        'lpointer : pointer'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_lconcat(self, p):
        'lconcat : LBRACE lconcatlist RBRACE'
        p[0] = LConcat(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_lconcatlist(self, p):
        'lconcatlist : lconcatlist COMMA lconcat_one'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_lconcatlist_one(self, p):
        'lconcatlist : lconcat_one'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_lconcat_one_identifier(self, p):
        'lconcat_one : identifier'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_lconcat_one_lpartselect(self, p):
        'lconcat_one : lpartselect'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_lconcat_one_lpointer(self, p):
        'lconcat_one : lpointer'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_lconcat_one_lconcat(self, p):
        'lconcat_one : lconcat'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_lvalue_partselect(self, p):
        'lvalue : lpartselect'
        p[0] = Lvalue(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_lvalue_pointer(self, p):
        'lvalue : lpointer'
        p[0] = Lvalue(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_lvalue_concat(self, p):
        'lvalue : lconcat'
        p[0] = Lvalue(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_lvalue_one(self, p):
        'lvalue : identifier'
        p[0] = Lvalue(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_rvalue(self, p):
        'rvalue : expression'
        p[0] = Rvalue(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 1 (Highest Priority)
    def p_expression_uminus(self, p):
        'expression : MINUS expression %prec UMINUS'
        p[0] = Uminus(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_uplus(self, p):
        'expression : PLUS expression %prec UPLUS'
        p[0] = p[2]
        p.set_lineno(0, p.lineno(1))

    def p_expression_ulnot(self, p):
        'expression : LNOT expression %prec ULNOT'
        p[0] = Ulnot(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_unot(self, p):
        'expression : NOT expression %prec UNOT'
        p[0] = Unot(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_uand(self, p):
        'expression : AND expression %prec UAND'
        p[0] = Uand(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_unand(self, p):
        'expression : NAND expression %prec UNAND'
        p[0] = Unand(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_unor(self, p):
        'expression : NOR expression %prec UNOR'
        p[0] = Unor(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_uor(self, p):
        'expression : OR expression %prec UOR'
        p[0] = Uor(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_uxor(self, p):
        'expression : XOR expression %prec UXOR'
        p[0] = Uxor(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_uxnor(self, p):
        'expression : XNOR expression %prec UXNOR'
        p[0] = Uxnor(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 2
    def p_expression_power(self, p):
        'expression : expression POWER expression'
        p[0] = Power(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 3
    def p_expression_times(self, p):
        'expression : expression TIMES expression'
        p[0] = Times(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_div(self, p):
        'expression : expression DIVIDE expression'
        p[0] = Divide(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_mod(self, p):
        'expression : expression MOD expression'
        p[0] = Mod(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 4
    def p_expression_plus(self, p):
        'expression : expression PLUS expression'
        p[0] = Plus(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_minus(self, p):
        'expression : expression MINUS expression'
        p[0] = Minus(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 5
    def p_expression_sll(self, p):
        'expression : expression LSHIFT expression'
        p[0] = Sll(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_srl(self, p):
        'expression : expression RSHIFT expression'
        p[0] = Srl(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_sla(self, p):
        'expression : expression LSHIFTA expression'
        p[0] = Sla(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_sra(self, p):
        'expression : expression RSHIFTA expression'
        p[0] = Sra(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 6
    def p_expression_lessthan(self, p):
        'expression : expression LT expression'
        p[0] = LessThan(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_greaterthan(self, p):
        'expression : expression GT expression'
        p[0] = GreaterThan(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_lesseq(self, p):
        'expression : expression LE expression'
        p[0] = LessEq(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_greatereq(self, p):
        'expression : expression GE expression'
        p[0] = GreaterEq(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 7
    def p_expression_eq(self, p):
        'expression : expression EQ expression'
        p[0] = Eq(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_noteq(self, p):
        'expression : expression NE expression'
        p[0] = NotEq(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_eql(self, p):
        'expression : expression EQL expression'
        p[0] = Eql(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_noteql(self, p):
        'expression : expression NEL expression'
        p[0] = NotEql(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 8
    def p_expression_And(self, p):
        'expression : expression AND expression'
        p[0] = And(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_Xor(self, p):
        'expression : expression XOR expression'
        p[0] = Xor(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_Xnor(self, p):
        'expression : expression XNOR expression'
        p[0] = Xnor(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 9
    def p_expression_Or(self, p):
        'expression : expression OR expression'
        p[0] = Or(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 10
    def p_expression_land(self, p):
        'expression : expression LAND expression'
        p[0] = Land(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 11
    def p_expression_lor(self, p):
        'expression : expression LOR expression'
        p[0] = Lor(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 12
    def p_expression_cond(self, p):
        'expression : expression COND expression COLON expression'
        p[0] = Cond(p[1], p[3], p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_expression_expr(self, p):
        'expression : LPAREN expression RPAREN'
        p[0] = p[2]
        p.set_lineno(0, p.lineno(2))

    # --------------------------------------------------------------------------
    def p_expression_concat(self, p):
        'expression : concat'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_expression_repeat(self, p):
        'expression : repeat'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_expression_partselect(self, p):
        'expression : partselect'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_expression_pointer(self, p):
        'expression : pointer'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_expression_functioncall(self, p):
        'expression : functioncall'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_expression_systemcall(self, p):
        'expression : systemcall'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_expression_id(self, p):
        'expression : identifier'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_expression_const(self, p):
        'expression : const_expression'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_concat(self, p):
        'concat : LBRACE concatlist RBRACE'
        p[0] = Concat(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_concatlist(self, p):
        'concatlist : concatlist COMMA expression'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_concatlist_one(self, p):
        'concatlist : expression'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_repeat(self, p):
        'repeat : LBRACE expression concat RBRACE'
        p[0] = Repeat(p[3], p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_partselect(self, p):
        'partselect : identifier LBRACKET expression COLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_partselect_plus(self, p):
        'partselect : identifier LBRACKET expression PLUSCOLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], Plus(
            p[3], p[5], lineno=p.lineno(1)), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_partselect_minus(self, p):
        'partselect : identifier LBRACKET expression MINUSCOLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], Minus(
            p[3], p[5], lineno=p.lineno(1)), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_partselect_pointer(self, p):
        'partselect : pointer LBRACKET expression COLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_partselect_pointer_plus(self, p):
        'partselect : pointer LBRACKET expression PLUSCOLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], Plus(
            p[3], p[5], lineno=p.lineno(1)), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_partselect_pointer_minus(self, p):
        'partselect : pointer LBRACKET expression MINUSCOLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], Minus(
            p[3], p[5], lineno=p.lineno(1)), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_pointer(self, p):
        'pointer : identifier LBRACKET expression RBRACKET'
        p[0] = Pointer(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_pointer_pointer(self, p):
        'pointer : pointer LBRACKET expression RBRACKET'
        p[0] = Pointer(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_const_expression_intnum(self, p):
        'const_expression : intnumber'
        p[0] = IntConst(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_const_expression_floatnum(self, p):
        'const_expression : floatnumber'
        p[0] = FloatConst(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_const_expression_stringliteral(self, p):
        'const_expression : stringliteral'
        p[0] = StringConst(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_floatnumber(self, p):
        'floatnumber : FLOATNUMBER'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_intnumber(self, p):
        """intnumber : INTNUMBER_DEC
        | SIGNED_INTNUMBER_DEC
        | INTNUMBER_BIN
        | SIGNED_INTNUMBER_BIN
        | INTNUMBER_OCT
        | SIGNED_INTNUMBER_OCT
        | INTNUMBER_HEX
        | SIGNED_INTNUMBER_HEX
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # String Literal
    def p_stringliteral(self, p):
        'stringliteral : STRING_LITERAL'
        p[0] = p[1][1:-1]  # strip \" and \"
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Always
    def p_always(self, p):
        'always : ALWAYS senslist always_statement'
        p[0] = Always(p[2], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_always_ff(self, p):
        'always_ff : ALWAYS_FF senslist always_statement'
        p[0] = AlwaysFF(p[2], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_always_comb(self, p):
        'always_comb : ALWAYS_COMB senslist always_statement'
        p[0] = AlwaysComb(p[2], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_always_latch(self, p):
        'always_latch : ALWAYS_LATCH senslist always_statement'
        p[0] = AlwaysLatch(p[2], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_sens_egde_paren(self, p):
        'senslist : AT LPAREN edgesigs RPAREN'
        p[0] = SensList(p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_posedgesig(self, p):
        'edgesig : POSEDGE edgesig_base'
        p[0] = Sens(p[2], 'posedge', lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_negedgesig(self, p):
        'edgesig : NEGEDGE edgesig_base'
        p[0] = Sens(p[2], 'negedge', lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_edgesig_base_identifier(self, p):
        'edgesig_base : identifier'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_edgesig_base_pointer(self, p):
        'edgesig_base : pointer'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_edgesigs(self, p):
        'edgesigs : edgesigs SENS_OR edgesig'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_edgesigs_comma(self, p):
        'edgesigs : edgesigs COMMA edgesig'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_edgesigs_one(self, p):
        'edgesigs : edgesig'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_sens_empty(self, p):
        'senslist : empty'
        p[0] = SensList(
            (Sens(None, 'all', lineno=p.lineno(1)),), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_sens_level(self, p):
        'senslist : AT levelsig'
        p[0] = SensList((p[2],), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_sens_level_paren(self, p):
        'senslist : AT LPAREN levelsigs RPAREN'
        p[0] = SensList(p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_levelsig(self, p):
        'levelsig : levelsig_base'
        p[0] = Sens(p[1], 'level', lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_levelsig_base_identifier(self, p):
        'levelsig_base : identifier'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_levelsig_base_pointer(self, p):
        'levelsig_base : pointer'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_levelsig_base_partselect(self, p):
        'levelsig_base : partselect'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_levelsigs(self, p):
        'levelsigs : levelsigs SENS_OR levelsig'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_levelsigs_comma(self, p):
        'levelsigs : levelsigs COMMA levelsig'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_levelsigs_one(self, p):
        'levelsigs : levelsig'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_sens_all(self, p):
        'senslist : AT TIMES'
        p[0] = SensList(
            (Sens(None, 'all', lineno=p.lineno(1)),), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_sens_all_paren(self, p):
        'senslist : AT LPAREN TIMES RPAREN'
        p[0] = SensList((Sens(None, 'all', lineno=p.lineno(1)),), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_basic_statement(self, p):
        """basic_statement : if_statement
        | case_statement
        | casex_statement
        | casez_statement
        | unique_case_statement
        | for_statement
        | while_statement
        | event_statement
        | wait_statement
        | forever_statement
        | block
        | namedblock
        | parallelblock
        | blocking_substitution
        | nonblocking_substitution
        | single_statement
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_always_statement(self, p):
        'always_statement : basic_statement'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_blocking_substitution(self, p):
        'blocking_substitution : blocking_substitution_base SEMICOLON'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_blocking_substitution_base(self, p):
        'blocking_substitution_base : lvalue EQUALS rvalue'
        p[0] = BlockingSubstitution(p[1], p[3], None, None, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(2))

    def p_blocking_substitution_base_nodelay_delay(self, p):
        'blocking_substitution_base : lvalue EQUALS delay rvalue'
        p[0] = BlockingSubstitution(p[1], p[4], None, p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(2))

    def p_blocking_substitution_base_delay_nodelay(self, p):
        'blocking_substitution_base : delay lvalue EQUALS rvalue'
        p[0] = BlockingSubstitution(p[2], p[4], p[1], None, lineno=p.lineno(2))
        p.set_lineno(0, p.lineno(2))

    def p_blocking_substitution_base_delay_delay(self, p):
        'blocking_substitution_base : delay lvalue EQUALS delay rvalue'
        p[0] = BlockingSubstitution(p[2], p[5], p[1], p[4], lineno=p.lineno(2))
        p.set_lineno(0, p.lineno(2))

    def p_nonblocking_substitution(self, p):
        'nonblocking_substitution : lvalue LE rvalue SEMICOLON'
        p[0] = NonblockingSubstitution(p[1], p[3], None, None, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(2))

    def p_nonblocking_substitution_nodelay_delay(self, p):
        'nonblocking_substitution : lvalue LE delay rvalue SEMICOLON'
        p[0] = NonblockingSubstitution(p[1], p[4], None, p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(2))

    def p_nonblocking_substitution_delay_nodelay(self, p):
        'nonblocking_substitution : delay lvalue LE rvalue SEMICOLON'
        p[0] = NonblockingSubstitution(p[2], p[4], p[1], None, lineno=p.lineno(2))
        p.set_lineno(0, p.lineno(2))

    def p_nonblocking_substitution_delay_delay(self, p):
        'nonblocking_substitution : delay lvalue LE delay rvalue SEMICOLON'
        p[0] = NonblockingSubstitution(p[2], p[5], p[1], p[4], lineno=p.lineno(2))
        p.set_lineno(0, p.lineno(2))

    # --------------------------------------------------------------------------
    def p_substitution_operator_plusequals(self, p):
        'substitution_operator : lvalue PLUSEQUALS rvalue'
        p[0] = PlusEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_minusequals(self, p):
        'substitution_operator : lvalue MINUSEQUALS rvalue'
        p[0] = MinusEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_timesequals(self, p):
        'substitution_operator : lvalue TIMESEQUALS rvalue'
        p[0] = TimesEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_divideequals(self, p):
        'substitution_operator : lvalue DIVIDEEQUALS rvalue'
        p[0] = DivideEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_modequals(self, p):
        'substitution_operator : lvalue MODEQUALS rvalue'
        p[0] = ModEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_orequals(self, p):
        'substitution_operator : lvalue OREQUALS rvalue'
        p[0] = OrEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_andequals(self, p):
        'substitution_operator : lvalue ANDEQUALS rvalue'
        p[0] = AndEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_xorequals(self, p):
        'substitution_operator : lvalue XOREQUALS rvalue'
        p[0] = XorEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_slaequals(self, p):
        'substitution_operator : lvalue LSHIFTAEQUALS rvalue'
        p[0] = SlaEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_sraequals(self, p):
        'substitution_operator : lvalue RSHIFTAEQUALS rvalue'
        p[0] = SraEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_sllequals(self, p):
        'substitution_operator : lvalue LSHIFTEQUALS rvalue'
        p[0] = SllEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_srlequals(self, p):
        'substitution_operator : lvalue RSHIFTEQUALS rvalue'
        p[0] = SrlEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_increment(self, p):
        'substitution_operator : lvalue INCREMENT'
        p[0] = Increment(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_decrement(self, p):
        'substitution_operator : lvalue DECREMENT'
        p[0] = Decrement(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_delay(self, p):
        'delay : DELAY LPAREN expression RPAREN'
        p[0] = DelayStatement(p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_delay_identifier(self, p):
        'delay : DELAY identifier'
        p[0] = DelayStatement(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_delay_intnumber(self, p):
        'delay : DELAY intnumber'
        p[0] = DelayStatement(
            IntConst(p[2], lineno=p.lineno(1)), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_delay_floatnumber(self, p):
        'delay : DELAY floatnumber'
        p[0] = DelayStatement(FloatConst(
            p[2], lineno=p.lineno(1)), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_block(self, p):
        'block : BEGIN block_statements END'
        p[0] = Block(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_block_empty(self, p):
        'block : BEGIN END'
        p[0] = Block((), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_block_statements(self, p):
        'block_statements : block_statements block_statement'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_block_statements_one(self, p):
        'block_statements : block_statement'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_block_statement(self, p):
        'block_statement : basic_statement'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_namedblock(self, p):
        'namedblock : BEGIN COLON ID namedblock_statements END'
        p[0] = Block(p[4], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_namedblock_empty(self, p):
        'namedblock : BEGIN COLON ID END'
        p[0] = Block((), p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_namedblock_statements(self, p):
        'namedblock_statements : namedblock_statements namedblock_statement'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_namedblock_statements_one(self, p):
        'namedblock_statements : namedblock_statement'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_namedblock_statement(self, p):
        """namedblock_statement : basic_statement
        | decl
        | timedecl
        | realdecl
        | realtimedecl
        | shortintdecl
        | intdecl
        | longintdecl
        | bytedecl
        | bitdecl
        | shortrealdecl
        | parameterdecl
        | localparamdecl
        """
        if isinstance(p[1], Decl):
            for r in p[1].list:
                if (not isinstance(r, Reg) and not isinstance(r, Wire) and
                    not isinstance(r, Integer) and not isinstance(r, Real) and
                        not isinstance(r, Parameter) and not isinstance(r, Localparam)):
                    raise ParseError("Syntax Error")
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_parallelblock(self, p):
        'parallelblock : FORK block_statements JOIN'
        p[0] = ParallelBlock(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_parallelblock_empty(self, p):
        'parallelblock : FORK JOIN'
        p[0] = ParallelBlock((), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_if_statement(self, p):
        'if_statement : IF LPAREN cond RPAREN true_statement ELSE else_statement'
        p[0] = IfStatement(p[3], p[5], p[7], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_if_statement_woelse(self, p):
        'if_statement : IF LPAREN cond RPAREN true_statement'
        p[0] = IfStatement(p[3], p[5], None, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_if_statement_delay(self, p):
        'if_statement : delay IF LPAREN cond RPAREN true_statement ELSE else_statement'
        p[0] = IfStatement(p[4], p[6], p[8], lineno=p.lineno(2))
        p.set_lineno(0, p.lineno(2))

    def p_if_statement_woelse_delay(self, p):
        'if_statement : delay IF LPAREN cond RPAREN true_statement'
        p[0] = IfStatement(p[4], p[6], None, lineno=p.lineno(2))
        p.set_lineno(0, p.lineno(2))

    def p_cond(self, p):
        'cond : expression'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_ifcontent_statement(self, p):
        'ifcontent_statement : basic_statement'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_true_statement(self, p):
        'true_statement : ifcontent_statement'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_else_statement(self, p):
        'else_statement : ifcontent_statement'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_for_statement(self, p):
        'for_statement : FOR LPAREN forpre forcond forpost RPAREN forcontent_statement'
        p[0] = ForStatement(p[3], p[4], p[5], p[7], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_forpre(self, p):
        'forpre : blocking_substitution'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_forpre_empty(self, p):
        'forpre : SEMICOLON'
        p[0] = None
        p.set_lineno(0, p.lineno(1))

    def p_forcond(self, p):
        'forcond : cond SEMICOLON'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_forcond_empty(self, p):
        'forcond : SEMICOLON'
        p[0] = None
        p.set_lineno(0, p.lineno(1))

    def p_forpost(self, p):
        'forpost : blocking_substitution_base'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_forpost_empty(self, p):
        'forpost : empty'
        p[0] = None

    def p_forcontent_statement(self, p):
        'forcontent_statement : basic_statement'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_while_statement(self, p):
        'while_statement : WHILE LPAREN cond RPAREN whilecontent_statement'
        p[0] = WhileStatement(p[3], p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_whilecontent_statement(self, p):
        'whilecontent_statement : basic_statement'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_case_statement(self, p):
        'case_statement : CASE LPAREN case_comp RPAREN casecontent_statements ENDCASE'
        p[0] = CaseStatement(p[3], p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_casex_statement(self, p):
        'casex_statement : CASEX LPAREN case_comp RPAREN casecontent_statements ENDCASE'
        p[0] = CasexStatement(p[3], p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_casez_statement(self, p):
        'casez_statement : CASEZ LPAREN case_comp RPAREN casecontent_statements ENDCASE'
        p[0] = CasezStatement(p[3], p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_unique_case_statement(self, p):
        'unique_case_statement : UNIQUE CASE LPAREN case_comp RPAREN casecontent_statements ENDCASE'
        p[0] = UniqueCaseStatement(p[3], p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_case_comp(self, p):
        'case_comp : expression'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_casecontent_statements(self, p):
        'casecontent_statements : casecontent_statements casecontent_statement'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_casecontent_statements_one(self, p):
        'casecontent_statements : casecontent_statement'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_casecontent_statement(self, p):
        'casecontent_statement : casecontent_condition COLON basic_statement'
        p[0] = Case(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_casecontent_condition_single(self, p):
        'casecontent_condition : casecontent_condition COMMA expression'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_casecontent_condition_one(self, p):
        'casecontent_condition : expression'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_casecontent_statement_default(self, p):
        'casecontent_statement : DEFAULT COLON basic_statement'
        p[0] = Case(None, p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_initial(self, p):
        'initial : INITIAL initial_statement'
        p[0] = Initial(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_initial_statement(self, p):
        'initial_statement : basic_statement'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_event_statement(self, p):
        'event_statement : senslist SEMICOLON'
        p[0] = EventStatement(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_wait_statement(self, p):
        'wait_statement : WAIT LPAREN cond RPAREN waitcontent_statement'
        p[0] = WaitStatement(p[3], p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_waitcontent_statement(self, p):
        'waitcontent_statement : basic_statement'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_waitcontent_statement_empty(self, p):
        'waitcontent_statement : SEMICOLON'
        p[0] = None
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_forever_statement(self, p):
        'forever_statement : FOREVER basic_statement'
        p[0] = ForeverStatement(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_instance(self, p):
        'instance : ID parameterlist instance_bodylist SEMICOLON'
        instancelist = []
        for instance_name, instance_ports, instance_array in p[3]:
            instancelist.append(Instance(p[1], instance_name, instance_ports,
                                         p[2], instance_array, lineno=p.lineno(1)))
        p[0] = InstanceList(p[1], p[2], tuple(instancelist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_or(self, p):
        'instance : SENS_OR parameterlist instance_bodylist SEMICOLON'
        instancelist = []
        for instance_name, instance_ports, instance_array in p[3]:
            instancelist.append(Instance(p[1], instance_name, instance_ports,
                                         p[2], instance_array, lineno=p.lineno(1)))
        p[0] = InstanceList(p[1], p[2], tuple(instancelist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_noparameterlist(self, p):
        'instance : ID instance_bodylist SEMICOLON'
        instancelist = []
        for instance_name, instance_ports, instance_array in p[2]:
            instancelist.append(Instance(p[1], instance_name, instance_ports,
                                         (), instance_array, lineno=p.lineno(1)))
        p[0] = InstanceList(p[1], (), tuple(instancelist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_or_noparameterlist(self, p):
        'instance : SENS_OR instance_bodylist SEMICOLON'
        instancelist = []
        for instance_name, instance_ports, instance_array in p[2]:
            instancelist.append(Instance(p[1], instance_name, instance_ports,
                                         (), instance_array, lineno=p.lineno(1)))
        p[0] = InstanceList(p[1], (), tuple(instancelist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_noname(self, p):
        'instance : ID instance_bodylist_noname SEMICOLON'
        instancelist = []
        for instance_name, instance_ports, instance_array in p[2]:
            instancelist.append(Instance(p[1], instance_name, instance_ports,
                                         (), instance_array, lineno=p.lineno(1)))
        p[0] = InstanceList(p[1], (), tuple(instancelist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_or_noname(self, p):
        'instance : SENS_OR instance_bodylist_noname SEMICOLON'
        instancelist = []
        for instance_name, instance_ports, instance_array in p[2]:
            instancelist.append(Instance(p[1], instance_name, instance_ports,
                                         (), instance_array, lineno=p.lineno(1)))
        p[0] = InstanceList(p[1], (), tuple(instancelist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_bodylist(self, p):
        'instance_bodylist : instance_bodylist COMMA instance_body'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_bodylist_one(self, p):
        'instance_bodylist : instance_body'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_body(self, p):
        'instance_body : ID LPAREN instance_ports RPAREN'
        p[0] = (p[1], p[3], None)
        p.set_lineno(0, p.lineno(1))

    def p_instance_body_array(self, p):
        'instance_body : ID width LPAREN instance_ports RPAREN'
        p[0] = (p[1], p[4], p[2])
        p.set_lineno(0, p.lineno(1))

    def p_instance_bodylist_noname(self, p):
        'instance_bodylist_noname : instance_bodylist_noname COMMA instance_body_noname'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_bodylist_one_noname(self, p):
        'instance_bodylist_noname : instance_body_noname'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_body_noname(self, p):
        'instance_body_noname : LPAREN instance_ports RPAREN'
        p[0] = ('', p[2], None)
        p.set_lineno(0, p.lineno(1))

    def p_parameterlist(self, p):
        'parameterlist : DELAY LPAREN param_args RPAREN'
        p[0] = p[3]
        p.set_lineno(0, p.lineno(1))

    def p_parameterlist_noname(self, p):
        'parameterlist : DELAY LPAREN param_args_noname RPAREN'
        p[0] = p[3]
        p.set_lineno(0, p.lineno(1))

    def p_param_args_noname(self, p):
        'param_args_noname : param_args_noname COMMA param_arg_noname'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_param_args_noname_one(self, p):
        'param_args_noname : param_arg_noname'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_param_args(self, p):
        'param_args : param_args COMMA param_arg'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_param_args_one(self, p):
        'param_args : param_arg'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_param_args_empty(self, p):
        'param_args : empty'
        p[0] = ()

    def p_param_arg_noname_exp(self, p):
        'param_arg_noname : expression'
        p[0] = ParamArg(None, p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_param_arg_exp(self, p):
        'param_arg : DOT ID LPAREN expression RPAREN'
        p[0] = ParamArg(p[2], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_ports(self, p):
        """instance_ports : instance_ports_list
        | instance_ports_arg
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_instance_ports_list(self, p):
        'instance_ports_list : instance_ports_list COMMA instance_port_list'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_ports_list_one(self, p):
        'instance_ports_list : instance_port_list'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_ports_list_empty(self, p):
        'instance_ports_list : empty'
        p[0] = ()
        p.set_lineno(0, p.lineno(1))

    def p_instance_port_list(self, p):
        'instance_port_list : expression'
        p[0] = PortArg(None, p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_ports_arg(self, p):
        'instance_ports_arg : instance_ports_arg COMMA instance_port_arg'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_ports_arg_one(self, p):
        'instance_ports_arg : instance_port_arg'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_port_arg(self, p):
        'instance_port_arg : DOT ID LPAREN identifier RPAREN'
        p[0] = PortArg(p[2], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_port_arg_exp(self, p):
        'instance_port_arg : DOT ID LPAREN expression RPAREN'
        p[0] = PortArg(p[2], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_port_arg_none(self, p):
        'instance_port_arg : DOT ID LPAREN RPAREN'
        p[0] = PortArg(p[2], None, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_genvardecl(self, p):
        'genvardecl : GENVAR genvarlist SEMICOLON'
        p[0] = Decl(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_genvarlist(self, p):
        'genvarlist : genvarlist COMMA genvar'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_genvarlist_one(self, p):
        'genvarlist : genvar'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_genvar(self, p):
        'genvar : ID'
        p[0] = Genvar(name=p[1],
                      width=Width(msb=IntConst('31', lineno=p.lineno(1)),
                                  lsb=IntConst('0', lineno=p.lineno(1)),
                                  lineno=p.lineno(1)),
                      lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_generate(self, p):
        'generate : GENERATE generate_items ENDGENERATE'
        p[0] = GenerateStatement(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_generate_items_empty(self, p):
        'generate_items : empty'
        p[0] = ()
        p.set_lineno(0, p.lineno(1))

    def p_generate_items(self, p):
        'generate_items : generate_items generate_item'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_generate_items_one(self, p):
        'generate_items : generate_item'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_generate_item(self, p):
        """generate_item : standard_item
        | generate_if
        | generate_for
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_generate_block(self, p):
        'generate_block : BEGIN generate_items END'
        p[0] = Block(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_generate_named_block(self, p):
        'generate_block : BEGIN COLON ID generate_items END'
        p[0] = Block(p[4], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_generate_if(self, p):
        'generate_if : IF LPAREN cond RPAREN gif_true_item ELSE gif_false_item'
        p[0] = IfStatement(p[3], p[5], p[7], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_generate_if_woelse(self, p):
        'generate_if : IF LPAREN cond RPAREN gif_true_item'
        p[0] = IfStatement(p[3], p[5], None, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_generate_if_true_item(self, p):
        """gif_true_item : generate_item
        | generate_block
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_generate_if_false_item(self, p):
        """gif_false_item : generate_item
        | generate_block
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_generate_for(self, p):
        'generate_for : FOR LPAREN forpre forcond forpost RPAREN generate_forcontent'
        p[0] = ForStatement(p[3], p[4], p[5], p[7], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_generate_forcontent(self, p):
        """generate_forcontent : generate_item
        | generate_block
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_systemcall_noargs(self, p):
        'systemcall : DOLLER ID'
        p[0] = SystemCall(p[2], (), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_systemcall(self, p):
        'systemcall : DOLLER ID LPAREN sysargs RPAREN'
        p[0] = SystemCall(p[2], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_systemcall_signed(self, p):  # for $signed system task
        'systemcall : DOLLER SIGNED LPAREN sysargs RPAREN'
        p[0] = SystemCall(p[2], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_systemcall_unsigned(self, p):  # for $unsigned system task
        'systemcall : DOLLER UNSIGNED LPAREN sysargs RPAREN'
        p[0] = SystemCall(p[2], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_sysargs(self, p):
        'sysargs : sysargs COMMA sysarg'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_sysargs_one(self, p):
        'sysargs : sysarg'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_sysargs_empty(self, p):
        'sysargs : empty'
        p[0] = ()

    def p_sysarg(self, p):
        'sysarg : expression'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_function(self, p):
        'function : FUNCTION width ID SEMICOLON function_statement ENDFUNCTION'
        p[0] = Function(p[3], p[2], p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_function_nowidth(self, p):
        'function : FUNCTION ID SEMICOLON function_statement ENDFUNCTION'
        p[0] = Function(p[2],
                        Width(IntConst('0', lineno=p.lineno(1)),
                              IntConst('0', lineno=p.lineno(1)),
                              lineno=p.lineno(1)),
                        p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_function_integer(self, p):
        'function : FUNCTION INTEGER ID SEMICOLON function_statement ENDFUNCTION'
        p[0] = Function(p[3],
                        Width(IntConst('31', lineno=p.lineno(1)),
                              IntConst('0', lineno=p.lineno(1)),
                              lineno=p.lineno(1)),
                        p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_function_statement(self, p):
        'function_statement : funcvardecls function_calc'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_funcvardecls(self, p):
        'funcvardecls : funcvardecls funcvardecl'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_funcvardecls_one(self, p):
        'funcvardecls : funcvardecl'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_funcvardecl(self, p):
        """funcvardecl : decl
        | integerdecl
        """
        if isinstance(p[1], Decl):
            for r in p[1].list:
                if (not isinstance(r, Input) and not isinstance(r, Reg) and
                        not isinstance(r, Integer)):
                    raise ParseError("Syntax Error")
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_function_calc(self, p):
        """function_calc : blocking_substitution
        | if_statement
        | for_statement
        | while_statement
        | case_statement
        | casex_statement
        | casez_statement
        | block
        | namedblock
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_functioncall(self, p):
        'functioncall : identifier LPAREN func_args RPAREN'
        p[0] = FunctionCall(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_func_args(self, p):
        'func_args : func_args COMMA expression'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_func_args_one(self, p):
        'func_args : expression'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_func_args_empty(self, p):
        'func_args : empty'
        p[0] = ()

    # --------------------------------------------------------------------------
    def p_task(self, p):
        'task : TASK ID SEMICOLON task_statement ENDTASK'
        p[0] = Task(p[2], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_task_statement(self, p):
        'task_statement : taskvardecls task_calc'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_taskvardecls(self, p):
        'taskvardecls : taskvardecls taskvardecl'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_taskvardecls_one(self, p):
        'taskvardecls : taskvardecl'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_taskvardecls_empty(self, p):
        'taskvardecls : empty'
        p[0] = ()

    def p_taskvardecl(self, p):
        """taskvardecl : decl
        | integerdecl
        """
        if isinstance(p[1], Decl):
            for r in p[1].list:
                if (not isinstance(r, Input) and not isinstance(r, Reg) and
                        not isinstance(r, Integer)):
                    raise ParseError("Syntax Error")
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_task_calc(self, p):
        """task_calc : blocking_substitution
        | if_statement
        | for_statement
        | while_statement
        | case_statement
        | casex_statement
        | casez_statement
        | block
        | namedblock
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_identifier(self, p):
        'identifier : ID'
        p[0] = Identifier(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_scope_identifier(self, p):
        'identifier : scope ID'
        p[0] = Identifier(p[2], p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_scope(self, p):
        'scope : identifier DOT'
        scope = () if p[1].scope is None else p[1].scope.labellist
        p[0] = IdentifierScope(
            scope + (IdentifierScopeLabel(p[1].name, lineno=p.lineno(1)),), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_scope_pointer(self, p):
        'scope : pointer DOT'
        scope = () if p[1].var.scope is None else p[1].var.scope.labellist
        p[0] = IdentifierScope(scope + (IdentifierScopeLabel(p[1].var.name,
                                                             p[1].ptr, lineno=p.lineno(1)),), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_disable(self, p):
        'disable : DISABLE ID'
        p[0] = Disable(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_single_statement_substitution_operator(self, p):
        'single_statement : substitution_operator SEMICOLON'
        p[0] = SingleStatement(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_single_statement_delay(self, p):
        'single_statement : DELAY expression SEMICOLON'
        p[0] = SingleStatement(DelayStatement([2], lineno=p.lineno(1)), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_single_statement_systemcall(self, p):
        'single_statement : systemcall SEMICOLON'
        p[0] = SingleStatement(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_single_statement_disable(self, p):
        'single_statement : disable SEMICOLON'
        p[0] = SingleStatement(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # fix me: to support task-call-statement
    # def p_single_statement_taskcall(self, p):
    #    'single_statement : functioncall SEMICOLON'
    #    p[0] = SingleStatement(p[1], lineno=p.lineno(1))
    #    p.set_lineno(0, p.lineno(1))

    # def p_single_statement_taskcall_empty(self, p):
    #    'single_statement : taskcall SEMICOLON'
    #    p[0] = SingleStatement(p[1], lineno=p.lineno(1))
    #    p.set_lineno(0, p.lineno(1))

    # def p_taskcall_empty(self, p):
    #    'taskcall : identifier'
    #    p[0] = FunctionCall(p[1], (), lineno=p.lineno(1))
    #    p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_interface(self, p):
        'interface : INTERFACE interfacename paramlist portlist interface_items ENDINTERFACE'
        p[0] = Interface(name=p[2], paramlist=p[3], portlist=p[4], items=p[5],
                         lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))
        p[0].end_lineno = p.lineno(6)

    def p_interfacename(self, p):
        'interfacename : ID'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_interface_items(self, p):
        'interface_items : interface_items interface_item'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_interface_items_one(self, p):
        'interface_items : interface_item'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_interface_item(self, p):
        """interface_item : decl
        | integerdecl
        | timedecl
        | realdecl
        | realtimedecl
        | shortintdecl
        | intdecl
        | longintdecl
        | bytedecl
        | bitdecl
        | shortrealdecl
        | modport
        | pragma
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_modport(self, p):
        'modport : MODPORT modportname LPAREN ioports RPAREN SEMICOLON'
        p[0] = Modport(p[2], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_modportname(self, p):
        'modportname : ID'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_struct(self, p):
        'struct : struct_base SEMICOLON'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_struct_base(self, p):
        'struct_base : STRUCT LBRACE struct_items RBRACE structname'
        p[0] = Struct(p[5], p[3], packed=False, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_struct_base_packed(self, p):
        'struct_base : STRUCT PACKED LBRACE struct_items RBRACE structname'
        p[0] = Struct(p[6], p[4], packed=True, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_structname(self, p):
        'structname : ID'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_struct_items(self, p):
        'struct_items : struct_items struct_item'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_struct_items_one(self, p):
        'struct_items : struct_item'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_struct_item(self, p):
        """struct_item : decl
        | integerdecl
        | timedecl
        | realdecl
        | realtimedecl
        | shortintdecl
        | intdecl
        | longintdecl
        | bytedecl
        | bitdecl
        | shortrealdecl
        | pragma
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_union(self, p):
        'union : union_base SEMICOLON'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_union_base(self, p):
        'union_base : UNION LBRACE union_items RBRACE unionname'
        p[0] = Union(p[5], p[3], packed=False, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_union_base_packed(self, p):
        'union_base : UNION PACKED LBRACE union_items RBRACE unionname'
        p[0] = Union(p[6], p[4], packed=True, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_unionname(self, p):
        'unionname : ID'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_union_items(self, p):
        'union_items : union_items union_item'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_union_items_one(self, p):
        'union_items : union_item'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_union_item(self, p):
        """union_item : decl
        | integerdecl
        | timedecl
        | realdecl
        | realtimedecl
        | shortintdecl
        | intdecl
        | longintdecl
        | bytedecl
        | bitdecl
        | shortrealdecl
        | pragma
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_enum(self, p):
        'enum : enum_base SEMICOLON'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_enum_base(self, p):
        'enum_base : ENUM LBRACE enumlist RBRACE enumname'
        type = 'INT'
        width = None
        p[0] = Enum(p[5], p[3], packed=False, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_enum_base_sigtype(self, p):
        'enum_base : ENUM sigtype LBRACE enumlist RBRACE enumname'
        type = p[1]
        width = None
        p[0] = Enum(p[5], p[3], packed=False, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_enum_base_sigtype_width(self, p):
        'enum_base : ENUM sigtype width LBRACE enumlist RBRACE enumname'
        type = p[1]
        width = p[2]
        p[0] = Enum(p[5], p[3], packed=False, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_enumname(self, p):
        'enumname : ID'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_enumlist_items(self, p):
        'enumlist : enum_items'
        p[0] = Enumlist(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_enumlist_length(self, p):
        'enumlist : ID LBRACKET expression RBRACKET'
        p[0] = Enumlist(name=p[1], length=p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_enumlist_length_value(self, p):
        'enumlist : ID LBRACKET expression RBRACKET EQUALS expression'
        p[0] = Enumlist(name=p[1], length=p[3], value=p[6], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_enumlist_start_end(self, p):
        'enumlist : ID LBRACKET expression COLON expression RBRACKET'
        p[0] = Enumlist(name=p[1], start=p[3], end=p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_enum_items(self, p):
        'enum_items : enum_items COMMA enum_item'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_enum_items_one(self, p):
        'enum_items : enum_item'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_enum_item(self, p):
        'enum_item : ID'
        p[0] = (p[1], None)  # identifier, value
        p.set_lineno(0, p.lineno(1))

    def p_enum_item_value(self, p):
        'enum_item : ID EQUALS rvalue'
        p[0] = (p[1], p[3])  # identifier, value
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_typedef(self, p):
        'typedef : TYPEDEF sigtypes ID SEMICOLON'
        p[0] = TypeDef(p[3], p[2], width=None, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_typedef_pdims_width(self, p):
        'typedef : TYPEDEF sigtypes pdims_width ID SEMICOLON'
        pdims, width = p[3]
        p[0] = TypeDef(p[4], p[2], width=width, pdims=pdims, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_typedef_pdims_width_udims(self, p):
        'typedef : TYPEDEF sigtypes pdims_width ID udims SEMICOLON'
        pdims, width = p[3]
        p[0] = TypeDef(p[4], p[2], width=width, pdims=pdims, udims=p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_typedef_udims(self, p):
        'typedef : TYPEDEF sigtypes ID udims SEMICOLON'
        p[0] = TypeDef(p[3], p[2], width=None, udims=p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_typedef_struct(self, p):
        'typedef : TYPEDEF struct_base SEMICOLON'
        p[0] = TypeDef(p[2].name, p[2], width=None, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_typedef_struct_udims(self, p):
        'typedef : TYPEDEF struct_base udims SEMICOLON'
        p[0] = TypeDef(p[2].name, p[2], width=None, udims=p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_typedef_union(self, p):
        'typedef : TYPEDEF union_base SEMICOLON'
        p[0] = TypeDef(p[2].name, p[2], width=None, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_typedef_union_udims(self, p):
        'typedef : TYPEDEF union_base udims SEMICOLON'
        p[0] = TypeDef(p[2].name, p[2], width=None, udims=p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_typedef_enum(self, p):
        'typedef : TYPEDEF enum_base SEMICOLON'
        p[0] = TypeDef(p[2].name, p[2], width=None, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_typedef_enum_udims(self, p):
        'typedef : TYPEDEF enum_base udims SEMICOLON'
        p[0] = TypeDef(p[2].name, p[2], width=None, udims=p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_empty(self, p):
        'empty : '
        pass

    # --------------------------------------------------------------------------
    def p_error(self, p):
        print("Syntax error")
        if p:
            self._parse_error(
                'before: %s' % p.value,
                self._coord(p.lineno))
        else:
            self._parse_error('At end of input', '')


class VerilogCodeParser(object):

    def __init__(self, filelist, preprocess_output='preprocess.output',
                 preprocess_include=None,
                 preprocess_define=None,
                 outputdir=".",
                 debug=True
                 ):
        self.preprocess_output = preprocess_output
        self.directives = ()
        self.preprocessor = VerilogPreprocessor(filelist, preprocess_output,
                                                preprocess_include,
                                                preprocess_define)
        self.parser = VerilogParser(outputdir=outputdir, debug=debug)

    def preprocess(self):
        self.preprocessor.preprocess()
        text = open(self.preprocess_output).read()
        os.remove(self.preprocess_output)
        return text

    def parse(self, preprocess_output='preprocess.output', debug=False):
        text = self.preprocess()
        ast = self.parser.parse(text, debug=debug)
        self.directives = self.parser.get_directives()
        return ast

    def get_directives(self):
        return self.directives


def parse(
    filelist,
    preprocess_include=None,
    preprocess_define=None,
    outputdir=".",
    debug=True
):
    codeparser = VerilogCodeParser(
        filelist,
        preprocess_include=preprocess_include,
        preprocess_define=preprocess_define,
        outputdir=outputdir,
        debug=debug
    )
    ast = codeparser.parse()
    directives = codeparser.get_directives()
    return ast, directives
