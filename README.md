Pyverilog
==============================
Python-based Tool-chain for design analysis and code generation of Verilog HDL

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

Pyverilog is open-source design analyzer/generator of Verilog HDL. All source codes are written in Python.

Pyverilog includes various independent software tools for Verilog HDL.
You can create your own design analyzer, code translator and code generator for Verilog HDL based on this tool-chain.


Software Requirements
------------------------------

* Python (2.7 and 3.3 or later)
   - 'controlflow' and 'graph' use Python 2.7 to generate a graph image using python-graphviz
* Jinja2 (2.7 or later)
   - pip3 install jinja2
* Icarus Verilog (0.9.6 or later)
   - apt-get install iverilog


Getting Started
------------------------------

This software includes various tools for Verilog HDL design.

Most useful tools are

* vparser: Code parser to generate AST (Abstract Syntax Tree) from source codes of Verilog HDL.
* definition\_analyzer: Dataflow analyzer.
* optimizer: Definition optimizer to remove redundant expressions.
* ast\_to\_code: Code generator of Verilog HDL from AST

The other tools are useful for control-flow analysis and active value inference to generate some accelerated logics.

To use them, plase type just 'make' in each sub directory.

