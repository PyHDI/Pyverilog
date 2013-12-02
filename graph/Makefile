#PYTHON=python3.3
PYTHON=python2.7
#OPT=-m pdb

GRAPH=graph.py
SRCS=../test/generate.v
TOP=-t TOP
TARGETS=-s "TOP.OUT4"

IDENTICAL=--identical
WALK=--walk
STEP=--step=0
#REORDER=--reorder
#DELAY=--delay
DUMP=out.png

GRAPHOPT=$(IDENTICAL) $(WALK) $(STEP) $(REORDER) $(DELAY) -o $(DUMP)

.PHONY: graph
graph:
	$(PYTHON) $(OPT) $(GRAPH) $(SRCS) $(TARGETS) $(TOP) $(GRAPHOPT)

.PHONY: open
open:
	open $(DUMP)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out *.png *.dot
