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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-01-21 11:22:12 +0000 (Fri, January 21, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2018-05-14 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

class TraitJsonHandlerBase():
    """Base class for all Trait json handlers;

     Any jsonHandler class must derive from TraitJsonHandlerBase and can subclass
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
    """

    def encode(self, obj, trait):
        "returns a json serialisable object"
        return getattr(obj, trait)

    def decode(self, obj, trait, value):
        "uses value to generate and set the new (or modified) obj"
        setattr(obj, trait, value)


class RecursiveDictHandlerABC(TraitJsonHandlerBase):
    """Abstract base class to handle (optionally) recursion of dict-like traits
    Each value of the (key,value) pairs must of CcpNmrJson (sub-)type
    """
    #--------------------------------------------------------------------------------------------
    # to be subclassed
    #--------------------------------------------------------------------------------------------
    klass = None
    recursion = True
    #--------------------------------------------------------------------------------------------
    # end to be subclassed
    #--------------------------------------------------------------------------------------------

    def encode(self, obj, trait):
        # convert dict into list of (key, value) pairs, recursing
        # for each value of (sub-)type CcpNmrJson

        # local imports to avoid circular dependencies
        from ccpn.util.traits.CcpNmrJson import CcpNmrJson

        theDict = getattr(obj, trait)
        if not isinstance(theDict, self.klass):
            raise RuntimeError('trait: "%s", expected instance class "%s", got "%s"' %
                               (trait, type(self.klass), type(theDict))
                               )
        theList = []
        for key, value in theDict.items():
            if self.recursion and isinstance(value, CcpNmrJson):
                value = value._encode()
            theList.append((key, value))
        return theList

    def decode(self, obj, trait, theList):
        # needs conversion from list into klass; recursing for each (key, value) pair
        # converting this to the relevant object

        # local imports to avoid circular dependencies
        from ccpn.util.traits.CcpNmrJson import CcpNmrJson

        result = []
        for key, value in theList:
            # check if this encoded a CcpNmrJson type object
            if self.recursion and CcpNmrJson._isEncodedObject(value):
                theDict = dict(value)
                value = CcpNmrJson._newObjectFromDict(theDict)
            result.append((key, value))
        # convert to class
        theDict = self.klass(result)
        setattr(obj, trait, theDict)
# end class


class RecursiveListHandlerABC(TraitJsonHandlerBase):
    """Abstract base class to handle recursion of list-like traits
    Each value of the (list must of CcpNmrJson (sub-)type
    """
    #--------------------------------------------------------------------------------------------
    # to be subclassed
    #--------------------------------------------------------------------------------------------
    klass = None
    recursion = True
    #--------------------------------------------------------------------------------------------
    # end to be subclassed
    #--------------------------------------------------------------------------------------------

    def encode(self, obj, trait):
        # convert list, recursing for each item of (sub-)type CcpNmrJson

        # local imports to avoid circular dependencies
        from ccpn.util.traits.CcpNmrJson import CcpNmrJson

        theList = getattr(obj, trait)
        if not isinstance(theList, self.klass):
            raise RuntimeError('trait: "%s", expected instance class "%s", got "%s"' %
                               (trait, type(self.klass), type(theList))
                               )
        result = []
        for i, item in enumerate(theList):
            if self.recursion and isinstance(item, CcpNmrJson):
                item = item._encode()
            result.append(item)
        return result

    def decode(self, obj, trait, theList):
        # needs recursing for each item in theList
        # converting this to the relevant klass

        # local imports to avoid circular dependencies
        from ccpn.util.traits.CcpNmrJson import CcpNmrJson

        result = []
        for item in theList:
            # check if this encoded a CcpNmrJson type object
            if self.recursion and CcpNmrJson._isEncodedObject(item):
                theDict = dict(item)
                item = CcpNmrJson._newObjectFromDict(theDict)
            result.append(item)
        # convert to klass
        result = self.klass(result)
        setattr(obj, trait, result)
# end class


class CcpNmrJsonClassHandlerABC(TraitJsonHandlerBase):
    """Abstract base class to handle class-like traits of the CcpNmrJson (sub-)type
    """
    # #--------------------------------------------------------------------------------------------
    # # to be subclassed
    # #--------------------------------------------------------------------------------------------
    # klass = None
    # #--------------------------------------------------------------------------------------------
    # # end to be subclassed
    # #--------------------------------------------------------------------------------------------

    def encode(self, obj, trait):
        # convert klass, of (sub-)type CcpNmrJson

        # local imports to avoid circular dependencies
        from ccpn.util.traits.CcpNmrJson import CcpNmrJson

        value = getattr(obj, trait)
        # if not isinstance(value, self.klass):
        #     raise RuntimeError('trait: "%s", expected instance class "%s", got "%s"' %
        #                        (trait, type(self.klass), type(value))
        #                        )
        if isinstance(value, CcpNmrJson):
            value = value._encode()

        return value

    def decode(self, obj, trait, value):
        # converting value to the relevant klass instance

        # local imports to avoid circular dependencies
        from ccpn.util.traits.CcpNmrJson import CcpNmrJson

        result = value
        # check if this encoded a CcpNmrJson type object
        if CcpNmrJson._isEncodedObject(value):
            theDict = dict(value)
            result = CcpNmrJson._newObjectFromDict(theDict)

        obj.setTraitValue(trait, result, force=True)
