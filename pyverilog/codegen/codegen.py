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
import math
import re
import functools
from jinja2 import Environment, FileSystemLoader

from pyverilog.parser.ast import *
from pyverilog.utils.op2mark import op2mark
from pyverilog.utils.op2mark import op2order

DEFAULT_TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/template/'

# -------------------------------------------------------------------------------
try:
    import textwrap
    indent = textwrap.indent
except:
    def indent(text, prefix, predicate=None):
        if predicate is None:
            def predicate(x): return x and not x.isspace()
        ret = []
        for line in text.split('\n'):
            if predicate(line):
                ret.append(prefix)
            ret.append(line)
            ret.append('\n')
        return ''.join(ret[:-1])


def indent_multiline_assign(text):
    ret = []
    texts = text.split('\n')
    if len(texts) <= 1:
        return text
    try:
        p = texts[0].index('=')
    except:
        return text
    ret.append(texts[0])
    ret.append('\n')
    ret.append(indent('\n'.join(texts[1:]), ' ' * (p + 2)))
    return ''.join(ret)

# -------------------------------------------------------------------------------


class ConvertVisitor(object):
    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        ret = []
        for c in node.children():
            ret.append(self.visit(c))
        return ''.join(ret)


def getfilename(node):
    return node.__class__.__name__.lower() + '.txt'


def escape(s):
    if s.startswith('\\'):
        return s + ' '
    return s


def del_paren(s):
    if s.startswith('(') and s.endswith(')'):
        return s[1:-1]
    return s


def del_space(s):
    return s.replace(' ', '')


def get_signed(node):
    if node.signed is None:
        return ''
    if not node.signed:
        return 'unsigned'
    return 'signed'


def get_items_signed(items):
    signed = ''
    for item in items:
        s = get_signed(item)
        if s != '':
            signed = s
            break
    return signed


class ASTCodeGenerator(ConvertVisitor):
    def __init__(self, indentsize=2):
        self.env = Environment(loader=FileSystemLoader(DEFAULT_TEMPLATE_DIR))
        self.indent = functools.partial(indent, prefix=' ' * indentsize)
        self.template_cache = {}

    def get_template(self, filename):
        if filename in self.template_cache:
            return self.template_cache[filename]

        template = self.env.get_template(filename)
        self.template_cache[filename] = template
        return template

    def visit_Source(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'description': self.visit(node.description),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Description(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'definitions': [self.visit(definition) for definition in node.definitions],
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Module(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        paramlist = (self.indent(self._paramlist(node.paramlist))
                     if node.paramlist is not None else '')
        portlist = (self.indent(self._portlist(node.portlist))
                    if node.portlist is not None else '')
        template_dict = {
            'modulename': escape(node.name),
            'paramlist': paramlist,
            'portlist': portlist,
            'items': [self.indent(self.visit(item)) for item in node.items] if node.items else (),
        }
        rslt = template.render(template_dict)
        return rslt

    def _paramlist(self, paramlist):
        filename = 'paramlist.txt'
        template = self.get_template(filename)
        params = [self.visit(param).replace(';', '') for param in paramlist]
        template_dict = {
            'params': params,
            'len_params': len(params),
        }
        rslt = template.render(template_dict)
        return rslt

    def _portlist(self, portlist):
        filename = 'portlist.txt'
        template = self.get_template(filename)
        ports = [self.visit(port).replace(';', '') for port in portlist]
        template_dict = {
            'ports': ports,
            'len_ports': len(ports),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_DeclParameters(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        var = node.items[0]
        sigtypes = ' '.join(var.sigtypes) if var.sigtypes is not None else ''
        signed = get_signed(var)
        items = [self.visit(item) for item in node.items]
        template_dict = {
            'sigtypes': sigtypes,
            'width': ('' if var.width is None or (value.startswith('"') and value.endswith('"')) else
                      self.visit(var.width)),
            'signed': signed,
            'pdims': '' if var.pdims is None else self.visit(var.pdims),
            'items': items,
            'len_items': len(items)
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_DeclLocalparams(self, node):
        return self.visit_DeclParameters(node)

    def visit_DeclVars(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        var = node.items[0]
        sigtypes = []
        for item in var.items:
            if not isinstance(item, CustomType):
                sigtypes.append(item.__class__.__name__.lower())
            elif item.modport is not None:
                sigtypes.append('.'.join([escape(item.typename), escape(item.modport)]))
            else:
                sigtypes.append(escape(item.typename))
        sigtypes = ' '.join(sigtypes)
        signed = get_items_signed(var.items)
        items = [self.visit(item) for item in node.items]
        template_dict = {
            'sigtypes': sigtypes,
            'width': '' if var.items[0].width is None else self.visit(var.items[0].width),
            'signed': signed,
            'pdims': '' if var.items[0].pdims is None else self.visit(var.items[0].pdims),
            'items': items,
            'len_items': len(items)
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_DeclVarAssign(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        var = node.var
        template_dict = {
            'sigtypes': ' '.join([item.__class__.__name__.lower() for item in var.items]),
            'width': '' if var.items[0].width is None else self.visit(var.items[0].width),
            'signed': signed,
            'pdims': '' if var.items[0].pdims is None else self.visit(var.items[0].pdims),
            'var': self.visit(var),
            'right': self.visit(node.assign.right),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_DeclInstances(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        paramlist = [self.indent(self.visit(param)) for param in node.items[0].paramlist]
        items = [self.visit(item) for item in node.items]
        template_dict = {
            'module': escape(node.module),
            'paramlist': paramlist,
            'len_paramlist': len(paramlist),
            'items': items,
            'len_items': len(items),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Port(self, node):
        # old-style port declaration
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name': escape(node.name),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Width(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        msb = del_space(del_paren(self.visit(node.msb)))
        lsb = del_space(del_paren(self.visit(node.lsb))) if node.lsb is not None else ''
        template_dict = {
            'msb': msb,
            'lsb': lsb,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Dims(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        dims = ''.join([self.visit(dim) for dim in node.dims])
        template_dict = {
            'dims': dims
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Identifier(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        scope = ('' if node.scope is None else
                 ''.join([self.visit(s) for s in node.scope]))
        template_dict = {
            'name': escape(node.name),
            'scope': scope,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_IdentifierScope(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name': escape(node.name),
            'iter': '' if node.iter is None else self.visit(node.iter),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_IntConst(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'value': node.value,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_FloatConst(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'value': node.value,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_StringConst(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'value': node.value,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Var(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name': escape(node.items[0].name),
            'udims': '' if node.items[0].udims is None else self.visit(node.items[0].udims),
        }
        rslt = template.render(template_dict)
        return rslt

#    def visit__Variable4State(self, node):
#        filename = '_variable4state.txt'
#        template = self.get_template(filename)
#        template_dict = {
#            'vartype': node.__class__.__name__.lower(),
#            'name': escape(node.name),
#            'width': '' if node.width is None else self.visit(node.width),
#            'signed': get_signed(node),
#            'pdims': '' if node.pdims is None else self.visit(node.pdims),
#            'udims': '' if node.udims is None else self.visit(node.udims),
#        }
#        rslt = template.render(template_dict)
#        return rslt
#
#    def visit__Variable4State_no_width(self, node):
#        filename = '_variable4state_no_width.txt'
#        template = self.get_template(filename)
#        template_dict = {
#            'vartype': node.__class__.__name__.lower(),
#            'name': escape(node.name),
#            'width': '',
#            'signed': get_signed(node),
#            'pdims': '' if node.pdims is None else self.visit(node.pdims),
#            'udims': '' if node.udims is None else self.visit(node.udims),
#        }
#        rslt = template.render(template_dict)
#        return rslt
#
#    def visit__Variable2State(self, node):
#        filename = '_variable2state.txt'
#        template = self.get_template(filename)
#        template_dict = {
#            'vartype': node.__class__.__name__.lower(),
#            'name': escape(node.name),
#            'width': '' if node.width is None else self.visit(node.width),
#            'signed': get_signed(node),
#            'pdims': '' if node.pdims is None else self.visit(node.pdims),
#            'udims': '' if node.udims is None else self.visit(node.udims),
#        }
#        rslt = template.render(template_dict)
#        return rslt
#
#    def visit__Variable2State_no_width(self, node):
#        filename = '_variable4state_no_width.txt'
#        template = self.get_template(filename)
#        template_dict = {
#            'vartype': node.__class__.__name__.lower(),
#            'name': escape(node.name),
#            'width': '',
#            'signed': get_signed(node),
#            'pdims': '' if node.pdims is None else self.visit(node.pdims),
#            'udims': '' if node.udims is None else self.visit(node.udims),
#        }
#        rslt = template.render(template_dict)
#        return rslt
#
#    def visit__VariableReal(self, node):
#        filename = '_variablereal.txt'
#        template = self.get_template(filename)
#        template_dict = {
#            'vartype': node.__class__.__name__.lower(),
#            'name': escape(node.name),
#            'width': '',
#            'signed': get_signed(node),
#            'pdims': '' if node.pdims is None else self.visit(node.pdims),
#            'udims': '' if node.udims is None else self.visit(node.udims),
#        }
#        rslt = template.render(template_dict)
#        return rslt
#
#    def visit_Input(self, node):
#        return self.visit__Variable4State(node)
#
#    def visit_Output(self, node):
#        return self.visit__Variable4State(node)
#
#    def visit_Inout(self, node):
#        return self.visit__Variable4State(node)
#
#    def visit_Tri(self, node):
#        return self.visit__Variable4State(node)
#
#    def visit_Wire(self, node):
#        return self.visit__Variable4State(node)
#
#    def visit_Reg(self, node):
#        return self.visit__Variable4State(node)
#
#    def visit_Supply0(self, node):
#        return self.visit__Variable4State(node)
#
#    def visit_Supply1(self, node):
#        return self.visit__Variable4State(node)
#
#    def visit_Integer(self, node):
#        return self.visit__Variable4State_no_width(node)
#
#    def visit_Time(self, node):
#        return self.visit__Variable4State_no_width(node)
#
#    def visit_Real(self, node):
#        return self.visit__VariableReal(node)
#
#    def visit_RealTime(self, node):
#        return self.visit__VariableReal(node)
#
#    def visit_Logic(self, node):
#        return self.visit__Variable4State(node)
#
#    def visit_ShortInt(self, node):
#        return self.visit__Variable2State_no_width(node)
#
#    def visit_Int(self, node):
#        return self.visit__Variable2State_no_width(node)
#
#    def visit_LongInt(self, node):
#        return self.visit__Variable2State_no_width(node)
#
#    def visit_Byte(self, node):
#        return self.visit__Variable2State_no_width(node)
#
#    def visit_Bit(self, node):
#        return self.visit__Variable2State(node)
#
#    def visit_ShortReal(self, node):
#        return self.visit__VariableReal(node)
#
#    def visit_CustomType(self, node):
#        filename = getfilename(node)
#        template = self.get_template(filename)
#        template_dict = {
#            'vartype': escape(node.typename),
#            'name': escape(node.name),
#            'modportname': escape(node.modportname) if node.modportname is not None else '',
#            'width': '' if node.width is None else self.visit(node.width),
#            'signed': get_signed(node),
#            'pdims': '' if node.pdims is None else self.visit(node.pdims),
#            'udims': '' if node.udims is None else self.visit(node.udims),
#        }
#        rslt = template.render(template_dict)
#        return rslt

    def visit_Parameter(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        sigtypes = ' '.join(node.sigtypes) if node.sigtypes is not None else '',
        template_dict = {
            'name': escape(node.name),
            'value': self.visit(node.value),
            'udims': '' if node.udims is None else self.visit(node.udims),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Localparam(self, node):
        return self.visit_Parameter(node)

    def visit_Concat(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        items = [del_paren(self.visit(item)) for item in node.items]
        template_dict = {
            'items': items,
            'len_items': len(items),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Repeat(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'value': del_paren(self.visit(node.value)),
            'times': del_paren(self.visit(node.times)),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Partselect(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'var': self.visit(node.var),
            'msb': del_space(del_paren(self.visit(node.msb))),
            'lsb': del_space(del_paren(self.visit(node.lsb))),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Pointer(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'var': self.visit(node.var),
            'ptr': del_paren(self.visit(node.ptr)),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Lvalue(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'var': del_paren(self.visit(node.var)),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Rvalue(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'var': del_paren(self.visit(node.var)),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit__BinaryOperator(self, node):
        filename = '_binaryoperator.txt'
        template = self.get_template(filename)
        order = op2order(node.__class__.__name__)
        lorder = op2order(node.left.__class__.__name__)
        rorder = op2order(node.right.__class__.__name__)
        left = self.visit(node.left)
        right = self.visit(node.right)
        if ((not isinstance(node.left, (Sll, Srl, Sra,
                                        LessThan, GreaterThan, LessEq, GreaterEq,
                                        Eq, NotEq, Eql, NotEql)))
                and (lorder is not None and lorder <= order)):
            left = del_paren(left)
        if ((not isinstance(node.right, (Sll, Srl, Sra,
                                         LessThan, GreaterThan, LessEq, GreaterEq,
                                         Eq, NotEq, Eql, NotEql))) and
                (rorder is not None and order > rorder)):
            right = del_paren(right)
        template_dict = {
            'left': left,
            'right': right,
            'op': op2mark(node.__class__.__name__),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit__UnaryOperator(self, node):
        filename = '_unaryoperator.txt'
        template = self.get_template(filename)
        right = self.visit(node.right)
        template_dict = {
            'right': right,
            'op': op2mark(node.__class__.__name__),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_StaticCast(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        casting_type = del_paren(self.visit(node.casting_type))
        right = del_paren(self.visit(node.right))
        template_dict = {
            'casting_type': casting_type,
            'right': right,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Uplus(self, node):
        return self.visit__UnaryOperator(node)

    def visit_Uminus(self, node):
        return self.visit__UnaryOperator(node)

    def visit_Ulnot(self, node):
        return self.visit__UnaryOperator(node)

    def visit_Unot(self, node):
        return self.visit__UnaryOperator(node)

    def visit_Uand(self, node):
        return self.visit__UnaryOperator(node)

    def visit_Unand(self, node):
        return self.visit__UnaryOperator(node)

    def visit_Uor(self, node):
        return self.visit__UnaryOperator(node)

    def visit_Unor(self, node):
        return self.visit__UnaryOperator(node)

    def visit_Uxor(self, node):
        return self.visit__UnaryOperator(node)

    def visit_Uxnor(self, node):
        return self.visit__UnaryOperator(node)

    def visit_Power(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Times(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Divide(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Mod(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Plus(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Minus(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Sll(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Srl(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Sra(self, node):
        return self.visit__BinaryOperator(node)

    def visit_LessThan(self, node):
        return self.visit__BinaryOperator(node)

    def visit_GreaterThan(self, node):
        return self.visit__BinaryOperator(node)

    def visit_LessEq(self, node):
        return self.visit__BinaryOperator(node)

    def visit_GreaterEq(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Eq(self, node):
        return self.visit__BinaryOperator(node)

    def visit_NotEq(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Eql(self, node):
        return self.visit__BinaryOperator(node)

    def visit_NotEql(self, node):
        return self.visit__BinaryOperator(node)

    def visit_And(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Xor(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Xnor(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Or(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Land(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Lor(self, node):
        return self.visit__BinaryOperator(node)

    def visit_Cond(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        true_value = del_paren(self.visit(node.true_value))
        false_value = del_paren(self.visit(node.false_value))
        if isinstance(node.false_value, Cond):
            false_value = ''.join(['\n', false_value])
        template_dict = {
            'cond': del_paren(self.visit(node.cond)),
            'true_value': true_value,
            'false_value': false_value,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Assign(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'left': self.visit(node.left),
            'right': self.visit(node.right),
        }
        rslt = template.render(template_dict)
        rslt = indent_multiline_assign(rslt)
        return rslt

    def visit_Always(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'sens_list': self.visit(node.sens_list),
            'statement': self.visit(node.statement),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_AlwaysFF(self, node):
        return self.visit_Always(node)

    def visit_AlwaysComb(self, node):
        return self.visit_Always(node)

    def visit_AlwaysLatch(self, node):
        return self.visit_Always(node)

    def visit_SensList(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        items = [self.visit(item) for item in node.items]
        template_dict = {
            'items': items,
            'len_items': len(items),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Sens(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'sig': '*' if node.type == 'all' else self.visit(node.sig),
            'type': node.type if node.type == 'posedge' or node.type == 'negedge' else ''
        }
        rslt = template.render(template_dict)
        return rslt

    def visit__Substitution(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'left': self.visit(node.left),
            'right': self.visit(node.right),
            'ldelay': '' if node.ldelay is None else self.visit(node.ldelay),
            'rdelay': '' if node.rdelay is None else self.visit(node.rdelay),
        }
        rslt = template.render(template_dict)
        rslt = indent_multiline_assign(rslt)
        return rslt

    def visit_BlockingSubstitution(self, node):
        return self.visit__Substitution(node)

    def visit_NonblockingSubstitution(self, node):
        return self.visit__Substitution(node)

    def visit__SubstitutionOperator(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        left = self.visit(node.left)
        right = self.visit(node.right)
        template_dict = {
            'left': left,
            'right': right,
            'ldelay': '' if node.ldelay is None else self.visit(node.ldelay),
            'rdelay': '' if node.rdelay is None else self.visit(node.rdelay),
            'op': op2mark(node.__class__.__name__),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_PlusEquals(self, node):
        return self.visit__SubstitutionOperator(node)

    def visit_MinusEquals(self, node):
        return self.visit__SubstitutionOperator(node)

    def visit_TimesEquals(self, node):
        return self.visit__SubstitutionOperator(node)

    def visit_DivideEquals(self, node):
        return self.visit__SubstitutionOperator(node)

    def visit_ModEquals(self, node):
        return self.visit__SubstitutionOperator(node)

    def visit_OrEquals(self, node):
        return self.visit__SubstitutionOperator(node)

    def visit_AndEquals(self, node):
        return self.visit__SubstitutionOperator(node)

    def visit_XorEquals(self, node):
        return self.visit__SubstitutionOperator(node)

    def visit_SlaEquals(self, node):
        return self.visit__SubstitutionOperator(node)

    def visit_SraEquals(self, node):
        return self.visit__SubstitutionOperator(node)

    def visit_SllEquals(self, node):
        return self.visit__SubstitutionOperator(node)

    def visit_SrlEquals(self, node):
        return self.visit__SubstitutionOperator(node)

    def visit_Increment(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        left = self.visit(node.left)
        template_dict = {
            'left': left,
            'op': op2mark(node.__class__.__name__),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Decrement(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        left = self.visit(node.left)
        template_dict = {
            'left': left,
            'op': op2mark(node.__class__.__name__),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_IfStatement(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        true_statement = '' if node.true_statement is None else self.visit(node.true_statement)
        false_statement = '' if node.false_statement is None else self.visit(node.false_statement)
        template_dict = {
            'cond': del_paren(self.visit(node.cond)),
            'true_statement': true_statement,
            'false_statement': false_statement,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_PriorityIf(self, node):
        return self.visit_IfStatement(node)

    def visit_ForStatement(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'pre': '' if node.pre is None else del_space(self.visit(node.pre)),
            'cond': '' if node.cond is None else del_space(del_paren(self.visit(node.cond))),
            'post': '' if node.post is None else del_space(self.visit(node.post).replace(';', '')),
            'statement': '' if node.statement is None else self.visit(node.statement),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_WhileStatement(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'cond': '' if node.cond is None else del_paren(self.visit(node.cond)),
            'statement': '' if node.statement is None else self.visit(node.statement),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_CaseStatement(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'comp': del_paren(self.visit(node.comp)),
            'caselist': [self.indent(self.visit(case)) for case in node.caselist],
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_CasexStatement(self, node):
        return self.visit_CaseStatement(node)

    def visit_CasezStatement(self, node):
        return self.visit_CaseStatement(node)

    def visit_UniqueCaseStatement(self, node):
        return self.visit_CaseStatement(node)

    def visit_Case(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        condlist = ['default'] if node.cond is None else [
            del_paren(self.visit(c)) for c in node.cond]
        cond = []
        for c in condlist:
            cond.append(c)
            cond.append(', ')
        template_dict = {
            'cond': ''.join(cond[:-1]),
            'statement': self.visit(node.statement),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Block(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'scope': '' if node.scope is None else escape(node.scope),
            'statements': [self.indent(self.visit(statement)) for statement in node.statements],
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Initial(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'statement': self.visit(node.statement),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_EventStatement(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'senslist': del_paren(self.visit(node.senslist)),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_WaitStatement(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'cond': del_paren(self.visit(node.cond)),
            'statement': self.visit(node.statement) if node.statement else '',
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_ForeverStatement(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'statement': self.visit(node.statement),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_DelayStatement(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'delay': self.visit(node.delay),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Instance(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        array = '' if node.array is None else self.visit(node.array)
        portlist = [self.indent(self.visit(port)) for port in node.portlist]
        template_dict = {
            'name': escape(node.name),
            'array': array,
            'portlist': portlist,
            'len_portlist': len(portlist),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_ParamArg(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'paramname': '' if node.paramname is None else escape(node.paramname),
            'argname': '' if node.argname is None else del_paren(self.visit(node.argname)),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_PortArg(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'portname': '' if node.portname is None else escape(node.portname),
            'argname': '' if node.argname is None else del_paren(self.visit(node.argname)),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Function(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        statement = [self.indent(self.visit(s)) for s in node.statement]
        template_dict = {
            'name': escape(node.name),
            'retwidth': self.visit(node.retwidth),
            'statement': statement,
            'automatic': node.automatic,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_FunctionCall(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        args = [self.visit(arg) for arg in node.args]
        template_dict = {
            'name': self.visit(node.name),
            'args': args,
            'len_args': len(args),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Task(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        statement = [self.indent(self.visit(s)) for s in node.statement]
        template_dict = {
            'name': escape(node.name),
            'statement': statement,
            'automatic': node.automatic,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Genvar(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name': escape(node.name),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_GenerateStatement(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'items': [self.visit(item) for item in node.items]
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_SystemCall(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        args = [self.visit(arg) for arg in node.args]
        template_dict = {
            'syscall': escape(node.syscall),
            'args': args,
            'len_args': len(args),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Pragma(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'entry': self.visit(node.entry),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_PragmaItem(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name': escape(node.name),
            'value': '' if node.value is None else self.visit(node.value),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Disable(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name': escape(node.dest),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_ParallelBlock(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'scope': '' if node.scope is None else escape(node.scope),
            'statements': [self.indent(self.visit(statement)) for statement in node.statements],
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_SingleStatement(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'statement': self.visit(node.statement),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Interface(self, node):
        return self.visit_Module(node)

    def visit_Modport(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        ports = self.indent(self._portlist(node.ports))
        template_dict = {
            'name': escape(node.name),
            'ports': ports,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Struct(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name': escape(node.name),
            'items': [self.indent(self.visit(item)) for item in node.items] if node.items else (),
            'packed': node.packed,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Union(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name': escape(node.name),
            'items': [self.indent(self.visit(item)) for item in node.items] if node.items else (),
            'packed': node.packed,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Enum(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        enumlist = self.indent(self.visit(node.enumlist)) if node.enumlist is not None else ''
        template_dict = {
            'name': escape(node.name),
            'enumlist': enumlist,
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_Enumlist(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        labels = [escape(l) for l, r in node.items] if node.items else ()
        rvalues = [(self.visit(r) if r is not None else None)
                   for l, r in node.items] if node.items else ()
        items = [('{} = {}'.format(l, r) if r is not None else l) for l, r in zip(labels, rvalues)]
        template_dict = {
            'items': items,
            'len_items': len(items),
            'name': '' if node.name is None else escape(node.name),
            'start': '' if node.start is None else escape(node.start),
            'end': '' if node.end is None else escape(node.end),
            'value': '' if node.value is None else escape(node.value),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_TypeDef(self, node):
        filename = getfilename(node)
        template = self.get_template(filename)
        template_dict = {
            'name': escape(node.name),
            'types': node.types,
            'width': '' if node.width is None else self.visit(node.width),
            'pdims': '' if node.pdims is None else self.visit(node.pdims),
            'udims': '' if node.udims is None else self.visit(node.udims),
        }
        rslt = template.render(template_dict)
        return rslt

    def visit_EmbeddedCode(self, node):
        return node.code
