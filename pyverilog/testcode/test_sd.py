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
        pass

    def test_supply(self):
        terms, binddict = self.dataflow_wrapper("supply.v")
        expect_bind = set(['(Bind dest:TOP.AAA tree:(IntConst 1))','(Bind dest:TOP.VDD tree:(IntConst 1))','(Bind dest:TOP.VSS tree:(IntConst 0))'])
        self.assertEqual(self.binddict2strset(binddict), expect_bind)

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

    def test_ptr_clock_reset(self):
        terms, binddict = self.dataflow_wrapper("ptr_clock_reset.v")
        self.assertEqual(binddict.values()[0][0].getClockBit(), 2)
        self.assertEqual(binddict.values()[0][0].getResetBit(), 0)

    def test_decimal(self):
        terms, binddict = self.dataflow_wrapper("decimal.v")
        self.assertEqual(binddict.values()[0][0].tostr(),
        "(Bind dest:TOP.cnt1 tree:(Branch Cond:(Terminal TOP.RST) True:(IntConst 'd0) False:(Operator Plus Next:(Terminal TOP.cnt1),(IntConst 8'd1))))")

    def test_ptr_clock_reset(self):
        terms, binddict = self.dataflow_wrapper("decimal2.v")
        self.assertEqual(binddict.values()[0][0].tostr(),
        "(Bind dest:TOP.cnt2 tree:(Branch Cond:(Terminal TOP.RST) True:(IntConst 'd0) False:(Operator Plus Next:(Terminal TOP.cnt2),(IntConst 'd1))))")


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

    def binddict2strset(self, binddict):
        bind_set = set([])
        for item in binddict.items():
            bind_set.add(item[1][0])
        return set([bind.tostr() for bind in bind_set])

if __name__ == '__main__':
    unittest.main()
