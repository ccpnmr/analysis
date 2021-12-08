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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2021-12-08 14:24:31 +0000 (Wed, December 08, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Optional, Sequence, Tuple

from ccpn.core.lib import Pid
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core._implementation.SpectrumDimensionAttributes import SpectrumDimensionAttributes
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
import ccpn.core.lib.SpectrumLib as specLib

from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.core.lib.ContextManagers import newObject
from ccpn.util.Logging import getLogger


class SpectrumReference(AbstractWrapperObject, SpectrumDimensionAttributes):
    """A SpectrumReference holds detailed information about axes and referencing
    needed for e.g. multple-quantum, projection, and reduced-dimensionality experiments.

    SpectrumReferences can only exist for frequency dimensions.
    Required for describing experiments with assignable splittings (e.g. J-coupling, RDC),
    reduced dimensionality, more than one nucleus per axis,
    or multi-atom parameters (J-dimensions, MQ dimensions)."""

    #: Short class name, for PID.
    shortClassName = 'SR'
    # Attribute it necessary as subclasses must use superclass className
    className = 'SpectrumReference'

    _parentClass = Spectrum

    #: Name of plural link to instances of class
    _pluralLinkName = 'spectrumReferences'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = Nmr.DataDimRef._metaclass.qualifiedName()

    #-----------------------------------------------------------------------------------------

    def __init__(self, project, wrappedData):
        super().__init__(project, wrappedData)

    #-----------------------------------------------------------------------------------------
    # CCPN properties
    #-----------------------------------------------------------------------------------------

    @property
    def _apiSpectrumReference(self) -> Nmr.DataDimRef:
        """ CCPN DataDimRef matching Spectrum"""
        return self._wrappedData

    @property
    def _dataDim(self):
        """
        :return: dataDim instance
        """
        return self._wrappedData.dataDim

    @property
    def _dataDimRef(self):
        """
        :return: dataDim instance
        """
        return self._wrappedData

    @property
    def _expDim(self):
        """
        :return: expDim instance
        """
        return self._dataDim.expDim

    @property
    def _expDimRef(self):
        """
        :return: expDimRef instance
        """
        return self._wrappedData.expDimRef

    @property
    def _key(self) -> str:
        """object identifier, used for id"""
        return Pid.createId(self._dataDim.dim, self._expDimRef.serial)

    @property
    def _localCcpnSortKey(self) -> Tuple:
        """Local sorting key, in context of parent."""
        return (self._dataDim.dim, self._expDimRef.serial)

    @property
    def _parent(self) -> Spectrum:
        """Spectrum containing spectrumReference."""
        return self._project._data2Obj[self._wrappedData.dataDim.dataSource]

    spectrum = _parent

    #-----------------------------------------------------------------------------------------
    # Object properties are inherited from SpectrumDimensionAttributes
    #-----------------------------------------------------------------------------------------

    #=========================================================================================
    # CCPN functions
    #=========================================================================================
    def pointToValue(self, point: float) -> float:
        """:return ppm-value corresponding to point (float)"""
        return self._dataDimRef.pointToValue(point)

    def valueToPoint(self, value: float) -> float:
        """:return point (float) corresponding to ppm-value"""
        return self._dataDimRef.valueToPoint(value)

    #=========================================================================================
    # Implementation properties and functions
    #=========================================================================================

    @property
    def _serial(self) -> int:
        """Spectrum reference serial number"""
        return self._expDimRef.serial

    @classmethod
    def _getAllWrappedData(cls, parent: Spectrum) -> list:
        """get wrappedData (Nmr.DataDimRefs) for all Spectrum children of parent Spectrum"""
        return [y for x in parent._wrappedData.sortedDataDims() if hasattr(x, 'dataDimRefs')
                for y in x.sortedDataDimRefs()]

    def _finaliseAction(self, action: str):
        if not super()._finaliseAction(action):
            return

        #TODO: GWV asks: why do we have this?
        # EJB: need to single out which would require an update of peaks, e.g., changing referencePoint
        #       (don't think it's many though)
        if action == 'change':
            for peak in self.spectrum.peaks:
                peak._finaliseAction('change')



#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(SpectrumReference)
def _newSpectrumReference(self: Spectrum, dimension: int, dataSource) -> SpectrumReference:
    """Create new SpectrumReference.

    :param dimension:
    :param dataSource: A spectrum dataSource instance

    :return: a new SpectrumReference instance.

    CCPNINTERNAL: called from _newSpectrumFromDataSource
    """

    axis = dimension - 1

    nPoints = dataSource.pointCounts[axis]
    isComplex = dataSource.isComplex[axis]

    dimType = dataSource.dimensionTypes[axis]
    if dimType == specLib.DIMENSION_FREQUENCY:
        # valuePerPoint is digital resolution in Hz
        # TODO: accommodate complex points
        valuePerPoint = dataSource.spectralWidthsHz[axis] / float(nPoints)
        axisUnit = 'ppm'

    elif dimType == specLib.DIMENSION_TIME:
        # valuePerPoint is dwell time
        # valuePerPoint = 1.0 / dataSource.spectralWidthsHz[n] if _isComplex \
        #                  else 0.5 / dataSource.spectralWidthsHz[n]

        # However, for now we leave it as until we have settled the FidDataDim issue (see below)
        valuePerPoint = dataSource.spectralWidthsHz[axis] / float(nPoints)
        axisUnit = 'point'  # model does not allow 'sec'!

    else:
        raise RuntimeError('Invalid dimensionType[%d]: "%s"' % (axis, dimType))

    spectrometerFrequency = dataSource.spectrometerFrequencies[axis]
    isotopeCodes = dataSource.isotopeCodes[axis:axis + 1]
    axisCode = dataSource.axisCodes[axis]

    # generate some api objects
    # Initialise the dimension; This seems a very complicated data structure! (GWV)
    apiDataSource = self._wrappedData
    apiExperiment = apiDataSource.experiment
    apiExpDim = apiExperiment.findFirstExpDim(dim=dimension)

    apiExpDim.isAcquisition = False  # undated later

    # for now, we have to give all dimensions a FreqDataDim, otherwise the code crashes
    # A FidDataDim cannot have a DataDimRef, and that is the object used as _wrappedData!
    if (apiDataDim := apiDataSource.newFreqDataDim(dim=dimension,
                                                   expDim=apiExpDim,
                                                   numPoints=nPoints,
                                                   numPointsOrig=nPoints,
                                                   pointOffset=0,
                                                   isComplex=isComplex,
                                                   valuePerPoint=valuePerPoint
                                                   )
    ) is None:
        raise RuntimeError("Cannot create SpectrumReference for dimension: %s" % dimension)

    if (apiExpDimRef := apiExpDim.newExpDimRef(sf=spectrometerFrequency,
                                               isotopeCodes=isotopeCodes,
                                               measurementType='Shift',
                                               isFolded=False,
                                               axisCode=axisCode,
                                               unit=axisUnit,
                                               minAliasedFreq=None,
                                               maxAliasedFreq=None,
                                               )
    ) is None:
        raise RuntimeError("Cannot create SpectrumReference for dimension: %s" % dimension)

    if (apiDataDimRef := apiDataDim.newDataDimRef(expDimRef=apiExpDimRef,
                                                  refPoint=0.0,
                                                  refValue=0.0
                                                  )
    ) is None:
        raise RuntimeError("Cannot create SpectrumReference for dimension: %s" % dimension)

    if (result := self.project._data2Obj[apiDataDimRef]) is None:
        raise RuntimeError("Cannot create SpectrumReference for dimension: %s" % dimension)

    return result


#EJB 20181205: moved to Spectrum
# Spectrum.newSpectrumReference = _newSpectrumReference
# del _newSpectrumReference


# Notifiers:
# TODO: Do we really need this?
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
