PYTHON=python3
#PYTHON=python

.PHONY: all
all: clean

.PHONY: test
test:
	$(PYTHON) -m pytest -vv

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out .cache
