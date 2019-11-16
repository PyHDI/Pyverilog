# -------------------------------------------------------------------------------
# identifierreplace.py
#
# Replaces identifier names based on a given dict
#
# Copyright (C) 2015, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
# -------------------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function
import sys
import os

import pyverilog.vparser.ast as vast
from pyverilog.vparser.ast import Node


def replaceIdentifiers(node, ids):
    v = IdentifierReplace(ids)
    return v.visit(node)


def ischild(node, attr):
    if not isinstance(node, Node):
        return False
    excludes = ('coord', 'attr_names',)
    if attr.startswith('__'):
        return False
    if attr in excludes:
        return False
    attr_names = getattr(node, 'attr_names')
    if attr in attr_names:
        return False
    attr_test = getattr(node, attr)
    if hasattr(attr_test, '__call__'):
        return False
    return True


def children_items(node):
    children = [attr for attr in dir(node) if ischild(node, attr)]
    ret = []
    for c in children:
        ret.append((c, getattr(node, c)))
    return ret


class IdentifierReplace(object):
    def __init__(self, ids):
        self.ids = ids

    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        ret = visitor(node)
        if ret is None:
            return node
        return ret

    def generic_visit(self, node):
        for name, child in children_items(node):
            ret = None
            if child is None:
                continue
            if (isinstance(child, list) or isinstance(child, tuple)):
                r = []
                for c in child:
                    r.append(self.visit(c))
                ret = tuple(r)
            else:
                ret = self.visit(child)
            setattr(node, name, ret)
        return node

    def visit_Identifier(self, node):
        if node.name in self.ids:
            return vast.Identifier(self.ids[node.name])
        return node
