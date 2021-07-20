"""
This module contains helper code for untarring file
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
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
__dateModified__ = "$dateModified: 2021-07-20 21:57:02 +0100 (Tue, July 20, 2021) $"
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

def _unpackCcpnTarfile(tarfilePath, outputPath=None, directoryPrefix='CcpnProject_'):
    """
    # CCPNINTERNAL - called in Framework.restoreFromArchive
    """

    if outputPath:
        if not os.path.exists(outputPath):
            os.makedirs(outputPath)
        temporaryDirectory = None
    else:
        temporaryDirectory = tempfile.TemporaryDirectory(prefix=directoryPrefix)
        outputPath = temporaryDirectory.name

    cwd = os.getcwd()
    try:
        os.chdir(outputPath)
        tp = tarfile.open(tarfilePath)
        tp.extractall()

        # look for a directory inside and assume the first found is the project directory (there should be exactly one)
        relfiles = os.listdir('.')
        for relfile in relfiles:
            fullfile = os.path.join(outputPath, relfile)
            if os.path.isdir(fullfile):
                outputPath = fullfile
                break
        else:
            raise IOError('Could not find project directory in tarfile')

    finally:
        os.chdir(cwd)

    return outputPath, temporaryDirectory
