TEST=*.py
ARGS=
if [ -z "${PYTHON}" ];then
        PYTHON=python3
fi
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
