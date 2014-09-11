#-------------------------------------------------------------------------------
# preprocessor.py
# 
# Preprocessor
#
# Current version calls Icarus Verilog as preprocessor.
# Please install Icarus Verilog on your environment.
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------

import sys
import os
import subprocess
import re

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

if __name__ == '__main__':
    filelist = ('../testcode/test.v',)
    pp_outputfile = 'pp.out'
    vp = VerilogPreprocessor(filelist, pp_outputfile, include=('./'))
    vp.preprocess()
    rslt = open(pp_outputfile, 'r').read()
    print(rslt)
