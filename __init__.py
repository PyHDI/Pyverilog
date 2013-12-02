import sys
if sys.version_info[0] < 3:
    import utils
    import vparser
    import definition_analyzer
    import definition_resolver
    import optimizer
    import tree_constructor
    import tree_walker
    import graph
    import subset
    import codegen	
    import controlflow
    import active_condition
    #import ast_to_code # Python 2.x does not support
