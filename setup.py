from setuptools import setup, find_packages

import pyverilog.utils.version
import re

m = re.search(r'(\d+\.\d+\.\d+)', pyverilog.utils.version.VERSION)
version = m.group(1) if m is not None else '0.0.0'

setup(name='pyverilog',
      version=version,
      description='Python-based Hardware Design Processing Toolkit for Verilog HDL',
      long_description=read('README.md'),
      keywords = 'Verilog HDL, Lexer, Parser, Dataflow Analyzer, Control-flow Analyzer, Code Generator, Visualizer',
      author='Shinya Takamaeda-Yamazaki',
      license="Apache License 2.0",
      url='http://shtaxxx.github.io/Pyverilog/',
      packages=find_packages(),
      package_data={ 'pyverilog.ast_code_generator' : ['template/*'], 
                     'pyverilog' : ['testcode/*'], },
)

