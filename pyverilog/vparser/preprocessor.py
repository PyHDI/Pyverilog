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
        self.filelist = filelist
        cmd = []
        cmd.append('iverilog ')
        if include:
            for inc in include:
                cmd.append('-I ')
                cmd.append(inc)
                cmd.append(' ')
        if define:
            for d in define:
                cmd.append('-D')
                cmd.append(d)
                cmd.append(' ')
        cmd.append('-E -o ')
        cmd.append(outputfile)
        self.iv = ''.join(cmd)

    def preprocess(self):
        cmd = self.iv + ' '
        for f in self.filelist:
            cmd += ' ' + f
        subprocess.call(cmd, shell=True)


def preprocess(filelist,
               output='preprocess.output', include=None, define=None):
    pre = VerilogPreprocessor(filelist, output, include, define)
    pre.preprocess()
    text = open(output).read()
    os.remove(output)
    return text
