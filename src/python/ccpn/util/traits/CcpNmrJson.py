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

    version 3.1.0: dict with two keys (_metadata, _data).
                   _data is dict of (taitName, encoded-value) pairs

    _metadata: dict with JSONVERSION, CLASSNAME, CLASSVERSION, CLASSINFO, OBJECT_ID keys (+ optional others)

"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
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
__dateModified__ = "$dateModified: 2023-10-10 16:27:30 +0100 (Tue, October 10, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2018-05-14 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
from collections import OrderedDict
import getpass
from enum import Enum, unique

from ccpn.util.decorators import singleton
from ccpn.util.Path import aPath, Path
from ccpn.util.AttributeDict import AttributeDict
from ccpn.util.traits.TraitBase import TraitBase
from ccpn.util.traits.TraitJsonHandlerBase import TraitJsonHandlerBase
from ccpn.util.traits.CcpNmrTraits import default, Dict, CString
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
    CCPNMRJSON = '_CcpNmrJson'
    METADATA = '_metadata'
    DATA = '_data'
    JSON_KEYS = [CCPNMRJSON, METADATA, DATA]

    # object data

    # used in metadata dict
    JSONVERSION = 'jsonVersion'  # 3.0 def
    CLASSNAME = 'className'
    CLASSVERSION = 'classVersion'
    CLASSINFO = 'classInfo'
    OBJECT_ID = '_id'
    USER = 'user'
    LASTPATH = 'lastPath'
    TIMESTAMP = 'timestamp'
    # 'reserved' metadata keys
    METADATA_KEYS = (CLASSNAME, CLASSVERSION, CLASSINFO, OBJECT_ID, USER, LASTPATH, TIMESTAMP)
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
    It also defines the _update method and _updateHandlers list for the class. 

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

    #--------------------------------------------------------------------------------------------
    # to be subclassed
    #--------------------------------------------------------------------------------------------

    saveAllTraitsToJson = False  # This flag effectively sets saveToJson to True/False for all traits
    classVersion = '1.0.0'  # The version identifier for the specific class (usefull when upgrading is required)
    classInfo = None  # Any information about the class

    #--------------------------------------------------------------------------------------------
    # end to be subclassed
    #--------------------------------------------------------------------------------------------

    # jsonVersion: 'A version id to track any changes to the JSON implementation'
    _jsonVersion = VersionString('3.1.0')

    #--------------------------------------------------------------------------------------------
    # _metadata: should be in-sinc with Constants.METADATA
    _metadata = Dict().tag(saveToJson=True, info='The metadata of the class')

    @default(Constants.METADATA)
    def _metadata_default(self) -> dict:
        """The defaults for the metadata dict"""
        defaults = {}
        defaults[Constants.CLASSNAME] = self.__class__.__name__
        defaults[Constants.CLASSVERSION] = self.classVersion
        defaults[Constants.CLASSINFO] = self.classInfo
        defaults[Constants.OBJECT_ID] = self._id
        # Added by the topobject that saved the file
        # defaults[Constants.USER] = getpass.getuser()
        # defaults[Constants.LASTPATH] = 'undefined'
        # defaults[Constants.TIMESTAMP] = str(now())
        return defaults

    # _metadata-specific json handler; note the invocation with the attribute, not a string!
    @jsonHandler(_metadata)
    class _metadataJsonHandler(TraitJsonHandlerBase):
        """Handle json metadata
        """
        # def encode(value):  # Handled by base class
        def decode(self, value):
            # retain essential current metadata; just update the others from value (reflecting the
            # data in the json file
            currentMetaData = getattr(self.obj, Constants.METADATA)
            currentMetaData.update(value)
            return currentMetaData
    # end class

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

    # Dict to track encoded/decoded objects
    _objectDict = {}

    @property
    def _id(self) -> str:
        """:return a Hex representation of id as string
        """
        return str(hex(id(self)))

    #--------------------------------------------------------------------------------------------

    @staticmethod
    def _getClassFromDict(theDict):
        """Return the class as defined in the objectdata that should be in theDict
        """
        className = theDict.get(Constants.METADATA).get(Constants.CLASSNAME)
        if className is None:
            raise ValueError(f'{Constants.METADATA} does not contain the classname of a CcpNmrJson (sub-)type')
        if not className in CcpNmrJson._registeredClasses:
            raise RuntimeError(f'Unregistered class "{className}"; Cannot decode the data in theDict')
        cls = CcpNmrJson._registeredClasses[className]
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
            # This could be a 3.1.0 encoded object; needs to be a dict of len 3 and have CCPNMRJSON key
            if len(theData) == 3 and Constants.CCPNMRJSON in theData:
                return True
            else:
                return False

        else:
            # not a list or dict
            return False

    @staticmethod
    def _newObjectFromDict(theData, **kwds):
        """Return new object as defined by theData; kwds are passed to the class instantiation
        requires presence of metadata and registered classname
        CCPNMRINTERNAL: used in recursive handler classes (see below)
        """
        theDict = CcpNmrJson._updateToJson3_1(theData)
        cls = CcpNmrJson._getClassFromDict(theDict)
        obj = cls(**kwds)
        theDict = obj._update(theDict)
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

    def keys(self, **metadata):
        """Return the keys; excluding the json.METADATA trait;
        optionally filter for trait metadata; NB these are different from the json METADATA. The latter
        store information regarding the class, version, user, path, etc of the json representation of the
        object.
        """
        keys = [key for key in super().keys(**metadata) if key not in Constants.JSON_KEYS]
        return keys

    #--------------------------------------------------------------------------------------------

    def __init__(self, **metadata):
        super().__init__()
        for key, value in metadata.items():
            # This affords the necesary safeguarding against accidentially overwriting
            # any protected keys.
            self.setJsonMetadata(key=key, value=value)

    def duplicate(self, **metadata):
        """Convenience method to return a duplicate of self, using
        json serialisation with trait jsonHandlers to assure 'deepcopy' behavior

        Method will fail if attributes cannot be serialised; e.g. an Any trait set to a non-serialisable
        object.
        Method will fail if there are any unregistered CcpNmrJson objects

        :parameter metadata: optional keyword=value pairs to update in the json metadata
        :returns a duplicate of self
        """
        CcpNmrJson._objectDict = {}
        _encoded = self._encode(encodeAllTraits=True)
        CcpNmrJson._objectDict = {}

        _json = json.dumps(_encoded)
        # effectively make a copy by loading the json string
        _encodedDuplicate = json.loads(_json)

        CcpNmrJson._objectDict = {}
        duplicate = self._newObjectFromDict(_encodedDuplicate, **metadata)
        CcpNmrJson._objectDict = {}

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
        try:
            # Encode the data
            # re-initialise the objectDict
            CcpNmrJson._objectDict = {}
            dataList = self._encode()
            # reset the _objectDict as we are done
            CcpNmrJson._objectDict = {}
        except Exception as es:
            # reset the _objectDict as we are done trying
            CcpNmrJson._objectDict = {}
            # GWV: Log this, as the error might be caught elsewhere
            getLogger().debug(f'toJson(): while encoding {self} for JSON an exception was raised: {es}')
            raise RuntimeError(f'While encoding {self} for JSON: {es}')

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
        _id = self._id
        self.setJsonMetadata(Constants.OBJECT_ID, _id, force=True)

        _data = {}
        if _id in CcpNmrJson._objectDict:
            # The data for this object have already been encoded; No need to do it again
            _data = None

        else:
            # Store the object-id for reference usage; need to do this here at the top,
            # as handling of traits might recurse and encounter self again.
            CcpNmrJson._objectDict[_id] = self

            # get all traits that need saving to json
            if encodeAllTraits:
                traitsToEncode = list(self.keys())
            else:
                traitsToEncode = [traitName for traitName in self.keys() if self._saveTraitToJson(traitName)]

            # create a dict of (traitName, value) pairs for the trait data
            _data = dict(self._encodeTrait(traitName) for traitName in traitsToEncode)

        # create the the encodedData dict
        _encodedData = {}
        _encodedData[Constants.CCPNMRJSON] = self._jsonVersion
        _encodedData[Constants.METADATA] = self._metadata
        _encodedData[Constants.DATA] = _data

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
        except json.JSONDecodeError:
            getLogger().warning('%s.fromJson: error decoding, retaining default values' % self.__class__.__name__)
            return self

        # check for updates
        try:
            dataDict = self._updateToJson3_1(data)
            dataDict = self._update(dataDict)
        except Exception as es:
            getLogger().debug(f'updating from JSON raised errror: {es}')
            getLogger().warning(f'{self.__class__.__name__}.fromJson: error updating data from JSON, retaining default values')
            return self

        # at this point, we expect dataDict to be compatible with the data structure of the object
        if (_className := dataDict.get(Constants.METADATA).get(Constants.CLASSNAME)) != self.__class__.__name__:
            raise RuntimeError(
                f'trying to restore from JSON encoded class {_className} incompatible with class {self.__class__.__name__}'
            )

        try:
            # re-initialise the class objectDict
            CcpNmrJson._objectDict = {}
            # Decodes the data
            self._decode(dataDict)
            # reset the _objectDict as we are done
            CcpNmrJson._objectDict = {}
        except Exception as es:
            # GWV: Log this, as the error might be caught elsewhere
            # reset the _objectDict as we are done trying
            CcpNmrJson._objectDict = {}
            getLogger().debug(f'fromJson: while decoding {self} as JSON an exception was raised: {es}')
            raise RuntimeError(f'While decoding {self} as JSON: {es}')

        return self

    def _decodeTrait(self, traitName, theDict):
        """Helper function to decode a single trait
        """
        # update the trait with value from theDict after optional decoding
        value = theDict.get(traitName)
        # Do not decode None's
        if value is not None:
            handler = self._getTraitJsonHandler(traitName)
            value = handler.decode(value)
        self.setTraitValue(traitName, value, force=True)

    def _decode(self, dataDict):
        """Populate/update self with data from dataDict
        :return Updated self or referenced object
        """
        self._decodeTrait(Constants.METADATA, dataDict)

        _storedId = self.getJsonMetadata(Constants.OBJECT_ID)
        _className = self.__class__.__name__

        if Constants.DATA not in dataDict:
            raise RuntimeError(f'{_className}._decode(): unable to get {Constants.DATA} from dataDict')
        _data = dataDict[Constants.DATA]

        if _data is None:
            # we have encountered an obj that already was decoded
            # Check: _storedId should be in the_objectDict
            if not _storedId in CcpNmrJson._objectDict:
                raise RuntimeError(f'{_className}._decode(): object {_storedId} referenced but no data retrievable')
            return CcpNmrJson._objectDict[_storedId]

        # We need to decode; Store the object-id for future reference usage;
        # need to do this here, as handling of traits might recurse and then need to skip self.
        CcpNmrJson._objectDict[_storedId] = self

        # Update currently defined traits
        for traitName in self.keys():
            if traitName in _data:
                self._decodeTrait(traitName, _data)

        return self

    #--------------------------------------------------------------------------------------------
    @classmethod
    def _updateToJson3_1(cls, theData) -> dict:
        """
        Update the data from 3.0 to json 3.1.0 defs
        :return: theData as an updated dict
        """
        # 3.0 json file was saved as list of (trait, value) tuples
        if isinstance(theData, list):
            _itemLengths = [len(item)!=2 for item in theData]
            if any(_itemLengths):
                raise RuntimeError(f'Updating from JSON 3.0: data invalid, expected list of (key, value) tuples')
            if len(theData) == 0:
                raise RuntimeError(f'Updating from JSON 3.0: data invalid, expected {Constants.METADATA}')

            _metaData = theData[0][1]

            # theData = dict(theData)
        # if (_metaData := theData.get(Constants.METADATA, None)) is None:
        #     raise RuntimeError(f'No {Constants.METADATA}: The data do not represent a valid JSON encoded object')

            if (_jsonVersion := _metaData.get(Constants.JSONVERSION, None)) is None:
                raise RuntimeError(f'No {Constants.JSONVERSION}: The data do not represent a valid JSON encoded 3.0 object')

            # Should be json 3.0 float
            if not isinstance(_jsonVersion, float) or _jsonVersion != 3.0:
                    raise RuntimeError(f'Updating from JSON 3.0: Undefined JSON version {_jsonVersion}')
            del(_metaData[Constants.JSONVERSION])

            if (_classVersion := _metaData.get(Constants.CLASSVERSION, None)) is None:
                _metaData[Constants.CLASSVERSION] = cls.classVersion
            else:
                _metaData[Constants.CLASSVERSION] = '%.1f' % _classVersion + '.0'

            # Encode the object trait data as a dict _data
            _data = dict(item for item in theData[1:])

            # we are now at 3.1.0
            _newData = {}
            _newData[Constants.CCPNMRJSON] = '3.1.0'
            _newData[Constants.METADATA] = _metaData
            _newData[Constants.DATA] = _data

            return _newData

        else:
            # No change: return unaltered
            return theData

    def _update(self, dataDict) -> dict:
        """Update dataDict using  the handlers
        :returns updated dataDict
        :raises RuntimeError
        """

        if hasattr(self, Constants.UPDATEHANDLERS):
            # We have updates
            for updateHandler in getattr(self, Constants.UPDATEHANDLERS):
                dataDict = updateHandler(self, dataDict)

        # # check if all is ok
        currentVersion = VersionString(dataDict[Constants.CCPNMRJSON])
        if currentVersion < self._jsonVersion:
            raise RuntimeError('invalid version "%s" of JSON data; cannot restore %s' %
                               (currentVersion, self))
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

        self._metadata[Constants.USER] = getpass.getuser()
        self._metadata[Constants.LASTPATH] = str(path)
        self._metadata[Constants.TIMESTAMP] = str(now())
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
        self._metadata[Constants.LASTPATH] = str(path)
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
    extension = '.json'
    #--------------------------------------------------------------------------------------------
    # end to be subclassed
    #--------------------------------------------------------------------------------------------

    def __init__(self):
        super().__init__()
        self.restoreFromJson()

    def restoreFromJson(self):
        "restore all records from directory; populate the ordered-dict"
        records = []
        for path in self.directory.glob('*.json'):
            records.append(CcpNmrJson.newObjectFromJson(path))
        if self.sorted:
            records.sort()
        for record in records:
            key = getattr(record, self.attributeName)
            self[key] = record

    def saveToJson(self):
        "Save all records to json"
        directory = aPath(self.directory)
        for key, record in self.items():
            path = directory / key + self.extension
            record.save(path)

