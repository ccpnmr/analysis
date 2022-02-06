"""
This module defines the data loading mechanism for loading a NMRStar file
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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-02-06 19:34:33 +0000 (Sun, February 06, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-06-30 10:28:41 +0000 (Fri, June 30, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Union, Optional
from contextlib import contextmanager

from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC
from ccpn.framework.lib.ccpnNef import CcpnNefIo
from ccpn.util import Path
from ccpn.core.Project import Project



class StarDataLoader(DataLoaderABC):
    """NMRStar data loader
    """
    dataFormat = 'starFile'
    suffixes = ['.str']  # a list of suffixes that get matched to path
    canCreateNewProject = True
    alwaysCreateNewProject = False

    def __init__(self, path):
        super(StarDataLoader, self).__init__(path)
        self._nefReader = CcpnNefIo.CcpnNefReader(application=self.application)
        self._dataBlock = None

    @property
    def dataBlock(self):
        """Get the NmrdataBlock from the file define by self.path
        """
        if self._dataBlock is None:
            self._dataBlock = self._nefReader.getNMRStarData(str(self.path))
        return self.dataBlock

    def load(self):
        """The actual NMRStar loading method; subclassed to account for special
        circumstances
        :return: a list of [project]
        """
        result = self.application._loadStarFile(dataLoader=self)
        return [result]


StarDataLoader._registerFormat()
