# -------------------------------------------------------------------------------
# optimizer.py
#
# Dataflow optimizer
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import math

import pyverilog.utils.verror as verror
import pyverilog.utils.signaltype as signaltype
from pyverilog.dataflow.dataflow import *


class VerilogOptimizer(object):
    default_width = 32
    compare_ops = ('LessThan', 'GreaterThan', 'LassEq', 'GreaterEq', 'Eq', 'NotEq', 'Eql', 'NotEql')

    def __init__(self, terms, constlist=None, default_width=32, level=2):
        self.terms = terms
        self.constlist = constlist if constlist is not None else {}
        self.default_width = default_width
        self.level = level

    def setConstant(self, name, value):
        self.constlist[name] = value

    def resetConstant(self, name):
        if name in self.constlist:
            del self.constlist[name]

    def getConstant(self, name):
        if not name in self.constlist:
            raise verror.DefinitionError('constant value not found: %s' % str(name))
        return self.constlist[name]

    def hasConstant(self, name):
        return name in self.constlist

    def getConstlist(self):
        return self.constlist

    def setTerm(self, name, term):
        self.terms[name] = term

    def getTerm(self, name):
        return self.terms[name]

    def hasTerm(self, name):
        return name in self.terms

    def optimize(self, tree):
        t = tree
        for i in range(self.level):
            t = self.optimizeConstant(t)
            t = self.optimizeHierarchy(t)
        return t

    def optimizeConstant(self, tree):
        if tree is None:
            return None
        if isinstance(tree, DFBranch):
            condnode = self.optimizeConstant(tree.condnode)
            truenode = self.optimizeConstant(tree.truenode)
            falsenode = self.optimizeConstant(tree.falsenode)
            if isinstance(condnode, DFEvalValue):
                if self.isCondTrue(condnode):
                    return truenode
                return falsenode
            return DFBranch(condnode, truenode, falsenode)

        if isinstance(tree, DFEvalValue):
            return tree
        if isinstance(tree, DFUndefined):
            return tree
        if isinstance(tree, DFHighImpedance):
            return tree
        if isinstance(tree, DFDelay):
            raise FormatError('Can not evaluate and optimize a DFDelay')
            # return tree

        if isinstance(tree, DFIntConst):
            if 'x' in tree.value or 'z' in tree.value:
                return DFUndefined(tree.width())
            if 'X' in tree.value or 'Z' in tree.value:
                return DFUndefined(tree.width())
            return DFEvalValue(tree.eval(), tree.width())
        if isinstance(tree, DFFloatConst):
            return DFEvalValue(tree.eval(), self.default_width, isfloat=True)
        if isinstance(tree, DFStringConst):
            return DFEvalValue(tree.eval(), None, isstring=True)
        if isinstance(tree, DFConstant):
            if 'x' in tree.value or 'z' in tree.value:
                return DFUndefined()
            if 'X' in tree.value or 'Z' in tree.value:
                return DFUndefined()
            return DFEvalValue(tree.eval(), self.default_width)

        if isinstance(tree, DFOperator):
            nextnodes_rslts, all_const = self.evalNextnodes(tree.nextnodes)
            if all_const:
                evalop = self.evalOperator(tree.operator, nextnodes_rslts)
                if evalop is not None:
                    return evalop
            return DFOperator(tuple(nextnodes_rslts), tree.operator)

        if isinstance(tree, DFTerminal):
            if not self.hasConstant(tree.name):
                return tree
            msb = self.getTerm(tree.name).msb
            lsb = self.getTerm(tree.name).lsb
            const = self.getConstant(tree.name)
            constwidth = const.width
            if msb is not None and lsb is not None:
                msb_val = self.optimizeConstant(msb)
                lsb_val = self.optimizeConstant(lsb)
                if isinstance(msb_val, DFEvalValue) and isinstance(lsb_val, DFEvalValue):
                    constwidth = msb_val.value - lsb_val.value + 1
            return DFEvalValue(const.value, constwidth)

        if isinstance(tree, DFConcat):
            nextnodes_rslts, all_const = self.evalNextnodes(tree.nextnodes)
            if all_const:
                evalcc = self.evalConcat(nextnodes_rslts)
                if evalcc is not None:
                    return evalcc
            return DFConcat(tuple(nextnodes_rslts))

        if isinstance(tree, DFPartselect):
            var = self.optimizeConstant(tree.var)
            msb = self.optimizeConstant(tree.msb)
            lsb = self.optimizeConstant(tree.lsb)
            if isinstance(var, DFEvalValue) and isinstance(msb, DFEvalValue) and isinstance(msb, DFEvalValue):
                evalcc = self.evalPartselect(var, msb, lsb)
                return evalcc
            return DFPartselect(var, msb, lsb)

        if isinstance(tree, DFPointer):
            if not isinstance(tree.var, DFTerminal):
                return tree
            term = self.getTerm(tree.var.name)
            var = self.optimizeConstant(tree.var)
            ptr = self.optimizeConstant(tree.ptr)
            if term.dims is not None:
                return DFPointer(var, ptr)
            if isinstance(var, DFEvalValue) and isinstance(ptr, DFEvalValue):
                evalcc = self.evalPointer(var, ptr)
                return evalcc
            return DFPointer(var, ptr)

        if isinstance(tree, DFSyscall):
            return DFSyscall(tree.syscall, tuple([self.optimizeConstant(n) for n in tree.nextnodes]))

        raise verror.DefinitionError('Can not optimize the tree: %s %s' %
                                     (str(type(tree)), str(tree)))

    def evalNextnodes(self, nextnodes):
        ret = []
        all_const = True
        for n in nextnodes:
            rslt = self.optimizeConstant(n)
            ret.append(rslt)
            if not isinstance(rslt, DFEvalValue):
                all_const = False
        return tuple(ret), all_const

    def evalOperator(self, operator, nextnodes):
        valuelist = []
        width = 0
        for n in nextnodes:
            if not isinstance(n, DFEvalValue):
                return None
            valuelist.append(n.value)
            if n.width > width:
                width = n.width
        rslt = self._evalOperator(operator, tuple(valuelist), width)
        return DFEvalValue(rslt, width)

    def _evalOperator(self, operator, valuelist, width=default_width):
        if operator == 'Uminus':
            return -1 * valuelist[0]
        if operator == 'Ulnot':
            if valuelist[0] == 0:
                return 1
            return 0
        if operator == 'Unot':
            retval = 0
            for i in range(width):
                if valuelist[0] & (1 << i) == 0:
                    retval |= (1 << i)
            return retval
        if operator == 'Uand':
            for i in range(width):
                if valuelist[0] & (1 << i) == 0:
                    return 0
            return 1
        if operator == 'Unand':
            for i in range(width):
                if valuelist[0] & (1 << i) == 0:
                    return 1
            return 0
        if operator == 'Uor':
            for i in range(width):
                if valuelist[0] & (1 << i) != 0:
                    return 1
            return 0
        if operator == 'Unor':
            for i in range(width):
                if valuelist[0] & (1 << i) != 0:
                    return 0
            return 1
        if operator == 'Uxor':
            rslt = 0
            for i in range(width):
                if valuelist[0] & (1 << i) != 0:
                    rslt = 1 if rslt == 0 else 0
            return rslt
        if operator == 'Uxnor':
            rslt = 1
            for i in range(width):
                if valuelist[0] & (1 << i) != 0:
                    rslt = 1 if rslt == 0 else 0
            return rslt
        if operator == 'Power':
            return valuelist[0] ** valuelist[1]
        if operator == 'Times':
            return valuelist[0] * valuelist[1]
        if operator == 'Divide':
            value = valuelist[0] / valuelist[1]
            if isinstance(valuelist[0], int) and isinstance(valuelist[1], int):
                return int(value)
            return value
        if operator == 'Mod':
            return valuelist[0] % valuelist[1]
        if operator == 'Plus':
            return valuelist[0] + valuelist[1]
        if operator == 'Minus':
            return valuelist[0] - valuelist[1]
        if operator == 'Sll':
            return valuelist[0] << valuelist[1]
        if operator == 'Srl':
            return valuelist[0] >> valuelist[1]
        if operator == 'Sra':
            return valuelist[0] >> valuelist[1]

        if operator == 'LessThan':
            return 1 if valuelist[0] < valuelist[1] else 0
        if operator == 'GreaterThan':
            return 1 if valuelist[0] > valuelist[1] else 0
        if operator == 'LessEq':
            return 1 if valuelist[0] <= valuelist[1] else 0
        if operator == 'GreaterEq':
            return 1 if valuelist[0] >= valuelist[1] else 0
        if operator == 'Eq':
            return 1 if valuelist[0] == valuelist[1] else 0
        if operator == 'NotEq':
            return 1 if valuelist[0] != valuelist[1] else 0
        if operator == 'Eql':
            return 1 if valuelist[0] == valuelist[1] else 0
        if operator == 'NotEql':
            return 1 if valuelist[0] != valuelist[1] else 0
        if operator == 'And':
            return valuelist[0] & valuelist[1]
        if operator == 'Xor':
            return valuelist[0] ^ valuelist[1]
        if operator == 'Xnor':
            return ~(valuelist[0] ^ valuelist[1])
        if operator == 'Or':
            return valuelist[0] | valuelist[1]
        if operator == 'Land':
            return 1 if valuelist[0] and valuelist[1] else 0
        if operator == 'Lor':
            return 1 if valuelist[0] or valuelist[1] else 0
        return None

    def getWidth(self, node):
        if node is None:
            return self.default_width
        if isinstance(node, DFUndefined):
            if node.width is not None:
                return node.width
            return self.default_width
        if isinstance(node, DFHighImpedance):
            if node.width is not None:
                return node.width
            return self.default_width
        if isinstance(node, DFIntConst):
            return node.width()
        if isinstance(node, DFConstant):
            return self.default_width
        if isinstance(node, DFEvalValue):
            if node.width is not None:
                return node.width
            return self.default_width
        if isinstance(node, DFTerminal):
            term = self.getTerm(node.name)
            msb = self.optimizeConstant(term.msb).value
            lsb = self.optimizeConstant(term.lsb).value
            width = abs(msb - lsb) + 1
            return width

        if isinstance(node, DFBranch):
            truewidth = self.getWidth(node.truenode)
            falsewidth = self.getWidth(node.falsenode)
            return max(truewidth, falsewidth)

        if isinstance(node, DFPartselect):
            msb = self.optimizeConstant(node.msb).value
            lsb = self.optimizeConstant(node.lsb).value
            width = abs(msb - lsb) + 1
            return width
        if isinstance(node, DFOperator):
            if node.operator in self.compare_ops:
                return 1
            if node.operator == 'Land' or node.operator == 'Lor':
                return 1
            maxwidth = 0
            for n in node.nextnodes:
                width = self.getWidth(n)
                if maxwidth < width:
                    maxwidth = width
            return maxwidth
        if isinstance(node, DFConcat):
            sumwidth = 0
            for n in node.nextnodes:
                width = self.getWidth(n)
                sumwidth += width
            return sumwidth
        if isinstance(node, DFPointer):
            if not isinstance(node.var, DFTerminal):
                return 1
            term = self.getTerm(node.var.name)
            if term.dims is not None:
                msb = self.optimizeConstant(term.msb).value
                lsb = self.optimizeConstant(term.lsb).value
                width = abs(msb - lsb) + 1
                return width
            return 1
        if isinstance(tree, DFSyscall):
            return self.default_width

        raise FormatError('Illegal Pointer in getWidth()')

    def evalConcat(self, nextnodes):
        concatval = 0
        sum_width = 0
        for node in nextnodes:
            width = self.getWidth(node)
            sum_width += width
            concatval = (concatval << width) | node.value
        return DFEvalValue(concatval, sum_width)

    def isCondTrue(self, cond):
        if not isinstance(cond, DFEvalValue):
            raise FormatError('Can not evaluate the branch condition.')
        if cond.value == 0:
            return False
        return True

    def evalPartselect(self, var, msb, lsb):
        width = msb.value - lsb.value + 1
        partval = var.value >> lsb.value
        if partval >= 2 ** width:
            partval = partval % (2 ** width)
        return DFEvalValue(partval, width)

    def evalPointer(self, var, ptr):
        ptrval = (var >> ptr) & 0x1
        return DFEvalValue(ptrval, 1)

    def optimizeHierarchy(self, tree):
        if tree is None:
            return None
        if isinstance(tree, DFIntConst):
            return tree
        if isinstance(tree, DFFloatConst):
            return tree
        if isinstance(tree, DFStringConst):
            return tree
        if isinstance(tree, DFEvalValue):
            return tree
        if isinstance(tree, DFUndefined):
            return tree
        if isinstance(tree, DFHighImpedance):
            return tree
        if isinstance(tree, DFTerminal):
            return tree
        if isinstance(tree, DFBranch):
            condnode = self.optimizeHierarchy(tree.condnode)
            truenode = self.optimizeHierarchy(tree.truenode)
            falsenode = self.optimizeHierarchy(tree.falsenode)
            if isinstance(condnode, DFEvalValue):
                if self.isCondTrue(condnode):
                    return truenode
                return falsenode
            if truenode == falsenode:
                return truenode
            return DFBranch(condnode, truenode, falsenode)
        if isinstance(tree, DFOperator):
            nextnodes = []
            for n in tree.nextnodes:
                nextnodes.append(self.optimizeHierarchy(n))
            ret = DFOperator(tuple(nextnodes), tree.operator)
            ret = self.replaceOperator(ret)
            ret = self.mergeIdenticalNodes(ret)
            ret = self.mergeStaticNodes(ret)
            ret = self.mergeLandLor(ret)
            return ret
        if isinstance(tree, DFPartselect):
            msb = self.optimizeHierarchy(tree.msb)
            lsb = self.optimizeHierarchy(tree.lsb)
            var = self.optimizeHierarchy(tree.var)
            if isinstance(var, DFConcat) and isinstance(msb, DFEvalValue) and isinstance(lsb, DFEvalValue):
                return self.takePart(var.nextnodes, msb, lsb)
            if isinstance(msb, DFEvalValue) and isinstance(lsb, DFEvalValue) and lsb.value == 0 and self.getWidth(var) == (msb.value + 1):
                return var
            return DFPartselect(var, msb, lsb)
        if isinstance(tree, DFPointer):
            ptr = self.optimizeHierarchy(tree.ptr)
            var = self.optimizeHierarchy(tree.var)
            if isinstance(var, DFConcat) and isinstance(ptr, DFEvalValue):
                return self.takePoint(var.nextnodes, ptr)
            return DFPointer(var, ptr)
        if isinstance(tree, DFConcat):
            nextnodes = []
            for n in tree.nextnodes:
                if isinstance(n, DFConcat):
                    nextnodes.extend(n.nextnodes)
                    continue
                nextnodes.append(self.optimizeHierarchy(n))
            return self.mergeConcat(DFConcat(tuple(nextnodes)))
        if isinstance(tree, DFSyscall):
            return DFSyscall(tree.syscall, tuple([self.optimizeHierarchy(n) for n in tree.nextnodes]))

        raise FormatError('Can not merge due to unrecognized type of tree')

    def takePoint(self, nextnodes, ptr):
        return self.takePart(nextnodes, ptr, ptr)

    def takePart(self, nextnodes, msb, lsb):
        widlist = []
        for n in reversed(nextnodes):  # from LSB
            widlist.append(self.getWidth(n))
        lsbcut = min(msb.value, lsb.value)
        msbcut = max(msb.value, lsb.value)
        cutwidth = msbcut - lsbcut + 1

        widsum = 0
        widpos = 1
        widoffset = 0
        usednodes = []
        lsb = -1
        msb = -1
        lsboffset = -1
        msboffset = -1
        use = False
        for w in widlist:  # from LSB
            if lsbcut >= widoffset and lsbcut < widoffset + w:
                lsb = widoffset
                lsboffset = lsbcut - lsb
                use = True
            if use:
                widsum += w
                usednodes.append(self.optimizeConstant(nextnodes[-widpos]))
            if msbcut >= widoffset and msbcut < widoffset + w:
                msb = widoffset + w - 1
                msboffset = msb - msbcut
                break
            widpos += 1
            widoffset += w

        usednodes.reverse()

        if len(usednodes) == 0:
            return DFUndefined(cutwidth)
        if msboffset < 0:
            if lsboffset == 0:
                return DFConcat((DFUndefined(cutwidth - widsum),) + tuple(usednodes))
            if len(usednodes) == 1:
                return DFConcat((DFUndefined(cutwidth - widsum + lsboffset), DFPartselect(usednodes[0], DFEvalValue(widsum - 1), DFEvalValue(lsb + lsboffset))))
            return DFConcat((DFUndefined(cutwidth - widsum + lsboffset), DFPartselect(DFConcat(tuple(usednodes)), DFEvalValue(widsum - 1), DFEvalValue(lsb + lsboffset))))
        if lsboffset == 0 and msboffset == 0:
            if len(usednodes) == 1:
                return usednodes[0]
            return DFConcat(tuple(usednodes))

        if len(usednodes) == 1:
            return DFPartselect(usednodes[0], DFEvalValue(msb - msboffset), DFEvalValue(lsb + lsboffset))

        ret_usednodes = []
        usednodes_cnt = 0
        for node in reversed(usednodes):  # from LSB
            if usednodes_cnt == 0 and lsboffset > 0:
                lsbval = lsboffset
                msbval = widlist[usednodes_cnt] - 1
                ret_usednodes.append(self.optimizeConstant(
                    DFPartselect(node, DFEvalValue(msbval), DFEvalValue(lsbval))))
            elif usednodes_cnt == len(usednodes) - 1 and msboffset > 0:
                lsbval = 0
                msbval = widlist[usednodes_cnt] - msboffset - 1
                ret_usednodes.append(self.optimizeConstant(
                    DFPartselect(node, DFEvalValue(msbval), DFEvalValue(lsbval))))
            else:
                ret_usednodes.append(self.optimizeConstant(node))
            usednodes_cnt += 1
        ret_usednodes.reverse()
        return DFPartselect(DFConcat(tuple(ret_usednodes)), DFEvalValue(msb - msboffset), DFEvalValue(lsb + lsboffset))

    def _isPowerOf2(self, value):
        if value <= 0:
            return False
        p = math.log(value, 2)
        if p % 1.0 == 0:
            return True
        return False

    def replaceOperator(self, node):
        if not isinstance(node, DFOperator):
            return node
        if (node.operator == 'Times' and
            (isinstance(node.nextnodes[1], DFEvalValue) and
             isinstance(node.nextnodes[1].value, int) and
             self._isPowerOf2(node.nextnodes[1].value))):
            return DFOperator((node.nextnodes[0], DFEvalValue(int(math.log(node.nextnodes[1].value, 2)))), 'Sll')
        if (node.operator == 'Times' and
            (isinstance(node.nextnodes[0], DFEvalValue) and
             isinstance(node.nextnodes[0].value, int) and
             self._isPowerOf2(node.nextnodes[0].value))):
            return DFOperator((node.nextnodes[1], DFEvalValue(int(math.log(node.nextnodes[0].value, 2)))), 'Sll')
        if (node.operator == 'Divide'
            and (isinstance(node.nextnodes[1], DFEvalValue) and
             isinstance(node.nextnodes[1].value, int) and
                 self._isPowerOf2(node.nextnodes[1].value))):
            return DFOperator((node.nextnodes[0], DFEvalValue(int(math.log(node.nextnodes[1].value, 2)))), 'Sra')
        return node

    def mergeConcat(self, concatnode):
        t = concatnode
        if isinstance(t, DFConcat):
            t = self.mergeConcat_constant(t)
        if isinstance(t, DFConcat):
            t = self.mergeConcat_undefined(t)
        if isinstance(t, DFConcat):
            t = self.mergeConcat_partselect(t)
        if isinstance(t, DFConcat):
            t = self.mergeConcat_branch(t)
        return t

    def mergeConcat_constant(self, concatnode):
        ret_nodes = []
        constvallist = []
        constval = 0
        for n in concatnode.nextnodes:
            if isinstance(n, DFEvalValue):
                constvallist.append(n)
                constval = self.evalConcat(tuple(constvallist))
                if len(constvallist) > 1:
                    ret_nodes.pop()
                ret_nodes.append(constval)
            else:
                constvallist = []
                ret_nodes.append(n)
        return DFConcat(tuple(ret_nodes))

    def mergeConcat_undefined(self, concatnode):
        ret_nodes = []
        width = 0
        for n in concatnode.nextnodes:
            if isinstance(n, DFUndefined):
                if width > 0:
                    ret_nodes.pop()
                width += self.getWidth(n)
                ret_nodes.append(DFUndefined(width))
            else:
                width = 0
                ret_nodes.append(n)
        return DFConcat(tuple(ret_nodes))

    def mergeConcat_partselect(self, concatnode):
        ret_nodes = []
        last_node = None
        for n in concatnode.nextnodes:
            if last_node is None:
                pass
            elif not isinstance(last_node, DFPartselect):
                pass
            elif not isinstance(n, DFPartselect):
                pass
            elif not isinstance(last_node.var, DFTerminal):
                pass
            elif not isinstance(n.var, DFTerminal):
                pass
            elif last_node.var.name != n.var.name:
                pass
            elif last_node.lsb.value == n.msb.value + 1:
                ret_nodes.pop()
                new_node = DFPartselect(last_node.var, last_node.msb, n.lsb)
                if self.getWidth(last_node.var) == (last_node.msb.value - n.lsb.value + 1):
                    new_node = last_node.var
                ret_nodes.append(new_node)
                last_node = new_node
                continue
            ret_nodes.append(n)
            last_node = n
        if len(ret_nodes) == 1:
            return ret_nodes[0]
        return DFConcat(tuple(ret_nodes))

    def mergeConcat_branch(self, concatnode):
        nodelist = []
        last_node = None
        for n in concatnode.nextnodes:
            if last_node is None:
                pass
            elif not isinstance(last_node, DFBranch):
                pass
            elif not isinstance(n, DFBranch):
                pass
            elif last_node.condnode == n.condnode:
                truenode_list = (last_node.truenode, n.truenode)
                falsenode_list = (last_node.falsenode, n.falsenode)
                new_truenode_list = []
                new_falsenode_list = []
                pos = 0
                for t in truenode_list:
                    if t is None:
                        new_truenode_list.append(DFUndefined(self.getWidth(falsenode_list[pos])))
                    else:
                        new_truenode_list.append(t)
                    pos += 1

                pos = 0
                for f in falsenode_list:
                    if f is None:
                        new_falsenode_list.append(DFUndefined(self.getWidth(truenode_list[pos])))
                    else:
                        new_falsenode_list.append(f)
                    pos += 1

                new_node = DFBranch(last_node.condnode, DFConcat(
                    tuple(new_truenode_list)), DFConcat(tuple(new_falsenode_list)))
                last_node = new_node
                nodelist.pop()
                nodelist.append(new_node)
                continue
            nodelist.append(n)
            last_node = n
        if len(nodelist) == 1:
            return nodelist[0]
        return DFConcat(tuple(nodelist))

    def mergeIdenticalNodes(self, node):
        if not isinstance(node, DFOperator):
            return node
        if len(node.nextnodes) == 1:
            return node
        if not (node.nextnodes[0] == node.nextnodes[1]):
            return node
        if node.operator == 'And':
            return node.nextnodes[0]
        if node.operator == 'Or':
            return node.nextnodes[0]
        if node.operator == 'Land':
            return node.nextnodes[0]
        if node.operator == 'Lor':
            return node.nextnodes[0]
        if node.operator == 'LessThan':
            return DFEvalValue(0, 1)  # value, width
        if node.operator == 'GreaterThan':
            return DFEvalValue(0, 1)
        if node.operator == 'LessEq':
            return DFEvalValue(1, 1)
        if node.operator == 'GreaterEq':
            return DFEvalValue(1, 1)
        if node.operator == 'Eq':
            return DFEvalValue(1, 1)
        if node.operator == 'NotEq':
            return DFEvalValue(0, 1)
        if node.operator == 'Eql':
            return DFEvalValue(1, 1)
        if node.operator == 'NotEql':
            return DFEvalValue(0, 1)
        return node

    def mergeStaticNodes(self, node):
        if not isinstance(node, DFOperator):
            return node
        if len(node.nextnodes) == 1:
            return node

        left = node.nextnodes[0]
        right = node.nextnodes[1]

        if node.operator == 'And':
            if isinstance(left, DFEvalValue) and left.value == 0:
                return DFEvalValue(0, self.getWidth(node))
            if isinstance(right, DFEvalValue) and right.value == 0:
                return DFEvalValue(0, self.getWidth(node))
            if isinstance(left, DFOperator) and left.operator == 'Unot'\
                    and left.nextnodes[0] == right:
                return DFEvalValue(0, self.getWidth(node))
            if isinstance(right, DFOperator) and right.operator == 'Unot'\
                    and right.nextnodes[0] == left:
                return DFEvalValue(0, self.getWidth(node))
            if isinstance(left, DFOperator) and left.operator == 'Ulnot'\
                    and left.nextnodes[0] == right:
                if self.getWidth(node) == 1:
                    return DFEvalValue(0, 1)
                else:
                    return node
            if isinstance(right, DFOperator) and right.operator == 'Ulnot'\
                    and right.nextnodes[0] == left:
                if self.getWidth(node) == 1:
                    return DFEvalValue(0, 1)
                else:
                    return node
            return node
        if node.operator == 'Or':
            if isinstance(left, DFEvalValue) and left.value == 0:
                return right
            if isinstance(right, DFEvalValue) and right.value == 0:
                return left
            if isinstance(left, DFOperator) and left.operator == 'Unot'\
                    and left.nextnodes[0] == right:
                return DFEvalValue(self._evalOperator('Unot', [0, ], self.getWidth(node)), self.getWidth(node))
            if isinstance(right, DFOperator) and right.operator == 'Unot'\
                    and right.nextnodes[0] == left:
                return DFEvalValue(self._evalOperator('Unot', [0, ], self.getWidth(node)), self.getWidth(node))
            if isinstance(left, DFOperator) and left.operator == 'Ulnot'\
                    and left.nextnodes[0] == right:
                if self.getWidth(node) == 1:
                    return DFEvalValue(1, 1)
                else:
                    return node
            if isinstance(right, DFOperator) and right.operator == 'Ulnot'\
                    and right.nextnodes[0] == left:
                if self.getWidth(node) == 1:
                    return DFEvalValue(1, 1)
                else:
                    return node
            return node
        if node.operator == 'Land':
            if isinstance(left, DFEvalValue) and left.value == 0:
                return DFEvalValue(0, 1)
            if isinstance(right, DFEvalValue) and right.value == 0:
                return DFEvalValue(0, 1)
            if isinstance(left, DFEvalValue) and left.value > 0:
                return right
            if isinstance(right, DFEvalValue) and right.value > 0:
                return left
            if isinstance(left, DFOperator) and left.operator == 'Unot'\
                    and left.nextnodes[0] == right:
                if self.getWidth(node) == 1:
                    return DFEvalValue(0, 1)
                else:
                    return node
            if isinstance(right, DFOperator) and right.operator == 'Unot'\
                    and right.nextnodes[0] == left:
                if self.getWidth(node) == 1:
                    return DFEvalValue(0, 1)
                else:
                    return node
            if isinstance(left, DFOperator) and left.operator == 'Ulnot'\
                    and left.nextnodes[0] == right:
                return DFEvalValue(0, 1)
            if isinstance(right, DFOperator) and right.operator == 'Ulnot'\
                    and right.nextnodes[0] == left:
                return DFEvalValue(0, 1)
            if isinstance(left, DFOperator) and left.operator == 'Eq'\
                    and isinstance(right, DFOperator) and right.operator == 'Eq'\
                    and left.nextnodes[0] == right.nextnodes[0]\
                    and isinstance(left.nextnodes[1], DFEvalValue)\
                    and isinstance(right.nextnodes[1], DFEvalValue)\
                    and left.nextnodes[1].value != right.nextnodes[1].value:
                return DFEvalValue(0, 1)
            if isinstance(left, DFOperator) and left.operator == 'Eq'\
                    and isinstance(right, DFOperator) and right.operator == 'Eq'\
                    and left.nextnodes[1] == right.nextnodes[1]\
                    and isinstance(left.nextnodes[0], DFEvalValue)\
                    and isinstance(right.nextnodes[0], DFEvalValue)\
                    and left.nextnodes[0].value != right.nextnodes[0].value:
                return DFEvalValue(0, 1)
            if isinstance(left, DFOperator) and left.operator == 'Eq'\
                    and isinstance(right, DFOperator) and right.operator == 'Eq'\
                    and left.nextnodes[0] == right.nextnodes[1]\
                    and isinstance(left.nextnodes[1], DFEvalValue)\
                    and isinstance(right.nextnodes[0], DFEvalValue)\
                    and left.nextnodes[1].value != right.nextnodes[0].value:
                return DFEvalValue(0, 1)
            if isinstance(left, DFOperator) and left.operator == 'Eq'\
                    and isinstance(right, DFOperator) and right.operator == 'Eq'\
                    and left.nextnodes[1] == right.nextnodes[0]\
                    and isinstance(left.nextnodes[0], DFEvalValue)\
                    and isinstance(right.nextnodes[1], DFEvalValue)\
                    and left.nextnodes[0].value != right.nextnodes[1].value:
                return DFEvalValue(0, 1)
            if isinstance(left, DFOperator) and left.operator == 'Ulnot'\
                    and isinstance(left.nextnodes[0], DFOperator) and left.nextnodes[0].operator == 'Eq'\
                    and isinstance(right, DFOperator) and right.operator == 'Eq'\
                    and left.nextnodes[0].nextnodes[0] == right.nextnodes[0]\
                    and isinstance(left.nextnodes[0].nextnodes[1], DFEvalValue)\
                    and isinstance(right.nextnodes[1], DFEvalValue)\
                    and left.nextnodes[0].nextnodes[1].value != right.nextnodes[1].value:
                return right
            if isinstance(left, DFOperator) and left.operator == 'Ulnot'\
                    and isinstance(left.nextnodes[0], DFOperator) and left.nextnodes[0].operator == 'Eq'\
                    and isinstance(right, DFOperator) and right.operator == 'Eq'\
                    and left.nextnodes[0].nextnodes[1] == right.nextnodes[0]\
                    and isinstance(left.nextnodes[0].nextnodes[0], DFEvalValue)\
                    and isinstance(right.nextnodes[1], DFEvalValue)\
                    and left.nextnodes[0].nextnodes[0].value != right.nextnodes[1].value:
                return right
            if isinstance(right, DFOperator) and right.operator == 'Ulnot'\
                    and isinstance(right.nextnodes[0], DFOperator) and right.nextnodes[0].operator == 'Eq'\
                    and isinstance(left, DFOperator) and left.operator == 'Eq'\
                    and right.nextnodes[0].nextnodes[0] == left.nextnodes[0]\
                    and isinstance(right.nextnodes[0].nextnodes[1], DFEvalValue)\
                    and isinstance(left.nextnodes[1], DFEvalValue)\
                    and right.nextnodes[0].nextnodes[1].value != left.nextnodes[1].value:
                return left
            if isinstance(right, DFOperator) and right.operator == 'Ulnot'\
                    and isinstance(right.nextnodes[0], DFOperator) and right.nextnodes[0].operator == 'Eq'\
                    and isinstance(left, DFOperator) and left.operator == 'Eq'\
                    and right.nextnodes[0].nextnodes[1] == left.nextnodes[0]\
                    and isinstance(right.nextnodes[0].nextnodes[0], DFEvalValue)\
                    and isinstance(left.nextnodes[1], DFEvalValue)\
                    and right.nextnodes[0].nextnodes[0].value != left.nextnodes[1].value:
                return left
            return node
        if node.operator == 'Lor':
            if isinstance(left, DFEvalValue) and left.value == 0:
                return right
            if isinstance(right, DFEvalValue) and right.value == 0:
                return left
            if isinstance(left, DFEvalValue) and left.value > 0:
                return DFEvalValue(1, 1)
            if isinstance(right, DFEvalValue) and right.value > 0:
                return DFEvalValue(1, 1)
            if isinstance(left, DFOperator) and left.operator == 'Unot'\
                    and left.nextnodes[0] == right:
                return DFEvalValue(1, 1)
            if isinstance(right, DFOperator) and right.operator == 'Unot'\
                    and right.nextnodes[0] == left:
                return DFEvalValue(1, 1)
            if isinstance(left, DFOperator) and left.operator == 'Ulnot'\
                    and left.nextnodes[0] == right:
                return DFEvalValue(1, 1)
            if isinstance(right, DFOperator) and right.operator == 'Ulnot'\
                    and right.nextnodes[0] == left:
                return DFEvalValue(1, 1)
            if isinstance(left, DFOperator) and left.operator == 'Land'\
                    and isinstance(right, DFOperator) and right.operator == 'Land'\
                    and isinstance(left.nextnodes[0], DFOperator) and left.nextnodes[0].operator == 'Ulnot'\
                    and left.nextnodes[0].nextnodes[0] == right.nextnodes[0]\
                    and left.nextnodes[1] == right.nextnodes[1]:
                return left.nextnodes[1]
            if isinstance(left, DFOperator) and left.operator == 'Land'\
                    and isinstance(right, DFOperator) and right.operator == 'Land'\
                    and isinstance(left.nextnodes[1], DFOperator) and left.nextnodes[1].operator == 'Ulnot'\
                    and left.nextnodes[1].nextnodes[0] == right.nextnodes[0]\
                    and left.nextnodes[0] == right.nextnodes[1]:
                return left.nextnodes[0]
            if isinstance(right, DFOperator) and right.operator == 'Land'\
                    and isinstance(left, DFOperator) and left.operator == 'Land'\
                    and isinstance(right.nextnodes[0], DFOperator) and right.nextnodes[0].operator == 'Ulnot'\
                    and right.nextnodes[0].nextnodes[0] == left.nextnodes[0]\
                    and right.nextnodes[1] == left.nextnodes[1]:
                return right.nextnodes[1]
            if isinstance(right, DFOperator) and right.operator == 'Land'\
                    and isinstance(left, DFOperator) and left.operator == 'Land'\
                    and isinstance(right.nextnodes[1], DFOperator) and right.nextnodes[1].operator == 'Ulnot'\
                    and right.nextnodes[1].nextnodes[0] == left.nextnodes[0]\
                    and right.nextnodes[0] == left.nextnodes[1]:
                return right.nextnodes[0]
            return node
        return node

    def mergeLandLor(self, node):
        return self.mergeLor(node)

    def mergeLand(self, node):
        ret = self._mergeLand(node)
        if isinstance(ret, tuple):
            retnode = None
            for r in ret:
                if retnode is None:
                    retnode = r
                else:
                    retnode = DFOperator((retnode, r), 'Land')
            return retnode
        return ret

    def _mergeLand(self, node):
        if not isinstance(node, DFOperator):
            return node
        if node.operator != 'Land':
            return node
        left = self._mergeLand(node.nextnodes[0])
        right = self._mergeLand(node.nextnodes[1])
        landlist = []
        if isinstance(left, tuple):
            landlist.extend(left)
        else:
            landlist.append(left)
        if isinstance(right, tuple):
            landlist.extend(right)
        else:
            landlist.append(right)
        ret_list = []
        ret_exist_list = []
        for l in landlist:
            s = l
            not_s = l.nextnodes[0] if isinstance(
                l, DFOperator) and l.operator == 'Ulnot' else DFOperator((l,), 'Ulnot')
            if not_s in ret_exist_list:
                return (DFEvalValue(0, 1),)
            if not (s in ret_exist_list):
                ret_list.append(l)
                ret_exist_list.append(s)
        return tuple(sorted(ret_list, key=lambda x: x.tocode(), reverse=True))

    def mergeLor(self, node):
        ret = self._mergeLor(node)
        if isinstance(ret, tuple):
            retnode = None
            for r in ret:
                if retnode is None:
                    retnode = r
                else:
                    retnode = DFOperator((retnode, r), 'Lor')
            return retnode
        return ret

    def _mergeLor(self, node):
        if not isinstance(node, DFOperator):
            return node
        if node.operator == 'Land':
            return self.mergeLand(node)
        if node.operator != 'Lor':
            return node
        left = self._mergeLor(node.nextnodes[0])
        right = self._mergeLor(node.nextnodes[1])
        landlist = []
        if isinstance(left, tuple):
            landlist.extend(left)
        else:
            landlist.append(left)
        if isinstance(right, tuple):
            landlist.extend(right)
        else:
            landlist.append(right)
        ret_list = []
        ret_exist_list = []
        for l in landlist:
            s = l
            not_s = l.nextnodes[0] if isinstance(
                l, DFOperator) and l.operator == 'Ulnot' else DFOperator((l,), 'Ulnot')
            if not_s in ret_exist_list:
                return (DFEvalValue(1, 1),)
            if not (s in ret_exist_list):
                ret_list.append(l)
                ret_exist_list.append(s)
        return tuple(sorted(ret_list, key=lambda x: x.tocode(), reverse=True))

# -------------------------------------------------------------------------------


class VerilogDataflowOptimizer(VerilogOptimizer):
    def __init__(self, terms, binddict):
        VerilogOptimizer.__init__(self, terms, {})
        self.binddict = binddict
        self.resolved_terms = {}
        self.resolved_binddict = {}

    def getResolvedTerms(self):
        return self.resolved_terms

    def getResolvedBinddict(self):
        return self.resolved_binddict

    def getConstlist(self):
        return self.constlist

    def getTerm(self, name):
        return self.terms[name]

    def resolveConstant(self):
        # 2-pass
        for bk, bv in sorted(self.binddict.items(), key=lambda x: len(x[0])):
            termtype = self.getTerm(bk).termtype
            if signaltype.isParameter(termtype) or signaltype.isLocalparam(termtype):
                rslt = self.optimizeConstant(bv[0].tree)
                if isinstance(rslt, DFEvalValue):
                    self.constlist[bk] = rslt

        for bk, bv in sorted(self.binddict.items(), key=lambda x: len(x[0])):
            termtype = self.getTerm(bk).termtype
            if signaltype.isParameter(termtype) or signaltype.isLocalparam(termtype):
                rslt = self.optimizeConstant(bv[0].tree)
                if isinstance(rslt, DFEvalValue):
                    self.constlist[bk] = rslt

        self.resolved_binddict = copy.deepcopy(self.binddict)
        for bk, bv in sorted(self.binddict.items(), key=lambda x: len(x[0])):
            new_bindlist = []
            for bind in bv:
                new_bind = copy.deepcopy(bind)
                if bk in self.constlist:
                    new_bind.tree = self.constlist[bk]
                new_bindlist.append(new_bind)
            self.resolved_binddict[bk] = new_bindlist

        self.resolved_terms = copy.deepcopy(self.terms)
        for tk, tv in sorted(self.resolved_terms.items(), key=lambda x: len(x[0])):
            if tv.msb is not None:
                rslt = self.optimizeConstant(tv.msb)
                self.resolved_terms[tk].msb = rslt
            if tv.lsb is not None:
                rslt = self.optimizeConstant(tv.lsb)
                self.resolved_terms[tk].lsb = rslt
            if tv.dims is not None:
                dims = []
                for l, r in tv.dims:
                    l = self.optimizeConstant(l)
                    r = self.optimizeConstant(r)
                    dims.append((l, r))
                self.resolved_terms[tk].dims = tuple(dims)
