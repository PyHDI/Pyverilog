#-------------------------------------------------------------------------------
# preprocessor.py
# 
# Verilog Preprocessor
# 
# Icarus Verilog is used as a preprocessor via command-line.
# Please install Icarus Verilog on your environment.
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------        
def preprocess(filelist,
               output='preprocess.output', include=None, define=None):
    pre = VerilogPreprocessor(filelist, output, include, define)
    pre.preprocess()
    text = open(output).read()
    os.remove(output)
    return text
