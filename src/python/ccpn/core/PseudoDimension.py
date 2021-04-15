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
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
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
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import SampledDataDim as ApiSampledDataDim
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import ExpDimRef as ApiExpDimRef


class PseudoDimension(AbstractWrapperObject):
    """ADVANCED. A sampled Spectrum axis with non-gridded values. Used to describe
    sampled-value axes in pseudo-2D and nD experiments, such as the time delay axis for T1
    experiments."""

    #: Short class name, for PID.
    shortClassName = 'SD'
    # Attribute it necessary as subclasses must use superclass className
    className = 'PseudoDimension'

    _parentClass = Spectrum

    # Type of dimension. Always 'Freq' for frequency (Fourier transformed) dimension
    dimensionType = 'Sampled'

    #: Name of plural link to instances of class
    _pluralLinkName = 'pseudoDimensions'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiSampledDataDim._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiSampledDataDim(self) -> ApiSampledDataDim:
        """ CCPN DataSource matching Spectrum"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """object identifier, used for id"""

        return str(self._wrappedData.dim)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData.dim,)

    @property
    def _parent(self) -> Spectrum:
        """Spectrum containing PseudoDimension."""
        return self._project._data2Obj[self._wrappedData.dataSource]

    spectrum = _parent

    @property
    def dimension(self) -> int:
        """dimension number"""
        return self._wrappedData.dim

    @property
    def pointCount(self) -> int:
        """dimension number"""
        return self._wrappedData.numPoints

    @property
    def axisCode(self) -> str:
        """PseudoDimension axisCode """

        expDimRef = self._wrappedData.expDim.findFirstExpDimRef(serial=1)
        return expDimRef and expDimRef.axisCode

    @axisCode.setter
    def axisCode(self, value: str):
        expDimRef = self._wrappedData.expDim.findFirstExpDimRef(serial=1)
        if expDimRef is not None:
            expDimRef.axisCode = value

    @property
    def axisParameter(self) -> str:
        """Name of the condition or parameter that is varied along the axis.
        Use 'sample' if samples are different for each point on the dimension"""
        return self._wrappedData.conditionVaried

    @axisParameter.setter
    def axisParameter(self, value: str):
        self._wrappedData.conditionVaried = value

    @property
    def axisUnit(self) -> str:
        """unit for transformed data using the reference (most commonly 'ppm')"""
        expDimRef = self._wrappedData.expDim.findFirstExpDimRef(serial=1)
        if expDimRef is not None:
            return expDimRef.unit

    @axisUnit.setter
    def axisUnit(self, value: str):
        expDimRef = self._wrappedData.expDim.findFirstExpDimRef(serial=1)
        if expDimRef is not None:
            expDimRef.unit = value

    @property
    def pointValues(self) -> typing.Tuple[float, ...]:
        """point values for PseudoDimension)."""
        return tuple(self._wrappedData.pointValues)

    @pointValues.setter
    def pointValues(self, value: typing.Sequence) -> tuple:
        self._wrappedData.pointValues = value

    @property
    def pointErrors(self) -> typing.Tuple[float, ...]:
        """point errors for PseudoDimension)."""
        return tuple(self._wrappedData.pointErrors)

    @pointErrors.setter
    def pointErrors(self, value: typing.Sequence) -> tuple:
        self._wrappedData.pointErrors = value

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Spectrum) -> list:
        """get wrappedData (Nmr.SampledDataDims) for all DataDim children of parent Spectrum"""

        return [x for x in parent._wrappedData.sortedDataDims() if x.className == 'SampledDataDim']


# No 'new' function - PseudoDimensions are made on spectrum load

#=========================================================================================
# Connections to parents:
#=========================================================================================

# Notifiers:
def _expDimRefHasChanged(project: Project, apiExpDimRef: ApiExpDimRef):
    """Refresh PseudoDimension when ExpDimRef has changed"""
    for dataDim in apiExpDimRef.expDim.dataDims:
        if isinstance(dataDim, ApiSampledDataDim):
            project._modifiedApiObject(dataDim)


Project._setupApiNotifier(_expDimRefHasChanged, ApiExpDimRef, '')
del _expDimRefHasChanged
