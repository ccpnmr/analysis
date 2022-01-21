"""
This module contains helper code for untarring file
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-01-21 11:22:11 +0000 (Fri, January 21, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2021-07-14 10:28:41 +0000 (Fri, July 14, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import tempfile
import tarfile
import shutil

from ccpn.util.Path import aPath
from ccpn.framework.PathsAndUrls import CCPN_DIRECTORY_SUFFIX

def _unpackCcpnTarfile(tarfilePath, outputDirectoryPath=None):
    """
    Restore project from tarFilePath to outputDirectoryPath
    # CCPNINTERNAL - called in Framework.restoreFromArchive
    """
    tarfilePath = aPath(tarfilePath)

    if outputDirectoryPath is None:
        temporaryDirectory = tempfile.TemporaryDirectory(prefix='CcpnProject_')
        _outputPath = aPath(temporaryDirectory.name)
    else:
        _outputPath = aPath(outputDirectoryPath).fetchDir(tarfilePath.basename)

    cwd = os.getcwd()
    try:
        os.chdir(_outputPath)
        tp = tarfile.open(tarfilePath)
        tp.extractall()

        # look for a ccpn-directory inside _outputPath; there should be exactly one
        _ccpnProjects = _outputPath.listdir(suffix=CCPN_DIRECTORY_SUFFIX)
        if len(_ccpnProjects) == 0:
            raise RuntimeError('Unable to extract archive %r' % tarfilePath)
        elif len(_ccpnProjects) > 1:
            raise RuntimeError('Error extracting archive %r; more than one project' % tarfilePath)


        # relfiles = os.listdir('.')
        # for relfile in relfiles:
        #     fullfile = os.path.join(outputPath, relfile)
        #     if os.path.isdir(fullfile):
        #         outputPath = fullfile
        #         break
        # else:
        #     raise IOError('Could not find project directory in tarfile')

    finally:
        os.chdir(cwd)

    # get the first hit
    result = _ccpnProjects[0]
    return result

    # newName = tarfilePath.basename + CCPN_DIRECTORY_SUFFIX
    # # shutil.move(result.name, newName)
    # return _outputPath / newName
