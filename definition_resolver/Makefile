PYTHON=python3.3
#OPT=-m pdb

RESOLVER=definition_resolver.py
SRCS=../test/generate.v
TOP=-t TOP

.PHONY: resolve
resolve:
	$(PYTHON) $(OPT) $(RESOLVER) $(SRCS) $(TOP)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out
