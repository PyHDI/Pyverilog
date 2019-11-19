# -------------------------------------------------------------------------------
# bindvisitor.py
#
# Binding visitor
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

from pyverilog.vparser.ast import *
import pyverilog.utils.util as util
import pyverilog.utils.verror as verror
import pyverilog.utils.signaltype as signaltype
from pyverilog.utils.scope import ScopeLabel, ScopeChain
from pyverilog.dataflow.dataflow import *
from pyverilog.dataflow.visit import *
from pyverilog.dataflow.optimizer import VerilogOptimizer
import pyverilog.dataflow.reorder as reorder
import pyverilog.dataflow.replace as replace


class BindVisitor(NodeVisitor):
    def __init__(self, moduleinfotable, top, frames, noreorder=False):
        self.moduleinfotable = moduleinfotable
        self.top = top
        self.frames = frames
        self.labels = Labels()
        self.dataflow = DataFlow()
        self.optimizer = VerilogOptimizer({}, {})

        self.noreorder = noreorder

        # set the top frame of top module
        self.frames.setCurrent(ScopeChain())
        self.stackInstanceFrame(top, top)

        self.copyAllFrameInfo()

        current = self.frames.getCurrent()
        self.copyFrameInfo(current)

        self.renamecnt = 0
        self.default_nettype = 'wire'

    def getDataflows(self):
        return self.dataflow

    def getFrameTable(self):
        return self.frames

    def start_visit(self):
        return self.visit(self.moduleinfotable.getDefinition(self.top))

    def visit_ModuleDef(self, node):
        self.default_nettype = node.default_nettype
        self.generic_visit(node)

    def visit_Input(self, node):
        self.addTerm(node)

    def visit_Output(self, node):
        self.addTerm(node)

    def visit_Inout(self, node):
        self.addTerm(node)

    def visit_Reg(self, node):
        self.addTerm(node)

    def visit_Wire(self, node):
        self.addTerm(node)

    def visit_Tri(self, node):
        self.addTerm(node)

    def visit_Integer(self, node):
        self.addTerm(node)

    def visit_Parameter(self, node):
        self.addTerm(node)
        current = self.frames.getCurrent()
        name = current + ScopeLabel(node.name, 'signal')
        if not self.hasConstant(name):
            value = self.optimize(self.getTree(node.value, current))
            self.setConstant(name, value)

        if len(self.dataflow.getBindlist(name)) == 0:
            self.addBind(node.name, node.value, bindtype='parameter')

    def visit_Supply(self, node):
        self.addTerm(node)
        current = self.frames.getCurrent()
        name = current + ScopeLabel(node.name, 'signal')
        self.addBind(node.name, node.value, bindtype='parameter')

    def visit_Localparam(self, node):
        self.addTerm(node)
        current = self.frames.getCurrent()
        name = current + ScopeLabel(node.name, 'signal')
        if not self.hasConstant(name):
            value = self.optimize(self.getTree(node.value, current))
            self.setConstant(name, value)

        self.addBind(node.name, node.value, bindtype='localparam')

    def visit_Genvar(self, node):
        self.addTerm(node)
        current = self.frames.getCurrent()
        name = self.frames.getCurrent() + ScopeLabel(node.name, 'signal')
        value = DFEvalValue(0)
        self.setConstant(name, value)

    def visit_Function(self, node):
        self.frames.setFunctionDef()
        self.generic_visit(node)
        self.frames.unsetFunctionDef()

    def visit_Task(self, node):
        self.frames.setTaskDef()
        self.generic_visit(node)
        self.frames.unsetTaskDef()

    def visit_InstanceList(self, node):
        for i in node.instances:
            self.visit(i)

    def visit_Instance(self, node):
        if node.array:
            return self._visit_Instance_array(node)
        nodename = node.name
        return self._visit_Instance_body(node, nodename)

    def _visit_Instance_array(self, node):
        if node.name == '':
            raise verror.FormatError("Module %s requires an instance name" % node.module)

        current = self.frames.getCurrent()
        msb = self.optimize(self.getTree(node.array.msb, current)).value
        lsb = self.optimize(self.getTree(node.array.lsb, current)).value
        num_of_pins = msb + 1 - lsb

        for i in range(lsb, msb + 1):
            nodename = node.name + '_' + str(i)
            self._visit_Instance_body(node, nodename, arrayindex=i)

    def _visit_Instance_body(self, node, nodename, arrayindex=None):
        if node.module in primitives:
            return self._visit_Instance_primitive(node, arrayindex)

        if nodename == '':
            raise verror.FormatError("Module %s requires an instance name" % node.module)

        current = self.stackInstanceFrame(nodename, node.module)

        scope = self.frames.getCurrent()

        paramnames = self.moduleinfotable.getParamNames(node.module)
        for paramnames_i, param in enumerate(node.parameterlist):
            self.addInstanceParameterBind(param, paramnames[paramnames_i])
            value = self.optimize(self.getTree(param.argname, current))
            paramname = paramnames[paramnames_i] if param.paramname is None else param.paramname
            if paramname not in paramnames:
                raise verror.FormatError("No such parameter: %s in %s" %
                                         (paramname, nodename))
            name = scope + ScopeLabel(paramname, 'signal')
            self.setConstant(name, value)
            definition = Parameter(paramname, str(value.value))
            term = self.makeConstantTerm(name, definition, current)
            self.setConstantTerm(name, term)

        ioports = self.moduleinfotable.getIOPorts(node.module)
        for ioport_i, port in enumerate(node.portlist):
            if port.portname is not None and not (port.portname in ioports):
                raise verror.FormatError("No such port: %s in %s" %
                                         (port.argname.name, nodename))
            self.addInstancePortBind(port, ioports[ioport_i], arrayindex)

        new_current = self.frames.getCurrent()
        self.copyFrameInfo(new_current)

        self.visit(self.moduleinfotable.getDefinition(node.module))
        self.frames.setCurrent(current)

    def _visit_Instance_primitive(self, node, arrayindex=None):
        primitive_type = primitives[node.module]
        left = node.portlist[0].argname
        if arrayindex is not None:
            left = Pointer(left, IntConst(str(arrayindex)))
        right = None
        if primitive_type == None:
            right = (Pointer(node.portlist[1].argname, IntConst('0')) if arrayindex is None else
                     Pointer(node.portlist[1].argname, IntConst(str(arrayindex))))
        elif primitive_type == Unot:
            right = (Ulnot(Pointer(node.portlist[1].argname, IntConst('0'))) if arrayindex is None else
                     Ulnot(Pointer(node.portlist[1].argname, IntConst(str(arrayindex)))))
        else:
            concat_list = ([Pointer(p.argname, IntConst('0')) for p in node.portlist[1:]] if arrayindex is None else
                           [Pointer(p.argname, IntConst(str(arrayindex))) for p in node.portlist[1:]])
            right = primitive_type(Concat(concat_list))
        self.addBind(left, right, bindtype='assign')

    def visit_Initial(self, node):
        pass
        # label = self.labels.get( self.frames.getLabelKey('initial') )
        # current = self.stackNextFrame(label, 'initial',
        #                              generate=self.frames.isGenerate(),
        #                              initial=True)
        # self.generic_visit(node)
        # self.frames.setCurrent(current)

    def visit_Always(self, node):
        label = self.labels.get(self.frames.getLabelKey('always'))
        current = self.stackNextFrame(label, 'always',
                                      generate=self.frames.isGenerate(),
                                      always=True)

        (clock_name, clock_edge, clock_bit,
         reset_name, reset_edge, reset_bit,
         senslist) = self._createAlwaysinfo(node, current)

        self.frames.setAlwaysInfo(clock_name, clock_edge, clock_bit,
                                  reset_name, reset_edge, reset_bit, senslist)

        self.generic_visit(node)
        self.frames.setCurrent(current)

    def _get_signal_name(self, n):
        if isinstance(n, Identifier):
            return n.name
        if isinstance(n, Pointer):
            return self._get_signal_name(n.var)
        if isinstance(n, Partselect):
            return self._get_signal_name(n.var)
        return None

    def _createAlwaysinfo(self, node, scope):
        sens = None
        senslist = []
        clock_edge = None
        clock_name = None
        clock_bit = None
        reset_edge = None
        reset_name = None
        reset_bit = None

        for l in node.sens_list.list:
            if l.sig is None:
                continue

            if isinstance(l.sig, pyverilog.vparser.ast.Pointer):
                signame = self._get_signal_name(l.sig.var)
                bit = int(l.sig.ptr.value)
            else:
                signame = self._get_signal_name(l.sig)
                bit = 0

            if signaltype.isClock(signame):
                clock_name = self.searchTerminal(signame, scope)
                clock_edge = l.type
                clock_bit = bit
            elif signaltype.isReset(signame):
                reset_name = self.searchTerminal(signame, scope)
                reset_edge = l.type
                reset_bit = bit
            else:
                senslist.append(l)

        if clock_edge is not None and len(senslist) > 0:
            raise verror.FormatError('Illegal sensitivity list')
        if reset_edge is not None and len(senslist) > 0:
            raise verror.FormatError('Illegal sensitivity list')

        return (clock_name, clock_edge, clock_bit, reset_name, reset_edge, reset_bit, senslist)

    def visit_IfStatement(self, node):
        if self.frames.isFunctiondef() and not self.frames.isFunctioncall():
            return
        if self.frames.isTaskdef() and not self.frames.isTaskcall():
            return

        if (self.frames.isGenerate() and
            not self.frames.isAlways() and not self.frames.isInitial() and
            not self.frames.isFunctioncall() and not self.frames.isTaskcall() and
                not self.frames.isFunctiondef() and not self.frames.isTaskdef()):
            # generate-if statement
            current = self.frames.getCurrent()
            tree = self.getTree(node.cond, current)
            rslt = self.optimize(tree)
            if not isinstance(rslt, DFEvalValue):
                raise verror.FormatError("Can not resolve generate-if condition")

            if rslt.value > 0:
                label = self._if_true(node)
                if node.true_statement is not None:
                    self.copyBlockingAssigns(current + ScopeLabel(label, 'if'), current)
            else:
                label = self.labels.get(self.frames.getLabelKey('if'))
                self._if_false(node, label)
                if node.false_statement is not None:
                    self.copyBlockingAssigns(
                        current + ScopeLabel(self._toELSE(label), 'if'), current)
            return

        label = self._if_true(node)
        self._if_false(node, label)

        current = self.frames.getCurrent()
        if node.true_statement is not None:
            self.copyBlockingAssigns(current + ScopeLabel(label, 'if'), current)
        if node.false_statement is not None:
            self.copyBlockingAssigns(current + ScopeLabel(self._toELSE(label), 'if'), current)

    def _toELSE(self, label):
        return label + '_ELSE'

    def _if_true(self, node):
        if node.true_statement is None:
            return None
        label = self.labels.get(self.frames.getLabelKey('if'))
        current = self.stackNextFrame(label, 'if',
                                      frametype='ifthen',
                                      condition=node.cond,
                                      functioncall=self.frames.isFunctioncall(),
                                      taskcall=self.frames.isTaskcall(),
                                      generate=self.frames.isGenerate(),
                                      always=self.frames.isAlways(),
                                      initial=self.frames.isInitial())

        self.copyPreviousNonblockingAssign(current + ScopeLabel(label, 'if'))

        if node.true_statement is not None:
            self.visit(node.true_statement)
        self.frames.setCurrent(current)
        return label

    def _if_false(self, node, label):
        if node.false_statement is None:
            return
        label = self._toELSE(label)
        current = self.stackNextFrame(label, 'if',
                                      frametype='ifelse',
                                      condition=node.cond,
                                      functioncall=self.frames.isFunctioncall(),
                                      taskcall=self.frames.isTaskcall(),
                                      generate=self.frames.isGenerate(),
                                      always=self.frames.isAlways(),
                                      initial=self.frames.isInitial())

        self.copyPreviousNonblockingAssign(current + ScopeLabel(label, 'if'))

        if node.false_statement is not None:
            self.visit(node.false_statement)
        self.frames.setCurrent(current)
        return label

    def visit_CaseStatement(self, node):
        if self.frames.isFunctiondef() and not self.frames.isFunctioncall():
            return
        if self.frames.isTaskdef() and not self.frames.isTaskcall():
            return
        start_frame = self.frames.getCurrent()
        caseframes = []
        self._case(node.comp, node.caselist, caseframes)
        self.frames.setCurrent(start_frame)
        for f in caseframes:
            self.copyBlockingAssigns(f, start_frame)

    def visit_CasexStatement(self, node):
        return self.visit_CaseStatement(node)

    def _case(self, comp, caselist, myframes):
        if len(caselist) == 0:
            return

        case = caselist[0]
        cond = IntConst('1')
        if case.cond is not None:
            if len(case.cond) > 1:
                cond = Eq(comp, case.cond[0])
                for c in case.cond[1:]:
                    cond = Lor(cond, Eq(comp, c))
            else:
                cond = Eq(comp, case.cond[0])
        # else: raise Exception
        label = self.labels.get(self.frames.getLabelKey('if'))
        current = self.stackNextFrame(label, 'if',
                                      frametype='ifthen',
                                      condition=cond,
                                      functioncall=self.frames.isFunctioncall(),
                                      taskcall=self.frames.isTaskcall(),
                                      generate=self.frames.isGenerate(),
                                      always=self.frames.isAlways(),
                                      initial=self.frames.isInitial())

        self.copyPreviousNonblockingAssign(current + ScopeLabel(label, 'if'))

        myframes.append(self.frames.getCurrent())

        if case.statement is not None:
            self.visit(case.statement)
        self.frames.setCurrent(current)

        if len(caselist) == 1:
            return

        label = self._toELSE(label)
        current = self.stackNextFrame(label, 'if',
                                      frametype='ifelse',
                                      condition=cond,
                                      functioncall=self.frames.isFunctioncall(),
                                      taskcall=self.frames.isTaskcall(),
                                      generate=self.frames.isGenerate(),
                                      always=self.frames.isAlways(),
                                      initial=self.frames.isInitial())

        self.copyPreviousNonblockingAssign(current + ScopeLabel(label, 'if'))

        myframes.append(current + ScopeLabel(label, 'if'))

        self._case(comp, caselist[1:], myframes)

    def visit_ForStatement(self, node):
        if self.frames.isFunctiondef() and not self.frames.isFunctioncall():
            return
        if self.frames.isTaskdef() and not self.frames.isTaskcall():
            return

        # pre-statement
        current = self.frames.getCurrent()
        pre_right = self.getTree(node.pre.right, current)
        pre_right_value = self.optimize(pre_right)
        loop = pre_right_value.value
        self.frames.setForPre()
        self.visit(node.pre)
        self.frames.unsetForPre()
        label = self.labels.get(self.frames.getLabelKey('for'))
        #loop = 0
        start_frame = self.frames.getCurrent()

        while True:
            # cond-statement
            current = self.frames.getCurrent()
            raw_tree = self.getTree(node.cond, current)
            rslt = self.optimize(raw_tree)
            if not isinstance(rslt, DFEvalValue):
                raise verror.FormatError(("Can not process the for-statement. "
                                          "for-condition should be evaluated statically."))
            if rslt.value <= 0:
                break

            # main-statement
            current = self.stackNextFrame(label, 'for',
                                          frametype='for',
                                          functioncall=self.frames.isFunctioncall(),
                                          taskcall=self.frames.isTaskcall(),
                                          generate=self.frames.isGenerate(),
                                          always=self.frames.isAlways(),
                                          initial=self.frames.isInitial(),
                                          loop=loop, loop_iter=self.frames.getForIter())

            self.visit(node.statement)
            self.copyBlockingAssigns(self.frames.getCurrent(), start_frame)
            self.frames.setCurrent(current)

            # post-statement
            current = self.frames.getCurrent()
            post_right = self.getTree(node.post.right, current)
            post_right_value = self.optimize(post_right)
            loop = post_right_value.value
            self.frames.setForPost()
            self.visit(node.post)
            self.frames.unsetForPost()
            #loop += 1

    def visit_WhileStatement(self, node):
        if self.frames.isFunctiondef() and not self.frames.isFunctioncall():
            return
        if self.frames.isTaskdef() and not self.frames.isTaskcall():
            return
        label = self.labels.get(self.frames.getLabelKey('while'))
        loop = 0
        start_frame = self.frames.getCurrent()

        while True:
            # cond-statement
            current = self.frames.getCurrent()
            raw_tree = self.getTree(node.cond, current)
            rslt = self.optimize(raw_tree)
            if not isinstance(rslt, DFEvalValue):
                raise verror.FormatError(("Can not process the while-statement. "
                                          "while-condition should be evaluated statically."))
            if rslt.value <= 0:
                break

            # main-statement
            current = self.stackNextFrame(label, 'while',
                                          frametype='while',
                                          functioncall=self.frames.isFunctioncall(),
                                          taskcall=self.frames.isTaskcall(),
                                          generate=self.frames.isGenerate(),
                                          always=self.frames.isAlways(),
                                          initial=self.frames.isInitial(),
                                          loop=loop)

            self.visit(node.statement)
            self.copyBlockingAssigns(self.frames.getCurrent(), start_frame)
            self.frames.setCurrent(current)
            loop += 1

    def visit_GenerateStatement(self, node):
        label = self.labels.get(self.frames.getLabelKey('generate'))
        current = self.stackNextFrame(label, 'generate',
                                      generate=True)

        self.generic_visit(node)
        self.frames.setCurrent(current)

    def visit_Block(self, node):
        label = None
        if node.scope is not None:
            label = node.scope
        else:
            label = self.labels.get(self.frames.getLabelKey('block'))

        current = self.stackNextFrame(label, 'block',
                                      frametype='block',
                                      functioncall=self.frames.isFunctioncall(),
                                      taskcall=self.frames.isTaskcall(),
                                      generate=self.frames.isGenerate(),
                                      always=self.frames.isAlways(),
                                      initial=self.frames.isInitial())

        self.generic_visit(node)
        self.frames.setCurrent(current)
        if self.frames.isAlways():
            self.copyBlockingAssigns(current + ScopeLabel(label, 'block'), current)

    def visit_Assign(self, node):
        self.addBind(node.left, node.right, bindtype='assign')

    def visit_BlockingSubstitution(self, node):
        self.addBind(node.left, node.right, self.frames.getAlwaysStatus(), 'blocking')

    def visit_NonblockingSubstitution(self, node):
        if self.frames.isForpre() or self.frames.isForpost():
            raise verror.FormatError(("Non Blocking Substitution is not allowed"
                                      "in for-statement"))
        if self.frames.isFunctioncall():
            raise verror.FormatError("Non Blocking Substitution is not allowed in function")
        self.addBind(node.left, node.right, self.frames.getAlwaysStatus(), 'nonblocking')

    def visit_SystemCall(self, node):
        print("Warning: Isolated system call is not supported: %s" % node.syscall)

    def optimize(self, node):
        return self.optimizer.optimize(node)

    def stackInstanceFrame(self, instname, modulename):
        current = self.frames.getCurrent()
        self.frames.setCurrent(current + ScopeLabel(instname, 'module'))
        self.copyFrameInfo(current + ScopeLabel(instname, 'module'))
        return current

    def stackNextFrame(self, label, scopetype,
                       frametype='none',
                       alwaysinfo=None, condition=None,
                       module=False, functioncall=False, taskcall=False,
                       generate=False, always=False, initial=False, loop=None, loop_iter=None):
        current = self.frames.getCurrent()
        scopelabel = ScopeLabel(label, scopetype, loop)
        nextscope = current + scopelabel

        if not self.frames.hasFrame(nextscope):
            current = self.frames.addFrame(scopelabel,
                                           frametype=frametype,
                                           alwaysinfo=alwaysinfo, condition=condition,
                                           module=module, functioncall=functioncall, taskcall=taskcall,
                                           generate=generate, always=always, initial=initial,
                                           loop=loop, loop_iter=loop_iter)

        self.frames.setCurrent(nextscope)
        new_current = self.frames.getCurrent()
        self.copyFrameInfo(new_current)
        return current

    def copyFrameInfo(self, current):
        for name, definitions in self.frames.getConsts(current).items():
            if len(definitions) > 1:
                raise verror.FormatError("Multiple definitions for Constant")
            for definition in definitions:
                termtype = definition.__class__.__name__
                term = Term(name, set([termtype]))
                self.dataflow.addTerm(name, term)

        for name, definitions in self.frames.getConsts(current).items():
            if len(definitions) > 1:
                raise verror.FormatError("Multiple definitions for Constant")
            for definition in definitions:
                cterm = self.makeConstantTerm(name, definition, current)
                self.setConstantTerm(name, cterm)

        all_passed = False
        while not all_passed:
            all_passed = True
            for name, definitions in self.frames.getConsts(current).items():
                if len(definitions) > 1:
                    raise verror.FormatError("Multiple definitions for Constant")
                if self.hasConstant(name):
                    continue

                for definition in definitions:
                    if isinstance(definition, Genvar):
                        continue
                    value = self.optimize(self.getTree(definition.value, current))
                    if not isinstance(value, DFEvalValue):
                        all_passed = False
                        continue
                    self.setConstant(name, value)

    def copyAllFrameInfo(self):
        for name, definitions in self.frames.getAllConsts().items():
            if len(definitions) > 1:
                raise verror.FormatError("Multiple definitions for Constant")

            for definition in definitions:
                termtype = definition.__class__.__name__
                term = Term(name, set([termtype]))
                self.dataflow.addTerm(name, term)

        for name, definitions in self.frames.getAllSignals().items():
            for definition in definitions:
                termtype = definition.__class__.__name__
                self.dataflow.addTerm(name, Term(name, set([termtype])))

        for name, definition in self.frames.getAllFunctions().items():
            self.dataflow.addFunction(name, definition.getDefinition())
            self.dataflow.addFunctionPorts(name, definition.getIOPorts())

        for name, definition in self.frames.getAllTasks().items():
            self.dataflow.addTask(name, definition.getDefinition())
            self.dataflow.addTaskPorts(name, definition.getIOPorts())

    def copyPreviousNonblockingAssign(self, scope):
        assign = self.frames.getPreviousNonblockingAssign()
        for name, bindlist in assign.items():
            for bind in bindlist:
                self.frames.addNonblockingAssign(name, bind)
                msb = bind.msb
                lsb = bind.lsb
                ptr = bind.ptr
                part_msb = None
                part_lsb = None
                condlist, flowlist = self.getCondflow(scope)
                alwaysinfo = bind.alwaysinfo
                raw_tree = bind.tree
                new_bind = self.makeBind(name, msb, lsb, ptr, part_msb, part_lsb,
                                         raw_tree, condlist, flowlist,
                                         alwaysinfo=alwaysinfo)
                self.dataflow.addBind(name, new_bind)

    def copyBlockingAssigns(self, scope_copy_from, scope_copy_to):
        assign = self.frames.getBlockingAssignsScope(scope_copy_from)
        for name, bindlist in assign.items():
            for bind in bindlist:
                self.frames.setBlockingAssign(name, bind, scope_copy_to)

    def setConstant(self, name, value):
        self.optimizer.setConstant(name, value)

    def resetConstant(self, name):
        self.optimizer.resetConstant(name)

    def getConstant(self, name):
        return self.optimizer.getConstant(name)

    def hasConstant(self, name):
        return self.optimizer.hasConstant(name)

    def setConstantTerm(self, name, term):
        self.optimizer.setTerm(name, term)

    def getTerm(self, name):
        term = self.dataflow.getTerm(name)
        return term

    def getTermWidth(self, name):
        term = self.dataflow.getTerm(name)
        return term.msb, term.lsb

    def getTermDims(self, name):
        term = self.dataflow.getTerm(name)
        return term.dims

    def getTermtype(self, name):
        term = self.dataflow.getTerm(name)
        return term.termtype

    def getBindlist(self, name):
        return self.dataflow.getBindlist(name)

    def renameVar(self, name):
        renamedvar = (name[:-1] +
                      ScopeLabel('_rn' + str(self.renamecnt) +
                                   '_' + name[-1].scopename, 'signal'))
        self.renamecnt += 1
        return renamedvar

    def toScopeChain(self, blocklabel, current):
        scopelist = []
        for b in blocklabel.labellist:
            if b.loop is not None:
                loop = self.optimize(self.getTree(b.loop, current))
                if not isinstance(loop, DFEvalValue):
                    raise verror.FormatError('Loop iterator should be constant')
                scopelist.append(ScopeLabel('for', 'for', loop.value))
            scopelist.append(ScopeLabel(b.name, 'any'))
        return ScopeChain(scopelist)

    def getModuleScopeChain(self, target):
        remove_cnt = 0
        length = len(target)
        for scope in reversed(target):
            if scope.scopetype == 'module':
                return target[:length - remove_cnt]
            remove_cnt += 1
        raise verror.DefinitionError('module not found')

    def searchScopeTerminal(self, blocklabel, name, current):
        currentmodule = self.getModuleScopeChain(current)
        localchain = currentmodule[-1:] + self.toScopeChain(blocklabel, current)
        matchedchain = self.frames.searchMatchedScopeChain(currentmodule, localchain)
        varname = currentmodule[:-1] + matchedchain + ScopeLabel(name, 'signal')
        if self.dataflow.hasTerm(varname):
            return varname
        raise verror.DefinitionError('No such signal: %s' % varname)

    # def searchScopeConstantDefinition(self, blocklabel, name, current):
    #    currentmodule = self.getModuleScopeChain(current)
    #    localchain = currentmodule[-1:] + self.toScopeChain(blocklabel, current)
    #    matchedchain = self.frames.searchMatchedScopeChain(currentmodule, localchain)
    #    constdef = self.frames.getConstantDefinition(matchedchain, name)
    #    return constdef

    # def searchScopeFunction(self, blocklabel, name, current):
    #    currentmodule = self.getModuleScopeChain(current)
    #    localchain = currentmodule[-1:] + self.toScopeChain(blocklabel, current)
    #    matchedchain = self.frames.searchMatchedScopeChain(currentmodule, localchain)
    #    varname = currentmodule[:-1] + matchedchain + ScopeLabel(name, 'function')
    #    if self.dataflow.hasFunction(varname): return self.dataflow.getFunction(varname)
    #    raise verror.DefinitionError('No such function: %s' % varname)

    # def searchScopeTask(self, blocklabel, name, current):
    #    currentmodule = self.getModuleScopeChain(current)
    #    localchain = currentmodule[-1:] + self.toScopeChain(blocklabel, current)
    #    matchedchain = self.frames.searchMatchedScopeChain(currentmodule, localchain)
    #    varname = currentmodule[:-1] + matchedchain + ScopeLabel(name, 'task')
    #    if self.dataflow.hasTask(varname): return self.dataflow.getTask(varname)
    #    raise verror.DefinitionError('No such task: %s' % varname)

    # def searchScopeFunctionPorts(self, blocklabel, name, current):
    #    currentmodule = self.getModuleScopeChain(current)
    #    localchain = currentmodule[-1:] + self.toScopeChain(blocklabel, current)
    #    matchedchain = self.frames.searchMatchedScopeChain(currentmodule, localchain)
    #    varname = currentmodule[:-1] + matchedchain + ScopeLabel(name, 'function')
    #    if self.dataflow.hasFunction(varname):
    #        return self.dataflow.getFunctionPorts(varname)
    #    raise verror.DefinitionError('No such function: %s' % varname)

    # def searchScopeTaskPorts(self, blocklabel, name, current):
    #    currentmodule = self.frames.getModuleScopeChain(current)
    #    localchain = currentmodule[-1:] + self.toScopeChain(blocklabel, current)
    #    matchedchain = self.frames.searchMatchedScopeChain(currentmodule, localchain)
    #    varname = currentmodule[:-1] + matchedchain + ScopeLabel(name, 'task')
    #    if self.dataflow.hasTask(varname):
    #        return self.dataflow.getTaskPorts(varname)
    #    raise verror.DefinitionError('No such task: %s' % varname)

    def searchConstantDefinition(self, key, name):
        const = self.frames.searchConstantDefinition(key, name)
        if const is None:
            raise verror.DefinitionError('constant value not found: %s' % name)
        return const

    def searchTerminal(self, name, scope):
        if len(scope) == 0:
            return None
        varname = scope + ScopeLabel(name, 'signal')
        if self.dataflow.hasTerm(varname):
            return varname
        if self.frames.dict[scope].isModule():
            return None
        # if self.frames.dict[scope].isFunctioncall(): return None
        return self.searchTerminal(name, scope[:-1])

    def searchFunction(self, name, scope):
        if len(scope) == 0:
            return None
        varname = scope + ScopeLabel(name, 'function')
        if self.dataflow.hasFunction(varname):
            return self.dataflow.getFunction(varname)
        if self.frames.dict[scope].isModule():
            return None
        return self.searchFunction(name, scope[:-1])

    def searchTask(self, name, scope):
        if len(scope) == 0:
            return None
        varname = scope + ScopeLabel(name, 'task')
        if self.dataflow.hasTask(varname):
            return self.dataflow.getTask(varname)
        if self.frames.dict[scope].isModule():
            return None
        return self.searchTask(name, scope[:-1])

    def searchFunctionPorts(self, name, scope):
        if len(scope) == 0:
            return ()
        varname = scope + ScopeLabel(name, 'function')
        if self.dataflow.hasFunction(varname):
            return self.dataflow.getFunctionPorts(varname)
        if self.frames.dict[scope].isModule():
            return ()
        return self.searchFunctionPorts(name, scope[:-1])

    def searchTaskPorts(self, name, scope):
        if len(scope) == 0:
            return ()
        varname = scope + ScopeLabel(name, 'task')
        if self.dataflow.hasTask(varname):
            return self.dataflow.getTaskPorts(varname)
        if self.frames.dict[scope].isModule():
            return ()
        return self.searchTaskPorts(name, scope[:-1])

    def makeConstantTerm(self, name, node, scope):
        termtype = node.__class__.__name__
        termtypes = set([termtype])
        msb = DFIntConst('31') if node.width is None else self.makeDFTree(node.width.msb, scope)
        lsb = DFIntConst('0') if node.width is None else self.makeDFTree(node.width.lsb, scope)
        return Term(name, termtypes, msb, lsb)

    def addTerm(self, node, rscope=None):
        if self.frames.isFunctiondef() and not self.frames.isFunctioncall():
            return
        if self.frames.isTaskdef() and not self.frames.isTaskcall():
            return
        scope = self.frames.getCurrent() if rscope is None else rscope
        name = scope + ScopeLabel(node.name, 'signal')
        termtype = node.__class__.__name__
        if self.frames.isFunctioncall():
            termtype = 'Function'
        if self.frames.isTaskcall():
            termtype = 'Task'
        termtypes = set([termtype])

        if isinstance(node, (Parameter, Localparam)):
            msb = DFIntConst('31') if node.width is None else self.makeDFTree(node.width.msb, scope)
        else:
            msb = DFIntConst('0') if node.width is None else self.makeDFTree(node.width.msb, scope)
        lsb = DFIntConst('0') if node.width is None else self.makeDFTree(node.width.lsb, scope)

        dims = None
        if node.dimensions is not None:
            dims = []
            for length in node.dimensions.lengths:
                l = self.makeDFTree(length.msb, scope)
                r = self.makeDFTree(length.lsb, scope)
                dims.append((l, r))
            dims = tuple(dims)

        term = Term(name, termtypes, msb, lsb, dims)
        self.dataflow.addTerm(name, term)
        self.setConstantTerm(name, term)

    def addBind(self, left, right, alwaysinfo=None, bindtype=None):
        if self.frames.isFunctiondef() and not self.frames.isFunctioncall():
            return
        if self.frames.isTaskdef() and not self.frames.isTaskcall():
            return
        lscope = self.frames.getCurrent()
        rscope = lscope
        dst = self.getDestinations(left, lscope)

        if bindtype == 'blocking':
            self.addDataflow_blocking(dst, right, lscope, rscope, alwaysinfo)
        else:
            self.addDataflow(dst, right, lscope, rscope, alwaysinfo, bindtype)

    def addInstanceParameterBind(self, param, name=None):
        lscope = self.frames.getCurrent()
        rscope = lscope[:-1]
        paramname = name if param.paramname is None else param.paramname
        dst = self.getDestinations(paramname, lscope)

        self.addDataflow(dst, param.argname, lscope, rscope, None, 'parameter')

    def addInstancePortBind(self, port, instportname=None, arrayindex=None):
        lscope = self.frames.getCurrent()
        rscope = lscope[:-1]
        portname = instportname if port.portname is None else port.portname
        ldst = self.getDestinations(portname, lscope)
        if ldst[0][0] is None:
            raise verror.DefinitionError('No such port: %s' % portname)

        termtype = self.getTermtype(ldst[0][0])
        for t in termtype:
            if t == 'Input':
                if port.argname is None:
                    continue
                portarg = (port.argname if arrayindex is None else
                           Pointer(port.argname, IntConst(str(arrayindex))))
                self.addDataflow(ldst, portarg, lscope, rscope)
            elif t == 'Output':
                if port.argname is None:
                    continue
                portarg = (port.argname if arrayindex is None else
                           Pointer(port.argname, IntConst(str(arrayindex))))
                rdst = self.getDestinations(portarg, rscope)
                self.addDataflow(rdst, portname, rscope, lscope)
            elif t == 'Inout':
                if port.argname is None:
                    continue
                portarg = (port.argname if arrayindex is None else
                           Pointer(port.argname, IntConst(str(arrayindex))))
                self.addDataflow(ldst, portarg, lscope, rscope)
                rdst = self.getDestinations(portarg, rscope)
                self.addDataflow(rdst, portname, rscope, lscope)

    def addDataflow(self, dst, right, lscope, rscope, alwaysinfo=None, bindtype=None):
        condlist, flowlist = self.getCondflow(lscope)
        raw_tree = self.getTree(right, rscope)
        self.setDataflow(dst, raw_tree, condlist, flowlist, alwaysinfo, bindtype)

    def addDataflow_blocking(self, dst, right, lscope, rscope, alwaysinfo):
        condlist, flowlist = self.getCondflow(lscope)
        raw_tree = self.getTree(right, rscope)

        self.setDataflow_rename(dst, raw_tree, condlist, flowlist, lscope, alwaysinfo)

        if len(dst) == 1:  # set genvar value to the constant table
            name = dst[0][0]
            if signaltype.isGenvar(self.getTermtype(name)):
                value = self.optimize(raw_tree)
                self.setConstant(name, value)
            else:  # for "for-statement"
                value = self.optimize(raw_tree)
                if isinstance(value, DFEvalValue):
                    self.setConstant(name, value)
                else:
                    self.resetConstant(name)

    def getCondflow(self, scope):
        condlist = self.getCondlist(scope)
        condlist = self.resolveCondlist(condlist, scope)
        flowlist = self.getFlowlist(scope)
        return (condlist, flowlist)

    def getCondlist(self, scope):
        ret = []
        s = scope
        while s is not None:
            frame = self.frames.dict[s]
            cond = frame.getCondition()
            if cond is not None:
                ret.append(self.makeDFTree(cond, self.reduceIfScope(s)))
            if frame.isModule():
                break
            s = frame.previous
        ret.reverse()
        return tuple(ret)

    def getFlowlist(self, scope):
        ret = []
        s = scope
        while s is not None:
            frame = self.frames.dict[s]
            cond = frame.getCondition()
            if cond is not None:
                ret.append(not frame.isIfelse())
            if frame.isModule():
                break
            s = frame.previous
        ret.reverse()
        return tuple(ret)

    def getTree(self, node, scope):
        expr = node.var if isinstance(node, Rvalue) else node
        tree = self.makeDFTree(expr, scope)
        tree = self.resolveBlockingAssign(tree, scope)
        if not self.noreorder:
            tree = reorder.reorder(tree)
        return tree

    def makeDFTree(self, node, scope):
        if isinstance(node, str):
            name = self.searchTerminal(node, scope)
            return DFTerminal(name)

        if isinstance(node, Identifier):
            if node.scope is not None:
                name = self.searchScopeTerminal(node.scope, node.name, scope)
                if name is None:
                    raise verror.DefinitionError('No such signal: %s' % node.name)
                return DFTerminal(name)
            name = self.searchTerminal(node.name, scope)
            if name is None:
                raise verror.DefinitionError('No such signal: %s' % node.name)
            return DFTerminal(name)

        if isinstance(node, IntConst):
            return DFIntConst(node.value)

        if isinstance(node, FloatConst):
            return DFFloatConst(node.value)

        if isinstance(node, StringConst):
            return DFStringConst(node.value)

        if isinstance(node, Cond):
            true_df = self.makeDFTree(node.true_value, scope)
            false_df = self.makeDFTree(node.false_value, scope)
            cond_df = self.makeDFTree(node.cond, scope)
            if isinstance(cond_df, DFBranch):
                return reorder.insertCond(cond_df, true_df, false_df)
            return DFBranch(cond_df, true_df, false_df)

        if isinstance(node, UnaryOperator):
            right_df = self.makeDFTree(node.right, scope)
            if isinstance(right_df, DFBranch):
                return reorder.insertUnaryOp(right_df, node.__class__.__name__)
            return DFOperator((right_df,), node.__class__.__name__)

        if isinstance(node, Operator):
            left_df = self.makeDFTree(node.left, scope)
            right_df = self.makeDFTree(node.right, scope)
            if isinstance(left_df, DFBranch) or isinstance(right_df, DFBranch):
                return reorder.insertOp(left_df, right_df, node.__class__.__name__)
            return DFOperator((left_df, right_df,), node.__class__.__name__)

        if isinstance(node, Partselect):
            var_df = self.makeDFTree(node.var, scope)
            msb_df = self.makeDFTree(node.msb, scope)
            lsb_df = self.makeDFTree(node.lsb, scope)

            if isinstance(var_df, DFBranch):
                return reorder.insertPartselect(var_df, msb_df, lsb_df)
            return DFPartselect(var_df, msb_df, lsb_df)

        if isinstance(node, Pointer):
            var_df = self.makeDFTree(node.var, scope)
            ptr_df = self.makeDFTree(node.ptr, scope)

            if isinstance(var_df, DFTerminal) and self.getTermDims(var_df.name) is not None:
                return DFPointer(var_df, ptr_df)
            return DFPartselect(var_df, ptr_df, copy.deepcopy(ptr_df))

        if isinstance(node, Concat):
            nextnodes = []
            for n in node.list:
                nextnodes.append(self.makeDFTree(n, scope))
            for n in nextnodes:
                if isinstance(n, DFBranch):
                    return reorder.insertConcat(tuple(nextnodes))
            return DFConcat(tuple(nextnodes))

        if isinstance(node, Repeat):
            nextnodes = []
            times = self.optimize(self.getTree(node.times, scope)).value
            value = self.makeDFTree(node.value, scope)
            for i in range(int(times)):
                nextnodes.append(copy.deepcopy(value))
            return DFConcat(tuple(nextnodes))

        if isinstance(node, FunctionCall):
            func = self.searchFunction(node.name.name, scope)
            if func is None:
                raise verror.DefinitionError('No such function: %s' % node.name.name)
            label = self.labels.get(self.frames.getLabelKey('functioncall'))

            save_current = self.frames.getCurrent()
            self.frames.setCurrent(scope)

            current = self.frames.addFrame(
                ScopeLabel(label, 'functioncall'),
                functioncall=True, generate=self.frames.isGenerate(),
                always=self.frames.isAlways())

            varname = self.frames.getCurrent() + ScopeLabel(func.name, 'signal')

            self.addTerm(Wire(func.name, func.retwidth))

            funcports = self.searchFunctionPorts(node.name.name, scope)
            funcargs = node.args

            if len(funcports) != len(funcargs):
                raise verror.FormatError("%s takes exactly %d arguments. (%d given)" %
                                         (func.name.name, len(funcports), len(funcargs)))
            for port in funcports:
                self.addTerm(Wire(port.name, port.width))

            lscope = self.frames.getCurrent()
            rscope = scope
            func_i = 0
            for port in funcports:
                arg = funcargs[func_i]
                dst = self.getDestinations(port.name, lscope)
                self.addDataflow(dst, arg, lscope, rscope)
                func_i += 1

            self.visit(func)

            self.frames.setCurrent(current)
            self.frames.setCurrent(save_current)

            return DFTerminal(varname)

        if isinstance(node, TaskCall):
            task = self.searchTask(node.name.name, scope)
            label = self.labels.get(self.frames.getLabelKey('taskcall'))

            current = self.frames.addFrame(
                ScopeLabel(label, 'taskcall'),
                taskcall=True, generate=self.frames.isGenerate(),
                always=self.frames.isAlways())

            varname = self.frames.getCurrent() + ScopeLabel(task.name, 'signal')

            taskports = self.searchTaskPorts(node.name.name, scope)
            taskargs = node.args

            if len(taskports) != len(taskargs):
                raise verror.FormatError("%s takes exactly %d arguments. (%d given)" %
                                         (task.name.name, len(taskports), len(taskargs)))
            for port in taskports:
                self.addTerm(Wire(port.name, port.width))

            lscope = self.frames.getCurrent()
            rscope = scope
            task_i = 0
            for port in taskports:
                arg = taskargs[task_i]
                dst = self.getDestinations(port.name, lscope)
                self.addDataflow(dst, arg, lscope, rscope)
                task_i += 1

            self.visit(taskargs)
            self.frames.setCurrent(current)
            return DFTerminal(varname)

        if isinstance(node, SystemCall):
            if node.syscall == 'unsigned':
                return self.makeDFTree(node.args[0], scope)
            if node.syscall == 'signed':
                return self.makeDFTree(node.args[0], scope)
            return DFIntConst('0')

        raise verror.FormatError("unsupported AST node type: %s %s" %
                                 (str(type(node)), str(node)))

    def reduceIfScope(self, scope):
        if len(scope) == 0:
            return scope
        if scope[-1].scopetype == 'if':
            return scope[:-1]
        return self.reduceIfScope(scope[:-1])

    def resolveCondlist(self, condlist, scope):
        resolved_condlist = []
        reducedscope = self.reduceIfScope(scope)
        for i, c in enumerate(reversed(condlist)):
            resolved_condlist.append(self.resolveBlockingAssign(c, reducedscope))
            reducedscope = self.reduceIfScope(reducedscope)
        return tuple(reversed(resolved_condlist))

    def removeOverwrappedCondition(self, tree, current_bindlist, scope):
        msb, lsb = self.getTermWidth(tree.name)
        merged_tree = self.getFitTree(current_bindlist, msb, lsb)
        condlist, flowlist = self.getCondflow(scope)
        (merged_tree,
         rest_condlist,
         rest_flowlist,
         match_flowlist) = self.diffBranchTree(merged_tree, condlist, flowlist)
        return replace.replaceUndefined(merged_tree, tree.name)

    def resolveBlockingAssign(self, tree, scope):
        if tree is None:
            return None

        if isinstance(tree, DFConstant):
            return tree

        if isinstance(tree, DFEvalValue):
            return tree

        if isinstance(tree, DFTerminal):
            if signaltype.isGenvar(self.getTermtype(tree.name)):
                return self.getConstant(tree.name)

            current_bindlist = self.frames.getBlockingAssign(tree.name, scope)
            if len(current_bindlist) == 0:
                return tree

            return self.removeOverwrappedCondition(tree, current_bindlist, scope)

        if isinstance(tree, DFBranch):
            truenode = self.resolveBlockingAssign(tree.truenode, scope)
            falsenode = self.resolveBlockingAssign(tree.falsenode, scope)
            condnode = self.resolveBlockingAssign(tree.condnode, scope)
            if isinstance(condnode, DFBranch):
                return reorder.insertBranch(condnode, truenode, falsenode)
            return DFBranch(condnode, truenode, falsenode)

        if isinstance(tree, DFOperator):
            resolvednodes = []
            for n in tree.nextnodes:
                resolvednodes.append(self.resolveBlockingAssign(n, scope))
            for r in resolvednodes:
                if isinstance(r, DFBranch):
                    return reorder.insertOpList(resolvednodes, tree.operator)
            return DFOperator(tuple(resolvednodes), tree.operator)

        if isinstance(tree, DFConcat):
            resolvednodes = []
            for n in tree.nextnodes:
                resolvednodes.append(self.resolveBlockingAssign(n, scope))
            for r in resolvednodes:
                if isinstance(r, DFBranch):
                    return reorder.insertConcat(resolvednodes)
            return DFConcat(tuple(resolvednodes))

        if isinstance(tree, DFPartselect):
            resolved_msb = self.resolveBlockingAssign(tree.msb, scope)
            resolved_lsb = self.resolveBlockingAssign(tree.lsb, scope)
            resolved_var = self.resolveBlockingAssign(tree.var, scope)
            if isinstance(resolved_var, DFBranch):
                return reorder.insertPartselect(resolved_var,
                                                resolved_msb, resolved_lsb)
            return DFPartselect(resolved_var, resolved_msb, resolved_lsb)

        if isinstance(tree, DFPointer):
            resolved_ptr = self.resolveBlockingAssign(tree.ptr, scope)
            if (isinstance(tree.var, DFTerminal) and
                    self.getTermDims(tree.var.name) is not None):
                current_bindlist = self.frames.getBlockingAssign(tree.var.name, scope)
                if len(current_bindlist) == 0:
                    return DFPointer(tree.var, resolved_ptr)
                new_tree = DFPointer(tree.var, resolved_ptr)
                for bind in current_bindlist:
                    new_tree = DFBranch(DFOperator((bind.ptr, resolved_ptr), 'Eq'),
                                        bind.tree, new_tree)
                print(("Warning: "
                       "Overwrting Blocking Assignment with Reg Array is not supported"))
                return new_tree
            resolved_var = self.resolveBlockingAssign(tree.var, scope)
            if isinstance(resolved_var, DFBranch):
                return reorder.insertPointer(resolved_var, resolved_ptr)
            return DFPointer(resolved_var, resolved_ptr)

        raise verror.FormatError("unsupported DFNode type: %s %s" %
                                 (str(type(tree)), str(tree)))

    def getFitTree(self, bindlist, msb, lsb):
        optimized_msb = self.optimize(msb)
        optimized_lsb = self.optimize(lsb)
        for bind in bindlist:
            if bind.msb is None and bind.lsb is None:
                return bind.tree
            if (self.optimize(bind.msb) == optimized_msb and
                    self.optimize(bind.lsb) == optimized_lsb):
                return bind.tree
        return self.getMergedTree(bindlist)

    def getMergedTree(self, bindlist):
        concatlist = []
        last_msb = -1
        last_ptr = -1

        def bindkey(x):
            lsb = 0 if x.lsb is None else x.lsb.value
            ptr = 0 if not isinstance(x.ptr, DFEvalValue) else x.ptr.value
            term = self.getTerm(x.dest)
            length = (abs(self.optimize(term.msb).value
                          - self.optimize(term.lsb).value) + 1)
            return ptr * length + lsb
        for bind in sorted(bindlist, key=bindkey):
            lsb = 0 if bind.lsb is None else bind.lsb.value
            if last_ptr != (-1 if not isinstance(bind.ptr, DFEvalValue)
                            else bind.ptr.value):
                continue
            if last_msb + 1 < lsb:
                concatlist.append(DFUndefined(last_msb - lsb - 1))
            concatlist.append(bind.tree)
            last_msb = -1 if bind.msb is None else bind.msb.value
            last_ptr = -1 if not isinstance(bind.ptr, DFEvalValue) else bind.ptr.value
        return DFConcat(tuple(reversed(concatlist)))

    def getDestinations(self, left, scope):
        ret = []
        dst = self.getDsts(left, scope)
        part_offset = DFIntConst('0')
        for name, msb, lsb, ptr in reversed(dst):
            if len(dst) == 1:
                ret.append((name, msb, lsb, ptr, None, None))
                continue

            if msb is None and lsb is None:
                msb, lsb = self.getTermWidth(name)
            diff = reorder.reorder(DFOperator((msb, lsb), 'Minus'))
            part_lsb = part_offset
            part_msb = reorder.reorder(DFOperator((part_offset, diff), 'Plus'))
            part_offset = reorder.reorder(
                DFOperator((part_msb, DFIntConst('1')), 'Plus'))

            ret.append((name, msb, lsb, ptr, part_msb, part_lsb))

        return tuple(ret)

    def getDsts(self, left, scope):
        if isinstance(left, Lvalue):
            return self.getDsts(left.var, scope)
        if isinstance(left, LConcat):
            dst = []
            for n in left.list:
                dst.extend(list(self.getDsts(n, scope)))
            return tuple(dst)
        ret = (self.getDst(left, scope),)
        return ret

    def getDst(self, left, scope):
        if isinstance(left, str):  # Parameter
            name = self.searchTerminal(left, scope)
            return (name, None, None, None)

        if isinstance(left, Identifier):
            name = self.searchTerminal(left.name, scope)
            if name is None:
                m = re.search('none', self.default_nettype)
                if m:
                    raise verror.FormatError("No such signal: %s" % left.name)
                m = re.search('wire', self.default_nettype)
                if m:
                    self.addTerm(Wire(left.name), rscope=scope)
                m = re.search('reg', self.default_nettype)
                if m:
                    self.addTerm(Reg(left.name), rscope=scope)
                name = self.searchTerminal(left.name, scope)
            if left.scope is not None:
                name = left.scope + ScopeLabel(left.name, 'signal')
            return (name, None, None, None)

        if isinstance(left, Partselect):
            if isinstance(left.var, Pointer):
                name, msb, lsb, ptr = self.getDst(left.var, scope)
                if msb is None and lsb is None:
                    msb = self.optimize(self.makeDFTree(left.msb, scope))
                    lsb = self.optimize(self.makeDFTree(left.lsb, scope))
                else:
                    raise verror.FormatError("%s is not array" % str(name))
                return (name, msb, lsb, ptr)
            name = self.searchTerminal(left.var.name, scope)
            if left.var.scope is not None:
                name = left.var.scope + ScopeLabel(left.var.name, 'signal')
            msb = self.optimize(self.makeDFTree(left.msb, scope))
            lsb = self.optimize(self.makeDFTree(left.lsb, scope))
            return (name, msb, lsb, None)

        if isinstance(left, Pointer):
            if isinstance(left.var, Pointer):
                name, msb, lsb, ptr = self.getDst(left.var, scope)
                if msb is None and lsb is None:
                    msb = self.optimize(self.makeDFTree(left.ptr, scope))
                    lsb = copy.deepcopy(msb)
                else:
                    raise verror.FormatError("%s is not array" % str(name))
                return (name, msb, lsb, ptr)
            name = self.searchTerminal(left.var.name, scope)
            if left.var.scope is not None:
                name = left.var.scope + ScopeLabel(left.var.name, 'signal')
            ptr = self.optimize(self.makeDFTree(left.ptr, scope))
            if self.getTermDims(name) is not None:
                return (name, None, None, ptr)
            return (name, ptr, copy.deepcopy(ptr), None)

        raise verror.FormatError("unsupported AST node type: %s %s" %
                                 (str(type(left)), str(left)))

    def setDataflow(self, dst, raw_tree, condlist, flowlist,
                    alwaysinfo=None, bindtype=None):

        for name, msb, lsb, ptr, part_msb, part_lsb in dst:
            bind = self.makeBind(name, msb, lsb, ptr, part_msb, part_lsb,
                                 raw_tree, condlist, flowlist,
                                 num_dst=len(dst),
                                 alwaysinfo=alwaysinfo,
                                 bindtype=bindtype)

            self.dataflow.addBind(name, bind)

            if alwaysinfo is not None:
                self.setNonblockingAssign(name, dst, raw_tree,
                                          msb, lsb, ptr,
                                          part_msb, part_lsb,
                                          alwaysinfo)

    def setDataflow_rename(self, dst, raw_tree, condlist, flowlist,
                           scope, alwaysinfo=None):
        renamed_dst = self.getRenamedDst(dst)
        self.setRenamedTree(renamed_dst, raw_tree, alwaysinfo)
        self.setRenamedFlow(dst, renamed_dst, condlist, flowlist, scope, alwaysinfo)

    def setNonblockingAssign(self, name, dst, raw_tree, msb, lsb, ptr,
                             part_msb, part_lsb, alwaysinfo):
        tree = raw_tree
        if len(dst) > 1:
            tree = reorder.reorder(DFPartselect(raw_tree, part_msb, part_lsb))
        bind = Bind(tree, name, msb, lsb, ptr, alwaysinfo)
        self.frames.addNonblockingAssign(name, bind)

    def getRenamedDst(self, dst):
        renamed_dst = ()
        for d in dst:
            dname = d[0]
            samename_exists = True
            while samename_exists:
                renamed_dname = self.renameVar(dname)
                samename_exists = self.dataflow.hasTerm(renamed_dname)
            term = self.dataflow.getTerm(dname)
            newterm = copy.deepcopy(term)
            newterm.name = renamed_dname
            newterm.termtype = set(['Rename'])
            self.dataflow.addTerm(renamed_dname, newterm)
            newd = (renamed_dname,) + d[1:]
            renamed_dst += (newd,)
        return renamed_dst

    def setRenamedTree(self, renamed_dst, raw_tree, alwaysinfo):
        for name, msb, lsb, ptr, part_msb, part_lsb in renamed_dst:
            tree = raw_tree
            if len(renamed_dst) > 1:
                tree = reorder.reorder(
                    DFPartselect(tree, part_msb, part_lsb))
            bind = Bind(tree, name, msb, lsb, ptr)
            self.dataflow.addBind(name, bind)

            value = self.optimize(tree)
            if isinstance(value, DFEvalValue):
                self.setConstant(name, value)
            msb, lsb = self.getTermWidth(name)
            self.setConstantTerm(name, Term(name, set(['Rename']), msb, lsb))

    def setRenamedFlow(self, dst, renamed_dst, condlist, flowlist,
                       scope, alwaysinfo=None):
        term_i = 0
        for name, msb, lsb, ptr, part_msb, part_lsb in dst:
            renamed_term = DFTerminal(renamed_dst[term_i][0])
            renamed_bind = self.makeBind(name, msb, lsb, ptr, part_msb, part_lsb,
                                         renamed_term, condlist, flowlist,
                                         num_dst=len(dst), alwaysinfo=alwaysinfo)
            self.dataflow.addBind(name, renamed_bind)
            self.frames.setBlockingAssign(name, renamed_bind, scope)
            term_i += 1

    def makeBind(self, name, msb, lsb, ptr, part_msb, part_lsb,
                 raw_tree, condlist, flowlist,
                 num_dst=1, alwaysinfo=None, bindtype=None):

        current_bindlist = self.getBindlist(name)
        current_tree = None
        current_msb = None
        current_lsb = None
        current_ptr = None

        if len(current_bindlist) > 0:
            for current_bind in current_bindlist:
                if (current_bind.msb == msb and
                    current_bind.lsb == lsb
                        and current_bind.ptr == ptr ):
                    current_tree = current_bind.tree
                    current_msb = current_bind.msb
                    current_lsb = current_bind.lsb
                    current_ptr = current_bind.ptr
                    break

        rest_tree = current_tree
        rest_condlist = condlist
        rest_flowlist = flowlist

        match_flowlist = ()
        if (current_msb == msb and
            current_lsb == lsb
                and current_ptr == ptr ):
            (rest_tree,
             rest_condlist,
             rest_flowlist,
             match_flowlist) = self.diffBranchTree(current_tree, condlist, flowlist)

        add_tree = self.makeBranchTree(rest_condlist, rest_flowlist, raw_tree)
        if rest_flowlist and rest_tree is not None:
            _rest_flowlist = rest_flowlist[:-1] + (not rest_flowlist[-1], )
            add_tree = self.appendBranchTree(add_tree, _rest_flowlist, rest_tree)

        tree = reorder.reorder(
            self.appendBranchTree(current_tree, match_flowlist, add_tree))

        if num_dst > 1:
            tree = reorder.reorder(
                DFPartselect(tree, part_msb, part_lsb))

        return Bind(tree, name, msb, lsb, ptr, alwaysinfo, bindtype)

    def diffBranchTree(self, tree, condlist, flowlist, matchflowlist=()):
        if len(condlist) == 0:
            return (tree, condlist, flowlist, matchflowlist)
        if not isinstance(tree, DFBranch):
            return (tree, condlist, flowlist, matchflowlist)
        if condlist[0] != tree.condnode:
            return (tree, condlist, flowlist, matchflowlist)
        if flowlist[0]:
            return self.diffBranchTree(
                tree.truenode, condlist[1:], flowlist[1:],
                matchflowlist + (flowlist[0],))
        else:
            return self.diffBranchTree(
                tree.falsenode, condlist[1:], flowlist[1:],
                matchflowlist + (flowlist[0],))

    def makeBranchTree(self, condlist, flowlist, node):
        if len(condlist) == 0 or len(flowlist) == 0:
            return node
        if len(condlist) == 1:
            if flowlist[0]:
                return DFBranch(condlist[0], node, None)
            else:
                return DFBranch(condlist[0], None, node)
        else:
            if flowlist[0]:
                return DFBranch(
                    condlist[0],
                    self.makeBranchTree(condlist[1:], flowlist[1:], node),
                    None)
            else:
                return DFBranch(
                    condlist[0],
                    None,
                    self.makeBranchTree(condlist[1:], flowlist[1:], node))

    def appendBranchTree(self, base, pos, tree):
        if len(pos) == 0:
            return tree
        if len(pos) == 1:
            if pos[0]:
                return DFBranch(base.condnode, tree, base.falsenode)
            else:
                return DFBranch(base.condnode, base.truenode, tree)
        else:
            if pos[0]:
                return DFBranch(
                    base.condnode,
                    self.appendBranchTree(base.truenode, pos[1:], tree),
                    base.falsenode)
            else:
                return DFBranch(
                    base.condnode,
                    base.truenode,
                    self.appendBranchTree(base.falsenode, pos[1:], tree))
