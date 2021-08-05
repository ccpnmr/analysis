"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$Author: Luca Mureddu $"
__dateModified__ = "$Date: 2021-07-31 19:26:11 +0000 (,  31, 2021) $"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2021-07-31 19:26:11 +0000 (,  31, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================


"""
Main server script for a pyqode.python backend. 
    Copied from:
    - miniconda/lib/python3.8/site-packages/pyqode/python/backend/server.py
    
    Called from /ui/gui/widgets/QPythonEditor.py at the init of super class PyCodeEditor
"""

import argparse
import sys


if __name__ == '__main__':
    """
    Server process' entry point
    """

    # setup argument parser and parse command line args
    parser = argparse.ArgumentParser()
    parser.add_argument("port", help="the local tcp port to use to run "
                        "the server")
    parser.add_argument('-s', '--syspath', nargs='*')
    args = parser.parse_args()

    # add user paths to sys.path
    if args.syspath:
        for path in args.syspath:
            sys.path.append(path)

    from pyqode.core import backend
    from pyqode.python.backend.workers import JediCompletionProvider

    # setup completion providers
    backend.CodeCompletionWorker.providers.append(JediCompletionProvider())
    backend.CodeCompletionWorker.providers.append(
        backend.DocumentWordsProvider())

    # starts the server
    backend.serve_forever(args)

