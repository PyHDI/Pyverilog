PYTHON=python3.3
#OPT=-m pdb

ASTTOCODE=ast_to_code.py
SRCS=../test/generate.v
TOP=-t TOP

.PHONY: analyze
analyze:
	$(PYTHON) $(OPT) $(ASTTOCODE) $(SRCS) $(TOP)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out
