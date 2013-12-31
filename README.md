Pyverilog
==============================
Python-based Hardware Design Processing Toolkit for Verilog HDL

Copyright (C) 2013, Shinya Takamaeda-Yamazaki

E-mail: takamaeda\_at\_arch.cs.titech.ac.jp


License
------------------------------
Apache License 2.0
(http://www.apache.org/licenses/LICENSE-2.0)

This software package includes PLY-3.4 in "vparser/ply".
The license of PLY is BSD.


What's Pyverilog?
------------------------------

Pyverilog is open-source hardware design processing toolkit for Verilog HDL.
All source codes are written in Python.

Pyverilog includes (1) code parser, (2) dataflow analyzer, (3) control-flow analyzer and (4) code generator.
You can create your own design analyzer, code translator and code generator of Verilog HDL based on this toolkit.


Software Requirements
------------------------------

* Python (2.7 and 3.3 or later)
* Graphviz and Pygraphviz (Python3 does not support)
   - graphgen.py in controlflow and controlflow.py in controlflow (without --nograph option) use Pygraphviz with Python 2.7.
   - If you do not use graphgen.py and controlflow.py without --nograph option, Python 3 is OK.
* Jinja2 (2.7 or later)
   - pip3 install jinja2
* Icarus Verilog (0.9.6 or later)
   - apt-get install iverilog


Getting Started
------------------------------

This software includes various tools for Verilog HDL design.

* vparser: Code parser to generate AST (Abstract Syntax Tree) from source codes of Verilog HDL.
* dataflow: Dataflow analyzer with an optimizer to remove redundant expressions and some dataflow handling tools.
* controlflow: Control-flow analyzer with condition analyzer that identify when a signal is activated.
* ast\_code\_generator: Verilog HDL code generator from AST.

To use them, please type 'make' in each sub directory.

