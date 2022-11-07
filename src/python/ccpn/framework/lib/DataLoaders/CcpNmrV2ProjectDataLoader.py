"""
This module defines the data loading mechanism for a V2 project
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-11-07 12:05:55 +0000 (Mon, November 07, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-06-30 10:28:41 +0000 (Fri, June 30, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC, NO_SUFFIX
from ccpn.framework.Framework import Framework

from ccpnmodel.ccpncore.memops.metamodel import Constants as metaConstants
MEMOPS = metaConstants.modellingPackageName
IMPLEMENTATION = metaConstants.implementationPackageName


class CcpNmrV2ProjectDataLoader(DataLoaderABC):
    """A CcpNmr V2-project data-loader. Should be a directory.
    """
    dataFormat = 'ccpNmrV2Project'
    suffixes = [NO_SUFFIX]  # a list of suffixes that get matched to path
    allowDirectory = True  # Have to allow a V2 project directory
    requireDirectory = True  # Open V2-project a directory
    alwaysCreateNewProject = True
    canCreateNewProject = False

    loadFunction = (Framework._loadV2Project, 'application')

    def checkValid(self) -> bool:
        """Check if self.path is valid.
        Calls _checkPath and _checkSuffix
        sets self.isValid and self.errorString
        :returns True if ok or False otherwise
        """
        if not super().checkValid():
            return False

        _apiPath = self.path /  MEMOPS / IMPLEMENTATION
        self.isValid = False
        if not _apiPath.exists():
            self.isValid = False
            self.errorString = f'Required sub-directory "{MEMOPS}/{IMPLEMENTATION}" not found'
            return False

        self.isValid = True
        self.errorString =  ''
        return True

CcpNmrV2ProjectDataLoader._registerFormat()
