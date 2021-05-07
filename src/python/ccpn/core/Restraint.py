"""
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
__dateModified__ = "$dateModified: 2021-05-07 12:57:52 +0100 (Fri, May 07, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Tuple, Union
import collections
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.RestraintList import RestraintList
from ccpn.core.Peak import Peak
from ccpnmodel.ccpncore.api.ccp.nmr import NmrConstraint
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject


class Restraint(AbstractWrapperObject):
    """Restraint. The type is defined in the containing RestraintList.

    Most of the values are the consensus of the values in the contained
    RestraintContributions. In the normal case, where you have only one
    RestraintContribution per Restraint, you can get and set the values
    directly from the Restraint without reference to the RestraintContributions. """

    #: Short class name, for PID.
    shortClassName = 'RE'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Restraint'

    _parentClass = RestraintList

    #: Name of plural link to instances of class
    _pluralLinkName = 'restraints'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = NmrConstraint.AbstractConstraint._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiConstraint(self) -> NmrConstraint.AbstractConstraint:
        """ CCPN API Constraint matching Restraint"""
        return self._wrappedData

    @property
    def _parent(self) -> RestraintList:
        """RestraintList object containing restraint."""
        return self._project._data2Obj[self._wrappedData.parentList]

    restraintList = _parent

    @property
    def _key(self) -> str:
        """id string - serial number converted to string"""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """serial number of Restraint, used in Pid and to identify the Restraint. """
        return self._wrappedData.serial

    # @property
    # def comment(self) -> str:
    #     """Free-form text comment"""
    #     return self._wrappedData.details
    #
    # @comment.setter
    # def comment(self, value: str):
    #     self._wrappedData.details = value

    @property
    def peaks(self) -> Tuple[Peak, ...]:
        """peaks used to derive restraint"""
        ff = self._project._data2Obj.get
        return tuple(sorted(ff(x) for x in self._wrappedData.peaks))

    @peaks.setter
    def peaks(self, value: Sequence):
        value = tuple(self.getByPid(x) if isinstance(x, str) else x for x in value)
        self._wrappedData.peaks = [x._wrappedData for x in value]

    @property
    def targetValue(self) -> float:
        """target value of constraint - consensus of all contributions or None"""
        aSet = set(x.targetValue for x in self._wrappedData.contributions)
        if len(aSet) == 1:
            return aSet.pop()
        else:
            return None

    @targetValue.setter
    def targetValue(self, value: float):
        for contribution in self._wrappedData.contributions:
            contribution.targetValue = value

    @property
    def error(self) -> float:
        """standard error of restraint - consensus of all contributions or None"""
        aSet = set(x.error for x in self._wrappedData.contributions)
        if len(aSet) == 1:
            return aSet.pop()
        else:
            return None

    @error.setter
    def error(self, value: float):
        for contribution in self._wrappedData.contributions:
            contribution.error = value

    @property
    def weight(self) -> float:
        """weight of restraint - consensus of all contributions or None"""
        aSet = set(x.weight for x in self._wrappedData.contributions)
        if len(aSet) == 1:
            return aSet.pop()
        else:
            return None

    @weight.setter
    def weight(self, value: float):
        for contribution in self._wrappedData.contributions:
            contribution.weight = value

    @property
    def upperLimit(self) -> float:
        """upperLimit of restraint - consensus of all contributions or None"""
        aSet = set(x.upperLimit for x in self._wrappedData.contributions)
        if len(aSet) == 1:
            return aSet.pop()
        else:
            return None

    @upperLimit.setter
    def upperLimit(self, value: float):
        for contribution in self._wrappedData.contributions:
            contribution.upperLimit = value

    @property
    def lowerLimit(self) -> float:
        """lowerLimit of restraint - consensus of all contributions or None"""
        aSet = set(x.lowerLimit for x in self._wrappedData.contributions)
        if len(aSet) == 1:
            return aSet.pop()
        else:
            return None

    @lowerLimit.setter
    def lowerLimit(self, value: float):
        for contribution in self._wrappedData.contributions:
            contribution.lowerLimit = value

    @property
    def additionalUpperLimit(self) -> float:
        """additionalUpperLimit of restraint - consensus of all contributions or None.
        Used for potential functions that require more than one parameter, typically for
        parabolic-linear potentials where the additionalUpperLimit marks the transition from
        parabolic to linear potential"""
        aSet = set(x.additionalUpperLimit for x in self._wrappedData.contributions)
        if len(aSet) == 1:
            return aSet.pop()
        else:
            return None

    @additionalUpperLimit.setter
    def additionalUpperLimit(self, value: float):
        for contribution in self._wrappedData.contributions:
            contribution.additionalUpperLimit = value

    @property
    def additionalLowerLimit(self) -> float:
        """additionalLowerLimit of restraint - consensus of all contributions or None
        Used for potential functions that require more than one parameter, typically for
        parabolic-linear potentials where the additionalLowerLimit marks the transition from
        parabolic to linear potential"""
        aSet = set(x.additionalLowerLimit for x in self._wrappedData.contributions)
        if len(aSet) == 1:
            return aSet.pop()
        else:
            return None

    @additionalLowerLimit.setter
    def additionalLowerLimit(self, value: float):
        for contribution in self._wrappedData.contributions:
            contribution.additionalLowerLimit = value

    @property
    def vectorLength(self) -> str:
        """Reference vector length, where applicable. (Mainly?) for Rdc"""
        return self._wrappedData.vectorLength

    @vectorLength.setter
    def vectorLength(self, value: float):
        self._wrappedData.vectorLength = value

    @property
    def figureOfMerit(self) -> str:
        """Restraint figure of merit, between 0.0 and 1.0 inclusive."""
        return self._wrappedData.figureOfMerit

    @figureOfMerit.setter
    def figureOfMerit(self, value: float):
        self._wrappedData.figureOfMerit = value

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: RestraintList) -> list:
        """get wrappedData - all Constraint children of parent ConstraintList"""
        return parent._wrappedData.sortedConstraints()

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def newRestraintContribution(self, targetValue: float = None, error: float = None,
                                  weight: float = 1.0, upperLimit: float = None, lowerLimit: float = None,
                                  additionalUpperLimit: float = None, additionalLowerLimit: float = None,
                                  scale: float = 1.0, isDistanceDependent: bool = False, combinationId: int = None,
                                  restraintItems: Sequence = (), **kwds):
        """Create new RestraintContribution within Restraint.

        See the RestraintContribution class for details.

        Optional keyword arguments can be passed in; see RestraintContribution._newRestraintContribution for details.

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
        from ccpn.core.RestraintContribution import _newRestraintContribution

        return _newRestraintContribution(self, targetValue=targetValue, error=error,
                                  weight=weight, upperLimit=upperLimit, lowerLimit=lowerLimit,
                                  additionalUpperLimit=additionalUpperLimit, additionalLowerLimit=additionalLowerLimit,
                                  scale=scale, isDistanceDependent=isDistanceDependent, combinationId=combinationId,
                                  restraintItems=restraintItems, **kwds)

#=========================================================================================
# Connections to parents:
#=========================================================================================

def getter(self: Peak) -> Tuple[Restraint, ...]:
    getDataObj = self._project._data2Obj.get
    result = []
    apiPeak = self._wrappedData
    # for restraintList in self._project.restraintLists:
    #     for apiRestraint in restraintList._wrappedData.constraints:
    #         if apiPeak in apiRestraint.peaks:
    #             result.append(getDataObj(apiRestraint))
    result = [getDataObj(apiRestraint) for restraintList in self._project.restraintLists
              for apiRestraint in restraintList._wrappedData.constraints if apiPeak in apiRestraint.peaks]
    return tuple(sorted(result))


def setter(self: Peak, value: Sequence):
    apiPeak = self._wrappedData
    for restraint in self.restraints:
        restraint._wrappedData.removePeak(apiPeak)
    for restraint in value:
        restraint._wrappedData.addPeak(apiPeak)


Peak.restraints = property(getter, setter, None,
                           "Restraints corresponding to Peak")
del getter
del setter

#=========================================================================================

@newObject(Restraint)
def _newRestraint(self: RestraintList, figureOfMerit: float = None, comment: str = None,
                  peaks: Sequence[Union['Peak', str]] = (), vectorLength: float = None, serial: int = None) -> Restraint:
    """Create new Restraint within RestraintList.

    ADVANCED: Note that you just create at least one RestraintContribution afterwards in order to
    have valid data. Use the simpler createSimpleRestraint instead, unless you have specific
    reasons for needing newRestraint

    See the Restraint class for details.

    :param figureOfMerit:
    :param comment: optional comment string
    :param peaks: optional list of peaks as objects or pids
    :param vectorLength:
    :param serial: optional serial number.
    :return: a new Restraint instance.
    """
    if peaks:
        getByPid = self._project.getByPid
        peaks = [(getByPid(x) if isinstance(x, str) else x) for x in peaks]

    dd = {'figureOfMerit': figureOfMerit, 'vectorLength': vectorLength, 'details': comment,
          'peaks': [pk._wrappedData for pk in peaks if pk is not None]}

    apiRestraint = self._wrappedData.newGenericConstraint(**dd)
    result = self._project._data2Obj.get(apiRestraint)
    if result is None:
        raise RuntimeError('Unable to generate new Restraint item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
                                         % (result, serial))

    return result


def _createSimpleRestraint(self: RestraintList, comment: str = None, figureOfMerit: float = None,
                          peaks: Sequence[Peak] = (), targetValue: float = None, error: float = None,
                          weight: float = 1.0, upperLimit: float = None, lowerLimit: float = None,
                          additionalUpperLimit: float = None, additionalLowerLimit: float = None,
                          scale=1.0, vectorLength=None, restraintItems: Sequence = ()) -> Restraint:
    """Create a Restraint with a single RestraintContribution within the RestraintList.
    The function takes all the information needed and creates the RestraintContribution as
    well as the Restraint proper.

    This function should be used routinely, unless there is a need to create more complex
    Restraints.

    See the Restraint class for details.

    :param comment:
    :param figureOfMerit:
    :param peaks:
    :param targetValue:
    :param error:
    :param weight:
    :param upperLimit:
    :param lowerLimit:
    :param additionalUpperLimit:
    :param additionalLowerLimit:
    :param scale:
    :param vectorLength:
    :param restraintItems:
    :return: a new Restraint instance.
    """

    defaults = collections.OrderedDict(
            (
                ('comment', None), ('figureOfMerit', None), ('peaks', ()), ('targetValue', None), ('error', None), ('weight', 1.0),
                ('upperLimit', None), ('lowerLimit', None), ('additionalUpperLimit', None),
                ('additionalLowerLimit', None), ('scale', 1.0), ('vectorLength', None), ('restraintItems', ()),
                )
            )
    values = locals().copy()
    if peaks:
        getByPid = self._project.getByPid
        peaks = [(getByPid(x) if isinstance(x, str) else x) for x in peaks]
        values['peaks'] = tuple(x.pid for x in peaks)

    restraint = self.newRestraint(comment=comment, peaks=peaks, figureOfMerit=figureOfMerit,
                                  vectorLength=vectorLength, )
    restraint.newRestraintContribution(targetValue=targetValue, error=error, weight=weight,
                                       upperLimit=upperLimit, lowerLimit=lowerLimit,
                                       additionalUpperLimit=additionalUpperLimit,
                                       additionalLowerLimit=additionalLowerLimit, scale=scale,
                                       restraintItems=restraintItems)

    return restraint


#EJB 20181205: moved to RestraintList
# RestraintList.newRestraint = _newRestraint
# del _newRestraint
# RestraintList.createSimpleRestraint = _createSimpleRestraint

# Notifiers:
for clazz in NmrConstraint.ConstraintPeakContrib._metaclass.getNonAbstractSubtypes():
    className = clazz.qualifiedName()
    Project._apiNotifiers.extend(
            (('_modifiedLink', {'classNames': ('Peak', 'Restraint')}, className, 'delete'),
             ('_modifiedLink', {'classNames': ('Peak', 'Restraint')}, className, 'create'),
             )
            )
