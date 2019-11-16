# -------------------------------------------------------------------------------
# visit.py
#
# Basic classes for binding tree analysis
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import re
import copy
import collections

import pyverilog
import pyverilog.utils.util as util
import pyverilog.utils.verror as verror
from pyverilog.utils.scope import ScopeLabel, ScopeChain
from pyverilog.vparser.ast import *


def map_key(f, d): return collections.OrderedDict([(f(k), v) for k, v in d.items()])


def map_value(f, d): return collections.OrderedDict([(k, f(v)) for k, v in d.items()])


# Primitive list
primitives = {
    'and': Uand,
    'nand': Unand,
    'or': Uor,
    'nor': Unor,
    'xor': Uxor,
    'xnor': Uxnor,
    'not': Unot,
    'buf': None
}


# Base Visitor
class NodeVisitor(object):
    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        for c in node.children():
            self.visit(c)


# Signal/Object Management Classes
class AlwaysInfo(object):
    def __init__(self, clock_name='', clock_edge=None, clock_bit=0,
                 reset_name='', reset_edge=None, reset_bit=0, senslist=()):
        self.clock_name = clock_name
        self.clock_edge = clock_edge
        self.clock_bit = clock_bit
        self.reset_name = reset_name
        self.reset_edge = reset_edge
        self.reset_bit = reset_bit
        self.senslist = senslist

    def getClockName(self):
        return self.clock_name

    def getClockEdge(self):
        return self.clock_edge

    def getClockBit(self):
        return self.clock_bit

    def getResetName(self):
        return self.reset_name

    def getResetEdge(self):
        return self.reset_edge

    def getResetBit(self):
        return self.reset_bit

    def isClockEdge(self):
        if self.clock_name != '' and self.clock_edge == 'posedge':
            return True
        if self.clock_name != '' and self.clock_edge == 'negedge':
            return True
        return False

    def isCombination(self):
        if self.clock_name is None:
            return True
        return False

    def isResetEdge(self):
        if self.reset_name != '' and self.reset_edge == 'posedge':
            return True
        if self.reset_name != '' and self.reset_edge == 'negedge':
            return True
        return False


class Label(object):
    def __init__(self, name):
        self.name = name
        self.cnt = 0

    def get(self):
        ret = self.name + str(self.cnt)
        self.inc()
        return ret

    def inc(self):
        self.cnt += 1


class Labels(object):
    def __init__(self):
        self.labels = {}

    def get(self, name):
        if not name in self.labels:
            self.labels[name] = Label(name)
        return self.labels[name].get()

    def inc(self, name):
        if not name in self.labels:
            self.labels[name] = Label(name)
        self.labels[name].inc()


class VariableTable(object):
    def __init__(self):
        self.dict = collections.OrderedDict()

    def add(self, name, var):
        if name in self.dict:
            self.dict[name] = self.dict[name] + (var, )
        else:
            self.dict[name] = (var, )

    def get(self, name):
        return self.dict[name]

    def has(self, name):
        return name in self.dict

    def update(self, table):
        self.dict.update(table)

    def getDict(self):
        return self.dict


class SignalTable(VariableTable):
    pass


class ConstTable(VariableTable):
    pass


class GenvarTable(VariableTable):
    pass


class Variables(object):
    def __init__(self):
        self.signal = SignalTable()
        self.const = ConstTable()
        self.genvar = GenvarTable()

    def addSignal(self, name, var):
        if self.const.has(name):
            return
        self.signal.add(name, var)

    def addConst(self, name, var):
        if self.const.has(name):
            return
        self.const.add(name, var)

    def addGenvar(self, name, var):
        if self.const.has(name):
            return
        self.genvar.add(name, var)

    def getSignal(self, name):
        return self.signal.get(name)

    def getConst(self, name):
        return self.const.get(name)

    def getGenvar(self, name):
        return self.genvar.get(name)

    def hasSignal(self, name):
        return self.signal.has(name)

    def hasConst(self, name):
        return self.const.has(name)

    def updateSignal(self, var):
        self.signal.update(var)

    def updateConst(self, var):
        self.const.update(var)

    def getSignals(self):
        return self.signal.getDict()

    def getConsts(self):
        return self.const.getDict()


class DefinitionInfo(object):
    def __init__(self, name, definition):
        self.name = name
        self.definition = definition
        self.variables = Variables()
        self.ioports = []
        self.params = []

    def addSignal(self, name, var):
        self.variables.addSignal(name, var)

    def addConst(self, name, var):
        self.variables.addConst(name, var)

    def addParamName(self, name):
        self.params.append(name)

    def addPort(self, port):
        self.ioports.append(port)

    def addPorts(self, ports):
        for p in ports:
            if isinstance(p, Ioport):
                self.ioports.append(p.first.name)
            else:
                self.ioports.append(p.name)

    def getSignals(self):
        return self.variables.getSignals()

    def getConsts(self):
        return self.variables.getConsts()

    def getDefinition(self):
        return self.definition

    def getIOPorts(self):
        return tuple(self.ioports)

    def getParamNames(self):
        return tuple(self.params)


class DefinitionInfoTable(object):
    def __init__(self):
        self.dict = collections.OrderedDict()
        self.current = None

    def addDefinition(self, name, definition):
        if name in self.dict:
            raise verror.DefinitionError('Already defined: %s' % name)
        self.dict[name] = DefinitionInfo(name, definition)
        self.current = name

    def addPorts(self, ports):
        self.dict[self.current].addPorts(ports)

    def addPort(self, port):
        self.dict[self.current].addPort(port)

    def addSignal(self, name, var):
        self.dict[self.current].addSignal(name, var)

    def addConst(self, name, var):
        self.dict[self.current].addConst(name, var)

    def addParamName(self, name):
        self.dict[self.current].addParamName(name)

    def getSignals(self, name):
        if name not in self.dict:
            raise verror.DefinitionError('No such module: %s' % name)
        return self.dict[name].getSignals()

    def getConsts(self, name):
        if name not in self.dict:
            raise verror.DefinitionError('No such module: %s' % name)
        return self.dict[name].getConsts()

    def getDefinition(self, name):
        if name not in self.dict:
            raise verror.DefinitionError('No such module: %s' % name)
        return self.dict[name].getDefinition()

    def getDefinitions(self):
        return self.dict

    def getIOPorts(self, name):
        if name not in self.dict:
            raise verror.DefinitionError('No such module: %s' % name)
        return self.dict[name].getIOPorts()

    def getParamNames(self, name):
        if name not in self.dict:
            raise verror.DefinitionError('No such module: %s' % name)
        return self.dict[name].getParamNames()

    def get_names(self):
        ret = []
        for dk, dv in self.dict.items():
            ret.append(dk)
        return ret

    def overwriteDefinition(self, name, definition):
        self.dict[name] = definition

    def copyDefinition(self, f, t):
        self.dict[t] = copy.deepcopy(self.dict[f])
        self.dict[t].definition.name = t
        self.dict[t].name = t


class ModuleInfo(DefinitionInfo):
    pass


class ModuleInfoTable(DefinitionInfoTable):
    pass


class FunctionInfo(DefinitionInfo):
    pass


class FunctionInfoTable(DefinitionInfoTable):
    pass


class TaskInfo(DefinitionInfo):
    pass


class TaskInfoTable(DefinitionInfoTable):
    pass


frametype_list = ('ifthen', 'ifelse', 'case', 'for', 'while', 'none')


class Frame(object):
    def __init__(self, name, previous, frametype='none',
                 alwaysinfo=None, condition=None,
                 module=False, functioncall=False, taskcall=False,
                 generate=False, always=False, initial=False, loop=None, loop_iter=None,
                 modulename=None):
        self.name = name
        self.previous = previous
        self.next = []
        self.frametype = frametype

        self.alwaysinfo = alwaysinfo
        self.condition = condition

        self.module = module
        self.functioncall = functioncall
        self.taskcall = taskcall
        self.generate = generate
        self.always = always
        self.initial = initial
        self.loop = loop
        self.loop_iter = loop_iter

        self.variables = Variables()
        self.functions = FunctionInfoTable()
        self.tasks = TaskInfoTable()
        self.blockingassign = collections.OrderedDict()
        self.nonblockingassign = collections.OrderedDict()

        self.modulename = modulename

    def getName(self):
        return self.name

    def getPrevious(self):
        return self.previous

    def getNext(self):
        return self.next

    def getFrametype(self):
        return self.frametype

    def isIfelse(self):
        return self.frametype == 'ifelse'

    def getAlwaysInfo(self):
        return self.alwaysinfo

    def getCondition(self):
        return self.condition

    def isModule(self):
        return self.module

    def isFunctioncall(self):
        return self.functioncall

    def isTaskcall(self):
        return self.taskcall

    def isGenerate(self):
        return self.generate

    def isAlways(self):
        return self.always

    def isInitial(self):
        return self.initial

    def setNext(self, nextframe):
        self.next.append(nextframe)

    def setAlwaysInfo(self, clock_name, clock_edge, clock_bit,
                      reset_name, reset_edge, reset_bit, senslist):
        self.alwaysinfo = AlwaysInfo(clock_name, clock_edge, clock_bit,
                                     reset_name, reset_edge, reset_bit, senslist)

    def addSignal(self, node):
        self.variables.addSignal(node.name, node)

    def addConst(self, node):
        self.variables.addConst(node.name, node)

    def addGenvar(self, node):
        self.variables.addGenvar(node.name, 0)

    def addFunction(self, node):
        self.functions.addDefinition(node.name, node)

    def addTask(self, node):
        self.tasks.addDefinition(node.name, node)

    def addFunctionPort(self, node):
        self.functions.addPort(node)

    def addTaskPort(self, node):
        self.tasks.addPort(node)

    def updateSignal(self, signal):
        self.variables.updateSignal(signal)

    def updateConst(self, const):
        self.variables.updateConst(const)

    def getConstant(self, name):
        return self.variables.getConst(name)

    def hasConstant(self, name):
        return self.variables.hasConst(name)

    def getSignal(self, name):
        return self.variables.getSignal(name)

    def hasSignal(self, name):
        return self.variables.hasSignal(name)

    def getSignals(self):
        return self.variables.getSignals()

    def getConsts(self):
        return self.variables.getConsts()

    def getFunctions(self):
        return self.functions.getDefinitions()

    def getTasks(self):
        return self.tasks.getDefinitions()

    def getModuleName(self):
        return self.modulename

    def setBlockingAssign(self, dst, bind):
        if not dst in self.blockingassign:
            self.blockingassign[dst] = (bind,)
            return
        current = self.blockingassign[dst]
        for c_i, c in enumerate(current):
            if c.msb == bind.msb and c.msb == bind.msb and c.ptr == bind.ptr:
                self.blockingassign[dst][c_i].tree = bind.tree
                return
        self.blockingassign[dst] = current + (bind,)

    def getBlockingAssign(self, dst):
        if dst in self.blockingassign:
            return self.blockingassign[dst]
        return ()

    def getBlockingAssigns(self):
        return self.blockingassign

    def addNonblockingAssign(self, dst, bind):
        if not dst in self.nonblockingassign:
            self.nonblockingassign[dst] = (copy.deepcopy(bind),)
            return
        current = self.nonblockingassign[dst]
        for c_i, c in enumerate(current):
            if c.msb == bind.msb and c.msb == bind.msb and c.ptr == bind.ptr:
                self.nonblockingassign[dst][c_i].tree = copy.deepcopy(bind.tree)
                return
        self.nonblockingassign[dst] = current + (copy.deepcopy(bind),)

    def getNonblockingAssigns(self):
        return self.nonblockingassign


class FrameTable(object):
    def __init__(self):
        self.dict = {}
        self.current = ScopeChain()

        self.function_def = False
        self.task_def = False
        self.for_pre = False
        self.for_post = False
        self.for_iter = None

    def toScopeChain(self, scopename):
        if scopename is None:
            return self.current
        return self.current + scopename

    def addFrame(self, scopename,
                 frametype='none',
                 alwaysinfo=None, condition=None,
                 module=False, functioncall=False, taskcall=False,
                 generate=False, always=False, initial=False, loop=None, loop_iter=None,
                 modulename=None):

        scopechain = self.toScopeChain(scopename)
        if scopechain in self.dict:
            raise verror.DefinitionError('Already Exists: %s' % str(scopechain))
        ret = self.current
        previous = self.current
        if len(previous) > 0:
            self.dict[previous].setNext(scopechain)
        self.dict[scopechain] = Frame(scopechain, previous, frametype=frametype,
                                      alwaysinfo=alwaysinfo, condition=condition,
                                      module=module, functioncall=functioncall,
                                      taskcall=taskcall, generate=generate,
                                      always=always, initial=initial, loop=loop, loop_iter=loop_iter,
                                      modulename=modulename)
        self.current = scopechain
        return ret

    def hasFrame(self, scope):
        return scope in self.dict

    def getFrametype(self):
        return self.dict[self.current].getFrametype()

    def getAlwaysInfo(self):
        return self.dict[self.current].getAlwaysInfo()

    def getCondition(self):
        return self.dict[self.current].getCondition()

    def isModule(self):
        return self.dict[self.current].isModule()

    def isFunctioncall(self):
        return self.dict[self.current].isFunctioncall()

    def isTaskcall(self):
        return self.dict[self.current].isTaskcall()

    def isGenerate(self):
        return self.dict[self.current].isGenerate()

    def isAlways(self):
        return self.dict[self.current].isAlways()

    def isInitial(self):
        return self.dict[self.current].isInitial()

    def getLoop(self):
        return self.dict[self.current].loop

    def getLoopIter(self):
        return self.dict[self.current].loop_iter

    def isFunctiondef(self):
        return self.function_def

    def isTaskdef(self):
        return self.task_def

    def isForpre(self):
        return self.for_pre

    def isForpost(self):
        return self.for_post

    def setFunctionDef(self):
        self.function_def = True

    def unsetFunctionDef(self):
        self.function_def = False

    def setTaskDef(self):
        self.task_def = True

    def unsetTaskDef(self):
        self.task_def = False

    def setForPre(self):
        self.for_pre = True

    def unsetForPre(self):
        self.for_pre = False

    def setForPost(self):
        self.for_post = True

    def unsetForPost(self):
        self.for_post = False

    def setForIter(self, iter):
        self.for_iter = iter

    def getForIter(self):
        return self.for_iter

    def setAlwaysInfo(self, clock_name, clock_edge, clock_bit,
                      reset_name, reset_edge, reset_bit, senslist):
        self.dict[self.current].setAlwaysInfo(clock_name, clock_edge, clock_bit,
                                              reset_name, reset_edge, reset_bit, senslist)

    def setCurrent(self, current):
        self.current = current

    def getCurrent(self):
        return self.current

    def getModuleName(self):
        return self.dict[self.current].getModuleName()

    def getLabelKey(self, name):
        ret = ''
        if self.isModule():
            ret += 'md_'
        if self.isGenerate():
            ret += 'ge_'
        if self.isAlways():
            ret += 'al_'
        if self.isInitial():
            ret += 'in_'
        if self.isFunctioncall():
            ret += 'fc_'
        if self.isTaskcall():
            ret += 'tc_'
        return ret + name

    def addSignal(self, var):
        if self.function_def and isinstance(var, Input):
            self.dict[self.current].addFunctionPort(var)
            return
        if self.task_def and isinstance(var, Input):
            self.dict[self.current].addTaskPort(var)
            return
        self.dict[self.current].addSignal(var)

    def addConst(self, var):
        self.dict[self.current].addConst(var)

    def addGenvar(self, var):
        self.dict[self.current].addGenvar(var)

    def addFunction(self, var):
        self.dict[self.current].addFunction(var)

    def addTask(self, var):
        self.dict[self.current].addTask(var)

    def updateSignal(self, signal):
        self.dict[self.current].updateSignal(signal)

    def updateConst(self, const):
        self.dict[self.current].updateConst(const)

    def getAllInstances(self):
        ret = []
        for dk in self.dict.keys():
            if dk[-1].scopetype == 'module':
                ret.append((dk, self.dict[dk].getModuleName()))
        return tuple(ret)

    def getAllSignals(self):
        ret = collections.OrderedDict()
        for dk, dv in self.dict.items():
            ret.update(
                map_key((lambda x: dk + ScopeLabel(x, 'signal')), dv.getSignals()))
        return ret

    def getAllConsts(self):
        ret = collections.OrderedDict()
        for dk, dv in self.dict.items():
            ret.update(
                map_key((lambda x: dk + ScopeLabel(x, 'signal')), dv.getConsts()))
        return ret

    def getAllFunctions(self):
        ret = collections.OrderedDict()
        for dk, dv in self.dict.items():
            ret.update(
                map_key((lambda x: dk + ScopeLabel(x, 'function')), dv.getFunctions()))
        return ret

    def getAllTasks(self):
        ret = collections.OrderedDict()
        for dk, dv in self.dict.items():
            ret.update(
                map_key((lambda x: dk + ScopeLabel(x, 'task')), dv.getTasks()))
        return ret

    def getSignals(self, scope):
        return map_key(
            (lambda x: scope + ScopeLabel(x, 'signal')), self.dict[scope].getSignals())

    def getConsts(self, scope):
        return map_key(
            (lambda x: scope + ScopeLabel(x, 'signal')), self.dict[scope].getConsts())

    def getFunctions(self, scope):
        return map_key(
            (lambda x: scope + ScopeLabel(x, 'function')), self.dict[scope].getFunctions())

    def getTasks(self, scope):
        return map_key(
            (lambda x: scope + ScopeLabel(x, 'task')), self.dict[scope].getTasks())

    def getGenerateConditions(self):
        ret = []
        ptr = self.current
        while True:
            frame = self.dict[ptr]
            if not frame.isGenerate():
                break
            if frame.loop is not None:  # generate for
                ret.append((frame.loop_iter, frame.loop))
            elif frame.condition is not None:  # generate if
                if frame.isIfelse():
                    ret.append((None, Ulnot(frame.condition)))
                else:
                    ret.append((None, frame.condition))
            ptr = self.dict[ptr].previous
        return tuple(reversed(ret))

    def getAlwaysStatus(self):
        ptr = self.current
        frame = self.dict[ptr]
        alwaysinfo = frame.getAlwaysInfo()
        while True:
            if frame.isFunctioncall():
                return None
            if frame.isTaskcall():
                return None
            if not frame.isAlways():
                return None
            if alwaysinfo is not None:
                return alwaysinfo
            ptr = self.dict[ptr].previous
            frame = self.dict[ptr]
            alwaysinfo = frame.getAlwaysInfo()

    def setBlockingAssign(self, dst, bind, scope):
        self.dict[scope].setBlockingAssign(dst, bind)

    def getBlockingAssign(self, dst, scope):
        p = scope
        while self.dict[p].isAlways():
            ret = self.dict[p].getBlockingAssign(dst)
            if ret:
                return ret
            p = self.dict[p].getPrevious()
        return ()

    def addNonblockingAssign(self, dst, bind):
        self.dict[self.current].addNonblockingAssign(dst, bind)

    def getBlockingAssigns(self):
        return self.dict[self.current].getBlockingAssigns()

    def getBlockingAssignsScope(self, scope):
        return self.dict[scope].getBlockingAssigns()

    def getNonblockingAssigns(self):
        return self.dict[self.current].getNonblockingAssigns()

    def getPreviousNonblockingAssign(self):
        previous = self.dict[self.current].previous
        if len(previous) == 0:
            return collections.OrderedDict()
        previous_frame = self.dict[previous]
        if not previous_frame.isAlways():
            return collections.OrderedDict()
        return previous_frame.getNonblockingAssigns()

    def searchConstantDefinition(self, key, name):
        if self.dict[key].hasConstant(name):
            return key, self.dict[key].getConstant(name)
        if self.dict[key].isModule():
            return None, None
        previous = self.dict[key].getPrevious()
        return self.searchConstantDefinition(previous, name)

    def getConstantDefinition(self, key, name):
        if self.dict[key].hasConstant(name):
            return self.dict[key].getConstant(name)
        return None

    def searchSignalDefinition(self, key, name):
        if self.dict[key].hasSignal(name):
            return key, self.dict[key].getSignal(name)
        if self.dict[key].isModule():
            return None, None
        previous = self.dict[key].getPrevious()
        return self.searchSignalDefinition(previous, name)

    def searchMatchedScopeChain(self, currentchain, targetchain):
        skiplength = len(currentchain) - 1
        printable = currentchain[skiplength].isPrintable()

        if printable:
            if currentchain[skiplength] != targetchain[0]:  # not match
                return None
            if len(targetchain) == 1:
                return ScopeChain([targetchain[0]])
            for nextframe in self.dict[currentchain].getNext():
                rslt = self.searchMatchedScopeChain(nextframe, targetchain[1:])
                if rslt is not None:
                    return ScopeChain([currentchain[skiplength]]) + rslt
            return None

        if (currentchain[skiplength].scopetype == 'for' and
                targetchain[0].scopetype == 'for'):
            if currentchain[skiplength].scopeloop != targetchain[0].scopeloop:
                return None
            if len(targetchain) == 1:
                return ScopeChain([targetchain[0]])
            for nextframe in self.dict[currentchain].getNext():
                rslt = self.searchMatchedScopeChain(nextframe, targetchain[1:])
                if rslt is not None:
                    return ScopeChain([currentchain[skiplength]]) + rslt

            return None

        for nextframe in self.dict[currentchain].getNext():
            rslt = self.searchMatchedScopeChain(nextframe, targetchain)
            if rslt is not None:
                return ScopeChain([currentchain[skiplength]]) + rslt
        return None
