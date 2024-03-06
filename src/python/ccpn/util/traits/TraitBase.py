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


import sys
import os
from contextlib import contextmanager
from traitlets import HasTraits, Undefined

from ccpn.util.Logging import getLogger


class TraitBase(HasTraits):
    """Class to give HasTraits dict-like methods keys, values, update, items and iteration

    class attributes:
    - keysInOrder = True   # If True, return key in order defined by _traitOrder attribute

    specific .tag() keywords:
    - reservedTrait:  True or False allow for selecting or skipping, respectively
    - doPrint: False skips printing by the .print() method

    """

    keysInOrder = True   # If True, return key in order defined by _traitOrder attribute
                         # of the keys; can bet put at end by traitAtEnd tag

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        # trait notifers
        self._traitNotifierBlanking = 0

    def getTraitValue(self, trait):
        """convenience (to complement setTraitValue)
        :parameter trait: the name of the trait
        :return value of trait
        """
        if not self.hasTrait(trait):
            raise ValueError('Trait "%s" does not exist for object %s' % (trait, self))
        try:
            value = self._trait_values[trait]
        except KeyError:
            # No values set; use getattr as this will trigger the machinery
            # if trait=='temperature':
            #     pass
            value = getattr(self, trait)
        return value

    def setTraitValue(self, trait, value, force=False):
        """Convenience: set value of trait, optionally overwriting immutable ones
        """
        if not self.hasTrait(trait):
            raise ValueError('Trait "%s" does not exist for object %s' % (trait, self))

        if self.isMutableTrait(trait) or force:
            self.set_trait(trait, value)
        else:
            raise ValueError('Trait "%s" is immutable' % trait)

    def getTraitDefaultValue(self, trait):
        """convenience: return default value of trait
        """
        if not self.hasTrait(trait):
            raise ValueError('Trait "%s" does not exist for object %s' % (trait, self))
        return self.getTraitObject(trait).default_value

    def setTraitDefaultValue(self, trait):
        """convenience: set trait to default value
        """
        if not self.hasTrait(trait):
            raise ValueError('Trait "%s" does not exist for object %s' % (trait, self))
        defaultValue =  self.getTraitObject(trait).default_value
        if defaultValue == Undefined:
            raise RuntimeError('Trait "%s" of object %s does not have a default value defined' % (trait, self))
        self.setTraitValue(trait, defaultValue, force=True)

    def setDefaultValues(self, overRide=False, **metadata):
        """convenience: set all traits (optionally filtered for metadata) that do not yet have
        a value (optionally overRide) to default value (if defined)
        :parameter overRide: set default vlue to all traits, including those that already have a value
                             i.e. a 'reset'.
        :parameter metadata: optionally filter traits for the metadata
        """
        for traitName, trait in self.items(**metadata):
            if (not self.trait_has_value(traitName) or overRide):
                if (defaultValue :=  trait.default_value) != Undefined:
                    self.setTraitValue(traitName, defaultValue, force=True)

    def hasTrait(self, trait):
        """Convenience, Return True if self has trait
        """
        return self.has_trait(trait)

    def getTrait(self, trait):
        """Return the trait class object corresponding to trait, or None if does not exists
        """
        return self.class_traits().get(trait)

    def getItemTrait(self, trait):
        """Return the trait object corresponding to trait for items of an iterable, i.e. used for validate_items
        or None if does not exists
        """
        theTrait = self.getTrait(trait)
        if theTrait is None: return None
        return theTrait._trait

    def getAllTraitObjects(self, objectOnly=False, **metadata) -> dict :
        """Return a dict of (traitName,  trait object) key,value pairs, optionally filtering
        for metadata.
        If objectOnly is True, only traits defined for this object are included;
        if False, also include any inherited traits.
        """
        if objectOnly:
            return self.class_own_traits(**metadata)
        else:
            return self.class_traits(**metadata)

    def getTraitObject(self, trait):
        """get the trait object or None if trait does not exist
        """
        traits = self.traits()
        return traits.get(trait)

    def isMutableTrait(self, trait):
        "Return True is trait is mutable"
        if not self.hasTrait(trait):
            raise ValueError('Trait "%s" does not exist for object %s' % (trait,self))
        traitObj = self.getTraitObject(trait)
        return not traitObj.read_only

    def getMetadata(self, trait, key, default=None):
        "convenience for trait_metadata"
        return self.trait_metadata(trait, key, default)

    def _keys(self, **metadata) -> list:
        """Get keys (object only), optionally filtering for metadata.
        Key order is determined by keysInOrder attribute and optional traitAtEnd tag settings.
        :return The keys as a list
        """
        if self.keysInOrder:
            frontKeys = [(trait._traitOrder, key) for key,trait in self.class_traits(**metadata).items()
                          if not 'traitAtEnd' in trait.metadata
                        ]
            frontKeys.sort()
            endKeys = [(trait._traitOrder, key) for key,trait in self.class_traits(**metadata).items()
                        if 'traitAtEnd' in trait.metadata
                      ]
            endKeys.sort()
            keys = [key for val,key in frontKeys] + [key for val,key in endKeys]

        else:
            keys = [key for key in self.class_traits(**metadata).keys()]
            keys.sort()
        return keys

    def keys(self, **kwds) -> list:
        """Allow for skipping or showing of reserved traits
        i.e. tagged with reservedTrait=False or True, respectively
        """
        # Downstream self._keys() call omits reservedTrait keyword,
        # as it is not set by default.

        if 'reservedTrait' not in kwds:
            # regular behavior:
            return self._keys(**kwds)

        reservedTrait = kwds['reservedTrait']

        if reservedTrait == True:
            # looking for those tagged with reservedTrait = True
            return self._keys(**kwds)

        elif reservedTrait == False:
            # reservedTrait == False; i.e. not the reserved ones
            _reservedTraits = self._keys(reservedTrait=True)  # yields those that are tagged
            # delete reservedTrait from kwds, as the tag most likely is not set
            # for (many) traits
            del kwds['reservedTrait']
            # get traits filtering for not in _reservedTraits
            return [key for key in self._keys(**kwds)
                    if key not in _reservedTraits]

        else:
            raise ValueError(f'keys(): Invalid parameter reservedTrait, expected None | True | False, got {reservedTrait}')


    # the ones below are derived from keys() method
    def values(self, **metadata):
        """get values, optionally filtering for metadata"""
        return [self.getTraitValue(key) for key in self.keys(**metadata)]

    def update(self, other, force=False, **metadata):
        """update self with values from other (dict-like), optionally filtering for metadata
        :parameter other: dict with (key,value) pairs to update
        :parameter force: force update of inmutable traits
        :parameter metadata: optional param=values pairs to filter for metadata (i.e. tag values)
        """
        for key in self.keys(**metadata):
            if key in other:
                self.setTraitValue(key, other[key], force=force)

    def items(self, **metadata):
        """iterable over key, value pairs, optionally filtering for metadata"""
        for key in self.keys(**metadata):
            value = self.getTraitValue(key)
            yield (key, value)

    def __iter__(self, **metadata):
        """iterable over key, optionally filtering for metadata"""
        for key in self.keys(**metadata):
            yield (key)

    def __getitem__(self, key):
        """Implement dict-like item assignment"""
        if key not in self.keys():
            raise KeyError("""trait "%s" does not exist; cannot get value""" % key)
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Implement dict-like item assignment"""
        if key not in self.keys():
            raise KeyError("""trait "%s" does not exist; cannot set value""" % key)
        setattr(self, key, value)

    def asDict(self, **metadata):
        """return trait, value pairs as dict, optionally filtering for metadata"""
        return dict(self.items(**metadata))

    @contextmanager
    def traitNotificationBlanking(self):
        """Blank all trait notification (per object!); i.e. they are not saved and executed late.
        If that is needed, use hold_trait_notifications()
        """

        # following hold_trait_notifications approach
        def blank(changes):
            pass

        try:
            self._traitNotifierBlanking += 1
            self.notify_change = blank
            yield

        except Exception as es:
            getLogger().debug(f'{self.__class__.__name__}.traitNotificationBlanking() level={self._traitNotifierBlanking}: caught error {es}')
            raise es

        finally:
            self._traitNotifierBlanking -= 1
            if self._traitNotifierBlanking == 0:
                del self.notify_change

    def __str__(self):
        return '<%s>' % (self.__class__.__name__,)

    def __repr__(self):
        return '<%s: at %x>' % (self.__class__.__name__, id(self))

    def print(self, printInfo=False):
        """Print all traits"""
        print('-------', self, '-------')
        for trait, value in self.items():
            doPrint = self.getMetadata(trait, key='doPrint', default=True)
            if doPrint:
                info = self.getMetadata(trait, key='info', default='')
                if len(info) > 0 and printInfo:
                    print('%-20s : %-40s (%s)' % (trait, value, info))
                else:
                    print('%-20s : %s' % (trait, value))

    # --------------------------------------------------------------------------------------------

    def getInfo(self, noDoc=False, noTraits=False, noValues=False, maxLen=50, **traits):
        """Extract information from:
        - Class docstring
        - .metadata['info'] (if metadata is present)
        - all traits tagged with 'info'

        Modify what is included using the noDoc, noTraits or **traits. For the latter, setting
        a trait True or False will switch its inclusion in the output.

            Example:    print(a.info(noDoc=True, noTraits=True, maxLen=50, mydict=True))

            ==> does not print the doc-string, does not print any traits (noTraits=True) except
            trait 'mydict' (mydict=True). The output of the trait values is limited to 50 
            characters.

        return string, optionally limited to maxLen if maxLen is not None
        """
        s = 'str:   %s\n' % self
        # doc string
        if self.__class__.__doc__ is not None and len(self.__class__.__doc__) > 0 and not noDoc:
            doc = self.__class__.__doc__.rstrip()
            s += 'doc:   %s\n' % doc
        # info if present in metadata attribute
        if hasattr(self, 'metadata') and 'info' in self.metadata and self.metadata['info'] is not None:
            s += 'info:  %s\n' % self.metadata['info']
        # find all traits that have info metadata
        iTraits = self.traits(info=lambda i: i is not None and len(i) > 0)
        if len(iTraits) > 0:
            for traitName, trait in iTraits.items():
                # the selector for displaying traits
                doTrait = traits.setdefault(traitName, not noTraits)
                if doTrait:
                    s += 'trait: %-20s %-20r' % (traitName +',',
                                                 trait.metadata['info']
                                                )
                    if not noValues:
                        value = str(self._trait_values[traitName])
                        m2 = int(maxLen / 2)
                        # Not sure why this does not work:
                        # value = value[0,m2] + ' ... ' + value[-m2:] if len(value) > maxLen else value
                        value = value[slice(0, m2)] + ' ... ' + value[slice(-m2, len(value))] \
                                if len(value) > maxLen else value
                        s += ', value = %s' % value
                    s += '\n'
        # strip last \n and return value
        #s = s[:-1] if s[-1] == '\n' else s
        return s.rstrip('\n ')

        # --------------------------------------------------------------------------------------------

# end class




