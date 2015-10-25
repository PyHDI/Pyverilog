PYTHON=python3
#PYTHON=python2.7
PYTHON27=python2.7
#OPT=-m pdb
#OPT=-m cProfile -s time
#OPT=-m cProfile -o profile.rslt

ANALYZER=dataflow_analyzer.py
MERGE=merge.py
WALKER=walker.py
SUBSET=subset.py
CODEGEN=codegen.py
GRAPHGEN=graphgen.py

SRCS=../../testcode/vectoradd.v
TOP=-t TOP
TARGETS=-s "TOP.MEM_A"

CODEGEN_OUT=out.v
CODEGEN_OPT=-o $(CODEGEN_OUT)
GRAPHGEN_OUT=out.png
GRAPHGEN_OPT=--identical --walk --step=0 -o $(GRAPHGEN_OUT)

.PHONY: all
all: analyze merge walk subset codegen graphgen

.PHONY: analyze
analyze:
	$(PYTHON) $(OPT) $(ANALYZER) $(SRCS) $(TOP)

.PHONY: merge
merge:
	$(PYTHON) $(OPT) $(MERGE) $(SRCS) $(TOP) $(TARGETS)

.PHONY: walk
walk:
	$(PYTHON) $(OPT) $(WALKER) $(SRCS) $(TOP) $(TARGETS)

.PHONY: subset
subset:
	$(PYTHON) $(OPT) $(SUBSET) $(SRCS) $(TOP) $(TARGETS)

.PHONY: codegen
codegen:
		$(PYTHON) $(OPT) $(CODEGEN) $(SRCS) $(TOP) $(TARGETS) $(CODEGEN_OPT)

.PHONY: graphgen
graphgen:
		$(PYTHON27) $(OPT) $(GRAPHGEN) $(SRCS) $(TOP) $(TARGETS) $(GRAPHGEN_OPT)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out *.png *.v *.dot
