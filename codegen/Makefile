PYTHON=python3.3
#OPT=-m pdb

CODEGEN=codegen.py

SRCS=../test/generate.v
TOP=-t TOP
TARGETS=-s "TOP.OUT4"

DUMP=out.v
CODEGENOPT=-o $(DUMP)

.PHONY: codegen
codegen:
	$(PYTHON) $(OPT) $(CODEGEN) $(SRCS) $(TOP) $(TARGETS) $(CODEGENOPT)

.PHONY: open
open:
	cat $(DUMP)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out *.v
