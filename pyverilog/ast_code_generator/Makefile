ifndef EXE_TRAVIS
	PYTHON=python3
else
	PYTHON=python
endif
#OPT=-m pdb
#OPT=-m cProfile -s time
#OPT=-m cProfile -o profile.rslt

CODEGEN=codegen.py
SRCS=../../testcode/led.v

.PHONY: codegen
codegen:
	$(PYTHON) $(OPT) $(CODEGEN) $(SRCS)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out
