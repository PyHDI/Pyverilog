from setuptools import setup, find_packages

setup(name='pyverilog',
      version='0.8.0',
      description='Verilog HDL Design Analysis Toolkit',
      author='Shinya Takamaeda-Yamazaki',
      url='http://shtaxxx.github.io/Pyverilog/',
      package_dir={ 'pyverilog': '' },
      packages=[ 'pyverilog',
                 'pyverilog.utils',
                 'pyverilog.vparser',
                 'pyverilog.vparser.ply',
                 'pyverilog.dataflow',
                 'pyverilog.controlflow',
                 'pyverilog.ast_code_generator',
                 'pyverilog.testcode', ],
      package_data={ 'pyverilog.ast_code_generator' : ['template/*'], 
                     'pyverilog.testcode' : ['*'], },
)

