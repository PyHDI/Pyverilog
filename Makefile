.PHONY: all
all:
	make -C ./pyverilog

.PHONY: clean
clean:
	make clean -C ./pyverilog
	rm -rf *.pyc __pycache__ pyverilog.egg-info build dist

.PHONY: release
release:
#	pandoc README.md -t rst | awk 'BEGIN{ skip=0 }; { if(match($$0, /\.\. figure.*/)) { skip=3 } else if(skip==0) { print } else if(skip>0) { skip=skip-1 } };' > README.rst
	pandoc README.md -t rst > README.rst
