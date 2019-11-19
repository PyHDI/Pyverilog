"""
   Copyright 2013, Shinya Takamaeda-Yamazaki and Contributors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

   ----
   Verilog Preprocessor
 
   Icarus Verilog is used as the internal preprocessor.
   Please install Icarus Verilog on your environment.
"""

from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import subprocess


class VerilogPreprocessor(object):
    def __init__(self, filelist, outputfile='pp.out', include=None, define=None):

        if not isinstance(filelist, (tuple, list)):
            filelist = list(filelist)

        self.filelist = filelist

        iverilog = os.environ.get('PYVERILOG_IVERILOG')
        if iverilog is None:
            iverilog = 'iverilog'

        if include is None:
            include = ()

        if define is None:
            define = ()

        self.iv = [iverilog]

        for inc in include:
            self.iv.append('-I')
            self.iv.append(inc)

        for dfn in define:
            self.iv.append('-D')
            self.iv.append(dfn)

        self.iv.append('-E')
        self.iv.append('-o')
        self.iv.append(outputfile)

    def preprocess(self):
        cmd = self.iv + list(self.filelist)
        subprocess.call(cmd)


def preprocess(
    filelist,
    output='preprocess.output',
    include=None,
    define=None
):
    pre = VerilogPreprocessor(filelist, output, include, define)
    pre.preprocess()
    text = open(output).read()
    os.remove(output)
    return text
