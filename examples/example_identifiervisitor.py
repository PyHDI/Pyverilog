from __future__ import absolute_import
from __future__ import print_function
import sys
import os

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyverilog.vparser.ast as vast
from pyverilog.utils.identifiervisitor import getIdentifiers


def main():
    a = vast.Identifier('a')
    b = vast.Identifier('b')
    c = vast.Plus(a, b)

    ids = getIdentifiers(c)
    print(ids)


if __name__ == '__main__':
    main()
