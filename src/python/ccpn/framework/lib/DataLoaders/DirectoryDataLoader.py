"""
This module defines the data loading mechanism for a directory
It creates a list of dataLoaders for each recognised type, optionally filtered
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
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
__dateModified__ = "$dateModified: 2024-07-25 10:11:17 +0100 (Thu, July 25, 2024) $"
__version__ = "$Revision: 3.2.5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-06-30 10:28:41 +0000 (Fri, June 30, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Logging import getLogger
from ccpn.framework.lib.DataLoaders.DataLoaderABC import (
    DataLoaderABC, _checkPathForDataLoader, NotFoundDataLoader,
    getDataLoaders, NO_SUFFIX, ANY_SUFFIX)
from ccpn.util.traits.CcpNmrTraits import Bool, List, Int


_DIRECTORY_DATA = 'directoryData'


class DirectoryDataLoader(DataLoaderABC):
    """A directory data loader: loads all recognised files contained in the directory.
    Should be a directory.
    """
    dataFormat = _DIRECTORY_DATA
    suffixes = [NO_SUFFIX, ANY_SUFFIX]  # a list of suffixes that get matched to path
    allowDirectory = True  # Have to allow a directory
    requireDirectory = True  # Require a directory
    priority = 3  # lower priority, project type checks should come before

    recursive = Bool(default_value=False).tag(info='Flag to define recursive behavior')
    dataLoaders = List(default_value=[]).tag(
            info='List with dataLoader instances for the files of the directory "path"')
    count = Int(default_value=0).tag(info='Number of valid dataLoaders including the recursive ones')
    depth = Int(default_value=0).tag(info='Number of subdirectories to traverse from the root')

    def __init__(self, path, recursive: bool = True, formatFilter: (tuple, list) = None, depth=0):
        """
        Initialise the DirectoryLoader instance
        :param path: directory path
        :param recursive: Recursively include subdirectories
        :param formatFilter: Only include defined dataFormats
        """

        super().__init__(path=path)
        self.recursive = recursive
        self.dataLoaders = []
        self.count = 0
        self.depth = depth

        # scan all the files in the directory,
        # skipping dotted files and only processing directories if recursion is True

        # Find valid files to load
        if not self.path.is_dir():
            raise RuntimeError(f'{self.path} is not a directory')

        _filesToExamine = self.path.listdir(excludeDotFiles=True)
        _filesToExamine.sort()
        _nFilesToExamine = len(_filesToExamine)

        # for f in _filesToExamine:
        while len(_filesToExamine) > 0:
            _path = _filesToExamine.pop(0)

            dataLoader = None
            if _path.stem.startswith("."):  # Exclude dotted-files
                pass

            elif _path.is_file():
                # check if we can find a data loader for _path, using  formatFilter
                # _checkPathForDataLoader always returns a dataLoader, potentially NotFoundDataLoader
                dataLoader = _checkPathForDataLoader(path=_path, formatFilter=formatFilter)[-1]
                if dataLoader.isValid or dataLoader.shouldBeValid:
                    self.dataLoaders.append(dataLoader)
                    if dataLoader.isValid:
                        self.count += 1
                    # remove all files already handled by the dataLoader; this prevents types that
                    # have two files; e.g. a binary data file and a parameter file, to be added twice
                    for _handledFile in dataLoader.getAllFilePaths():
                        if _handledFile in _filesToExamine:
                            _filesToExamine.remove(_handledFile)

            elif _path.is_dir():
                # This situation is harder, as this could be a directory as a Spectrum (e.g Bruker)
                # which should be included, or yet another directory which inclusion depends on the
                # recursion flag.
                _filters = list(formatFilter) if formatFilter is not None else \
                           list(getDataLoaders().keys())
                # Find dataLoader for _path if it was anything but a general directory
                if DirectoryDataLoader.dataFormat in _filters:
                    _filters.remove(DirectoryDataLoader.dataFormat)

                # _checkPathForDataLoader always returns a dataLoader, potentially NotFoundDataLoader
                dataLoader = _checkPathForDataLoader(path=_path, formatFilter=_filters)[-1]
                if dataLoader.isValid or dataLoader.shouldBeValid:
                    self.dataLoaders.append(dataLoader)
                    if dataLoader.isValid:
                        self.count += 1

                # Haven't found a dataLoader yet; add _path using DirectoryLoader if recursive is True
                if dataLoader.dataFormat == NotFoundDataLoader.dataFormat and recursive:
                    if (_dirLoader := DirectoryDataLoader(path=_path,
                                                          recursive=recursive,
                                                          formatFilter=_filters,
                                                          depth=self.depth + 1)) and \
                            _dirLoader.isValid:
                        # add dataLoaders
                        self.dataLoaders.extend(_dirLoader.dataLoaders)
                        self.count += _dirLoader.count

        getLogger().debug2(f'Directory "{self.path}": {self.count} loadable items out of {_nFilesToExamine}')

        self.checkValid()

    def checkValid(self) -> bool:
        """Check if self.path is valid.
        Calls _checkPath and _checkSuffix
        sets self.isValid and self.errorString
        :returns True if ok or False otherwise
        """
        if not super().checkValid():
            return False

        # We now have found a directory; expect to find loadable files
        self.shouldBeValid = True

        self.isValid = False
        self.errorString = 'Checking validity'

        if self.count == 0:
            _shouldBeValid = len([dl for dl in self.dataLoaders if dl.shouldBeValid])
            _text = f'; \nhowever {_shouldBeValid} should be valid but encountered errors' if _shouldBeValid>0 else ''
            self.errorString = f'{self.path}: No valid files found {_text}'
            return False

        self.isValid = True
        self.errorString = ''
        return True

    def load(self):
        """The actual loading method;
        :return: a list of [object(s)] representing the directory
        """
        result = []
        for dataLoader in self.dataLoaders:
            if dataLoader.isValid and (objs := dataLoader.load()) is not None:
                result.extend(objs)
        return result

    def __len__(self):
        return self.count

    @property
    def maximumDepth(self) -> int:
        maxD = self.depth
        for loader in self.dataLoaders:
            if isinstance(loader, DirectoryDataLoader):
                maxD = max(maxD, loader.maximumDepth)
        return maxD

    @property
    def newProjectCount(self) -> int:
        maxD = 0
        for loader in self.dataLoaders:
            if isinstance(loader, DirectoryDataLoader):
                maxD += loader.newProjectCount
            elif loader.createNewProject:
                maxD += 1
        return maxD


DirectoryDataLoader._registerFormat()
