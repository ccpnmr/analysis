"""
Implementing V3 property that allows for type checking,
notifications and tagging.
Following Traitlets style

e.g. in type MyClass:

    @V3Property(modelled=True
                validator=Int(allow_none=False, min=0, default_value=0
                ).tag(isImportant=True)

    def count(self) -> int:
        ":return The number of spectra"
        return self._count

    @count.setter
    def count(self, value):
        self._count = value

elsewhere:
    myObject = MyClass()

    otherObject.setNotifier(myObject, [OBSERVE], 'count', callback=someFunc)

    myObject.count = 1, will trigger the callback someFunc()
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
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
__dateModified__ = "$dateModified: 2024-10-27 11:52:37 +0000 (Sun, October 27, 2024) $"
__version__ = "$Revision: 3.2.7.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2024-10-27 11:20:30 +0100 (Sun, October 27, 2024) $"

#=========================================================================================
# Start of code
#=========================================================================================
#
from typing import Tuple, Any
from functools import partial

from ccpn.util.Common import Sentinel
from ccpn.util.Logging import getLogger
from ccpn.util.traits.CcpNmrTraits import TraitType, Bunch
from ccpn.core.lib.ContextManagers import \
    apiNotificationBlanking, notificationBlanking, undoStack, undoBlock


class HasTraities(object):
    """The class used for registering and functional behavior
    """

    @classmethod
    def _registerTraities(cls):
        """Find and collect all traities in the _traitiesDict
        """
        cls._traitiesDict = {}

        for name, val in vars(cls).items():
            if isinstance(val, V3Property):
                val.klass = cls
                # All name-related stuff handled by .setter decorator
                cls._traitiesDict[name] = val

    @classmethod
    def _getTraities(cls, names: list | tuple = (), **filterFor) -> dict:
        """Get dict of (name, V3Property) as defined by names,
        optionally filtered by metadata filterFor
        :param names: names of traities, defaults to all traities
        :param filterFor:dict: a metadata filter of (tag,value) pairs, defaults to None;
                              to be included: tag in metadata and metadata[tag] == filterFor[tag]
        :return: dict of (name, V3Property) pairs
        """
        _tDict = cls._traitiesDict
        if not names:
            names = _tDict.keys()

        if filterFor:
            _names = []
            for _name in names:
                if _name in _tDict:
                    _prop = _tDict[_name]
                    for tag in filterFor.keys():
                        if tag in _prop.metadata and _prop.metadata[tag] == filterFor[tag]:
                            _names.append(_name)
        else:
            _names = names

        return dict( (_name, cls._traitiesDict[_name]) for _name in _names )

    def _getTraitiesValues(self, names: list | tuple = (), **filterFor) -> dict:
        """Get dict of (name, V3Property-value) as defined by names,
        optionally filtered by metadata filterFor.
        :param names: names of traities, defaults to all traities
        :param filterFor:dict: a metadata filter of (tag,value) pairs, defaults to None;
                              to be included: tag in metadata and metadata[tag] == filterFor[tag]
        :return: dict of (name, V3Property) pairs
        """
        return dict( (_name, getattr(self, _name))
                     for _name in self._getTraities(names, **filterFor).keys()
                   )

#end class -----------------------------------------------------------------------------------------



class V3Property(property):
    # Doc-string commented as otherwise it appears in addition to the description of the wrapped
    # attribute ==> too much info

    def __init__(self,
                 validator: TraitType = None,
                 validateGetter: bool = True,
                 crossReference: tuple[str, str] | None = None,
                 ):
        """V3Property decorator
        :param validator: TraitType: A trait instance used for validating
        :param crossReference: tuple[str, str] | None: An optional (className, property-name) crossReference
        """
        super().__init__()

        self.name: str | None = None
        self.klass = None
        self.value = Sentinel
        self.previousValue = Sentinel

        # Note that fset and fget are reserved properties of the property object
        self._fget: callable = None
        self._fset: callable = None

        self.validateGetter = validateGetter
        self.crossReference = crossReference

        # optional validator
        if not isinstance(validator, TraitType):
            raise ValueError(f'V3Property: Invalid {validator = }')

        self.validator: TraitType | None = validator
        if self.validator:
            self.validator.v3property = self

        self.metadata: dict = {}

    #-----------------------------------------------------------------------------------------
    # getter routines
    #-----------------------------------------------------------------------------------------

    def getter(self, func):
        """"""  # deliberately empty, as not to pollute the docstring
        self._fget = func
        self.__doc__ = func.__doc__
        self.name = self.__name__ = func.__name__
        if self.validator:
            self.validator.name = self.name
        return self

    # allow for decorator to be used in normal way without explicit "setter"
    __call__ = getter

    def __get__(self, __instance, __owner):
        """"""  # deliberately empty, as not to pollute the docstring
        if __instance is None:
            return self
        else:
            return self._getter(__instance)

    def _getter(self, instance):
        """Get the values from the instance, using the _fget method
        Performs a validator (if defined) on the value of fget, catching any errors and
        returning the Sentinel

        Sets and returns self.value if properly validated
        :param instance: The instance from which to get the attribute value
        :return the value of the attribute
        :raises AttributeError: if the attribute is not properly defined or cannot be retrieved
        """
        if self.name is None:
            raise AttributeError(f'V3Property: undefined attribute name; cannot get value from {instance}')

        if self.klass is None:
            raise AttributeError(f'V3Property: undefined klass; cannot get value from {instance}')

        if self._fget is None:
            raise AttributeError(f'V3Property: cannot get {type(instance).__name__}.{self.name}')

        _value = Sentinel
        try:
            _value = self._fget(instance)
        except Exception as ex:
            raise AttributeError(f'Unable to get value for attribute {self.name!r} of {instance}; {ex}')

        if self.validateGetter and self.validator:
            # also run validator on get, as it will do any conversions to the set type
            try:
                _value = self.validator.validate(instance, _value)
            except Exception as ex:
                getLogger().debug(f'V3Property {self.klass.__name__}.{self.name}: validating {_value} failed; {ex}')
                return Sentinel

        self.value = _value
        return self.value

    #-----------------------------------------------------------------------------------------
    # setter routines
    #-----------------------------------------------------------------------------------------

    def setter(self, func):
        """"""  # deliberately empty, as not to pollute the docstring
        self._fset = func
        return self

    def __set__(self, __instance, __value):
        """"""  # deliberately empty, as not to pollute the docstring

        with undoStack() as addUndoItem:

            # split the undo in before and after, as to allow the _setter / _fset
            # to add items to the undo-stack
            addUndoItem(undo=None,
                        redo=partial(self._setter, __instance, __value)
                        )

            _previousValue, _tmp = self._setter(__instance, __value,
                                                  validate=True, fireNotifiers=True
                                               )

            addUndoItem(undo=partial(self._setter, __instance, _previousValue),
                        redo=None
                        )

    def _setter(self, instance, value, validate=True, fireNotifiers=True) -> Tuple[Any, Any]:
        """Set the value, run optional validator and fire the notifiers
        :param instance: the instance of self.klass to set attribute value for
        :param value: the value to set attribute value for
        :param validate: boolean, default True. Do validation if validator is set
        :param fireNotifiers: boolean, default True. Do fire notifiers if True
        :return: (previousValue, value) tuple
        :raises AttributeError, TypeError
        """
        if self.name is None:
            raise AttributeError(f'V3Property: undefined attribute name; cannot set value of {instance}')

        if self.klass is None:
            raise AttributeError(f'V3Property: undefined klass; cannot set value of {instance}')

        if self._fset is None:
            raise AttributeError(f'V3Property: cannot set {type(instance).__name__}.{self.name}')

        previousValue = self.previousValue = self.value if self.value is not Sentinel \
                                             else self._getter(instance)

        with notificationBlanking():
            with apiNotificationBlanking():
                try:
                    if validate and self.validator:
                        value = self.validator.validate(instance, value)

                    self._fset(instance, value)

                except Exception as ex:
                    raise ValueError(f'Setting {self.name!r} of {instance}: {ex}')

        # successfully completed the setting; store the value and fire notifiers
        self.value = value
        if fireNotifiers:
            self._fireNotifiers(instance=instance, previousValue=previousValue, value=self.value)
        return (previousValue, value)

    def _fireNotifiers(self, instance, previousValue, value, callbackDict={}):
        """Fire the Notifiers
        :param instance: the instance of self.klass to set attribute value for
        :param previousValue: the previous value of the attribute
        :param value: the new value of the attribute
        :param callbackDict: an optional dict of (key, callback) passed-on to the notifiers
        """
        # local import to avoid cycles
        from ccpn.core.lib.Notifiers import NotifierABC

        _callbackDict = {NotifierABC.OBJECT        : instance,
                         NotifierABC.ATTRIBUTE_NAME: self.name,
                         NotifierABC.PREVIOUSVALUE : previousValue,
                         NotifierABC.VALUE         : value
                         }
        _callbackDict.update(callbackDict)

        instance._fireRegisteredNotifiers(trigger=NotifierABC.OBSERVE,
                                          targetName=self.name,
                                          callbackDict=_callbackDict
                                          )

        instance._finaliseAction(NotifierABC.CHANGE)

    def _itemChangedCallback(self, bunch: Bunch):
        """Callback from the _TypedList, (_TypedDict) instances
        """
        # local import to avoid cycles
        from ccpn.core.lib.Notifiers import NotifierABC

        #convert some of the bunch (i.e. traitlets) values to callbackDict ones:
        _callbackDict = {}
        for key in [NotifierABC.ITEMS_CHANGED, NotifierABC.SUBTYPE]:
            _callbackDict[key] = bunch[key]

        _instance = bunch.owner
        with (undoStack() as addUndoItem):

            # split the undo in before and after, as to allow the _setter / _fset
            # to add items to the undo-stack
            addUndoItem(undo=None,
                        redo=partial(self._itemChangedCallback, bunch)
                       )

            # Set the value. No need for the validator, as this is a callback from a validated
            # _TypedList object; The notifiers also get fired later
            _tmp, _value = self._setter(_instance, bunch.new, validate=False, fireNotifiers=False)

            # override previous value, as this is the Item-changed callback
            _previousValue = self.previousValue = bunch.old

            _undoBunch = Bunch()
            _undoBunch.update(bunch)
            _undoBunch.new = bunch.old
            _undoBunch.old = bunch.new
            for indx,val in bunch.itemsChanged:
                _undoBunch.itemsChanged[indx] = (indx, _previousValue[indx])

            addUndoItem(undo=partial(self._itemChangedCallback, _undoBunch),
                        redo=None
                        )

        # Fire notifiers
        self._fireNotifiers(instance=_instance,
                            previousValue=_previousValue,
                            value=_value,
                            callbackDict=_callbackDict)

    #-----------------------------------------------------------------------------------------

    def tag(self, **metadata):
        """Tag the V3Property with metadata
        :param metadata: (key,value) pairs to store in the metadata dict
        :return: self
        """
        self.metadata.update(metadata)
        return self

    #-----------------------------------------------------------------------------------------

    def __str__(self):
        return (f'<V3Property {self.klass.__name__}.{self.name}>')

    __repr__ = __str__

#end class -----------------------------------------------------------------------------------------
