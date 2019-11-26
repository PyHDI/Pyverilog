PYTHON=python3
#PYTHON=python

.PHONY: all
all: clean

.PHONY: test
test:
	$(PYTHON) -m pytest -vv tests

.PHONY: clean
clean:
	make clean -C ./pyverilog
	make clean -C ./examples
	make clean -C ./tests
	rm -rf *.egg-info build dist *.pyc __pycache__ parsetab.py .cache tmp.v uut.vcd *.out *.png *.dot 

#.PHONY: release
#release:
#	pandoc README.md -t rst > README.rst
