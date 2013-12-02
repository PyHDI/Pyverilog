PYTHON=python3.3
#OPT=-m pdb

OPTIMIZER=optimizer.py
SRCS=../test/statemachine.v

.PHONY: optimize
optimize:
	$(PYTHON) $(OPT) $(OPTIMIZER) $(SRCS)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out
