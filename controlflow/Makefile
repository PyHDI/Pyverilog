#PYTHON=python3.3
PYTHON=python2.7
#OPT=-m pdb

CONTROLFLOW=controlflow.py
SRCS=../test/vectoradd.v
TOP=-t TOP
TARGETS=-s "TOP.MEM_A"

#NOGRPAH=--nograph
NOLABEL=--nolabel
CONTROLFLOWOPT=$(NOGRAPH) $(NOLABEL)

.PHONY: controlflow
controlflow:
	$(PYTHON) $(OPT) $(CONTROLFLOW) $(SRCS) $(TOP) $(TARGETS) $(CONTROLFLOWOPT)

.PHONY: open
open:
	open *.png

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out *.png *.dot
