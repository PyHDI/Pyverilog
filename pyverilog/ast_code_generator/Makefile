PYTHON=python3
#PYTHON=python
#OPT=-m pdb
#OPT=-m cProfile -s time
#OPT=-m cProfile -o profile.rslt

CODEGEN=codegen.py
SRCS=../../verilogcode/led.v

.PHONY: codegen
codegen:
	$(PYTHON) $(OPT) $(CODEGEN) $(SRCS)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out
