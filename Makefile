.PHONY: all
all:
	make -C ./vparser
	make -C ./definition_analyzer
	make -C ./definition_resolver
	make -C ./optimizer
	make -C ./tree_constructor
	make -C ./tree_walker
	make -C ./graph
	make -C ./subset
	make -C ./codegen	
	make -C ./controlflow
	make -C ./active_condition
	make -C ./ast_to_code

.PHONY: clean
clean:
	make clean -C ./utils
	make clean -C ./vparser
	make clean -C ./definition_analyzer
	make clean -C ./definition_resolver
	make clean -C ./optimizer
	make clean -C ./tree_constructor
	make clean -C ./tree_walker
	make clean -C ./graph
	make clean -C ./subset
	make clean -C ./codegen	
	make clean -C ./controlflow
	make clean -C ./active_condition
	make clean -C ./ast_to_code
	rm -rf *.pyc __pycache__ *.out parsetab.py *.html
