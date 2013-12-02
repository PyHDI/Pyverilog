#-------------------------------------------------------------------------------
# active_condition.py
#
# Active condition list generator from Verilog Definitions with Pyverilog
#
# Copyright (C) 2013, Shinya Takamaeda-Yamazaki
# License: Apache 2.0
#-------------------------------------------------------------------------------

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

import pyverilog.utils.version
import pyverilog.utils.util as util
import pyverilog.utils.tree_reorder as tree_reorder
import pyverilog.utils.tree_splitter as tree_splitter
import pyverilog.utils.inference as inference
import pyverilog.utils.state_transition as state_transition
from pyverilog.utils.dataflow import *

from pyverilog.controlflow.controlflow import VerilogControlflow

class VerilogActiveCondition(VerilogControlflow):
    def __init__(self, topmodule, terms, binddict, 
                 resolved_terms, resolved_binddict, constlist):
        VerilogControlflow.__init__(self, topmodule, terms, binddict, 
                                    resolved_terms, resolved_binddict, constlist)
        self.fsm_loops, self.fsms = self.getLoops()

    ############################################################################
    def getActiveConditions(self, termname, condition=tree_splitter.active_constant):
        if not termname in self.resolved_binddict: return {}
        tree = self.makeTree(termname)
        funcdict = tree_splitter.split(tree)
        funcdict = tree_splitter.filter(funcdict, termname, condition)
        funcdict = tree_splitter.remove_reset_condition(funcdict)

        if len(funcdict) == 1 and len(list(funcdict.keys())[0]) == 0:
            func = funcdict.values()[0]
            return {termname : ( ('any', None), )}

        active_conditions = {}
        active_conditions_size = 0
        for fsm_sig in self.fsms.keys():
            rslt = self.getActiveConditions_fsm(fsm_sig, funcdict)
            if len(rslt) > 0: active_conditions[fsm_sig] = rslt
            active_conditions_size += len(rslt)

        if active_conditions_size == 0:
            rslt = self.getActiveConditions_fsm(termname, funcdict)
            if len(rslt) > 0: active_conditions[termname] = rslt

        return active_conditions

    def getActiveConditions_fsm(self, fsm_sig, funcdict):
        # returns a list of some (state, transcond) pairs
        active_conditions = []
        fsm_sig_width = self.getWidth(fsm_sig)
        for condlist, func in sorted(funcdict.items(), key=lambda x:len(x[0])):
            node = state_transition.walkCondlist(condlist, fsm_sig, fsm_sig_width)
            state_node_list = []
            if isinstance(node, state_transition.StateNodeList):
                for n in node.nodelist: state_node_list.append(n)
            elif node:
                state_node_list.append(node)

            for state_node in state_node_list:
                #if state_node.isany:
                #    active_conditions.append( ('any', state_node.transcond) )
                for rs, re in state_node.range_pairs:
                    for state in range(rs, re+1):
                        transcond = self.optimizer.optimize(state_node.transcond)
                        if isinstance(transcond, DFEvalValue) and transcond.value == 0: continue
                        active_conditions.append( (state, transcond) )
        return tuple(active_conditions)
            
################################################################################
if __name__ == '__main__':
    from optparse import OptionParser
    from pyverilog.definition_analyzer.definition_analyzer import VerilogDefinitionAnalyzer
    from pyverilog.definition_resolver.definition_resolver import VerilogDefinitionResolver
    INFO = "Active condition analyzer for Verilog definitions with Pyverilog"
    VERSION = pyverilog.utils.version.VERSION
    USAGE = "Usage: python active_analyzer.py -t TOPMODULE file ..."

    def showVersion():
        print(INFO)
        print(VERSION)
        print(USAGE)
        sys.exit()
    
    optparser = OptionParser()
    optparser.add_option("-v","--version",action="store_true",dest="showversion",
                         default=False,help="Show the version")
    optparser.add_option("-t","--top",dest="topmodule",
                         default="TOP",help="Top module, Default=TOP")
    optparser.add_option("-s","--search",dest="searchtarget",action="append",
                         default=[],help="Search Target Signal")
    (options, args) = optparser.parse_args()

    filelist = args
    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f): raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()

    verilogdefinitionanalyzer = VerilogDefinitionAnalyzer(filelist, options.topmodule)
    verilogdefinitionanalyzer.generate()

    directives = verilogdefinitionanalyzer.get_directives()
    terms = verilogdefinitionanalyzer.getTerms()
    binddict = verilogdefinitionanalyzer.getBinddict()

    verilogdefinitionresolver = VerilogDefinitionResolver(terms, binddict)

    verilogdefinitionresolver.resolveConstant()
    resolved_terms = verilogdefinitionresolver.getResolvedTerms()
    resolved_binddict = verilogdefinitionresolver.getResolvedBinddict()
    constlist = verilogdefinitionresolver.getConstlist()

    active = VerilogActiveCondition(options.topmodule, terms, binddict, resolved_terms, resolved_binddict, constlist)

    for target in options.searchtarget:
        signal = util.toTermname(target)
        active_conditions = active.getActiveConditions( signal )

        #active_conditions = active.getActiveConditions( signal, condition=tree_splitter.active_modify )
        #active_conditions = active.getActiveConditions( signal, condition=tree_splitter.active_unmodify )

        print('Active Cases: %s' % signal)
        for fsm_sig, active_conditions in sorted(active_conditions.items(), key=lambda x:str(x[0])):
            print('FSM: %s' % fsm_sig)
            for state, active_condition in sorted(active_conditions, key=lambda x:str(x[0])):
                s = []
                s.append('state: %d -> ' % state)
                if active_condition: s.append(active_condition.tocode())
                else: s.append('empty')
                print(''.join(s))
