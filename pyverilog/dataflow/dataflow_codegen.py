# -------------------------------------------------------------------------------
# codegen.py (Obsoleted)
#
# Code generator from dataflow
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import re

import pyverilog.utils.util as util
import pyverilog.utils.signaltype as signaltype
from pyverilog.dataflow.subset import VerilogSubset


class VerilogCodeGenerator(VerilogSubset):
    def __init__(self, topmodule, terms, binddict,
                 resolved_terms, resolved_binddict, constlist,
                 modulename='Subset', enable_name='HT_enable', num_indent=2, flat=True):
        VerilogSubset.__init__(self, topmodule, terms, binddict,
                               resolved_terms, resolved_binddict, constlist)
        self.modulename = modulename
        self.enable_name = enable_name
        self.num_indent = num_indent
        self.flat = flat

    def addBind(self, name, bind):
        if name in self.binddict:
            self.binddict[name] += (bind,)
        else:
            self.binddict[name] = (bind,)
        if name in self.resolved_binddict:
            self.resolved_binddict[name] += (bind,)
        else:
            self.resolved_binddict[name] = (bind,)

    def addTerm(self, name, term):
        self.terms[name] = term
        self.resolved_terms[name] = term

    def _input(self, name):
        return 'input ' + name + ';\n'

    def _output(self, name):
        return 'output ' + name + ';\n'

    def _inout(self, name):
        return 'inout ' + name + ';\n'

    def _wire(self, name):
        return 'wire ' + name + ';\n'

    def _modulehead(self, terms):
        modulehead = ''
        modulehead += '`default_nettype none\n'
        modulehead += 'module ' + self.modulename + '('
        modulehead += '\n' + (' ' * self.num_indent)
        modulehead += self.clock_name + ', '
        modulehead += self.reset_name + ', '
        modulehead += self.enable_name + ', '
        modulehead += '\n' + (' ' * self.num_indent)

        for tk, tv in terms.items():
            scope = util.getScope(tk)
            if util.isTopmodule(scope):
                termtype = self.getTermtype(tk)
                if signaltype.isInput(termtype) and tk == util.toTermname((self.topmodule, self.reset_name)):
                    continue
                if signaltype.isInput(termtype) and tk == util.toTermname((self.topmodule, self.clock_name)):
                    continue
                if signaltype.isInput(termtype):
                    modulehead += util.toFlatname(tk) + ', '
                elif signaltype.isInout(termtype):
                    modulehead += util.toFlatname(tk) + ', '
                elif signaltype.isOutput(termtype):
                    modulehead += util.toFlatname(tk) + ', '
        modulehead = modulehead[:-2] + ');\n\n'
        return modulehead

    def _system_io(self, clock_name, reset_name, enable_name):
        flat_clock_name = util.toFlatname(util.toTermname((self.topmodule, clock_name)))
        flat_reset_name = util.toFlatname(util.toTermname((self.topmodule, reset_name)))
        flat_enable_name = util.toFlatname(util.toTermname((self.topmodule, enable_name)))
        code = ''
        code += self._input(clock_name)
        code += self._input(reset_name)
        code += self._input(enable_name)
        code += self._wire(flat_clock_name)
        code += self._wire(flat_reset_name)
        code += self._assign(flat_clock_name, clock_name)
        code += self._assign(flat_reset_name, reset_name)
        code += '\n'
        return code

    def _assign(self, left, right, msb=None, lsb=None):
        code = 'assign ' + left
        if msb is not None and lsb is not None:
            code += '[' + msb.tocode(None) + ':' + lsb.tocode(None) + ']'
        elif msb is not None:
            code += '[' + msb.tocode(None) + ']'
        elif lsb is not None:
            code += '[' + lsb.tocode(None) + ']'
        code += ' = ' + right + ';\n'
        return code

    def generateCode(self, targets=()):
        if len(targets) > 0:
            return self.generateSubsetCode(targets)
        return self.generateEntireCode()

    def generateSubsetCode(self, targets):
        terms, parameter, assign, always_clockedge, always_combination = self.getSubset(targets)
        return self._toCode(terms, parameter, assign, always_clockedge, always_combination)

    def generateEntireCode(self):
        terms, parameter, assign, always_clockedge, always_combination = self.getEntire()
        return self._toCode(terms, parameter, assign, always_clockedge, always_combination)

    def _toCode(self, terms, parameter, assign, always_clockedge, always_combination):
        # module header
        modulehead = self._modulehead(terms)

        code = ''
        # clock, reset, control input definition
        code += self._system_io(self.clock_name, self.reset_name, self.enable_name)

        # general signal definition
        for tk, tv in terms.items():
            termtype = self.getTermtype(tk)
            if signaltype.isInput(termtype) and tk == util.toTermname((self.topmodule, self.reset_name)):
                continue
            if signaltype.isInput(termtype) and tk == util.toTermname((self.topmodule, self.clock_name)):
                continue
            code += tv.tocode()

        for pk, pv in parameter.items():
            code += pv.tocode()

        # assign
        for ak, avv in assign.items():
            cnt = 0
            for av in avv:
                code += av.tocode()

        # always (clock edge)
        for ck, cvv in always_clockedge.items():
            for cv in cvv:
                code += cv.tocode()

        # always (combination)
        for ck, cvv in always_combination.items():
            for cv in cvv:
                code += cv.tocode()

        # module tail
        moduletail = '\nendmodule\n'

        ret = modulehead + code + moduletail

        if self.flat:
            ret = re.sub('\.', '_', ret)

        return ret
