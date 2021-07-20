"""
This module defines the data loading mechanism for a directory
It creates a list of dataLoaders for each recognised type, optionally filtered
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

from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC, checkPathForDataLoader
from ccpn.util.traits.CcpNmrTraits import Bool, List, Int
from ccpn.core.lib.ContextManagers import logCommandManager


class DirectoryDataLoader(DataLoaderABC):
    """A directory data loader
    """
    dataFormat = 'directoryData'
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
        raises RunTimeError on error
        :return: a list of [object(s)] representing the directory
        """
        with logCommandManager('application.', 'loadData', self.path):

            result = []
            try:
                for dataLoader in self.dataLoaders:
                    objs = dataLoader.load()  # This will automatically recurse
                    result.extend(objs)
            except (ValueError, RuntimeError) as es:
                raise RuntimeError('Error loading files from "%s"' % self.path)
        return result

    def __init__(self, path, recursive: bool = False, filterForDataFormats: (tuple,list) = None):
        """
        Initialise the DirectoryLoader instance
        :param path: directory path
        :param recursive: Recursively include subdirectories
        :param filterForDataFormats: Only include defined dataFormats
        """
        super().__init__(path=path)
        self.recursive = recursive
        self.count = 0

        # scan all the files in the directory, skipping dotted files and only processing directories
        # if recursion is True
        for f in self.path.glob('*'):
            dataLoader = None
            if f.name.startswith("."):  # Exclude dotted-files
                pass

            elif f.is_dir() and self.recursive: # get directories if recursive is True
                dataLoader = DirectoryDataLoader(path=f, recursive=recursive, filterForDataFormats=filterForDataFormats)
                if dataLoader is not None and len(dataLoader) > 0:
                    # Loadable files were found
                    self.count += len(dataLoader)
                    self.dataLoaders.append(dataLoader)

            elif not f.is_dir():
                # "f" is a file: check if it is of a recognisable dataFormat
                dataLoader = checkPathForDataLoader(f)
                if dataLoader is not None:
                    if filterForDataFormats is not None and \
                       len(filterForDataFormats) > 0 and \
                       dataLoader.dataFormat not in filterForDataFormats:
                        # we are filtering and this dataLoader is not for a desired format
                        pass
                    else:
                        self.dataLoaders.append(dataLoader)
                        self.count += 1

    def __len__(self):
        return self.count

DirectoryDataLoader._registerFormat()
