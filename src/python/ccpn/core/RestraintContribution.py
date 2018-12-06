"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================

__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
from typing import Sequence, Tuple, Dict

from ccpn.core.Project import Project
from ccpn.core.Restraint import Restraint
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import CcpnSorting
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccp.nmr import NmrConstraint
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSetter, logCommandBlock
from ccpn.util.Logging import getLogger


class RestraintContribution(AbstractWrapperObject):
    """Restraint contribution, corresponding to a set of alternative Atom
    tuples with associated limits, target value, weight, and other parameters.
    Simple restraints will have only contribution, whereas more complex restraints
    can have multiple contributions with different parameters and possibly logical relationships"""

    #: Short class name, for PID.
    shortClassName = 'RC'
    # Attribute it necessary as subclasses must use superclass className
    className = 'RestraintContribution'

    _parentClass = Restraint

    #: Name of plural link to instances of class
    _pluralLinkName = 'restraintContributions'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = NmrConstraint.GenericContribution._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiContribution(self) -> NmrConstraint.GenericContribution:
        """ API Contribution matching Contribution"""
        return self._wrappedData

    @property
    def _parent(self) -> Restraint:
        """Restraint object containing restraintContribution."""
        return self._project._data2Obj[self._wrappedData.constraint]

    restraint = _parent

    @property
    def _key(self) -> str:
        """id string - serial number converted to string"""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """serial number of RestraintContribution, used in Pid and to identify the
        RestraintContribution. """
        return self._wrappedData.serial

    @property
    def targetValue(self) -> float:
        """targetValue of contribution """
        return self._wrappedData.targetValue

    @targetValue.setter
    def targetValue(self, value: float):
        self._wrappedData.targetValue = value

    @property
    def error(self) -> float:
        """error of contribution """
        return self._wrappedData.error

    @error.setter
    def error(self, value: float):
        self._wrappedData.error = value

    @property
    def weight(self) -> float:
        """weight of contribution """
        return self._wrappedData.weight

    @weight.setter
    def weight(self, value: float):
        self._wrappedData.weight = value

    @property
    def additionalLowerLimit(self) -> float:
        """additionalLowerLimit of contribution
        Used for potential functions that require more than one parameter, typically for
        parabolic-linear potentials where the additionalLowerLimit marks the transition from
        parabolic to linear potential"""
        return self._wrappedData.additionalLowerLimit

    @additionalLowerLimit.setter
    def additionalLowerLimit(self, value: float):
        self._wrappedData.additionalLowerLimit = value

    @property
    def lowerLimit(self) -> float:
        """lowerLimit of contribution """
        return self._wrappedData.lowerLimit

    @lowerLimit.setter
    def lowerLimit(self, value: float):
        self._wrappedData.lowerLimit = value

    @property
    def upperLimit(self) -> float:
        """upperLimit of contribution """
        return self._wrappedData.upperLimit

    @upperLimit.setter
    def upperLimit(self, value: float):
        self._wrappedData.upperLimit = value

    @property
    def additionalUpperLimit(self) -> float:
        """additionalUpperLimit of contribution.
        Used for potential functions that require more than one parameter, typically for
        parabolic-linear potentials where the additionalUpperLimit marks the transition from
        parabolic to linear potential"""
        return self._wrappedData.additionalUpperLimit

    @additionalUpperLimit.setter
    def additionalUpperLimit(self, value: float):
        self._wrappedData.additionalUpperLimit = value

    @property
    def scale(self) -> float:
        """scaling factor (relevant mainly for RDC) to be multiplied with targetValue to get scaled
        value """
        return self._wrappedData.scale

    @scale.setter
    def scale(self, value: float):
        self._wrappedData.scale = value

    @property
    def isDistanceDependent(self) -> bool:
        """Does targetValue depend on a variable distance (where this is relevant, e.g. for Rdc) """
        return self._wrappedData.isDistanceDependent

    @isDistanceDependent.setter
    def isDistanceDependent(self, value: bool):
        self._wrappedData.isDistanceDependent = value

    @property
    def combinationId(self) -> int:
        """combinationId of contribution. Contributions with the same combinationId
        are AND'ed together, where contributions with different combinationId (or combinationId None)
        are OR'ed"""
        return self._wrappedData.combinationId

    @combinationId.setter
    def combinationId(self, value: int):
        self._wrappedData.combinationId = value

    @property
    def restraintItems(self) -> Tuple[Tuple[str, ...]]:
        """restraint items of contribution - given as a tuple of tuples of AtomId (not Pid).

        Example value:
        (('A.127.ALA.HA','A.130.SER.H'), ('A.93.VAL.HA','A.93.TYR.H'))
        """

        itemLength = self._wrappedData.constraint.parentList.itemLength
        result = []
        sortkey = CcpnSorting.universalSortKey

        if itemLength == 1:
            for apiItem in self._wrappedData.items:
                result.append((_fixedResonance2AtomId(apiItem.resonance),))
        else:
            for apiItem in self._wrappedData.items:
                atomIds = [_fixedResonance2AtomId(x) for x in apiItem.resonances]
                if sortkey(atomIds[0]) > sortkey(atomIds[-1]):
                    # order so smallest string comes first
                    # NB This assumes that assignments are either length 2 or ordered (as is so far the case)
                    atomIds.reverse()
                result.append(tuple(atomIds))
        #
        return tuple(sorted(result, key=sortkey))

    @restraintItems.setter
    def restraintItems(self, value: Sequence[Sequence[str]]):

        itemLength = self._wrappedData.constraint.parentList.itemLength

        for ll in value:
            # make new items
            if len(ll) != itemLength:
                raise ValueError("RestraintItems must have length %s: %s" % (itemLength, ll))

        apiContribution = self._wrappedData
        for item in apiContribution.items:
            # remove old items
            item.delete()

        fetchFixedResonance = self._parent._parent._parent._fetchFixedResonance
        if itemLength == 1:
            for ll in value:
                # make new items
                apiContribution.newSingleAtomItem(
                        resonance=fetchFixedResonance(ll[0]))
        else:
            if itemLength == 4:
                func = apiContribution.newFourAtomItem
            else:
                func = apiContribution.newAtomPairItem
            for ll in value:
                # make new items
                func(resonances=tuple(fetchFixedResonance(x) for x in ll))

    def addRestraintItem(self, restraintItem: Sequence[str], _string2Item: Dict = None):
        """Add a restraint item, given as aa tuple of atomId (NOT Pid).
        Example value: ('A.127.ALA.HA','A.130.SER.H')

        The optional _string2Item dictionary speeds up the generation of many restraintItems
        in a single operation. It must be initialised with DataSet._getTempItemMap(),
        and serves only for a single DataSet.
        On principle it must be used for a closed set of operations and then discarded,
        since it is a cache of underlying FixedResonance objects
        which are in theory mutable (don't ask)"""

        itemLength = self._wrappedData.constraint.parentList.itemLength
        if len(restraintItem) != itemLength:
            raise ValueError("RestraintItem must have length %s: %s" % (itemLength, restraintItem))

        apiContribution = self._wrappedData

        fetchFixedResonance = self._parent._parent._parent._fetchFixedResonance
        resonances = []
        if _string2Item is None:
            for ss in restraintItem:
                resonance = fetchFixedResonance(ss)
                resonances.append(resonance)
        else:
            for ss in restraintItem:
                resonance = _string2Item.get(ss)
                if resonance is None:
                    resonance = fetchFixedResonance(ss, checkUniqueness=False)
                    _string2Item[ss] = resonance
                resonances.append(resonance)

        if itemLength == 1:
            # make new item
            resonance = resonances[0]
            if apiContribution.findFirstItem(resonance=resonance) is None:
                apiContribution.newSingleAtomItem(resonance=resonance)
            else:
                raise ValueError("Cannot add RestraintItem due to clash with pre-existing item: %s"
                                 % restraintItem)

        elif itemLength == 4:
            if apiContribution.findFirstItem(resonances=resonances) is None:
                apiContribution.newFourAtomItem(
                        resonances=resonances
                        )
            else:
                raise ValueError("Cannot add RestraintItem due to clash with pre-existing item: %s"
                                 % restraintItem)
        else:
            # Assume length 2
            if apiContribution.findFirstItem(resonances=resonances) is None:
                apiContribution.newAtomPairItem(
                        resonances=resonances
                        )
            else:
                raise ValueError("Cannot add RestraintItem due to clash with pre-existing item: %s"
                                 % restraintItem)
        #
        return self._project._data2Obj[apiContribution]

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Restraint) -> list:
        """get wrappedData - all ConstraintContribution children of parent ConstraintList"""
        return parent._wrappedData.sortedContributions()

    def _finaliseAction(self, action: str):
        super()._finaliseAction(action)
        # pass on any action in the list to the parent object
        if action in ['change', 'delete', 'create']:
            self.restraint._finaliseAction(action)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(RestraintContribution)
def _newRestraintContribution(self: Restraint, targetValue: float = None, error: float = None,
                              weight: float = 1.0, upperLimit: float = None, lowerLimit: float = None,
                              additionalUpperLimit: float = None, additionalLowerLimit: float = None,
                              scale: float = 1.0, isDistanceDependent: bool = False, combinationId: int = None,
                              restraintItems: Sequence = (), serial: int = None) -> RestraintContribution:
    """Create new RestraintContribution within Restraint

    See the RestraintContribution class for details.

    :param targetValue:
    :param error:
    :param weight:
    :param upperLimit:
    :param lowerLimit:
    :param additionalUpperLimit:
    :param additionalLowerLimit:
    :param scale:
    :param isDistanceDependent:
    :param combinationId:
    :param restraintItems:
    :param serial: optional serial number.
    :return: a new RestraintContribution instance.
    """
    func = self._wrappedData.newGenericContribution

    obj = func(targetValue=targetValue, error=error, weight=weight, upperLimit=upperLimit,
               lowerLimit=lowerLimit, additionalUpperLimit=additionalUpperLimit,
               additionalLowerLimit=additionalLowerLimit, scale=scale,
               isDistanceDependent=isDistanceDependent, combinationId=combinationId)
    result = self._project._data2Obj.get(obj)
    if result is None:
        raise RuntimeError('Unable to generate new RestraintContribution item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
                                         % (result, serial))

    result.restraintItems = restraintItems

    return result


#EJB 20181206: moved to Restraint
# Restraint.newRestraintContribution = _newRestraintContribution
# del _newRestraintContribution

# Notifiers:
# Change RestraintContribution when Api RestraintItems are created or deleted
for clazz in NmrConstraint.ConstraintItem._metaclass.getNonAbstractSubtypes():
    className = clazz.qualifiedName()
    Project._apiNotifiers.extend(
            (('_notifyRelatedApiObject', {'pathToObject': 'contribution', 'action': 'change'},
              className, 'delete'),
             ('_notifyRelatedApiObject', {'pathToObject': 'contribution', 'action': 'change'},
              className, 'create'),
             )
            )


def _fixedResonance2AtomId(fixedResonance: NmrConstraint.FixedResonance) -> str:
    """Utility function - get AtomId from FixedResonance """
    tags = ('chainCode', 'sequenceCode', 'residueType', 'name')
    return Pid.createId(*(getattr(fixedResonance, tag) for tag in tags))

#EJB 20181122: moved to _finaliseAction
# # Change constraint when ConstraintContribution is creted, deleted, or changed
# RestraintContribution._setupCoreNotifier('create', AbstractWrapperObject._finaliseRelatedObject,
#                                          {'pathToObject': 'restraint', 'action': 'change'})
# RestraintContribution._setupCoreNotifier('delete', AbstractWrapperObject._finaliseRelatedObject,
#                                          {'pathToObject': 'restraint', 'action': 'change'})
# RestraintContribution._setupCoreNotifier('change', AbstractWrapperObject._finaliseRelatedObject,
#                                          {'pathToObject': 'restraint', 'action': 'change'})
