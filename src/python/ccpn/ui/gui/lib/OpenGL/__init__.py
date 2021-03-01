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
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-03-01 19:14:38 +0000 (Mon, March 01, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2018-12-20 13:28:13 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Logging import getLogger
from ctypes import util
from PyQt5 import QtWidgets
import sys

_OpenGLLibraryPathOSX = '/System/Library/Frameworks/%s.framework/%s'

def patched_find_library(name):
    res = util.find_library(name)
    if res: return res
    return _OpenGLLibraryPathOSX %(name, name)

try:
    try:
        from OpenGL import GL, GLU, GLUT
        import OpenGL.arrays.vbo as VBO
    except ImportError:
        # getLogger().warn('Error importing OpenGL libraries... Patching imports for OS X 11.x')
        util.find_library = patched_find_library
        from OpenGL import GL, GLU, GLUT
        import OpenGL.arrays.vbo as VBO
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "Error importing OpenGL.",
                                   "OpenGL must be installed to run CcpNmrAnalysis correctly.")
    sys.exit(1)
