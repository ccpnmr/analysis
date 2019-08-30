"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:27 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import operator
from typing import Tuple
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.NmrAtom import NmrAtom
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.core.lib.ContextManagers import newObject


class ChemicalShift(AbstractWrapperObject):
    """Chemical Shift, containing a ChemicalShift value for the NmrAtom they belong to.

    Chemical shift values are continuously averaged over peaks assigned to the NmrAtom,
    unless this behaviour is turned off. If the NmrAtom is reassigned, the ChemcalShift
    is reassigned with it.

    ChemicalShift objects sort as the NmrAtom they belong to."""

    #: Short class name, for PID.
    shortClassName = 'CS'
    # Attribute it necessary as subclasses must use superclass className
    className = 'ChemicalShift'

    _parentClass = ChemicalShiftList

    #: Name of plural link to instances of class
    _pluralLinkName = 'chemicalShifts'

    # the attribute name used by current
    _currentAttributeName = 'chemicalShifts'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = Nmr.Shift._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiShift(self) -> Nmr.Shift:
        """ CCPN Chemical Shift matching ChemicalShift"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """identifier - assignment string"""
        # return ','.join(x or '' for x in self.nmrAtom.assignment)
        return self.nmrAtom._id

    @property
    def _localCcpnSortKey(self) -> Tuple:
        """Local sorting key, in context of parent."""

        return self.nmrAtom._ccpnSortKey[2:]

    @property
    def _parent(self) -> Project:
        """ChemicalShiftList containing ChemicalShift."""
        return self._project._data2Obj[self._wrappedData.parentList]

    chemicalShiftList = _parent

    @property
    def value(self) -> float:
        """shift value of ChemicalShift, in unit as defined in the ChemicalShiftList"""
        return self._wrappedData.value

    @value.setter
    def value(self, value: float):
        self._wrappedData.value = value

    @property
    def valueError(self) -> float:
        """shift valueError of ChemicalShift, in unit as defined in the ChemicalShiftList"""
        return self._wrappedData.error

    @valueError.setter
    def valueError(self, value: float):
        self._wrappedData.error = value

    @property
    def figureOfMerit(self) -> str:
        """Figure of Merit for ChemicalShift, between 0.0 and 1.0 inclusive."""
        return self._wrappedData.figOfMerit

    @figureOfMerit.setter
    def figureOfMerit(self, value: float):
        self._wrappedData.figOfMerit = value

    # @property
    # def comment(self) -> str:
    #     """Free-form text comment"""
    #     return self._wrappedData.details
    #
    # @comment.setter
    # def comment(self, value: str):
    #     self._wrappedData.details = value

    @property
    def nmrAtom(self) -> NmrAtom:
        """NmrAtom that the shift belongs to"""
        try:
            return self._project._data2Obj.get(self._wrappedData.resonance)
        except Exception as es:
            pass

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: ChemicalShiftList) -> list:
        """get wrappedData (ApiShift) for all ChemicalShift children of parent ChemicalShiftList"""
        # NB this is NOT the right sorting order, but sorting on atomId is not possible at the API level
        return sorted(parent._wrappedData.measurements,
                      key=operator.attrgetter('resonance.serial'))

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    def _tryToRecover(self):
        """Routine to try to recover an object that has not loaded correctly to repair integrity
        """
        pass

#=========================================================================================
# Connections to parents:
#=========================================================================================

# GWV 20181122: Moved to NmrAtom class
# def getter(self:NmrAtom) -> Tuple[ChemicalShift, ...]:
#   getDataObj = self._project._data2Obj.get
#   return tuple(sorted(getDataObj(x) for x in self._wrappedData.shifts))
#
# NmrAtom.chemicalShifts = property(getter, None, None, "Returns ChemicalShift objects connected to NmrAtom")
#
# del getter

@newObject(ChemicalShift)
def _newChemicalShift(self: ChemicalShiftList, value: float, nmrAtom: NmrAtom,
                      valueError: float = 0.0, figureOfMerit: float = 1.0,
                      comment: str = None, serial: int = None) -> ChemicalShift:
    """Create new ChemicalShift within ChemicalShiftList.

    See the ChemicalShift class for details.

    :param value:
    :param nmrAtom:
    :param valueError:
    :param figureOfMerit:
    :param comment:
    :param serial: optional serial number.
    :return: a new ChemicalShift instance.
    """

    nmrAtom = self.getByPid(nmrAtom) if isinstance(nmrAtom, str) else nmrAtom
    if not nmrAtom:
        try:
            # if there is no nmrAtom, create a new one from the default chain
            nmrChain = self.project.fetchNmrChain(shortName='@-')
            nmrResidue = nmrChain.fetchNmrResidue()
            nmrAtom = nmrResidue.fetchNmrAtom()
        except Exception as es:
            raise RuntimeError('chemicalShift: nmrAtom undefined - unable to create associated nmrAtom')

    apiShift = self._wrappedData.newShift(value=value,
                                     resonance=nmrAtom._wrappedData, error=valueError,
                                     figOfMerit=figureOfMerit, details=comment)
    result = self._project._data2Obj.get(apiShift)
    if result is None:
        raise RuntimeError('Unable to generate new ChemicalShift item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
                                         % (result, serial))

    return result


#EJB 20181203: moved to ChemicalShiftList
# ChemicalShiftList.newChemicalShift = _newChemicalShift
# del _newChemicalShift

# Notifiers:
# GWV 20181122: refactored as explicit call in NmrAtom._finalise
# # rename chemicalShifts when atom is renamed
# NmrAtom._setupCoreNotifier('rename', AbstractWrapperObject._finaliseRelatedObjectFromRename,
#                           {'pathToObject':'chemicalShifts', 'action':'rename'})
# # NB The link to NmrAtom is immutable - does need a link notifier
