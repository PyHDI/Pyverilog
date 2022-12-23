from __future__ import absolute_import
from __future__ import print_function

import os

with open(os.path.join(os.path.dirname(__file__), "VERSION")) as f:
    __version__ = f.read().splitlines()[0]
