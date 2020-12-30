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
import re

from ply.lex import *


class VerilogLexer(object):
    """ Verilog HDL Lexical Analayzer """

    def __init__(self, error_func):
        self.filename = ''
        self.error_func = error_func
        self.directives = []
        self.default_nettype = 'wire'

    def build(self, **kwargs):
        self.lexer = lex(object=self, **kwargs)

    def input(self, data):
        self.lexer.input(data)

    def reset_lineno(self):
        self.lexer.lineno = 1

    def get_directives(self):
        return tuple(self.directives)

    def get_default_nettype(self):
        return self.default_nettype

    def token(self):
        return self.lexer.token()

    keywords = (
        'MODULE', 'ENDMODULE', 'BEGIN', 'END', 'GENERATE', 'ENDGENERATE', 'GENVAR',
        'FUNCTION', 'ENDFUNCTION', 'TASK', 'ENDTASK',
        'INPUT', 'INOUT', 'OUTPUT', 'TRI', 'REG', 'LOGIC', 'WIRE', 'INTEGER', 'REAL', 'SIGNED',
        'PARAMETER', 'LOCALPARAM', 'SUPPLY0', 'SUPPLY1',
        'ASSIGN', 'ALWAYS', 'ALWAYS_FF', 'ALWAYS_COMB', 'ALWAYS_LATCH', 'SENS_OR', 'POSEDGE', 'NEGEDGE', 'INITIAL',
        'IF', 'ELSE', 'FOR', 'WHILE', 'CASE', 'CASEX', 'CASEZ', 'UNIQUE', 'ENDCASE', 'DEFAULT',
        'WAIT', 'FOREVER', 'DISABLE', 'FORK', 'JOIN',
    )

    reserved = {}
    for keyword in keywords:
        if keyword == 'SENS_OR':
            reserved['or'] = keyword
        else:
            reserved[keyword.lower()] = keyword

    operators = (
        'PLUS', 'MINUS', 'POWER', 'TIMES', 'DIVIDE', 'MOD',
        'NOT', 'OR', 'NOR', 'AND', 'NAND', 'XOR', 'XNOR',
        'LOR', 'LAND', 'LNOT',
        'LSHIFTA', 'RSHIFTA', 'LSHIFT', 'RSHIFT',
        'LT', 'GT', 'LE', 'GE', 'EQ', 'NE', 'EQL', 'NEL',
        'COND',  # ?
        'EQUALS',
    )

    tokens = keywords + operators + (
        'ID',
        'AT', 'COMMA', 'COLON', 'SEMICOLON', 'DOT',
        'PLUSCOLON', 'MINUSCOLON',
        'FLOATNUMBER', 'STRING_LITERAL',
        'INTNUMBER_DEC', 'SIGNED_INTNUMBER_DEC',
        'INTNUMBER_HEX', 'SIGNED_INTNUMBER_HEX',
        'INTNUMBER_OCT', 'SIGNED_INTNUMBER_OCT',
        'INTNUMBER_BIN', 'SIGNED_INTNUMBER_BIN',
        'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET', 'LBRACE', 'RBRACE',
        'DELAY', 'DOLLER',
    )

    skipped = (
        'COMMENTOUT', 'LINECOMMENT', 'DIRECTIVE',
    )

    # Ignore
    t_ignore = ' \t'

    # Directive
    directive = r"""\`.*?\n"""

    @TOKEN(directive)
    def t_DIRECTIVE(self, t):
        self.directives.append((self.lexer.lineno, t.value))
        t.lexer.lineno += t.value.count("\n")
        m = re.match("^`default_nettype\s+(.+)\n", t.value)
        if m:
            self.default_nettype = m.group(1)
        pass

    # Comment
    linecomment = r"""//.*?\n"""
    commentout = r"""/\*(.|\n)*?\*/"""

    @TOKEN(linecomment)
    def t_LINECOMMENT(self, t):
        t.lexer.lineno += t.value.count("\n")
        pass

    @TOKEN(commentout)
    def t_COMMENTOUT(self, t):
        t.lexer.lineno += t.value.count("\n")
        pass

    # Operator
    t_LOR = r'\|\|'
    t_LAND = r'\&\&'

    t_NOR = r'~\|'
    t_NAND = r'~\&'
    t_XNOR = r'~\^'
    t_OR = r'\|'
    t_AND = r'\&'
    t_XOR = r'\^'
    t_LNOT = r'!'
    t_NOT = r'~'

    t_LSHIFTA = r'<<<'
    t_RSHIFTA = r'>>>'
    t_LSHIFT = r'<<'
    t_RSHIFT = r'>>'

    t_EQL = r'==='
    t_NEL = r'!=='
    t_EQ = r'=='
    t_NE = r'!='

    t_LE = r'<='
    t_GE = r'>='
    t_LT = r'<'
    t_GT = r'>'

    t_POWER = r'\*\*'
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_MOD = r'%'

    t_COND = r'\?'
    t_EQUALS = r'='

    t_PLUSCOLON = r'\+:'
    t_MINUSCOLON = r'-:'

    t_AT = r'@'
    t_COMMA = r','
    t_SEMICOLON = r';'
    t_COLON = r':'
    t_DOT = r'\.'

    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'

    t_DELAY = r'\#'
    t_DOLLER = r'\$'

    bin_number = '[0-9]*\'[bB][0-1xXzZ?][0-1xXzZ?_]*'
    signed_bin_number = '[0-9]*\'[sS][bB][0-1xZzZ?][0-1xXzZ?_]*'
    octal_number = '[0-9]*\'[oO][0-7xXzZ?][0-7xXzZ?_]*'
    signed_octal_number = '[0-9]*\'[sS][oO][0-7xXzZ?][0-7xXzZ?_]*'
    hex_number = '[0-9]*\'[hH][0-9a-fA-FxXzZ?][0-9a-fA-FxXzZ?_]*'
    signed_hex_number = '[0-9]*\'[sS][hH][0-9a-fA-FxXzZ?][0-9a-fA-FxXzZ?_]*'

    decimal_number = '([0-9]*\'[dD][0-9xXzZ?][0-9xXzZ?_]*)|([0-9][0-9_]*)'
    signed_decimal_number = '[0-9]*\'[sS][dD][0-9xXzZ?][0-9xXzZ?_]*'

    exponent_part = r"""([eE][-+]?[0-9]+)"""
    fractional_constant = r"""([0-9]*\.[0-9]+)|([0-9]+\.)"""
    float_number = '((((' + fractional_constant + ')' + \
        exponent_part + '?)|([0-9]+' + exponent_part + ')))'

    simple_escape = r"""([a-zA-Z\\?'"])"""
    octal_escape = r"""([0-7]{1,3})"""
    hex_escape = r"""(x[0-9a-fA-F]+)"""
    escape_sequence = r"""(\\(""" + simple_escape + '|' + octal_escape + '|' + hex_escape + '))'
    string_char = r"""([^"\\\n]|""" + escape_sequence + ')'
    string_literal = '"' + string_char + '*"'

    identifier = r"""(([a-zA-Z_])([a-zA-Z_0-9$])*)|((\\\S)(\S)*)"""

    @TOKEN(string_literal)
    def t_STRING_LITERAL(self, t):
        return t

    @TOKEN(float_number)
    def t_FLOATNUMBER(self, t):
        return t

    @TOKEN(signed_bin_number)
    def t_SIGNED_INTNUMBER_BIN(self, t):
        return t

    @TOKEN(bin_number)
    def t_INTNUMBER_BIN(self, t):
        return t

    @TOKEN(signed_octal_number)
    def t_SIGNED_INTNUMBER_OCT(self, t):
        return t

    @TOKEN(octal_number)
    def t_INTNUMBER_OCT(self, t):
        return t

    @TOKEN(signed_hex_number)
    def t_SIGNED_INTNUMBER_HEX(self, t):
        return t

    @TOKEN(hex_number)
    def t_INTNUMBER_HEX(self, t):
        return t

    @TOKEN(signed_decimal_number)
    def t_SIGNED_INTNUMBER_DEC(self, t):
        return t

    @TOKEN(decimal_number)
    def t_INTNUMBER_DEC(self, t):
        return t

    @TOKEN(identifier)
    def t_ID(self, t):
        t.type = self.reserved.get(t.value, 'ID')
        return t

    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")
        pass

    def t_error(self, t):
        msg = 'Illegal character %s' % repr(t.value[0])
        self._error(msg, t)

    def _error(self, msg, token):
        location = self._make_tok_location(token)
        self.error_func(msg, location[0], location[1])
        self.lexer.skip(1)

    def _find_tok_column(self, token):
        i = token.lexpos
        while i > 0:
            if self.lexer.lexdata[i] == '\n':
                break
            i -= 1
        return (token.lexpos - i) + 1

    def _make_tok_location(self, token):
        return (token.lineno, self._find_tok_column(token))


def dump_tokens(text):
    def my_error_func(msg, a, b):
        sys.write(msg + "\n")
        sys.exit()

    lexer = VerilogLexer(error_func=my_error_func)
    lexer.build()
    lexer.input(text)

    ret = []

    # Tokenize
    while True:
        tok = lexer.token()
        if not tok:
            break  # No more input
        ret.append("%s %s %d %s %d\n" %
                   (tok.value, tok.type, tok.lineno, lexer.filename, tok.lexpos))

    return ''.join(ret)
