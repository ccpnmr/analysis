"""Spectrum  class.
Maintains the parameters of a spectrum, including per-dimension/axis values.
Values that are not defined for a given dimension (e.g. sampled dimensions) are given as None.

Dimension identifiers run from 1 to the number of dimensions, i.e. dimensionCount,  (e.g. 1,2,3 for a 3D).
CCPN data the preferred convention is to have the acquisition dimension as dimension 1.

Axes identifiers run from 0 to the dimensionCount-1 (e.g. 0,1,2 for a 3D)
Per-axis values are given in the order data are stored in the spectrum file

The axisCodes are used as an alternative axis identifier. These are unique strings that typically
reflect the isotope on the relevant axis.
By default upon loading a new spectrum, the axisCodes are derived from the isotopeCodes that define
the experimental data for each dimension.
They can match the dimension identifiers in the reference experiment templates, linking a dimension
to the correct reference experiment dimension.
They are also used to automatically map spectrum display-axes between different spectra on a first
character basis.
Axes that are linked by a one-bond magnetisation transfer could be given a lower-case suffix to
show the nucleus bound to. Duplicate axis names should be distinguished by a numerical suffix.
The rules are best illustrated by example:

Experiment                          axisCodes

15N-NOESY-HSQC OR 15N-HSQC-NOESY:   Hn, Nh, H
4D HCCH-TOCSY                       Hc, Ch, Hc1, Ch1
HNCA/CB                             H, N, C
HNCO                                H, N, CO
HCACO                               H, CA, CO
3D proton NOESY-TOCSY               H, H1, H2

1D Bromine NMR                      Br
19F-13C-HSQC                        Fc, Cf

Useful reordering methods exist to get dimensional/axis parameters in a particular order, i.e.:
getByDimension(), setByDimension(), getByAxisCode(), setByAxisCode()
See doc strings of these methods for detailed documentation

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
__dateModified__ = "$dateModified: 2021-06-28 19:12:26 +0100 (Mon, June 28, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import sys
from typing import Sequence, Tuple, Optional, Union, List
from functools import partial
from itertools import permutations
import numpy

from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpnmodel.ccpncore.api.ccp.general import DataLocation

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.lib import Pid

import ccpn.core.lib.SpectrumLib as specLib
from ccpn.core.lib.SpectrumLib import MagnetisationTransferTuple, _getProjection, getDefaultSpectrumColours
from ccpn.core.lib.SpectrumLib import _includeInDimensionalCopy, _includeInCopy, _includeInCopyList, checkSpectrumPropertyValue

from ccpn.core.lib.ContextManagers import \
    newObject, deleteObject, ccpNmrV3CoreSimple, \
    undoStackBlocking, renameObject, undoBlock, notificationBlanking, \
    ccpNmrV3CoreSetter, inactivity, undoBlockWithoutSideBar

from ccpn.core.lib.DataStore import DataStore, DataStoreTrait

from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import \
    getDataFormats, getSpectrumDataSource, checkPathForSpectrumFormats, DataSourceTrait
from ccpn.core.lib.SpectrumDataSources.EmptySpectrumDataSource import EmptySpectrumDataSource
from ccpn.core.lib.Cache import cached

from ccpn.core.lib.PeakPickers.PeakPickerABC import PeakPickerTrait

from ccpn.util.traits.CcpNmrJson import CcpNmrJson, jsonHandler
from ccpn.util.traits.CcpNmrTraits import Int, Float, Instance, Any
from ccpn.core.lib.SpectrumLib import SpectrumDimensionTrait

from ccpn.framework.PathsAndUrls import CCPN_STATE_DIRECTORY

from ccpn.util.Constants import SCALETOLERANCE
from ccpn.util.Common import isIterable, _getObjectsByPids
from ccpn.core.lib.AxisCodeLib import getAxisCodeMatch
from ccpn.util.Logging import getLogger
from ccpn.util.decorators import logCommand, singleton
from ccpn.util.Path import Path, aPath


# updated ccpnInternal settings
INCLUDEPOSITIVECONTOURS = 'includePositiveContours'
INCLUDENEGATIVECONTOURS = 'includeNegativeContours'
PREFERREDAXISORDERING = 'preferredAxisOrdering'
SERIESITEMS = '_seriesItems'
DISPLAYFOLDEDCONTOURS = 'displayFoldedContours'

MAXALIASINGRANGE = 3

#=========================================================================================
# Spectrum class
#=========================================================================================

class Spectrum(AbstractWrapperObject, CcpNmrJson):
    """A Spectrum object contains all the stored properties of an NMR spectrum, as well as the
    path to the NMR (binary) data file. The Spectrum object has methods to get the binary data
    as numpy arrays.
    """
    #-----------------------------------------------------------------------------------------

    #: Short class name, for PID.
    shortClassName = 'SP'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Spectrum'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'spectra'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = Nmr.DataSource._metaclass.qualifiedName()

    _referenceSpectrumHit = None
    _snr = None
    #-----------------------------------------------------------------------------------------

    # 'local' definitions of constants; defining defs in SpectrumLib to prevent circular imports
    # elsewhere
    MAXDIM = specLib.MAXDIM  # 8  # Maximum dimensionality

    X_AXIS = specLib.X_AXIS  # 0
    Y_AXIS = specLib.Y_AXIS  # 1
    Z_AXIS = specLib.Z_AXIS  # 2
    A_AXIS = specLib.A_AXIS  # 3
    B_AXIS = specLib.B_AXIS  # 4
    C_AXIS = specLib.C_AXIS  # 5
    D_AXIS = specLib.D_AXIS  # 6
    E_AXIS = specLib.E_AXIS  # 7
    UNDEFINED_AXIS = specLib.Y_AXIS  # 8
    axisNames = specLib.axisNames

    X_DIM = specLib.X_DIM  # 1
    Y_DIM = specLib.Y_DIM  # 2
    Z_DIM = specLib.Z_DIM  # 3
    A_DIM = specLib.A_DIM  # 4
    B_DIM = specLib.B_DIM  # 5
    C_DIM = specLib.C_DIM  # 6
    D_DIM = specLib.D_DIM  # 7
    E_DIM = specLib.E_DIM  # 8

    #-----------------------------------------------------------------------------------------
    # Internal NameSpace  and other definitions
    #-----------------------------------------------------------------------------------------

    # Key for storing the dataStore info in the Ccpn internal parameter store
    _DATASTORE_KEY = '_dataStore'
    _REFERENCESUBSANCESCACHE = '_referenceSubstances'

    _AdditionalAttribute = 'AdditionalAttribute'
    _ReferenceSubstancesPids = '_ReferenceSubstancesPids'

    version = 1.0  # for json saving

    #-----------------------------------------------------------------------------------------
    # Attributes of the data structure
    #-----------------------------------------------------------------------------------------

    @property
    def peakLists(self):
        """STUB: hot-fixed later"""
        return ()

    @property
    def multipletLists(self):
        """STUB: hot-fixed later"""
        return ()

    @property
    def integralLists(self):
        """STUB: hot-fixed later"""
        return ()

    @property
    def spectrumViews(self):
        """STUB: hot-fixed later"""
        return ()

    @property
    def chemicalShiftList(self):
        """STUB: hot-fixed later"""
        return None

    @property
    def spectrumReferences(self) -> list:
        """list of spectrumReferences objects
        STUB: hot-fixed later
        """
        return []

    @property
    def spectrumDimensions(self) -> list:
        """:return A list with the spectrum dimension (== SpectrumReference) instances
        """
        from ccpn.core.SpectrumReference import SpectrumReference
        return self._getChildrenByClass(SpectrumReference)

    @property
    def spectrumHits(self) -> list:
        """STUB: hot-fixed later"""
        return None

    @property
    def sample(self):
        """STUB: hot-fixed later"""
        return None

    # Inherited from AbstractWrapperObject
    # @property
    # def project(self) -> 'Project':
    #     """The Project (root)containing the object."""
    #     return self._project

    @property
    def _parent(self) -> Project:
        """Parent (containing) object."""
        return self._project

    #-----------------------------------------------------------------------------------------

    def __init__(self, project: Project, wrappedData: Nmr.DataSource):

        # super().__init__(project, wrappedData)
        CcpNmrJson.__init__(self)
        AbstractWrapperObject.__init__(self, project, wrappedData)

        # 1D data references
        self._intensities = None
        self._positions = None

        self.doubleCrosshairOffsets = self.dimensionCount * [0]  # TBD: do we need this to be a property?
        self.showDoubleCrosshair = False
        self._scaleChanged = False
    #-----------------------------------------------------------------------------------------
    # end __init__
    #-----------------------------------------------------------------------------------------

    # References to DataStore / DataSource instances for filePath manipulation and (binary) data reading;
    _dataStore = DataStoreTrait(default_value = None, read_only = True).tag(
                                saveToJson = True,
                                info = """
                                A DataStore instance encoding the path and dataFormat of the (binary) spectrum data.
                                None indicates no spectrum data file path has been defined"""
                                )

    # CCPNINTERNAL: Also used in PeakPickers
    _dataSource = DataSourceTrait(default_value = None, read_only = True).tag(
                                  saveToJson = True,
                                  info = """
                                  A SpectrumDataSource instance for reading (writing) of the (binary) spectrum data.
                                  None indicates no valid spectrum data file has been defined""")

    _peakPicker = PeakPickerTrait(default_value = None).tag(
                                  saveToJson = True,
                                  info = "A PeakPicker instance")

    @property
    def peakPicker(self):
        """A peakPicker instance for region picking in this spectrum.
        None indicates no valid peakPicker has been defined
        """
        from ccpn.core.lib.SpectrumLib import _createPeakPicker

        if not self._peakPicker:
            _peakPicker = _createPeakPicker(self)
            # automatically store in the spectrum internal store
            if _peakPicker:
                with undoBlockWithoutSideBar():
                    self._peakPicker = _peakPicker
                    self._peakPicker._storeAttributes()

        return self._peakPicker

    #-----------------------------------------------------------------------------------------
    # Spectrum properties
    #-----------------------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """short form of name, used for id"""
        return self._wrappedData.name

    @name.setter
    def name(self, value: str):
        """set name of Spectrum."""
        self.rename(value)

    @property
    def dimensionCount(self) -> int:
        """Number of dimensions in spectrum"""
        return self._wrappedData.numDim

    @property
    def dimensions(self) -> tuple:
        """Convenience: tuple of length dimensionCount with dimension integers (1-based); e.g. (1,2,3,..).
        Useful for mapping axisCodes: eg: self.getByAxisCodes('dimensions', ['N','C','H'])
        """
        return tuple(range(1, self.dimensionCount + 1))

    @property
    def axes(self) -> tuple:
        """Convenience: tuple of length dimensionCount with axes integers (0-based); e.g. (0,1,2,3).
        Useful for mapping axisCodes: eg: self.getByAxisCodes('axes', ['N','C','H'])
        """
        return tuple(range(0, self.dimensionCount))

    @property
    def axisTriples(self) -> tuple:
        """Convenience: return a tuple of triples (axis, axisCode, dimension) for each dimension

        Useful for iterating over axis codes; eg in an H-N-CO ordered spectrum
            for axis, axisCode, dimension in self.getByAxisCodes('axisTriples', ('N','C','H'), exactMatch=False)

            would yield:
                (1, 'N', 2)
                (2, 'CO', 3)
                (0, 'H', 1)
        """
        return tuple(z for z in zip(self.axes, self.axisCodes, self.dimensions))

    @property
    @_includeInCopy
    def positiveContourCount(self) -> int:
        """number of positive contours to draw"""
        return self._wrappedData.positiveContourCount

    @positiveContourCount.setter
    def positiveContourCount(self, value):
        self._wrappedData.positiveContourCount = value

    @property
    @_includeInCopy
    def positiveContourBase(self) -> float:
        """base level of positive contours"""
        return self._wrappedData.positiveContourBase

    @positiveContourBase.setter
    def positiveContourBase(self, value):
        self._wrappedData.positiveContourBase = value

    @property
    @_includeInCopy
    def positiveContourFactor(self) -> float:
        """level multiplier for positive contours"""
        return self._wrappedData.positiveContourFactor

    @positiveContourFactor.setter
    def positiveContourFactor(self, value):
        self._wrappedData.positiveContourFactor = value

    @property
    @_includeInCopy
    def positiveContourColour(self) -> str:
        """colour of positive contours"""
        return self._wrappedData.positiveContourColour

    @positiveContourColour.setter
    def positiveContourColour(self, value):
        self._wrappedData.positiveContourColour = value

    @property
    @_includeInCopy
    def includePositiveContours(self):
        """Include flag for the positive contours
        """
        result = self._getInternalParameter(INCLUDEPOSITIVECONTOURS)
        if result is None:
            # default to True
            return True
        return result

    @includePositiveContours.setter
    def includePositiveContours(self, value: bool):
        """Include flag for the positive contours
        """
        if not isinstance(value, bool):
            raise ValueError("Spectrum.includePositiveContours: must be True/False")

        self._setInternalParameter(INCLUDEPOSITIVECONTOURS, value)

    @property
    @_includeInCopy
    def negativeContourCount(self) -> int:
        """number of negative contours to draw"""
        return self._wrappedData.negativeContourCount

    @negativeContourCount.setter
    def negativeContourCount(self, value):
        self._wrappedData.negativeContourCount = value

    @property
    @_includeInCopy
    def negativeContourBase(self) -> float:
        """base level of negative contours"""
        return self._wrappedData.negativeContourBase

    @negativeContourBase.setter
    def negativeContourBase(self, value):
        self._wrappedData.negativeContourBase = value

    @property
    @_includeInCopy
    def negativeContourFactor(self) -> float:
        """level multiplier for negative contours"""
        return self._wrappedData.negativeContourFactor

    @negativeContourFactor.setter
    def negativeContourFactor(self, value):
        self._wrappedData.negativeContourFactor = value

    @property
    @_includeInCopy
    def negativeContourColour(self) -> str:
        """colour of negative contours"""
        return self._wrappedData.negativeContourColour

    @negativeContourColour.setter
    def negativeContourColour(self, value):
        self._wrappedData.negativeContourColour = value

    @property
    @_includeInCopy
    def includeNegativeContours(self):
        """Include flag for the negative contours
        """
        result = self._getInternalParameter(INCLUDENEGATIVECONTOURS)
        if result is None:
            # default to True
            return True
        return result

    @includeNegativeContours.setter
    def includeNegativeContours(self, value: bool):
        """Include flag for the negative contours
        """
        if not isinstance(value, bool):
            raise ValueError("Spectrum.includeNegativeContours: must be True/False")

        self._setInternalParameter(INCLUDENEGATIVECONTOURS, value)

    @property
    @_includeInCopy
    def sliceColour(self) -> str:
        """colour of 1D slices
        """
        return self._wrappedData.sliceColour

    @sliceColour.setter
    def sliceColour(self, value):
        self._wrappedData.sliceColour = value
        # for spectrumView in self.spectrumViews:
        #     spectrumView.setSliceColour()  # ejb - update colour here

    @property
    @_includeInCopy
    def scale(self) -> float:
        """Scaling factor for data in the spectrum.
        """
        value = self._wrappedData.scale
        if value is None:
            getLogger().warning('Scaling {} changed from None to 1.0'.format(self))
            value = 1.0
        if -SCALETOLERANCE < value < SCALETOLERANCE:
            getLogger().warning('Scaling {} by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        return value

    @scale.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSimple()
    def scale(self, value: Union[float, int, None]):
        if value is None:
            getLogger().warning('Scaling {} changed from None to 1.0'.format(self))
            value = 1.0

        if not isinstance(value, (float, int)):
            raise TypeError('Spectrum.scale {} must be a float or integer'.format(self))

        if value is not None and -SCALETOLERANCE < value < SCALETOLERANCE:
            # Display a warning, but allow to be set
            getLogger().warning('Scaling {} by minimum tolerance (±{})'.format(self, SCALETOLERANCE))

        self._scaleChanged = True
        if value is None:
            self._wrappedData.scale = None
        else:
            self._wrappedData.scale = float(value)

        if self.dimensionCount == 1 and self._intensities is not None:
            # some 1D data were read before; update the intensities as the scale has changed
            self._intensities = self.getSliceData()

    @property
    @_includeInCopy
    def spinningRate(self) -> float:
        """NMR tube spinning rate (in Hz)
        """
        return self._wrappedData.experiment.spinningRate

    @spinningRate.setter
    def spinningRate(self, value: float):
        self._wrappedData.experiment.spinningRate = value

    @property
    @_includeInCopy
    def noiseLevel(self) -> (float, None):
        """Noise level for the spectrum
        """
        noise = self._wrappedData.noiseLevel
        if noise is None:
            getLogger().debug2('Returning noiseLevel=None')
        return noise

    @noiseLevel.setter
    def noiseLevel(self, value: float):
        self._wrappedData.noiseLevel = value

    @property
    @_includeInCopy
    def negativeNoiseLevel(self) -> float:
        """Negative noise level value. Stored in Internal"""
        propertyName = sys._getframe().f_code.co_name
        value = self.getParameter(self._AdditionalAttribute, propertyName)
        return value

    @negativeNoiseLevel.setter
    def negativeNoiseLevel(self, value):
        """Stored in Internal """
        propertyName = sys._getframe().f_code.co_name
        self.setParameter(self._AdditionalAttribute, propertyName, value)

    @property
    def synonym(self) -> (str, None):
        """Systematic experiment type descriptor (CCPN system)."""
        refExperiment = self._wrappedData.experiment.refExperiment
        if refExperiment is None:
            return None
        else:
            return refExperiment.synonym

    @property
    @_includeInCopy
    def experimentType(self) -> (str, None):
        """Systematic experiment type descriptor (CCPN system)."""
        refExperiment = self._wrappedData.experiment.refExperiment
        if refExperiment is None:
            return None
        else:
            return refExperiment.name

    @experimentType.setter
    def experimentType(self, value: str):
        from ccpn.core.lib.SpectrumLib import _setApiExpTransfers, _setApiRefExperiment, _clearLinkToRefExp

        if value is None:
            self._wrappedData.experiment.refExperiment = None
            self.experimentName = None
            _clearLinkToRefExp(self._wrappedData.experiment)
            return
        # nmrExpPrototype = self._wrappedData.root.findFirstNmrExpPrototype(name=value) # Why not findFirst instead of looping all sortedNmrExpPrototypes
        for nmrExpPrototype in self._wrappedData.root.sortedNmrExpPrototypes():
            for refExperiment in nmrExpPrototype.sortedRefExperiments():
                if refExperiment.name == value:
                    # set API RefExperiment and ExpTransfer
                    _setApiRefExperiment(self._wrappedData.experiment, refExperiment)
                    _setApiExpTransfers(self._wrappedData.experiment)
                    synonym = refExperiment.synonym
                    if synonym:
                        self.experimentName = synonym
                    return
        # nothing found - error:
        raise ValueError('No reference experiment matches name "%s"' % value)

    @property
    def experiment(self):
        """Return the experiment assigned to the spectrum
        """
        return self._wrappedData.experiment

    @property
    @_includeInCopy
    def experimentName(self) -> str:
        """Common experiment type descriptor (May not be unique).
        """
        return self._wrappedData.experiment.name

    @experimentName.setter
    def experimentName(self, value):
        # force to a string
        # because: reading from .nef files extracts the name from the end of the experiment_type in nef reader
        #           which is not wrapped with quotes, so defaults to an int if it can?
        self._wrappedData.experiment.name = str(value)

    @property
    def filePath(self) -> Optional[str]:
        """Path to NMR data file; can contain redirections (e.g. $DATA)
        """
        if self._dataStore is None:
            raise RuntimeError('dataStore not defined')
        return str(self._dataStore.path)

    @filePath.setter
    @ccpNmrV3CoreSetter()
    def filePath(self, value: str):

        if self._dataStore is None:
            raise RuntimeError('dataStore not defined')

        if value is None:
            self._clearCache()
            self._dataStore.path = None
            self.setTraitValue('_dataStore', None, force=True)
            return

        newDataStore = DataStore.newFromPath(path=value, dataFormat=self.dataFormat)
        newDataStore.spectrum = self

        try:
            newDataSource = self._getDataSource(newDataStore)
        except:
            raise ValueError('Spectrum.filePath: incompatible file "%s"' % value)

        # we found a valid new file
        self.setTraitValue('_dataSource', newDataSource, force=True)
        self.setTraitValue('_dataStore', newDataStore, force=True)
        self._dataStore._saveInternal()
        self._clearCache()
        self._saveSpectrumMetaData()

    def reload(self):
        """Reload the spectrum defined by filePath
        """
        # setting filePath will re-initialiase a dataSource instance
        _filePath = self.filePath
        self.filePath  = _filePath
        self._dataSource.exportToSpectrum(self, includePath=False)

    @property
    def path(self):
        """return a Path instance defining the absolute path of filePath
        """
        if self._dataStore is None:
            raise RuntimeError('dataStore not defined')
        return self._dataStore.aPath()

    def hasValidPath(self) -> bool:
        """Return true if the spectrum's dataSource currently defines an valid dataSource object
        with a valid path defined
        """
        return self._dataSource is not None and self._dataSource.hasValidPath()

    def isEmptySpectrum(self):
        """Return True if instance refers to an empty spectrum; i.e. as in without actual spectral data"
        """
        if self._dataStore is None:
            raise RuntimeError('dataStore not defined')
        return self._dataStore.dataFormat == EmptySpectrumDataSource.dataFormat

    @property
    def dataFormat(self):
        """Return the spectrum data-format identifier (e.g. Hdf5, NMRPipe)
        """
        if self._dataStore is None:
            raise RuntimeError('dataStore not defined')

        return self._dataStore.dataFormat

    #-----------------------------------------------------------------------------------------
    # Dimensional Attributes
    #-----------------------------------------------------------------------------------------

    def _setDimensionalAttributes(self, attributeName: str, value: (list, tuple)):
        """Conveniance function set the spectrumReference.attributeName to the items of value
        Assumes all checks have been done
        """
        specDims = self.spectrumDimensions  # local copy to avoid getting it N-times
        for idx, val in enumerate(value):
            setattr(specDims[idx], attributeName, val)

    def _getDimensionalAttributes(self, attributeName: str) -> list:
        """Conveniance function get the values for each spectrumReference.attributeName
        """
        return [getattr(specDim, attributeName) for specDim in self.spectrumDimensions]

    @property
    @_includeInDimensionalCopy
    def pointCounts(self) -> List[int]:
        """Number of points per dimension"""
        return self._getDimensionalAttributes('pointCount')

    @pointCounts.setter
    @checkSpectrumPropertyValue(iterable=True, types=(int,float))
    def pointCounts(self, value: Sequence):
        self._setDimensionalAttributes('pointCount', value)

    @property
    @_includeInDimensionalCopy
    def totalPointCounts(self) -> List[int]:
        """Total number of points per dimension; i.e. twice pointCounts in case of complex data"""
        result = self.pointCounts
        for axis, isC in enumerate(self.isComplex):
            if isC:
                result[axis] *= 2
        return result

    @property
    @_includeInDimensionalCopy
    def isComplex(self) -> List[bool]:
        """Boolean denoting Complex data per dimension"""
        return self._getDimensionalAttributes('isComplex')

    @isComplex.setter
    @checkSpectrumPropertyValue(iterable=True, types=(bool, int, float))
    def isComplex(self, value: Sequence):
        self._setDimensionalAttributes('isComplex', value)

    @property
    @_includeInDimensionalCopy
    def isAquisition(self) -> List[bool]:
        """Boolean per dimension denoting if it is the aquisition dimension"""
        return self._getDimensionalAttributes('isAcquisition')

    @isAquisition.setter
    @checkSpectrumPropertyValue(iterable=True, types=(bool, int, float))
    def isAquisition(self, value: Sequence):
        trues = [val for val in value if val == True]
        if len(trues) > 1:
            raise ValueError('Spectrum.isAquisition: expected zero or one dimension; got %r' % value)
        self._setDimensionalAttributes('isAcquisition', value)

    @property
    @_includeInDimensionalCopy
    def axisCodes(self) -> List[Optional[str]]:
        """List of an unique axisCode per dimension"""
        return self._getDimensionalAttributes('axisCode')

    @axisCodes.setter
    @checkSpectrumPropertyValue(iterable=True, unique=True, allowNone=True, types=(str,))
    def axisCodes(self, value):
        self._setDimensionalAttributes('axisCode', value)

    @property
    @_includeInCopy
    def acquisitionAxisCode(self) -> Optional[str]:
        """Axis code of acquisition axis - None if not known"""
        trues = [idx for idx, val in enumerate(self.isAquisition) if val == True]
        if len(trues) == 0:
            return None
        elif len(trues) == 1:
            return self.axisCodes[trues[0]]
        else:
            raise RuntimeError(
        'Spectrum.aquisitionAxisCode: this should not happen; more then one dimension defined as acquisition dimension')

    @property
    def dimensionTypes(self) -> List[Optional[str]]:
        """Dimension types ('Time' / 'Frequency' / 'Sampled') per dimension"""
        return self._getDimensionalAttributes('dimensionType')

    @dimensionTypes.setter
    @checkSpectrumPropertyValue(iterable=True, allowNone=True, types=(str,))
    def dimensionTypes(self, value):
        self._setDimensionalAttributes('dimensionType', value)

    @property
    @_includeInDimensionalCopy
    def spectralWidthsHz(self) -> List[float]:
        """spectral width (in Hz) per dimension"""
        return self._getDimensionalAttributes('spectralWidthHz')

    @spectralWidthsHz.setter
    @checkSpectrumPropertyValue(iterable=True, types=(float, int))
    def spectralWidthsHz(self, value: Sequence):
        self._setDimensionalAttributes('spectralWidthHz', value)

    @property
    @_includeInDimensionalCopy
    def spectralWidths(self) -> List[float]:
        """spectral width (in ppm) per dimension """
        return self._getDimensionalAttributes('spectralWidth')

    @spectralWidths.setter
    @checkSpectrumPropertyValue(iterable=True, types=(float, int))
    def spectralWidths(self, value):
        self._setDimensionalAttributes('spectralWidth', value)

    @property
    def valuesPerPoint(self) -> List[Optional[float]]:
        """valuePerPoint for each dimension:
        in ppm for Frequency dimensions
        in time units (seconds) for Time (Fid) dimensions
        None for sampled dimensions
        """
        result = []
        for axis, dimType in enumerate(self.dimensionTypes):

            if dimType == specLib.DIMENSION_FREQUENCY:
                valuePerPoint = self.spectralWidths[axis] / self.pointCounts[axis]

            elif dimType == specLib.DIMENSION_TIME:
                # valuePerPoint is dwell time
                valuePerPoint = 1.0 / self.spectralWidthsHz[axis] if self.isComplex[axis] \
                                 else 0.5 / self.spectralWidthsHz[axis]
            else:
                valuePerPoint = None

            result.append(valuePerPoint)

        # for dataDim in self._wrappedData.sortedDataDims():
        #     if hasattr(dataDim, 'primaryDataDimRef'):
        #         # FreqDataDim - get ppm valuePerPoint
        #         ddr = dataDim.primaryDataDimRef
        #         valuePerPoint = ddr and ddr.valuePerPoint
        #     elif hasattr(dataDim, 'valuePerPoint'):
        #         # FidDataDim - get time valuePerPoint
        #         valuePerPoint = dataDim.valuePerPoint
        #     else:
        #         # Sampled DataDim - return None
        #         valuePerPoint = None

        return result

    @property
    @_includeInDimensionalCopy
    def phases0(self) -> List[Optional[float]]:
        """Zero-order phase correction (or None), per dimension"""
        return self._getDimensionalAttributes('phase0')

    @phases0.setter
    @checkSpectrumPropertyValue(iterable=True, allowNone=True, types=(float, int))
    def phases0(self, value: Sequence):
        self._setDimensionalAttributes('phase0', value)
        # self._setStdDataDimValue('phase0', value)

    @property
    @_includeInDimensionalCopy
    def phases1(self) -> List[Optional[float]]:
        """First-order phase correction (or None) per dimension"""
        return self._getDimensionalAttributes('phase1')

    @phases1.setter
    @checkSpectrumPropertyValue(iterable=True, allowNone=True, types=(float, int))
    def phases1(self, value: Sequence):
        self._setDimensionalAttributes('phase1', value)

    @property
    @_includeInDimensionalCopy
    def windowFunctions(self) -> List[Optional[str]]:
        """Window function name (or None) per dimension
        e.g. 'EM', 'GM', 'SINE', 'QSINE', .... (defined in SpectrumLib.WINDOW_FUNCTIONS)
        """
        return self._getDimensionalAttributes('windowFunction')

    @windowFunctions.setter
    @checkSpectrumPropertyValue(iterable=True, allowNone=True, types=(str,), enumerated=specLib.WINDOW_FUNCTIONS)
    def windowFunctions(self, value: Sequence):
        self._setDimensionalAttributes('windowFunction', value)

    @property
    @_includeInDimensionalCopy
    def lorentzianBroadenings(self) -> List[Optional[float]]:
        """Lorenzian broadening per dimension (in Hz)"""
        return self._getDimensionalAttributes('lorentzianBroadening')

    @lorentzianBroadenings.setter
    @checkSpectrumPropertyValue(iterable=True, allowNone=True, types=(float, int))
    def lorentzianBroadenings(self, value: Sequence):
        self._setDimensionalAttributes('lorentzianBroadening', value)

    @property
    @_includeInDimensionalCopy
    def gaussianBroadenings(self) -> List[Optional[float]]:
        """Gaussian broadening per dimension"""
        return self._getDimensionalAttributes('gaussianBroadening')

    @gaussianBroadenings.setter
    @checkSpectrumPropertyValue(iterable=True, allowNone=True, types=(float, int))
    def gaussianBroadenings(self, value: Sequence):
        self._setDimensionalAttributes('gaussianBroadening', value)

    @property
    @_includeInDimensionalCopy
    def sineWindowShifts(self) -> List[Optional[float]]:
        """Shift of sine/sine-square window function per dimension (in degrees)"""
        return self._getDimensionalAttributes('sineWindowShift')

    @sineWindowShifts.setter
    @checkSpectrumPropertyValue(iterable=True, allowNone=True, types=(float, int))
    def sineWindowShifts(self, value: Sequence):
        self._setDimensionalAttributes('sineWindowShift', value)

    @property
    @_includeInDimensionalCopy
    def spectrometerFrequencies(self) -> List[float]:
        """List of spectrometer frequency for each dimension"""
        return self._getDimensionalAttributes('spectrometerFrequency')

    @spectrometerFrequencies.setter
    @checkSpectrumPropertyValue(iterable=True, types=(float, int))
    def spectrometerFrequencies(self, value):
        self._setDimensionalAttributes('spectrometerFrequency', value)

    @property
    @_includeInDimensionalCopy
    def measurementTypes(self) -> List[Optional[str]]:
        """Type of value being measured, per dimension.
        In normal cases the measurementType will be 'Shift', but other values might be
        'MQSHift' (for multiple quantum axes), JCoupling (for J-resolved experiments),
        'T1', 'T2', --- defined SpectrumLib.MEASUREMENT_TYPES
        """
        return self._getDimensionalAttributes('measurementType')

    @measurementTypes.setter
    @checkSpectrumPropertyValue(iterable=True, types=(str,), enumerated=specLib.MEASUREMENT_TYPES)
    def measurementTypes(self, value):
        self._setDimensionalAttributes('measurementType', value)

    @property
    @_includeInDimensionalCopy
    def isotopeCodes(self) -> List[str]:
        """isotopeCode per dimension - None if not known"""
        return self._getDimensionalAttributes('isotopeCode')

    @isotopeCodes.setter
    @checkSpectrumPropertyValue(iterable=True, allowNone=True, types=(str,))
    def isotopeCodes(self, value: Sequence):
        self._setDimensionalAttributes('isotopeCode', value)

    @property
    @_includeInDimensionalCopy
    def referenceExperimentDimensions(self) -> Tuple[Optional[str], ...]:
        """dimensions of reference experiment - None if no code"""
        result = []
        for dataDim in self._wrappedData.sortedDataDims():
            expDim = dataDim.expDim
            if expDim is None:
                result.append(None)
            else:
                referenceExperimentDimension = (expDim.ccpnInternalData and expDim.ccpnInternalData.get('expDimToRefExpDim')) or None
                result.append(referenceExperimentDimension)

        return tuple(result)

    @referenceExperimentDimensions.setter
    @ccpNmrV3CoreSetter()
    @checkSpectrumPropertyValue(iterable=True, unique=True, allowNone=True, types=(str,))
    def referenceExperimentDimensions(self, values: Sequence):
        apiDataSource = self._wrappedData

        # if not isinstance(values, (tuple, list)):
        #     raise ValueError('referenceExperimentDimensions must be a list or tuple')
        # if len(values) != apiDataSource.numDim:
        #     raise ValueError('referenceExperimentDimensions must have length %s, was %s' % (apiDataSource.numDim, values))
        # if not all(isinstance(dimVal, (str, type(None))) for dimVal in values):
        #     raise ValueError('referenceExperimentDimensions must be str, None')

        # _vals = [val for val in values if val is not None]
        # if len(_vals) != len(set(_vals)):
        #     raise ValueError('referenceExperimentDimensions must be unique')

        #TODO: use self.spectrumReferences and its attributes/methods (if needed add method)
        for ii, (dataDim, val) in enumerate(zip(apiDataSource.sortedDataDims(), values)):
            expDim = dataDim.expDim
            if expDim is None and val is not None:
                raise ValueError('Cannot set referenceExperimentDimension %s in dimension %s' % (val, ii + 1))
            else:
                _update = {'expDimToRefExpDim': val}
                _ccpnInt = expDim.ccpnInternalData
                if _ccpnInt is None:
                    expDim.ccpnInternalData = _update
                else:
                    _expDimCID = expDim.ccpnInternalData.copy()
                    _ccpnInt.update(_update)
                    expDim.ccpnInternalData = _ccpnInt

    def getAvailableReferenceExperimentDimensions(self, _experimentType=None) -> tuple:
        """Return list of available reference experiment dimensions based on spectrum isotopeCodes
        """
        _refExperiment = None
        if _experimentType is not None:
            # search for the named reference experiment
            _refExperiment = self.project._getReferenceExperimentFromType(_experimentType)

        # get the nucleus codes from the current isotope codes
        nCodes = tuple(val.strip('0123456789') for val in self.isotopeCodes)

        # match against the current reference experiment or passed in value
        apiExperiment = self._wrappedData.experiment
        apiRefExperiment = _refExperiment or apiExperiment.refExperiment

        if apiRefExperiment:
            # get the permutations of the axisCodes and nucleusCodes
            axisCodePerms = permutations(apiRefExperiment.axisCodes)
            nucleusPerms = permutations(apiRefExperiment.nucleusCodes)

            # return only those that match the current nucleusCodes (from isotopeCodes)
            result = tuple(ac for ac, nc in zip(axisCodePerms, nucleusPerms) if nCodes == nc)
            return result

        else:
            return ()

    @property
    @_includeInDimensionalCopy
    def foldingModes(self) -> List[Optional[str]]:
        """folding mode (values: 'circular', 'mirror', None), per dimension"""
        return self._getDimensionalAttributes('foldingMode')
        # dd = {True: 'mirror', False: 'circular', None: None}
        # return tuple(dd[x and x.isFolded] for x in self._mainExpDimRefs())

    @foldingModes.setter
    @checkSpectrumPropertyValue(iterable=True, allowNone=True, types=(str,), enumerated=specLib.FOLDING_MODES)
    def foldingModes(self, value):
        self._setDimensionalAttributes('foldingMode', value)

        # dd = {'circular': False, 'mirror': True, None: False}
        #
        # if len(values) != self.dimensionCount:
        #     raise ValueError("Length of %s does not match number of dimensions." % str(values))
        # if not all(isinstance(dimVal, (str, type(None))) and dimVal in dd.keys() for dimVal in values):
        #     raise ValueError("Folding modes must be 'circular', 'mirror', None")
        #
        # self._setExpDimRefAttribute('isFolded', [dd[x] for x in values])

    @property
    @_includeInDimensionalCopy
    def axisUnits(self) -> List[Optional[str]]:
        """Main axis unit (most commonly 'ppm'), per dimension - None if no unique code"""
        return self._getDimensionalAttributes('axisUnit')

    @axisUnits.setter
    @checkSpectrumPropertyValue(iterable=True, allowNone=True, types=(str,))
    def axisUnits(self, value):
        self._setDimensionalAttributes('axisUnit', value)

    @property
    @_includeInDimensionalCopy
    def referencePoints(self) -> List[Optional[float]]:
        """point used for axis (chemical shift) referencing, per dimension."""
        return self._getDimensionalAttributes('referencePoint')

    @referencePoints.setter
    @checkSpectrumPropertyValue(iterable=True, allowNone=False, types=(float, int))
    def referencePoints(self, value):
        self._setDimensionalAttributes('referencePoint', value)

    @property
    @_includeInDimensionalCopy
    def referenceValues(self) -> List[Optional[float]]:
        """ppm-value used for axis (chemical shift) referencing, per dimension."""
        return self._getDimensionalAttributes('referenceValue')

    @referenceValues.setter
    @checkSpectrumPropertyValue(iterable=True, allowNone=False, types=(float, int))
    def referenceValues(self, value):
        self._setDimensionalAttributes('referenceValue', value)

    @property
    @cached(_REFERENCESUBSANCESCACHE, maxItems=5000, debug=False)
    def referenceSubstances(self):
        """
        :return: a list of substances
        """
        pids = self._ccpnInternalData.get(self._ReferenceSubstancesPids) or []
        objs = _getObjectsByPids(self.project, pids)
        return objs

    @referenceSubstances.setter
    def referenceSubstances(self, substances):
        """
        """
        from ccpn.core.Substance import Substance

        pids = [su.pid for su in substances if isinstance(su, Substance)]
        if isinstance(self._ccpnInternalData, dict):
            tempCcpn = self._ccpnInternalData.copy()
            tempCcpn[self._ReferenceSubstancesPids] = pids
            self._ccpnInternalData = tempCcpn
        else:
            raise ValueError("Substance linked spectra CCPN internal must be a dictionary")

    @property
    def referenceSubstance(self):
        """
        Deprecated. See referenceSubstances
        """
        getLogger().warning('spectrum.referenceSubstance is deprecated. Use referenceSubstances instead. ')
        substance = None
        if len(self.referenceSubstances) > 0:
            substance = self.referenceSubstances[-1]
        return substance

    @referenceSubstance.setter
    def referenceSubstance(self, substance):
        getLogger().warning('spectrum.referenceSubstance is deprecated. Use referenceSubstances instead. ')
        self.referenceSubstances = [substance]

    @property
    @_includeInDimensionalCopy
    def assignmentTolerances(self) -> List[Optional[float]]:
        """Assignment tolerance in axis unit (ppm), per dimension"""
        return self._getDimensionalAttributes('assignmentTolerance')

    @assignmentTolerances.setter
    @checkSpectrumPropertyValue(iterable=True, allowNone=True, types=(float, int))
    def assignmentTolerances(self, value):
        self._setDimensionalAttributes('assignmentTolerance', value)

    @property
    def defaultAssignmentTolerances(self) -> List[Optional[float]]:
        """Default assignment tolerances per dimension (in ppm), upward adjusted (if needed) for
        digital resolution
        NB for Time or Sampled dimensions value will be None
        """
        tolerances = [None] * self.dimensionCount
        for ii, dimensionType in enumerate(self.dimensionTypes):
            if dimensionType == specLib.DIMENSION_FREQUENCY:
                tolerance = specLib.getAssignmentTolerances(self.isotopeCodes[ii])
                tolerances[ii] = max(tolerance, self.spectralWidths[ii] / self.pointCounts[ii])
        #
        return tolerances

    @property
    @_includeInDimensionalCopy
    def aliasingLimits(self) -> Tuple[tuple, ...]:
        """Tuple of tuples of sorted(minAliasingLimit, maxAliasingLimit) per dimension
        """
        minVals = self._getDimensionalAttributes('minAliasedFrequency')
        maxVals = self._getDimensionalAttributes('maxAliasedFrequency')
        return tuple(tuple(sorted(t)) for t in zip(minVals, maxVals))

        # result = [(x and x.minAliasedFreq, x and x.maxAliasedFreq) for x in self._mainExpDimRefs()]
        #
        # if any(None in tt for tt in result):
        #     # Some values not set, or missing. Try to get them as spectrum limits
        #     for ii, dataDimRef in enumerate(self._mainDataDimRefs()):
        #         if None in result[ii] and dataDimRef is not None:
        #             dataDim = dataDimRef.dataDim
        #             ff = dataDimRef.pointToValue
        #             point1 = 1 - dataDim.pointOffset
        #             result[ii] = tuple(sorted((ff(point1), ff(point1 + dataDim.numPointsOrig))))
        # #
        # return tuple(result)

    @aliasingLimits.setter
    @checkSpectrumPropertyValue(iterable=True, allowNone=False, types=(tuple, list))
    def aliasingLimits(self, value):
        # check that we have iterables with two (min,max) values
        for axis, t in enumerate(value):
            if not isIterable(t) and len(t) != 2:
                raise ValueError('invalid aliasingLimit[%s]; expected (minLimit, maxlimit) but got %r' % (axis, t))
        minVals = [t[0] for t in value]
        maxVals = [t[1] for t in value]
        self._setDimensionalAttributes('minAliasedFrequency', minVals)
        self._setDimensionalAttributes('maxAliasedFrequency', maxVals)

    #     if len(value) != self.dimensionCount:
    #         raise ValueError("length of aliasingLimits must match spectrum dimension, was %s" % value)
    #
    #     expDimRefs = self._mainExpDimRefs()
    #     for ii, tt in enumerate(value):
    #         expDimRef = expDimRefs[ii]
    #         if expDimRef:
    #             if len(tt) != 2:
    #                 raise ValueError("Aliasing limits must have two value (min,max), was %s" % tt)
    #             expDimRef.minAliasedFreq = tt[0]
    #             expDimRef.maxAliasedFreq = tt[1]

    @property
    def spectrumLimits(self) -> List[Tuple[float, float]]:
        """list of tuples of (ppmPoint(1), ppmPoint(n)) for each dimension
        """
        return self._getDimensionalAttributes('limits')
        # ll = []
        # for ii, ddr in enumerate(self._mainDataDimRefs()):
        #     if ddr is None:
        #         ll.append((None, None))
        #     else:
        #         ll.append((ddr.pointToValue(1), ddr.pointToValue(ddr.dataDim.numPoints + 1)))
        # return tuple(ll)

    def get1Dlimits(self):
        """Get the 1D spectrum ppm-limits and the intensity limits
        :return ((ppm1, ppm2), (minValue, maxValue)
        """
        if self.dimensionCount != 1:
            raise RuntimeError('Spectrum.get1Dlimits() is only implemented for 1D spectra')
        ppmLimits = self.spectrumLimits[0]
        sliceData = self.getSliceData()
        minValue = float(min(sliceData))
        maxValue = float(max(sliceData))
        return (ppmLimits, (minValue, maxValue))

    @property
    def axesReversed(self) -> Tuple[Optional[bool], ...]:
        """Return True if the axis is reversed per dimension
        """
        return tuple(self._getDimensionalAttributes('isReversed'))
        # return tuple((x and x.isAxisReversed) for x in self._mainExpDimRefs())

    @property
    def magnetisationTransfers(self) -> Tuple[MagnetisationTransferTuple, ...]:
        """tuple of MagnetisationTransferTuple describing magnetisation transfer between
        the spectrum dimensions.

        MagnetisationTransferTuple is a namedtuple with the fields
        ['dimension1', 'dimension2', 'transferType', 'isIndirect'] of types [int, int, str, bool]
        The dimensions are dimension numbers (one-origin]
        transfertype is one of (in order of increasing priority):
        'onebond', 'Jcoupling', 'Jmultibond', 'relayed', 'relayed-alternate', 'through-space'
        isIndirect is used where there is more than one successive transfer step;
        it is combined with the highest-priority transferType in the transfer path.

        The magnetisationTransfers are deduced from the experimentType and axisCodes.
        Only when the experimentType is unset or does not match any known reference experiment
        magnetisationTransfers are kept separately in the API layer.
        """

        result = []
        apiExperiment = self._wrappedData.experiment
        apiRefExperiment = apiExperiment.refExperiment

        if apiRefExperiment:
            # We should use the refExperiment - if present
            magnetisationTransferDict = apiRefExperiment.magnetisationTransferDict()
            mainExpDimRefs = [dim._expDimRef for dim in self.spectrumReferences]
            refExpDimRefs = [x if x is None else x.refExpDimRef for x in mainExpDimRefs]
            for ii, rxdr in enumerate(refExpDimRefs):
                dim1 = ii + 1
                if rxdr is not None:
                    for jj in range(dim1, len(refExpDimRefs)):
                        rxdr2 = refExpDimRefs[jj]
                        if rxdr2 is not None:
                            tt = magnetisationTransferDict.get(frozenset((rxdr, rxdr2)))
                            if tt:
                                result.append(MagnetisationTransferTuple(dim1, jj + 1, tt[0], tt[1]))

        else:
            # Without a refExperiment use parameters stored in the API (for reproducibility)
            ll = []
            for apiExpTransfer in apiExperiment.expTransfers:
                item = [x.expDim.dim for x in apiExpTransfer.expDimRefs]
                item.sort()
                item.append(apiExpTransfer.transferType)
                item.append(not (apiExpTransfer.isDirect))
                ll.append(item)
            for item in sorted(ll):
                result.append(MagnetisationTransferTuple(*item))

        #
        return tuple(result)

    def _setMagnetisationTransfers(self, value: Tuple[MagnetisationTransferTuple, ...]):
        """Setter for magnetisation transfers

        The magnetisationTransfers are deduced from the experimentType and axisCodes.
        When the experimentType is set this function is a No-op.
        Only when the experimentType is unset or does not match any known reference experiment
        does this function set the magnetisation transfers, and the corresponding values are
        ignored if the experimentType is later set
        """

        apiExperiment = self._wrappedData.experiment
        apiRefExperiment = apiExperiment.refExperiment
        if apiRefExperiment is None:
            for et in apiExperiment.expTransfers:
                et.delete()
            mainExpDimRefs = [dim._expDimRef for dim in self.spectrumReferences]  # self._mainExpDimRefs()
            for tt in value:
                try:
                    dim1, dim2, transferType, isIndirect = tt
                    expDimRefs = (mainExpDimRefs[dim1 - 1], mainExpDimRefs[dim2 - 1])
                except:
                    raise ValueError(
                            "Attempt to set incorrect magnetisationTransfer value %s in spectrum %s"
                            % (tt, self.pid)
                            )
                apiExperiment.newExpTransfer(expDimRefs=expDimRefs, transferType=transferType,
                                             isDirect=(not isIndirect))
        else:
            getLogger().warning(
                    """An attempt to set Spectrum.magnetisationTransfers directly was ignored
                  because the spectrum experimentType was defined.
                  Use axisCodes to set magnetisation transfers instead.""")

    @property
    def intensities(self) -> np.ndarray:
        """ spectral intensities as NumPy array for 1D spectra
        """

        if self.dimensionCount != 1:
            getLogger().warning('Currently this method only works for 1D spectra')
            return np.array([])

        if self._intensities is None:
            self._intensities = self.getSliceData()  # Assignment is Redundant as getSliceData does that;

            # Nevertheless for clarity
            if self._intensities is None:
                getLogger().warning('Unable to get 1D slice data for %s' % self)
                return np.array([])

        return self._intensities

    @intensities.setter
    def intensities(self, value: np.ndarray):
        self._intensities = value

        # NOTE:ED - temporary hack for showing straight the result of intensities change
        for spectrumView in self.spectrumViews:
            spectrumView.refreshData()

    @property
    def positions(self) -> np.array:
        """ spectral region in ppm as NumPy array for 1D spectra """

        if self.dimensionCount != 1:
            getLogger().warning('Currently this method only works for 1D spectra')
            return np.array([])

        if self._positions is None:
            self._positions = self.getPpmArray(dimension=1)

        return self._positions

    @positions.setter
    def positions(self, value):
        # self._scaleChanged = True
        self._positions = value

        # NOTE:ED - temporary hack for showing straight the result of intensities change
        for spectrumView in self.spectrumViews:
            spectrumView.refreshData()

    @property
    @_includeInCopy
    def displayFoldedContours(self):
        """Return whether the folded spectrum contours are to be displayed
        """
        result = self._getInternalParameter(DISPLAYFOLDEDCONTOURS)
        if result is None:
            # default to True
            return True
        return result

    @displayFoldedContours.setter
    def displayFoldedContours(self, value):
        """Set whether the folded spectrum contours are to be displayed
        """
        if not isinstance(value, bool):
            raise ValueError("Spectrum.displayFoldedContours: must be True/False.")

        self._setInternalParameter(DISPLAYFOLDEDCONTOURS, value)

    @property
    def aliasingValues(self) -> Optional[Tuple[Tuple, ...]]:
        """Return a tuple of the aliasing values in each dimension, as multiples of the spectral width.
        This is a derived property from the aliasingLimits.
        """
        _alias = self.aliasingLimits
        _limits = self.spectrumLimits

        values = []
        for alias, lim in zip(_alias, _limits):
            width = abs(max(lim) - min(lim))
            minA, maxA = min(alias), max(alias)
            minLim, maxLim = min(lim), max(lim)
            values.append((int((minA - minLim + width / 2) // width), int((maxA - maxLim + width / 2) // width)))

        return tuple(values)

    @property
    def _seriesItems(self):
        """Return a tuple of the series items for the spectrumGroups
        """
        items = self._getInternalParameter(SERIESITEMS)
        if items is not None:
            series = ()
            for sg in self.spectrumGroups:
                if sg.pid in items:
                    series += (items[sg.pid],)
                else:
                    series += (None,)
            return series

    @_seriesItems.setter
    @ccpNmrV3CoreSetter()
    def _seriesItems(self, items):
        """Set the series items for all spectrumGroups that spectrum is attached to.
        Must be of the form ( <item1>,
                              <item2>,
                              ...
                              <itemN>
                            )
            where <itemsN> are of the same type (or None)
        """
        if not items:
            raise ValueError('items is not defined')
        if not isinstance(items, (tuple, list, type(None))):
            raise TypeError('items is not of type tuple/None')
        if len(items) != len(self.spectrumGroups):
            raise ValueError('Number of items does not match number of spectrumGroups')

        if isinstance(items, tuple):
            diffItems = set(type(item) for item in items)
            if len(diffItems) > 2 or (len(diffItems) == 2 and type(None) not in diffItems):
                raise ValueError('Items must be of the same type (or None)')

            seriesItems = self._getInternalParameter(SERIESITEMS)
            for sg, item in zip(self.spectrumGroups, items):
                if seriesItems:
                    seriesItems[sg.pid] = item
                else:
                    seriesItems = {sg.pid: item}
            self._setInternalParameter(SERIESITEMS, seriesItems)

        else:
            self._setInternalParameter(SERIESITEMS, None)

    def _getSeriesItem(self, spectrumGroup):
        """Return the series item for the current spectrum for the selected spectrumGroup
        """
        from ccpn.core.SpectrumGroup import SpectrumGroup

        spectrumGroup = self.project.getByPid(spectrumGroup) if isinstance(spectrumGroup, str) else spectrumGroup
        if not isinstance(spectrumGroup, SpectrumGroup):
            raise TypeError('%s is not a spectrumGroup' % str(spectrumGroup))
        if self not in spectrumGroup.spectra:
            raise ValueError('Spectrum %s does not belong to spectrumGroup %s' % (str(self), str(spectrumGroup)))

        seriesItems = self._getInternalParameter(SERIESITEMS)
        if seriesItems and spectrumGroup.pid in seriesItems:
            return seriesItems[spectrumGroup.pid]

    def _setSeriesItem(self, spectrumGroup, item):
        """Set the series item for the current spectrum for the selected spectrumGroup
        MUST be called from spectrumGroup - error checking for item types is handled there
        """
        from ccpn.core.SpectrumGroup import SpectrumGroup

        # check that the spectrumGroup and spectrum are valid
        spectrumGroup = self.project.getByPid(spectrumGroup) if isinstance(spectrumGroup, str) else spectrumGroup
        if not isinstance(spectrumGroup, SpectrumGroup):
            raise TypeError('%s is not a spectrumGroup', spectrumGroup)
        if self not in spectrumGroup.spectra:
            raise ValueError('Spectrum %s does not belong to spectrumGroup %s' % (str(self), str(spectrumGroup)))

        seriesItems = self._getInternalParameter(SERIESITEMS)

        if seriesItems:
            seriesItems[spectrumGroup.pid] = item
        else:
            seriesItems = {spectrumGroup.pid: item}
        self._setInternalParameter(SERIESITEMS, seriesItems)

    def _renameSeriesItems(self, spectrumGroup, oldPid):
        """rename the keys in the seriesItems to reflect the updated spectrumGroup name
        """
        seriesItems = self._getInternalParameter(SERIESITEMS)
        if oldPid in (seriesItems if seriesItems else ()):
            # insert new items with the new pid
            oldItems = seriesItems[oldPid]
            del seriesItems[oldPid]
            seriesItems[spectrumGroup.pid] = oldItems
            self._setInternalParameter(SERIESITEMS, seriesItems)

    def _getSeriesItemsById(self, id):
        """Return the series item for the current spectrum by 'id'
        CCPNINTERNAL: used in creating new spectrumGroups - not for external use
        """
        seriesItems = self._getInternalParameter(SERIESITEMS)
        if seriesItems and id in seriesItems:
            return seriesItems[id]

    def _setSeriesItemsById(self, id, item):
        """Set the series item for the current spectrum by 'id'
        CCPNINTERNAL: used in creating new spectrumGroups - not for external use
        """
        seriesItems = self._getInternalParameter(SERIESITEMS)
        if seriesItems:
            seriesItems[id] = item
        else:
            seriesItems = {id: item}
        self._setInternalParameter(SERIESITEMS, seriesItems)

    def _removeSeriesItemsById(self, spectrumGroup, id):
        """Remove the keys in the seriesItems allocated to 'id'
        CCPNINTERNAL: used in creating new spectrumGroups - not for external use
        """
        # useful for storing an item
        seriesItems = self._getInternalParameter(SERIESITEMS)
        if id in seriesItems:
            del seriesItems[id]
            self._setInternalParameter(SERIESITEMS, seriesItems)

    @property
    def temperature(self):
        """The temperature of the spectrometer when the spectrum was recorded
        """
        if self._wrappedData.experiment:
            return self._wrappedData.experiment.temperature

    @temperature.setter
    def temperature(self, value):
        """The temperature of the spectrometer when the spectrum was recorded
        """
        if self._wrappedData.experiment:
            self._wrappedData.experiment.temperature = value

    @property
    def preferredAxisOrdering(self):
        """Return the preferred ordering for the axis codes when opening a new spectrumDisplay
        """
        result = self._getInternalParameter(PREFERREDAXISORDERING)
        if result is None:
            result = self.axes
        return result

    @preferredAxisOrdering.setter
    @checkSpectrumPropertyValue(iterable=True, unique=True, types=(int,))
    def preferredAxisOrdering(self, order):
        """Set the preferred ordering for the axis codes when opening a new spectrumDisplay
        """
        # if not order:
        #     raise ValueError('order is not defined')
        # if not isinstance(order, tuple):
        #     raise TypeError('order is not a tuple')
        # if len(order) != self.dimensionCount:
        #     raise TypeError('order is not the correct length')
        if not all(isinstance(ss, int) and ss >= 0 and ss < self.dimensionCount for ss in order):
            raise TypeError('Spectrum.preferredAxisOrdering: elements must be in range (0 .. %d)' % (self.dimensionCount - 1))
        # if len(set(order)) != len(order):
        #     raise ValueError('order must contain unique elements')

        self._setInternalParameter(PREFERREDAXISORDERING, order)

    #-----------------------------------------------------------------------------------------
    # Library functions
    #-----------------------------------------------------------------------------------------

    def ppm2point(self, value, axisCode=None, dimension=None):
        """Convert ppm value to point value for axis corresponding to either axisCode or
        dimension (1-based)
        """
        if dimension is None and axisCode is None:
            raise ValueError('Spectrum.ppm2point: either axisCode or dimension needs to be defined')
        if dimension is not None and axisCode is not None:
            raise ValueError('Spectrum.ppm2point: axisCode and dimension cannot be both defined')

        if axisCode is not None:
            dimension = self.getByAxisCodes('dimensions', [axisCode], exactMatch=False)[0]

        if dimension is None or dimension < 1 or dimension > self.dimensionCount:
            raise RuntimeError('Invalid dimension (%s)' % (dimension,))

        return self.spectrumReferences[dimension - 1].valueToPoint(value)

    def point2ppm(self, value, axisCode=None, dimension=None):
        """Convert point value to ppm for axis corresponding to to either axisCode or
        dimension (1-based)
        """
        if dimension is None and axisCode is None:
            raise ValueError('Spectrum.point2ppm: either axisCode or dimension needs to be defined')
        if dimension is not None and axisCode is not None:
            raise ValueError('Spectrum.point2ppm: axisCode and dimension cannot be both defined')

        if axisCode is not None:
            dimension = self.getByAxisCodes('dimensions', [axisCode], exactMatch=False)[0]

        if dimension is None or dimension < 1 or dimension > self.dimensionCount:
            raise RuntimeError('Invalid dimension (%s)' % (dimension,))

        return self.spectrumReferences[dimension - 1].pointToValue(value)

    def getPpmArray(self, axisCode=None, dimension=None):
        """Return a numpy array with ppm values of the grid points along axisCode or dimension
        """
        if dimension is None and axisCode is None:
            raise ValueError('Spectrum.getPpmArray: either axisCode or dimension needs to be defined')
        if dimension is not None and axisCode is not None:
            raise ValueError('Spectrum.getPpmArray: axisCode and dimension cannot be both defined')

        if axisCode is not None:
            dimension = self.getByAxisCodes('dimensions', [axisCode], exactMatch=False)[0]

        if dimension is None or dimension < 1 or dimension > self.dimensionCount:
            raise RuntimeError('Invalid dimension (%s)' % (dimension,))

        spectrumLimits = self.spectrumLimits[dimension - 1]
        result = np.linspace(spectrumLimits[0], spectrumLimits[1], self.pointCounts[dimension - 1])

        return result

    def getDefaultOrdering(self, axisOrder):
        if not axisOrder:
            # axisOption = self.project.application.preferences.general.axisOrderingOptions

            preferredAxisOrder = self.preferredAxisOrdering
            if preferredAxisOrder is not None:

                specAxisOrder = self.axisCodes
                axisOrder = [specAxisOrder[ii] for ii in preferredAxisOrder]

            else:

                # sets an Nd default to HCN (or possibly 2d to HC)
                specAxisOrder = self.axisCodes
                pOrder = self.searchAxisCodePermutations(('H', 'C', 'N'))
                if pOrder:
                    self.preferredAxisOrdering = pOrder
                    axisOrder = [specAxisOrder[ii] for ii in pOrder]
                    getLogger().debug('setting default axisOrdering: ', str(axisOrder))

                else:

                    # just set to the normal ordering
                    self.preferredAxisOrdering = tuple(ii for ii in range(self.dimensionCount))
                    axisOrder = specAxisOrder

                    # try permutations of repeated codes
                    duplicates = [('H', 'H'), ('C', 'C'), ('N', 'N')]
                    for dCode in duplicates:
                        pOrder = self.searchAxisCodePermutations(dCode)

                        # if permutation found and matches first axis
                        if pOrder and pOrder[0] == 0:
                            self.preferredAxisOrdering = pOrder
                            axisOrder = [specAxisOrder[ii] for ii in pOrder]
                            getLogger().debug('setting duplicate axisOrdering: ', str(axisOrder))
                            break

        return axisOrder

    # def automaticIntegration(self, spectralData):
    #     return self._apiDataSource.automaticIntegration(spectralData)

    def _mapAxisCodes(self, axisCodes: Sequence[str]):
        """Map axisCodes on self.axisCodes
        return mapped axisCodes as list
        """
        # find the map of newAxisCodeOrder to self.axisCodes; eg. 'H' to 'Hn'
        axisCodeMap = getAxisCodeMatch(axisCodes, self.axisCodes)
        if len(axisCodeMap) == 0:
            raise ValueError('axisCodes %s contains an invalid element' % str(axisCodes))
        return [axisCodeMap[a] for a in axisCodes]

    def _reorderValues(self, values: Sequence, newAxisCodeOrder: Sequence[str]):
        """Reorder values in spectrum dimension order to newAxisCodeOrder
        """
        mapping = dict((axisCode, i) for i, axisCode in enumerate(self.axisCodes))
        # assemble the newValues in order
        newValues = []
        for axisCode in newAxisCodeOrder:
            if axisCode in mapping:
                newValues.append(values[mapping[axisCode]])
            else:
                raise ValueError('Invalid axisCode "%s" in %s; should be one of %s' %
                                 (axisCode, newAxisCodeOrder, self.axisCodes))
        return newValues

    def getByAxisCodes(self, parameterName: str, axisCodes: Sequence[str] = None, exactMatch: bool = False, matchLength: bool = True):
        """Return values defined by attributeName in order defined by axisCodes:
        (default order if None).

        Perform a mapping if exactMatch=False (eg. 'H' to 'Hn')

        NB: Use getByDimensions for dimensions (1..dimensionCount) based access
        """
        if not hasattr(self, parameterName):
            raise ValueError('%s does not have parameter "%s"' % (self, parameterName))

        if not isIterable(axisCodes):
            raise ValueError('axisCodes is not iterable "%s"; expected list or tuple' % axisCodes)

        if axisCodes is not None and not exactMatch:
            if (_axisCodes := self._mapAxisCodes(axisCodes)) is None:
                raise ValueError('Failed mapping axisCodes "%s"' % axisCodes)
            axisCodes = _axisCodes

        try:
            values = getattr(self, parameterName)
        except AttributeError:
            raise ValueError('Error getting parameter "%s" from %s' % (parameterName, self))
        if not isIterable(values):
            raise ValueError('Parameter "%s" of %s is not iterable; "%s"' % (parameterName, self, values))

        if axisCodes is not None:
            # change to order defined by axisCodes
            values = self._reorderValues(values, axisCodes[:self.dimensionCount] if matchLength else axisCodes)
        return values

    def setByAxisCodes(self, parameterName: str, values: Sequence, axisCodes: Sequence[str] = None, exactMatch: bool = False, matchLength: bool = True):
        """Set attributeName to values in order defined by axisCodes:
        (default order if None)

        Perform a mapping if exactMatch=False (eg. 'H' to 'Hn')

        NB: Use setByDimensions for dimensions (1..dimensionCount) based access
        """
        if not hasattr(self, parameterName):
            raise ValueError('%s does not have parameter "%s"' % (self, parameterName))

        if not isIterable(values):
            raise ValueError('Parameter "%s" of %s requires iterable; "%s"' % (parameterName, self, values))

        if not isIterable(axisCodes):
            raise ValueError('axisCodes is not iterable "%s"; expected list or tuple' % axisCodes)

        if axisCodes is not None and not exactMatch:
            axisCodes = self._mapAxisCodes(axisCodes)

        if axisCodes is not None:
            # change values to the order appropriate for spectrum
            values = self._reorderValues(values, axisCodes[:self.dimensionCount] if matchLength else axisCodes)
        try:
            setattr(self, parameterName, values)
        except AttributeError:
            raise ValueError('Unable to set parameter "%s" of %s to "%s"' % (parameterName, self, values))

    def getByDimensions(self, parameterName: str, dimensions: Sequence[int] = None):
        """Return values of parameterName in order defined by dimensions (1..dimensionCount).
           (default order if None)
           NB: Use getByAxisCodes for axisCode based access
        """
        if not hasattr(self, parameterName):
            raise ValueError('Spectrum object does not have parameter "%s"' % parameterName)

        values = getattr(self, parameterName)
        if not isIterable(values):
            raise ValueError('Parameter "%s" of %s is not iterable; "%s"' % (parameterName, self, values))

        if dimensions is None:
            return values

        newValues = []
        for dim in dimensions:
            if not (1 <= dim <= self.dimensionCount):
                raise ValueError('Invalid dimension "%d"; should be one of %s' % (dim, self.dimensions))
            else:
                newValues.append(values[dim - 1])
        return newValues

    def setByDimensions(self, parameterName: str, values: Sequence, dimensions: Sequence[int] = None):
        """Set parameterName to values as defined by dimensions (1..dimensionCount).
           (default order if None)
           NB: Use setByAxisCodes for axisCode based access
        """
        if not hasattr(self, parameterName):
            raise ValueError('Spectrum object does not have parameter "%s"' % parameterName)

        if not isIterable(values):
            raise ValueError('Parameter "%s" of %s requires iterable; "%s"' % (parameterName, self, values))

        if dimensions is None:
            dimensions = self.dimensions
        if not isIterable(dimensions):
            raise ValueError('dimensions "%s" is not iterable' % (dimensions))

        newValues = getattr(self, parameterName)
        for idx, dim in enumerate(dimensions):
            if not (1 <= dim <= self.dimensionCount):
                raise ValueError('Invalid dimension "%d"; should be one of %s' % (dim, self.dimensions))
            else:
                newValues[dim - 1] = values[idx]
        try:
            setattr(self, parameterName, newValues)
        except AttributeError:
            raise ValueError('Unable to set parameter "%s" of %s to "%s"' % (parameterName, self, values))

    def searchAxisCodePermutations(self, checkCodes: Tuple[str, ...]) -> Optional[Tuple[int]]:
        """Generate the permutations of the current axisCodes
        """
        if not checkCodes:
            raise ValueError('checkCodes is not defined')
        if not isinstance(checkCodes, (tuple, list)):
            raise TypeError('checkCodes is not a list/tuple')
        if not all(isinstance(ss, str) for ss in checkCodes):
            raise TypeError('checkCodes elements must be strings')

        from itertools import permutations

        # add permutations for the axes
        axisPerms = tuple(permutations([axisCode for axisCode in self.axisCodes]))
        axisOrder = tuple(permutations(list(range(len(self.axisCodes)))))

        for ii, perm in enumerate(axisPerms):
            n = min(len(checkCodes), len(perm))
            if n and all(pCode[0] == cCode[0] for pCode, cCode in zip(perm[:n], checkCodes[:n])):
                return axisOrder[ii]

    def _setDefaultContourValues(self, base=None, multiplier=1.41, count=10):
        """Set default contour values
        """
        if base is None:
            base = self.noiseLevel * multiplier if self.noiseLevel else 1e6
        base = max(base, 1.0)  # Contour bases have to be > 0.0

        self.positiveContourBase = base
        self.positiveContourFactor = multiplier
        self.positiveContourCount = count
        self.negativeContourBase = -1.0 * base
        self.negativeContourFactor = multiplier
        self.negativeContourCount = count

    def _setDefaultContourColours(self):
        """Set default contour colours
        """
        (self.positiveContourColour, self.negativeContourColour) = getDefaultSpectrumColours(self)
        self.sliceColour = self.positiveContourColour

    def getPeakAliasingRanges(self):
        """Return the min/max aliasing Values for the peakLists in the spectrum, if there are no peakLists with peaks, return None
        """
        # get the aliasingRanges for non-empty peakLists
        aliasRanges = [peakList.getPeakAliasingRanges() for peakList in self.peakLists if peakList.peaks]

        if aliasRanges:
            # if there is only one then return it (for clarity)
            if len(aliasRanges) == 1:
                return aliasRanges[0]

            # get the value from all the peakLists
            newRanges = list(aliasRanges[0])
            for ii, alias in enumerate(aliasRanges[1:]):
                if alias is not None:
                    newRanges = tuple((min(minL, minR), max(maxL, maxR)) for (minL, maxL), (minR, maxR) in zip(alias, newRanges))

            return newRanges

    def _copyDimensionalParameters(self, axisCodes, target):
        """Copy dimensional parameters for axisCodes from self to target
        """
        for attr in _includeInCopyList().getMultiDimensional():
            try:
                values = self.getByAxisCodes(attr, axisCodes, exactMatch=True)
                target.setByAxisCodes(attr, values, axisCodes, exactMatch=True)
            except Exception as es:
                getLogger().error('Copying "%s" from %s to %s for axisCodes %s: %s' %
                                  (attr, self, target, axisCodes, es)
                                  )

    def _copyNonDimensionalParameters(self, target):
        """Copy non-dimensional parameters from self to target
        """
        for parameterName in _includeInCopyList().getNoneDimensional():
            try:
                value = getattr(self, parameterName)
                setattr(target, parameterName, value)
            except Exception as es:
                getLogger().warning('Copying parameter %r from %s to %s: %s' % (parameterName, self, target, es))

    def copyParameters(self, axisCodes, target):
        """Copy non-dimensional and dimensional parameters for axisCodes from self to target
        """
        self._copyNonDimensionalParameters(target)
        self._copyDimensionalParameters(axisCodes, target)

    def estimateNoise(self):
        """Estimate and return the noise level, or None if it cannot be
        """
        if self._dataSource is not None:
            noise = self._dataSource.estimateNoise()
        else:
            noise = None
        return noise

    #-----------------------------------------------------------------------------------------
    # data access functions
    #-----------------------------------------------------------------------------------------

    @logCommand(get='self')
    def getIntensity(self, ppmPositions):
        """Returns the interpolated height at the ppm position
        """
        # The height below is not derived from any fitting
        # but is a weighted average of the values at the neighbouring grid points

        getLogger().warning('This routine has been replaced with getHeight')
        return self.getHeight(ppmPositions)

    @logCommand(get='self')
    def getHeight(self, ppmPositions):
        """Returns the interpolated height at the ppm position
        """
        if len(ppmPositions) != self.dimensionCount:
            raise ValueError('Length of %s does not match number of dimensions' % str(ppmPositions))
        if not all(isinstance(dimVal, (int, float)) for dimVal in ppmPositions):
            raise ValueError('ppmPositions values must be floats')

        pointPositions = [self.ppm2point(p, dimension=idx + 1) for idx, p in enumerate(ppmPositions)]
        return self.getPointValue(pointPositions)

    @logCommand(get='self')
    def getPointValue(self, pointPositions):
        """Return the value interpolated at the position given in points (1-based, float values).
        """
        if len(pointPositions) != self.dimensionCount:
            raise ValueError('Length of %s does not match number of dimensions.' % str(pointPositions))
        if not all(isinstance(dimVal, (int, float)) for dimVal in pointPositions):
            raise ValueError('position values must be floats.')

        if self._dataSource is None:
            getLogger().warning('No proper (filePath, dataFormat) set for %s; Returning zero' % self)
            return 0.0

        # need to check folding/circular/±sign

        # pointPositions = []
        # aliasing = []
        # for idx, (p, np) in enumerate(zip(ppmPos, spectrum.pointCounts)):
        #     pp = spectrum.ppm2point(p, dimension=idx + 1)
        #     pointPositions.append(((pp - 1) % np) + 1)
        #     aliasing.append((pp - 1) // np)

        aliasingFlags = [1] * self.dimensionCount
        value = self._dataSource.getPointValue(pointPositions, aliasingFlags=aliasingFlags)
        return value * self.scale

    @logCommand(get='self')
    def getSliceData(self, position=None, sliceDim: int = 1):
        """Get a slice defined by sliceDim and a position vector

        :param position: An optional list/tuple of point positions (1-based);
                         defaults to [1,1,1,1]
        :param sliceDim: Dimension of the slice axis (1-based)

        :return: numpy 1D data array

        NB: use getSlice() method for axisCode based access
        """
        if self._dataSource is None:
            getLogger().warning('No proper (filePath, dataFormat) set for %s; Returning zeros only' % self)
            data = numpy.zeros((self.pointCounts[sliceDim - 1],), dtype=numpy.float32)

        else:
            try:
                position = self._dataSource.checkForValidSlice(position, sliceDim)
                data = self._dataSource.getSliceData(position=position, sliceDim=sliceDim)
                data = data.copy(order='K') * self.scale

            except (RuntimeError, ValueError) as es:
                getLogger().error('Spectrum.getSliceData: %s' % es)
                raise es

        # For 1D, save as intensities attribute; TODO: remove
        self._intensities = data
        return data

    @logCommand(get='self')
    def getSlice(self, axisCode, position) -> numpy.array:
        """Get a slice defined by axisCode and a position vector

        :param axisCode: valid axisCode of the slice axis
        :param position: An optional list/tuple of point positions (1-based);
                         defaults to [1,1,1,1]

        :return: numpy 1D data array

        NB: use getSliceData() method for dimension based access
        """
        dimensions = self.getByAxisCodes('dimensions', [axisCode], exactMatch=True)
        return self.getSliceData(position=position, sliceDim=dimensions[0])

    @logCommand(get='self')
    def extractSliceToFile(self, axisCode, position, path=None, dataFormat='Hdf5'):
        """Extract 1D slice from self as new Spectrum; saved to path
        if 1D it effectively yields a copy of self

        :param axisCode: axiscode of slice to extract
        :param position: position vector (1-based)
        :param path: optional path; if None, constructed from current filePath

        :return: Spectrum instance
        """
        if self._dataSource is None:
            text = 'No proper (filePath, dataFormat) set for %s; unable to extract slice' % self
            getLogger().error(text)
            raise RuntimeError(text)

        if axisCode is None or axisCode not in self.axisCodes:
            raise ValueError('Invalid axisCode %r, should be one of %s' % (axisCode, self.axisCodes))

        try:
            dimensions = self.getByAxisCodes('dimensions', [axisCode])
            self._dataSource.checkForValidSlice(position=position, sliceDim=dimensions[0])
            newSpectrum = self._extractToFile(axisCodes=[axisCode], position=position,
                                              path=path, dataFormat=dataFormat, tag='slice')

        except (ValueError, RuntimeError) as es:
            text = 'Spectrum.extractSliceToFile: %s' % es
            raise ValueError(es)

        return newSpectrum

    @logCommand(get='self')
    def getPlaneData(self, position=None, xDim: int = 1, yDim: int = 2):
        """Get a plane defined by by xDim and yDim ('1'-based), and a position vector ('1'-based)
        Dimensionality must be >= 2

        :param position: A list/tuple of point-positions (1-based)
        :param xDim: Dimension of the first axis (1-based)
        :param yDim: Dimension of the second axis (1-based)

        :return: 2D float32 NumPy array in order (yDim, xDim)

        NB: use getPlane() method for axisCode based access
        """
        if self.dimensionCount < 2:
            raise RuntimeError("Spectrum.getPlaneData: dimensionality < 2")

        if self._dataSource is None:
            getLogger().warning('No proper (filePath, dataFormat) set for %s; Returning zeros only' % self)
            data = numpy.zeros((self.pointCounts[yDim - 1], self.pointCounts[xDim - 1]), dtype=numpy.float32)

        else:
            try:
                position = self._dataSource.checkForValidPlane(position, xDim=xDim, yDim=yDim)
            except (RuntimeError, ValueError) as es:
                getLogger().error('invalid arguments: %s' % es)
                raise es

            data = self._dataSource.getPlaneData(position=position, xDim=xDim, yDim=yDim)
            # Make a copy in order to preserve the original data and apply scaling
            data = data.copy(order='K') * self.scale

        return data

    @logCommand(get='self')
    def getPlane(self, axisCodes, position=None):
        """Get a plane defined by axisCodes and position
        Dimensionality must be >= 2

        :param axisCodes: tuple/list of two axisCodes; expand if exactMatch=False
        :param position: A list/tuple of point-positions (1-based)

        :return: 2D float32 NumPy array in order (yDim, xDim)

        NB: use getPlaneData method for dimension based access
        """
        if len(axisCodes) != 2:
            raise ValueError('Invalid axisCodes %s, len should be 2' % axisCodes)

        xDim, yDim = self.getByAxisCodes('dimensions', axisCodes, exactMatch=True)
        return self.getPlaneData(position=position, xDim=xDim, yDim=yDim)

    @logCommand(get='self')
    def extractPlaneToFile(self, axisCodes: (tuple, list), position=None, path=None, dataFormat='Hdf5'):
        """Save a plane, defined by axisCodes and position, to path using dataFormat
        Dimensionality must be >= 2

        :param axisCodes: tuple/list of two axisCodes
        :param position: a list/tuple of point-positions (1-based)
        :param path: path of the resulting file; auto-generated if None
        :param dataFormat: a data format valid for writing

        :returns plane as Spectrum instance
        """
        if self._dataSource is None:
            text = 'No proper (filePath, dataFormat) set for %s; unable to extract plane' % self
            getLogger().error(text)
            raise RuntimeError(text)

        if axisCodes is None or len(axisCodes) != 2:
            raise ValueError('Invalid parameter axisCodes "%s", should be two of %s' % (axisCodes, self.axisCodes))

        try:
            dimensions = self.getByAxisCodes('dimensions', axisCodes)
            self._dataSource.checkForValidPlane(position=position, xDim=dimensions[0], yDim=dimensions[1])
            newSpectrum = self._extractToFile(axisCodes=axisCodes, position=position, path=path, dataFormat=dataFormat,
                                              tag='plane')

        except (ValueError, RuntimeError) as es:
            text = 'Spectrum.extractPlaneToFile: %s' % es
            raise ValueError(text)

        return newSpectrum

    @logCommand(get='self')
    def getProjection(self, axisCodes: (tuple, list), method: str = 'max', threshold=None):
        """Get projected plane defined by two axisCodes, using method and an optional threshold

        :param axisCodes: tuple/list of two axisCodes; expand if exactMatch=False
        :param method: 'max', 'max above threshold', 'min', 'min below threshold',
                       'sum', 'sum above threshold', 'sum below threshold'
        :param threshold: threshold value for relevant method

        :return: projected spectrum data as 2D float32 NumPy array in order (yDim, xDim)
        """
        projectedData = _getProjection(self, axisCodes=axisCodes, method=method, threshold=threshold)
        return projectedData

    @logCommand(get='self')
    def extractProjectionToFile(self, axisCodes: (tuple, list), method: str = 'max', threshold=None,
                                path=None, dataFormat='Hdf5'):
        """Save a projected plane, defined by axisCodes and position, using method and an optional threshold,
        to path using dataFormat
        Dimensionality must be >= 2

        :param axisCodes: tuple/list of two axisCodes
        :param method: 'max', 'max above threshold', 'min', 'min below threshold',
                       'sum', 'sum above threshold', 'sum below threshold'
        :param threshold: threshold value for relevant method
        :param path: path of the resulting file; auto-generated if None
        :param dataFormat: a data format valid for writing

        :returns projected plane as Spectrum instance
        """
        if self._dataSource is None:
            text = 'No proper (filePath, dataFormat) set for %s; unable to extract plane' % self
            getLogger().error(text)
            raise RuntimeError(text)

        if axisCodes is None or len(axisCodes) != 2:
            raise ValueError('Invalid parameter axisCodes "%s", should be two of %s' % (axisCodes, self.axisCodes))

        try:
            xDim, yDim = self.getByAxisCodes('dimensions', axisCodes)
            position = [1] * self.dimensionCount
            self._dataSource.checkForValidPlane(position=position, xDim=xDim, yDim=yDim)
            newSpectrum = self._extractToFile(axisCodes=axisCodes, position=position, path=path, dataFormat=dataFormat,
                                              tag='projection')
            projectionData = self.getProjection(axisCodes=axisCodes, method=method, threshold=threshold)
            # For writing, we need to remap the axisCodes onto the newSpectrum
            xDim2, yDim2 = newSpectrum.getByAxisCodes('dimensions', axisCodes)
            newSpectrum._dataSource.setPlaneData(data=projectionData, position=position, xDim=xDim2, yDim=yDim2)

        except (ValueError, RuntimeError) as es:
            text = 'Spectrum.extractProjectionToFile: %s' % es
            raise ValueError(text)

        return newSpectrum

    def _clone1D(self):
        """Clone 1D spectrum to a new spectrum."""
        #FIXME Crude approach / hack

        newSpectrum = self.project.newEmptySpectrum(isotopeCodes=self.isotopeCodes, name=self.name)
        newSpectrum._positions = self.positions
        newSpectrum._intensities = self.intensities
        for peakList in self.peakLists:
            peakList.copyTo(newSpectrum)

        import inspect

        attr = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        filteredAttr = [a for a in attr if not (a[0].startswith('__') and a[0].endswith('__')) and not a[0].startswith('_')]
        for i in filteredAttr:
            att, val = i
            try:
                setattr(newSpectrum, att, val)
            except AttributeError:
                # print(e, att)
                pass
        return newSpectrum

    def _axisDictToSliceTuples(self, axisDict) -> list:
        """Convert dict of (key,value) = (axisCode, (startPpm, stopPpm)) pairs
        to a list of sliceTuples (1-based)

        if (axisDict[axisCode] is None) ==> use spectrumLimits
        if (startPpm is None) ==> point=1
        if (stopPpm is None) ==> point=pointCounts[axis]

        :param axisDict: dict of (axisCode, (startPpm,stopPpm)) (key,value) pairs
        :return list of sliceTuples

        CCPNINTERNAL: also used by PeakPickerABC
        """
        axisCodes = [ac for ac in axisDict.keys()]

        # augment axisDict with any missing axisCodes or replace any None values with spectrumLimits
        inds = self.getByAxisCodes('axes', axisCodes)
        for idx, ac in enumerate(self.axisCodes):
            if idx not in inds:
                axisDict[ac] = self.spectrumLimits[idx]

        axisPpms = [ppm for ppm in axisDict.values()]
        sliceTuples = [None] * self.dimensionCount
        for axis, ac, dim in self.axisTriples:
            idx = inds.index(axis)
            stopPpm, startPpm = axisPpms[idx] # to be converted to points; ppm scale runs backwards

            if startPpm is None:
                startPoint = 1
            else:
                startPoint = int(self.ppm2point(startPpm, dimension=idx + 1) + 0.5)

            if stopPpm is None:
                stopPoint = self.pointCounts[axis]
            else:
                stopPoint = int(self.ppm2point(stopPpm, dimension=idx + 1) + 0.5)

            sliceTuples[axis] = (startPoint, stopPoint)

        getLogger().debug('Spectrum._axisDictToSliceTuples: axisDict = %s; sliceTuples = %s' %
                          (axisDict, sliceTuples))
        return sliceTuples

    def getRegion(self, **axisDict):
        """
        Return the region of the spectrum data defined by the axis limits in ppm as numpy array
        of the same dimensionality as defined by the Spectrum instance.

        Axis limits  are passed in as a dict of (axisCode, tupleLimit) key, value pairs
        with the tupleLimit supplied as (startPpm,stopPpm) axis limits in ppm (lower ppm value first).

        For axisCodes that are not included in the axisDict, the limits will by taken from the
        spectrum limits along the relevant axis
        For axisCodes that are None, the limits will by taken from the spectrum limits along the
        relevant axis

        Illegal axisCodes will raise an error.

        Example dict:
            {'Hn': (7.0, 9.0),
             'Nh': (110, 130)
             }

        Example calling function:
            regionData = spectrum.getRegion(**limitsDict)
            regionData = spectrum.getRegion(Hn=(7.0, 9.0), Nh=(110, 130))

        :param axisDict: dict of (axisCode, (startPpm,stopPpm)) key,value pairs
        :return: numpy array
        """
        if not self.hasValidPath():
            raise RuntimeError('Not valid path for %s ' % self)
        sliceTuples = self._axisDictToSliceTuples(axisDict)
        return self._dataSource.getRegionData(sliceTuples)

    def getRegionData(self, exclusionBuffer: Optional[Sequence] = None, minimumDimensionSize: int = 3, **axisDict):
        """Return the region of the spectrum data defined by the axis limits.
        GWV: Old routine replaced by getRegion
        """
        raise NotImplementedError('replace by getRegion')

    @logCommand(get='self')
    def createPeak(self, peakList=None, **ppmPositions) -> Optional['Peak']:
        """Create peak at position specified by the ppmPositions dict.

        Return the peak created at this ppm position or None.

        Ppm positions are passed in as a dict of (axisCode, ppmValue) key, value pairs
        with the ppmValue supplied mapping to the closest matching axis.

        Illegal or non-matching axisCodes will return None.

        Example ppmPosition dict:

        ::

            {'Hn': 7.0, 'Nh': 110}

        Example calling function:

        ::

        >>> peak = spectrum.createPeak(**ppmPositions)
        >>> peak = spectrum.createPeak(peakList, **ppmPositions)
        >>> peak = spectrum.createPeak(peakList=peakList, Hn=7.0, Nh=110)

        :param peakList: peakList to create new peak in, or None for the last peakList belonging to spectrum
        :param ppmPositions: dict of (axisCode, ppmValue) key,value pairs
        :return: new peak or None
        """
        from ccpn.core.lib.SpectrumLib import _createPeak

        return _createPeak(self, peakList, **ppmPositions)

    @peakPicker.setter
    def peakPicker(self, peakPicker):
        """Set the current peakPicker class instance
        """
        from ccpn.core.lib.PeakPickers.PeakPickerABC import PeakPickerABC

        if not isinstance(peakPicker, (PeakPickerABC, type(None))):
            raise ValueError('Not a valid peakPickerABC class')
        elif peakPicker and peakPicker.spectrum != self:
            raise ValueError(f'peakPicker is already linked to spectrum {peakPicker.spectrum}')
        elif peakPicker:
            with undoBlockWithoutSideBar():
                # set the current peakPicker
                self._peakPicker = peakPicker

                # automatically store in the spectrum CCPN internal store
                self._peakPicker._storeAttributes()
                getLogger().debug('Setting new peak picker')
        else:
            with undoBlockWithoutSideBar():
                # clear the current peakPicker
                if self._peakPicker:
                    self._peakPicker._detachFromSpectrum()
                    self._peakPicker = None
                    getLogger().debug('Clearing old peak picker')

    @logCommand(get='self')
    def pickPeaks(self, peakList=None, positiveThreshold=None, negativeThreshold=None, **ppmRegions) -> Optional[Tuple['Peak', ...]]:
        """Pick peaks in the region defined by the ppmRegions dict.

        Ppm regions are passed in as a dict containing the axis codes and the required limits.
        Each limit is defined as a key, value pair: (str, tuple), with the tuple supplied as (min, max) axis limits in ppm.
        Axis codes supplied are mapped to the closest matching axis.

        Illegal or non-matching axisCodes will return None.

        Example ppmRegions dict:

        ::

            {'Hn': (7.0, 9.0),
             'Nh': (110, 130)
             }

        Example calling function:

        ::

        >>> peaks = spectrum.pickPeaks(**ppmRegions)
        >>> peaks = spectrum.pickPeaks(peakList, **ppmRegions)
        >>> peaks = spectrum.pickPeaks(peakList=peakList, Hn=(7.0, 9.0), Nh=(110, 130))

        :param peakList: peakList to create new peak in, or None for the last peakList belonging to spectrum
        :param positiveThreshold: float or None specifying the positive threshold above which to find peaks.
                                  if None, positive peak picking is disabled.
        :param negativeThreshold: float or None specifying the negative threshold below which to find peaks.
                                  if None, negative peak picking is disabled.
        :param ppmRegions: dict of (axisCode, tupleValue) key, value pairs
        :return: tuple of new peaks or None
        """
        from ccpn.core.lib.SpectrumLib import _pickPeaks

        return _pickPeaks(self, peakList, positiveThreshold, negativeThreshold, **ppmRegions)

    def _extractToFile(self, axisCodes, position, path, dataFormat, tag):
        """Local routine to prevent code duplication across extractSliceToFile, extractPlaneToFile,
        extractProjectionToFile.
        Return new spectrum instance
        """
        dimensions = self.getByAxisCodes('dimensions', axisCodes)

        dataFormats = getDataFormats()
        validFormats = [k.dataFormat for k in dataFormats.values() if k.hasWritingAbility]
        klass = dataFormats.get(dataFormat)
        if klass is None:
            raise ValueError('Invalid dataFormat %r; must be one of %s' % (dataFormat, validFormats))
        if not klass.hasWritingAbility:
            raise ValueError('Unable to write to dataFormat %r; must be one of %s' % (dataFormat, validFormats))
        suffix = klass.suffixes[0] if len(klass.suffixes) > 0 else '.dat'

        tagStr = '%s_%s' % (tag, '_'.join(axisCodes))
        appendToFilename = '_%s_%s' % (tagStr, '_'.join([str(p) for p in position]))

        if path is None:
            dataStore = DataStore.newFromPath(path=self.filePath, appendToName=appendToFilename,
                                              autoVersioning=True, withSuffix=suffix,
                                              dataFormat=klass.dataFormat)
        else:
            dataStore = DataStore.newFromPath(path=path,
                                              autoVersioning=True, withSuffix=suffix,
                                              dataFormat=klass.dataFormat)

        newSpectrum = _extractRegionToFile(self, dimensions=dimensions, position=position, dataStore=dataStore)

        # add some comment as to the origin of the data
        comment = newSpectrum.comment
        if comment is None:
            comment = ''
        if len(comment) > 0:
            comment += '; '
        comment += '%s at (%s) from %s' % (tagStr, ','.join([str(p) for p in position]), self)
        newSpectrum.comment = comment

        return newSpectrum

    #-----------------------------------------------------------------------------------------
    # Iterators
    #-----------------------------------------------------------------------------------------

    def allPlanes(self, axisCodes: tuple, exactMatch=True):
        """An iterator over all planes defined by axisCodes, yielding (positions, data-array) tuples
        Expand axisCodes if exactMatch=False
        positions are 1-based
        """
        if len(axisCodes) != 2:
            raise ValueError('Invalid axisCodes %s, len should be 2' % axisCodes)

        axisDims = self.getByAxisCodes('dimensions', axisCodes, exactMatch=exactMatch)  # check and optionally expand axisCodes
        if axisDims[0] == axisDims[1]:
            raise ValueError('Invalid axisCodes %s; identical' % axisCodes)

        if not self.hasValidPath():
            raise RuntimeError('Not valid path for %s ' % self)
        return self._dataSource.allPlanes(xDim=axisDims[0], yDim=axisDims[1])

    def allSlices(self, axisCode, exactMatch=True):
        """An iterator over all slices defined by axisCode, yielding (positions, data-array) tuples
        positions are 1-based
        """
        sliceDim = self.getByAxisCodes('dimensions', [axisCode], exactMatch=exactMatch)[0]
        if not self.hasValidPath():
            raise RuntimeError('Not valid path for %s ' % self)
        return self._dataSource.allSlices(sliceDim=sliceDim)

    #-----------------------------------------------------------------------------------------
    # Implementation properties and functions
    #-----------------------------------------------------------------------------------------

    @property
    def _serial(self) -> int:
        """Return the _wrappedData serial
        CCPN Internal
        """
        return self._wrappedData.serial

    def _getDataSource(self, dataStore):
        """Check the validity and access the file defined by dataStore;
        returns: SpectrumDataSource instance or None when filePath and/or dataFormat of the
        dataStore instance are incorrect
        """

        if dataStore is None:
            raise ValueError('dataStore not defined')
        if not isinstance(dataStore, DataStore):
            raise ValueError('dataStore has invalid type')

        if dataStore.dataFormat == EmptySpectrumDataSource.dataFormat:
            # Special case, empty spectrum
            dataSource = EmptySpectrumDataSource()
            dataSource.importFromSpectrum(self)

        else:
            dataSource = getSpectrumDataSource(dataStore.aPath(), dataStore.dataFormat)
            if dataSource is None:
                raise RuntimeError('Spectrum._getDataSource: dataStore path "%s" is incompatible with dataFormat "%s"' %
                                    (dataStore.aPath(), dataStore.dataFormat))

            # check some fundamental parameters
            if dataSource.dimensionCount != self.dimensionCount:
                raise RuntimeError('Spectrum._getDataSource: incompatible dimensionCount (%s) of "%s"' %
                                 (dataSource.dimensionCount, dataStore.aPath()))

            for idx, np in enumerate(self.pointCounts):
                if dataSource.pointCounts[idx] != np:
                    raise RuntimeError('Spectrum._getDataSource: incompatible pointsCount[%s] = %s of "%s"' %
                                     (idx, dataSource.pointCounts[idx], dataStore.aPath()))

            dataSource.spectrum = self

        return dataSource

    def _getPeakPicker(self):
        """Check whether a peakPicker class has been saved with this spectrum.
        Returns new peakPicker instance or None if one has not been defined
        """
        from ccpn.core.lib.PeakPickers.PeakPickerABC import PeakPickerABC

        return PeakPickerABC._restorePeakPicker(self)

    def _updateParameterValues(self):
        """This method check, and if needed updates specific parameter values
        """
        # Quietly set some values
        getLogger().debug2('Updating %s parameters' % self)
        with inactivity():
            # getting the noiseLevel by calling estimateNoise() if not defined
            if self.noiseLevel is None:
                self.noiseLevel = self.estimateNoise()

            # Check  contourLevels, contourColours
            if self.positiveContourCount == 0 or self.negativeContourCount == 0:
                self._setDefaultContourValues()
                self._setDefaultContourColours()
            if not self.sliceColour:
                self.sliceColour = self.positiveContourColour

    def _updateEdgeToAlpha1(self):
        """Update the _ccpnInternal settings from version3.0.4 -> 3.1.0.alpha
        """
        if not isinstance(self._ccpnInternalData, dict):
            return

        # deprecated ccpnInternal settings
        SPECTRUMAXES = 'spectrumAxesOrdering'
        SPECTRUMPREFERREDAXISORDERING = 'spectrumPreferredAxisOrdering'
        SPECTRUMALIASING = 'spectrumAliasing'
        SPECTRUMSERIES = 'spectrumSeries'
        SPECTRUMSERIESITEMS = 'spectrumSeriesItems'

        # include positive/negative contours
        if INCLUDEPOSITIVECONTOURS in self._ccpnInternalData:
            value = self._ccpnInternalData.get(INCLUDEPOSITIVECONTOURS)
            self._setInternalParameter(INCLUDEPOSITIVECONTOURS, value)
            del self._ccpnInternalData[INCLUDEPOSITIVECONTOURS]

        if INCLUDENEGATIVECONTOURS in self._ccpnInternalData:
            value = self._ccpnInternalData.get(INCLUDENEGATIVECONTOURS)
            self._setInternalParameter(INCLUDENEGATIVECONTOURS, value)
            del self._ccpnInternalData[INCLUDENEGATIVECONTOURS]

        # spectrum preferred axis order
        if self.hasParameter(SPECTRUMAXES, SPECTRUMPREFERREDAXISORDERING):
            value = self.getParameter(SPECTRUMAXES, SPECTRUMPREFERREDAXISORDERING)
            if value is not None:
                self._setInternalParameter(PREFERREDAXISORDERING, value)

        # spectrumgroup series items
        if self.hasParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS):
            value = self.getParameter(SPECTRUMSERIES, SPECTRUMSERIESITEMS)
            if value is not None:
                self._setInternalParameter(SERIESITEMS, value)

        # display folded contours
        if self.hasParameter(SPECTRUMALIASING, DISPLAYFOLDEDCONTOURS):
            value = self.getParameter(SPECTRUMALIASING, DISPLAYFOLDEDCONTOURS)
            if value is not None:
                self._setInternalParameter(DISPLAYFOLDEDCONTOURS, value)
        # visibleAliasingRange/aliasingRange should already have gone

        # remove unnecessary dict items
        if SPECTRUMAXES in self._ccpnInternalData:
            del self._ccpnInternalData[SPECTRUMAXES]
        if SPECTRUMSERIES in self._ccpnInternalData:
            del self._ccpnInternalData[SPECTRUMSERIES]
        if SPECTRUMALIASING in self._ccpnInternalData:
            del self._ccpnInternalData[SPECTRUMALIASING]

    @classmethod
    def _restoreObject(cls, project, apiObj):
        """Subclassed to allow for initialisations on restore, not on creation via newSpectrum
        """
        spectrum = super()._restoreObject(project, apiObj)
        dataStore = None

        # NOTE - version 3.0.4 -> 3.1.0.alpha update
        # move parameters from _ccpnInternal to the correct namespace, delete old parameters
        spectrum._updateEdgeToAlpha1()

        try:
            # Restore the dataStore info
            dataStore = DataStore()._importFromSpectrum(spectrum)
            spectrum.setTraitValue('_dataStore', dataStore, force=True)
        except (ValueError, RuntimeError) as es:
            getLogger().warning('Error restoring valid data store for %s (%s)' % (spectrum, es))

        try:
            # Get a dataSource object
            dataSource = spectrum._getDataSource(dataStore)
            spectrum.setTraitValue('_dataSource', dataSource, force=True)
        except (ValueError, RuntimeError) as es:
            getLogger().warning('Error restoring valid data source for %s (%s)' % (spectrum, es))

        try:
            spectrum._peakPicker = spectrum._getPeakPicker()
        except (ValueError, RuntimeError) as es:
            getLogger().warning('Error restoring valid peak picker for %s (%s)' % (spectrum, es))

        # Assure a setting of crucial attributes
        spectrum._updateParameterValues()
        # save the spectrum metadata
        spectrum._saveSpectrumMetaData()

        return spectrum

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename Spectrum, changing its name and Pid.
        """
        self._deleteSpectrumMetaData()
        result = self._rename(value)
        self._saveSpectrumMetaData()
        return result

    def _saveSpectrumMetaData(self):
        """Save the spectrum metadata in the project/state/spectra in json file for optional future reference
        """
        _tmpPath = aPath(self.project.path).fetchDir(CCPN_STATE_DIRECTORY, self._pluralLinkName)
        self.save(_tmpPath / self.name + '.json')

    def _restoreFromSpectrumMetaData(self):
        """Retore the spectrum metadata from the project/state/spectra json file
        """
        _tmpPath = aPath(self.project.path).fetchDir(CCPN_STATE_DIRECTORY, self._pluralLinkName)
        self.restore(_tmpPath / self.name + '.json')
        self._dataStore.spectrum = self
        self._dataStore._saveInternal()
        self._dataSource.spectrum = self

    def _deleteSpectrumMetaData(self):
        """Delete the spectrum metadata in the project/state/spectra
        """
        _tmpPath = aPath(self.project.path).joinpath(CCPN_STATE_DIRECTORY, self._pluralLinkName)
        _path = _tmpPath / self.name + '.json'
        if _path.exists():
            _path.removeFile()

    def _finaliseAction(self, action: str):
        """Subclassed to handle associated spectrumViews instances
        """
        if not super()._finaliseAction(action):
            return

        if action == 'create':
            self._saveSpectrumMetaData()

        if action == 'delete':
            self._deleteSpectrumMetaData()

        # notify peak/integral/multiplet list
        if action in ['create', 'delete']:
            for peakList in self.peakLists:
                peakList._finaliseAction(action)
            for multipletList in self.multipletLists:
                multipletList._finaliseAction(action)
            for integralList in self.integralLists:
                integralList._finaliseAction(action)

        # propagate the rename to associated spectrumViews
        if action in ['change']:
            for specView in self.spectrumViews:
                if specView:
                    if self._scaleChanged:
                        # force a rebuild of the contours/etc.
                        specView.buildContoursOnly = True
                    specView._finaliseAction(action)

            if self._scaleChanged:
                self._scaleChanged = False

                # notify peaks/multiplets/integrals that the scale has changed
                for peakList in self.peakLists:
                    for peak in peakList.peaks:
                        peak._finaliseAction(action)
                for multipletList in self.multipletLists:
                    for multiplet in multipletList.multiplets:
                        multiplet._finaliseAction(action)
                for integralList in self.integralLists:
                    for integral in integralList.integrals:
                        integral._finaliseAction(action)

            # from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
            #
            # GLSignals = GLNotifier(parent=self)
            # GLSignals.emitPaintEvent()

    @cached.clear(_REFERENCESUBSANCESCACHE)
    def _clearCache(self):
        """Clear the cache
        """
        if self._dataSource is not None:
            self._dataSource.clearCache()

    # # in baseclass
    # @deleteObject()
    # def _delete(self):
    #     """Delete the spectrum wrapped data.
    #     """
    #     self._wrappedData.delete()

    @logCommand(get='self')
    def delete(self):
        """Delete Spectrum"""
        with undoBlock():

            # self._deleteSpectrumMetaData()

            self._clearCache()
            if self._dataSource is not None:
                self._dataSource.closeFile()

            # self.deleteAllNotifiers() TODO: no longer required?

            # handle spectrumView ordering - this should be moved to spectrumView or spectrumDisplay via notifier?
            specDisplays = []
            specViews = []
            for sp in self.spectrumViews:
                if sp._parent.spectrumDisplay not in specDisplays:
                    specDisplays.append(sp._parent.spectrumDisplay)
                    specViews.append((sp._parent, sp._parent.spectrumViews.index(sp)))

            listsToDelete = tuple(self.peakLists)
            listsToDelete += tuple(self.integralLists)
            listsToDelete += tuple(self.multipletLists)

            # delete the connected lists, should undo in the correct order
            for obj in listsToDelete:
                obj.delete()

            with undoStackBlocking() as addUndoItem:
                # notify spectrumViews of delete/create
                addUndoItem(undo=partial(self._notifySpectrumViews, 'create'),
                            redo=partial(self._notifySpectrumViews, 'delete'))

            # delete the _wrappedData
            self._delete()

            # with undoStackBlocking() as addUndoItem:
            #     # notify spectrumViews of delete
            #     addUndoItem(redo=self._finaliseSpectrumViews, '')

            for sd in specViews:
                sd[0]._removeOrderedSpectrumViewIndex(sd[1])

    def _deleteChild(self, child):
        """Delete child object
        child is Pid or V3 object
        If child exists and is a valid child then delete otherwise log a warning
        """
        child = self.project.getByPid(child) if isinstance(child, str) else child

        if child and child in self._getChildrenByClass(child):
            # only delete objects that are valid children - calls private _delete
            # so now infinite loop with baseclass delete
            child._delete()
        elif child:
            getLogger().warning(f'{child} not deleted - not child of {self}')
        else:
            getLogger().warning(f'{child} not deleted')

    def _deletePeakList(self, child):
        """Delete child object and ensure that there always exists at least one peakList
        """
        with undoBlock():
            self._deleteChild(child)
            if not self.peakLists:
                # if there are no peakLists then create another (there must always be one)
                self.newPeakList()

    #-----------------------------------------------------------------------------------------
    # CCPN properties and functions
    #-----------------------------------------------------------------------------------------

    def _resetPeakLists(self):
        """Delete autocreated peaklists and reset
        CCPN Internal - not for general use
        required by nef importer
        """
        for peakList in list(self.peakLists):
            # overrides spectrum contains at least one peakList
            self._deleteChild(peakList)
        self._wrappedData.__dict__['_serialDict']['peakLists'] = 0

    @property
    def _apiDataSource(self) -> Nmr.DataSource:
        """ CCPN DataSource matching Spectrum"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """name, regularised as used for id"""
        return self._wrappedData.name.translate(Pid.remapSeparators)

    @property
    def _localCcpnSortKey(self) -> Tuple:
        """Local sorting key, in context of parent.
        """
        return (self._wrappedData.experiment.serial, self._wrappedData.serial)

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData (Nmr.DataSources) for all Spectrum children of parent Project"""
        return list(x for y in parent._wrappedData.sortedExperiments() for x in y.sortedDataSources())

    def _notifySpectrumViews(self, action):
        for sv in self.spectrumViews:
            sv._finaliseAction(action)

    # Attributes belonging to ExpDimRef and DataDimRef

    # def _mainExpDimRefs(self) -> tuple:
    #     """Get main API ExpDimRef (serial=1) for each dimension
    #     """
    #     result = []
    #     for ii, dataDim in enumerate(self._wrappedData.sortedDataDims()):
    #         # NB MUST loop over dataDims, in case of projection spectra
    #         result.append(dataDim.expDim.findFirstExpDimRef(serial=1))
    #     return tuple(result)

    # def _setExpDimRefAttribute(self, attributeName: str, value: Sequence, mandatory: bool = True):
    #     """Set main ExpDimRef attribute (serial=1) for each dimension"""
    #     apiDataSource = self._wrappedData
    #     if len(value) == apiDataSource.numDim:
    #         for ii, dataDim in enumerate(self._wrappedData.sortedDataDims()):
    #             # NB MUST loop over dataDims, in case of projection spectra
    #             expDimRef = dataDim.expDim.findFirstExpDimRef(serial=1)
    #             val = value[ii]
    #             if expDimRef is None and val is not None:
    #                 raise ValueError("Attempt to set attribute %s in dimension %s to %s - must be None" %
    #                                  (attributeName, ii + 1, val))
    #             elif val is None and mandatory:
    #                 raise ValueError(
    #                         "Attempt to set mandatory attribute %s to None in dimension %s: %s" %
    #                         (attributeName, ii + 1, val))
    #             else:
    #                 setattr(expDimRef, attributeName, val)

    #-----------------------------------------------------------------------------------------
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #-----------------------------------------------------------------------------------------

    @logCommand(get='self')
    def newPeakList(self, title: str = None, comment: str = None,
                    isSimulated: bool = False, symbolStyle: str = None, symbolColour: str = None,
                    textColour: str = None, **kwds):
        """Create new empty PeakList within Spectrum

        See the PeakList class for details.

        Optional keyword arguments can be passed in; see PeakList._newPeakList for details.

        :param title:
        :param comment:
        :param isSimulated:
        :param symbolStyle:
        :param symbolColour:
        :param textColour:
        :return: a new PeakList attached to the spectrum.
        """
        from ccpn.core.PeakList import _newPeakList

        return _newPeakList(self, title=title, comment=comment, isSimulated=isSimulated,
                            symbolStyle=symbolStyle, symbolColour=symbolColour, textColour=textColour,
                            **kwds)

    @logCommand(get='self')
    def newIntegralList(self, title: str = None, symbolColour: str = None,
                        textColour: str = None, comment: str = None, **kwds):
        """Create new IntegralList within Spectrum.

        See the IntegralList class for details.

        Optional keyword arguments can be passed in; see IntegralList._newIntegralList for details.

        :param self:
        :param title:
        :param symbolColour:
        :param textColour:
        :param comment:
        :return: a new IntegralList attached to the spectrum.
        """
        from ccpn.core.IntegralList import _newIntegralList

        return _newIntegralList(self, title=title, comment=comment,
                                symbolColour=symbolColour, textColour=textColour,
                                **kwds)

    @logCommand(get='self')
    def newMultipletList(self, title: str = None,
                         symbolColour: str = None, textColour: str = None, lineColour: str = None,
                         multipletAveraging=None,
                         comment: str = None, multiplets: Sequence[Union['Multiplet', str]] = None, **kwds):
        """Create new MultipletList within Spectrum.

        See the MultipletList class for details.

        Optional keyword arguments can be passed in; see MultipletList._newMultipletList for details.

        :param title: title string
        :param symbolColour:
        :param textColour:
        :param lineColour:
        :param multipletAveraging:
        :param comment: optional comment string
        :param multiplets: optional list of multiplets as objects or pids
        :return: a new MultipletList attached to the Spectrum.
        """
        from ccpn.core.MultipletList import _newMultipletList

        return _newMultipletList(self, title=title, comment=comment,
                                 lineColour=lineColour, symbolColour=symbolColour, textColour=textColour,
                                 multipletAveraging=multipletAveraging,
                                 multiplets=multiplets,
                                 **kwds)

    @logCommand(get='self')
    def newSpectrumHit(self, substanceName: str, pointNumber: int = 0,
                       pseudoDimensionNumber: int = 0, pseudoDimension=None,
                       figureOfMerit: float = None, meritCode: str = None, normalisedChange: float = None,
                       isConfirmed: bool = None, concentration: float = None, concentrationError: float = None,
                       concentrationUnit: str = None, comment: str = None, **kwds):
        """Create new SpectrumHit within Spectrum.

        See the SpectrumHit class for details.

        Optional keyword arguments can be passed in; see SpectrumHit._newSpectrumHit for details.

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
        :param comment: optional comment string
        :return: a new SpectrumHit instance.
        """
        from ccpn.core.SpectrumHit import _newSpectrumHit

        return _newSpectrumHit(self, substanceName=substanceName, pointNumber=pointNumber,
                               pseudoDimensionNumber=pseudoDimensionNumber, pseudoDimension=pseudoDimension,
                               figureOfMerit=figureOfMerit, meritCode=meritCode, normalisedChange=normalisedChange,
                               isConfirmed=isConfirmed, concentration=concentration, concentrationError=concentrationError,
                               concentrationUnit=concentrationUnit, comment=comment, **kwds)

    # GWV: this should nver be done by a user; newSpectum generates these on creation

    # @logCommand(get='self')
    # def newSpectrumReference(self, dimension: int, spectrometerFrequency: float,
    #                          isotopeCodes: Sequence[str], axisCode: str = None, measurementType: str = 'Shift',
    #                          maxAliasedFrequency: float = None, minAliasedFrequency: float = None,
    #                          foldingMode: str = None, axisUnit: str = None, referencePoint: float = 0.0,
    #                          referenceValue: float = 0.0, **kwds):
    #     """Create new SpectrumReference.
    #
    #     See the SpectrumReference class for details.
    #
    #     Optional keyword arguments can be passed in; see SpectrumReference._newSpectrumReference for details.
    #
    #     :param dimension:
    #     :param spectrometerFrequency:
    #     :param isotopeCodes:
    #     :param axisCode:
    #     :param measurementType:
    #     :param maxAliasedFrequency:
    #     :param minAliasedFrequency:
    #     :param foldingMode:
    #     :param axisUnit:
    #     :param referencePoint:
    #     :param referenceValue:
    #     :return: a new SpectrumReference instance.
    #     """
    #     from ccpn.core.SpectrumReference import _newSpectrumReference
    #
    #     return _newSpectrumReference(self, dimension=dimension, spectrometerFrequency=spectrometerFrequency,
    #                                  isotopeCodes=isotopeCodes, axisCode=axisCode, measurementType=measurementType,
    #                                  maxAliasedFrequency=maxAliasedFrequency, minAliasedFrequency=minAliasedFrequency,
    #                                  foldingMode=foldingMode, axisUnit=axisUnit, referencePoint=referencePoint,
    #                                  referenceValue=referenceValue, **kwds)

    #-----------------------------------------------------------------------------------------
    # Output, printing, etc
    #-----------------------------------------------------------------------------------------

    def __str__(self):
        return '<%s; %dD (%s)>' % (self.pid, self.dimensionCount, ','.join(self.axisCodes))

    def _infoString(self, includeDimensions=False):
        """Return info string about self, optionally including dimensional
        parameters
        """
        string = '================= %s =================\n' % self
        string += 'path = %s\n' % self.filePath
        string += 'dataFormat = %s\n' % self.dataFormat
        string += 'dimensions = %s\n' % self.dimensionCount
        string += 'sizes = (%s)\n' % ' x '.join([str(d) for d in self.pointCounts])
        for attr in """
                scale 
                noiseLevel 
                experimentName
                """.split():
            value = getattr(self, attr)
            string += '%s = %s\n' % (attr, value)

        if includeDimensions:
            string += '\n'
            for attr in """
                dimensions
                axisCodes
                pointCounts
                isComplex
                dimensionTypes
                isotopeCodes
                measurementTypes
                spectralWidths
                spectralWidthsHz
                spectrometerFrequencies
                referencePoints
                referenceValues
                axisUnits
                foldingModes
                windowFunctions
                lorentzianBroadenings
                gaussianBroadenings
                phases0
                phases1
                assignmentTolerances
                """.split():
                values = getattr(self, attr)
                string += '%-25s: %s\n' % (attr,
                                           ' '.join(['%-20s' % str(v) for v in values])
                                           )
        return string

    def printParameters(self, includeDimensions=True):
        """Print the info string
        """
        print(self._infoString(includeDimensions))


#=========================================================================================
# New and empty spectra
#=========================================================================================

# Hack; remove the api notifier on create
# _notifiers = [nf for nf in Project._apiNotifiers if nf[3] == '__init__' and 'cls' in nf[1] and nf[1]['cls'] == Spectrum]
# if len(_notifiers) == 1:
#     Project._apiNotifiers.remove(_notifiers[0])


@newObject(Spectrum)
def _newSpectrumFromDataSource(project, dataStore, dataSource, name=None) -> Spectrum:
    """Create a new Spectrum instance with name using the data in dataStore and dataSource
    :returns Spectrum instance or None on error
    """
    from ccpn.core.SpectrumReference import _newSpectrumReference

    if dataStore is None:
        raise ValueError('dataStore cannot be None')

    if dataSource is None:
        raise ValueError('dataSource cannot be None')
    if dataSource.dimensionCount == 0:
        raise ValueError('dataSource.dimensionCount = 0')

    if name is None:
        name = dataStore.path.basename
    # assure unique name
    name = Spectrum._uniqueName(project=project, name=name)

    # check the dataSources of all spectra of the project for open file pointers to the same file
    for ds in [sp._dataSource for sp in project.spectra if sp.hasValidPath()]:
        if ds.path == dataStore.aPath() and ds.hasOpenFile():
            raise RuntimeError('Unable to create new Spectrum; project has existing open dataSource %s' % ds)

    apiProject = project._wrappedData
    apiExperiment = apiProject.newExperiment(name=name, numDim=dataSource.dimensionCount)

    apiDataSource = apiExperiment.newDataSource(name=name,
                                                dataStore=None,
                                                numDim=dataSource.dimensionCount,
                                                dataType='processed'
                                                )
    # Done with api generation; Create the Spectrum object

    # Agggh, cannot do
    #   spectrum = Spectrum(self, apiDataSource)
    # as the object was magically already created
    # This was done by Project._newApiObject, called from Nmr.DataSource.__init__ through an api notifier.
    # This notifier is set in the AbstractWrapper class and is part of the machinery generation; i.e.
    # _linkWrapperClasses (needs overhaul!!)

    spectrum = project._data2Obj.get(apiDataSource)
    if spectrum is None:
        raise RuntimeError("something went wrong creating a new Spectrum instance")
    spectrum._apiExperiment = apiExperiment

    # initialise the dimensional SpectrumReference objects
    with inactivity():
        for dim in dataSource.dimensions:
            _newSpectrumReference(spectrum, dimension=dim, dataSource=dataSource)

    # Set the references between spectrum and dataStore
    dataStore.dataFormat = dataSource.dataFormat
    dataStore.spectrum = spectrum
    dataStore._saveInternal()
    spectrum.setTraitValue('_dataStore', dataStore, force=True)

    # update dataSource with proper expanded path
    dataSource.setPath(dataStore.aPath())
    # Update all parameters from the dataSource to the Spectrum instance; retain the dataSource instance
    dataSource.exportToSpectrum(spectrum, includePath=False)
    spectrum.setTraitValue('_dataSource', dataSource, force=True)

    # Quietly update some essentials
    with inactivity():
        # Link to default (i.e. first) chemicalShiftList
        spectrum.chemicalShiftList = project.chemicalShiftLists[0]
        # Assure at least one peakList
        if len(spectrum.peakLists) == 0:
            spectrum.newPeakList()

        # Hack to trigger initialisation of contours
        spectrum.positiveContourCount = 0
        spectrum.negativeContourCount = 0

        # set default assignment tolerances
        spectrum.assignmentTolerances = spectrum.defaultAssignmentTolerances

        spectrum._updateParameterValues()
        spectrum._saveSpectrumMetaData()

    return spectrum


def _newEmptySpectrum(project: Project, isotopeCodes: Sequence[str], name: str = 'emptySpectrum') -> Spectrum:
    """Creation of new Empty Spectrum;
    :return: Spectrum instance or None on error
    """

    if not isIterable(isotopeCodes) or len(isotopeCodes) == 0:
        raise ValueError('invalid isotopeCodes "%s"' % isotopeCodes)

    dataStore = DataStore()

    # Intialise a dataSource instance
    dataSource = EmptySpectrumDataSource()
    if dataSource is None:
        raise RuntimeError('Error creating empty DataSource')
    # Fill in some of the parameters
    dataSource.dimensionCount = len(isotopeCodes)
    dataSource.isotopeCodes = isotopeCodes
    dataSource._setSpectralParametersFromIsotopeCodes()
    dataSource._assureProperDimensionality()

    spectrum = _newSpectrumFromDataSource(project, dataStore, dataSource, name)

    return spectrum


def _newSpectrum(project: Project, path: (str, Path), name: str=None) -> (Spectrum, None):
    """Creation of new Spectrum;
    :return: Spectrum instance or None on error
    """

    logger = getLogger()

    dataStore = DataStore.newFromPath(path)
    if not dataStore.exists():
        dataStore.errorMessage()
        return None

    _path = dataStore.aPath()

    # Try to determine data format from the path and intialise a dataSource instance with parsed parameters
    dataSource = checkPathForSpectrumFormats(path=_path)
    if dataSource is None:
        logger.warning('Invalid spectrum path "%s"' % path)  # report the argument given
        return None

    spectrum = _newSpectrumFromDataSource(project, dataStore, dataSource, name)
    # spectrum._updateParameterValues()

    return spectrum


def _extractRegionToFile(spectrum, dimensions, position, dataStore) -> Spectrum:
    """Extract a region of spectrum, defined by dimensions, position to path defined by dataStore
    (optionally auto-generated from spectrum.path)

    :param dimensions:  [dim_a, dim_b, ...];  defining dimensions to be extracted (1-based)
    :param position, spectrum position-vector of length spectrum.dimensionCount (list, tuple; 1-based)
    """

    getLogger().debug('Extracting from %s, dimensions=%r, position=%r, dataStore=%s, dataFormat %r' %
                      (spectrum, dimensions, position, dataStore, dataStore.dataFormat))

    if spectrum is None or not isinstance(spectrum, Spectrum):
        raise ValueError('invalid spectrum argument %r' % spectrum)
    if spectrum._dataSource is None:
        raise RuntimeError('No proper (filePath, dataFormat) set for %s' % spectrum)

    for dim in dimensions:
        if dim < 1 or dim > spectrum.dimensionCount:
            raise ValueError('Invalid dimnsion %r in dimensions argument (%s)' % (dim, dimensions))
    dimensions = list(dimensions)  # assure a list

    position = spectrum._dataSource.checkForValidPosition(position)

    if dataStore is None:
        raise ValueError('Undefined dataStore')
    if dataStore.dataFormat is None:
        raise ValueError('Undefined dataStore.dataFormat')

    # dimString = '_' + '_'.join(spectrum.getByDimensions('axisCodes', dimensions))
    # if name is None:
    #     name = spectrum.name + dimString

    klass = getDataFormats().get(dataStore.dataFormat)
    if klass is None:
        raise ValueError('Invalid dataStore.dataFormat %r' % dataStore.dataFormat)

    # Do path-related stuff
    suffix = klass.suffixes[0] if len(klass.suffixes) > 0 else '.dat'
    # if dataStore is None:
    #     dataStore = DataStore.newFromPath(spectrum.filePath,
    #                                       appendToName=dimString, withSuffix=suffix, autoVersioning=True,
    #                                       dataFormat=klass.dataFormat
    #                                      )
    # else:
    #     dataStore.dataFormat = klass.dataFormat

    # Create a dataSource object
    dataSource = klass(spectrum=spectrum)

    disgardedDimensions = list(set(spectrum.dimensions) - set(dimensions))
    # The dimensional parameters of spectrum were copied on initialisation
    # remap the N-axes (as defined by the N items in the dimensions argument) onto the first N axes
    # of the dataSource;
    dimensionsMap = dict(zip(dimensions + disgardedDimensions, dataSource.dimensions))
    dataSource._mapDimensionalParameters(dimensionsMap=dimensionsMap)
    # Now reduce the dimensionality to the length of dimensions; i.e. the dimensionality of the
    # new spectrum
    dataSource.setDimensionCount(len(dimensions))

    # copy the data
    indexMap = dict((k - 1, v - 1) for k, v in dimensionsMap.items())  # source -> destination
    inverseIndexMap = dict((v - 1, k - 1) for k, v, in dimensionsMap.items())  # destination -> source

    readSliceDim = dimensions[0]  # first retained dimension from the original data
    writeSliceDim = 1  # which was mapped to the first dimension of the new data

    sliceTuples = [(p, p) for p in position]
    # assure full range for all dimensions, other than readSliceDim
    for dim in dimensions[1:]:
        sliceTuples[dim - 1] = (1, spectrum.pointCounts[dim - 1])

    with spectrum._dataSource.openExistingFile() as input:
        with dataSource.openNewFile(path=dataStore.aPath()) as output:
            # loop over all requested slices
            for position, aliased in input._selectedPointsIterator(sliceTuples=sliceTuples,
                                                                   excludeDimensions=[readSliceDim]):
                data = input.getSliceData(position, readSliceDim)

                # map the input position to the output position and write the data
                outPosition = [position[inverseIndexMap[p]] for p in output.axes]
                # print('>>>', position, outPosition)
                output.setSliceData(data, outPosition, writeSliceDim)

    # create the new spectrum from the dataSource
    newSpectrum = _newSpectrumFromDataSource(project=spectrum.project,
                                             dataStore=dataStore,
                                             dataSource=dataSource)

    # copy/set some more parameters (e.g. noiseLevel)
    spectrum._copyNonDimensionalParameters(newSpectrum)
    newSpectrum._updateParameterValues()

    return newSpectrum


# Additional Notifiers:
Project._apiNotifiers.extend(
        (
            # GWV: not needed?
            # ('_finaliseApiRename', {}, Nmr.DataSource._metaclass.qualifiedName(), 'setName'),
            #
            ('_notifyRelatedApiObject', {'pathToObject': 'dataSources', 'action': 'change'},
             Nmr.Experiment._metaclass.qualifiedName(), ''),

            ('_notifyRelatedApiObject', {'pathToObject': 'dataSource', 'action': 'change'},
             Nmr.AbstractDataDim._metaclass.qualifiedName(), ''),

            ('_notifyRelatedApiObject', {'pathToObject': 'dataDim.dataSource', 'action': 'change'},
             Nmr.DataDimRef._metaclass.qualifiedName(), ''),

            ('_notifyRelatedApiObject', {'pathToObject': 'experiment.dataSources', 'action': 'change'},
             Nmr.ExpDim._metaclass.qualifiedName(), ''),

            ('_notifyRelatedApiObject', {'pathToObject': 'expDim.experiment.dataSources', 'action': 'change'},
             Nmr.ExpDimRef._metaclass.qualifiedName(), ''),

            ('_notifyRelatedApiObject', {'pathToObject': 'nmrDataSources', 'action': 'change'},
             DataLocation.AbstractDataStore._metaclass.qualifiedName(), ''),

            )
        )
