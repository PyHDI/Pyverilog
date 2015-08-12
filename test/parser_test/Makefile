TEST=test.py
ARGS=

PYTHON=python3
#PYTHON=python
#OPT=-m pdb
#OPT=-m cProfile -s time
#OPT=-m cProfile -o profile.rslt

.PHONY: all
all: test

.PHONY: test
test:
	$(PYTHON) -m pytest -vv $(TEST)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out
