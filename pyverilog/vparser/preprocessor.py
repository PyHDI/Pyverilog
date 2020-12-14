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
import tempfile
import subprocess


class VerilogPreprocessor(object):
    def __init__(self, filelist, outputfile='pp.out', include=None, define=None):

        if not isinstance(filelist, (tuple, list)):
            filelist = list(filelist)

        # Elements in `filelist` can either be raw Verilog files, or Verilog code
        # in python string. The following loop iterates through these `sources`,
        # and normalizes all of them into files.
        #
        # For Verilog code in python string, the contents of the string is stored
        # in a temporary file for further use with `iverilog`.
        self.temp_files_paths = []
        self.filelist = []

        for source in filelist:
            # If `source` is verilog code in python strings
            if not os.path.isfile(source):
                temp_fd, temp_path = tempfile.mkstemp(prefix="pyverilog_temp_", suffix=".v")
                with open(temp_fd, 'w') as f:
                    f.write(source)

                self.temp_files_paths.append(temp_path)

            else: # else if it is normal verilog file path
                self.filelist.append(source)

        self.filelist += self.temp_files_paths

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

        # Removing the temporary files that were created
        for temp_file_path in self.temp_files_paths:
            os.remove(temp_file_path)


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
