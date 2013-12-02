PYTHON=python3.3
#OPT=-m pdb

WALKER=tree_walker.py
SRCS=../test/generate.v
TOP=-t TOP
TARGETS=-s "TOP.OUT4"

.PHONY: walk
walk:
	$(PYTHON) $(OPT) $(WALKER) $(SRCS) $(TOP) $(TARGETS)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out
