"""
This module defines the data loading mechanism for loading a NEF file
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


class NefDataLoader(DataLoaderABC):
    """NEF data loader
    """

    dataFormat = 'nefFile'
    suffixes = ['.nef']  # a list of suffixes that get matched to path
    allowDirectory = False  # Can/Can't open a directory
    createsNewProject = True

    def __init__(self, path):
        super(NefDataLoader, self).__init__(path)
        self.makeNewProject = self.createsNewProject  # A instance 'copy' to allow modification

    @classmethod
    def checkForValidFormat(cls, path):
        """check if valid format corresponding to dataFormat
        :return: None or instance of the class
        """
        if (_path := cls.checkPath(path)) is None:
            return None
        # assume that all is good
        instance = cls(path)
        return instance

    def load(self):
        """The actual Nef loading method;
        raises RunTimeError on error
        :return: a list of [project]
        """
        try:
            project = self.application._loadNefFile(self.path, makeNewProject=self.makeNewProject)
        except Exception as es:
            raise RuntimeError('Error loading "%s" (%s)' % (self.path, str(es)))

        return [project]

NefDataLoader._registerFormat()