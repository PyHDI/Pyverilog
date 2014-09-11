from setuptools import setup, find_packages

import pyverilog.utils.version
import re

m = re.search(r'(\d+\.\d+\.\d+)', pyverilog.utils.version.VERSION)
version = m.group(1) if m is not None else '0.0.0'

setup(name='pyverilog',
      version=version,
      description='Python-based Hardware Design Processing Toolkit for Verilog HDL',
      author='Shinya Takamaeda-Yamazaki',
      url='http://shtaxxx.github.io/Pyverilog/',
      packages=find_packages(),
      package_data={ 'pyverilog.ast_code_generator' : ['template/*'], 
                     'pyverilog' : ['testcode/*'], },
)

