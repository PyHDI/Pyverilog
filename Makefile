.PHONY: all
all:
	make -C ./pyverilog

.PHONY: clean
clean:
	make clean -C ./pyverilog
	make clean -C ./tests
	rm -rf *.pyc __pycache__ *.out parsetab.py pyverilog.egg-info build dist

.PHONY: release
release:
	pandoc README.md -t rst > README.rst
