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
__dateModified__ = "$dateModified: 2021-06-28 14:33:30 +0100 (Mon, June 28, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing

from ccpn.core.lib import Pid
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.core.lib.ContextManagers import newObject
from ccpn.util.Logging import getLogger


class SpectrumReference(AbstractWrapperObject):
    """A SpectrumReference holds detailed information about axes and referencing
    needed for e.g. multple-quantum, projection, and reduced-dimensionality experiments.

    SpectrumRefefences can only exist for frequency dimensions.
    Required for describing experiments with assignable splittings (e.g. J-coupling, RDC),
    reduced dimensionality, more than one nucleus per axis,
    or multi-atom parameters (J-dimensions, MQ dimensions)."""

    #: Short class name, for PID.
    shortClassName = 'SR'
    # Attribute it necessary as subclasses must use superclass className
    className = 'SpectrumReference'

    _parentClass = Spectrum

    # Type of dimension. Always 'Frequency' for frequency (Fourier transformed) dimension
    dimensionType = 'Frequency'

    #: Name of plural link to instances of class
    _pluralLinkName = 'spectrumReferences'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = Nmr.DataDimRef._metaclass.qualifiedName()

    def __init__(self, project, wrappedData):
        super().__init__(project, wrappedData)

    # CCPN properties
    @property
    def _apiSpectrumReference(self) -> Nmr.DataDimRef:
        """ CCPN DataDimRef matching Spectrum"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """object identifier, used for id"""
        dataDimRef = self._wrappedData
        return Pid.createId(dataDimRef.dataDim.dim, dataDimRef.expDimRef.serial)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        dataDimRef = self._wrappedData
        return (dataDimRef.dataDim.dim, dataDimRef.expDimRef.serial)

    @property
    def _parent(self) -> Spectrum:
        """Spectrum containing spectrumReference."""
        return self._project._data2Obj[self._wrappedData.dataDim.dataSource]

    spectrum = _parent

    # Attributes of DataSource and Experiment:

    @property
    def dimension(self) -> int:
        """dimension number"""
        return self._wrappedData.dataDim.dim

    @property
    def referenceSerial(self) -> int:
        """Spectrum reference serial number"""
        return self._wrappedData.expDimRef.serial

    # Attributes belonging to ExpDimRef and DataDimRef

    @property
    def spectrometerFrequency(self) -> float:
        """Absolute frequency at carrier (or at splitting 0.0). In MHz or dimensionless."""
        return self._wrappedData.expDimRef.sf

    @spectrometerFrequency.setter
    def spectrometerFrequency(self, value):
        self._wrappedData.expDimRef.sf = value

    @property
    def measurementType(self) -> str:
        """Type of NMR measurement referred to by this reference. Legal values are:
        'Shift','ShiftAnisotropy','JCoupling','Rdc','TROESY','DipolarCoupling',
        'MQShift','T1','T2','T1rho','T1zz'"""
        return self._wrappedData.expDimRef.measurementType

    @measurementType.setter
    def measurementType(self, value):
        self._wrappedData.expDimRef.measurementType = value

    @property
    def maxAliasedFrequency(self) -> float:
        """maximum possible peak frequency (in ppm) for this reference """
        return self._wrappedData.expDimRef.maxAliasedFreq

    @maxAliasedFrequency.setter
    def maxAliasedFrequency(self, value):
        self._wrappedData.expDimRef.maxAliasedFreq = value

    @property
    def minAliasedFrequency(self) -> float:
        """minimum possible peak frequency (in ppm) for this reference """
        return self._wrappedData.expDimRef.minAliasedFreq

    @minAliasedFrequency.setter
    def minAliasedFrequency(self, value):
        self._wrappedData.expDimRef.minAliasedFreq = value

    @property
    def isotopeCodes(self) -> typing.Tuple[str, ...]:
        """Isotope identification strings for isotopes.
        NB there can be several isotopes for e.g. J-coupling or multiple quantum coherence.
        """
        return self._wrappedData.expDimRef.isotopeCodes

    @isotopeCodes.setter
    def isotopeCodes(self, value: typing.Sequence):
        self._wrappedData.expDimRef.isotopeCodes = value

    @property
    def foldingMode(self) -> typing.Optional[str]:
        """folding mode matching reference (values: 'aliased', 'folded', None)"""
        dd = {True: 'folded', False: 'aliased', None: None}
        return dd[self._wrappedData.expDimRef.isFolded]

    @foldingMode.setter
    def foldingMode(self, value):
        dd = {'aliased': False, 'folded': True, None: None}
        self._wrappedData.expDimRef.isFolded = dd[value]

    @property
    def axisCode(self) -> str:
        """Reference axisCode """
        expDimRef = self._wrappedData.expDimRef
        # dataDim = self._wrappedData.dataDim
        result = expDimRef.axisCode
        # if result is None:
        #     dataDim.dataSource.experiment.resetAxisCodes()
        #     result = expDimRef.axisCode
        #
        return result

    @axisCode.setter
    def axisCode(self, value: str):
        self._wrappedData.expDimRef.axisCode = value

    @property
    def axisUnit(self) -> str:
        """unit for transformed data using thei reference (most commonly 'ppm')"""
        return self._wrappedData.expDimRef.unit

    @axisUnit.setter
    def axisUnit(self, value: str):
        self._wrappedData.expDimRef.unit = value

    # Attributes belonging to DataDimRef

    @property
    def referencePoint(self) -> float:
        """point used for axis (chemical shift) referencing."""
        return self._wrappedData.refPoint

    @referencePoint.setter
    def referencePoint(self, value):
        self._wrappedData.refPoint = value

    @property
    def referenceValue(self) -> float:
        """value used for axis (chemical shift) referencing."""
        return self._wrappedData.refValue

    @referenceValue.setter
    def referenceValue(self, value: float):
        self._wrappedData.refValue = value

    @property
    def spectralWidth(self) -> float:
        """spectral width after processing (generally in ppm) """
        return self._wrappedData.spectralWidth

    @spectralWidth.setter
    def spectralWidth(self, value: float):
        if not value:
            raise ValueError("Attempt to set spectralWidth to %s"
                             % value)
        else:
            # We assume that the number of points is constant, so setting SW changes valuePerPoint
            dataDimRef = self._wrappedData
            swold = dataDimRef.spectralWidth
            if dataDimRef.localValuePerPoint:
                dataDimRef.localValuePerPoint *= (value / swold)
            else:
                dataDimRef.dataDim.valuePerPoint *= (value / swold)

    @property
    def isAcquisition(self) -> bool:
        """True if this dimension is the acquisition dimension?"""
        return self._wrappedData.dataDim.expDim.isAcquisition

    @isAcquisition.setter
    def isAcquisition(self, value):
        self._wrappedData.dataDim.expDim.isAcquisition = value

    def pointToValue(self, point: float) -> float:
        """Axis (ppm) value corresponding to point"""
        return self._wrappedData.pointToValue(point)

    def valueToPoint(self, value: float) -> float:
        """ Point number (float) corresponding to (ppm) value"""
        return self._wrappedData.valueToPoint(value)

    @property
    def numPointsOrig(self) -> bool:
        """numPointsOrig"""
        return self._wrappedData.dataDim.numPointsOrig

    @property
    def assignmentTolerance(self) -> float:
        """Assignment Tolerance"""
        return self._wrappedData.assignmentTolerance

    @assignmentTolerance.setter
    def assignmentTolerance(self, value):
        self._wrappedData.assignmentTolerance = value

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Spectrum) -> list:
        """get wrappedData (Nmr.DataDimRefs) for all Spectrum children of parent Spectrum"""
        return [y for x in parent._wrappedData.sortedDataDims() if hasattr(x, 'dataDimRefs')
                for y in x.sortedDataDimRefs()]

    def _finaliseAction(self, action: str):
        if not super()._finaliseAction(action):
            return

        if action == 'change':
            for peak in self.spectrum.peaks:
                peak._finaliseAction('change')

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

@newObject(SpectrumReference)
def _newSpectrumReference(self: Spectrum, dimension: int, spectrometerFrequency: float,
                          isotopeCodes: typing.Sequence[str], axisCode: str = None, measurementType: str = 'Shift',
                          maxAliasedFrequency: float = None, minAliasedFrequency: float = None,
                          foldingMode: str = None, axisUnit: str = None, referencePoint: float = 0.0,
                          referenceValue: float = 0.0
                          ) -> SpectrumReference:
    """Create new SpectrumReference.

    See the SpectrumReference class for details.

    :param dimension:
    :param spectrometerFrequency:
    :param isotopeCodes:
    :param axisCode:
    :param measurementType:
    :param maxAliasedFrequency:
    :param minAliasedFrequency:
    :param foldingMode:
    :param axisUnit:
    :param referencePoint:
    :param referenceValue:
    :return: a new SpectrumReference instance.
    """

    dataSource = self._wrappedData
    dataDim = dataSource.findFirstDataDim(dim=dimension)
    if dataDim is None:
        raise ValueError("Cannot create SpectrumReference for non-existent dimension: %s" % dimension)

    expDimRef = dataDim.expDim.newExpDimRef(sf=spectrometerFrequency, isotopeCodes=isotopeCodes,
                                            measurementType=measurementType,
                                            isFolded=(foldingMode != 'folded'), axisCode=axisCode,
                                            unit=axisUnit, minAliasedFreq=minAliasedFrequency,
                                            maxAliasedFreq=maxAliasedFrequency, )

    apiDataDimRef = dataDim.newDataDimRef(expDimRef=expDimRef, refPoint=referencePoint,
                                       refValue=referenceValue)
    result = self.project._data2Obj[apiDataDimRef]
    if result is None:
        raise RuntimeError('Unable to generate new SpectrumReference item')

    return result


#EJB 20181205: moved to Spectrum
# Spectrum.newSpectrumReference = _newSpectrumReference
# del _newSpectrumReference


# def getter(self: Spectrum) -> typing.List[typing.Optional[SpectrumReference]]:
#     data2Obj = self._project._data2Obj
#     return list(data2Obj.get(x) if x else None for x in self._mainDataDimRefs())
#
#
# Spectrum.mainSpectrumReferences = property(getter, None, None,
#                                            "Main SpectrumReference for each dimension (value is None for non-frequency dimensions"
#                                            )


# Notifiers:
def _isAcquisitionHasChanged(project: Project, apiExpDim: Nmr.ExpDim):
    """Refresh SpectrumReference when ExpDim.isAcquisition has changed"""
    for dataDim in apiExpDim.dataDims:
        for dataDimRef in dataDim.dataDimRefs:
            project._modifiedApiObject(dataDimRef)


Project._setupApiNotifier(_isAcquisitionHasChanged, Nmr.ExpDim, '')
del _isAcquisitionHasChanged

Project._apiNotifiers.extend(
        (('_notifyRelatedApiObject', {'pathToObject': 'dataDimRefs', 'action': 'change'},
          Nmr.ExpDimRef._metaclass.qualifiedName(), ''),
         )
        )
className = Nmr.FreqDataDim._metaclass.qualifiedName()
Project._apiNotifiers.append(
        ('_notifyRelatedApiObject', {'pathToObject': 'dataDimRefs', 'action': 'change'}, className, ''),
        )
