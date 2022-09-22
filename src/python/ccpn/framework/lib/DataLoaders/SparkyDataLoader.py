"""
This module defines the data loading mechanism for loading a Sparky project
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
__dateModified__ = "$dateModified: 2022-09-22 17:43:36 +0100 (Thu, September 22, 2022) $"
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


class SparkyDataLoader(DataLoaderABC):
    """The Sparky data-loader.
    """
    dataFormat = 'sparkyProject'
    suffixes = ['.proj', '.save']  # a list of suffixes that get matched to path
    allowDirectory = False  # Can/Can't open a directory
    canCreateNewProject = True
    alwaysCreateNewProject = False

    def load(self):
        """The actual sparky loading method; subclassed to account for special
        circumstances
        raises RunTimeError on error
        :return: a list of [project]
        """
        try:
            project = self.application._loadSparkyFile(path=self.path, createNewProject=self.createNewProject)

        except (ValueError, RuntimeError) as es:
            raise RuntimeError('Error loading "%s" (%s)' % (self.path, str(es)))

        return [project]

SparkyDataLoader._registerFormat()
