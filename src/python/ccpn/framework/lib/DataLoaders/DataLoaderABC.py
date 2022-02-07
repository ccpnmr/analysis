"""
This module defines the data loading mechanism.

Loader instances have all the information regarding a particular data type
(e.g. a ccpn project, a NEF file, a PDB file, etc. and include a load() function to to the actual
work of loading the data into the project.
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
__dateModified__ = "$dateModified: 2022-02-07 12:34:47 +0000 (Mon, February 07, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-06-30 10:28:41 +0000 (Fri, June 30, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict

from ccpn.util.Path import Path, aPath
from ccpn.util.traits.TraitBase import TraitBase
from ccpn.util.traits.CcpNmrTraits import Unicode, Any, List, Bool, CPath, Odict
from ccpn.util.Logging import getLogger
from ccpn.util.decorators import singleton


#--------------------------------------------------------------------------------------------
# Need to review lib/io/Formats.py and ioFormats.analyseUrl(path)
#--------------------------------------------------------------------------------------------

CCPNMRTGZCOMPRESSED = 'ccpNmrTgzCompressed'
CCPNMRZIPCOMPRESSED = 'ccpNmrZipCompressed'

SPARKYFILE = 'sparkyFile'

def getDataLoaders():
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
    from ccpn.framework.lib.DataLoaders.SpectrumDataLoader import SpectrumDataLoader
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


def checkPathForDataLoader(path, filter=None):
    """Check path if it corresponds to any defined data format.
    Optionally exclude any dataLoader with types defined by filter

    :param filter: a tuple/list of dataFormat strings
    :return a DataLoader instance or None if there was no match
    """
    if not isinstance(path, (str, Path)):
        raise ValueError('checkPathForDataLoader: invalid path %r' % path)

    _path = aPath(path)
    if not _path.exists():
        raise ValueError('checkPathForDataLoader: path %r does not exist' % path)

    if filter is None:
        filter = list(getDataLoaders().keys())

    for fmt, cls in getDataLoaders().items():
        instance = cls.checkForValidFormat(path)
        if instance is None:
            getLogger().debug2('%-20s %-20s: %s' % (cls.dataFormat, '(Not Valid)', path))
            continue

        # we found an instance
        if cls.dataFormat not in filter:
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
    loadFunction = (None, None) # A (function, attributeName) tuple;
                                # :param function(obj:(Application,Project), path:Path) -> List[newObj]
                                # :param attributeName := 'project' or 'application'

    #=========================================================================================
    # end to be subclassed
    #=========================================================================================

    # traits
    path = CPath().tag(info='a path to a file to be loaded')
    application = Any(default_value=None, allow_none=True)
    createNewProject = Bool().tag(info='flag to indicate if a new project will be created')

    # A dict of registered DataLoaders: filled by _registerFormat classmethod, called
    # once after each definition of a new derived class (e.g. PdbDataLoader)
    _dataLoaders = OrderedDict()

    @classmethod
    def _registerFormat(cls):
        "register cls.dataFormat"
        if cls.dataFormat in DataLoaderABC._dataLoaders:
            raise RuntimeError('dataLoader "%s" was already registered' % cls.dataFormat)
        DataLoaderABC._dataLoaders[cls.dataFormat] = cls

    #=========================================================================================
    # start of methods
    #=========================================================================================
    def __init__(self, path):
        super().__init__()
        self.path = aPath(path)
        if not self.path.exists():
            raise ValueError('Invalid path "%s"' % path)

        # get default setting for project creation
        self.createNewProject = self.alwaysCreateNewProject or self.canCreateNewProject

        # local import to avoid cycles
        from ccpn.framework.Application import getApplication
        self.application = getApplication()

    @property
    def project(self):
        """Current poject instance
        """
        return self.application.project

    @classmethod
    def checkForValidFormat(cls, path):
        """check if valid format corresponding to dataFormat
        :return: None or instance of the class

        Can be subclassed
        """
        if (_path := cls.checkPath(path)) is None:
            return None
        # assume that all is good
        instance = cls(path)
        return instance

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
    def checkPath(cls, path):
        """Check if path exists and confirms to settings of class attributes suffixes and allowDirectory
        do not allow dot-file (e.g. .cshrc)
        :returns Path instance of path, or None
        """
        _path = aPath(path)
        if not _path.exists():
            return None
        if len(cls.suffixes) > 0 and not _path.suffix in cls.suffixes:
            return None
        if _path.basename == '':
            return None
        if _path.is_dir() and not cls.allowDirectory:
            return None
        return _path

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.path)

    __repr__ = __str__


