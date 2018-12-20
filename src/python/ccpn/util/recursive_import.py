#!/usr/bin/env python

"""python-recursive-import-test [<options>] [<dir> ...]

Recursively find the files under the given directories and launch Python
subprocess that attempt to import them individually.  This is used to check
initalization time problems and dependencies: a well-written program should not
do much on module initialization.  In other words, a good program allows its
modules to be imported individually.  This has important consequences in large
codebases, and allows more flexibility.
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:59 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Martin Blais <blais@furius.ca> $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


import os, re, subprocess
from os.path import *


def find_pyfiles(dirs):
    """
    Find all the files ending with .py
    """
    for dn in dirs:
        dn = abspath(dn)
        for root, dirs, files in os.walk(dn, followlinks=True):
            for r in '.svn', 'CVS':
                try:
                    dirs.remove(r)
                except ValueError:
                    pass

            pyfiles = [fn for fn in files if fn.endswith('.py')]
            if not pyfiles:
                continue

            # Find the root of the packages.
            packroot = root
            while 1:
                if not exists(join(packroot, '__init__.py')):
                    break
                packroot = dirname(packroot)

            for fn in pyfiles:
                yield join(root[len(packroot) + 1:], fn)


def filename2module(fn):
    """
    Given a Python source filename, return a module name to import.
    """
    if basename(fn) == '__init__.py':
        fn = dirname(fn)
    return re.sub('\.py$', '', fn.replace(os.sep, '.'))


def main():
    import optparse

    parser = optparse.OptionParser(__doc__.strip())
    opts, args = parser.parse_args()

    for fn in find_pyfiles(args or ('.',)):
        modname = filename2module(fn)
        print("import %s" % modname)
        subprocess.call(('python', '-c', 'import %s' % modname))


##############################################################################
# Alternative added by Rasmus Fogh, CCPN project 2/2/2016

def find_all_pyfiles(topDirectory, ignoreDirs=(), ignoreFiles=()):
    """
    Find all the files ending with .py inside topDirectory
    """
    dn = packroot = abspath(topDirectory)
    for root, dirs, files in os.walk(dn, followlinks=True):
        for r in ignoreDirs:
            try:
                dirs.remove(r)
                print("test skipping:  %s/%s" % (root, r))
            except ValueError:
                pass

        for fn in files:
            if fn.endswith('.py'):
                if fn in ignoreFiles:
                    print("test skipping:  %s/%s" % (root, fn))
                else:
                    yield join(root[len(packroot) + 1:], fn)


def importAllPyfiles(topDirectory, ignoreDirs=(), ignoreFiles=(), addToSysPath: str = None):
    """Test import all python files in a directory tree.
    topDirectory must be (intended to be) on the Python path"""

    for fn in find_all_pyfiles(topDirectory, ignoreDirs=ignoreDirs, ignoreFiles=ignoreFiles):
        modname = filename2module(fn)
        print("test import %s :" % modname)
        if addToSysPath:
            subprocess.call(('python', '-t', '-c',
                             'import sys; sys.path.append("%s"); import %s'
                             % (addToSysPath, modname)))
        else:
            subprocess.call(('python', '-t', '-c', 'import %s' % modname))


if __name__ == '__main__':
    main()
