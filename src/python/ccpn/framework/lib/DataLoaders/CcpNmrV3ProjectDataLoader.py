"""
This module defines the data loading mechanism for a V3 project
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-09-21 15:03:26 +0100 (Wed, September 21, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-06-30 10:28:41 +0000 (Fri, June 30, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC
from ccpn.framework.PathsAndUrls import CCPN_DIRECTORY_SUFFIX, CCPN_API_DIRECTORY
from ccpn.framework.Framework import Framework


class CcpNmrV3ProjectDataLoader(DataLoaderABC):
    """The CcpNmr V3-project data-loader. Should be a directory.
    """
    dataFormat = 'ccpNmrV3Project'
    suffixes = [CCPN_DIRECTORY_SUFFIX]  # a list of suffixes that get matched to path
    allowDirectory = True  # Have to allow a V3 project directory
    requireDirectory = True  # Open a V3 project directory
    alwaysCreateNewProject = True
    canCreateNewProject = False
    loadFunction = (Framework._loadV3Project, 'application')

    def checkValid(self) -> bool:
        """Check if self.path is valid.
        Calls _checkPath and _checkSuffix
        sets self.isValid and self.errorString
        :returns True if ok or False otherwise
        """
        if not super().checkValid():
            return False
        _apiPath = self.path / CCPN_API_DIRECTORY
        if not _apiPath.exists():
            self.isValid = False
            self.errorString = f'Invalid path "{self.path}"; required sub-directory "{CCPN_API_DIRECTORY}" not found'
            return False

        self.isValid = True
        self.errorString =  ''
        return True

    # @classmethod
    # def checkForValidFormat(cls, path):
    #     """check if valid format corresponding to dataFormat
    #     :return: None or instance of the class
    #     """
    #     if (instance := super().checkForValidFormat(path)) is None:
    #         return None
    #     if not instance.checkValid():
    #         # instance.isValid = False
    #         # instance.errorString = f'Invalid path "{instance.path}"; required sub-directory "{CCPN_API_DIRECTORY}" not found'
    #         return None
    #
    #     instance.isValid = True
    #     instance.errorString = ''
    #     return instance

CcpNmrV3ProjectDataLoader._registerFormat()
