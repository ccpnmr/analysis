"""
This module defines the data loading mechanism for a directory
It creates a list of dataLoaders for each recognised type, optionally filtered
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
__dateModified__ = "$dateModified: 2022-11-05 10:42:26 +0000 (Sat, November 05, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-06-30 10:28:41 +0000 (Fri, June 30, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Logging import getLogger
from ccpn.framework.lib.DataLoaders.DataLoaderABC import \
    DataLoaderABC, checkPathForDataLoader, getDataLoaders, NO_SUFFIX, ANY_SUFFIX
from ccpn.util.traits.CcpNmrTraits import Bool, List, Int
from ccpn.core.lib.ContextManagers import logCommandManager

_DIRECTORY_DATA = 'directoryData'

class DirectoryDataLoader(DataLoaderABC):
    """A directory data loader: loads all recognised files contained in the directory.
    Should be a directory.
    """
    dataFormat = _DIRECTORY_DATA
    suffixes = [NO_SUFFIX, ANY_SUFFIX]  # a list of suffixes that get matched to path
    allowDirectory = True  # Have to allow a directory
    requireDirectory = True  # Require a directory

    recursive = Bool(default_value=False).tag(info='Flag to define recursive behavior')
    dataLoaders = List(default_value=[]).tag(info='List with dataLoader instances for the files of the directory "path"')
    count = Int(default_value=0).tag(info='Count of number of dataLoaders including the recursive ones')

    def __init__(self, path, recursive: bool = False, pathFilter: (tuple, list) = None):
        """
        Initialise the DirectoryLoader instance
        :param path: directory path
        :param recursive: Recursively include subdirectories
        :param pathFilter: Only include defined dataFormats
        """
        super().__init__(path=path)
        self.recursive = recursive
        self.dataLoaders = []
        self.count = 0

        # scan all the files in the directory,
        # skipping dotted files and only processing directories if recursion is True
        if pathFilter is None:
            pathFilter = list(getDataLoaders().keys())

        if _DIRECTORY_DATA in pathFilter:
            pathFilter.remove(_DIRECTORY_DATA)

        # Find valid files to load
        self.isValid = False
        _files = list(self.path.glob('*'))
        for f in _files:
            dataLoader = None
            if f.stem.startswith("."):  # Exclude dotted-files
                pass

            # check if we can find a data loader for f, using the filter which excludes
            # a directory data loader
            elif f.is_file() and \
                (dataLoader := checkPathForDataLoader(f, pathFilter=pathFilter)) is not None:
                self.dataLoaders.append(dataLoader)
                self.count += 1
                self.isValid = True

            # get directories if recursive is True
            elif f.is_dir() and self.recursive:
                dataLoader = DirectoryDataLoader(path=f, recursive=recursive, pathFilter=pathFilter)
                if dataLoader is not None and len(dataLoader) > 0:
                    # Loadable files were found
                    self.dataLoaders.append(dataLoader)
                    self.count += len(dataLoader)
                    self.isValid = True

        getLogger().debug2(f'Directory "{self.path}": {self.count} loadable items out of {len(_files)}')
        self.checkValid()

    def checkValid(self) -> bool:
        """Check if self.path is valid.
        Calls _checkPath and _checkSuffix
        sets self.isValid and self.errorString
        :returns True if ok or False otherwise
        """
        if not super().checkValid():
            return False
        if self.count == 0:
            self.isValid = False
            self.errorString = f'Invalid directory path "{self.path}"; no recognised files found'

    def load(self):
        """The actual loading method;
        :return: a list of [object(s)] representing the directory
        """
        result = []
        for dataLoader in self.dataLoaders:
            objs = dataLoader.load()  # This will automatically recurse
            result.extend(objs)
        return result

    def __len__(self):
        return self.count

DirectoryDataLoader._registerFormat()
