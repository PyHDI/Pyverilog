PYTHON=python3
#PYTHON=python
#OPT=-m pdb
#OPT=-m cProfile -s time
#OPT=-m cProfile -o profile.rslt

PREPROCESSOR=example_preprocessor.py
LEXER=example_lexer.py
PARSER=example_parser.py

DATAFLOW=example_dataflow_analyzer.py
OPTIMIZER=example_optimizer.py
MERGE=example_merge.py
WALKER=example_walker.py
SUBSET=example_subset.py
DFCODEGEN=example_dataflow_codegen.py
GRAPHGEN=example_graphgen.py

CONTROLFLOW=example_controlflow_analyzer.py
ACTIVE=example_active_analyzer.py
ACTIVERANGE=example_active_range.py

CODEGEN=example_codegen.py

SRCS=../verilogcode/vectoradd.v
TOP=-t TOP
TARGETS=-s "TOP.MEM_A"

CODEGEN_OUT=out.v
CODEGEN_OPT=-o $(CODEGEN_OUT)
GRAPHGEN_OUT=out.png
GRAPHGEN_OPT=--identical --walk --step=0 -o $(GRAPHGEN_OUT)

NOGRAPH=--nograph
NOLABEL=--nolabel
CONTROLFLOW_OPT=$(NOGRAPH) $(NOLABEL)

.PHONY: all
all: preprocess lex parse dataflow optimize merge walk subset dfcodegen \
controlflow active activerange codegen

.PHONY: preprocess
preprocess:
	$(PYTHON) $(OPT) $(PREPROCESSOR) $(SRCS)

.PHONY: lex
lex:
	$(PYTHON) $(OPT) $(LEXER) $(SRCS)

.PHONY: parse
parse:
	$(PYTHON) $(OPT) $(PARSER) $(SRCS)

.PHONY: dataflow
dataflow:
	$(PYTHON) $(OPT) $(DATAFLOW) $(SRCS) $(TOP)

.PHONY: optimize
optimize:
	$(PYTHON) $(OPT) $(OPTIMIZER) $(SRCS) $(TOP)

.PHONY: merge
merge:
	$(PYTHON) $(OPT) $(MERGE) $(SRCS) $(TOP) $(TARGETS)

.PHONY: walk
walk:
	$(PYTHON) $(OPT) $(WALKER) $(SRCS) $(TOP) $(TARGETS)

.PHONY: subset
subset:
	$(PYTHON) $(OPT) $(SUBSET) $(SRCS) $(TOP) $(TARGETS)

.PHONY: dfcodegen
dfcodegen:
		$(PYTHON) $(OPT) $(DFCODEGEN) $(SRCS) $(TOP) $(TARGETS) $(CODEGEN_OPT)

.PHONY: graphgen
graphgen:
		$(PYTHON) $(OPT) $(GRAPHGEN) $(SRCS) $(TOP) $(TARGETS) $(GRAPHGEN_OPT)

.PHONY: controlflow
controlflow:
	$(PYTHON) $(OPT) $(CONTROLFLOW) $(SRCS) $(TOP) $(TARGETS) $(CONTROLFLOW_OPT)

.PHONY: active
active:
	$(PYTHON) $(OPT) $(ACTIVE) $(TOP) $(SRCS) $(TARGETS) 

.PHONY: activerange
activerange:
	$(PYTHON) $(OPT) $(ACTIVERANGE) $(TOP) $(SRCS) $(TARGETS) 

.PHONY: codegen
codegen:
	$(PYTHON) $(OPT) $(CODEGEN) $(SRCS)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out *.png *.v *.dot
