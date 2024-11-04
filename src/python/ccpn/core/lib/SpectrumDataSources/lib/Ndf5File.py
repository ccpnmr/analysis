"""
This file contains the Ndf5File definitions and its implementation on the h5py standard

Version history:
No-version:     Luca's initial implementation
1.0 (float):    Version info (float) stored as 'version' in spectrum parameters;
                spectralWidth definition updated (if need be)
1.0.1 (string): ndf5 metadata; stored in attributes top object (i.e. self.fp)
1.1.0 (string): ndf5 metadata; implementation change

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
__dateModified__ = "$dateModified: 2024-11-04 13:51:27 +0000 (Mon, November 04, 2024) $"
__version__ = "$Revision: 3.2.7.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2024-10-10 18:53:48 +0000 (Thu, October 10, 2024) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Tuple
import numpy as np
import h5py

from ccpn.util.Logging import getLogger
from ccpn.util.Common import isIterable
from ccpn.framework.Version import VersionString

from ccpn.core._implementation.SpectrumData import SliceData, PlaneData, RegionData


#--------------------------------------------------------------------------------------------------
# ndf5 metadata keys, as stored in the 'top' file object and copied into the metadata dict
#
NDF5_VERSION_KEY = 'ndf5_version'
NDF5_VERSION = VersionString('1.1.0')  # Current ndf5 implementation version

NDF5_UID_KEY = 'uid'
NDF5_USER_KEY = 'user'
NDF5_DATE_KEY = 'date'
NDF5_SPECTROMETER_KEY = 'spectrometer'

# the key in the metadata dict defining the dict of all data types contained in the file
NDF5_DATATYPES_KEY = 'dataTypes'
# the key in the metadata dict defining datatype used for retrieving the spectrum data
NDF5_SPECTRUM_DATATYPE_KEY = 'spectrum_dataType'

# Metadata Version 1.0.1 definitions
HDF5_VERSION_KEY = 'HDF5_Version'
HDF5_DATATYPE_KEY = 'HDF5_DataType'
HDF5_DATASET_KEY = 'HDF5_DatasetName'

_defaultNdf5MetadataDict = {

    NDF5_VERSION_KEY : str(NDF5_VERSION),
    NDF5_UID_KEY : None,
    NDF5_USER_KEY : None,
    NDF5_DATE_KEY : None,
    NDF5_SPECTROMETER_KEY : None,

    # key to the data types present in the ndf5-file
    NDF5_DATATYPES_KEY : {},
    # key to the spectrum-data descriptor
    NDF5_SPECTRUM_DATATYPE_KEY : None,

    # for backward compatibility, allowing older code to read newly generated ndf5 files
    HDF5_VERSION_KEY : '1.0.1',
    HDF5_DATATYPE_KEY: 'SpectrumData',
    HDF5_DATASET_KEY: 'spectrumData',
}

#--------------------------------------------------------------------------------------------------
# ndf5 dataTypes and data locations
#--------------------------------------------------------------------------------------------------

NDF5_SPECTRUM = 'spectrum'
# pulseprogram:
NDF5_DATATYPE_PULSEPROGRAM =        f'dataType_{NDF5_SPECTRUM}_pulseprogram'
# spectrum: a complete (i.e. all dimensions), np.ndarray-like data matrix
NDF5_DATATYPE_SPECTRUM_NDARRAY =    f'dataType_{NDF5_SPECTRUM}_ndarray'

# NUS:
NDF5_NUS = 'nus'
NDF5_DATATYPE_NUSLIST =             f'dataType_{NDF5_NUS}_nuslist'
NDF5_DATATYPE_NUSDATA =             f'dataType_{NDF5_NUS}_nusdata'

# NEF
NDF5_NEF = 'nef'
NDF5_DATATYPE_NEFDATA =             f'dataType_{NDF5_NEF}_nefdata'

# Dict of ndf5 data types and their (default) ndf5-file storage key;
_ndf5DataTypes = {
    NDF5_DATATYPE_SPECTRUM_NDARRAY  : 'spectrumData', # historical; keep for now
    NDF5_DATATYPE_PULSEPROGRAM      : f'pulseprogram',

    NDF5_DATATYPE_NUSLIST           : f'{NDF5_NUS}/nuslist',
    NDF5_DATATYPE_NUSDATA           : f'{NDF5_NUS}/nusdata',

    NDF5_DATATYPE_NEFDATA           : f'{NDF5_NEF}/nefdata',
}

#--------------------------------------------------------------------------------------------------
# Compression modes
#
# GWV 2020 for full files:
#   lzf compression seems not to yield any improvement, but rather a increase in file size;
#   gzip compression some (max 30%) reductions, albeit at a speed-penalty
# GWV 7/10/2024 update:
#   gzip works well on file writing sparse data and the sparse=True option

NDF5_COMPRESSION_GZIP = 'gzip'
NDF5_COMPRESSION_LZF = 'lzf'
# 'szip' not in conda distribution
# NDF5_COMPRESSION_SZIP = 'szip'
NDF5_COMPRESSION_MODES = (NDF5_COMPRESSION_GZIP, NDF5_COMPRESSION_LZF)


#--------------------------------------------------------------------------------------------------
# a class to set property getter, setter from the metadata dict

class _Property(property):
    # GWV: Only by having no doc strings I seem to be able to dynamically set these!

    # """A property class for the getting and setting of attributes from the metadata dict
    # """
    def __init__(self, attributeName, key, hasSetter, cast=None, doc=None):
        # GWV: Only by having no doc strings I seem to be able to dynamically set these!

        # """
        # :param attributeName: the name of the attribute
        # :param key: the corresponding key in metadata dict
        # :param hasSetter: flag to include setter
        # :param cast: optional casting function
        # :param doc: optional documentation; if None, taken from 'info' tag for traits
        # """

        super(_Property, self).__init__(fget=self._getter, fset=self._setter, doc=doc)
        self.attributeName = attributeName
        self.key = key
        self.hasSetter = hasSetter
        self.cast = cast
        self.__doc__ = self.doc = doc

    def _getter(self, __instance):
        if not self.key in __instance.metadata:
            raise AttributeError(f'Cannot get {__instance.__class.__.__name__}.{self.attributeName}: invalid key "{self.key}"')
        result = __instance.metadata[self.key]
        if self.cast:
            result = self.cast(result)
        return result

    def _setter(self, __instance, value):
        if not self.hasSetter:
            raise AttributeError(f'Cannot set {__instance.__class.__.__name__}.{self.attributeName}')
        if not self.key in __instance.metadata:
            raise AttributeError(f'Cannot set {__instance.__class.__.__name__}.{self.attributeName}: invalid key "{self.key}"')
        __instance.metadata[self.key] = value

#--------------------------------------------------------------------------------------------------


class Ndf5File(object):
    """A class that implements the ndf5 standard
    """

    version =      _Property('version', NDF5_VERSION_KEY, hasSetter=False, cast=VersionString,
                             doc='The current ndf5 version as a VersionString instance')
    uid =          _Property('uid', NDF5_UID_KEY, hasSetter=False,
                             doc='The UID of the file')
    user =         _Property('user', NDF5_USER_KEY, hasSetter=True,
                             doc='The user associated with the file')
    date =         _Property('date', NDF5_DATE_KEY, hasSetter=True,
                             doc='The date associated with the file')
    spectrometer = _Property('spectrometer', NDF5_SPECTROMETER_KEY, hasSetter=True,
                             doc='The spectrometer associated with the file')

    dataTypes =    _Property('dataTypes', NDF5_DATATYPES_KEY, hasSetter=False,
                             doc='The dict with available (dataType, ndf5-dataKey) pairs present in the file')

    spectrumDataType = _Property('spectrumDataType', NDF5_SPECTRUM_DATATYPE_KEY, hasSetter=True,
                             doc=' The spectrum dataType')

    # @property
    # def spectrumDataType(self) -> str:
    #     """:return The spectrum dataType, as contained in NDF5_SPECTRUM_DATATYPE_KEY
    #     """
    #     return self.metadata[NDF5_SPECTRUM_DATATYPE_KEY]
    #
    # @spectrumDataType.setter
    # def spectrumDataType(self, value: str):
    #     """Set spectrumDataType to value
    #     """
    #     if value not in _ndf5DataTypes:
    #         raise ValueError(f'Ndf5File.spectrumDataType: invalid dataType "{value}"')
    #     self.metadata[NDF5_SPECTRUM_DATATYPE_KEY] = value

    def getSpectrumDataKey(self):
        """:return The spectrum dataKey used for retrieving the spectrum data in the ndf5 file.
                   Retrieved from self.spectrumDataType and the self.dataTypes dict.
                   Return None if there is no dataKey defined.
        """
        if (_dataType := self.spectrumDataType) is None:
            return None
        return self.dataTypes.get(_dataType, None)

    def getSpectrumData(self):
        """:return The spectrumData instance as defined by the spectrumDataKey
        :raises RuntimeError, KeyError
        """
        if self.fp is None:
            raise RuntimeError(f'Ndf5File.getSpectrumData(): File is closed')
        if (_dataKey := self.getSpectrumDataKey()) is None:
            raise KeyError((f'Ndf5File.getSpectrumData(): invalid dataKey "{_dataKey}"'))
        if (_data := self.fp.get(_dataKey, None)) is None:
            raise KeyError((f'Ndf5File.getSpectrumData(): no data for dataKey "{_dataKey}"'))
        return _data

    def getSpectrumParameters(self) -> dict:
        """:return A dict of (parameterName, parameterValue) pairs as contained in the attributes of the
                   spectrumData.
        :raises RuntimeError on error
        """
        if self.fp is None:
            raise RuntimeError(f'Ndf5File.getSpectrumParameters(): File is closed')
        try:
            dataset = self.getSpectrumData()
        except KeyError as es:
            raise RuntimeError(f'Ndf5File.getSpectrumParameters(): unable to get spectrum dataset')

        _params = dataset.attrs
        result = {}
        for parName, value in _params.items():
            result[parName] = _decode(value)

        return result

    def setSpectrumParameters(self, parameterDict, clear=True):
        """Set the attributes of the spectrumData from the parameterDict.
        :param parameterDict: Dict of (parameterName, parameterValue) pairs
        :param clear: Flag to optionally clear the attributes first
        :raises RuntimeError on error
        """
        if self.fp is None:
            raise RuntimeError(f'Ndf5File.setSpectrumParameters(): File is closed')
        try:
            dataset = self.getSpectrumData()
        except KeyError as es:
            raise RuntimeError(f'Ndf5File.setSpectrumParameters(): unable to get spectrum dataset')

        _params = dataset.attrs

        if clear:
            for parName, value in _params.items():
                del _params[parName]

        for parName, value in parameterDict.items():
            _params[parName] = _encode(value)

    def __init__(self, dataSource):
        """Initialise the object; maintain the backling to the dataSource object
        """

        self.dataSource = dataSource
        self.metadata = {}  # The dict with metadata, upgraded later
        self.blockUpdate = 0   # blocking for when updating

        self.path = None
        self.mode = None
        self.cacheSize = None
        self.newFile = None
        self.fp = None  # The h5py.File object

    def open(self, path, mode, cacheSize, **kwds):
        """Open path using mode; set sensible values for rdcc_nbytes, rdcc_nslots, and rdcc_w0
        :param path of the file (str or Path)
        :param mode: open file mode;
            from hdf5 documentation:
                r	    Readonly, file must exist (default)
                r+	    Read/write, file must exist
                w	    Create file, truncate if exists
                x	    Create file, fail if exists
                a	    Read/write if exists, create otherwise
        :param cacheSize: size of ndf5 cache in bytes; sets rdcc_nbytes
        :return self
        """

        kwds.setdefault('rdcc_nbytes', cacheSize)
        kwds.setdefault('rdcc_nslots', 9973)  # large 'enough' prime number
        kwds.setdefault('rdcc_w0', 0.25)  # most-often will read
        self.fp = h5py.File(str(path), mode=mode, **kwds)

        self.path = path
        self.mode = mode
        self.cacheSize = cacheSize
        self.newFile = not mode.startswith('r')

        if self.newFile:
            self._initMetadata()
            self._saveMetadata()
        else:
            self._restoreMetadata()

        return self

    def _reopen(self):
        """Reopen the file as r+
        """
        # local import to avoid cycles
        from ccpn.core.lib.SpectrumDataSources.Hdf5SpectrumDataSource import Hdf5SpectrumDataSource
        self.close()
        _mode = Hdf5SpectrumDataSource.defaultAppendMode
        self.open(self.path, mode=_mode, cacheSize=self.cacheSize)

    def close(self):
        """Close the file
        """
        if self.fp is not None:
            self.fp.close()
            self.fp = None

    def _initMetadata(self, spectrumDataType=None):
        """Initialise self.metadata with default values, optionally setting the spectrum dataType
        """
        import uuid

        self.metadata.clear()
        self.metadata.update(_defaultNdf5MetadataDict)
        self.metadata[NDF5_UID_KEY] = str(uuid.uuid4())

        if spectrumDataType:
            self.addDataType(spectrumDataType)
            self.spectrumDataType = spectrumDataType

    def addDataType(self, dataType, dataKey=None) -> str:
        """Add dataType to the dict of available data
        Use dataKey or set to default value as defined in the _ndf5DataTypes dict
        :return the dataKey
        """
        if dataType not in _ndf5DataTypes:
            raise ValueError(f'Ndf5File.addDataType: invalid dataType {dataType!r}')
        if dataKey is None:
            dataKey = _ndf5DataTypes[dataType]
        self.dataTypes[dataType] = dataKey
        return dataKey

    def _updateVersion100(self):
        """Update pre 1.0.1 version to 1.1.0
        """
        # pre 1.0.1 version;
        _oldDataKey = 'spectrumData' # This is historic from the first implementation

        _params = self.fp[_oldDataKey].attrs
        if not 'version' in _params:
            raise RuntimeError('Hdf5Metadata._updateVersion100(): non-versioned metadata instance')

        _version = VersionString('1.0.0')  # it was a float in this implementation
        del _params['version']

        # we can now set the 1.1.0 ndf5 version
        self._initMetadata()
        self.metadata[NDF5_VERSION_KEY] = '1.1.0'

        self.addDataType(NDF5_DATATYPE_SPECTRUM_NDARRAY, _oldDataKey)
        self.spectrumDataType = NDF5_DATATYPE_SPECTRUM_NDARRAY

        # We are now upto version 1.1.0, as defined above
        _version = self.version
        return _version

    def _updateVersion101(self):
        """Update 1.0.1 version to 1.1.0
        """
        # 1.0.1 -> 1.1.0
        _version = VersionString(self.metadata[HDF5_VERSION_KEY])
        if not _version == '1.0.1':
            RuntimeError(f'Ndf5File._updateVersion101(): unknown version {_version}')

        # remap
        _oldDataKey = self.metadata[HDF5_DATASET_KEY]

        self._initMetadata()
        self.metadata[NDF5_VERSION_KEY] = '1.1.0'

        # # This works, but don't for now
        # # reopen the file as we are going to write the update info
        # _fp = self._reopenFile()
        # # the spectrum data; move to new location
        # _fp.create_group(NDF5_SPECTRUM)
        # _newDataKey = self.addDataType(NDF5_DATATYPE_SPECTRUM_NDARRAY)
        # _fp.move(_oldDataKey, _newDataKey)
        # self.spectrumDataType = NDF5_DATATYPE_SPECTRUM_NDARRAY
        # self.saveToNdf5()

        # instead, just leave it were it is for backward compatibility
        self.addDataType(NDF5_DATATYPE_SPECTRUM_NDARRAY, _oldDataKey)
        self.spectrumDataType = NDF5_DATATYPE_SPECTRUM_NDARRAY

        # We are now upto version 1.1.0, as defined above
        _version = self.version
        return _version

    def _updateMetadata(self):
        """Update the self to the latest version
        """
        if self.blockUpdate > 0:
            return

        self.blockUpdate += 1
        _version = None

        if self.fp is None:
            raise RuntimeError(f'Ndf5File._updateMetadata(): File is closed')

        if NDF5_VERSION_KEY in self.metadata:
            # we are already at 1.1.0 or higher
            _version = self.version

        elif not HDF5_VERSION_KEY in self.metadata and not NDF5_VERSION_KEY in self.metadata:
            # # pre 1.0.1 version;
            _version = self._updateVersion100()

        elif HDF5_VERSION_KEY in self.metadata and not NDF5_VERSION_KEY in self.metadata:
            # 1.0.1 -> 1.1.0
            _version = self._updateVersion101()

        else:
            raise RuntimeError('Ndf5File._updateMetadata(): non-versioned instance')

        # # Next update would go here
        # if _version == '1.1.0':
        #     pass

        if _version != NDF5_VERSION:
            raise RuntimeError(f'Ndf5File._updateMetadata(): updating failed; stuck at version {_version}')

        self.blockUpdate -= 1

    def _restoreMetadata(self):
        """Update self from the ndf5 file toplevel attributes
        """
        if self.fp is None:
            raise RuntimeError(f'Ndf5File._restoreMetadata(): File is closed')

        self.metadata.clear()

        _metadata = self.fp.attrs
        # the hdf5 _metadata object is unfortunately not a real dict;
        # Decode it from the earlier encoding
        for key, value in _metadata.items():
            self.metadata[key] = _decode(value)
        self._updateMetadata()

    def _saveMetadata(self):
        """Update the metadata to the hdf5 file toplevel attributes
        """
        if self.fp is None:
            raise RuntimeError(f'Ndf5File.saveMetadata(): File is closed')

        # the _metadata object is unfortunately not a real dict
        _metadata = self.fp.attrs

        # fist delete current values in the hdf5 file
        for key in list(_metadata):
            del _metadata[key]

        for key, value in self.metadata.items():
            # now copy the values from self
            try:
               _metadata[key] = _encode(value)
            except Exception as es:
                _txt = f'Ndf5File.saveMetadata(): error saving {key = } {value = }; {es}'
                getLogger().error(_txt)
                raise RuntimeError(_txt)

    def createSpectrumData(self, dimensionCount, pointCounts, dtype, sparse=False, compressionMode=None):
        """Create the ndf5 spectrum data ndarray at the location storage spectrumDataKey
        :param dimensionCount: number of dimensions.
        :param pointCounts: list/tuple of total points for each dimension.
        :param dtype: numpy dtype
        :param sparse: flag to set chunking to smaller (i.e. more sparse) blocks
        :param compressionMode: compression mode; defaults to None
        """
        dataSetKwds = {}
        dataSetKwds.setdefault('fillvalue', 0.0)

        if compressionMode is not None and compressionMode not in NDF5_COMPRESSION_MODES:
            raise ValueError(f'Ndf5File.createSpectrumdata(): invalid {compressionMode = }; should be None or one of {NDF5_COMPRESSION_MODES}')
        self.compressionMode = compressionMode
        if self.compressionMode is not None:
            dataSetKwds.setdefault('compression', self.compressionMode)
            dataSetKwds.setdefault('fletcher32', False)
        else:
            dataSetKwds.setdefault('fletcher32', True)

        if sparse:
            # sparse data have smaller, explicitly set chunk's
            _chunkSizes = {
                1 : [64],
                2 : [32]*2,
                3 : [8]*3,
                4 : [8]*4,
                5 : [4]*5,
                6 : [4]*6,
                7 : [4]*7,
                8 : [4]*8,
            }
            _chunks = tuple(_chunkSizes.get(dimensionCount, [4]*dimensionCount))
            dataSetKwds.setdefault('chunks', _chunks)
        else:
            # Setting chucks to True amounts to h5py sorting the optimal settings
            dataSetKwds.setdefault('chunks', True)

        # we are storing a spectrum data ndarray
        # addDataType method returns the dataKey under which we store the ndarray in the file;
        _dataKey = self.addDataType(NDF5_DATATYPE_SPECTRUM_NDARRAY)
        self.spectrumDataType = NDF5_DATATYPE_SPECTRUM_NDARRAY

        self.fp.create_dataset(_dataKey,
                               shape=pointCounts[::-1],  # data are organised numpy style z, y, x
                               dtype=dtype,
                               track_times=False,  # to assure same hash after opening/storing
                               **dataSetKwds
                               )

        # need to update the metadata as we have added info
        self._saveMetadata()

#--------------------------------------------------------------------------------------------------
# Encoding of metadata and parameters; the h5py attributes can't handle None's nor dicts

_NONE_STR = '__NONE__'

# define some tags to denote a dict, xml-style
_DICT = '<__DICT__>'
_DICT_END = '</__DICT__>'

def _encode(value):
    """Encode value for None; process and recurse into any tuple or list or dicts
    """
    if value is None:
        result = _NONE_STR

    elif isinstance(value, dict):
        # hdf5 attributes do not do dict's;
        # tried numpy object_: no avail; i.e. result = np.array(value.items())
        # tried arrays of tuples; no avail
        # now: Encoded as a list of _DICT, n-times key, val, _DICT_END
        result = [_DICT]
        for key, val in value.items():
            result.append(key)
            result.append(_encode(val))
        result.append(_DICT_END)

    elif isinstance(value, (tuple, list)):
        result = [_encode(val) for val in value]

    else:
        result = value

    return result


def _decode(value):
    """Decode value for None; process and recurse into any tuple, list or dicts
    """

    # the special case dict need to be first in the checks
    if isinstance(value, (np.ndarray,)) and len(value)>= 2 \
            and value[0] == _DICT and value[-1] == _DICT_END:
        # Encoded as a list of list of _DICT, n-times key, val, _ICT_END
        result = {}
        ii = 1
        while ii < len(value) and value[ii] != _DICT_END:
            key = value[ii]
            val = _decode(value[ii+1])
            result[key] = val
            ii += 2

    elif isinstance(value, (np.ndarray,)):
        result = [_decode(val) for val in value]

    elif isinstance(value, np.bytes_):
        #  string values were previously (1.0.1) encoded as bytes
        result = _decode(value.decode('utf8'))  # calling decode again to change any _NONE_STR instances

    elif value == _NONE_STR:
        result = None

    else:
        result = value

    return result

