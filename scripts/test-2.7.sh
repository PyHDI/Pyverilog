#!/bin/sh
set -e

mkdir 2.7
cd 2.7
virtualenv --python=python .
source bin/activate
git clone https://github.com/PyHDI/Pyverilog.git
cd Pyverilog
python setup.py install
pip install pytest pytest-pythonpath
mv pyverilog pyverilog.old
make -C examples PYTHON=python
make clean -C examples
make test -C tests PYTHON=python
mv pyverilog.old pyverilog
cd ..
deactivate
cd ..
