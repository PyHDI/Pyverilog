PYTHON=python3
#OPT=-m pdb

CODEGEN=codegen.py
SRCS=../testcode/test.v

.PHONY: codegen
codegen:
	$(PYTHON) $(OPT) $(CODEGEN) $(SRCS)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out
