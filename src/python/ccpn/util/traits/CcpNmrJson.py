#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2018"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                 )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: geertenv $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:36 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
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

from ccpn.util.decorators import singleton
from ccpn.util.Path import aPath, Path
from ccpn.util.AttributeDict import AttributeDict
from ccpn.util.traits.TraitBase import TraitBase
from ccpn.util.traits.TraitJsonHandlerBase import TraitJsonHandlerBase
from ccpn.util.traits.CcpNmrTraits import default, Dict
from ccpn.util.Logging import getLogger
from sandbox.Geerten.Refactored.decorators import debug2Enter, debug3Enter, debug3Leave


@singleton
class Constants(TraitBase):
    # jsonHandlers
    JSONHANDLER = 'jsonHandler'
    RECURSION = 'recursion'

    # used for file handler routines
    SAVE = '_save'
    RESTORE = '_restore'
    FILEHANDLERS = '_fileHandlers'

    # update handler routines
    UPDATEHANDLERS = '_updateHandlers'
    UPDATE = '_update'

    # metadata
    METADATA = '_metadata'

    # used in metadata dict
    JSONVERSION = 'jsonVersion'
    CLASSNAME = 'className'
    CLASSVERSION = 'classVersion'
    USER = 'user'
    LASTPATH = 'lastPath'
# end class

# create one instance
constants = Constants()


def jsonHandler(trait):
    """decorator for defining a json handler class on a trait
    """
    def theDecorator(cls):
        trait.tag(jsonHandler=cls)
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

    @debug2Enter()
    def save(self, obj, path, **kwds):
        """Saves obj to path
        """
        path = aPath(path)
        if not path.suffix == self.extension:
            # this should not happen
            raise ValueError('invalid path "%s"; does not match extension "%s"' % (path, self.extension))

        path.write_text(self.toString(obj, **kwds))

    @debug2Enter()
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
    """Define toString, fromString methods for a file with extension.
    Decorates the class with the _save and _restore routines;
    It also defines the _fileHandler dict for the class, used to store the handlers. 
    """

    def theDecorator(cls):
        """This function will decorate cls with filehandler dict and save and restore routines
        """

        def getExtension(path):
            "Return extension of path or None is not present"
            extension = Path(path).suffix
            if len(extension) == 0:
                extension = None
            return extension

        def _save(self, path, **kwds):
            """This is the _save method for the class; select the handler on the basis of the 
            extension of path.
            """
            extension = getExtension(path)
            if extension is None:
                raise ValueError('invalid path "%s"; cannot determine type from extension "%s"' % (path, extension))
            if extension not in self._fileHandlers:
                raise ValueError('invalid extension "%s", no handler defined' % extension)
            self._fileHandlers[extension].save(self, path, **kwds)

        setattr(cls, constants.SAVE, _save)

        def _restore(self, path, **kwds):
            """This is the restore method for the class; select the handler on the basis of the 
            extension of path.
            Return self
            """
            extension = getExtension(path)
            if extension is None:
                raise ValueError('invalid path "%s"; cannot determine type from extension "%s"' % (path, extension))
            if extension not in self._fileHandlers:
                raise ValueError('invalid extension "%s", no handler defined' % extension)
            self._fileHandlers[extension].restore(self, path, **kwds)
            return self

        setattr(cls, constants.RESTORE, _restore)

        # assure that the filehandlers can be stored
        if not hasattr(cls, constants.FILEHANDLERS):
            setattr(cls, constants.FILEHANDLERS, {})
        handlers = getattr(cls, constants.FILEHANDLERS)
        # add the handler
        handlers[extension] = _GenericFileHandler(extension=extension, cls=cls, toString=toString,
                                                  fromString=fromString)

        return cls

    return theDecorator


def update(updateHandler, push=False):
    """Decorator to register updateHandler function
    It also defines the _update method and _updateHandlers list for the class. 
    
    profile updatHandler: 
    
        updateHandler(obj, dataDict) -> dataDict
        
        obj: object that is being restored
        dataDict: (attribute, value) pairs
        
        returns: dataDict in-line with obj
    """

    def theDecorator(cls):
        """This function will decorate cls with _update, _updateHandler list and registers the updateHandler
        """

        def _update(self, dataDict):
            """Process the updates using all the handlers; returns dataDict dict
            """
            for handler in getattr(self, constants.UPDATEHANDLERS):
                dataDict = handler(self, dataDict)
            # check if updates went ok
            currentVersion = dataDict[constants.METADATA][constants.JSONVERSION]
            if currentVersion < self.jsonVersion:
                raise RuntimeError('invalid version "%s" of json data; cannot restore' % currentVersion)
            return dataDict

        setattr(cls, constants.UPDATE, _update)

        # assure that the update handlers can be stored
        if not hasattr(cls, constants.UPDATEHANDLERS):
            setattr(cls, constants.UPDATEHANDLERS, [])
        handlers = getattr(cls, constants.UPDATEHANDLERS)
        # add the handler
        indx = 0 if push else len(handlers)
        handlers.insert(indx, updateHandler)

        return cls

    return theDecorator

# Dummy's to test
#
# def _updateJson_1_0(obj, dataDict):
#     "dummy to try"
#
#     if not constants.METADATA in dataDict:
#         # invalid file without metadata
#         raise RuntimeError('No metadata dict')
#
#     version = dataDict[constants.METADATA][constants.JSONVERSION]
#     if version > 1.0:
#         print('>>> skipping _upgradeJson_1.0 (%s)' % obj.__class__.__name__)
#         return dataDict
#     print('>>> upgrading version %s to 2.0 (%s)' % (version, obj.__class__.__name__))
#     dataDict[constants.METADATA][constants.JSONVERSION] = 2.0
#     return dataDict
#
#
# def _updateJson_2_0(obj, dataDict):
#     "dummy to try"
#     if not constants.METADATA in dataDict:
#         # invalid file without metadata
#         raise RuntimeError('No metadata dict')
#
#     version = dataDict[constants.METADATA][constants.JSONVERSION]
#     if version > 2.0:
#         print('>>> skipping _upgradeJson_1.0 (%s)' % obj.__class__.__name__)
#         return dataDict
#     print('>>> upgrading version %s to 2.0 (%s)' % (version, obj.__class__.__name__))
#     dataDict[constants.METADATA][constants.JSONVERSION] = 3.0
#     return dataDict


# decorate the class
#@update(_updateJson_2_0)
#@update(_updateJson_1_0)

@fileHandler('.json', 'toJson', 'fromJson')
class CcpNmrJson(TraitBase):
    """
    Abstract base class to handle objects to and from json

    --------------------------------------------------------------------------------------------
     Define attributes (traits) as traitlets instances (Import from util/traits/CcpNmrTraits).

     Traits to be saved to json are tagged saveToJson=True.
         Example:  myint = Int().tag(saveToJson=True)

     All traits can be saved by default setting the class attribute saveAllTraitsToJson to True
        Example:   saveAllTraitsToJson = True
         
         
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

     2) A custom traitlet class can have a traitlet-specific jsonHandler class defined inside its class
     definition (see Adict for example).
     
     3) A TraitBase class can have a jsonHandler, which it would use for all traits. NB assure that the handler
     can deal with all trait types defined in the class
     
     4) No explicit handler defined, json decoders are assumed be able to handle it.
     

     A jsonHandler class must derive from TraitJsonHandlerBase and can subclass
     two  methods:

         encode(obj, trait) which returns a json serialisable object
         decode(obj, trait, value) which uses value to generate and set the new (or modified) obj 

     Example:

         class myHandler(TraitJsonHandlerBase):
               def encode(self, obj, trait):
                   "returns a json serialisable object"
                   value = getattr(obj, trait)
                   -- some action on value --
                   return value

               def decode(self, obj, trait, value):
                   "uses value to generate and set the new (or modified) obj"
                   newValue =  --- some action using value ---
                   setattr(obj, trait, newValue)

     Any CcpNmrJson-derived class maintains metadata. Use the setMetadata() method to add data

     NB: Need to register the class for proper restoring from the json data
     Example:

         class MyClass(CcpNmrJson):

            .. actions

         #end class
         MyClass.register()
    --------------------------------------------------------------------------------------------
    """

    #--------------------------------------------------------------------------------------------
    # to be subclassed
    #--------------------------------------------------------------------------------------------

    saveAllTraitsToJson = False  # This flag effectively sets saveToJson to True/False for all traits
    version = None  # The version idetifier for the specific class (usefull when upgrading is required)

    #--------------------------------------------------------------------------------------------
    # end to be subclassed
    #--------------------------------------------------------------------------------------------

    jsonVersion = 3.0

    _registeredClasses = {}  # A dict that contains the (className, class) mappings for restoring
                             # CcpNmrJson (sub-)classes from json files

    @staticmethod
    def isRegistered(className):
        """Return True if className is registered"""
        return className in CcpNmrJson._registeredClasses

    @classmethod
    def register(cls):
        """Register the class"""
        className = cls.__name__
        if cls.isRegistered(className):
            raise RuntimeError('className "%s" is already registered' % className)
        CcpNmrJson._registeredClasses[className] = cls

    @staticmethod
    def _getClassFromDict(theDict):
        """Return the class from theDict
        """
        metadata = theDict.get(constants.METADATA)
        if metadata is None:
            raise ValueError('theDict is not a valid representation of a CcpNmrJson (sub-)type')

        className = metadata.get(constants.CLASSNAME)
        if className is None:
            raise ValueError('metadata does not contain the classname of a CcpNmrJson (sub-)type')

        if not className in CcpNmrJson._registeredClasses:
            raise RuntimeError('Cannot decode class "%s"' % className)
        cls = CcpNmrJson._registeredClasses[className]
        return cls

    @staticmethod
    def isEncodedObject(theList):
        """Return True if theList defines an encoded CcpNmr object. To establish this, we look at the structure
        which must be a list of (key,value) items, encoded as a list, with the first (key,value) pair encoding the
        metadata dict.
        """
        if isinstance(theList, list) and len(theList) > 0 and \
           isinstance(theList[0], (list,tuple)) and len(theList[0]) == 2 and theList[0][0] == constants.METADATA and \
           isinstance(theList[0][1], dict) and constants.JSONVERSION in theList[0][1]:
            return True
        return False

    @staticmethod
    def _newObjectFromDict(theDict):
        """Return new object as defined by theDict;
        requires presence of metadata and registered classname
        CCPNMRINTERNAL: used in recursive handler classes (see below)
        """
        cls = CcpNmrJson._getClassFromDict(theDict)
        obj = cls()
        obj._decode(theDict)
        return obj

    @staticmethod
    def newObjectFromJson(path):
        """Create a new object defined by json-file path; this should be a json file with valid metadata
        needed for restoring
        """
        path = aPath(path)
        if not path.exists():
            raise FileNotFoundError('file "%s" does not exist' % path)

        with path.open('r') as fp:
            theDict = dict(json.load(fp))

        return CcpNmrJson._newObjectFromDict(theDict)

    #--------------------------------------------------------------------------------------------

    # _metadata(should be in-sinc with constants.METADATA)
    _metadata = Dict().tag(saveToJson=True)

    @default(constants.METADATA)
    def _metadata_default(self):
        defaults = {}
        defaults[constants.JSONVERSION] = self.jsonVersion
        defaults[constants.CLASSNAME] = self.__class__.__name__
        defaults[constants.CLASSVERSION] = self.version
        defaults[constants.USER] = getpass.getuser()
        defaults[constants.LASTPATH] = 'undefined'
        return defaults

    # _metadata-specific json handler; note the invocation with the attribute, not a string!
    @jsonHandler(_metadata)
    class _metadataJsonHandler(TraitJsonHandlerBase):
        """Handle json metadata
        """
        # def encode(self, obj, trait):  # Handled by base class
        #     return getattr(obj, trait)

        def decode(self, obj, trait, value):
            # retain current metadata; just update the ones from value
            currentMetaData = getattr(obj, constants.METADATA)
            currentMetaData.update(value)
            setattr(obj, trait, currentMetaData)
    # end class

    @property
    def metadata(self):
        "Return metadata dict"
        return getattr(self, constants.METADATA)

    def setMetadata(self, **kwds):
        "Update metadata with kwds (key,value) pairs"
        self.metadata.update(**kwds)

    #--------------------------------------------------------------------------------------------

    def keys(self, **metadata):
        """Return the keys; excluding the json.METADATA trait;
        optionally filter for trait metadata; NB these are different from the json METADATA. The latter
        store information regarding the class, version, user, path, etc of the json representation of the
        object.
        """
        keys = super().keys(**metadata)
        # check if we have to remove the _metadata key
        if constants.METADATA in keys:
            idx = keys.index(constants.METADATA)
            keys.pop(idx)
        return keys

    #--------------------------------------------------------------------------------------------

    def __init__(self, **metadata):
        super().__init__()
        self.metadata.update(metadata)

    def duplicate(self, **metadata):
        """Convenience method to return a duplicate of self, using toJson and fromJson methods
        and a ad-hoc json conversion for those traits that were not included.
        Method will fail if attributes cannot be serialised
        """
        duplicate = self.__class__(**metadata)
        duplicate.fromJson(self.toJson(indent=None))
        # now find the traits that were skipped, taking all traits minus the ones we have done
        skippedTraits = set(self.keys()) - set(self.keys(saveToJson=True))
        for trait in skippedTraits:
            # duplicate using json serialisation (explicit conversion assures 'deepcopy' behavior)
            handler = self._getJsonHandler(trait)
            if handler is not None:
                value = handler().encode(self, trait)
                value = json.loads(json.dumps(value))
                handler().decode(duplicate, trait, value)
            else:
                value = json.loads(json.dumps(getattr(self, trait)))
                setattr(duplicate, trait, value)
        return duplicate

    #--------------------------------------------------------------------------------------------

    @debug3Enter()
    @debug3Leave()
    def _getJsonHandler(self, trait):
        """Check metadata trait for specific jsonHandler, 
        or subsequently check for one of the traitlet class.
        or subsequently check for one of self
        Return handler or None
        """
        # check for trait specific handler
        handler = self.trait_metadata(trait, constants.JSONHANDLER)
        if handler is not None:
            return handler
        # check for traitlet class specific handler
        # if hasattr(self.traits()[trait], constants.JSONHANDLER):
        traitObj = self.getTraitObject(trait)
        if hasattr(traitObj, constants.JSONHANDLER):
            return getattr(traitObj, constants.JSONHANDLER)
        # check for TraitBase class specific handler
        if hasattr(self, constants.JSONHANDLER):
            return getattr(self, constants.JSONHANDLER)

        return None

    def toJson(self, **kwds):
        """Return self as list of (trait, value) tuples represented in a json string
        """
        indent = kwds.setdefault('indent', 2)
        dataList = self._encode()
        return json.dumps(dataList, indent=indent)

    def _encode(self):
        """Return self as list of (trait, value) tuples
        """

        # get all traits that need saving to json
        # Subtle but important implementation change relative to the previous one-liner (~2 commits ago)
        traits = [constants.METADATA]
        traits += self.keys() if self.saveAllTraitsToJson else self.keys(saveToJson=lambda i: i)

        # create a list of (trait, value) tuples
        dataList = []
        for trait in traits:
            handler = self._getJsonHandler(trait)
            if handler is not None:
                dataList.append((trait, handler().encode(self, trait)))
            else:
                dataList.append((trait, getattr(self, trait)))
        return dataList

    def fromJson(self, string):
        """Populate/update self with data from json string; a list of (trait, value) tuples 
        Return self
        """
        if len(string) == 0:
            getLogger().warning('%s.fromJson: empty string, retaining default values' % self.__class__.__name__)
            return self
        # json file was saved as list of (trait, value) tuples
        try:
            data = json.loads(string)
            # Subtle but important implementation change relative to the previous AttributeDict (~2 commits ago)
            dataDict = dict(data)
        except json.JSONDecodeError:
            getLogger().warning('%s.fromJson: error decoding, retaining default values' % self.__class__.__name__)
            return self

        # check for upgrade method and optionally execute
        if hasattr(self, constants.UPDATE):
            updateFunc = getattr(self, constants.UPDATE)
            dataDict = updateFunc(dataDict)

        # at this point, we expect dataDict to be compatible with the data structure of the object
        if constants.METADATA in dataDict:
            if dataDict[constants.METADATA][constants.CLASSNAME] != self.__class__.__name__:
                raise RuntimeError(
                        'trying to restore from json file incompatible with class "%s"' % self.__class__.__name__)

            self._decode(dataDict)
        else:
            getLogger().warning('%s.fromJson: error decoding: no metadata, retaining default values' % self.__class__.__name__)

        return self

    def _decode(self, dataDict):
        """Populate/update self with data from dataDict
        """
        for trait in [constants.METADATA] + self.keys():
            if trait in dataDict:
                # update the trait with value from dataDict after optional decoding
                value = dataDict[trait]
                handler = self._getJsonHandler(trait)
                if handler is not None:
                    handler().decode(self, trait, value)
                else:
                    setattr(self, trait, value)
        return self

    #--------------------------------------------------------------------------------------------

    def save(self, path, **kwds):
        """Save using appropriate handlers depending on extension.
        Non-functional until the constants.SAVE method is added by fileHandler decorators.
        **kwds do get passed on to the 'toX' method defined by the fileHandler decorator.
        """
        if not hasattr(self, constants.SAVE):
            raise RuntimeError('Unable to save; no fileHandlers defined for "%s"' % self)
        self.metadata[constants.LASTPATH] = str(path)
        getattr(self, constants.SAVE)(path, **kwds)

    def restore(self, path, **kwds):
        """Restore from file using appropriate handlers depending on extension; return self
        Non-functional until the constants.RESTORE method is added by fileHandler decorators
        **kwds do get passed on to the 'fromX' method defined by the fileHandler decorator.
        """
        if not hasattr(self, constants.RESTORE):
            raise RuntimeError('Unable to restore; no fileHandlers defined for "%s"' % self)
        getattr(self, constants.RESTORE)(path, **kwds)
        # print('>>> restore:', self.metadata.setdefault(constants.LASTPATH,'undefined'), path)
        self.metadata[constants.LASTPATH] = str(path)
        return self

# end class


class CcpnJsonDirectoryABC(OrderedDict):
    """An Abstract base class that restores objects from the json files in a directory
    as (key, object) pairs
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

