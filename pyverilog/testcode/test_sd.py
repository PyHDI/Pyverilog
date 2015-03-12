#-------------------------------------------------------------------------------
# test_sd.py
#
#
#
# Copyright (C) 2015, ryosuke fukatani
# License: Apache 2.0
#-------------------------------------------------------------------------------


import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

from pyverilog.dataflow.dataflow_analyzer import *
import unittest


class TestSequenceFunctions(unittest.TestCase):
    def setUp(self):
        path_clone = sys.path
        pop_target = []
        for i,path in enumerate(path_clone):
            if path == 'C:\\Python27\\lib\\site-packages\\pyverilog-0.9.0-py2.7.egg':
                pop_target.append(i)
        for i in reversed(pop_target):
            sys.path.pop(i)
        reload(pyverilog.dataflow.dataflow_analyzer)

    def test_signed(self):
        terms, binddict = self.dataflow_wrapper("signed.v")
        self.assertEqual(binddict.values()[0][0].tostr(),
        "(Bind dest:TOP.cnt tree:(Branch Cond:(Terminal TOP.RST) True:(IntConst 'd0) False:(Operator Plus Next:(Terminal TOP.cnt),(IntConst 1'sd1))))")

    def test_signed_task(self):
        terms, binddict = self.dataflow_wrapper("signed_task.v")
        self.assertEqual(binddict.values()[0][0].tostr(),
        "(Bind dest:TOP.cnt tree:(Branch Cond:(Terminal TOP.RST) True:(Terminal TOP.cnt) False:(Terminal TOP.cnt)))")

    def test_casex(self):
        self.dataflow_wrapper("casex.v")

    def dataflow_wrapper(self,code_file):

        from optparse import OptionParser

        optparser = OptionParser()
        optparser.add_option("-v","--version",action="store_true",dest="showversion",
                             default=False,help="Show the version")
        optparser.add_option("-I","--include",dest="include",action="append",
                             default=[],help="Include path")
        optparser.add_option("-D",dest="define",action="append",
                             default=[],help="Macro Definition")
        optparser.add_option("-t","--top",dest="topmodule",
                             default="TOP",help="Top module, Default=TOP")
        optparser.add_option("--nobind",action="store_true",dest="nobind",
                             default=False,help="No binding traversal, Default=False")
        optparser.add_option("--noreorder",action="store_true",dest="noreorder",
                             default=False,help="No reordering of binding dataflow, Default=False")

        filelist = {code_file}
        options = optparser.get_default_values()


        for f in filelist:
            if not os.path.exists(f): raise IOError("file not found: " + f)

        verilogdataflowanalyzer = VerilogDataflowAnalyzer(filelist, options.topmodule,
                                                          noreorder=options.noreorder,
                                                          nobind=options.nobind,
                                                          preprocess_include=options.include,
                                                          preprocess_define=options.define)
        verilogdataflowanalyzer.generate()

        directives = verilogdataflowanalyzer.get_directives()
        print('Directive:')
        for dr in directives:
            print(dr)

        instances = verilogdataflowanalyzer.getInstances()
        print('Instance:')
        for ins in instances:
            print(ins)

        if options.nobind:
            print('Signal:')
            signals = verilogdataflowanalyzer.getSignals()
            for sig in signals:
                print(sig)

            print('Const:')
            consts = verilogdataflowanalyzer.getConsts()
            for con in consts:
                print(con)

        else:
            terms = verilogdataflowanalyzer.getTerms()
            print('Term:')
            for tk, tv in sorted(terms.items(), key=lambda x:len(x[0])):
                print(tv.tostr())

            binddict = verilogdataflowanalyzer.getBinddict()
            print('Bind:')
            for bk, bv in sorted(binddict.items(), key=lambda x:len(x[0])):
                for bvi in bv:
                    print(bvi.tostr())

        return terms, binddict

if __name__ == '__main__':
    unittest.main()
