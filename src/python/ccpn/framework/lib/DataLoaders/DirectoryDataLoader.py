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
__dateModified__ = "$dateModified: 2022-02-16 08:42:10 +0000 (Wed, February 16, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-06-30 10:28:41 +0000 (Fri, June 30, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.lib.DataLoaders.DataLoaderABC import \
    DataLoaderABC, checkPathForDataLoader, getDataLoaders
from ccpn.util.traits.CcpNmrTraits import Bool, List, Int
from ccpn.core.lib.ContextManagers import logCommandManager

_DIRECTORY_DATA = 'directoryData'

class DirectoryDataLoader(DataLoaderABC):
    """A directory data loader
    """
    dataFormat = _DIRECTORY_DATA
    suffixes = []  # a list of suffixes that get matched to path
    allowDirectory = True  # Can/Can't open a directory

    recursive = Bool(default_value=False).tag(info='Flag to define recursive behavior')
    dataLoaders = List(default_value=[]).tag(info='List with dataLoader instances for the files of the directory "path"')
    count = Int(default_value=0).tag(info='Count of number of dataLoaders including the recursive ones')

    @classmethod
    def checkForValidFormat(cls, path):
        """check if valid format corresponding to dataFormat
        :return: None or instance of the class
        """
        if (_path := cls.checkPath(path)) is None:
            return None
        if not _path.is_dir():
            return None
        # assume that all is good for now
        instance = cls(path)
        return instance

    def load(self):
        """The actual loading method;
        :return: a list of [object(s)] representing the directory
        """
        result = []
        for dataLoader in self.dataLoaders:
            objs = dataLoader.load()  # This will automatically recurse
            result.extend(objs)
        return result

    def __init__(self, path, recursive: bool = False, filter: (tuple,list) = None):
        """
        Initialise the DirectoryLoader instance
        :param path: directory path
        :param recursive: Recursively include subdirectories
        :param filter: Only include defined dataFormats
        """
        super().__init__(path=path)
        self.recursive = recursive
        self.dataLoaders = []
        self.count = 0

        # scan all the files in the directory,
        # skipping dotted files and only processing directories if recursion is True
        if filter is None:
            filter = list(getDataLoaders().keys())

        if _DIRECTORY_DATA in filter:
            filter.remove(_DIRECTORY_DATA)

        for f in self.path.glob('*'):
            dataLoader = None
            if f.stem.startswith("."):  # Exclude dotted-files
                pass

            # check if we can find a data loader for f, using the filter which excludes
            # a directory data loader
            elif f.is_file() and \
                (dataLoader := checkPathForDataLoader(f, filter=filter)) is not None:
                self.dataLoaders.append(dataLoader)
                self.count += 1

            # get directories if recursive is True
            elif f.is_dir() and self.recursive:
                dataLoader = DirectoryDataLoader(path=f, recursive=recursive, filter=filter)
                if dataLoader is not None and len(dataLoader) > 0:
                    # Loadable files were found
                    self.dataLoaders.append(dataLoader)
                    self.count += len(dataLoader)

    def __len__(self):
        return self.count

DirectoryDataLoader._registerFormat()
