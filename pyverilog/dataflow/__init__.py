import sys
if sys.version_info[0] < 3:
    import modulevisitor
    import signalvisitor
    import bindvisitor
    import dataflow_analyzer
    import merge
    import walker
    import subset
    import codegen
    import graphgen
