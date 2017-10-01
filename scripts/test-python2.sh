#!/bin/sh
set -e

mkdir python
cd python
virtualenv --python=python .
source bin/activate

git clone https://github.com/PyHDI/Pyverilog.git
cd Pyverilog
python setup.py install
pip install pytest pytest-pythonpath
mv pyverilog pyverilog.old

python -m pytest -vv .

mv pyverilog.old pyverilog
cd ..
deactivate
cd ..
