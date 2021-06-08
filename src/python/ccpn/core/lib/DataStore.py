"""

Code to:
    - implement path redirections $DATA, $ALONGSIDE, $INSIDE
    - implement a DataStore object to handle Spectrum file paths properly
    - thereby wraps the silly dataStore and dataUrl data structures

Replaced:
    - core.lib.util.expandDollarFilePath
    - cor.lib.util._fetchDataUrl

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-04-20 15:57:57 +0100 (Tue, April 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2017-04-07 10:28:48 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os

from ccpn.util.Path import aPath, Path
from ccpn.framework import constants
from ccpn.util.traits.CcpNmrJson import CcpNmrJson
from ccpn.util.traits.CcpNmrTraits import Unicode, Any, CPath, Bool, Dict, CString

from ccpn.util.decorators import singleton

from ccpn.framework.Application import getApplication
from ccpn.util.Logging import getLogger


#=========================================================================================
# Redirections
#=========================================================================================

class RedirectionABC(CcpNmrJson):
    """
    Base class for maintaining a single redirection
    """

    apiName = None  # to be subclassed
    identifier = None # to be subclassed
    expand = False # expand to handle None, zero-length and '.'

    _application = Any(default_value=None, allow_none=True)
    _path = CPath(default_value=None, allow_none=True)

    def __init__(self):
        super().__init__()
        self._application = getApplication()

    @property
    def path(self):
        if self.expand:
            return self.expandPath()
        else:
            return self._path

    def expandPath(self):
        "expand path to handle None, zero-length and '.'"
        if self._path is None or len(self._path) == 0:
            self._path = Path.home()
        elif self._path == '.':
            self._path = Path.cwd()
        return self._path

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.identifier)

    __repr__ = __str__


@singleton
class DataRedirection(RedirectionABC):

    identifier = '$DATA'
    apiName = 'remoteData'
    expand = True

    @property
    def path(self):
        if self._path is None:
            self._path = aPath(self._application.preferences.general.dataPath)
        return super().path

    @path.setter
    def path(self, path):
        self._path = aPath(path)
        self._application.preferences.general.dataPath = str(self._path)


@singleton
class InsideRedirection(RedirectionABC):

    identifier = '$INSIDE'
    apiName = 'insideData'
    expand = False

    @property
    def path(self):
        self._path = aPath(self._application.project.path)
        return super().path


@singleton
class AlongsideRedirection(RedirectionABC):

    identifier = '$ALONGSIDE'
    apiName = 'alongsideData'
    expand = False

    @property
    def path(self):
        self._path = aPath(self._application.project.path).parent
        return super().path


@singleton
class PathRedirections(list):
    """
    Class to maintain the path redirections $DATA, $ALONGSIDE, $INSIDE
    """

    def __init__(self):
        super().__init__()
        self.append(DataRedirection())
        self.append(AlongsideRedirection())
        self.append(InsideRedirection())

    @property
    def dataPath(self):
        return self[0].path

    @dataPath.setter
    def dataPath(self, path):
        self[0].path = path

    @property
    def alongsidePath(self):
        return self[1].path

    @property
    def insidePath(self):
        return self[2].path

    def getPaths(self):
        "Return a list of (identifier, path) tuples"
        paths = [(r.identifier, r.path) for r in self]
        return paths

    def getApiMappings(self):
        "Return a list with (apiName, indentifier) tuples"
        pairs = [(r.apiName, r.identifier) for r in self]
        return pairs

    def _getPathFromApiStore(self, storeName):
        """Return path associated with api storeName; for backward compatibility purposes
        """
        apiNames = [r.apiName for r in self]
        if storeName not in apiNames:
            raise ValueError('_getPathFromApiStore: invalid storeName "%s"' % storeName)

        project = getApplication().project
        if project is None:
            raise RuntimeError('_getPathFromApiStore: undefined project')

        dataUrl = project._apiNmrProject.root.findFirstDataLocationStore(
                    name='standard').findFirstDataUrl(name=storeName)
        path = dataUrl.url.dataLocation
        return path

#=========================================================================================
# DataStores
#=========================================================================================

class DataStore(CcpNmrJson):
    """
    This class wraps the implementation of $DATA, $ALONGSIDE, $INSIDE redirections
    """

    # For old Spectrum instances, its parses the api insideData, remoteData, alongSideData etc.
    # api dataStores
    #
    # Once linked to a Spectrum, it stores the path and other relevant info as json-encoded string
    # in the spectrum instance internal parameter storage

    version = 1.0

    _path = CPath(allow_none=True, default_value=None).tag(saveToJson=True)
    dataFormat = CString(allow_none=True, default_value=None).tag(saveToJson=True)

    spectrum = Any(allow_none=True, default_value=None).tag(saveToJson=False)
    autoVersioning = Bool(default_value=True).tag(saveToJson=False)
    autoRedirect = Bool(default_value=False).tag(saveToJson=False)

    # api dataStore
    apiDataStore = Any(allow_none=True, default_value=None).tag(saveToJson=False)
    apiDataStoreName = Unicode(allow_none=True, default_value=None).tag(saveToJson=True)
    apiDataStoreDir = Unicode(allow_none=True, default_value=None).tag(saveToJson=True)
    apiDataStorePath = Unicode(allow_none=True, default_value=None).tag(saveToJson=True)

    # Dict with edirection paths; for reference
    pathRedirections = Dict(default_value={}).tag(saveToJson=True)

    def __init__(self, spectrum=None, autoRedirect=False, autoVersioning=False):
        """
        autoRedirect: optionally try to redefine path into $DATA, $ALONGSIDE, $INSIDE redirections
        autoVersioning: optionally add a versioning identifier (e.g. for new spectra)
        """
        super().__init__()
        self.spectrum = spectrum
        self.autoRedirect = autoRedirect
        self.autoVersioning = autoVersioning

        self._getPathRedirections()

    @property
    def path(self):
        """Return a Path representation of self, optionally encoded with $DATA, $ALONGSIDE, $INSIDE redirections
        """
        if self._path is None:
            return Path(constants.UNDEFINED_STRING)

        return Path(self._path)

    @path.setter
    def path(self, value):
        """Set path to value; optionally auto versioning or redirecting
        None makes it undefined
        """
        self._path = value
        while self._path is not None and self.autoVersioning and self.exists():
            self._path = self.path.incrementVersion().asString()

        if self._path is not None and self.autoRedirect:
            self._path = self.redirectPath(self._path)

        if self.spectrum is not None:
            self._saveInternal()

    @classmethod
    def newFromPath(cls, path, autoRedirect=False, autoVersioning=False,
                         appendToName=None, withSuffix=None, dataFormat=None):
        """Create and return a new instance from path; optionally append to name and set suffix
        """
        _p = Path(path)

        suffix = _p.suffix if withSuffix is None else withSuffix

        if appendToName is not None:
            _p = _p.parent / _p.basename + appendToName

        if len(suffix) > 0:
            _p = _p.withSuffix(suffix)

        instance = cls(autoRedirect=autoRedirect, autoVersioning=autoVersioning)
        instance.path = _p

        instance.dataFormat= dataFormat

        return instance

    def hasPathDefined(self):
        """Return True if path has been defined
        """
        return self._path is not None

    def expandPath(self, path=None):
        """return path decoded for $DATA, $ALONGSIDE, $INSIDE redirections
        returns Path instance
        """
        if path is None:
            _path = Path(self._path)
        else:
            _path = Path(path)

        for d, p in self._getPathRedirections():
            if _path.startswith(d):
                _path = p / Path._from_parts(_path.parts[1:])  # Using undocumented private method!
                break
        return _path

    def redirectPath(self, path=None):
        """Redefine path into $DATA, $ALONGSIDE, $INSIDE redirections
        return Path instance
        """
        if path is None:
            _path = Path(self._path)
        else:
            _path = Path(path)

        # check in reverse order, prioritising $INSIDE, then $ALONGSIDE, then $DATA
        for d, p in self._getPathRedirections()[::-1]:
            if str(path).startswith(str(p)):
                _path = Path(d) / _path.relative_to(p)
                break
        return _path

    def aPath(self):
        """Return aPath instance of self, decoded for $DATA, $ALONGSIDE, $INSIDE redirections
        """
        if self._path is None:
            return aPath(constants.UNDEFINED_STRING)
        # expand any $DATA, $INSIDE $ALONGSIDE
        _path = self.expandPath(self._path)
        return aPath(_path)

    def exists(self):
        """Return True if self.aPath() (i.e. expanded) exists
        """
        if self._path is None:
            return False
        else:
            return self.aPath().exists()

    def warningMessage(self):
        """Error message displayed on logger
        """
        getLogger().warning(self._message())

    def errorMessage(self):
        """Error message displayed on logger
        """
        getLogger().error(self._message())

    #=========================================================================================
    # Implementation
    #=========================================================================================

    def _importFromSpectrum(self, spectrum):
        """Restore state from spectrum, either from internal parameter store or from api-dataStores
        Returns self
        """
        if spectrum is None:
            raise ValueError('Invalid spectrum "%s"' % spectrum)

        if spectrum._hasInternalParameter(spectrum._DATASTORE_KEY):
            self.spectrum = spectrum
            self._restoreInternal()
        else:
            self._restoreFromApiSpectrum(spectrum._wrappedData)
            self.spectrum = spectrum
            self._saveInternal()

        return self

    def _saveInternal(self):
        """Save into spectrum internal parameter store
        CCPNINTERNAL: e.g. _newSpectrum
        """
        if self.spectrum is None:
            raise RuntimeError('%s._saveInternal: spectrum not defined' % self.__class__.__name__)

        jsonData = self.toJson()
        self.spectrum._setInternalParameter(self.spectrum._DATASTORE_KEY, jsonData)

    def _restoreInternal(self):
        """Restore from spectrum internal parameter store
        CCPNINTERNAL: e.g. _newSpectrum
        """
        if self.spectrum is None:
            raise RuntimeError('%s._restoreInternal: spectrum not defined' % self.__class__.__name__)

        jsonData = self.spectrum._getInternalParameter(self.spectrum._DATASTORE_KEY)
        if jsonData is None or len(jsonData) == 0:
            raise RuntimeError('DataStore._restoreInternal: json data appear to be corrupted')

        self.fromJson(jsonData)

    def _restoreFromApiSpectrum(self, apiSpectrum):
        """This routine implements the extraction from the old storage mechanism (using api DataStores).
        Returns self
        """
        if apiSpectrum is None:
            raise ValueError('Invalid spectrum "%s"' % apiSpectrum)

        self.apiDataStore = apiSpectrum.dataStore

        if self.apiDataStore is not None:
            self.apiDataStoreName = self.apiDataStore.dataUrl.name
            self.apiDataStoreDir = self.apiDataStore.dataUrl.url.path
            self.apiDataStorePath = self.apiDataStore.path

            # Encode the different dataStores
            pDict = dict(PathRedirections().getApiMappings())
            if self.apiDataStoreName in pDict:
                self._path = os.path.join(pDict[self.apiDataStoreName], self.apiDataStorePath)
            else:
                self._path = os.path.join(self.apiDataStoreDir, self.apiDataStorePath)

            self.dataFormat = self.apiDataStore.fileType

        else:
            # This happens for dummy spectra
            from ccpn.core.lib.SpectrumDataSources.EmptySpectrumDataSource import EmptySpectrumDataSource
            self._path = None
            self.dataFormat = EmptySpectrumDataSource.dataFormat

        return self

    def _getPathRedirections(self):
        """Get the redirection paths; return list of items of the pathRedirection dict
        """
        redirections = PathRedirections().getPaths()
        # Convert and store the redirections for future reference
        self.pathRedirections = dict( [(r, str(p)) for r, p in redirections] )
        return redirections

    def _message(self):
        """return message to be displayed on logger
        """
        text = 'path "%s" is invalid ' % self.path
        for d, p in self._getPathRedirections():
            if self.path.startswith(d):
                if p.exists():
                    text += ' (check %s)' % d
                else:
                    text += ' (%s "%s" does not exist)' % (d, p)
                break
        return text

    def __eq__(self, other):
        return self._path == other._path

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return '<%s: %s (%s)>' % (self.__class__.__name__, self.path, self.dataFormat)

    __repr__ = __str__


from ccpn.util.traits.CcpNmrTraits import Instance
from ccpn.util.traits.TraitJsonHandlerBase import CcpNmrJsonClassHandlerABC

class DataStoreTrait(Instance):
    """Specific trait for a Datastore instance encoding the path and dataFormat of the (binary) spectrum data.
    None indicates no spectrum data file path has been defined
    """
    def __init__(self, **kwds):
        Instance.__init__(self, klass=DataStore, allow_none=True, **kwds)

    class jsonHandler(CcpNmrJsonClassHandlerABC):
        klass = DataStore
