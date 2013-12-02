PYTHON=python3.3
#OPT=-m pdb

ACTIVE=active_condition.py
SRCS=../test/vectoradd.v
TOP=-t TOP
TARGETS=-s "TOP.MEM_RE"

.PHONY: active
active:
	$(PYTHON) $(OPT) $(ACTIVE) $(TOP) $(SRCS) $(TARGETS) 

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out
