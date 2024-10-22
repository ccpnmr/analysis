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
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-10-22 08:11:10 +0100 (Tue, October 22, 2024) $"
__version__ = "$Revision: 3.2.5.GWV $"
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

from ccpn.framework.Application import getApplication, getProject
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

    _path = CPath(default_value=None, allow_none=True)

    @property
    def path(self):
        if self.expand:
            return self.expandPath()
        else:
            return self._path

    def expandPath(self):
        """expand path to handle None, zero-length and '.'"""
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
    def path(self) -> Path:
        """:return dataPath from application preferences
        """
        if (_app := getApplication()) is None:
            raise RuntimeError(f'DataRedirection.path: unable to get application')
        if self._path is None:
            self._path = aPath(_app.preferences.general.dataPath)
        return super().path

    @path.setter
    def path(self, path):
        if (_app := getApplication()) is None:
            raise RuntimeError(f'DataRedirection.path: unable to get application')
        self._path = aPath(path)
        _app.preferences.general.dataPath = str(self._path)


@singleton
class InsideRedirection(RedirectionABC):

    identifier = '$INSIDE'
    apiName = 'insideData'
    expand = False

    @property
    def path(self) -> Path:
        """:return project path, or None if project is not defined
        """
        if (_project := getProject()) is None:
            return None
        self._path = aPath(_project.path)
        return super().path


@singleton
class AlongsideRedirection(RedirectionABC):

    identifier = '$ALONGSIDE'
    apiName = 'alongsideData'
    expand = False

    @property
    def path(self) -> Path:
        """:return directory where project resides, or None if project is not defined
        """
        if (_project := getProject()) is None:
            return None
        self._path = aPath(_project.path).parent
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

    def getPaths(self) -> dict:
        """:return a dict of (identifier, path) pairs
        """
        # paths = [(r.identifier, r.path) for r in self]
        paths = dict((r.identifier, getattr(r, 'path', None)) for r in self)
        return paths

    def getApiMappings(self):
        """Return a list with (apiName, indentifier) tuples"""
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

    classVersion = '1.0.0'
    _encodeAsJson_3_0 = True  # needs to be readible by all versions

    _path = CPath(allow_none=True, default_value=None).tag(saveToJson=True)
    dataFormat = CString(allow_none=True, default_value=None).tag(saveToJson=True)
    useBuffer = Bool(default_value=False).tag(saveToJson=True,
                info="""Flag to indicate if spectrum should be opened in buffered mode"""
    )

    spectrum = Any(allow_none=True, default_value=None).tag(saveToJson=False)
    autoVersioning = Bool(default_value=True).tag(saveToJson=False)
    autoRedirect = Bool(default_value=False).tag(saveToJson=False)

    # api dataStore
    apiDataStore = Any(allow_none=True, default_value=None).tag(saveToJson=False)
    apiDataStoreName = Unicode(allow_none=True, default_value=None).tag(saveToJson=True)
    apiDataStoreDir = Unicode(allow_none=True, default_value=None).tag(saveToJson=True)
    apiDataStorePath = Unicode(allow_none=True, default_value=None).tag(saveToJson=True)

    # Dict with redirection paths; for reference
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

        # self._getPathRedirections()

    @property
    def path(self) -> Path:
        """Return a Path representation of self, optionally encoded with $DATA, $ALONGSIDE, $INSIDE redirections
        """
        if self._path is None:
            return Path(constants.UNDEFINED_STRING)

        return Path(self._path)

    @path.setter
    def path(self, value):
        """Set path to value; optionally auto versioning or redirecting
        len(value) = 0 or None makes it undefined
        """
        if value is not None:
            if not isinstance(value, (str, Path)):
                raise ValueError(f'invalid value "{value}"')

            value = str(value)
            if len(value) == 0:
                value = None

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
        instance.dataFormat = dataFormat

        instance.path = _p

        return instance

    def hasPathDefined(self) -> bool:
        """:return True if path has been defined
        """
        return self._path is not None

    def expandPath(self, path=None) -> Path:
        """return path decoded for $DATA, $ALONGSIDE, $INSIDE redirections
        :parameter path: path to expand (set to self._path if None)
        :return Path instance
        """
        # first convert to a path instance
        if path is not None:
            _path = Path(path)
        elif path is None and self._path is not None:
            _path = Path(self._path)
        else:
            raise RuntimeError('Undefined path: cannot expand')

        for d, p in self._getPathRedirections().items():
            if _path.startswith(d):
                if p is None:
                    raise RuntimeError(f'Undefined redirection "{d}" for {_path}; this can happen if getProject() yielded None')
                _path = p / Path._from_parts(_path.parts[1:])  # Using undocumented private method!
                break
        return _path

    def redirectPath(self, path=None) -> Path:
        """Redefine path into $DATA, $ALONGSIDE, $INSIDE redirections
        :return Path instance
        """
        if path is not None:
            _path = Path(path)
        elif path is None and self._path is not None:
            _path = Path(self._path)
        else:
            raise RuntimeError('Undefined path: cannot redirect')

        # check in reverse order, prioritising $INSIDE, then $ALONGSIDE, then $DATA
        for d, p in list(self._getPathRedirections().items())[::-1]:
            p = str(p)
            if _path.startswith(p):
                _path = Path(d) / _path.relative_to(p)
                break
        return _path

    @property
    def redirectionIdentifier(self):
        """Return the identifier of the current redirection
        """
        # check in reverse order, prioritising $INSIDE, then $ALONGSIDE, then $DATA
        return next((d for d, p in self._getPathRedirections().items() if self._path and self._path.startswith(d)), None)

    def aPath(self) -> Path:
        """:return aPath instance of self, decoded for $DATA, $ALONGSIDE, $INSIDE redirections
        """
        if self._path is None:
            return aPath(constants.UNDEFINED_STRING)
        # expand any $DATA, $INSIDE $ALONGSIDE
        _path = self.expandPath(self._path)
        return aPath(_path)

    def exists(self) -> bool:
        """:return True if self.aPath() (i.e. expanded) exists
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
        :return self
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

        jsonData = self.toJson(indent=None)  # Use compact style
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
        :return self
        """
        from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
        from ccpn.core.lib.SpectrumDataSources.EmptySpectrumDataSource import EmptySpectrumDataSource

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

            # Convert the (potentially old) dataFormat specifier
            _tmp = self.apiDataStore.fileType
            if (_dataFormat := SpectrumDataSourceABC._dataFormatDict.get(_tmp)) is None:
                getLogger().warning(f'Restore dataFormat from older definitions: dataFormat "{_tmp}": not recognised')
            self.dataFormat = _dataFormat

        else:
            # This happens for dummy spectra
            self._path = None
            self.dataFormat = EmptySpectrumDataSource.dataFormat

        return self

    def _getPathRedirections(self) -> dict:
        """Get the redirection paths;
        :return the pathRedirection dict
        #CCPNINTERNAL: V4 Spectrum._postRestore
        """
        redirections = PathRedirections().getPaths()
        for redirection, path in redirections.items():
            # check path
            if path is None:
                getLogger().debug(f'Path of redirection {redirection} is None; using fallback')
                path = self.pathRedirections.get(redirection, None)
                if path is not None:
                    path = Path(path)
                redirections[redirection] = path
            else:
                # store the redirection for future reference
                self.pathRedirections[redirection] = str(path)
        return redirections

    def _message(self):
        """return message to be displayed on logger
        """
        text = 'path "%s" is invalid' % self.path
        for d, p in self._getPathRedirections():
            if self.path.startswith(d):
                if p is None:
                    text += f'; no path for {d} defined'
                elif not p.exists():
                    text += f'; {d} (= {p}) does not exist)'
                else:
                    text += f'; check {d} (= {p})'
                break
        return text

    def __eq__(self, other):
        if not isinstance(other, DataStore):
            return False
        else:
            return self._path == other._path

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return '<%s: %s (dataFormat=%r, useBuffer=%s)>' % \
               (self.__class__.__name__, self.path, self.dataFormat, self.useBuffer)

    __repr__ = __str__

DataStore.register()


# GWV: moved to ccpn.core.lib.CoreTraits
# from ccpn.util.traits.CcpNmrTraits import OWTraits
#
# class DataStoreTrait(OWTraits):
#     """Specific trait for a Datastore instance encoding the path and dataFormat of the (binary) spectrum data.
#     None indicates no spectrum data file path has been defined
#     """
#     klass = DataStore
#     # def __init__(self, **kwds):
#     #     OWTraits.__init__(self, klass=self.klass, allow_none=True, **kwds)

