"""
This module defines the data loading mechanism for a V2 project
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
__dateModified__ = "$dateModified: 2021-07-20 21:57:01 +0100 (Tue, July 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-06-30 10:28:41 +0000 (Fri, June 30, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC
from ccpn.framework.Framework import Framework

from ccpnmodel.ccpncore.memops.metamodel import Constants as metaConstants
MEMOPS = metaConstants.modellingPackageName
IMPLEMENTATION = metaConstants.implementationPackageName


class CcpNmrV2ProjectDataLoader(DataLoaderABC):
    """V2 project data loader
    """
    dataFormat = 'ccpNmrV2Project'
    suffixes = []  # a list of suffixes that get matched to path
    allowDirectory = True  # Can/Can't open a directory
    alwaysCreateNewProject = True
    canCreateNewProject = False
    loadFunction = (Framework._loadV2Project, 'application')

    @classmethod
    def checkForValidFormat(cls, path):
        """check if valid format corresponding to dataFormat
        :return: None or instance of the class
        """
        if (_path := cls.checkPath(path)) is None:
            return None
        if not _path.is_dir():
            return None
        # assume that all is good if we find the CCPN_API_DIRECTORY
        _apiPath = _path / MEMOPS / IMPLEMENTATION
        if _apiPath.exists():
            # it is a directory that has memops/implementation subdirectory,
            # so we must assume it to be a V2 project directory.
            instance = cls(path)
            return instance
        return None

CcpNmrV2ProjectDataLoader._registerFormat()