# -------------------------------------------------------------------------------
# util.py
#
# utility functions for Pyverilog
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import copy

from pyverilog.utils.scope import ScopeLabel, ScopeChain


def toTermname(name):
    if isinstance(name, str):
        return toTermname_str(name)
    if isinstance(name, list):
        return toTermname_list(name)
    if isinstance(name, tuple):
        return toTermname_list(name)
    raise TypeError()


def toTermname_str(name):
    scopechain_list = []
    for n in name.split('.'):
        # fix me: to support "module.scope.signal[ptr]", lexical analyzer is required.
        scopechain_list.append(ScopeLabel(n, 'any'))
    return ScopeChain(scopechain_list)


def toTermname_list(name):
    scopechain_list = []
    for n in name:
        if not isinstance(n, str):
            raise TypeError()
        scopechain_list.append(ScopeLabel(n, 'any'))
    return ScopeChain(scopechain_list)


def getScope(termname):
    return termname[:-1]


def toFlatname(termname):
    #flatname = ''
    # for t in termname:
    #    flatname += str(t.scopename) + '__'
    # return flatname[:-2]
    return termname.tocode()


def splitScopeName(termname):
    scope = termname[:-1]
    scope_str = ''
    for s in scope:
        scope_str += s.scopename + '.'
    scope_str = scope_str[:-1]
    signame_str = termname[-1]
    return scope_str, signame_str


def isTopmodule(scope):
    if len(scope) == 1:
        return True
    return False


def dictlistmerge(a, b):
    ret = {}
    ret.update(a)
    for bk, bv in b.items():
        if bk in ret:
            for bvv in bv:
                if bvv not in ret[bk]:
                    ret[bk].append(bvv)
        else:
            ret[bk] = bv
    return ret


def maxValue(width):
    return 2 ** width - 1
