#-------------------------------------------------------------------------------
# ast.py
# 
# Verilog HDL AST classes with Pyverilog
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------

import sys
import re

class Node(object):
    '''Abstact class for every element in parser'''
    coord = False
    def children(self):
        pass
    def show(self, buf=sys.stdout, offset=0, attrnames=False, showcoord=False):
        indent = 2
        lead = ' ' * offset
        buf.write(lead + self.__class__.__name__ + ': ')
        if self.attr_names:
            if attrnames:
                nvlist = [(n, getattr(self,n)) for n in self.attr_names]
                attrstr = ', '.join('%s=%s' & nv for nv in nvlist)
            else:
                vlist = [getattr(self,n) for n in self.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            buf.write(attrstr)
        if showcoord:
            buf.write(' (at %s)' % self.coord)
        buf.write('\n')
        for c in self.children():
            c.show(buf, offset + indent, attrnames, showcoord)
    def __eq__(self, other):
        if type(self) != type(other): return False
        self_attrs = tuple( [ getattr(self, a) for a in self.attr_names ] )
        other_attrs = tuple( [ getattr(other, a) for a in other.attr_names ] )
        if self_attrs != other_attrs: return False
        other_children = other.children()
        for i, c in enumerate(self.children()):
            if c != other_children[i]: return False
        return True
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        s = hash(tuple([getattr(self, a) for a in self.attr_names]))
        c = hash(self.children())
        return hash((s, c))
        
################################################################################
class Source(Node):
    attr_names = ('name',)
    def __init__(self, name, description):
        self.name = name
        self.description = description
    def children(self):
        nodelist = []
        if self.description: nodelist.append(self.description)
        return tuple(nodelist)

class Description(Node):
    attr_names = ()
    def __init__(self, definitions):
        self.definitions = definitions
    def children(self):
        nodelist = []
        if self.definitions: nodelist.extend(self.definitions)
        return tuple(nodelist)

class ModuleDef(Node):
    attr_names = ('name',)
    def __init__(self, name, paramlist, portlist, items, default_nettype='wire'):
        self.name = name
        self.paramlist = paramlist
        self.portlist = portlist
        self.items = items
        self.default_nettype = default_nettype
    def children(self):
        nodelist = []
        if self.paramlist: nodelist.append(self.paramlist)
        if self.portlist: nodelist.append(self.portlist)
        if self.items: nodelist.extend(self.items)
        return tuple(nodelist)

class Paramlist(Node):
    attr_names = ()
    def __init__(self, params):
        self.params = params
    def children(self):
        nodelist = []
        if self.params: nodelist.extend(self.params)
        return tuple(nodelist)

class Portlist(Node):
    attr_names = ()
    def __init__(self, ports):
        self.ports = ports
    def children(self):
        nodelist = []
        if self.ports: nodelist.extend(self.ports)
        return tuple(nodelist)

class Port(Node):
    attr_names = ('name','type',)
    def __init__(self, name, width, type):
        self.name = name
        self.width = width
        self.type = type
    def children(self):
        nodelist = []
        if self.width: nodelist.append(self.width)
        return tuple(nodelist)

class Width(Node):
    attr_names = ()
    def __init__(self, msb, lsb):
        self.msb = msb
        self.lsb = lsb
    def children(self):
        nodelist = []
        if self.msb: nodelist.append(self.msb)
        if self.lsb: nodelist.append(self.lsb)
        return tuple(nodelist)
class Length(Width): pass

class Identifier(Node):
    attr_names = ('name',)
    def __init__(self, name, scope=None):
        self.name = name
        self.scope = scope
    def children(self):
        nodelist = []
        if self.scope: nodelist.append(self.scope)
        return tuple(nodelist)
    def __repr__(self):
        if self.scope is None:
            return self.name
        return self.scope.__repr__() + '.' + self.name

class Value(Node):
    attr_names = ()
    def __init__(self, value):
        self.value = value
    def children(self):
        nodelist = []
        if self.value: nodelist.append(self.value)
        return tuple(nodelist)

class Constant(Value):
    attr_names = ('value',)
    def __init__(self, value):
        self.value = value
    def children(self):
        nodelist = []
        return tuple(nodelist)
    def __repr__(self):
        return str(self.value)

class IntConst(Constant): pass
class FloatConst(Constant): pass
class StringConst(Constant): pass

class Variable(Value):
    attr_names = ('name', 'signed')
    def __init__(self, name, width=None, signed=False):
        self.name = name
        self.width = width if width else Width(IntConst('0'),IntConst('0'))
        self.signed = signed
    def children(self):
        nodelist = []
        if self.width: nodelist.append(self.width)
        return tuple(nodelist)
        
class Input(Variable): pass
class Output(Variable): pass
class Inout(Variable): pass
class Tri(Variable): pass
class Wire(Variable): pass
class Reg(Variable): pass
class WireArray(Variable):
    attr_names = ('name', 'signed')
    def __init__(self, name, width, length, signed=False):
        self.name = name
        self.width = width
        self.length = length
        self.signed = signed
    def children(self):
        nodelist = []
        if self.width: nodelist.append(self.width)
        if self.length: nodelist.append(self.length)
        return tuple(nodelist)
class RegArray(Variable):
    attr_names = ('name', 'signed')
    def __init__(self, name, width, length, signed=False):
        self.name = name
        self.width = width
        self.length = length
        self.signed = signed
    def children(self):
        nodelist = []
        if self.width: nodelist.append(self.width)
        if self.length: nodelist.append(self.length)
        return tuple(nodelist)
class Integer(Variable): pass
class Real(Variable): pass
class Genvar(Variable): pass

class Ioport(Node):
    attr_names = ()
    def __init__(self, first, second=None):
        self.first = first
        self.second = second
    def children(self):
        nodelist = []
        if self.first: nodelist.append(self.first)
        if self.second: nodelist.append(self.second)
        return tuple(nodelist)

class Parameter(Node):
    attr_names = ('name', 'signed')
    def __init__(self, name, value, width=None, signed=False):
        self.name = name
        self.value = value
        self.width = width #if width else Width(msb=IntConst('31'),lsb=IntConst('0'))
        self.signed = signed
    def children(self):
        nodelist = []
        if self.value: nodelist.append(self.value)
        if self.width: nodelist.append(self.width)
        return tuple(nodelist)
class Localparam(Parameter): pass

class Decl(Node):
    attr_names = ()
    def __init__(self, list):
        self.list = list
    def children(self):
        nodelist = []
        if self.list: nodelist.extend(self.list)
        return tuple(nodelist)

class Concat(Node):
    attr_names = ()
    def __init__(self, list):
        self.list = list
    def children(self):
        nodelist = []
        if self.list: nodelist.extend(self.list)
        return tuple(nodelist)
class LConcat(Concat): pass

class Repeat(Node):
    attr_names = ()
    def __init__(self, value, times):
        self.value = value
        self.times = times
    def children(self):
        nodelist = []
        if self.value: nodelist.append(self.value)
        if self.times: nodelist.append(self.times)
        return tuple(nodelist)

class Partselect(Node):
    attr_names = ()
    def __init__(self, var, msb, lsb):
        self.var = var
        self.msb = msb
        self.lsb = lsb
    def children(self):
        nodelist = []
        if self.var: nodelist.append(self.var)
        if self.msb: nodelist.append(self.msb)
        if self.lsb: nodelist.append(self.lsb)
        return tuple(nodelist)

class Pointer(Node):
    attr_names = ()
    def __init__(self, var, ptr):
        self.var = var
        self.ptr = ptr
    def children(self):
        nodelist = []
        if self.var: nodelist.append(self.var)
        if self.ptr: nodelist.append(self.ptr)
        return tuple(nodelist)

class Lvalue(Node):
    attr_names = ()
    def __init__(self, var):
        self.var = var
    def children(self):
        nodelist = []
        if self.var: nodelist.append(self.var)
        return tuple(nodelist)

class Rvalue(Node):
    attr_names = ()
    def __init__(self, var):
        self.var = var
    def children(self):
        nodelist = []
        if self.var: nodelist.append(self.var)
        return tuple(nodelist)

################################################################################
class Operator(Node):
    attr_names = ()
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def children(self):
        nodelist = []
        if self.left: nodelist.append(self.left)
        if self.right: nodelist.append(self.right)
        return tuple(nodelist)
    def __repr__(self):
        ret = '('+self.__class__.__name__
        for c in self.children(): ret += ' ' + c.__repr__()
        ret += ')'
        return ret

class UnaryOperator(Operator):
    attr_names = ()
    def __init__(self, right):
        self.right = right
    def children(self):
        nodelist = []
        if self.right: nodelist.append(self.right)
        return tuple(nodelist)

################################################################################
# Level 1 (Highest Priority)
class Uplus(UnaryOperator): pass
class Uminus(UnaryOperator): pass
class Ulnot(UnaryOperator): pass
class Unot(UnaryOperator): pass
class Uand(UnaryOperator): pass
class Unand(UnaryOperator): pass
class Uor(UnaryOperator): pass
class Unor(UnaryOperator): pass
class Uxor(UnaryOperator): pass
class Uxnor(UnaryOperator): pass
################################################################################
# Level 2
class Power(Operator): pass
class Times(Operator): pass
class Divide(Operator): pass
class Mod(Operator): pass
################################################################################    
# Level 3
class Plus(Operator): pass
class Minus(Operator): pass
################################################################################    
# Level 4
class Sll(Operator): pass
class Srl(Operator): pass
class Sra(Operator): pass
################################################################################
# Level 5
class LessThan(Operator): pass
class GreaterThan(Operator): pass
class LessEq(Operator): pass
class GreaterEq(Operator): pass
################################################################################
# Level 6
class Eq(Operator): pass
class NotEq(Operator): pass
class Eql(Operator): pass # ===
class NotEql(Operator): pass # !==
################################################################################
# Level 7
class And(Operator): pass
class Xor(Operator): pass
class Xnor(Operator): pass
################################################################################
# Level 8
class Or(Operator): pass
################################################################################
# Level 9
class Land(Operator): pass
################################################################################
# Level 10
class Lor(Operator): pass
################################################################################
# Level 11
class Cond(Operator):
    attr_names = ()
    def __init__(self, cond, true_value, false_value):
        self.cond = cond
        self.true_value = true_value
        self.false_value = false_value
    def children(self):
        nodelist = []
        if self.cond: nodelist.append(self.cond)
        if self.true_value: nodelist.append(self.true_value)
        if self.false_value: nodelist.append(self.false_value)
        return tuple(nodelist)

################################################################################
class Assign(Node):
    attr_names = ()
    def __init__(self, left, right, ldelay=None, rdelay=None):
        self.left = left
        self.right = right
        self.ldelay = ldelay
        self.rdelay = rdelay
    def children(self):
        nodelist = []
        if self.left: nodelist.append(self.left)
        if self.right: nodelist.append(self.right)
        if self.ldelay: nodelist.append(self.ldelay)
        if self.rdelay: nodelist.append(self.rdelay)
        return tuple(nodelist)

class Always(Node):
    attr_names = ()
    def __init__(self, sens_list, statement):
        self.sens_list = sens_list
        self.statement = statement
    def children(self):
        nodelist = []
        if self.sens_list: nodelist.append(self.sens_list)
        if self.statement: nodelist.append(self.statement)
        return tuple(nodelist)

class SensList(Node):
    attr_names = ()
    def __init__(self, list):
        self.list = list
    def children(self):
        nodelist = []
        if self.list: nodelist.extend(self.list)
        return tuple(nodelist)

class Sens(Node):
    attr_names = ('type',)
    def __init__(self, sig, type='posedge'):
        self.sig = sig
        self.type = type # 'posedge', 'negedge', 'level', 'all' (*)
    def children(self):
        nodelist = []
        if self.sig: nodelist.append(self.sig)
        return tuple(nodelist)

class Substitution(Node):
    attr_names = ()
    def __init__(self, left, right, ldelay=None, rdelay=None):
        self.left = left
        self.right = right
        self.ldelay = ldelay
        self.rdelay = rdelay
    def children(self):
        nodelist = []
        if self.left: nodelist.append(self.left)
        if self.right: nodelist.append(self.right)
        if self.ldelay: nodelist.append(self.ldelay)
        if self.rdelay: nodelist.append(self.rdelay)
        return tuple(nodelist)
class BlockingSubstitution(Substitution): pass
class NonblockingSubstitution(Substitution): pass

class IfStatement(Node):
    attr_names = ()
    def __init__(self, cond, true_statement, false_statement):
        self.cond = cond
        self.true_statement = true_statement
        self.false_statement = false_statement
    def children(self):
        nodelist = []
        if self.cond: nodelist.append(self.cond)
        if self.true_statement: nodelist.append(self.true_statement)
        if self.false_statement: nodelist.append(self.false_statement)
        return tuple(nodelist)

class ForStatement(Node):
    attr_names = ()
    def __init__(self, pre, cond, post, statement):
        self.pre = pre
        self.cond = cond
        self.post = post
        self.statement = statement
    def children(self):
        nodelist = []
        if self.pre: nodelist.append(self.pre)
        if self.cond: nodelist.append(self.cond)
        if self.post: nodelist.append(self.post)
        if self.statement: nodelist.append(self.statement)
        return tuple(nodelist)

class WhileStatement(Node):
    attr_names = ()
    def __init__(self, cond, statement):
        self.cond = cond
        self.statement = statement
    def children(self):
        nodelist = []
        if self.cond: nodelist.append(self.cond)
        if self.statement: nodelist.append(self.statement)
        return tuple(nodelist)

class CaseStatement(Node):
    attr_names = ()
    def __init__(self, comp, caselist):
        self.comp = comp
        self.caselist = caselist
    def children(self):
        nodelist = []
        if self.comp: nodelist.append(self.comp)
        if self.caselist: nodelist.extend(self.caselist)
        return tuple(nodelist)

class Case(Node):
    attr_names = ()
    def __init__(self, cond, statement):
        self.cond = cond
        self.statement = statement
    def children(self):
        nodelist = []
        if self.cond: nodelist.extend(self.cond)
        if self.statement: nodelist.append(self.statement)
        return tuple(nodelist)

class Block(Node):
    attr_names = ('scope',)
    def __init__(self, statements, scope=None):
        self.statements = statements
        self.scope = scope
    def children(self):
        nodelist = []
        if self.statements: nodelist.extend(self.statements)
        return tuple(nodelist)

class Initial(Node):
    attr_names = ()
    def __init__(self, statement):
        self.statement = statement
    def children(self):
        nodelist = []
        if self.statement: nodelist.append(self.statement)
        return tuple(nodelist)

class EventStatement(Node): 
    attr_names = ()
    def __init__(self, senslist):
        self.senslist = senslist
    def children(self):
        nodelist = []
        if self.senslist: nodelist.append(self.senslist)
        return tuple(nodelist)

class WaitStatement(Node):
    attr_names = ()
    def __init__(self, cond, statement):
        self.cond = cond
        self.statement = statement
    def children(self):
        nodelist = []
        if self.cond: nodelist.append(self.cond)
        if self.statement: nodelist.append(self.statement)
        return tuple(nodelist)

class ForeverStatement(Node):
    attr_names = ()
    def __init__(self, statement):
        self.statement = statement
    def children(self):
        nodelist = []
        if self.statement: nodelist.append(self.statement)
        return tuple(nodelist)

class DelayStatement(Node):
    attr_names = ()
    def __init__(self, delay):
        self.delay = delay
    def children(self):
        nodelist = []
        if self.delay: nodelist.append(self.delay)
        return tuple(nodelist)

class Instance(Node):
    attr_names = ('name', 'module')
    def __init__(self, module, name, portlist, parameterlist):
        self.module = module
        self.name = name
        self.portlist = portlist
        self.parameterlist = parameterlist
    def children(self):
        nodelist = []
        if self.portlist: nodelist.extend(self.portlist)
        if self.parameterlist: nodelist.extend(self.parameterlist)
        return tuple(nodelist)

class ParamArg(Node):
    attr_names = ('paramname',)
    def __init__(self, paramname, argname):
        self.paramname = paramname
        self.argname = argname
    def children(self):
        nodelist = []
        if self.argname: nodelist.append(self.argname)
        return tuple(nodelist)

class PortArg(Node):
    attr_names = ('portname',)
    def __init__(self, portname, argname):
        self.portname = portname
        self.argname = argname
    def children(self):
        nodelist = []
        if self.argname: nodelist.append(self.argname)
        return tuple(nodelist)

class Function(Node):
    attr_names = ('name',)
    def __init__(self, name, retwidth, statement):
        self.name = name
        self.retwidth = retwidth
        self.statement = statement
    def children(self):
        nodelist = []
        if self.retwidth: nodelist.append(self.retwidth)
        if self.statement: nodelist.extend(self.statement)
        return tuple(nodelist)
    def __repr__(self):
        return self.name.__repr__()

class FunctionCall(Node):
    attr_names = ()
    def __init__(self, name, args):
        self.name = name
        self.args = args
    def children(self):
        nodelist = []
        if self.name: nodelist.append(self.name)
        if self.args: nodelist.extend(self.args)
        return tuple(nodelist)
    def __repr__(self):
        return self.name.__repr__()

class Task(Node):
    attr_names = ('name',)
    def __init__(self, name, statement):
        self.name = name
        self.statement = statement
    def children(self):
        nodelist = []
        if self.statement: nodelist.extend(self.statement)
        return tuple(nodelist)

#class TaskCall(Node):
#    attr_names = ()
#    def __init__(self, name, args):
#        self.name = name
#        self.args = args
#    def children(self):
#        nodelist = []
#        if self.name: nodelist.append(self.name)
#        if self.args: nodelist.extend(self.args)
#        return tuple(nodelist)

class GenerateStatement(Node):
    attr_names = ()
    def __init__(self, items):
        self.items = items
    def children(self):
        nodelist = []
        if self.items: nodelist.extend(self.items)
        return tuple(nodelist)

class SystemCall(Node):
    attr_names = ('syscall',)
    def __init__(self, syscall, args):
        self.syscall = syscall
        self.args = args
    def children(self):
        nodelist = []
        if self.args: nodelist.extend(self.args)
        return tuple(nodelist)
    def __repr__(self):
        ret = []
        ret.append('(')
        ret.append('$')
        ret.append(self.syscall)
        for a in self.args:
            ret.append(' ')
            ret.append(str(a))
        ret.append(')')
        return ''.join(ret)

class IdentifierScopeLabel(Node):
    attr_names = ('name', 'loop')
    def __init__(self, name, loop=None):
        self.name = name
        self.loop = loop
    def children(self):
        nodelist = []
        return tuple(nodelist)

class IdentifierScope(Node):
    attr_names = ()
    def __init__(self, labellist):
        self.labellist = labellist
    def children(self):
        nodelist = []
        if self.labellist: nodelist.extend(self.labellist)
        return tuple(nodelist)

class Pragma(Node):
    attr_names = ()
    def __init__(self, entry):
        self.entry = entry
    def children(self):
        nodelist = []
        if self.entry: nodelist.append(self.entry)
        return tuple(nodelist)

class PragmaEntry(Node):
    attr_names = ('name', )
    def __init__(self, name, value=None):
        self.name = name
        self.value = value
    def children(self):
        nodelist = []
        if self.value: nodelist.append(self.value)
        return tuple(nodelist)

class Disable(Node):
    attr_names = ('dest',)
    def __init__(self, dest):
        self.dest = dest
    def children(self):
        nodelist = []
        return tuple(nodelist)

class ParallelBlock(Node):
    attr_names = ('scope',)
    def __init__(self, statements, scope=None):
        self.statements = statements
        self.scope = scope
    def children(self):
        nodelist = []
        if self.statements: nodelist.extend(self.statements)
        return tuple(nodelist)

class SingleStatement(Node):
    attr_names = ()
    def __init__(self, statement):
        self.statement = statement
    def children(self):
        nodelist = []
        if self.statement: nodelist.append(self.statement)
        return tuple(nodelist)

