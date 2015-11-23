#!/bin/sh
set -e

mkdir 3.4
cd 3.4
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
