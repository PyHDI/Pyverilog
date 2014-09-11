PYTHON = python3
#OPT=-m pdb

PREPROCESS=preprocessor.py
LEXER=lexer.py
PARSER=parser.py

SRCS=../testcode/test.v
#SRCS=../testcode/generate.v

.PHONY: parse
parse:
	$(PYTHON) $(OPT) $(PARSER) $(SRCS)

.PHONY: lexer_test
lexer_test:
	$(PYTHON) $(OPT) $(LEXER)

.PHONY: preprocess_test
preprocess_test:
	$(PYTHON) $(OPT) $(PREPROCESS)

.PHONY: clean
clean:
	rm -rf *.pyc __pycache__ parsetab.py *.out ply/__pycache__ ply/*.pyc 
