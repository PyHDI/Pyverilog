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
cd examples
make PYTHON=python
make clean
cd ..
cd tests
make test PYTHON=python
cd ..
mv pyverilog.old pyverilog
cd ..
deactivate
cd ..
