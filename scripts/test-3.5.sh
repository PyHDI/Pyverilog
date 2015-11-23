#!/bin/sh
set -e

mkdir 3.5
cd 3.5
virtualenv --python=python3 .
source bin/activate
git clone https://github.com/PyHDI/Pyverilog.git
cd Pyverilog
python3 setup.py install
pip install pytest pytest-pythonpath
mv pyverilog pyverilog.old
make -C examples
make clean -C examples
make test -C tests
mv pyverilog.old pyverilog
cd ..
deactivate
cd ..
