"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2021-07-29 20:46:52 +0100 (Thu, July 29, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-07-07 11:47:57 +0100 (Wed, July 07, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

# from json import loads
from collections import OrderedDict
# from ccpn.core.lib.CcpnNefCommon import _isALoop
from ccpn.util.traits.CcpNmrJson import CcpNmrJson
# from ccpn.util.traits.CcpNmrTraits import CFloat, CInt, CBool, CString
from ccpn.util.Logging import getLogger
# from ccpn.util.Common import loadModules
# from ccpn.framework.PathsAndUrls import nefSaveFramePath


#=========================================================================================
# Available saveFrame handlers
#=========================================================================================

def getSaveFrameTypes() -> OrderedDict:
    """Get saveFrame types

    :return: a dictionary of (type-identifier-strings, SaveFrame classes) as (key, value) pairs
    """
    # register the saveFrame types in the correct order
    from ccpn.core.lib.NefImporter.MetaData import MetaData

    # # load all from folder
    # loadModules([nefSaveFramePath, ])

    return SaveFrameABC._saveFrames


def getSaveFrame(saveFrameType, spectrum, *args, **kwds):
    """Return instance of class if SaveFrame defined by saveFrameType has been registered

    :param saveFrameType: type str; reference to saveFrameType of saveFrame class
    :return: new instance of class if registered else None
    """
    saveFrameTypes = getSaveFrameTypes()
    cls = saveFrameTypes.get(saveFrameType)
    if cls is None:
        raise ValueError('getSaveFrame: invalid format "%s"; must be one of %s' %
                         (saveFrameType, [k for k in saveFrameTypes.keys()])
                         )

    return cls(spectrum, *args, **kwds)


def isRegistered(saveFrameType):
    """Return True if a SaveFrame class of type saveFrameType is registered

    :param saveFrameType: type str; reference to saveFrameType of saveFrame class
    :return: True if class referenced by saveFrameType has been registered else False
    """
    return getSaveFrameTypes().get(saveFrameType) is not None


#=========================================================================================
# Start of class
#=========================================================================================

class SaveFrameABC(CcpNmrJson):
    """ABC for implementation of a saveFrame import/export/content/verify
    """

    classVersion = 1.0  # For json saving

    #=========================================================================================
    # to be subclassed
    #=========================================================================================

    saveFrameType = None  # A unique string identifying the saveFrame

    #=========================================================================================
    # data formats
    #=========================================================================================
    # A dict of registered dataFormat: filled by _registerSaveFrame classmethod, called once after
    # each definition of a new derived class
    _saveFrames = OrderedDict()

    @classmethod
    def register(cls):
        """register cls.saveFrameType"""
        if cls.saveFrameType in cls._saveFrames:
            raise RuntimeError(f'SaveFrame "{cls.saveFrameType}" was already registered')
        SaveFrameABC._saveFrames[cls.saveFrameType] = cls
        getLogger().info(f'Registering saveFrame class {cls.saveFrameType}')

    #=========================================================================================
    # parameter definitions
    #=========================================================================================

    keysInOrder = True  # maintain the definition order

    saveAllTraitsToJson = True
    version = 1.0  # for json saving

    # list of core saveFrame attributes

    # parameters
    # loopnames

    #=========================================================================================
    # start of methods
    #=========================================================================================

    def __init__(self):
        """Initialise the instance
        """

        if self.saveFrameType is None:
            raise RuntimeError('%s: saveFrameType is undefined' % self.__class__.__name__)

        # parameter verify here

        super().__init__()

        # default parameters for all saveFrames
        self.setDefaultParameters()

        # initialise from parameters
        pass

    def load(self):
        """load the saveframe into the project
        """
        # This can check the common parameters, subclassing can check local
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

        # # Get ccpn-to-nef mapping for saveframe
        # category = saveFrame['sf_category']
        # framecode = saveFrame['sf_framecode']
        # mapping = nef2CcpnMap.get(category) or {}
        #
        # name = framecode[len(category) + 1:]
        # parameters, loopNames = self._parametersFromSaveFrame(saveFrame, mapping)
        #
        # # Load loops, with object as parent
        # for loopName in loopNames:
        #     loop = saveFrame.get(loopName)
        #     if loop:
        #         importer = self.importers[loopName]
        #         importer(self, project, loop, saveFrame, name)

    def verify(self):
        """verify the saveframe
        """
        # This can check the common parameters, subclassing can check local
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

        # # Get ccpn-to-nef mapping for saveframe
        # category = saveFrame['sf_category']
        # framecode = saveFrame['sf_framecode']
        # name = framecode[len(category) + 1:]
        #
        # # Verify main object
        # result = project.getCcpnNefLogging(name)
        # if result is not None:
        #     self.error('ccpn_logging - ccpnLogging {} already exists'.format(result), saveFrame, (result,))
        #     saveFrame._rowErrors[category] = (name,)

    def contents(self):
        """list the contents of the saveframe
        """
        # This can check the common parameters, subclassing can check local
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def setDefaultParameters(self):
        """Set default values for all parameters
        """
        for par in self.keys():
            self.setTraitDefaultValue(par)

    def __str__(self):
        return '<%s>' % (self.__class__.__name__)


#end class

# GUI class to handle nef import popup?

#

from ccpn.util.traits.CcpNmrTraits import Instance
from ccpn.util.traits.TraitJsonHandlerBase import CcpNmrJsonClassHandlerABC


class SaveFrameTrait(Instance):
    """Specific trait for a SaveFrame instance.
    """
    klass = SaveFrameABC

    def __init__(self, **kwds):
        Instance.__init__(self, klass=self.klass, allow_none=True, **kwds)


    class jsonHandler(CcpNmrJsonClassHandlerABC):
        # klass = SaveFrameABC
        pass
