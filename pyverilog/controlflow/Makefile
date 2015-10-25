ifndef EXE_TRAVIS
	PYTHON=python3
else
	PYTHON=python
endif

#OPT=-m pdb
#OPT=-m cProfile -s time
#OPT=-m cProfile -o profile.rslt

ANALYZER=controlflow_analyzer.py
ACTIVE=active_analyzer.py
ACTIVERANGE=active_range.py

SRCS=../../testcode/vectoradd.v
TOP=-t TOP
TARGETS=-s "TOP.MEM_A"

NOGRAPH=--nograph
NOLABEL=--nolabel
ANALYZER_OPT=$(NOGRAPH) $(NOLABEL)

.PHONY: all
all: analyze active activerange

.PHONY: analyze
analyze:
	$(PYTHON) $(OPT) $(ANALYZER) $(SRCS) $(TOP) $(TARGETS) $(ANALYZER_OPT)

.PHONY: active
active:
	$(PYTHON) $(OPT) $(ACTIVE) $(TOP) $(SRCS) $(TARGETS) 

.PHONY: activerange
activerange:
	$(PYTHON) $(OPT) $(ACTIVERANGE) $(TOP) $(SRCS) $(TARGETS) 

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out *.png *.dot
