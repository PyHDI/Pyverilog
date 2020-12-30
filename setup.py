from setuptools import setup, find_packages

import os


def read(filename):
    # return open(os.path.join(os.path.dirname(__file__), filename), encoding='utf8').read()
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(name='pyverilog',
      version=read('pyverilog/VERSION').splitlines()[0],
      description='Python-based Hardware Design Processing Toolkit for Verilog HDL: Parser, Dataflow Analyzer, Controlflow Analyzer and Code Generator',
      long_description=read('README.md'),
      long_description_content_type="text/markdown",
      keywords='Verilog HDL, Lexer, Parser, Dataflow Analyzer, Control-flow Analyzer, Code Generator, Visualizer',
      author='Shinya Takamaeda-Yamazaki',
      license="Apache License 2.0",
      url='https://github.com/PyHDI/Pyverilog',
      packages=find_packages(),
      package_data={'pyverilog': ['VERSION'],
                    'pyverilog.ast_code_generator': ['template/*'], },
      install_requires=['Jinja2>=2.10', 'ply>=3.4'],
      extras_require={
          'test': ['pytest>=3.8.1', 'pytest-pythonpath>=0.7.3'],
          'graph': ['pygraphviz>=1.3.1'],
      },
      )
