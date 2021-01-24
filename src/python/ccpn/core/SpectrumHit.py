"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-01-24 17:58:22 +0000 (Sun, January 24, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Spectrum import Spectrum
from ccpn.core.PseudoDimension import PseudoDimension
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import SpectrumHit as ApiSpectrumHit
from ccpn.core.lib import Pid
from ccpn.util import Constants
from ccpn.core.lib.ContextManagers import newObject
from ccpn.util.Logging import getLogger
import numpy as np
from ccpn.util.Common import makeIterableList

SpectrumHitPeakList = 'SpectrumHitPeakList'

from collections import OrderedDict as od

defaultScoring = od((
                    ('A (Highest)',     100),
                    ('B (Very High)',    80),
                    ('C (High)',         60),
                    ('D (Moderate)',     40),
                    ('E (Low)',          30),
                    ('F (Very low)',     10),
                    ('G (Dubious)',       1),
                    ('H (Unlikely)',      0),
                    ))


def _grade(i):
    for k,v in defaultScoring.items():
        if i>=v: return k

def _getReferenceLevel(referenceSpectrum):
    """

    :return:int  the hit level based on  how many experiment type the reference has appeared to be a hit.
    EG. STD only -- Grade:1
    EG. STD and Wlogsy -- Grade:2 etc



    """

    if referenceSpectrum is None:
        return 0, []

    experimentTypes = []
    levelHit = 1
    for spectrumHit in referenceSpectrum.project.spectrumHits:
        if referenceSpectrum in spectrumHit._linkedReferenceSpectra:
            experimentTypes.append(spectrumHit._parent.experimentType)
    levelHit = set(experimentTypes)

    return len(levelHit), list(experimentTypes)

def scoreHit(heights, snr):
    score = 0
    try:
        totHeights= np.sum(heights)
        count = len(heights)
        score = (snr/totHeights)*count
    except Exception as err:
        print('Hit Scoring Error:', err)
    return abs(score)

def scoreHit_tot(heights, snr, shifts):
    score = 0
    try:
        totHeights= np.sum(heights)
        maxShift = np.max(np.absolute(shifts))
        count = len(shifts)
        score = (totHeights*snr*count)/maxShift
    except Exception as err:
        print('Hit Scoring Error:', err)
    return abs(score)

def _norm(x):
    z = None
    try:
        z = (x-np.min(x))/(np.max(x)-np.min(x))
    except ZeroDivisionError:
        print('Normalisation Error')
    return z


def _scoreHits(vv):
    """score = median(deltas) * len(deltas).
    if len(deltas) <=2 than is only the min
    """
    d = abs(np.array(vv))
    c = len(d)
    if c <=2:
        return np.min(d)
    D = np.median(d)
    s = D*c
    return s

class SpectrumHit(AbstractWrapperObject):
    """Used in screening and metabolomics implementations to describe
      a 'hit', i.e. that a Substance has been found to be present (metabolomics) or active (screening) in a given
      spectrum.

      The Substance referred to is defined by the SubsanceName attribute, which is part of the ID.
      For this reason SpectrumHits cannot be renamed."""

    # A spectrumHit will provide extra information for screening 1D. These are stored in _ccpnInternal as dataFrame

    #: Short class name, for PID.
    shortClassName = 'SH'
    # Attribute it necessary as subclasses must use superclass className
    className = 'SpectrumHit'

    _parentClass = Spectrum

    #: Name of plural link to instances of class
    _pluralLinkName = 'spectrumHits'

    # the attribute name used by current
    _currentAttributeName = 'spectrumHit'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiSpectrumHit._metaclass.qualifiedName()

    # link To a reference Spectrum #LM needed for screening hit analysis
    _linkedReferenceSpectra = []
    _peakListsHit = []

    # CCPN properties
    @property
    def _apiSpectrumHit(self) -> ApiSpectrumHit:
        """ CCPN SpectrumHit matching SpectrumHit"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """object identifier, used for id"""

        obj = self._wrappedData
        return Pid.createId(obj.substanceName, obj.sampledDimension, obj.sampledPoint)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        obj = self._wrappedData
        return (obj.substanceName, obj.sampledDimension, obj.sampledPoint)

    @property
    def _parent(self) -> Spectrum:
        """Spectrum containing spectrumHit."""
        return self._project._data2Obj[self._wrappedData.dataSource]

    spectrum = _parent

    @property
    def substanceName(self) -> str:
        """Name of hit substance"""
        return self._wrappedData.substanceName

    @property
    def pseudoDimensionNumber(self) -> int:
        """Dimension number for pseudoDimension (0 if none),
        if the Hit only refers to one point in a pseudoDimension"""
        return self._wrappedData.sampledDimension

    @property
    def pseudoDimension(self) -> PseudoDimension:
        """PseudoDimension,
        if the Hit only refers to one point in a pseudoDimension"""
        dimensionNumber = self._wrappedData.sampledDimension
        if dimensionNumber == 0:
            return None
        else:
            return self.spectrum.getPseudoDimension(dimensionNumber)

    @property
    def pointNumber(self) -> int:
        """Point number for pseudoDimension (0 if none),
        if the Hit only refers to one point in a pseudoDimension"""
        return self._wrappedData.sampledPoint

    @property
    def figureOfMerit(self) -> float:
        """Figure of merit describing quality of hit, between 0.0 and 1.0 inclusive."""
        return self._wrappedData.figureOfMerit

    @figureOfMerit.setter
    def figureOfMerit(self, value: float):
        self._wrappedData.figureOfMerit = value

    @property
    def meritCode(self) -> str:
        """User-defined merit code string describing quality of hit."""
        return self._wrappedData.meritCode

    @meritCode.setter
    def meritCode(self, value: str):
        self._wrappedData.meritCode = value

    @property
    def normalisedChange(self) -> float:
        """Normalized size of effect (normally intensity change). in range -1 <= x <= 1.
        Positive values denote expected changes,
        while negative values denote changes in the 'wrong' direction,
        e.g. intensity increase where a decrease was expected."""
        return self._wrappedData.normalisedChange

    @normalisedChange.setter
    def normalisedChange(self, value: float):
        self._wrappedData.normalisedChange = value

    @property
    def isConfirmed(self) -> typing.Optional[bool]:
        """True if this Hit is confirmed? True: yes; False; no; None: not determined"""
        return self._wrappedData.isConfirmed

    @isConfirmed.setter
    def isConfirmed(self, value: bool):
        self._wrappedData.isConfirmed = value

    @property
    def concentration(self) -> float:
        """Concentration determined for the spectrumHit -
        used for e.g. Metabolomics where concentrations are not known a priori."""
        return self._wrappedData.concentration

    @concentration.setter
    def concentration(self, value: float):
        self._wrappedData.concentration = value

    @property
    def concentrationError(self) -> float:
        """Estimated Standard error of SpectrumHit.concentration"""
        return self._wrappedData.concentrationError

    @concentrationError.setter
    def concentrationError(self, value: float):
        self._wrappedData.concentrationError = value

    @property
    def concentrationUnit(self) -> str:
        """Unit of SpectrumHit.concentration, one of: %s% Constants.concentrationUnits """

        result = self._wrappedData.concentrationUnit
        if result not in Constants.concentrationUnits:
            self._project._logger.warning(
                    "Unsupported stored value %s for SpectrumHit.concentrationUnit."
                    % result)
        return result

    @concentrationUnit.setter
    def concentrationUnit(self, value: str):
        if value not in Constants.concentrationUnits:
            if value is not None:
                self._project._logger.warning(
                        "Setting unsupported value %s for SpectrumHit.concentrationUnit."
                        % value)
        self._wrappedData.concentrationUnit = value

    # @property
    # def comment(self) -> str:
    #     """Free-form text comment"""
    #     return self._wrappedData.details
    #
    # @comment.setter
    # def comment(self, value: str):
    #     self._wrappedData.details = value

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Spectrum) -> list:
        """get wrappedData (Nmr.SpectrumHit) for all SpectrumHit children of parent Spectrum"""
        return parent._wrappedData.sortedSpectrumHits()


    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(SpectrumHit)
def _newSpectrumHit(self: Spectrum, substanceName: str, pointNumber: int = 0,
                    pseudoDimensionNumber: int = 0, pseudoDimension: PseudoDimension = None,
                    figureOfMerit: float = None, meritCode: str = None, normalisedChange: float = None,
                    isConfirmed: bool = None, concentration: float = None, concentrationError: float = None,
                    concentrationUnit: str = None, comment: str = None, serial: int = None):
    """Create new SpectrumHit within Spectrum.

    See the SpectrumHit class for details.

    :param substanceName:
    :param pointNumber:
    :param pseudoDimensionNumber:
    :param pseudoDimension:
    :param figureOfMerit:
    :param meritCode:
    :param normalisedChange:
    :param isConfirmed:
    :param concentration:
    :param concentrationError:
    :param concentrationUnit:
    :param comment:
    :param serial: optional serial number.
    :return: a new SpectrumHit instance.
    """

    if concentrationUnit not in Constants.concentrationUnits:
        if concentrationUnit is not None:
            self._project._logger.warning(
                    "Unsupported value %s for SpectrumHit.concentrationUnit."
                    % concentrationUnit)

    if pseudoDimension is not None:
        if not pseudoDimensionNumber:
            pseudoDimensionNumber = pseudoDimension.dimension
        elif pseudoDimensionNumber != pseudoDimension.dimension:
            raise ValueError("pseudoDimension %s incompatible with pseudoDimensionNumber %s"
                             % (pseudoDimensionNumber, pseudoDimension))

    apiSpectrumHit = self._apiDataSource.newSpectrumHit(substanceName=substanceName,
                                             sampledDimension=pseudoDimensionNumber,
                                             sampledPoint=pointNumber, figureOfMerit=figureOfMerit,
                                             meritCode=meritCode, normalisedChange=normalisedChange,
                                             isConfirmed=isConfirmed, concentration=concentration,
                                             concentrationError=concentrationError,
                                             concentrationUnit=concentrationUnit, details=comment)

    result = self._project._data2Obj.get(apiSpectrumHit)
    if result is None:
        raise RuntimeError('Unable to generate new SpectrumHit item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))

    return result


#EJB 20181203: moved to Spectrum
# Spectrum.newSpectrumHit = _newSpectrumHit
# del _newSpectrumHit


def getter(self: PseudoDimension) -> typing.List[SpectrumHit]:
    dimensionNumber = self.dimension
    return list(x for x in self.spectrum.spectrumHits if x.dimensionNumber == dimensionNumber)


PseudoDimension.spectrumHits = property(getter, None, None,
                                        "SpectrumHits (for screening/metabolomics) that refer to individual points in the PseudoDimension"
                                        )
del getter

# Additional Notifiers:
