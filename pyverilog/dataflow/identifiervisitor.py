#-------------------------------------------------------------------------------
# identifiervisitor.py
# 
# Identifier list generator in a nested operator 
#
# Copyright (C) 2015, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

if sys.version_info[0] >= 3:
    from pyverilog.dataflow.visit import NodeVisitor
else:
    from visit import NodeVisitor

def getIdentifiers(node):
    v = IdentifierVisitor()
    v.visit(node)
    ids = v.getIdentifiers()
    return ids
    
class IdentifierVisitor(NodeVisitor):
    def __init__(self):
        self.identifiers = []

    def getIdentifiers(self):
        return tuple(self.identifiers)

    def reset(self):
        self.identifiers = []
    
    def visit_Identifier(self, node):
        self.identifiers.append(node.name)

if __name__ == '__main__':
    import pyverilog.vparser.ast as vast

    a = vast.Identifier('a')
    b = vast.Identifier('b')
    c = vast.Plus(a, b)

    ids = getIdentifiers(c)
    print(ids)
