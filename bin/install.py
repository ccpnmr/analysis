#!/usr/bin/env python --

from __future__ import print_function
import os


print('hello: running', __file__)

path1 = os.path.abspath(__file__)
#print(path1)

ccpnmr_top_dir = os.path.normpath(os.path.dirname(path1) + '/..')  # one up from the bin direcotry
#print(ccpnmr_top_dir)

userdir = os.path.expanduser('~/.ccpn')
#print(userdir)

if not os.path.exists(userdir):
	os.makedirs(userdir)
	
path2 = os.path.join(userdir, 'path.sh')
with open(path2, 'w') as fp:
	fp.write('#!/bin/bash\n')
	fp.write('export CCPNMR_TOP_DIR="%s"' % ccpnmr_top_dir)
	
print('Done, created "%s"' % path2)



