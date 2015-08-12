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

import sys
import os
import subprocess
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

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

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    import pyverilog.utils.version
    from optparse import OptionParser

    INFO = "Verilog Preprocessor"
    VERSION = pyverilog.utils.version.VERSION
    USAGE = "Usage: python preprocessor.py file ..."

    def showVersion():
        print(INFO)
        print(VERSION)
        print(USAGE)
        sys.exit()

    optparser = OptionParser()
    optparser.add_option("-v","--version",action="store_true",dest="showversion",
                         default=False,help="Show the version")
    optparser.add_option("-I","--include",dest="include",action="append",
                         default=[],help="Include path")
    optparser.add_option("-D",dest="define",action="append",
                         default=[],help="Macro Definition")
    (options, args) = optparser.parse_args()

    filelist = args
    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f): raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()
        
    text = preprocess(filelist, include=options.include, define=options.define)
    
    print(text)
