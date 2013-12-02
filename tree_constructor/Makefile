PYTHON=python3.3
#OPT=-m pdb

CONSTRUCTOR=tree_constructor.py
SRCS=../test/generate.v
TOP=-t TOP
TARGETS=-s "TOP.OUT4"

.PHONY: construct
construct:
	$(PYTHON) $(OPT) $(CONSTRUCTOR) $(SRCS) $(TOP) $(TARGETS)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out
