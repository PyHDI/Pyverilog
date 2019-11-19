# -------------------------------------------------------------------------------
# dataflow.py
#
# Basic classes of Data flow nodes
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# Contributor: ryosuke fukatani
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import re
import copy

dfnodelist = ('DFIntConst', 'DFFloatConst', 'DFStringConst',
              'DFEvalValue', 'DFUndefined', 'DFHighImpedance',
              'DFTerminal',
              'DFBranch', 'DFOperator', 'DFPartselect', 'DFPointer',
              'DFConcat', 'DFDelay', 'DFSyscall')


def printIndent(s, indent=4):
    print((' ' * indent) + s)


def generateWalkTree(offset=1):
    base_indent = 4
    printIndent('def walkTree(tree):', base_indent * (0 + offset))
    for df in dfnodelist:
        printIndent('if isinstance(tree, %s):' % df, base_indent * (1 + offset))
        printIndent('pass', base_indent * (2 + offset))


if __name__ == '__main__':
    generateWalkTree()
    exit()

import pyverilog.utils.verror as verror
import pyverilog.utils.util as util
import pyverilog.utils.signaltype as signaltype
import pyverilog.utils.op2mark as op2mark


class DFNode(object):
    attr_names = ()

    def __init__(self): pass

    def __repr__(self): pass

    def tostr(self): pass

    def tocode(self, dest='dest'): return self.__repr__()

    def tolabel(self): return self.__repr__()

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return id(self)


class DFTerminal(DFNode):
    attr_names = ('name',)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        ret = ''
        for n in self.name:
            ret += str(n) + '.'
        return ret[:-1]

    def tostr(self):
        ret = '(Terminal '
        for n in self.name:
            ret += str(n) + '.'
        return ret[0:-1] + ')'

    def tocode(self, dest='dest'):
        # ret = ''
        # for n in self.name:
        #    ret += n.tocode() + '__'
        # return ret[:-2]
        return self.name.tocode()

    def tolabel(self):
        return self.tocode()

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class DFConstant(DFNode):
    attr_names = ('value',)

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return str(self.value)

    def tostr(self):
        ret = '(Constant ' + str(self.value) + ')'
        return ret

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def eval(self):
        return None

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)


class DFIntConst(DFConstant):
    def __init__(self, value):
        self.value = value

    def tostr(self):
        ret = '(IntConst ' + str(self.value) + ')'
        return ret

    def eval(self):
        targ = self.value.replace('_', '')
        signed = False
        match = re.search(r'[Ss](.+)', targ)
        if match is not None:
            signed = True
        match = re.search(r'[Hh](.+)', targ)
        if match is not None:
            return int(match.group(1), 16)
        match = re.search(r'[Dd](.+)', targ)
        if match is not None:
            return int(match.group(1), 10)
        match = re.search(r'[Oo](.+)', targ)
        if match is not None:
            return int(match.group(1), 8)
        match = re.search(r'[Bb](.+)', targ)
        if match is not None:
            return int(match.group(1), 2)
        return int(targ, 10)

    def width(self):
        targ = self.value.replace('_', '')
        match = re.search(r'(.+)\'[Hh].+', targ)
        if match is not None:
            return int(match.group(1), 10)
        match = re.search(r'(.+)\'[Dd].+', targ)
        if match is not None:
            return int(match.group(1), 10)
        match = re.search(r'(.+)\'[Oo].+', targ)
        if match is not None:
            return int(match.group(1), 10)
        match = re.search(r'(.+)\'[Bb].+', targ)
        if match is not None:
            return int(match.group(1), 10)
        return 32


class DFFloatConst(DFConstant):
    def __init__(self, value):
        self.value = value

    def tostr(self):
        ret = '(FloatConst ' + str(self.value) + ')'
        return ret

    def eval(self):
        return float(self.value)


class DFStringConst(DFConstant):
    def __init__(self, value):
        self.value = value

    def tostr(self):
        ret = '(StringConst ' + str(self.value) + ')'
        return ret

    def eval(self):
        return self.value


class DFNotTerminal(DFNode):
    pass


class DFOperator(DFNotTerminal):
    attr_names = ('operator',)

    def __init__(self, nextnodes, operator):
        self.nextnodes = nextnodes
        self.operator = operator

        for n in nextnodes:
            if n is None:
                raise verror.DefinitionError()

    def __repr__(self):
        return self.operator

    def tostr(self):
        ret = '(Operator ' + self.operator
        ret += ' Next:'
        for n in self.nextnodes:
            ret += n.tostr() + ','
        ret = ret[0:-1] + ')'
        return ret

    def tocode(self, dest='dest'):
        ret = ''
        if len(self.nextnodes) > 1:
            ret += '(' + self.nextnodes[0].tocode(dest)
            ret += op2mark.op2mark(self.operator)
            ret += self.nextnodes[1].tocode(dest) + ')'
        else:
            ret += '(' + op2mark.op2mark(self.operator)
            ret += self.nextnodes[0].tocode(dest) + ')'
        return ret

    def children(self):
        nodelist = []
        if self.nextnodes is not None:
            nodelist.extend(self.nextnodes)
        return tuple(nodelist)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.operator == other.operator and self.nextnodes == other.nextnodes

    def __hash__(self):
        return hash((self.operator, tuple(self.nextnodes)))


class DFPartselect(DFNotTerminal):
    attr_names = ()

    def __init__(self, var, msb, lsb):
        self.var = var
        self.msb = msb
        self.lsb = lsb

    def __repr__(self):
        return 'PartSelect'

    def tostr(self):
        ret = '(Partselect'
        ret += ' Var:' + self.var.tostr()
        ret += ' MSB:' + self.msb.tostr()
        ret += ' LSB:' + self.lsb.tostr()
        ret += ')'
        return ret

    def tocode(self, dest='dest'):
        ret = self.var.tocode(dest)
        msbcode = self.msb.tocode(dest)
        lsbcode = self.lsb.tocode(dest)
        if msbcode == lsbcode:
            ret += '[' + msbcode + ']'
        else:
            ret += '[' + msbcode
            ret += ':' + lsbcode + ']'
        return ret

    def children(self):
        nodelist = []
        if self.var is not None:
            nodelist.append(self.var)
        if self.msb is not None:
            nodelist.append(self.msb)
        if self.lsb is not None:
            nodelist.append(self.lsb)
        return tuple(nodelist)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.var == other.var and self.msb == other.msb and self.lsb == other.lsb

    def __hash__(self):
        return hash((self.var, self.msb, self.lsb))


class DFPointer(DFNotTerminal):
    attr_names = ()

    def __init__(self, var, ptr):
        self.var = var
        self.ptr = ptr

    def __repr__(self):
        return 'Pointer'

    def tostr(self):
        ret = '(Pointer'
        ret += ' Var:' + self.var.tostr()
        ret += ' PTR:' + self.ptr.tostr()
        ret += ')'
        return ret

    def tocode(self, dest='dest'):
        ret = self.var.tocode(dest)
        ret += '[' + self.ptr.tocode(dest) + ']'
        return ret

    def children(self):
        nodelist = []
        if self.var is not None:
            nodelist.append(self.var)
        if self.ptr is not None:
            nodelist.append(self.ptr)
        return tuple(nodelist)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.var == other.var and self.ptr == other.ptr

    def __hash__(self):
        return hash((self.var, self.ptr))


class DFConcat(DFNotTerminal):
    attr_names = ()

    def __init__(self, nextnodes):
        self.nextnodes = nextnodes

    def __repr__(self):
        return 'Concat'

    def tostr(self):
        ret = '(Concat'
        ret += ' Next:'
        for n in self.nextnodes:
            ret += n.tostr() + ','
        ret = ret[0:-1] + ')'
        return ret

    def tocode(self, dest='dest'):
        ret = '{'
        for n in self.nextnodes:
            ret += n.tocode(dest) + ','
        ret = ret[:-1]
        ret += '}'
        return ret

    def children(self):
        nodelist = []
        if self.nextnodes is not None:
            nodelist.extend(self.nextnodes)
        return tuple(nodelist)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.nextnodes == other.nextnodes

    def __hash__(self):
        return hash(tuple(self.nextnodes))


class DFBranch(DFNotTerminal):
    attr_names = ()

    def __init__(self, condnode, truenode, falsenode):
        self.condnode = condnode
        self.truenode = truenode
        self.falsenode = falsenode

    def __repr__(self):
        return 'Branch'

    def tostr(self):
        ret = '(Branch'
        if self.condnode is not None:
            ret += ' Cond:' + self.condnode.tostr()
        if self.truenode is not None:
            ret += ' True:' + self.truenode.tostr()
        if self.falsenode is not None:
            ret += ' False:' + self.falsenode.tostr()
        ret += ')'
        return ret

    def tocode(self, dest='dest', always=''):
        if always == 'clockedge':
            return self._tocode_always(dest, always)
        if always == 'combination':
            return self._tocode_always(dest, always)
        ret = '('
        if self.condnode is not None:
            ret += '(' + self.condnode.tocode(dest) + ')'
        ret += '? '
        if self.truenode is not None:
            ret += self.truenode.tocode(dest)
        else:
            ret += dest
        ret += " : "
        if self.falsenode is not None:
            ret += self.falsenode.tocode(dest)
        else:
            ret += dest
        ret += ")"
        return ret

    def _tocode_always(self, dest='dest', always='clockedge'):
        ret = 'if('
        if self.condnode is not None:
            ret += self.condnode.tocode(dest)
        ret += ') begin\n'
        if self.truenode is not None:
            if isinstance(self.truenode, DFBranch):
                ret += self.truenode.tocode(dest, always=always)
            elif always == 'clockedge':
                ret += dest + ' <= ' + self.truenode.tocode(dest) + ';\n'
            elif always == 'combination':
                ret += dest + ' = ' + self.truenode.tocode(dest) + ';\n'
        ret += 'end\n'
        if self.falsenode is not None:
            ret += 'else begin\n'
            if isinstance(self.falsenode, DFBranch):
                ret += self.falsenode.tocode(dest, always=always)
            elif always == 'clockedge':
                ret += dest + ' <= ' + self.falsenode.tocode(dest) + ';\n'
            elif always == 'combination':
                ret += dest + ' = ' + self.falsenode.tocode(dest) + ';\n'
            ret += 'end\n'
        return ret

    def children(self):
        nodelist = []
        if self.truenode is not None:
            nodelist.append(self.truenode)
        if self.condnode is not None:
            nodelist.append(self.condnode)
        if self.falsenode is not None:
            nodelist.append(self.falsenode)
        return tuple(nodelist)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return (self.condnode == other.condnode
                and self.truenode == other.truenode
                and self.falsenode == other.falsenode)

    def __hash__(self):
        return hash((self.condnode, self.truenode, self.falsenode))


class DFEvalValue(DFNode):
    attr_names = ('value', 'width',)

    def __init__(self, value, width=32, isfloat=False, isstring=False):
        self.value = value
        self.width = width
        self.isfloat = isfloat
        self.isstring = isstring

    def __repr__(self):
        if self.isstring:
            return self.value
        ret = ''
        if self.value < 0:
            ret += '(-'
        if self.width != 32:
            ret += str(self.width)
        ret += "'d"
        ret += str(abs(self.value))
        if self.value < 0:
            ret += ')'
        return ret

    def tostr(self):
        if self.isstring:
            return self.value
        ret = ''
        if self.value < 0:
            ret += '(-'
        if self.width != 32:
            ret += str(self.width)
        ret += "'d"
        ret += str(abs(self.value))
        if self.value < 0:
            ret += ')'
        return ret

    def tocode(self, dest='dest'):
        return self.__repr__()

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def eval(self):
        return self.value

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return (self.value == other.value
                and self.width == other.width
                and self.isfloat == other.isfloat
                and self.isstring == other.isstring)

    def __hash__(self):
        return hash((self.value, self.width, self.isfloat, self.isstring))


class DFUndefined(DFNode):
    attr_names = ('width',)

    def __init__(self, width):
        self.width = width

    def __repr__(self):
        ret = ''
        if self.width != 32:
            ret += str(self.width)
        ret += "'d"
        ret += 'x'
        return ret

    def tostr(self):
        ret = ''
        if self.width != 32:
            ret += str(self.width)
        ret += "'d"
        ret += 'x'
        return ret

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.width == other.width

    def __hash__(self):
        return hash(self.width)


class DFHighImpedance(DFNode):
    attr_names = ('width',)

    def __init__(self, width):
        self.width = width

    def __repr__(self):
        ret = ''
        if self.width != 32:
            ret += str(self.width)
        ret += "'d"
        ret += 'z'
        return ret

    def tostr(self):
        ret = ''
        if self.width != 32:
            ret += str(self.width)
        ret += "'d"
        ret += 'z'
        return ret

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.width == other.width

    def __hash__(self):
        return hash(self.width)


class DFDelay(DFNotTerminal):
    attr_names = ()

    def __init__(self, nextnode):
        self.nextnode = nextnode

    def __repr__(self):
        return 'Delay'

    def tostr(self):
        ret = '(Delay '
        if self.nextnode is not None:
            ret += self.nextnode.tostr()
        ret += ')'
        return ret

    def tocode(self, dest='dest'):
        raise verror.DefinitionError('DFDelay does not support tocode()')

    def children(self):
        nodelist = []
        if self.nextnode is not None:
            nodelist.append(self.nextnode)
        return tuple(nodelist)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.nextnodes == other.nextnodes

    def __hash__(self):
        return hash(tuple(self.nextnodes))


class DFSyscall(DFNotTerminal):
    attr_names = ()

    def __init__(self, syscall, nextnodes):
        self.syscall = syscall
        self.nextnodes = nextnodes

    def __repr__(self):
        return 'Syscall'

    def tostr(self):
        ret = '(Syscall '
        ret += self.syscall
        ret += ' Next:'
        for n in self.nextnodes:
            ret += n.tostr() + ','
        ret = ret[0:-1] + ')'
        return ret

    def tocode(self, dest='dest'):
        ret = '$' + self.syscall + '('
        for n in self.nextnodes:
            ret += n.tocode(dest) + ','
        ret = ret[:-1]
        ret += ')'
        return ret

    def children(self):
        nodelist = []
        if self.nextnodes is not None:
            nodelist.extend(self.nextnodes)
        return tuple(nodelist)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if self.syscall != other.syscall:
            return False
        return self.nextnodes == other.nextnodes

    def __hash__(self):
        return hash(tuple(self.nextnodes))


class Term(object):
    def __init__(self, name, termtype=(), msb=None, lsb=None, dims=None):
        self.name = name  # tuple (str)
        self.termtype = termtype  # set (str)
        self.msb = msb  # DFNode
        self.lsb = lsb  # DFNode
        self.dims = dims  # tuple/list of pair of DFNode

    def __repr__(self):
        return str(self.name)

    def tostr(self):
        ret = '(Term name:' + str(self.name) + ' type:' + \
            str(sorted(self.termtype, key=lambda x: str(x)))
        if self.msb is not None:
            ret += ' msb:' + self.msb.tostr()
        if self.lsb is not None:
            ret += ' lsb:' + self.lsb.tostr()
        if self.dims is not None:
            ret += ' dims:'
            ret += ''.join(['[' + l.tostr() + ':' + r.tostr() + ']'
                            for l, r in self.dims])
        ret += ')'
        return ret

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return (self.name == other.name
                and self.termtype == other.termtype
                and self.msb == other.msb
                and self.lsb == other.lsb
                and self.dims == other.dims)

    def __hash__(self):
        return hash((self.name, self.termtype, self.msb, self.lsb, self.dims))

    def getScope(self, termname):
        return termname[:-1]

    def isTopmodule(self, scope):
        if len(scope) == 1:
            return True
        return False

    def tocode(self):
        flatname = util.toFlatname(self.name)
        scope = self.getScope(self.name)
        code = ''
        if self.isTopmodule(scope):
            if signaltype.isInput(self.termtype):
                code += 'input '
            elif signaltype.isInout(self.termtype):
                code += 'inout '
            elif signaltype.isOutput(self.termtype):
                code += 'output '
        else:
            if signaltype.isInput(self.termtype):
                code += 'wire '
            elif signaltype.isInout(self.termtype):
                code += 'wire '
            elif signaltype.isOutput(self.termtype) and not signaltype.isReg(self.termtype):
                code += 'wire '

        if signaltype.isReg(self.termtype):
            code += 'reg '
        if signaltype.isWire(self.termtype):
            code += 'wire '
        if signaltype.isInteger(self.termtype):
            code += 'integer '
        if signaltype.isFunction(self.termtype):
            code += 'wire '
        if signaltype.isRename(self.termtype):
            code += 'wire '

        if (not signaltype.isInteger(self.termtype)
                and self.msb is not None and self.lsb is not None):
            code += '[' + self.msb.tocode(None) + ':' + self.lsb.tocode(None) + '] '
        code += flatname  # signal name
        if self.dims is not None:
            code += ''.join(['[' + l.tocode() + ':' + r.tocode() + ']'
                             for l, r in self.dims])
        code += ';\n'
        return code


class Bind(object):
    def __init__(self, tree, dest, msb=None, lsb=None, ptr=None,
                 alwaysinfo=None, parameterinfo=''):
        self.tree = tree
        self.dest = dest
        self.msb = msb
        self.lsb = lsb
        self.ptr = ptr
        self.alwaysinfo = alwaysinfo
        self.parameterinfo = parameterinfo
        if dest is None:
            raise verror.DefinitionError('Bind dest is empty')

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return (self.tree == other.tree and
                self.dest == other.dest
                and self.msb == other.msb
                and self.lsb == other.lsb
                and self.ptr == other.ptr
                and self.alwaysinfo == other.alwaysinfo
                and self.parameterinfo == other.parameterinfo)

    def __hash__(self):
        return hash((self.tree, self.dest, self.msb, self.lsb, self.ptr,
                     self.alwaysinfo, self.parameterinfo))

    def isCombination(self):
        if self.alwaysinfo is None:
            return True
        if self.alwaysinfo.isCombination():
            return True
        return False

    def tostr(self):
        ret = '(Bind'
        if self.dest is not None:
            ret += ' dest:' + str(self.dest)
        if self.msb is not None:
            ret += ' msb:' + self.msb.tostr()
        if self.lsb is not None:
            ret += ' lsb:' + self.lsb.tostr()
        if self.ptr is not None:
            ret += ' ptr:' + self.ptr.tostr()
        if self.tree is not None:
            ret += ' tree:' + self.tree.tostr()
        ret += ')'
        return ret

    def tocode(self):
        if self.parameterinfo == 'parameter':
            return self._parameter()
        if self.parameterinfo == 'localparam':
            return self._localparam()
        if self.alwaysinfo is None:
            return self._assign()
        if self.alwaysinfo.isCombination():
            return self._always_combination()
        else:
            return self._always_clockedge()

    def getdest(self):
        dest = util.toFlatname(self.dest)
        if self.ptr is not None:
            dest += '[' + self.ptr.tocode(None) + ']'
        if self.msb is not None and self.lsb is not None:
            msbcode = self.msb.tocode(None)
            lsbcode = self.lsb.tocode(None)
            if msbcode == lsbcode:
                dest += '[' + msbcode + ']'
            else:
                dest += '[' + msbcode + ':' + lsbcode + ']'
        return dest

    def _parameter(self):
        dest = self.getdest()
        code = 'parameter ' + dest
        code += ' = ' + self.tree.tocode(dest) + ';\n'
        return code

    def _localparam(self):
        dest = self.getdest()
        code = 'localparam ' + dest
        code += ' = ' + self.tree.tocode(dest) + ';\n'
        return code

    def _assign(self):
        dest = self.getdest()
        code = 'assign ' + dest
        code += ' = ' + self.tree.tocode(dest) + ';\n'
        return code

    def _always_clockedge(self):
        dest = self.getdest()
        code = 'always @('
        if self.alwaysinfo.clock_edge is not None and self.alwaysinfo.clock_name is not None:
            code += self.alwaysinfo.clock_edge + ' '
            code += util.toFlatname(self.alwaysinfo.clock_name)
        if self.alwaysinfo.reset_edge is not None and self.alwaysinfo.reset_name is not None:
            code += ' or '
            code += self.alwaysinfo.reset_edge + ' '
            code += util.toFlatname(self.alwaysinfo.reset_name)
        code += ') begin\n'
        if isinstance(self.tree, DFBranch):
            code += self.tree.tocode(dest, always='clockedge')
        else:
            code += dest
            code += ' <= ' + self.tree.tocode(dest) + ';\n'
        code += 'end\n'
        code += '\n'
        return code

    def _always_combination(self):
        dest = self.getdest()
        code = ''
        code += 'always @*'
        code += ' begin\n'
        if isinstance(self.tree, DFBranch):
            code += self.tree.tocode(dest, always='combination')
        else:
            code += dest
            code += ' = ' + self.tree.tocode(dest) + ';\n'
        code += 'end\n'
        code += '\n'
        return code

    def isClockEdge(self):
        if self.alwaysinfo is None:
            return False
        return self.alwaysinfo.isClockEdge()

    def getClockName(self):
        if self.alwaysinfo is None:
            return ''
        return self.alwaysinfo.getClockName()

    def getClockEdge(self):
        if self.alwaysinfo is None:
            return ''
        return self.alwaysinfo.getClockEdge()

    def getClockBit(self):
        if self.alwaysinfo is None:
            return ''
        return self.alwaysinfo.getClockBit()

    def getResetName(self):
        if self.alwaysinfo is None:
            return ''
        return self.alwaysinfo.getResetName()

    def getResetEdge(self):
        if self.alwaysinfo is None:
            return ''
        return self.alwaysinfo.getResetEdge()

    def getResetBit(self):
        if self.alwaysinfo is None:
            return ''
        return self.alwaysinfo.getResetBit()

    def getSenslist(self):
        if self.alwaysinfo is None:
            return ''
        return self.alwaysinfo.getSenslist()


class DataFlow(object):
    def __init__(self):
        self.terms = {}
        self.binddict = {}

        self.functions = {}
        self.function_ports = {}
        self.tasks = {}
        self.task_ports = {}
        self.temporal_value = {}

    def addTerm(self, name, term):
        if not name in self.terms:
            self.terms[name] = term
        else:
            self.setTerm(name, term)

    def setTerm(self, name, term):
        self.terms[name].termtype |= term.termtype
        if self.terms[name].msb is None:
            self.terms[name].msb = term.msb
        if self.terms[name].lsb is None:
            self.terms[name].lsb = term.lsb
        if self.terms[name].dims is None:
            self.terms[name].dims = term.dims

    def hasTerm(self, name):
        return name in self.terms

    def getTerm(self, name):
        if name in self.terms:
            return self.terms[name]
        return None

    def getTerms(self):
        return self.terms

    def addBind(self, name, bind):
        if name is None:
            raise verror.DefinitionError('Bind name is empty')
        if not name in self.binddict:
            self.binddict[name] = [bind, ]
        else:
            self.setBind(name, bind)

    def setBind(self, name, bind):
        if name is None:
            raise verror.DefinitionError('Bind name is empty')
        currentbindlist = self.binddict[name]
        c_i = 0
        for c in currentbindlist:
            if c.msb == bind.msb and c.lsb == bind.lsb and c.ptr == bind.ptr:
                self.binddict[name][c_i].tree = bind.tree
                return
            c_i += 1
        self.binddict[name] = currentbindlist + [bind, ]

    def getBindlist(self, name):
        if name in self.binddict:
            return tuple(self.binddict[name])
        return ()

    def getBinddict(self):
        return self.binddict

    def addFunction(self, name, definition):
        self.functions[name] = definition

    def hasFunction(self, name):
        return name in self.functions

    def getFunction(self, name):
        if name in self.functions:
            return self.functions[name]
        return None

    def addFunctionPorts(self, name, ports):
        self.function_ports[name] = ports

    def getFunctionPorts(self, name):
        if name in self.function_ports:
            return self.function_ports[name]
        return ()

    def addTask(self, name, definition):
        self.tasks[name] = definition

    def hasTask(self, name):
        return name in self.tasks

    def getTask(self, name):
        if name in self.tasks:
            return self.tasks[name]
        return None

    def addTaskPorts(self, name, ports):
        self.task_ports[name] = ports

    def getTaskPorts(self, name):
        if name in self.task_ports:
            return self.task_ports[name]
        return ()

    def setTemporalValue(self, name, value):
        self.temporal_value[name] = value

    def getTemporalValue(self, name):
        return self.temporal_value[name]
