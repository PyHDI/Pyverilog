# -------------------------------------------------------------------------------
# active_range.py (Obsoluted)
#
# Active condition analyzer from dataflow
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os

import pyverilog.utils.util as util
import pyverilog.utils.signaltype as signaltype
import pyverilog.utils.inference as inference
from pyverilog.dataflow.dataflow import *
import pyverilog.controlflow.splitter as splitter
from pyverilog.controlflow.controlflow_analyzer import VerilogControlflowAnalyzer


class VerilogActiveAnalyzer(VerilogControlflowAnalyzer):
    def __init__(self, topmodule, terms, binddict,
                 resolved_terms, resolved_binddict, constlist):
        VerilogControlflowAnalyzer.__init__(self, topmodule, terms, binddict,
                                            resolved_terms, resolved_binddict, constlist)

    def getActiveConditions(self, termname, op='>', conditionvalue=0):
        if not termname in self.resolved_binddict:
            return ()
        tree = self.makeConditionalTree(termname, step=0)
        funcdict = splitter.split(tree)
        condlists = self.getActiveFuncdictKeys(funcdict, op=op, conditionvalue=conditionvalue)
        active_conditions = self.inferActiveConditions(condlists)
        return active_conditions  # OR-style

    def getChangedConditions(self, termname):
        if not termname in self.resolved_binddict:
            return ()
        bindlist = self.resolved_binddict[termname]
        termtype = self.getTermtype(termname)
        tree = self.makeTree(termname)
        funcdict = splitter.split(tree)
        if len(funcdict) == 0:
            return ()
        changed_condlists = self.getChangedFuncdictKeys(funcdict, termname)
        changed_conditions = self.inferActiveConditions(changed_condlists)
        return changed_conditions

    def getChangedConditionsWithAssignments(self, termname):
        if not termname in self.resolved_binddict:
            return {}
        bindlist = self.resolved_binddict[termname]
        termtype = self.getTermtype(termname)
        tree = self.makeTree(termname)
        funcdict = splitter.split(tree)
        if len(funcdict) == 0:
            return {}
        changed_condfuncs = self.getChangedFuncdict(funcdict, termname)
        changed_conditiondict = self.inferActiveConditionDict(changed_condfuncs)
        return changed_conditiondict

    def getUnchangedConditions(self, termname):
        if not termname in self.resolved_binddict:
            return ()
        bindlist = self.resolved_binddict[termname]
        termtype = self.getTermtype(termname)
        tree = self.makeTree(termname)
        funcdict = splitter.split(tree)
        if len(funcdict) == 0:
            return ()
        unchanged_condlists = self.getUnchangedFuncdictKeys(funcdict, termname)
        unchanged_conditions = self.inferActiveConditions(unchanged_condlists)
        return unchanged_conditions

    def makeConditionalTree(self, termname, step=0):
        tree = self.makeTree(termname)
        return tree

    def getActiveFuncdictKeys(self, funcdict, op='>', conditionvalue=0):
        activekeys = []
        for _condlist, func in funcdict.items():
            condlist = splitter.remove_reset_condlist(_condlist)
            if isinstance(func, DFEvalValue):
                e = eval('func.value' + op + str(conditionvalue))
                if e:
                    activekeys.append(condlist)
        return activekeys

    def getChangedFuncdictKeys(self, funcdict, termname):
        changedkeys = []
        for _condlist, func in funcdict.items():
            condlist = splitter.remove_reset_condlist(_condlist)
            if not (isinstance(func, DFTerminal) and func.name == termname):
                changedkeys.append(condlist)
        return changedkeys

    def getUnchangedFuncdictKeys(self, funcdict, termname):
        unchangedkeys = []
        for _condlist, func in funcdict.items():
            condlist = splitter.remove_reset_condlist(_condlist)
            if isinstance(func, DFTerminal) and func.name == termname:
                unchangedkeys.append(condlist)
        return unchangedkeys

    def getChangedFuncdict(self, funcdict, termname):
        changeddict = {}
        for _condlist, func in funcdict.items():
            condlist = splitter.remove_reset_condlist(_condlist)
            if not (isinstance(func, DFTerminal) and func.name == termname):
                changeddict[condlist] = func
        return changeddict

    def inferActiveConditions(self, condlists):
        active_conditions = []
        for condlist in condlists:
            l = self.inferActiveCondition(condlist)
            if isinstance(l, ActiveTerm):
                activecond = ActiveCondition()
                activecond.set(l.name, l)
                if not (activecond in active_conditions):
                    active_conditions.append(activecond)
            if isinstance(l, ActiveCondition):
                l.resolve()
                if len(l) > 0 and not (l in active_conditions):
                    active_conditions.append(l)
            if isinstance(l, ActiveConditionList):
                for condition in l.conditions:
                    condition.resolve()
                    if not (condition in active_conditions):
                        active_conditions.append(condition)
        return tuple(active_conditions)

    def inferActiveConditionDict(self, condfuncs):
        active_conditions = {}
        for condlist, func in condfuncs.items():
            l = self.inferActiveCondition(condlist)
            if isinstance(l, ActiveTerm):
                if len(l.range_pairs) == 0:
                    continue
                activecond = ActiveCondition()
                activecond.set(l.name, l)
                if not (activecond in active_conditions):
                    active_conditions[activecond] = func
            if isinstance(l, ActiveCondition):
                l.resolve()
                if len(l) > 0 and not (l in active_conditions):
                    active_conditions[l] = func
            if isinstance(l, ActiveConditionList):
                for condition in l.conditions:
                    condition.resolve()
                    if not (condition in active_conditions):
                        active_conditions[condition] = func
        return active_conditions

    def inferActiveCondition(self, condlist):
        condition = None
        for cond in condlist:
            walkrslt = self.walkActiveCond(cond)
            if condition is None:
                condition = walkrslt
            else:
                condition = self._activecond_opAnd(condition, walkrslt)
        return condition

    def walkActiveCond(self, cond):
        if isinstance(cond, DFTerminal):
            return self._walkActiveCond(DFOperator((cond, DFEvalValue(0)), 'GreaterThan'))
        return self._walkActiveCond(cond)

    def _walkActiveCond(self, cond):
        if isinstance(cond, DFOperator):
            if len(cond.nextnodes) == 1:
                return self._walkActiveCond_DFOperator_unary(cond)
            if len(cond.nextnodes) == 2:
                return self._walkActiveCond_DFOperator_dual(cond)
        return None

    def _walkActiveCond_DFOperator_unary(self, cond):
        activecond = self.walkActiveCond(cond.nextnodes[0])
        if signaltype.isNot(cond.operator):
            return self._activecond_opNot(activecond)
        return None

    def _walkActiveCond_DFOperator_dual(self, cond):
        l = cond.nextnodes[0]
        r = cond.nextnodes[1]

        if signaltype.isOr(cond.operator):
            lactivecond = self.walkActiveCond(l)
            ractivecond = self.walkActiveCond(r)
            if lactivecond is None and ractivecond is not None:
                return ractivecond
            if lactivecond is not None and ractivecond is None:
                return lactivecond
            return self._activecond_opOr(lactivecond, ractivecond)

        if signaltype.isAnd(cond.operator):
            lactivecond = self.walkActiveCond(l)
            ractivecond = self.walkActiveCond(r)
            if lactivecond is None and ractivecond is not None:
                return ractivecond
            if lactivecond is not None and ractivecond is None:
                return lactivecond
            return self._activecond_opAnd(lactivecond, ractivecond)

        if isinstance(l, DFTerminal):
            infval = inference.infer(cond.operator, r)
            minval = 0
            maxval = util.maxValue(self.getWidth(l.name))
            range_pairs = ((infval.minval, infval.maxval),)
            return ActiveTerm(l.name, range_pairs, minval, maxval)

        if isinstance(r, DFTerminal):
            new_op = re.sub('Greater', 'TMP', cond.operator)
            new_op = re.sub('Less', 'Greater', new_op)
            new_op = re.sub('TMP', 'Less', new_op)
            infval = inference.infer(new_op, l)
            minval = 0
            maxval = util.maxValue(self.getWidth(r.name))
            range_pairs = ((infval.minval, infval.maxval),)
            return ActiveTerm(r.name, range_pairs, minval, maxval)

        if cond.operator == 'Eq':
            lactivecond = self.walkActiveCond(l)
            ractivecond = self.walkActiveCond(r)
            if lactivecond is not None and ractivecond is None and isinstance(r, DFEvalValue):
                if r.value > 0:
                    return lactivecond
                return self._activecond_opNot(lactivecond)
            if lactivecond is None and ractivecond is not None and isinstance(l, DFEvalValue):
                if l.value > 0:
                    return ractivecond
                return self._activecond_opNot(ractivecond)
            return self._activecond_opAnd(lactivecond, ractivecond)

        if cond.operator == 'NotEq':
            lactivecond = self.walkActiveCond(l)
            ractivecond = self.walkActiveCond(r)
            if lactivecond is not None and ractivecond is None and isinstance(r, DFEvalValue):
                if r.value == 0:
                    return lactivecond
                return self._activecond_opNot(lactivecond)
            if lactivecond is None and ractivecond is not None and isinstance(l, DFEvalValue):
                if l.value == 0:
                    return ractivecond
                return self._activecond_opNot(ractivecond)
            return None
        return None

    def _activecond_opNot(self, node):
        if isinstance(node, ActiveTerm):
            new_node = node
            new_node.opNot()
            return new_node
        if isinstance(node, ActiveCondition):
            activelist = []
            for name, term in node.termdict.items():
                new_term = term
                new_term.opNot()
                new_cond = ActiveCondition()
                new_cond.set(name, new_term)
                activelist.append(new_cond)
            return ActiveConditionList(tuple(activelist))
        if isinstance(node, ActiveConditionList):
            activelist = []
            now_appended = []
            for cnt in range(len(node.conditions)):
                if cnt == 0:
                    continue
                left = node.conditions[cnt - 1]
                right = node.conditions[cnt]
                if cnt == 1:
                    for lname, lterm in left.termdict.items():
                        not_lterm = lterm.opNot()
                        for rname, rterm in right.termdict.items():
                            not_rterm = rterm.opNot()
                            r = self._activecond_opAnd(not_lterm, not_rterm)
                            if r:
                                now_appended.append(r)
                    activelist.extend(now_appended)
                else:
                    left = ActiveConditionList(tuple(now_appended))
                    now_appended = []
                    for lcondition in left.conditions:
                        for rname, rterm in right.termdict.items():
                            not_rterm = rterm.opNot()
                            r = self._activecond_opAnd(lcondition, not_rterm)
                            if r:
                                now_appended.append(r)
                    activelist.extend(now_appended)
            if len(activelist) > 0:
                return ActiveConditionList(tuple(activelist))
        return None

    def _activecond_opAnd(self, left, right):
        if isinstance(left, ActiveTerm):
            return self._activecond_opAnd_right_term(left, right)
        if isinstance(left, ActiveCondition):
            return self._activecond_opAnd_right_condition(left, right)
        if isinstance(left, ActiveConditionList):
            return self._activecond_opAnd_right_conditionlist(left, right)
        return None

    def _activecond_opAnd_right_term(self, left, right):
        if isinstance(right, ActiveTerm):
            new_cond = ActiveCondition()
            new_cond.set(left.name, left)
            new_cond.set(right.name, right)
            return new_cond
        if isinstance(right, ActiveCondition):
            new_cond = ActiveCondition()
            new_cond.set(left.name, left)
            for name, term in right.termdict.items():
                new_cond.set(name, term)
            return new_cond
        if isinstance(right, ActiveConditionList):
            activelist = []
            for condition in right.conditions:
                new_condition = condition
                new_condition.set(left.name, left)
                activelist.append(new_condition)
            return ActiveConditionList(tuple(activelist))
        return None

    def _activecond_opAnd_right_condition(self, left, right):
        if isinstance(right, ActiveTerm):
            new_cond = ActiveCondition()
            for name, term in left.termdict.items():
                new_cond.set(name, term)
            new_cond.set(right.name, right)
            return new_cond
        if isinstance(right, ActiveCondition):
            new_cond = ActiveCondition()
            for name, term in left.termdict.items():
                new_cond.set(name, term)
            for name, term in right.termdict.items():
                new_cond.set(name, term)
            return new_cond
        if isinstance(right, ActiveConditionList):
            activelist = []
            for condition in right.conditions:
                new_condition = self._activecond_opAnd_right_condition(left, condition)
                activelist.append(new_condition)
            return ActiveConditionList(tuple(activelist))
        return None

    def _activecond_opAnd_right_conditionlist(self, left, right):
        if isinstance(right, ActiveTerm):
            activelist = []
            for condition in left.conditions:
                new_condition = condition
                new_condition.set(right.name, right)
                activelist.append(new_condition)
            return ActiveConditionList(tuple(activelist))
        if isinstance(right, ActiveCondition):
            activelist = []
            for condition in left.conditions:
                new_condition = self._activecond_opAnd_right_condition(condition, right)
                activelist.append(new_condition)
            return ActiveConditionList(tuple(activelist))
        if isinstance(right, ActiveConditionList):
            activelist = []
            for rcondition in right.conditions:
                for condition in left.conditions:
                    new_condition = self._activecond_opAnd_right_condition(condition, rcondition)
                    activelist.append(new_condition)
            return ActiveConditionList(tuple(activelist))
        return None

    def _activecond_opOr(self, left, right):
        if isinstance(left, ActiveTerm):
            return self._activecond_opOr_right_term(left, right)
        if isinstance(left, ActiveCondition):
            return self._activecond_opOr_right_condition(left, right)
        if isinstance(left, ActiveConditionList):
            return self._activecond_opOr_right_conditionlist(left, right)
        return None

    def _activecond_opOr_right_term(self, left, right):
        if isinstance(right, ActiveTerm):
            activelist = []
            lactivecond = ActiveCondition()
            lactivecond.set(left.name, left)
            activelist.append(lactivecond)
            ractivecond = ActiveCondition()
            ractivecond.set(right.name, right)
            activelist.append(ractivecond)
            return ActiveConditionList(tuple(activelist))
        if isinstance(right, ActiveCondition):
            activelist = []
            lactivecond = ActiveCondition()
            lactivecond.set(left.name, left)
            activelist.append(lactivecond)
            activelist.append(right)
            return ActiveConditionList(tuple(activelist))
        if isinstance(right, ActiveConditionList):
            activelist = []
            lactivecond = ActiveCondition()
            lactivecond.set(left.name, left)
            activelist.append(lactivecond)
            for condition in right.conditions:
                activelist.append(condition)
            return ActiveConditionList(tuple(activelist))
        return None

    def _activecond_opOr_right_condition(self, left, right):
        if isinstance(right, ActiveTerm):
            activelist = []
            activelist.append(left)
            ractivecond = ActiveCondition()
            ractivecond.set(right.name, right)
            activelist.append(ractivecond)
            return ActiveConditionList(tuple(activelist))
        if isinstance(right, ActiveCondition):
            activelist = []
            activelist.append(left)
            activelist.append(right)
            return ActiveConditionList(tuple(activelist))
        if isinstance(right, ActiveConditionList):
            activelist = []
            activelist.append(left)
            for condition in right.conditions:
                activelist.append(condition)
            return ActiveConditionList(tuple(activelist))
        return None

    def _activecond_opOr_right_conditionlist(self, left, right):
        if isinstance(right, ActiveTerm):
            activelist = []
            for condition in left.conditions:
                activelist.append(condition)
            ractivecond = ActiveCondition()
            ractivecond.set(right.name, right)
            activelist.append(ractivecond)
            return ActiveConditionList(tuple(activelist))
        if isinstance(right, ActiveCondition):
            activelist = []
            for condition in left.conditions:
                activelist.append(condition)
            activelist.append(right)
            return ActiveConditionList(tuple(activelist))
        if isinstance(right, ActiveConditionList):
            activelist = []
            for condition in left.conditions:
                activelist.append(condition)
            for condition in right.conditions:
                activelist.append(condition)
            return ActiveConditionList(tuple(activelist))
        return None


class ActiveTerm(object):
    def __init__(self, name, range_pairs=(), minval=0, maxval=0):
        self.name = name
        self.range_pairs = range_pairs
        self.minval = minval
        self.maxval = maxval

    def set(self, range_pairs):
        self.range_pairs = range_pairs

    def __eq__(self, o):
        return self.name == o.name and self.range_pairs == o.range_pairs and self.minval == o.minval and self.maxval == o.maxval

    def opNot(self):
        if len(self.range_pairs) > 0:
            self._inv_range_pairs()

    def _inv_range_pairs(self):
        new_range_pairs = []
        cur_min = self.minval
        for rmin, rmax in sorted(self.range_pairs, key=lambda x: x[0]):
            if rmax is None:
                rmax = self.maxval
            if rmin - 1 >= cur_min:
                new_range_pairs.append((cur_min, rmin - 1))
            cur_min = max(rmax + 1, cur_min)
        if cur_min <= self.maxval:
            new_range_pairs.append((cur_min, self.maxval))
        self.range_pairs = tuple(new_range_pairs)

    def __repr__(self):
        ret = '('
        ret += util.toFlatname(self.name) + ' '
        for rmin, rmax in self.range_pairs:
            ret += str(rmin) + ':' + str(rmax) + ', '
        ret = ret[:-2]
        ret += ')'
        return ret

    def tocode(self):
        ret = '('
        for rmin, rmax in self.range_pairs:
            ret += '('
            ret += str(rmin) + '<=' + util.toFlatname(self.name)
            if rmax is not None:
                ret += '&&'
                ret += util.toFlatname(self.name) + '<=' + str(rmax)
            ret += ')'
            ret += '||'
        return ret[:-2] + ')'

    def toTree(self):
        retnode = None
        for rmin, rmax in self.range_pairs:
            if rmax is None:
                t = DFOperator((DFEvalValue(rmin), DFTerminal(self.name)), 'LessEq')
                if retnode is None:
                    retnode = t
                else:
                    retnode = DFOperator((retnode, t), 'Lor')
            else:
                t = DFOperator((DFOperator((DFEvalValue(rmin), DFTerminal(self.name)), 'LessEq'), DFOperator(
                    (DFTerminal(self.name), DFEvalValue(rmax)), 'GreaterEq')), 'Land')
                if retnode is None:
                    retnode = t
                else:
                    retnode = DFOperator((retnode, t), 'Lor')
        return retnode

    def include(self, termname):
        if termname == self.name:
            return True
        return False

    def satisfy(self, value):
        for rmin, rmax in sorted(self.range_pairs, key=lambda x: x[0]):
            if rmin <= value and value <= rmax:
                return True
        return False


class ActiveCondition(object):
    def __init__(self):
        self.termdict = {}

    def has(self, name):
        return name in self.termdict

    def set(self, name, term):
        if not self.has(name):
            self.termdict[name] = term
            return
        self._andTerm(name, term)

    def empty(self):
        return len(self.termdict) == 0

    def resolve(self):
        new_termdict = {}
        for name, term in self.termdict.items():
            if len(term.range_pairs) == 0:
                continue
            new_termdict[name] = term
        self.termdict = new_termdict

    def tocode(self):
        if len(self.termdict) == 0:
            return '1'
        ret = '('
        for name, term in self.termdict.items():
            ret += term.tocode()
            ret += '&&'
        return ret[:-2] + ')'

    def toTree(self):
        if len(self.termdict) == 0:
            return DFEvalValue(1)
        retnode = None
        for name, term in self.termdict.items():
            t = term.toTree()
            if retnode is None:
                retnode = t
            else:
                retnode = DFOperator((retnode, t), 'Land')
        return retnode

    def __repr__(self):
        if len(self.termdict) == 0:
            return '(empty)'
        ret = '('
        for name, term in sorted(self.termdict.items(), key=lambda x: str(x[0])):
            ret += term.__repr__() + ' && '
        ret = ret[:-4] + ')'
        return ret

    def __len__(self):
        return len(self.termdict)

    def _andTerm(self, name, term):
        current_term = self.termdict[name]
        new_range_pairs = self._and_range_pairs(current_term, term)
        self.termdict[name].set(new_range_pairs)

    def _and_range_pairs(self, sna, snb):
        range_pairs = []
        a_ptr = 0
        b_ptr = 0
        sorted_sna = sorted(sna.range_pairs, key=lambda x: x[0])
        sorted_snb = sorted(snb.range_pairs, key=lambda x: x[0])
        if len(sorted_sna) == 0:
            return ()
        if len(sorted_snb) == 0:
            return ()
        amin, amax = sorted_sna[a_ptr]
        bmin, bmax = sorted_snb[b_ptr]
        last_a_ptr = -1
        last_b_ptr = -1
        while True:
            next_min = max(amin, bmin)
            next_max = min(amax, bmax)
            if bmax < amin or bmin > amax:
                pass
            else:
                range_pairs.append((next_min, next_max))
            if amax >= bmax and b_ptr < len(sorted_snb) - 1:
                b_ptr += 1
                bmin, bmax = sorted_snb[b_ptr]
            elif amax <= bmax and a_ptr < len(sorted_sna) - 1:
                a_ptr += 1
                amin, amax = sorted_sna[a_ptr]
            if a_ptr == last_a_ptr and b_ptr == last_b_ptr:
                break
            last_a_ptr = a_ptr
            last_b_ptr = b_ptr
        ret_set = set(range_pairs)
        ret_list = tuple(ret_set)
        return ret_list

    def include(self, termname):
        for name, term in self.termdict.items():
            if term.include(termname):
                return True
        return False

    def split(self, termname):
        termdict_including = {}
        termdict_excluding = {}
        for name, term in self.termdict.items():
            if term.include(termname):
                termdict_including[name] = term
            else:
                termdict_excluding[name] = term
        including = ActiveCondition()
        including.termdict = termdict_including
        excluding = ActiveCondition()
        excluding.termdict = termdict_excluding
        return including, excluding

    def satisfy(self, valuedict):
        for termname, value in valuedict.items():
            if not termname in self.termdict:
                continue
            if not self.termdict[termname].satisfy(value):
                return False
        return True


class ActiveConditionList(object):
    def __init__(self, conditions=()):
        self.conditions = conditions

    def __len__(self):
        return len(self.conditions)

    def __repr__(self):
        ret = ''
        for c in self.conditions:
            ret += c.__repr__() + ' || '
        ret = ret[:-4] + ''
        return ret

    def andterm(self, name, term):
        if len(self.conditions) == 0:
            self.conditions = (term,)
        else:
            for condition in self.conditions:
                condition.set(name, term)

    def include(self, termname):
        for condition in self.conditions:
            if condition.include(termname):
                return True
        return False
