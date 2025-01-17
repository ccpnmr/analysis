"""Module Documentation here

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
__dateModified__ = "$dateModified: 2018-12-20 14:08:00 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from distutils.core import setup
from distutils.extension import Extension
import sys


if __name__ == '__main__':

    if '--use-cython' in sys.argv:
        USE_CYTHON = True
        sys.argv.remove('--use-cython')
    else:
        USE_CYTHON = False
    ext = '.pyx' if USE_CYTHON else '.c'

    # make a list of Extensions in here, or use '*', '*'+ext to catch all,
    # but puts .so files into a subdirectory /python
    # ignore 'does not match fully qualified name' warnings
    extensions = [Extension('CcpnOpenGLContours',
                            ['CcpnOpenGLContours' + ext],
                            language='c',
                            include_dirs=['c/']), ]

    if USE_CYTHON:
        from Cython.Build import cythonize


        extensions = cythonize(extensions,
                               annotate=True)

    setup(
            ext_modules=extensions
            )
