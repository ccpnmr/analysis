"""
This module defines the data loading mechanism.

Loader instances have all the information regarding a particular data type
(e.g. a ccpn project, a NEF file, a PDB file, etc. and include a load() function to to the actual
work of loading the data into the project.
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
__dateModified__ = "$dateModified: 2022-09-19 20:46:18 +0100 (Mon, September 19, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-06-30 10:28:41 +0000 (Fri, June 30, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict, defaultdict
from typing import Tuple

from ccpn.util.Path import Path, aPath
from ccpn.util.traits.TraitBase import TraitBase
from ccpn.util.traits.CcpNmrTraits import Unicode, Any, List, Bool, CPath, Odict, CString
from ccpn.util.Logging import getLogger
from ccpn.util.decorators import singleton


#--------------------------------------------------------------------------------------------
# Need to review lib/io/Formats.py and ioFormats.analyseUrl(path)
#--------------------------------------------------------------------------------------------

CCPNMRTGZCOMPRESSED = 'ccpNmrTgzCompressed'
CCPNMRZIPCOMPRESSED = 'ccpNmrZipCompressed'

SPARKYFILE = 'sparkyFile'

# NO_SUFFIX = 'No-suffix'
# ANY_SUFFIX = 'Any-suffix'
from ccpn.framework.constants import NO_SUFFIX, ANY_SUFFIX

def getDataLoaders() -> dict:
    """Get data loader classes
    :return: a dictionary of (format-identifier-strings, DataLoader classes) as (key, value) pairs
    """
    #--------------------------------------------------------------------------------------------
    # The following imports are just to assure that all the classes have been imported
    # hierarchy matters!
    # It is local to prevent circular imports
    #--------------------------------------------------------------------------------------------
    from ccpn.framework.lib.DataLoaders.CcpNmrV3ProjectDataLoader import CcpNmrV3ProjectDataLoader
    from ccpn.framework.lib.DataLoaders.CcpNmrV2ProjectDataLoader import CcpNmrV2ProjectDataLoader
    from ccpn.framework.lib.DataLoaders.SpectrumDataLoader import SpectrumDataLoaderABC
    from ccpn.framework.lib.DataLoaders.NefDataLoader import NefDataLoader
    from ccpn.framework.lib.DataLoaders.StarDataLoader import StarDataLoader
    from ccpn.framework.lib.DataLoaders.FastaDataLoader import FastaDataLoader
    from ccpn.framework.lib.DataLoaders.ExelDataLoader import ExcelDataLoader
    from ccpn.framework.lib.DataLoaders.PdbDataLoader import PdbDataLoader
    from ccpn.framework.lib.DataLoaders.TextDataLoader import TextDataLoader
    from ccpn.framework.lib.DataLoaders.PythonDataLoader import PythonDataLoader
    from ccpn.framework.lib.DataLoaders.HtmlDataLoader import HtmlDataLoader
    from ccpn.framework.lib.DataLoaders.SparkyDataLoader import SparkyDataLoader
    from ccpn.framework.lib.DataLoaders.DirectoryDataLoader import DirectoryDataLoader
    return DataLoaderABC._dataLoaders


def getSpectrumLoaders() -> dict:
    """Get data spectrum-specific loader classes
    :return: a dictionary of (format-identifier-strings, DataLoader classes) as (key, value) pairs
    """
    _loaders = getDataLoaders()
    return dict( [(df, dl) for df, dl in _loaders.items() if dl.isSpectrumLoader])


def _getSuffixDict() -> Tuple[dict, defaultdict]:
    """
    :return dict of (suffix, [dataLoader class]-list) (key, value) pairs

    NB: Only to be used internally
    """
    _loadersDict = getDataLoaders()

    # create an (suffix, [dataFormats]) dict
    _suffixDict = defaultdict(list)

    for dType, dl in _loadersDict.items():

        suffixes =  [NO_SUFFIX, ANY_SUFFIX] if len(dl.suffixes) == 0 else dl.suffixes
        for suffix in suffixes:

            suffix = NO_SUFFIX if suffix is None else suffix
            _suffixDict[suffix].append(dl)

    return _suffixDict


def _getPotentialDataLoaders(path) -> list:
    """
    :param path: path to evaluate
    :return list of possible dataLoader classes based on suffix

    NB: Only to be used internally
    """

    if path is None:
        raise ValueError('Undefined path')
    path = aPath(path)

    # get the dict that maps the suffix to potential loaders
    _suffixDict =  _getSuffixDict()
    if len(path.suffixes) == 0:
        # No suffix; return all loaders that are accept no-suffix
        loaders = _suffixDict.get(NO_SUFFIX, [])
    else:
        # get the loaders for suffix; fall-back to those that accept any suffix
        # in case there was none defined for suffix
        loaders = _suffixDict.get(path.suffix,
                                  _suffixDict.get(ANY_SUFFIX, []))

    # # filter for loaders that do not allow a directory
    # if path.is_dir():
    #     # we have a directory
    #     loaders = [dl for dl in loaders if (dl.allowDirectory or dl.requireDirectory)]
    # else:
    #     # we have a file; i.e. all the loaders that not requireDirectory
    #     loaders = [dl for dl in loaders if (not dl.requireDirectory)]

    return loaders


def checkPathForDataLoader(path, pathFilter=None):
    """Check path if it corresponds to any defined data format.
    Optionally exclude any dataLoader with types not in pathFilter (default: all dataFormats)

    :param pathFilter: a tuple/list of dataFormat strings; expands to all dataFormat if None
    :return a DataLoader instance or None if there was no match
    """
    if not isinstance(path, (str, Path)):
        raise ValueError('checkPathForDataLoader: invalid path %r' % path)

    _path = aPath(path)
    if not _path.exists():
        raise ValueError('checkPathForDataLoader: path %r does not exist' % path)

    if pathFilter is None:
        pathFilter = list(getDataLoaders().keys())

    _loaders = _getPotentialDataLoaders(path)
    for cls in _loaders:
        instance = cls.checkForValidFormat(path)
        if instance is None:
            getLogger().debug2('%-20s %-20s: %s' % (cls.dataFormat, '(Not Valid)', path))
            continue

        # we found an instance
        if cls.dataFormat not in pathFilter:
            getLogger().debug2('%-20s %-20s: %s' % (cls.dataFormat, '(Valid, not in filter)', path))
            return None
        else:
            getLogger().debug2('%-20s %-20s: %s' % (cls.dataFormat, '(Valid, in filter)', path))
            return instance  # we found a valid format for path

    return None

#--------------------------------------------------------------------------------------------
# DataLoader class
#--------------------------------------------------------------------------------------------

class DataLoaderABC(TraitBase):
    """A DataLoaderABC: has definition for patterns

    Maintains a load() method to call the actual loading function (presumably from self.application
    or self.project
    """

    #=========================================================================================
    # to be subclassed
    #=========================================================================================
    dataFormat = None
    suffixes = []  # a list of suffixes that gets matched to path
    alwaysCreateNewProject = False
    canCreateNewProject = False
    allowDirectory = False  # Can/Can't open a directory
    requireDirectory = False  # explicitly require a directory
    isSpectrumLoader = False    # Subclassed for SpectrumLoaders
    loadFunction = (None, None) # A (function, attributeName) tuple;
                                # :param function(obj:(Application,Project), path:Path) -> List[newObj]
                                # :param attributeName := 'project' or 'application'

    #=========================================================================================
    # end to be subclassed
    #=========================================================================================

    # traits
    path = CPath().tag(info='a path to a file to be loaded')
    application = Any(default_value=None, allow_none=True)

    # project related
    createNewProject = Bool(default_value=False).tag(info='flag to indicate if a new project will be created')
    newProjectName = CString(default_value='newProject').tag(info='Name for a new project')
    makeArchive = Bool(default_value=False).tag(info='flag to indicate if a project needs to be archived before loading')

    # new implementation, using newFromPath method and validity testing later on
    isValid = Bool(default_value=False).tag(info='flag to indicate if path denotes a valid dataType')
    errorString = CString(default_value='').tag(info='error description for validity testing')

    ignore = Bool(default_value=False).tag(info='flag to indicate if loader needs ignoring')

    # A dict of registered DataLoaders: filled by _registerFormat classmethod, called
    # once after each definition of a new derived class (e.g. PdbDataLoader)
    _dataLoaders = OrderedDict()

    @classmethod
    def _registerFormat(cls):
        """register cls.dataFormat"""
        if cls.dataFormat in DataLoaderABC._dataLoaders:
            raise RuntimeError('dataLoader "%s" was already registered' % cls.dataFormat)
        DataLoaderABC._dataLoaders[cls.dataFormat] = cls

    #=========================================================================================
    # start of methods
    #=========================================================================================
    def __init__(self, path):
        super().__init__()
        self.path = aPath(path)
        # if not self.path.exists():
        #     raise ValueError('Invalid path "%s"' % path)

        # get default setting for project creation
        self.createNewProject = self.alwaysCreateNewProject or self.canCreateNewProject
        self.makeArchive = False

        # local import to avoid cycles
        from ccpn.framework.Application import getApplication
        self.application = getApplication()

    @property
    def project(self):
        """Current project instance
        """
        return self.application.project

    @classmethod
    def newFromPath(cls, path):
        """New instance with path
        :return: instance of the class
        """
        instance = cls(path)
        return instance

    @classmethod
    def checkForValidFormat(cls, path):
        """check if valid format corresponding to dataFormat
        :return: None or instance of the class

        Can be subclassed
        """
        instance = cls(path)
        if not instance._checkPath():
            return None
        # assume that all is good
        return instance
        #
        # if (_path := cls.checkPath(path)) is None:
        #     return None
        # # assume that all is good
        # instance = cls(path)
        # return instance

    def load(self):
        """The actual file loading method;
        raises RunTimeError on error
        :return: a list of [objects]

        Can be subclassed
        """
        try:
            func, attributeName = self.loadFunction
            obj = getattr(self, attributeName)
            result = func(obj, self.path)

        except (ValueError, RuntimeError) as es:
            raise RuntimeError('Error loading "%s" (%s)' % (self.path, str(es)))

        return result

    @classmethod
    def checkSuffix(cls, path) -> bool:
        """Check if suffix of path confirms to settings of class attribute suffixes.
        :returns True or False
        """
        _path = aPath(path)
        if len(_path.suffixes) == 0 and NO_SUFFIX in cls.suffixes:
            return True
        if len(_path.suffixes) > 0 and ANY_SUFFIX in cls.suffixes:
            return True
        if len(_path.suffixes) > 0 and _path.suffix in cls.suffixes:
            return True
        return False

    @classmethod
    def checkPath(cls, path):
        """Check if path exists and confirms to settings of class attributes suffixes and allowDirectory
        do not allow dot-file (e.g. .cshrc)
        :returns Path instance of path, or None
        """
        _path = aPath(path)
        if not _path.exists():
            return None
        if not cls.checkSuffix(path):
            return None
        if _path.basename == '':
            return None
        if _path.is_dir() and not cls.allowDirectory:
            # path is a directory: cls does not allow
            return None
        if not _path.is_dir() and cls.requireDirectory:
            # path is a file, but cls requires a directory
            return None
        return _path

    def checkValid(self) -> bool:
        """Check if self.path is valid.
        Calls _checkPath and _checkSuffix
        sets self.isValid and self.errorString
        :returns True if ok or False otherwise
        Can be subclassed
        """
        self.isValid = False
        self.errorString = ''

        if not self._checkSuffix():
            return False
        if not self._checkPath():
            return False

        self.isValid = True
        return True

    def _checkSuffix(self) -> bool:
        """Check if suffix of self.path confirms to settings of class attribute suffixes.
        sets self.isValid and self.errorString
        :returns True if ok or False otherwise
        """
        _path = self.path
        if len(_path.suffixes) == 0 and NO_SUFFIX in self.suffixes:
            self.isValid = True
            return True
        if len(_path.suffixes) > 0 and ANY_SUFFIX in self.suffixes:
            self.isValid = True
            return True
        if len(_path.suffixes) > 0 and _path.suffix in self.suffixes:
            self.isValid = True
            return True

        self.isValid = False
        self.errorString = f'Invalid path suffix for "{_path}"; should be one of {self.suffixes}'
        return False

    def _checkPath(self):
        """Check if self.path exists and confirms to settings of class attributes suffixes and allowDirectory
        do not allow dot-file (e.g. .cshrc)
        :returns True if ok or False otherwise
        """
        _path = self.path
        if not _path.exists():
            self.errorString = f'Path "{_path}" does not exists'
            self.isValid = False
            return False
        if not self._checkSuffix():
            return False
        if _path.basename == '':
            self.errorString = f'Invalid path "{_path}"'
            self.isValid = False
            return False
        if _path.is_dir() and not self.allowDirectory:
            # path is a directory: cls does not allow
            self.errorString = f'Invalid path "{_path}"; directory not allowed'
            self.isValid = False
            return False
        if not _path.is_dir() and self.requireDirectory:
            # path is a file, but cls requires a directory
            self.errorString = f'Invalid path "{_path}"; directory required'
            return False

        self.errorString = ''
        self.isValid = True
        return True

    @classmethod
    def _documentClass(cls) -> str:
        """:return a documentation string comprised of __doc__ and some class attributes
        """
        if cls.requireDirectory:
            _directory = 'Required'
        elif cls.allowDirectory:
            _directory = 'Allowed'
        else:
            _directory = 'Not allowed'

        if cls.canCreateNewProject:
            _newProject = 'Potentially'
        elif cls.alwaysCreateNewProject:
            _newProject = 'Always'
        else:
            _newProject = 'Never'

        result = cls.__doc__ +\
            f'\n' +\
            f'    Valid suffixes:      {cls.suffixes}\n' +\
            f'    Directory:           {_directory}\n' +\
            f'    Creates new project: {_newProject}'

        return result

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.path)

    __repr__ = __str__


