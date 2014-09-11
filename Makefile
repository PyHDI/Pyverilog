.PHONY: all
all:
	make -C ./pyverilog

.PHONY: clean
clean:
	make clean -C ./pyverilog
	rm -rf *.pyc __pycache__ pyverilog.egg-info build dist
