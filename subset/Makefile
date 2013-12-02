PYTHON=python3.3
#OPT=-m pdb

SUBSET=subset.py

SRCS=../test/generate.v
TOP=-t TOP
TARGETS=-s "TOP.OUT4"

.PHONY: subset
subset:
	$(PYTHON) $(OPT) $(SUBSET) $(SRCS) $(TOP) $(TARGETS)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out *.v
