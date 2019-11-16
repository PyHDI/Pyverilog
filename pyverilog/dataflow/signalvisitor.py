# -------------------------------------------------------------------------------
# signalvisitor.py
#
# Signal definition visitor
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os

from pyverilog.vparser.ast import *
import pyverilog.utils.util as util
import pyverilog.utils.verror as verror
from pyverilog.utils.scope import ScopeLabel, ScopeChain
from pyverilog.dataflow.dataflow import *
from pyverilog.dataflow.visit import *
from pyverilog.dataflow.optimizer import VerilogOptimizer
import pyverilog.dataflow.reorder as reorder


class SignalVisitor(NodeVisitor):
    def __init__(self, moduleinfotable, top):
        self.moduleinfotable = moduleinfotable
        self.top = top
        self.frames = FrameTable()
        self.labels = Labels()
        self.optimizer = VerilogOptimizer({}, {})

        # set the top frame of top module
        self.stackInstanceFrame(top, top)

    def getFrameTable(self):
        return self.frames

    def start_visit(self):
        return self.visit(self.moduleinfotable.getDefinition(self.top))

    def visit_Input(self, node):
        self.frames.addSignal(node)

    def visit_Output(self, node):
        self.frames.addSignal(node)

    def visit_Inout(self, node):
        self.frames.addSignal(node)

    def visit_Reg(self, node):
        self.frames.addSignal(node)

    def visit_Wire(self, node):
        self.frames.addSignal(node)

    def visit_Supply(self, node):
        self.frames.addSignal(node)

    def visit_Tri(self, node):
        self.frames.addSignal(node)

    def visit_Integer(self, node):
        self.frames.addSignal(node)

    def visit_Parameter(self, node):
        self.frames.addConst(node)
        name = self.frames.getCurrent() + ScopeLabel(node.name, 'signal')
        if not self.hasConstant(name):
            value = self.optimize(self.getTree(node.value, self.frames.getCurrent()))
            self.setConstant(name, value)

    def visit_Localparam(self, node):
        self.frames.addConst(node)
        name = self.frames.getCurrent() + ScopeLabel(node.name, 'signal')
        if not self.hasConstant(name):
            value = self.optimize(self.getTree(node.value, self.frames.getCurrent()))
            self.setConstant(name, value)

    def visit_Genvar(self, node):
        self.frames.addConst(node)
        name = self.frames.getCurrent() + ScopeLabel(node.name, 'signal')
        if not self.hasConstant(name):
            value = DFEvalValue(0)
            self.setConstant(name, value)

    def visit_Function(self, node):
        self.frames.addFunction(node)
        self.frames.setFunctionDef()
        self.generic_visit(node)
        self.frames.unsetFunctionDef()

    def visit_Task(self, node):
        self.frames.addTask(node)
        self.frames.setTaskDef()
        self.generic_visit(node)
        self.frames.unsetTaskDef()

    def visit_Initial(self, node):
        pass
        #label = self.labels.get( self.frames.getLabelKey('initial') )
        # current = self.frames.addFrame(ScopeLabel(label, 'initial'),
        #                               generate=self.frames.isGenerate(),
        #                               initial=True)
        # self.generic_visit(node)
        # self.frames.setCurrent(current)

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

        for i in range(lsb, msb + 1):
            nodename = node.name + '_' + str(i)
            self._visit_Instance_body(node, nodename)

    def _visit_Instance_body(self, node, nodename):
        if node.module in primitives:
            return self._visit_Instance_primitive(node)

        if nodename == '':
            raise verror.FormatError("Module %s requires an instance name" % node.module)

        current = self.stackInstanceFrame(nodename, node.module)

        self.setInstanceSimpleConstantTerms()

        scope = self.frames.getCurrent()

        paramnames = self.moduleinfotable.getParamNames(node.module)
        for paramnames_i, param in enumerate(node.parameterlist):
            paramname = paramnames[paramnames_i] if param.paramname is None else param.paramname
            if paramname not in paramnames:
                raise verror.FormatError("No such parameter: %s in %s" %
                                         (paramname, nodename))
            value = self.optimize(self.getTree(param.argname, current))
            name, definition = self.searchConstantDefinition(scope, paramname)
            self.setConstant(name, value)

        self.setInstanceConstants()
        self.setInstanceConstantTerms()

        self.visit(self.moduleinfotable.getDefinition(node.module))
        self.frames.setCurrent(current)

    def _visit_Instance_primitive(self, node):
        pass

    def visit_Always(self, node):
        label = self.labels.get(self.frames.getLabelKey('always'))
        current = self.frames.addFrame(ScopeLabel(label, 'always'),
                                       generate=self.frames.isGenerate(),
                                       always=True)
        self.generic_visit(node)
        self.frames.setCurrent(current)

    def visit_IfStatement(self, node):

        if (self.frames.isGenerate()
            and not self.frames.isAlways() and not self.frames.isInitial()
            and not self.frames.isFunctioncall() and not self.frames.isTaskcall()
                and not self.frames.isFunctiondef() and not self.frames.isTaskdef()):
            # generate-if statement
            current = self.frames.getCurrent()
            tree = self.getTree(node.cond, current)
            rslt = self.optimize(tree)
            if not isinstance(rslt, DFEvalValue):
                raise verror.FormatError("Can not resolve generate-if condition")
            if rslt.value > 0:
                label = self._if_true(node)
            else:
                label = self.labels.get(self.frames.getLabelKey('if'))
                self._if_false(node, label)
            return

        label = self._if_true(node)
        self._if_false(node, label)

    def _toELSE(self, label):
        return label + '_ELSE'

    def _if_true(self, node):
        if node.true_statement is None:
            return None
        label = self.labels.get(self.frames.getLabelKey('if'))
        current = self.frames.addFrame(ScopeLabel(label, 'if'),
                                       frametype='ifthen',
                                       condition=node.cond,
                                       functioncall=self.frames.isFunctioncall(),
                                       taskcall=self.frames.isTaskcall(),
                                       generate=self.frames.isGenerate(),
                                       always=self.frames.isAlways(),
                                       initial=self.frames.isInitial())
        self.visit(node.true_statement)
        self.frames.setCurrent(current)
        return label

    def _if_false(self, node, label):
        if node.false_statement is None:
            return
        label = self._toELSE(label)
        current = self.frames.addFrame(ScopeLabel(label, 'if'),
                                       frametype='ifelse',
                                       condition=node.cond,
                                       functioncall=self.frames.isFunctioncall(),
                                       taskcall=self.frames.isTaskcall(),
                                       generate=self.frames.isGenerate(),
                                       always=self.frames.isAlways(),
                                       initial=self.frames.isInitial())
        self.visit(node.false_statement)
        self.frames.setCurrent(current)
        return label

    def visit_CaseStatement(self, node):
        start_frame = self.frames.getCurrent()
        self._case(node.comp, node.caselist)
        self.frames.setCurrent(start_frame)

    def visit_CasexStatement(self, node):
        return self.visit_CaseStatement(node)

    def _case(self, comp, caselist):
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
        label = self.labels.get(self.frames.getLabelKey('if'))
        current = self.frames.addFrame(ScopeLabel(label, 'if'),
                                       frametype='ifthen',
                                       condition=cond,
                                       functioncall=self.frames.isFunctioncall(),
                                       taskcall=self.frames.isTaskcall(),
                                       generate=self.frames.isGenerate(),
                                       always=self.frames.isAlways(),
                                       initial=self.frames.isInitial())
        if case.statement is not None:
            self.visit(case.statement)
        self.frames.setCurrent(current)
        if len(caselist) == 1:
            return
        label = self._toELSE(label)
        current = self.frames.addFrame(ScopeLabel(label, 'if'),
                                       frametype='ifelse',
                                       condition=cond,
                                       functioncall=self.frames.isFunctioncall(),
                                       taskcall=self.frames.isTaskcall(),
                                       generate=self.frames.isGenerate(),
                                       always=self.frames.isAlways(),
                                       initial=self.frames.isInitial())
        self._case(comp, caselist[1:])

    def visit_ForStatement(self, node):
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
        while True:
            # cond-statement
            current = self.frames.getCurrent()
            tree = self.getTree(node.cond, current)
            rslt = self.optimize(tree)
            if not isinstance(rslt, DFEvalValue):
                raise verror.FormatError(("Can not process the for-statement. "
                                          "for-condition should be evaluated statically."))
            # loop termination
            if rslt.value <= 0:
                break

            # main-statement
            current = self.frames.addFrame(ScopeLabel(label, 'for', loop),
                                           frametype='for',
                                           functioncall=self.frames.isFunctioncall(),
                                           taskcall=self.frames.isTaskcall(),
                                           generate=self.frames.isGenerate(),
                                           always=self.frames.isAlways(),
                                           initial=self.frames.isInitial(),
                                           loop=loop, loop_iter=self.frames.getForIter())
            self.visit(node.statement)
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
        pass

    def visit_GenerateStatement(self, node):
        label = self.labels.get(self.frames.getLabelKey('generate'))
        current = self.frames.addFrame(ScopeLabel(label, 'generate'),
                                       generate=True)
        self.generic_visit(node)
        self.frames.setCurrent(current)

    def visit_Block(self, node):
        label = None
        if node.scope is not None:
            label = node.scope
        else:
            label = self.labels.get(self.frames.getLabelKey('block'))
        current = self.frames.addFrame(ScopeLabel(label, 'block'),
                                       frametype='block',
                                       functioncall=self.frames.isFunctioncall(),
                                       taskcall=self.frames.isTaskcall(),
                                       generate=self.frames.isGenerate(),
                                       always=self.frames.isAlways(),
                                       initial=self.frames.isInitial())
        self.generic_visit(node)
        self.frames.setCurrent(current)

    def visit_Assign(self, node):
        pass

    def visit_BlockingSubstitution(self, node):
        if self.frames.isForpre() or self.frames.isForpost():
            current = self.frames.getCurrent()
            name, definition = self.searchConstantDefinition(current,
                                                             node.left.var.name)
            value = self.optimize(self.getTree(node.right.var, current))
            self.setConstant(name, value)
            self.frames.setForIter(name)

    def visit_NonblockingSubstitution(self, node):
        pass

    def optimize(self, node):
        return self.optimizer.optimize(node)

    def stackInstanceFrame(self, instname, modulename):
        current = self.frames.addFrame(ScopeLabel(instname, 'module'), module=True,
                                       modulename=modulename)
        self.frames.updateSignal(self.moduleinfotable.getSignals(modulename))
        self.frames.updateConst(self.moduleinfotable.getConsts(modulename))
        return current

    def setInstanceSimpleConstantTerms(self):
        current = self.frames.getCurrent()
        for name, definitions in self.frames.getConsts(current).items():
            if len(definitions) > 1:
                raise verror.FormatError("Multiple definitions for Constant")
            for definition in definitions:
                simple_definition = copy.deepcopy(definition)
                if simple_definition.width is not None:
                    simple_definition.width.msb = None
                    simple_definition.width.lsb = None
                term = self.makeConstantTerm(name, simple_definition, current)
                self.setConstantTerm(name, term)

    def setInstanceConstantTerms(self):
        current = self.frames.getCurrent()
        for name, definitions in self.frames.getConsts(current).items():
            if len(definitions) > 1:
                raise verror.FormatError("Multiple definitions for Constant")
            for definition in definitions:
                term = self.makeConstantTerm(name, definition, current)
                self.setConstantTerm(name, term)

    def setInstanceConstants(self):
        current = self.frames.getCurrent()

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

    def setConstant(self, name, value):
        self.optimizer.setConstant(name, value)

    def getConstant(self, name):
        return self.optimizer.getConstant(name)

    def hasConstant(self, name):
        return self.optimizer.hasConstant(name)

    def setConstantTerm(self, name, term):
        self.optimizer.setTerm(name, term)

    def hasConstantTerm(self, name):
        self.optimizer.hasTerm(name)

    def toScopeChain(self, blocklabel):
        scopelist = []
        for b in blocklabel.labellist:
            if b.loop is not None:
                loop = self.optimize(b.loop)
                if not isinstance(loop, DFEvalValue):
                    raise verror.FormatError('Loop iterator should be constant')
                scopelist.append(ScopeLabel(b.name, 'for', loop))
            scopelist.append(ScopeLabel(b.name, 'any'))
        return ScopeChain(scopelist)

    def searchScopeConstantValue(self, blocklabel, name):
        currentmodule = self.frames.getCurrentModuleScopeChain()
        localchain = currentmodule[-1:] + self.toScopeChain(blocklabel)
        matchedchain = self.frames.searchMatchedScopeChain(currentmodule, localchain)
        varname = currentmodule[:-1] + matchedchain + ScopeLabel(name, 'signal')
        const = self.getConstant(varname)
        return const

    # def searchScopeConstantDefinition(self, blocklabel, name):
    #    currentmodule = self.frames.getCurrentModuleScopeChain()
    #    localchain = currentmodule[-1:] + self.toScopeChain(blocklabel)
    #    matchedchain = self.frames.searchMatchedScopeChain(currentmodule, localchain)
    #    constdef = self.frames.getConstantDefinition(matchedchain, name)
    #    return constdef

    def searchConstantDefinition(self, key, name):
        foundkey, founddef = self.frames.searchConstantDefinition(key, name)
        if foundkey is not None:
            return foundkey + ScopeLabel(name, 'signal'), founddef
        foundkey, founddef = self.frames.searchSignalDefinition(key, name)
        if foundkey is not None:
            return foundkey + ScopeLabel(name, 'signal'), founddef
        if foundkey is None:
            raise verror.DefinitionError('constant value not found: %s' % name)

    def searchConstantValue(self, key, name):
        foundkey, founddef = self.searchConstantDefinition(key, name)
        const = self.getConstant(foundkey)
        return const

    def makeConstantTerm(self, name, node, scope):
        termtype = node.__class__.__name__
        termtypes = set([termtype])
        msb = DFIntConst('31') if node.width is None else self.makeDFTree(node.width.msb, scope)
        lsb = DFIntConst('0') if node.width is None else self.makeDFTree(node.width.lsb, scope)
        return Term(name, termtypes, msb, lsb)

    def getTree(self, node, scope):
        expr = node.var if isinstance(node, Rvalue) else node
        return self.makeDFTree(expr, scope)

    def makeDFTree(self, node, scope):
        if isinstance(node, str):
            return self.searchConstantValue(scope, node)

        if isinstance(node, Identifier):
            if node.scope is not None:
                const = self.searchScopeConstantValue(node.scope, node.name)
                return const
            return self.searchConstantValue(scope, node.name)

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

            return DFPointer(var_df, ptr_df)

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

        if isinstance(node, SystemCall):
            if node.syscall == 'unsigned':
                return self.makeDFTree(node.args[0])
            if node.syscall == 'signed':
                return self.makeDFTree(node.args[0])
            return DFIntConst('0')

        raise verror.FormatError("unsupported AST node type: %s %s" %
                                 (str(type(node)), str(node)))
