from setuptools import setup, find_packages

import pyverilog.utils.version
import re
import os

m = re.search(r'(\d+\.\d+\.\d+(-.+)?)', pyverilog.utils.version.VERSION)
version = m.group(1) if m is not None else '0.0.0'


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename), encoding='utf8').read()


setup(name='pyverilog',
      version=version,
      description='Python-based Hardware Design Processing Toolkit for Verilog HDL: Parser, Dataflow Analyzer, Controlflow Analyzer and Code Generator',
      long_description=read('README.rst'),
      keywords='Verilog HDL, Lexer, Parser, Dataflow Analyzer, Control-flow Analyzer, Code Generator, Visualizer',
      author='Shinya Takamaeda-Yamazaki',
      license="Apache License 2.0",
      url='https://github.com/PyHDI/Pyverilog',
      packages=find_packages(),
      package_data={'pyverilog.ast_code_generator': ['template/*'], },
      install_requires=['Jinja2>=2.10'],
      extras_require={
          'graph': ['pygraphviz>=1.3.1'],
          'test': ['pytest>=3.2', 'pytest-pythonpath>=0.7'],
      },
      )
