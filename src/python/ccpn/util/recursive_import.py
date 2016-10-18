#!/usr/bin/env python

"""python-recursive-import-test [<options>] [<dir> ...]

Recursively find the files under the given directories and launch Python
subprocess that attempt to import them individually.  This is used to check
initalization time problems and dependencies: a well-written program should not
do much on module initialization.  In other words, a good program allows its
modules to be imported individually.  This has important consequences in large
codebases, and allows more flexibility.
"""

__author__ = 'Martin Blais <blais@furius.ca>'
__version__ = "Revision: 1.10 "

__copyright__ = """Copyright (C) 2006 Martin Blais <blais@furius.ca>.
This code is distributed under the terms of the GNU General Public License."""


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
                yield join(root[len(packroot)+1:], fn)

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
        subprocess.call( ('python', '-c', 'import %s' % modname) )


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
          print("test skipping:  %s/%s" % (root,r))
        except ValueError:
          pass

      for fn in files:
        if fn.endswith('.py'):
          if fn in ignoreFiles:
            print("test skipping:  %s/%s" % (root,fn))
          else:
            yield join(root[len(packroot)+1:], fn)

def importAllPyfiles(topDirectory, ignoreDirs=(),ignoreFiles=(), addToSysPath:str=None):
  """Test import all python files in a directory tree.
  topDirectory must be (intended to be) on the Python path"""

  for fn in find_all_pyfiles(topDirectory, ignoreDirs=ignoreDirs, ignoreFiles=ignoreFiles):
    modname = filename2module(fn)
    print("test import %s :" % modname)
    if addToSysPath:
      subprocess.call( ('python','-t', '-c',
                        'import sys; sys.path.append("%s"); import %s'
                        % (addToSysPath, modname) ) )
    else:
      subprocess.call( ('python', '-t', '-c', 'import %s' % modname) )


if __name__ == '__main__':
    main()

