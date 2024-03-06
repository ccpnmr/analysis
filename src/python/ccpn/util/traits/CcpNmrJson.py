"""
CcpNmrJson(TraitBase):

    Abstract base class to handle an object with traits and to- and fromJson methods for storing
    and retrieving

    --------------------------------------------------------------------------------------------
     Define attributes (traits) as traitlets instances (Import from util/traits/CcpNmrTraits).


     All traits can be saved by default setting the class attribute saveAllTraitsToJson to True
     (default is False):
        Example:   saveAllTraitsToJson = True

     Traits to be explicitly saved or not save to json are tagged saveToJson=True/False. This
     overrides the effect of the saveAllTraitsToJson class attribute for the trait:
         Example:  myint = Int().tag(saveToJson=True)


     Trait handlers are defined by hiarachy:

     1) Traits can use jsonHandler tag key to define a specific jsonHandler class (typically defined
     outside the class) or use the jsonHandler(trait) decorator (typically inside a class definition).
         Example:
                   myint = Int().tag(saveToJson=True, jsonHandler=myHandler)  # myHandler defined elsewhere

         or
                   myint = Int().tag(saveToJson=True)

                   @jsonHandler(myint)
                   class myHandler(object):   #myHandler defined inside the class
                        ....

     2) A (custom) traitlet class can have a traitlet-specific jsonHandler class defined inside its class
     definition (see Adict for example).

     # GWV 5/10/23: disabled as not usefull and gives too much headache
     # 3) A TraitBase class can have a jsonHandler, which it would use for all traits. NB assure that the handler
     # can deal with all trait types defined in the class

     4) The default handler defined for all traits does nothing, json decoders are assumed be able to handle it.


     A jsonHandler class must derive from TraitJsonHandlerBase / DictTraitJsonHandleABC / ListTraitJsonHandlerABC
     and can subclass the following methods:

         encode(self, value) which returns a json serialisable python object
         decode(self, value) which uses value (a python object) to generate the new (or modified) obj

     For handlers of container objects (list, dict, tuple, set, ...) inheriting from DictTraitJsonHandleABC /
     ListTraitJsonHandlerABC:
         encodeItem(self, value) which returns a json serialisable python object for an item of a container
                                 object
         decodeItem(self, value) which uses value (a python object) to generate the new item of a container
                                 object

         An jsonHandler instance has two attributes:
            self.obj : The object which trait is being decoded/encoded
            self.trait : The Trait instance; use Trait.name and other usefull attributes

     Example:

         class myHandler(TraitJsonHandlerBase):
               def encode(self, value):
                   "returns a json serialisable object"
                   -- some action on value; optionally use self.obj, self.trait --
                   return value

               def decode(self, value):
                   "uses value to generate and set the new (or modified) obj"
                   newValue =  --- some action using value; optionally use self.obj, self.trait ---
                   return newValue

     Any CcpNmrJson-derived class maintains metadata. Use the setJsonMetadata(), getJsonMetadata()
     and hasJsonMetadata() methods to access

     NB: Need to register the class for proper restoring from the json data; best use the register
     decorator
     Example:
        from ccpn.util.traits.CcpNmrJson import CcpNmrJson, register

         @register()
         class MyClass(CcpNmrJson):

            .. traits
            .. methods

         #end class

    --------------------------------------------------------------------------------------------

    JSON file for storage:

    version 3.0: list of (key, encoded-value) tuples; first (key, encoded-value) pair is _metadata

    version 3.1.0: dict with four keys


    _ccpNmrJson: the CcpNmrJson identifier
    _objectdata: dict with CLASSNAME, CLASSVERSION, CLASSINFO, OBJECT_UID keys
    _metadata: dict with USER, LASTPATH, TIMESTAMP (+ optional others)
    _data: a dict of (taitName, encoded-value) pairs

    --------------------------------------------------------------------------------------------

    Class initialisation / restore methods and hiarchies

    - obj:
        obj.fromJson(string)
            string -> JSON -> theDict
            return ._decode(theDict)

    - Static
        _newInstanceFromDict(theDict)
            theDict -> class
            obj = class()
            return obj._decode(theDict)

        newObjectFromJson(string, path)
            (string or path) -> JSON -> theDict
            theDict -> class
            obj = class()
            return obj._decode(theDict)

"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
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
__dateModified__ = "$dateModified: 2024-03-06 17:48:14 +0000 (Wed, March 06, 2024) $"
__version__ = "$Revision: 3.2.2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2018-05-14 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from contextlib import contextmanager

import json
from collections import OrderedDict
import getpass

class CcpNmrJsonError(RuntimeError):
    """A class to bail out of Json recursion
    """
    pass

from ccpn.util.decorators import singleton
from ccpn.util.Path import aPath, Path
from ccpn.util.AttributeDict import AttributeDict
from ccpn.util.traits.TraitBase import TraitBase
from ccpn.util.traits.TraitJsonHandlerBase import TraitJsonHandlerBase
from ccpn.util.traits.CcpNmrTraits import default, Dict, CString, Bool, Unicode
from ccpn.util.Logging import getLogger
from ccpn.util.Time import now
from ccpn.util.decorators import debug2Enter, debug3Enter, debug3Leave  # Not used now to avoid circular import

from ccpn.framework.Version import VersionString

class Constants(object):
    # jsonHandlers
    JSONHANDLER = 'jsonHandler'
    RECURSION = 'recursion'

    # file handler routines
    FILEHANDLERS = '_fileHandlers'

    # update handler routines
    UPDATEHANDLERS = '_updateHandlers'

    # the json keys:  _objectData, _metadata, _data
    CCPNMRJSON = '_ccpNmrJson'
    OBJECT_UID = '_json_uid'
    OBJECTDATA = '_objectdata'
    METADATA = '_metadata'
    DATA = '_data'
    JSON_KEYS = [CCPNMRJSON, OBJECT_UID, OBJECTDATA, METADATA, DATA]

    # used in _objectdata dict
    CLASSNAME = 'className'
    CLASSVERSION = 'classVersion'
    CLASSINFO = 'classInfo'

    # used in _metadata dict
    JSONVERSION = 'jsonVersion'  # 3.0 def
    USER = 'user'
    LASTPATH = 'lastPath'
    TIMESTAMP = 'timestamp'
    # 'reserved' metadata keys; some for backward 3.0 compatibility
    METADATA_KEYS = (JSONVERSION, USER, LASTPATH, TIMESTAMP, OBJECT_UID)
# end class


def jsonHandler(trait):
    """decorator for defining a json handler class on a trait
    """
    def theDecorator(cls):
        trait.tag(jsonHandler=cls)
        return cls
    return theDecorator


def register(overwrite=False):
    """A decorator to register the class
    """
    def theDecorator(cls):
        cls.register(overwrite=overwrite)
        return cls
    return theDecorator


class _GenericFileHandler(object):
    """Saves/restores obj to file with extension using toString and fromString methods of obj
    """

    def __init__(self, extension, cls, toString, fromString):
        """ Intialise with the info
        """
        self.cls = cls
        self.extension = extension

        if not hasattr(cls, toString):
            raise AttributeError('invalid toString method "%s" for object "%s"' % (toString, cls))
        self.toString = getattr(cls, toString)

        if not hasattr(cls, fromString):
            raise AttributeError('invalid fromString method "%s" for object "%s"' % (fromString, cls))
        self.fromString = getattr(cls, fromString)

    # @debug2Enter()
    def save(self, obj, path, **kwds):
        """Saves obj to path
        """
        path = aPath(path)
        if not path.suffix == self.extension:
            # this should not happen
            raise ValueError('invalid path "%s"; does not match extension "%s"' % (path, self.extension))

        path.write_text(self.toString(obj, **kwds))

    # @debug2Enter()
    def restore(self, obj, path, **kwds):
        """Restores obj from path, returns obj
        """
        path = aPath(path)
        if not path.suffix == self.extension:
            # this should not happen
            raise ValueError('invalid path "%s"; does not match extension "%s"' % (path, self.extension))

        self.fromString(obj, path.read_text(), **kwds)
        return obj
# end class


def fileHandler(extension, toString, fromString):
    """Decorator to define toString, fromString methods for a file with extension.
    It defines the _fileHandler dict for the class, used to store the various fileHandlers
    (for each extension type).
    """

    def theDecorator(cls):
        """This function will decorate cls with fileHandler dict and save and restore routines
        """
        # assure that the fileHandlers can be stored; doing it this way assures each class (when sub-classing) has
        # its own version
        if not hasattr(cls, Constants.FILEHANDLERS):
            setattr(cls, Constants.FILEHANDLERS, {})
        handlers = getattr(cls, Constants.FILEHANDLERS)
        # add the handler
        handlers[extension] = _GenericFileHandler(extension=extension, cls=cls,
                                                  toString=toString, fromString=fromString)

        return cls

    return theDecorator


def update(updateHandler, push=False):
    """Decorator to register updateHandler function
    It defines the _updateHandlers list for the class.

    :param updateHandler: a function to update the dataDict with profile:
    
                updateHandler(obj, dataDict) -> dataDict
                    obj: object that is being restored
                    dataDict: original dict with (attribute, value) pairs
                    returns: dataDict consistent with obj

    :param push: push to the front of the _updateHandlersList (i.e executed first)
    """

    def theDecorator(cls):
        """This function will decorate cls with _update, _updateHandler list and registers the updateHandler
        """
        # assure that the update handlers can be stored; doing it here assures that every class has its own
        # updateHandlers list
        if not hasattr(cls, Constants.UPDATEHANDLERS):
            setattr(cls, Constants.UPDATEHANDLERS, [])
        handlers = getattr(cls, Constants.UPDATEHANDLERS)
        # add the handler
        indx = 0 if push else len(handlers)
        handlers.insert(indx, updateHandler)

        return cls

    return theDecorator

#--------------------------------------------------------------------------------------------
# Dummy's to test
#--------------------------------------------------------------------------------------------
#
# def _updateJson_1_0(obj, dataDict):
#     "dummy to try"
#
#     if not Constants.METADATA in dataDict:
#         # invalid file without metadata
#         raise RuntimeError('No metadata dict')
#
#     version = dataDict[Constants.METADATA][Constants.JSONVERSION]
#     if version > 1.0:
#         print('>>> skipping _upgradeJson_1.0 (%s)' % obj.__class__.__name__)
#         return dataDict
#     print('>>> upgrading version %s to 2.0 (%s)' % (version, obj.__class__.__name__))
#     dataDict[Constants.METADATA][Constants.JSONVERSION] = 2.0
#     return dataDict
#
#
# def _updateJson_2_0(obj, dataDict):
#     "dummy to try"
#     if not Constants.METADATA in dataDict:
#         # invalid file without metadata
#         raise RuntimeError('No metadata dict')
#
#     version = dataDict[Constants.METADATA][Constants.JSONVERSION]
#     if version > 2.0:
#         print('>>> skipping _upgradeJson_1.0 (%s)' % obj.__class__.__name__)
#         return dataDict
#     print('>>> upgrading version %s to 2.0 (%s)' % (version, obj.__class__.__name__))
#     dataDict[Constants.METADATA][Constants.JSONVERSION] = 3.0
#     return dataDict


# decorate the class
#@update(_updateJson_2_0)
#@update(_updateJson_1_0)
#--------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------
# Some info regarding the call hiarchy on restoring
#
# restore(path)
#   from json(string) -> data
#   dataDict = _update_3_1(data)
#   dataDict = _update(dataDict)
#   _decode(dataDict)
#       for key,value in dataDict.items():
#           _getJsonHandler(key) -> handler(obj, trait)
#           newValue = handler.decode(value)  # Also handles optional recursion
#           setTraitValue(key, newValue)
#   return obj
#
#--------------------------------------------------------------------------------------------



@fileHandler('.json', 'toJson', 'fromJson')
class CcpNmrJson(TraitBase):
    """
    Abstract base class to handle an object with traits and to- and fromJson methods for storing
    and retrieving (see module doc)
    """
    # From HasTraits; keeping keys in order
    keysInOrder = True   # If True, return key in order defined by _traitOrder attribute
                         # of the keys; can be put at end by traitAtEnd tag

    #--------------------------------------------------------------------------------------------
    # to be subclassed
    #--------------------------------------------------------------------------------------------

    saveAllTraitsToJson = False  # This flag effectively sets saveToJson to True/False for all traits
    classVersion = '1.0.0'  # The version identifier for the specific class (useful when upgrading is required)
    classInfo = None  # Any information about the class

    _encodeAsJson_3_0 = False  # Encode object in json 3.0 format; for backward compatibility
                               # (e.g. DataStore, ProjectHistory). This way, older program versions can restore

    initDefaults = {}  # Any arguments given to class instantiation when restoring

    #--------------------------------------------------------------------------------------------
    # end to be subclassed
    #--------------------------------------------------------------------------------------------

    # jsonVersion: 'A version id to track any changes to the JSON implementation'
    _jsonVersion = VersionString('3.1.0')

    #--------------------------------------------------------------------------------------------
    # # _metadata: should be in-sinc with Constants.METADATA
    _metadata = Dict(default_value={}, allow_none=True).tag(saveToJson=True, info='The metadata of the class')

    #--------------------------------------------------------------------------------------------

    _registeredClasses = {}  # A dict that contains the (className, class) mappings for restoring
                             # CcpNmrJson (sub-)classes from json files

    #--------------------------------------------------------------------------------------------
    @staticmethod
    def isRegistered(className):
        """Return True if className is registered"""
        return className in CcpNmrJson._registeredClasses

    @classmethod
    def register(cls, overwrite=False):
        """Register the class
        :parameter overwrite: allow for a second call to register to overwrite;
                              usefull for e.g. testing macro's
        """
        className = cls.__name__
        if cls.isRegistered(className) and not overwrite:
            raise RuntimeError('className "%s" is already registered' % className)
        CcpNmrJson._registeredClasses[className] = cls

    #--------------------------------------------------------------------------------------------
    # Code used for saving / restoring
    #--------------------------------------------------------------------------------------------
    # Class Dict to track encoded/decoded objects
    _objectDict = {}

    # Class (global) counter to indicate that the object is being restored;
    # maintained by _setRestoring
    _isRestoring = 0

    _errorStack = []

    @property
    def isRestoring(self) -> bool:
        """flag to indicate if restoring, i.e. decoding, is in progress
        """
        return CcpNmrJson._isRestoring > 0

    @classmethod
    def _setRestoring(cls, flag):
        """Class method to set the restoring on/off
        If flag == True: initialise _objectDict to {} if _isRestoring=0; _isRestoring += 1
        If flag == False: _isRestoring -= 1; reset _objectDict to {} if _isRestoring=0
        """
        if flag:
            if CcpNmrJson._isRestoring == 0:
                CcpNmrJson._objectDict = {}
                CcpNmrJson._errorStack = []

            CcpNmrJson._isRestoring += 1
        else:
            CcpNmrJson._isRestoring -= 1
            if CcpNmrJson._isRestoring < 0:
                raise RuntimeError(f'_setRestoring(): global restoring flag < 0; this should not happen!')
            if CcpNmrJson._isRestoring == 0:
                CcpNmrJson._errorStack = []

    @contextmanager
    def _doProcessJson(self, action=''):
        """Context method for restoring / saving.

        with obj._doRestoreJson() as _objectDict:

            actions; e.g. checking if obj already present
            if obj.isRestoring:
                ....

        :parameter action: e.g. 'encoding', 'decoding', 'importing' (for context only)
        :yields _objectDict
        """
        CcpNmrJson._setRestoring(True)
        _error = None
        try:
            yield CcpNmrJson._objectDict

        except Exception as es:
            _isRestoring = CcpNmrJson._isRestoring
            # print(f'Exception level: {_isRestoring}')
            _error = f'While {action} {self}: {es}'
            CcpNmrJson._errorStack.append(_error)
            if _isRestoring == 1:
                # We are at the starting restore level
                _error = CcpNmrJson._errorStack[0]
                getLogger().debug(f'_doProcessJson() {action}: caught exception: {_error}')
                CcpNmrJson._setRestoring(False)
                raise RuntimeError(_error)
            else:
                CcpNmrJson._setRestoring(False)
                raise es

        CcpNmrJson._setRestoring(False)


    def _getJsonUid(self) -> str:
        """Generate a UID for the object;
        currently a Hex representation of id as string
        :return uid-string
        #CCPNINTERNAL: subclassed in Tree-derived classes
        """
        return str(hex(id(self)))

    def _getObjectDataDict(self):
        """":return a dict with the object data, saved as JSON key OBJECTDATA
        """
        result = {}
        result[Constants.CLASSNAME] = self.__class__.__name__
        result[Constants.CLASSVERSION] = self.classVersion
        if self.classInfo is not None:
            result[Constants.CLASSINFO] = self.classInfo
        return result

    #--------------------------------------------------------------------------------------------

    @staticmethod
    def _getClassFromDict(theDict):
        """Return the class as defined in the objectdata that should be in theDict
        """
        if (_objectdata := theDict.get(Constants.OBJECTDATA)) is None:
            raise ValueError(f'theDict does not contain any {Constants.OBJECTDATA}')

        if not isinstance(_objectdata, dict):
            # This should really never happen, but while developing it occured
            raise RuntimeError(f'An error occured getting _objectdata; got {_objectdata}')

        if (className := _objectdata.get(Constants.CLASSNAME)) is None:
            raise ValueError(f'{Constants.OBJECTDATA} does not contain the classname of a CcpNmrJson (sub-)type')

        if (cls := CcpNmrJson._registeredClasses.get(className, None)) is None:
            raise RuntimeError(f'Unregistered class "{className}"; Cannot decode the data in theDict')

        return cls

    @classmethod
    def _isEncodedObject(cls, theData):
        """Return True if theList defines an encoded CcpNmr object.
        To establish this, we look at the structure of either 3.0 or 3.1.0 data

        CCPNINTERNAL: used in TraitJsonHandlerBase
        """
        # We should have a list or dict, if not it was something else
        # This can happen, as the method is called by jsonHandlers, to check if we have an encoded object
        if isinstance(theData, list):
            # this could be 3.0 encoded object; check that there is at least one (key, value) tuple
            # and check that the key is METADATA
            if len(theData) >= 1 and \
               len(theData[0]) == 2 and \
               theData[0][0] == Constants.METADATA:
                return True
            else:
                return False

        elif isinstance(theData, dict):
            # This could be a 3.1.0 encoded object; needs to be a dict with all JSON_KEYS and have CCPNMRJSON key
            if len(theData) == len(Constants.JSON_KEYS) and Constants.CCPNMRJSON in theData:
                return True
            else:
                return False

        else:
            # not a list or dict
            return False

    @classmethod
    def _newObject(cls, **kwds):
        """:return a new instance of cls
        """
        _kwds = cls.initDefaults.copy()
        _kwds.update(kwds)
        obj = cls(**_kwds)
        return obj

    @staticmethod
    def _newObjectFromDict(theData, **kwds):
        """Return new object as defined by theData;
        kwds are passed to the class instantiation
        CCPNMRINTERNAL: used in recursive handler classes (see below)
        """
        theDict = CcpNmrJson._updateToJson3_1_0(theData)

        if not Constants.OBJECT_UID in theDict:
            raise RuntimeError(f'_newObjectFromDict(): unable to get {Constants.OBJECT_UID} from theData')
        _uid = theDict[Constants.OBJECT_UID]

        # check the _uid; can be None because of 3.0 encoding!
        if _uid is not None and _uid in CcpNmrJson._objectDict:
            # we have encountered an obj that already was decoded;
            # get it and return
            return CcpNmrJson._objectDict[_uid]

        # we need create this object and update theDict
        cls = CcpNmrJson._getClassFromDict(theDict)
        theDict = cls._update(cls, theDict)
        obj = cls._newObject(**kwds)

        # decoding might return an existing obj;
        obj = obj._decode(theDict)
        return obj

    @staticmethod
    def newObjectFromJson(path=None, jsonString=None, **kwds):
        """Create a new object defined by either the:
        - json-file path; reading the jsonString or
        - jsonString
        The jsonString should be a json encoded dict with valid metadata needed for restoring the objects
        kwds are passed to the class instantiation of the object

        :return the object restored from the Json data
        """
        if path is not None:
            path = aPath(path)
            if not path.exists():
                raise FileNotFoundError('file "%s" does not exist' % path)

            with path.open('r') as fp:
                theData =  json.load(fp)

        elif jsonString is not None:
            theData = json.loads(jsonString)

        else:
            raise RuntimeError('newObjectFromJson: undefined path and jsonString')

        obj = CcpNmrJson._newObjectFromDict(theData, **kwds)

        return obj

    #--------------------------------------------------------------------------------------------

    def setJsonMetadata(self, key, value, force=False):
        """Update Json metadata with kwds (key,value) pairs;
        guard for any json-related keys that should not be changed this way
        :param key: the key of the metadata to be updated
        :param value: the value of the metadata to be updated; must be json serialisable
        """
        if key in Constants.METADATA_KEYS and not force:
            raise ValueError('setJsonMetadata: Attempted to set protected metadata key "%s" on object %s' %
                             (key, self))
        try:
            _tmp = json.dumps(value)
        except Exception:
            raise ValueError('setJsonMetadata: Attempted to set metadata key "%s" on object %s '
                             'to non Json-serialisable value %r' % (key, self, value))
        # for debugging
        # if key == Constants.USER:
        #     pass
        self._metadata[key] = value

    def getJsonMetadata(self, key, default=None):
        """Return the value for key.
        :parameter key: key defining the value to get
        :parameter default: default value to return if key is not present
        :return value for key from metadata
        """
        return self._metadata.get(key, default)

    def hasJsonMetadata(self, key) -> bool:
        """Return: True if metadata has key
        """
        return key in self._metadata

    #--------------------------------------------------------------------------------------------

    def keys(self, **metadata) -> list:
        """Return the keys; excluding the json.METADATA trait;
        Optionally filter for trait metadata;
        NB these are different from the json METADATA. The latter store the information regarding the user, path, etc of the json representation
           of the object.
        Key order is determined by keysInOrder attribute and optional traitAtEnd tag settings.
        :return The keys as a list
        """
        keys = [key for key in super().keys(**metadata) if key != Constants.METADATA]
        return keys

    #--------------------------------------------------------------------------------------------

    def __init__(self, **metadata):
        super().__init__()
        setattr(self, Constants.METADATA, {})
        for key, value in metadata.items():
            # This affords the necesary safeguarding against accidentially overwriting
            # any protected keys; also checks for JSON serialisation
            self.setJsonMetadata(key=key, value=value)

    #--------------------------------------------------------------------------------------------

    def duplicate(self, **metadata):
        """Convenience method to return a duplicate of self, using
        json serialisation with trait jsonHandlers to assure 'deepcopy' behavior

        Method will fail if attributes cannot be serialised; e.g. an Any trait set to a non-serialisable
        object.
        Method will fail if there are any unregistered CcpNmrJson objects

        :parameter metadata: optional keyword=value pairs to update in the json metadata
        :returns a duplicate of self
        """
        _encoded = self._encode(encodeAllTraits=True)

        _json = json.dumps(_encoded)
        # effectively make a copy by loading the json string
        _encodedDuplicate = json.loads(_json)

        duplicate = self._newObjectFromDict(_encodedDuplicate, **metadata)

        return duplicate

    #--------------------------------------------------------------------------------------------

    # @debug3Enter()
    # @debug3Leave()
    def _getTraitJsonHandler(self, traitName):
        """just a helper function to get a json handler instance from trait traitName
        Checks (via trait.getJsonHandler call):
        - metadata trait for specific jsonHandler,
        - or subsequently check for one of the trait class.

        :return handler instance
        :raises RuntimeError if no handler can be found
        """
        traitObj = self.getTraitObject(traitName)
        return traitObj.getJsonHandler(self)

    def toJson(self, **kwds):
        """Encode self represented in a json string
        :return The encoded json string
        :raises RuntimeError
        """
        indent = kwds.setdefault('indent', 2)
        dataList = self._encode()

        try:
            # Convert to JSON
            _json = json.dumps(dataList, indent=indent)
        except Exception as es:
            # GWV: Log this, as the error might be caught elsewhere
            getLogger().debug(f'toJson(): while converting data to JSON an exception was raised: {es}')
            raise RuntimeError(f'While encoding {self} as JSON: {es}')

        return _json

    def _saveTraitToJson(self, traitName) -> bool:
        """Determine if trait traitName should be saved to json, depending on settings
        :return True/False
        """
        # Subtle but important implementation change relative to the earlier one:
        # Allow trait-specific saveToJson metadata (i.e. 'tag'), to override object's saveAllToJson

        # check if saveToJson was defined for this trait; use None as default as the tag can be True/False
        _saveTraitToJson = self.trait_metadata(traitname=traitName, key='saveToJson', default=None)
        # if saveToJson was not defined for this trait, check saveAllToJson flag
        if _saveTraitToJson is None:
            # We didn't obtain a result; check the global saveAllTraitsToJson flag
            _saveTraitToJson = True if self.saveAllTraitsToJson else False

        return _saveTraitToJson

    def _encodeTrait(self, traitName):
        """Encode trait traitName
        :return (traitName, encoded-value) tuple
        """
        value = self.getTraitValue(traitName)
        # Do not try to encode None's
        if value is not None:
            handler = self._getTraitJsonHandler(traitName)
            value = handler.encode(value)
        return (traitName, value)

    def _encode(self, encodeAllTraits=False):
        """
        :parameter encodeAllTraits: flag to encode all traits, rather than than only the saveToJson
                                    defined ones; used by duplicate()
        :return self as 3.1.0 encoded dict
        """
        if self._encodeAsJson_3_0:
            return self._encode_3_0()

        with self._doProcessJson(action='encoding') as _objectDict:
            _uid = self._getJsonUid()
            if _uid in _objectDict:
                # The data for this object have already been encoded; No need to do it again
                # create the the encodedData dict;
                # set OBJECT_UID to the _uid and objectdata, metdadata and data to None.
                _encodedData = {}
                _encodedData[Constants.CCPNMRJSON] = self._jsonVersion
                _encodedData[Constants.OBJECT_UID] = _uid
                _encodedData[Constants.OBJECTDATA] = None
                _encodedData[Constants.METADATA] = None
                _encodedData[Constants.DATA] = None

            else:
                # Store the object-id for reference usage; need to do this here at the top,
                # as handling of traits might recurse and encounter self again.
                _objectDict[_uid] = self

                # encode the metadata
                _tmp, _metadata = self._encodeTrait(Constants.METADATA)

                # get all traits that need saving to json
                if encodeAllTraits:
                    # used for duplicate()
                    traitsToEncode = list(self.keys())
                else:
                    traitsToEncode = [traitName for traitName in self.keys() if self._saveTraitToJson(traitName)]

                # create a dict of (traitName, value) pairs for the trait data
                _data = dict(self._encodeTrait(traitName) for traitName in traitsToEncode)

                # create the the encodedData dict
                _encodedData = {}
                _encodedData[Constants.CCPNMRJSON] = self._jsonVersion
                _encodedData[Constants.OBJECT_UID] = _uid
                _encodedData[Constants.OBJECTDATA] = self._getObjectDataDict()
                _encodedData[Constants.METADATA] = _metadata
                _encodedData[Constants.DATA] = _data

        return _encodedData

    def _encode_3_0(self):
        """
        :return self as 3.0 encoded dict to maintain compatiblity with earlier versions;
        i.e. allowing those versions to read it and determine save-version
        """
        with self._doProcessJson(action='encoding-3.0') as _objectDict:
            _uid = self._getJsonUid()
            if _uid in _objectDict:
                raise RuntimeError(f'encode_3_0(): object can only be encoded once in JSON 3.0')
            _objectDict[_uid] = self

            # 3.0: store _objectdata in the _metadata dict
            _objectdata = self._getObjectDataDict()
            for key, value in _objectdata.items():
                self.setJsonMetadata(key, value, force=True)
            self.setJsonMetadata(Constants.JSONVERSION, 3.0, force=True)
            self.setJsonMetadata(Constants.OBJECT_UID, _uid, force=True)

            # Encode 3.0 style; i.e. a list of (traitName, encoded-value) tuples
            traitsToEncode = [Constants.METADATA] + [traitName for traitName in self.keys() if self._saveTraitToJson(traitName)]
            _encodedData = [self._encodeTrait(traitName) for traitName in traitsToEncode]

        return _encodedData

    def fromJson(self, string):
        """Populate/update self with data from json string; a list of (trait, value) tuples 
        Return self
        """
        if len(string) == 0:
            getLogger().warning('%s.fromJson: empty string, retaining default values' % self.__class__.__name__)
            return self

        try:
            data = json.loads(string)
        except json.JSONDecodeError as es:
            txt = f'{self.__class__.__name__}.fromJson: error while decoding: {es}'
            getLogger().warning(txt)
            raise RuntimeError(txt)

        # check for updates
        try:
            dataDict = self._updateToJson3_1_0(data)
            dataDict = self._update(dataDict)
        except Exception as es:
            getLogger().debug(f'updating from JSON raised errror: {es}')
            getLogger().warning(f'{self.__class__.__name__}.fromJson: error updating data from JSON, retaining default values')
            return self

        # at this point, we expect dataDict to be compatible with the data structure of the object
        if (_className := dataDict.get(Constants.OBJECTDATA).get(Constants.CLASSNAME)) != self.__class__.__name__:
            raise RuntimeError(
                f'trying to restore from JSON encoded class {_className} incompatible with class {self.__class__.__name__}'
            )

        with self._doProcessJson(action='decoding'):
            self._decode(dataDict)
        return self

    def _decodeTrait(self, traitName, theDict):
        """Helper function to decode a single trait
        """
        # update the trait with value from theDict after optional decoding
        try:
            value = theDict.get(traitName)
            # Do not decode None's
            if value is not None:
                handler = self._getTraitJsonHandler(traitName)
                value = handler.decode(value)
            self.setTraitValue(traitName, value, force=True)

        except Exception as es:
            _error = f'While decoding {self} trait "{traitName}": {es}'
            CcpNmrJson._errorStack.append(_error)
            raise es

    def _decode(self, dataDict):
        """Populate/update self with data from dataDict
        :return Updated self or referenced object
        """
        _className = self.__class__.__name__

        if not isinstance(dataDict, dict):
            raise RuntimeError(f'decode(): invalid dataDict; got {dataDict}')

        with self._doProcessJson(action='decoding') as _objectDict:
            # NB errors are logged by the context manager

            if not Constants.OBJECT_UID in dataDict:
                raise RuntimeError(f'{_className}._decode(): unable to get {Constants.OBJECT_UID} from dataDict')
            _uid = dataDict[Constants.OBJECT_UID]
            # fix _uid if it was None (which happens if dataDict was upgraded from 3.0 encoding)
            if _uid is None:
                _uid = self._getJsonUid()
                dataDict[Constants.OBJECT_UID] = _uid

            # check if encountered the _uid before
            if _uid in _objectDict:
                # we have encountered an obj that already was decoded;
                # get it and return
                return _objectDict[_uid]

            # We need to decode;

            # Store the object-id for future reference usage;
            # need to do this here, as handling of traits might recurse and then need to skip self.
            _objectDict[_uid] = self

            # check the presence of object data
            if (_objectdata := dataDict.get(Constants.OBJECTDATA), None) is None:
                raise RuntimeError(f'{_className}._decode(): unable to get {Constants.OBJECTDATA} from dataDict')

            # check the presence of metadata
            if (_metadata := dataDict.get(Constants.METADATA), None) is None:
                raise RuntimeError(f'{_className}._decode(): unable to get {Constants.METADATA} from dataDict')
            # decode the metadata
            self._decodeTrait(Constants.METADATA, dataDict)

            # Get the data encoding the traits
            if (_data := dataDict.get(Constants.DATA), None) is None:
                raise RuntimeError(f'{_className}._decode(): unable to get {Constants.DATA} from dataDict')

            # Handle the data; Update currently defined traits
            # Handle without any notifications; values should be correct
            with self.traitNotificationBlanking():
                for traitName in self.keys():
                    if traitName in _data:
                        self._decodeTrait(traitName, _data)

        return self

    #--------------------------------------------------------------------------------------------
    @classmethod
    def _updateToJson3_1_0(cls, theData) -> dict:
        """
        Update the data from 3.0 to json 3.1.0 defs
        :return: theData as an updated dict
        """
        if isinstance(theData, dict) \
            and (jsonVersion := theData.get(Constants.CCPNMRJSON)) is not None \
            and jsonVersion >= '3.1.0':
            # 3.1.0 No change: return unaltered
            return theData

        if isinstance(theData, dict) and (_metaData := theData.get('_metadata')) is not None:
            _metaData['jsonVersion'] = 3.0
            # reverted to 3.0 list of tuples for Luca's resource's files
            theData = list(theData.items())

        if isinstance(theData, list):
            _itemLengths = [len(item)!=2 for item in theData]
            if any(_itemLengths):
                raise RuntimeError(f'Updating from JSON 3.0: data invalid, expected list of (key, value) tuples')
            if len(theData) == 0:
                raise RuntimeError(f'Updating from JSON 3.0: data invalid, expected {Constants.METADATA}')

            _metaData = theData[0][1]

            # jsonversion
            if (_jsonVersion := _metaData.get(Constants.JSONVERSION, None)) is None:
                raise RuntimeError(f'No {Constants.JSONVERSION}: The data do not represent a valid JSON encoded 3.0 object')
            if isinstance(_jsonVersion, int):
                _jsonVersion = float(_jsonVersion)
            # Should now be json 3.0 float
            if not isinstance(_jsonVersion, float) or _jsonVersion != 3.0:
                raise RuntimeError(f'Updating from JSON 3.0: Undefined JSON version {_jsonVersion}')
            del(_metaData[Constants.JSONVERSION])

            # Not all 3.0 have a _uid; i.e. they do now if generated later for backward
            # compatibility, but not if originating from previous code
            if Constants.OBJECT_UID in _metaData:
                _uid = _metaData[Constants.OBJECT_UID]
                del _metaData[Constants.OBJECT_UID]
            else:
                # cannot generate now, as this is a classmethod; i.e. we do not have a object yet
                # Set to None, so it is done later
                _uid = None

            _objectdata = {}
            _objectdata[Constants.CLASSNAME] = _metaData.get(Constants.CLASSNAME)
            del(_metaData[Constants.CLASSNAME])

            _classVersion = _metaData.get(Constants.CLASSVERSION, None)
            if isinstance(_classVersion, str):
                # A string, we should be good
                _objectdata[Constants.CLASSVERSION] = _classVersion
            elif _classVersion is None:
                _objectdata[Constants.CLASSVERSION] = cls.classVersion
            elif isinstance(_classVersion, (float,int)):
                # Converting to string
                _objectdata[Constants.CLASSVERSION] = '%.1f' % _classVersion + '.0'
            else:
                getLogger().debug(f'_updateToJson_3_1: Undefined _classversion {_classVersion}; setting to {cls.classVersion}')
                _objectdata[Constants.CLASSVERSION] = cls.classVersion
            del(_metaData[Constants.CLASSVERSION])

            if Constants.CLASSINFO in _metaData:
                _objectdata[Constants.CLASSINFO] = _metaData.get(Constants.CLASSINFO)
                del(_metaData[Constants.CLASSINFO])

            # Encode the object trait data as a dict _data
            _data = dict(item for item in theData[1:])

            # we are now at 3.1.0
            _newData = {}
            _newData[Constants.CCPNMRJSON] = '3.1.0'
            _newData[Constants.OBJECT_UID] = _uid
            _newData[Constants.OBJECTDATA] = _objectdata
            _newData[Constants.METADATA] = _metaData
            _newData[Constants.DATA] = _data

            return _newData

        else:
            raise RuntimeError(f'updating JSON 3.0 to 3.1.0: unrecognised data {theData}')

    def _update(cls, dataDict) -> dict:
        """Update dataDict using  the handlers
        :returns updated dataDict
        :raises RuntimeError
        """
        # this should not be necessary, but just a check
        dataDict = cls._updateToJson3_1_0(dataDict)

        if hasattr(cls, Constants.UPDATEHANDLERS):
            # We have updates
            for updateHandler in getattr(cls, Constants.UPDATEHANDLERS):
                dataDict = updateHandler(cls, dataDict)

        # # check if all is ok
        currentVersion = VersionString(dataDict[Constants.CCPNMRJSON])
        if currentVersion < cls._jsonVersion:
            raise RuntimeError(f'invalid version {cls} of JSON data; should be >= {cls._jsonVersion}')
        return dataDict

    def save(self, path, **kwds):
        """Save using appropriate handlers depending on extension.
        Non-functional unless a handler is added by fileHandler decorator.
        **kwds do get passed on to the 'toX' method defined by the fileHandler decorator.
        """
        extension = Path(path).suffix
        if not extension:
            raise ValueError('Unable to save: invalid path "%s"; cannot determine type from extension "%s"' % (path, extension))

        if not hasattr(self, Constants.FILEHANDLERS):
            raise RuntimeError('Unable to save; No fileHandlers defined for %s' % self)
        _fileHandlers = getattr(self, Constants.FILEHANDLERS)

        if (fileHandler := _fileHandlers.get(extension)) is None:
            raise RuntimeError('Unable to save; no fileHandler defined for extension "%s"' % extension)

        self.setJsonMetadata(Constants.USER, getpass.getuser(), force=True)
        self.setJsonMetadata(Constants.LASTPATH, str(path), force=True)
        self.setJsonMetadata(Constants.TIMESTAMP, str(now()), force=True)
        fileHandler.save(self, path, **kwds)

    def restore(self, path, **kwds):
        """Restore from file using appropriate handlers depending on extension; return self
        Non-functional unless a handler is added by fileHandler decorator.
        **kwds do get passed on to the 'fromX' method defined by the fileHandler decorator.
        :return self
        """
        extension = Path(path).suffix
        if not extension:
            raise ValueError('Unable to restore: invalid path "%s"; cannot determine type from extension "%s"' % (path, extension))

        if not hasattr(self, Constants.FILEHANDLERS):
            raise RuntimeError('Unable to restore: no fileHandlers defined for %s' % self)
        _fileHandlers = getattr(self, Constants.FILEHANDLERS)

        if (fileHandler := _fileHandlers.get(extension)) is None:
            raise RuntimeError('Unable to restore; no fileHandler defined for extension "%s"' % extension)

        fileHandler.restore(self, path, **kwds)
        self.setJsonMetadata(Constants.LASTPATH, str(path), force=True)
        return self

# end class


class CcpnJsonDirectoryABC(OrderedDict):
    """An Abstract base class that restores objects (type CcpNmrJson) from the json files in a
    directory as (key, object) pairs
    """

    #--------------------------------------------------------------------------------------------
    # to be subclassed
    #--------------------------------------------------------------------------------------------
    attributeName = None # attribute of object whose value functions as the key to store the object
    directory = None  # directory containing the json files
    sorted = False  # defines if objects needs sorting; if True, the objects generated from the json
                    # files require the __le__ and __lt__ methods
    recursive = False
    extension = '.json'
    searchPattern = '*.json'
    #--------------------------------------------------------------------------------------------
    # end to be subclassed
    #--------------------------------------------------------------------------------------------

    def __init__(self):
        super().__init__()
        self._traits = self.readFromJson()
        self.populate()

    def readFromJson(self) -> list:
        """read json file(s) in directory to create a list of object(s)
        """
        objs = []
        if self.directory is None:
            return objs
        if isinstance(self.directory, str):
            self.directory = aPath(self.directory)

        for path in self.directory.glob(self.searchPattern):
            try:
                obj = CcpNmrJson.newObjectFromJson(path)
                objs.append(obj)
            except Exception as err:
                getLogger().warn(f'Cannot load the file {path}. Skipping with error: {err}')
        return objs

    def populate(self):
        " populate the ordered-dict"
        if self.sorted:
            self._traits.sort()
        for record in self._traits:
            key = getattr(record, self.attributeName)
            self[key] = record

    def saveToJson(self, directory=None):
        "Save all records to json"
        if directory is None:
            directory = aPath(self.directory)
        for key, record in self.items():
            path = directory / key + self.extension
            record.save(path)

