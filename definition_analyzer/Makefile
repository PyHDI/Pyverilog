PYTHON=python3.3
#OPT=-m pdb

ANALYZER=definition_analyzer.py
SRCS=../test/generate.v
TOP=-t TOP

.PHONY: analyze
analyze:
	$(PYTHON) $(OPT) $(ANALYZER) $(SRCS) $(TOP)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out
