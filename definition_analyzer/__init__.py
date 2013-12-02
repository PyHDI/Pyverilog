import sys
if sys.version_info[0] < 3:
    import modulevisitor
    import signalvisitor
    import bindvisitor
    import definition_analyzer
