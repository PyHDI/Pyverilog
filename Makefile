.PHONY: all
all:
	export PYTHON=python3
	export PYTHON27=python2.7
	make -C ./tests

.PHONY: clean
clean:
	make clean -C ./pyverilog
	rm -rf *.pyc __pycache__ *.out parsetab.py pyverilog.egg-info build dist

.PHONY: release
release:
	pandoc README.md -t rst > README.rst
