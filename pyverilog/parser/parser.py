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
from ply.yacc import yacc

from pyverilog.parser.preprocessor import VerilogPreprocessor
from pyverilog.parser.lexer import VerilogLexer
from pyverilog.parser.ast import *


class VerilogParser(object):
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
        ('right', 'UMINUS', 'UPLUS', 'ULNOT', 'UNOT',
         'UAND', 'UNAND', 'UOR', 'UNOR', 'UXOR', 'UXNOR'),
        ('left', 'SQUOTE'),
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
        coord = self._coord(line, column)
        raise ParseError('%s: %s' % (coord, msg))

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
        """definition : module
        | interface
        | struct
        | union
        | enum
        | typedef
        | pragma
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_pragma_assign(self, p):
        'pragma : LPAREN TIMES _id EQUALS expression TIMES RPAREN'
        p[0] = Pragma(PragmaItem(p[3], p[5], lineno=p.lineno(1)),
                      lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_pragma(self, p):
        'pragma : LPAREN TIMES _id TIMES RPAREN'
        p[0] = Pragma(PragmaItem(p[3], lineno=p.lineno(1)),
                      lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_module(self, p):
        'module : MODULE _id paramlist portlist items ENDMODULE'
        p[0] = Module(name=p[2], paramlist=p[3], portlist=p[4], items=p[5],
                      default_nettype=self.get_default_nettype(), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))
        p[0].end_lineno = p.lineno(6)

    def p_paramlist(self, p):
        'paramlist : SHARP LPAREN params RPAREN'
        p[0] = p[3]
        p.set_lineno(0, p.lineno(1))

    def p_paramlist_empty(self, p):
        'paramlist : empty'
        p[0] = ()

    def p_params(self, p):
        'params : params COMMA param'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_params_one(self, p):
        'params : param'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_param(self, p):
        'param : PARAMETER var_sigtype_or_empty sign_sigtype_or_empty width_or_empty param_substitution_list'
        ptype = None if p[2] == () else p[2]
        signed = None if p[3] == () else p[3]
        width = None if p[4] == () else p[4]
        paramlist = [Parameter(rname, rvalue, width, signed=signed, ptype=ptype, lineno=p.lineno(1))
                     for rname, rvalue in p[5]]
        p[0] = Decl(tuple(paramlist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_portlist(self, p):
        'portlist : LPAREN ioports RPAREN SEMICOLON'
        p[0] = p[2]
        p.set_lineno(0, p.lineno(1))

    def p_portlist_paren_empty(self, p):
        'portlist : LPAREN RPAREN SEMICOLON'
        p[0] = ()
        p.set_lineno(0, p.lineno(1))

    def p_portlist_empty(self, p):
        'portlist : SEMICOLON'
        p[0] = ()
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_ioports(self, p):
        'ioports : ioports COMMA ioport'
        if isinstance(p[1][0], Port) and not isinstance(p[3], Port):
            self._raise_error(p)

        if isinstance(p[1][0], Ioport) and isinstance(p[3], Port):
            t = None
            r = p[1][-1]
            first_type = type(r.first)
            second_type = type(r.second) if r.second is not None else None

            if second_type is not None:
                t = Ioport(first_type(name=p[3].name, width=r.first.width, lineno=p.lineno(3)),
                           second_type(name=p[3].name, width=r.first.width, lineno=p.lineno(3)),
                           lineno=p.lineno(3))

            else:
                t = Ioport(first_type(name=p[3].name, width=r.first.width, lineno=p.lineno(3)),
                           lineno=p.lineno(3))

            p[0] = p[1] + (t,)

        else:
            p[0] = p[1] + (p[3],)

        p.set_lineno(0, p.lineno(1))

    def p_ioports_one(self, p):
        'ioports : ioport'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def create_ioport(self, p, sigtypes, name, width=None, pdims=None, udims=None, lineno=0):
        signed = None
        first = None
        second = None

        self.typecheck_ioport(p, sigtypes)

        sigtypes = list(sigtypes)

        if 'signed' in sigtypes:
            signed = True
            sigtypes.remove('signed')

        elif 'unsigned' in sigtypes:
            signed = False
            sigtypes.remove('unsigned')

        if len(sigtypes) > 2:
            self._raise_error(p)

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
            self._raise_error(p)

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

        elif 'integer' in sigtypes:
            second = Integer(name=name, signed=signed,
                             pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('integer')

        elif 'time' in sigtypes:
            second = Time(name=name, signed=signed,
                          pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('time')

        elif 'real' in sigtypes:
            second = Real(name=name, signed=signed,
                          pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('real')

        elif 'realtime' in sigtypes:
            second = RealTime(name=name, signed=signed,
                              pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('realtime')

        elif 'logic' in sigtypes:
            second = Logic(name=name, width=width, signed=signed,
                           pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('logic')

        elif 'shortint' in sigtypes:
            second = ShortInt(name=name, signed=signed,
                              pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('shortint')

        elif 'int' in sigtypes:
            second = Int(name=name, signed=signed,
                         pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('int')

        elif 'longint' in sigtypes:
            second = LongInt(name=name, signed=signed,
                             pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('longint')

        elif 'byte' in sigtypes:
            second = Byte(name=name, signed=signed,
                          pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('byte')

        elif 'bit' in sigtypes:
            second = Bit(name=name, width=width, signed=signed,
                         pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('bit')

        elif 'shortreal' in sigtypes:
            second = ShortReal(name=name, width=width, signed=signed,
                               pdims=pdims, udims=udims, lineno=lineno)
            sigtypes.remove('shortreal')

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
            self._raise_error(p)

        return Ioport(first, second, lineno=lineno)

    def typecheck_ioport(self, p, sigtypes):
        if len(sigtypes) > 3:
            self._raise_error(p)

        if len(sigtypes) != len(set(sigtypes)):
            self._raise_error(p)

        if 'signed' not in sigtypes and 'unsigned' not in sigtypes and len(sigtypes) > 2:
            self._raise_error(p)

        if 'signed' in sigtypes and len(sigtypes) == 1:
            self._raise_error(p)

        if 'unsigned' in sigtypes and len(sigtypes) == 1:
            self._raise_error(p)

        if 'signed' in sigtypes and 'unsigned' in sigtypes:
            self._raise_error(p)

        # if 'input' not in sigtypes and 'output' not in sigtypes and 'inout' not in sigtypes:
        #     self._raise_error(p)

        if 'input' in sigtypes and 'output' in sigtypes:
            self._raise_error(p)

        if 'inout' in sigtypes and 'output' in sigtypes:
            self._raise_error(p)

        if 'inout' in sigtypes and 'input' in sigtypes:
            self._raise_error(p)

        if 'input' in sigtypes and 'reg' in sigtypes:
            self._raise_error(p)

        if 'inout' in sigtypes and 'reg' in sigtypes:
            self._raise_error(p)

        if 'input' in sigtypes and 'tri' in sigtypes:
            self._raise_error(p)

        if 'output' in sigtypes and 'tri' in sigtypes:
            self._raise_error(p)

    def _separate_sigtypes_id_allow_no_sigtypes(self, p, sigtypes):
        ID = sigtypes[-1]
        sigtypes = sigtypes[:-1]
        if ID in self.lexer.reserved:
            self._raise_error(p)
        return sigtypes, ID

    def _separate_sigtypes_id(self, p, sigtypes):
        ID = sigtypes[-1]
        sigtypes = sigtypes[:-1]
        if len(sigtypes) == 0:
            self._raise_error(p)
        if ID in self.lexer.reserved:
            self._raise_error(p)
        return sigtypes, ID

    def p_ioport(self, p):
        'ioport : sigtypes_id'
        sigtypes, ID = self._separate_sigtypes_id(p, p[1])
        p[0] = self.create_ioport(p, sigtypes, ID, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_ioport_pdims_width(self, p):
        'ioport : sigtypes pdims_width _id'
        pdims, width = p[2]
        p[0] = self.create_ioport(p, p[1], p[3], width=width, pdims=pdims, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_ioport_pdims_width_udims(self, p):
        'ioport : sigtypes pdims_width _id udims'
        pdims, width = p[2]
        p[0] = self.create_ioport(p, p[1], p[3], width=width,
                                  pdims=pdims, udims=p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_ioport_oldstyle(self, p):
        'ioport : _id'
        p[0] = Port(name=p[1], width=None,
                    pdims=None, udims=None, type=None, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_width_vector(self, p):
        'width : LBRACKET expression COLON expression RBRACKET'
        p[0] = Width(p[2], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_width(self, p):
        'width : LBRACKET expression RBRACKET'
        p[0] = Width(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_width_or_empty(self, p):
        'width_or_empty : width'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_width_or_empty_empty(self, p):
        'width_or_empty : empty'
        p[0] = ()

    def _separate_pdims_width(self, p, dims):
        if dims[-1].msb is None:
            self._raise_error(p)
        if dims[-1].lsb is None:
            self._raise_error(p)

        width = Width(dims[-1].msb, dims[-1].lsb, lineno=dims[-1].lineno)

        if len(dims[:-1]) == 0:
            pdims = None
        else:
            pdims = Dims(dims[:-1], lineno=dims[0].lineno)

        return pdims, width

    def p_pdims_width(self, p):
        'pdims_width : dims'
        pdims, width = self._separate_pdims_width(p, p[1])
        p[0] = (pdims, width)
        p.set_lineno(0, p.lineno(1))

    def p_pdims_width_or_empty(self, p):
        'pdims_width_or_empty : pdims_width'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_pdims_width_or_empty_empty(self, p):
        'pdims_width_or_empty : empty'
        p[0] = ()

    def p_udims(self, p):
        'udims : dims'
        p[0] = Dims(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_udims_or_empty(self, p):
        'udims_or_empty : udims'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_udims_or_empty_empty(self, p):
        'udims_or_empty : empty'
        p[0] = ()

    def p_dims(self, p):
        'dims : dims width'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_dims_one(self, p):
        'dims : width'
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
        | parameter_decl
        | localparam_decl
        | decl_assign
        | typedef
        | genvar_decl
        | assignment
        | always
        | always_ff
        | always_comb
        | always_latch
        | initial
        | function
        | task
        | pragma
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def create_decl(self, p, sigtypes, name, width=None, pdims=None, udims=None, lineno=0):
        signed = None
        decls = []

        self.typecheck_decl(p, sigtypes, pdims, udims)

        sigtypes = list(sigtypes)

        if 'signed' in sigtypes:
            signed = True
            sigtypes.remove('signed')

        elif 'unsigned' in sigtypes:
            signed = False
            sigtypes.remove('unsigned')

        if len(sigtypes) > 2:
            self._raise_error(p)

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
            self._raise_error(p)

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

        elif 'integer' in sigtypes:
            decls.append(Integer(name=name,
                                 signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('integer')

        elif 'time' in sigtypes:
            decls.append(Time(name=name,
                              signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('time')

        elif 'real' in sigtypes:
            decls.append(Real(name=name,
                              signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('real')

        elif 'realtime' in sigtypes:
            decls.append(RealTime(name=name,
                                  signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('realtime')

        elif 'supply0' in sigtypes:
            decls.append(Supply(name=name, value=IntConst('0', lineno=lineno),
                                width=width, signed=signed, lineno=lineno))
            sigtypes.remove('supply0')

        elif 'supply1' in sigtypes:
            decls.append(Supply(name=name, value=IntConst('1', lineno=lineno),
                                width=width, signed=signed, lineno=lineno))
            sigtypes.remove('supply1')

        elif 'logic' in sigtypes:
            decls.append(Logic(name=name, width=width,
                               signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('logic')

        elif 'shortint' in sigtypes:
            decls.append(ShortInt(name=name,
                                  signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('shortint')

        elif 'int' in sigtypes:
            decls.append(Int(name=name,
                             signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('int')

        elif 'longloint' in sigtypes:
            decls.append(LongInt(name=name,
                                 signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('longint')

        elif 'byte' in sigtypes:
            decls.append(Byte(name=name,
                              signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('byte')

        elif 'bit' in sigtypes:
            decls.append(Bit(name=name,
                             signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('bit')

        elif 'shortreal' in sigtypes:
            decls.append(ShortReal(name=name,
                                   signed=signed, lineno=lineno, pdims=pdims, udims=udims))
            sigtypes.remove('shortreal')

        if len(sigtypes) > 0:
            if isinstance(sigtypes[0], tuple):
                typename = sigtypes[0][0]
                modportname = sigtypes[0][1]
            else:
                typename = sigtypes[0][0]
                modportname = None
            decls.append(CustomVariable(typename=typename, name=name, modportname=modportname,
                                        width=width, signed=signed,
                                        pdims=pdims, udims=udims, lineno=lineno))
            sigtypes.remove(sigtypes[0])

        if len(sigtypes) > 0:
            self._raise_error(p)

        return decls

    def typecheck_decl(self, p, sigtypes, pdims=None, udims=None):
        if len(sigtypes) > 3:
            self._raise_error(p)

        if len(sigtypes) != len(set(sigtypes)):
            self._raise_error(p)

        if 'signed' not in sigtypes and 'unsigned' not in sigtypes and len(sigtypes) > 2:
            self._raise_error(p)

        if 'signed' in sigtypes and len(sigtypes) == 1:
            self._raise_error(p)

        if 'unsigned' in sigtypes and len(sigtypes) == 1:
            self._raise_error(p)

        if 'signed' in sigtypes and 'unsigned' in sigtypes:
            self._raise_error(p)

        if ('supply0' in sigtypes or 'supply1' in sigtypes) and pdims is not None:
            self._raise_error(p)

        if ('supply0' in sigtypes or 'supply1' in sigtypes) and udims is not None:
            self._raise_error(p)

        if 'input' in sigtypes and 'output' in sigtypes:
            self._raise_error(p)

        if 'inout' in sigtypes and 'output' in sigtypes:
            self._raise_error(p)

        if 'inout' in sigtypes and 'input' in sigtypes:
            self._raise_error(p)

        if 'input' in sigtypes and 'reg' in sigtypes:
            self._raise_error(p)

        if 'inout' in sigtypes and 'reg' in sigtypes:
            self._raise_error(p)

        if 'input' in sigtypes and 'tri' in sigtypes:
            self._raise_error(p)

        if 'output' in sigtypes and 'tri' in sigtypes:
            self._raise_error(p)

    def p_decl_one(self, p):
        'decl : sigtypes_id SEMICOLON'
        sigtypes, ID = self._separate_sigtypes_id(p, p[1])
        decllist = []
        decllist.extend(self.create_decl(p, sigtypes, ID, pdims=None, udims=None,
                                         lineno=p.lineno(1)))
        p[0] = Decl(tuple(decllist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_decl_one_udims(self, p):
        'decl : sigtypes_id udims SEMICOLON'
        sigtypes, ID = self._separate_sigtypes_id(p, p[1])
        decllist = []
        decllist.extend(self.create_decl(p, sigtypes, ID, pdims=None, udims=p[2],
                                         lineno=p.lineno(1)))
        p[0] = Decl(tuple(decllist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_decl_list(self, p):
        'decl : sigtypes_id COMMA declnamelist SEMICOLON'
        sigtypes, ID = self._separate_sigtypes_id(p, p[1])
        decllist = []
        decllist.extend(self.create_decl(p, sigtypes, ID, pdims=None, udims=None,
                                         lineno=p.lineno(1)))
        for rname, rudims in p[3]:
            decllist.extend(self.create_decl(p, sigtypes, rname, pdims=None, udims=rudims,
                                             lineno=p.lineno(1)))
        p[0] = Decl(tuple(decllist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_decl_udims_list(self, p):
        'decl : sigtypes_id udims COMMA declnamelist SEMICOLON'
        sigtypes, ID = self._separate_sigtypes_id(p, p[1])
        decllist = []
        decllist.extend(self.create_decl(p, sigtypes, ID, pdims=None, udims=p[2],
                                         lineno=p.lineno(1)))
        for rname, rudims in p[4]:
            decllist.extend(self.create_decl(p, sigtypes, rname, pdims=None, udims=rudims,
                                             lineno=p.lineno(1)))
        p[0] = Decl(tuple(decllist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_decl_pdims_width(self, p):
        'decl : sigtypes pdims_width declnamelist SEMICOLON'
        decllist = []
        pdims, width = p[2]
        for rname, rudims in p[3]:
            decllist.extend(self.create_decl(p, p[1], rname, width=width, pdims=pdims, udims=rudims,
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
        'declname : _id'
        p[0] = (p[1], None)
        p.set_lineno(0, p.lineno(1))

    def p_declname_udims(self, p):
        'declname : _id udims'
        p[0] = (p[1], p[2])
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_decl_instance_no_param(self, p):
        'decl : sigtypes_id udims_or_empty instance_port_list comma_instance_body_list_or_empty SEMICOLON'
        sigtypes, ID = self._separate_sigtypes_id(p, p[1])
        if len(sigtypes) > 1:
            self._raise_error(p)
        modulename = sigtypes[0]
        instance_param_list = ()
        udims, length = (None, None) if p[2] == () else (p[2].dims[:-1], p[2].dims[-1])
        if isinstance(udims, tuple) and len(udims) > 0:
            self._raise_error(p)
        instance_body = (ID, p[3], length)
        instance_body_list = (instance_body,) + p[4]
        instancelist = []
        for instance_name, instance_port_list, instance_array in instance_body_list:
            instancelist.append(Instance(modulename, instance_name,
                                         instance_param_list, instance_port_list,
                                         instance_array, lineno=p.lineno(1)))
        p[0] = DeclInstances(tuple(instancelist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_decl_instance(self, p):
        'decl : _id instance_param_list instance_body_list SEMICOLON'
        instance_param_list = () if p[2] == () else p[2]
        instancelist = []
        for instance_name, instance_port_list, instance_array in p[3]:
            instancelist.append(Instance(p[1], instance_name,
                                         instance_param_list, instance_port_list,
                                         instance_array, lineno=p.lineno(1)))
        p[0] = DeclInstances(tuple(instancelist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_decl_instance_noname(self, p):
        'decl : _id instance_body_list_noname SEMICOLON'
        instancelist = []
        for instance_name, instance_port_list, instance_array in p[2]:
            instancelist.append(Instance(p[1], instance_name,
                                         (), instance_port_list,
                                         instance_array, lineno=p.lineno(1)))
        p[0] = DeclInstances(tuple(instancelist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_comma_instance_body_list_or_empty(self, p):
        'comma_instance_body_list_or_empty : COMMA instance_body_list'
        p[0] = p[2]
        p.set_lineno(0, p.lineno(1))

    def p_comma_instance_body_list_or_empty_empty(self, p):
        'comma_instance_body_list_or_empty : empty'
        p[0] = ()

    def p_instance_body_list(self, p):
        'instance_body_list : instance_body_list COMMA instance_body'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_body_list_one(self, p):
        'instance_body_list : instance_body'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_body(self, p):
        'instance_body : _id width_or_empty instance_port_list'
        length = None if p[2] == () else p[2]
        p[0] = (p[1], p[3], length)
        p.set_lineno(0, p.lineno(1))

    def p_instance_body_list_noname(self, p):
        'instance_body_list_noname : instance_body_list_noname COMMA instance_body_noname'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_body_list_one_noname(self, p):
        'instance_body_list_noname : instance_body_noname'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_body_noname(self, p):
        'instance_body_noname : instance_port_list'
        p[0] = ('', p[1], None)
        p.set_lineno(0, p.lineno(1))

    def p_instance_param_list(self, p):
        'instance_param_list : SHARP LPAREN instance_params RPAREN'
        p[0] = p[3]
        p.set_lineno(0, p.lineno(1))

    def p_instance_param_list_noname(self, p):
        'instance_param_list : SHARP LPAREN instance_params_noname RPAREN'
        p[0] = p[3]
        p.set_lineno(0, p.lineno(1))

    def p_instance_params(self, p):
        'instance_params : instance_params COMMA instance_param'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_params_one(self, p):
        'instance_params : instance_param'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_params_empty(self, p):
        'instance_params : empty'
        p[0] = ()

    def p_instance_param_exp(self, p):
        'instance_param : DOT _id LPAREN expression RPAREN'
        p[0] = ParamArg(p[2], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_params_noname(self, p):
        'instance_params_noname : instance_params_noname COMMA instance_param_noname'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_params_noname_one(self, p):
        'instance_params_noname : instance_param_noname'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_param_noname_exp(self, p):
        'instance_param_noname : expression'
        p[0] = ParamArg(None, p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_port_list(self, p):
        'instance_port_list : LPAREN instance_ports RPAREN'
        p[0] = p[2]
        p.set_lineno(0, p.lineno(1))

    def p_instance_port_list_noname(self, p):
        'instance_port_list : LPAREN instance_ports_noname RPAREN'
        p[0] = p[2]
        p.set_lineno(0, p.lineno(1))

    def p_instance_port_list_empty(self, p):
        'instance_port_list : empty'
        p[0] = ()

    def p_instance_ports(self, p):
        'instance_ports : instance_ports COMMA instance_port'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_ports_one(self, p):
        'instance_ports : instance_port'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_port(self, p):
        'instance_port : DOT _id LPAREN expression RPAREN'
        p[0] = PortArg(p[2], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_port_empty(self, p):
        'instance_port : DOT _id LPAREN RPAREN'
        p[0] = PortArg(p[2], None, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_ports_noname(self, p):
        'instance_ports_noname : instance_ports_noname COMMA instance_port_noname'
        p[0] = p[1] + (p[3],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_ports_noname_one(self, p):
        'instance_ports_noname : instance_port_noname'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_instance_port_noname(self, p):
        'instance_port_noname : expression'
        p[0] = PortArg(None, p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_instance_ports_noname_empty(self, p):
        'instance_ports_noname : empty'
        p[0] = ()
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def create_decl_assign(self, p, sigtypes, name, assign, width=None, pdims=None, udims=None, lineno=0):
        signed = None
        decls = []

        self.typecheck_decl_assign(p, sigtypes)

        sigtypes = list(sigtypes)

        if 'signed' in sigtypes:
            signed = True
            sigtypes.remove('signed')

        elif 'unsigned' in sigtypes:
            signed = False
            sigtypes.remove('unsigned')

        if len(sigtypes) > 2:
            self._raise_error(p)

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
            self._raise_error(p)

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
            decls.append(CustomVariable(typename=typename, name=name, modportname=modportname,
                                        width=width, signed=signed,
                                        pdims=pdims, udims=udims, lineno=lineno))
            sigtypes.remove(sigtypes[0])

        if len(sigtypes) > 0:
            self._raise_error(p)

        decls.append(assign)
        return decls

    def typecheck_decl_assign(self, p, sigtypes):
        if len(sigtypes) > 3:
            self._raise_error(p)

        if len(sigtypes) != len(set(sigtypes)):
            self._raise_error(p)

        if 'signed' not in sigtypes and 'unsigned' not in sigtypes and len(sigtypes) > 2:
            self._raise_error(p)

        if 'signed' in sigtypes and len(sigtypes) == 1:
            self._raise_error(p)

        if 'unsigned' in sigtypes and len(sigtypes) == 1:
            self._raise_error(p)

        if 'signed' in sigtypes and 'unsigned' in sigtypes:
            self._raise_error(p)

        if 'input' in sigtypes and 'output' in sigtypes:
            self._raise_error(p)

        if 'inout' in sigtypes and 'output' in sigtypes:
            self._raise_error(p)

        if 'inout' in sigtypes and 'input' in sigtypes:
            self._raise_error(p)

        if 'input' in sigtypes and 'reg' in sigtypes:
            self._raise_error(p)

        if 'inout' in sigtypes and 'reg' in sigtypes:
            self._raise_error(p)

        if 'reg' not in sigtypes and 'wire' not in sigtypes:
            self._raise_error(p)

        if 'supply0' in sigtypes and len(sigtypes) != 1:
            self._raise_error(p)

        if 'supply1' in sigtypes and len(sigtypes) != 1:
            self._raise_error(p)

    def p_decl_assign(self, p):
        'decl_assign : sigtypes pdims_width_or_empty delay_or_empty _id decl_assign_right SEMICOLON'
        pdims, width = (None, None) if p[2] == () else p[2]
        sigtypes = p[1]
        ID = p[4]
        left = Lvalue(Identifier(ID, lineno=p.lineno(1)), lineno=p.lineno(1))
        right = p[5][0]
        ldelay = None if p[4] == () else p[4]
        rdelay = p[5][1]
        assign = Assign(left, right, ldelay, rdelay, lineno=p.lineno(1))
        decllist = self.create_decl_assign(p, sigtypes, ID, assign,
                                          width=width, pdims=pdims, lineno=p.lineno(1))
        p[0] = Decl(tuple(decllist), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_decl_assign_right(self, p):
        'decl_assign_right : EQUALS rvalue'
        p[0] = (p[2], None)  # value, delay
        p.set_lineno(0, p.lineno(2))

    def p_decl_assign_right_delay(self, p):
        'decl_assign_right : EQUALS delay rvalue'
        p[0] = (p[3], p[2])  # value, delay
        p.set_lineno(0, p.lineno(3))

    # --------------------------------------------------------------------------
    def p_parameter_decl(self, p):
        'parameter_decl : param SEMICOLON'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_localparam_decl(self, p):
        'localparam_decl : LOCALPARAM var_sigtype_or_empty sign_sigtype_or_empty width_or_empty param_substitution_list SEMICOLON'
        ptype = None if p[2] == () else p[2]
        signed = None if p[3] == () else p[3]
        width = None if p[4] == () else p[4]
        paramlist = [Localparam(rname, rvalue, width, signed=signed, ptype=ptype, lineno=p.lineno(1))
                     for rname, rvalue in p[5]]
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
        'param_substitution : _id EQUALS rvalue'
        p[0] = (p[1], p[3])
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_sigtypes_io_var(self, p):
        'sigtypes : io_sigtype var_sigtype sign_sigtype_or_empty'
        p[0] = (p[1], p[2]) + p[3]
        p.set_lineno(0, p.lineno(1))

    def p_sigtypes_io(self, p):
        'sigtypes : io_sigtype sign_sigtype_or_empty'
        p[0] = (p[1],) + p[2]
        p.set_lineno(0, p.lineno(1))

    def p_sigtypes_var(self, p):
        'sigtypes : var_sigtype sign_sigtype_or_empty'
        p[0] = (p[1],) + p[2]
        p.set_lineno(0, p.lineno(1))

    def p_sigtypes_custom(self, p):
        'sigtypes : custom_sigtype'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_io_sigtype(self, p):
        """io_sigtype : INPUT
        | OUTPUT
        | INOUT
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_var_sigtype(self, p):
        """var_sigtype : TRI
        | REG
        | WIRE
        | INTEGER
        | TIME
        | REAL
        | REALTIME
        | SUPPLY0
        | SUPPLY1
        | LOGIC
        | SHORTINT
        | INT
        | LONGINT
        | BYTE
        | BIT
        | SHORTREAL
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_var_sigtype_or_empty(self, p):
        'var_sigtype_or_empty : var_sigtype'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_var_sigtype_or_empty_empty(self, p):
        'var_sigtype_or_empty : empty'
        p[0] = ()

    def p_sign_sigtype(self, p):
        """sign_sigtype : SIGNED
        | UNSIGNED
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_sign_sigtype_or_empty(self, p):
        'sign_sigtype_or_empty : sign_sigtype'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_sign_sigtype_or_empty_empty(self, p):
        'sign_sigtype_or_empty : empty'
        p[0] = ()

    def p_custom_sigtype(self, p):
        'custom_sigtype : identifier'
        if p[1].scope is not None:
            if len(p[1].scope) > 1:
                self._raise_error(p)
            if p[1].scope[0].iter is not None:
                self._raise_error(p)
            p[0] = (p[1].scope[0].name, p[1].name)
        else:
            p[0] = p[1].name
        p.set_lineno(0, p.lineno(1))

    def p_sigtypes_id(self, p):
        'sigtypes_id : sigtypes _id'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_sigtypes_id_id(self, p):
        'sigtypes_id : sigtypes _id _id'
        p[0] = p[1] + (p[2], p[3])
        p.set_lineno(0, p.lineno(1))

    def p_sigtypes_id_signed_id(self, p):
        'sigtypes_id : sigtypes _id sign_sigtype _id'
        p[0] = p[1] + (p[2], p[3], p[4])
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_assignment(self, p):
        'assignment : ASSIGN delay_or_empty lvalue EQUALS delay_or_empty rvalue SEMICOLON'
        ldelay = None if p[2] == () else p[2]
        rdelay = None if p[5] == () else p[5]
        p[0] = Assign(p[3], p[6], ldelay, rdelay, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_lpointer(self, p):
        'lpointer : pointer'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_lpartselect(self, p):
        'lpartselect : partselect'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_lconcat(self, p):
        'lconcat : concat'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_lvalue_pointer(self, p):
        'lvalue : lpointer'
        p[0] = Lvalue(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_lvalue_partselect(self, p):
        'lvalue : lpartselect'
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
    def p_static_cast(self, p):
        'static_cast : expression SQUOTE LPAREN expression RPAREN'
        p[0] = StaticCast(p[1], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 2
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
    # Level 3
    def p_expression_power(self, p):
        'expression : expression POWER expression'
        p[0] = Power(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 4
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
    # Level 5
    def p_expression_plus(self, p):
        'expression : expression PLUS expression'
        p[0] = Plus(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_expression_minus(self, p):
        'expression : expression MINUS expression'
        p[0] = Minus(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 6
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
    # Level 7
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
    # Level 8
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
    # Level 9
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
    # Level 10
    def p_expression_Or(self, p):
        'expression : expression OR expression'
        p[0] = Or(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 11
    def p_expression_land(self, p):
        'expression : expression LAND expression'
        p[0] = Land(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 12
    def p_expression_lor(self, p):
        'expression : expression LOR expression'
        p[0] = Lor(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    # Level 13
    def p_expression_cond(self, p):
        'expression : expression QUESTION expression COLON expression'
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

    def p_expression_static_cast(self, p):
        'expression : static_cast'
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
        p[0] = Partselect(p[1], p[3], Plus(p[3], p[5], lineno=p.lineno(1)), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_partselect_minus(self, p):
        'partselect : identifier LBRACKET expression MINUSCOLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], Minus(p[3], p[5], lineno=p.lineno(1)), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_partselect_pointer(self, p):
        'partselect : pointer LBRACKET expression COLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_partselect_pointer_plus(self, p):
        'partselect : pointer LBRACKET expression PLUSCOLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], Plus(p[3], p[5], lineno=p.lineno(1)), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_partselect_pointer_minus(self, p):
        'partselect : pointer LBRACKET expression MINUSCOLON expression RBRACKET'
        p[0] = Partselect(p[1], p[3], Minus(p[3], p[5], lineno=p.lineno(1)), lineno=p.lineno(1))
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
        | substitution_operator
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
        'blocking_substitution_base : lvalue EQUALS delay_or_empty rvalue'
        ldelay = None
        rdelay = None if p[3] == () else p[3]
        p[0] = BlockingSubstitution(p[1], p[4], ldelay, rdelay, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_blocking_substitution_base_ldelay(self, p):
        'blocking_substitution_base : delay lvalue EQUALS delay_or_empty rvalue'
        ldelay = p[1]
        rdelay = None if p[4] == () else p[4]
        p[0] = BlockingSubstitution(p[2], p[5], ldelay, rdelay, lineno=p.lineno(2))
        p.set_lineno(0, p.lineno(2))

    def p_nonblocking_substitution(self, p):
        'nonblocking_substitution : lvalue LE delay_or_empty rvalue SEMICOLON'
        ldelay = None
        rdelay = None if p[3] == () else p[3]
        p[0] = NonblockingSubstitution(p[1], p[4], ldelay, rdelay, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_nonblocking_substitution_ldelay(self, p):
        'nonblocking_substitution : delay lvalue LE delay_or_empty rvalue SEMICOLON'
        ldelay = p[1]
        rdelay = None if p[4] == () else p[4]
        p[0] = NonblockingSubstitution(p[2], p[5], ldelay, rdelay, lineno=p.lineno(2))
        p.set_lineno(0, p.lineno(2))

    # --------------------------------------------------------------------------
    def p_substitution_operator_plusequals(self, p):
        'substitution_operator : lvalue PLUSEQUALS rvalue SEMICOLON'
        p[0] = PlusEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_minusequals(self, p):
        'substitution_operator : lvalue MINUSEQUALS rvalue SEMICOLON'
        p[0] = MinusEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_timesequals(self, p):
        'substitution_operator : lvalue TIMESEQUALS rvalue SEMICOLON'
        p[0] = TimesEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_divideequals(self, p):
        'substitution_operator : lvalue DIVIDEEQUALS rvalue SEMICOLON'
        p[0] = DivideEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_modequals(self, p):
        'substitution_operator : lvalue MODEQUALS rvalue SEMICOLON'
        p[0] = ModEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_orequals(self, p):
        'substitution_operator : lvalue OREQUALS rvalue SEMICOLON'
        p[0] = OrEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_andequals(self, p):
        'substitution_operator : lvalue ANDEQUALS rvalue SEMICOLON'
        p[0] = AndEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_xorequals(self, p):
        'substitution_operator : lvalue XOREQUALS rvalue SEMICOLON'
        p[0] = XorEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_slaequals(self, p):
        'substitution_operator : lvalue LSHIFTAEQUALS rvalue SEMICOLON'
        p[0] = SlaEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_sraequals(self, p):
        'substitution_operator : lvalue RSHIFTAEQUALS rvalue SEMICOLON'
        p[0] = SraEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_sllequals(self, p):
        'substitution_operator : lvalue LSHIFTEQUALS rvalue SEMICOLON'
        p[0] = SllEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_srlequals(self, p):
        'substitution_operator : lvalue RSHIFTEQUALS rvalue SEMICOLON'
        p[0] = SrlEquals(p[1], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_increment(self, p):
        'substitution_operator : lvalue INCREMENT SEMICOLON'
        p[0] = Increment(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_substitution_operator_decrement(self, p):
        'substitution_operator : lvalue DECREMENT SEMICOLON'
        p[0] = Decrement(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_delay(self, p):
        'delay : SHARP LPAREN expression RPAREN'
        p[0] = DelayStatement(p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_delay_identifier(self, p):
        'delay : SHARP identifier'
        p[0] = DelayStatement(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_delay_intnumber(self, p):
        'delay : SHARP intnumber'
        p[0] = DelayStatement(
            IntConst(p[2], lineno=p.lineno(1)), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_delay_floatnumber(self, p):
        'delay : SHARP floatnumber'
        p[0] = DelayStatement(FloatConst(
            p[2], lineno=p.lineno(1)), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_delay_or_empty(self, p):
        'delay_or_empty : delay'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_delay_or_empty_empty(self, p):
        'delay_or_empty : empty'
        p[0] = ()

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
        'namedblock : BEGIN COLON _id namedblock_statements END'
        p[0] = Block(p[4], p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_namedblock_empty(self, p):
        'namedblock : BEGIN COLON _id END'
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
        | parameter_decl
        | localparam_decl
        """
        if isinstance(p[1], Decl):
            for r in p[1].list:
                if (not isinstance(r, Reg) and not isinstance(r, Wire) and
                    not isinstance(r, Integer) and not isinstance(r, Real) and
                        not isinstance(r, Parameter) and not isinstance(r, Localparam)):
                    self._raise_error(p)

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
    def p_genvar_decl(self, p):
        'genvar_decl : GENVAR genvarlist SEMICOLON'
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
        'genvar : _id'
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

    def p_generate_items(self, p):
        'generate_items : generate_items generate_item'
        p[0] = p[1] + (p[2],)
        p.set_lineno(0, p.lineno(1))

    def p_generate_items_one(self, p):
        'generate_items : generate_item'
        p[0] = (p[1],)
        p.set_lineno(0, p.lineno(1))

    def p_generate_items_empty(self, p):
        'generate_items : empty'
        p[0] = ()
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
        'generate_block : BEGIN COLON _id generate_items END'
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
        'systemcall : DOLLER systemcall_name'
        p[0] = SystemCall(p[2], (), lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_systemcall(self, p):
        'systemcall : DOLLER systemcall_name LPAREN sysargs RPAREN'
        p[0] = SystemCall(p[2], p[4], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_systemcall_name(self, p):
        """systemcall_name : _id
        | sign_sigtype
        """
        p[0] = p[1]
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
        'function : FUNCTION width_or_empty _id SEMICOLON function_statement ENDFUNCTION'
        retwidth = None if p[2] == () else p[2]
        p[0] = Function(p[3], p[5], retwidth=retwidth, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_function_rettype(self, p):
        'function : FUNCTION var_sigtype _id SEMICOLON function_statement ENDFUNCTION'
        p[0] = Function(p[3], p[5], rettype=p[2], lineno=p.lineno(1))
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
        'funcvardecl : decl'
        if isinstance(p[1], Decl):
            for r in p[1].list:
                if (not isinstance(r, Input) and not isinstance(r, Reg) and
                        not isinstance(r, Integer)):
                    self._raise_error(p)

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
        'task : TASK _id SEMICOLON task_statement ENDTASK'
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
        'taskvardecl : decl'

        if isinstance(p[1], Decl):
            for r in p[1].list:
                if (not isinstance(r, Input) and not isinstance(r, Reg) and
                        not isinstance(r, Integer)):
                    self._raise_error(p)

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
    def p__id(self, p):
        """_id : ID
        | SENS_OR
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_single_identifier(self, p):
        'identifier : _id'
        p[0] = Identifier(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_identifier_scope(self, p):
        'identifier : identifier DOT _id'
        scope = () if p[1].scope is None else p[1].scope
        scope = scope + (IdentifierScope(p[1].name, lineno=p.lineno(1)),)
        p[0] = Identifier(p[3], scope=scope, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_identifier_pointer(self, p):
        'identifier : identifier LBRACKET expression RBRACKET DOT _id'
        scope = () if p[1].scope is None else p[1].scope
        scope = scope + (IdentifierScope(p[1].name, p[3], lineno=p.lineno(1)),)
        p[0] = Identifier(p[6], scope=scope, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_disable(self, p):
        'disable : DISABLE _id'
        p[0] = Disable(p[2], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_single_statement_delay(self, p):
        'single_statement : SHARP expression SEMICOLON'
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
        'interfacename : _id'
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
        | parameter_decl
        | localparam_decl
        | typedef
        | pragma
        | modport
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_modport(self, p):
        'modport : MODPORT _id LPAREN ioports RPAREN SEMICOLON'
        p[0] = Modport(p[2], p[4], lineno=p.lineno(1))
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
        'structname : _id'
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
        | parameter_decl
        | localparam_decl
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
        'unionname : _id'
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
        | parameter_decl
        | localparam_decl
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
        'enum_base : ENUM enum_sigtype LBRACE enumlist RBRACE enumname'
        type = p[1]
        width = None
        p[0] = Enum(p[5], p[3], packed=False, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_enum_base_sigtype_width(self, p):
        'enum_base : ENUM enum_sigtype width LBRACE enumlist RBRACE enumname'
        type = p[1]
        width = p[2]
        p[0] = Enum(p[5], p[3], packed=False, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_enum_sigtype(self, p):
        """enum_sigtype : var_sigtype
        | custom_sigtype
        """
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_enumname(self, p):
        'enumname : _id'
        p[0] = p[1]
        p.set_lineno(0, p.lineno(1))

    def p_enumlist_items(self, p):
        'enumlist : enum_items'
        p[0] = Enumlist(p[1], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_enumlist_length(self, p):
        'enumlist : _id LBRACKET expression RBRACKET'
        p[0] = Enumlist(name=p[1], length=p[3], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_enumlist_length_value(self, p):
        'enumlist : _id LBRACKET expression RBRACKET EQUALS expression'
        p[0] = Enumlist(name=p[1], length=p[3], value=p[6], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_enumlist_start_end(self, p):
        'enumlist : _id LBRACKET expression COLON expression RBRACKET'
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
        'enum_item : _id'
        p[0] = (p[1], None)  # ID, value
        p.set_lineno(0, p.lineno(1))

    def p_enum_item_value(self, p):
        'enum_item : _id EQUALS rvalue'
        p[0] = (p[1], p[3])  # ID, value
        p.set_lineno(0, p.lineno(1))

    # --------------------------------------------------------------------------
    def p_typedef(self, p):
        'typedef : TYPEDEF sigtypes_id SEMICOLON'
        sigtypes, ID = self._separate_sigtypes_id(p, p[2])
        p[0] = TypeDef(ID, sigtypes, width=None, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_typedef_pdims_width(self, p):
        'typedef : TYPEDEF sigtypes pdims_width _id SEMICOLON'
        pdims, width = p[3]
        p[0] = TypeDef(p[4], p[2], width=width, pdims=pdims, lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_typedef_pdims_width_udims(self, p):
        'typedef : TYPEDEF sigtypes pdims_width _id udims SEMICOLON'
        pdims, width = p[3]
        p[0] = TypeDef(p[4], p[2], width=width, pdims=pdims, udims=p[5], lineno=p.lineno(1))
        p.set_lineno(0, p.lineno(1))

    def p_typedef_udims(self, p):
        'typedef : TYPEDEF sigtypes_id udims SEMICOLON'
        sigtypes, ID = self._separate_sigtypes_id(p, p[2])
        p[0] = TypeDef(ID, sigtypes, width=None, udims=p[3], lineno=p.lineno(1))
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
        if p:
            msg = 'before: "%s"' % p.value
            coord = self._coord(p.lineno)
        else:
            msg = 'at end of input'
            coord = None

        raise ParseError("%s: %s" % (coord, msg))

    # --------------------------------------------------------------------------
    def _raise_error(self, p):
        msg = 'syntax error'

        try:
            coord = self._coord(p.lineno(1))
        except:
            coord = None

        raise ParseError("%s: %s" % (coord, msg))

    def _coord(self, lineno, column=None):
        ret = [self.lexer.filename]
        ret.append('line:%s' % lineno)
        if column is not None:
            ret.append('column:%s' % column)
        return ' '.join(ret)


class ParseError(Exception):
    pass


class VerilogCodeParser(object):

    def __init__(self, filelist, preprocess_output='preprocess.output',
                 preprocess_include=None,
                 preprocess_define=None,
                 outputdir=".",
                 debug=False
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


def parse(filelist,
          preprocess_include=None,
          preprocess_define=None,
          outputdir=".",
          debug=False):

    codeparser = VerilogCodeParser(
        filelist,
        preprocess_include=preprocess_include,
        preprocess_define=preprocess_define,
        outputdir=outputdir,
        debug=debug
    )

    ast = codeparser.parse(debug=debug)
    directives = codeparser.get_directives()

    return ast, directives
