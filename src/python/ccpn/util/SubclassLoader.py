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
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import sys
import importlib
import inspect


def loadSubclasses(path: str, baseclass, levels=2) -> set:
    '''
    Gather subclasses of baseclass from path

    This attempts to import any file in the directory that doesn't start with a period or underscore,
    Then checks each class definition in that imported module for subclasses of the specified baseclass
    and finally returns the set of all classes it found.
    '''

    extensions = []
    savedPythonPath = sys.path
    try:
        path = os.path.expanduser(path)
        for root, dirs, files in os.walk(path):
            levels -= 1
            if levels == 0:
                break
            dirs = [dir for dir in dirs if not dir.startswith('_')]
            dirs = [dir for dir in dirs if not dir.startswith('.')]
            dirs.insert(0, '.')
            for dir in dirs:
                pth = os.path.join(root, dir)
                sys.path = [pth]
                moduleFiles = os.listdir(pth)
                moduleFiles = [f for f in moduleFiles if not f.startswith('_')]
                moduleFiles = [f for f in moduleFiles if not f.startswith('.')]
                moduleFiles = [os.path.splitext(f)[0] for f in moduleFiles]
                for f in moduleFiles:
                    try:  # Fails on non-python files, directories, etc,...
                        if f not in sys.modules:
                            module = importlib.import_module(f)
                        else:
                            module = importlib.reload(sys.modules.get(f))
                        potentials = inspect.getmembers(module, inspect.isclass)
                        for name, p in potentials:
                            if issubclass(p, baseclass):
                                if p.__module__ == f:  # Make sure we only import classes declared in that module.
                                    extensions.append(p)
                    except ImportError:
                        pass
    finally:
        sys.path = savedPythonPath
    return set(extensions)
