import os
import sys
import subprocess

text = open('list_ast.txt', 'r').read()
lines = text.split('\n')
for line in lines:
    if line != '':
        subprocess.call('touch template/' + line.lower() + '.txt', shell=True)
