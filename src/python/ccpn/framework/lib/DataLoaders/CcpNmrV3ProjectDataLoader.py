"""
This module defines the data loading mechanism for a V3 project
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2018"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: geertenv $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:36 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2018-05-14 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC
from ccpn.util.Path import aPath
from ccpn.framework.PathsAndUrls import CCPN_DIRECTORY_SUFFIX, CCPN_API_DIRECTORY


class CcpNmrV3ProjectDataLoader(DataLoaderABC):
    """V3 project data loader
    """

    dataFormat = 'ccpNmrV3Project'
    suffixes = [CCPN_DIRECTORY_SUFFIX]  # a list of suffixes that get matched to path
    createsNewProject = True

    @classmethod
    def checkForValidFormat(cls, path):
        """check if valid format corresponding to dataFormat
        :return: None or instance of the class
        """
        _path = aPath(path)
        if not _path.exists():
            return None
        if not _path.suffix in cls.suffixes:
            return None
        if not _path.is_dir():
            return None
        # assume that all is good if we find the CCPN_API_DIRECTORY
        _apiPath = _path / CCPN_API_DIRECTORY
        if _apiPath.exists():
            instance = cls(path)
            return instance
        return None

    def load(self):
        """The actual project loading method;
        raises RunTimeError on error
        :return: a list of [project]
        """
        try:
            project = self.application._loadV3Project(self.path)
        except Exception as es:
            raise RuntimeError('Error loading "%s" (%s)' % (self.path, str(es)))

        return [project]

CcpNmrV3ProjectDataLoader._registerFormat()