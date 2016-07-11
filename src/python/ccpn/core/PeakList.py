"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, List, Optional
import collections
import numpy
from numpy import argwhere
from scipy.ndimage import maximum_filter

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Spectrum import Spectrum
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakList as ApiPeakList

from ccpnmodel.ccpncore.lib.CopyData import copySubTree
from ccpnmodel.ccpncore.lib._ccp.nmr.Nmr.PeakList import fitExistingPeakList
from ccpnmodel.ccpncore.lib.spectrum import Spectrum as spectrumLib
from ccpnmodel.ccpncore.lib._ccp.nmr.Nmr.PeakList import pickNewPeaks

class PeakList(AbstractWrapperObject):
  """Peak List."""
  
  #: Short class name, for PID.
  shortClassName = 'PL'
  # Attribute it necessary as subclasses must use superclass className
  className = 'PeakList'

  _parentClass = Spectrum

  #: Name of plural link to instances of class
  _pluralLinkName = 'peakLists'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiPeakList._metaclass.qualifiedName()

  # Special error-raising functions for people who think PeakList is a list
  def __iter__(self):
    raise TypeError("'PeakList object is not iterable - for a list of peaks use Peaklist.peaks")

  def __getitem__(self, index):
    raise TypeError("'PeakList object does not support indexing - for a list of peaks use Peaklist.peaks")

  def __len__(self):
    raise TypeError("'PeakList object has no length - for a list of peaks use Peaklist.peaks")

  # CCPN properties  
  @property
  def _apiPeakList(self) -> ApiPeakList:
    """ API peakLists matching PeakList"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number of PeakList, used in Pid and to identify the PeakList. """
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> Spectrum:
    """Spectrum containing Peaklist."""
    return  self._project._data2Obj[self._wrappedData.dataSource]
  
  spectrum = _parent
  
  @property
  def title(self) -> str:
    """title of PeakList"""
    return self._wrappedData.name
    
  @title.setter
  def title(self, value:str):
    self._wrappedData.name = value
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def symbolStyle(self) -> str:
    """Symbol style for peak annotation display"""
    return self._wrappedData.symbolStyle

  @symbolStyle.setter
  def symbolStyle(self, value:str):
    self._wrappedData.symbolStyle = value

  @property
  def symbolColour(self) -> str:
    """Symbol colour for peak annotation display"""
    return self._wrappedData.symbolColour

  @symbolColour.setter
  def symbolColour(self, value:str):
    self._wrappedData.symbolColour = value

  @property
  def textColour(self) -> str:
    """Text colour for peak annotation display"""
    return self._wrappedData.textColour

  @textColour.setter
  def textColour(self, value:str):
    self._wrappedData.textColour = value

  @property
  def isSimulated(self) -> bool:
    """Is peakList simulated"""
    return self._wrappedData.isSimulated

  @isSimulated.setter
  def isSimulated(self, value:bool):
    self._wrappedData.isSimulated = value

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: Spectrum)-> list:
    """get wrappedData (PeakLists) for all PeakList children of parent Spectrum"""
    return [x for x in parent._wrappedData.sortedPeakLists() if x.dataType == 'Peak']

  # Library functions

  def pickPeaksNd(self, positions:Sequence[float]=None,
                  doPos:bool=True, doNeg:bool=True,
                  fitMethod:str='gaussian', excludedRegions=None,
                  excludedDiagonalDims=None, excludedDiagonalTransform=None):

    # TODO NBNB Add doc string and put type annotation on all parameters

    defaults = collections.OrderedDict(
      ( ('positions', None), ('doPos', True), ('doNeg', True),
        ('fitMethod', 'gaussian'), ('excludedRegions', None), ('excludedDiagonalDims', None),
        ('excludedDiagonalTransform', None)
      )
    )
    # NBNB TODO dataDims are NOT being echoed.
    # NBNB TODO function needs refactoring because 1) we have API objects (dataDims) as input
    # which 2) makes proper echoing impossible.



    self._startFunctionCommandBlock('pickPeaksNd', values=locals(), defaults=defaults)
    # try:
    if len(positions[0]) != self.spectrum.dimensionCount:
      positions = list(sorted(map(list, zip(*positions))))

    startPoint = []
    endPoint = []
    dataDims = self.spectrum._apiDataSource.sortedDataDims()
    spectrum = self.spectrum
    for ii, dataDim in enumerate(dataDims):
      # -1 below because points start at 1 in data model
      position0 = dataDim.primaryDataDimRef.valueToPoint(positions[0][ii]) - 1
      position1 = dataDim.primaryDataDimRef.valueToPoint(positions[1][ii]) - 1
      position0, position1 = min(position0, position1), max(position0, position1)
      # want integer grid points above position0 and below position1
      # add 1 to position0 because above
      # add 1 to position1 because doing start <= x < end not <= end
      # yes, this negates -1 above but they are for different reasons
      position0 = int(position0+1)
      position1 = int(position1+1)
      startPoint.append((dataDim.dim, position0))
      endPoint.append((dataDim.dim, position1))

    startPoints = [point[1] for point in sorted(startPoint)]
    endPoints = [point[1] for point in sorted(endPoint)]
    # print(isoOrdering, startPoint, startPoints, endPoint, endPoints)

    posLevel = spectrum.positiveContourBase if doPos else None
    negLevel = spectrum.negativeContourBase if doNeg else None

    apiPeaks = pickNewPeaks(self._apiPeakList, startPoint=startPoints, endPoint=endPoints,
                   posLevel=posLevel, negLevel=negLevel, fitMethod=fitMethod, excludedRegions=excludedRegions,
                   excludedDiagonalDims=excludedDiagonalDims, excludedDiagonalTransform=excludedDiagonalTransform)

    data2ObjDict = self._project._data2Obj

    # finally:
    #   self._project._appBase._endCommandBlock()

    return [data2ObjDict[apiPeak] for apiPeak in apiPeaks]

  # def pickPeaks1d(self:'PeakList', spectrumView, size:int=3, mode:str='wrap'):
  def pickPeaks1d(self, data1d, dataRange, intensityRange=None, size:int=3, mode:str='wrap') -> List['Peak']:
    """
    Pick 1D peaks form data1d float array
    """

    self._project.suspendNotification()

    try:
      if dataRange[0] < dataRange[1]:
        dataRange[0], dataRange[1] = dataRange[1], dataRange[0]
      # code below assumes that dataRange[1] > dataRange[0]
      peaks = []
      spectrum = self.spectrum
      data1d = spectrum._apiDataSource.get1dSpectrumData()
      selectedData = data1d[:, (data1d[0] < dataRange[0]) * (data1d[0] > dataRange[1])]
      if selectedData.size == 0:
        return peaks
      maxFilter = maximum_filter(selectedData[1], size=size, mode=mode)
      boolsMax = selectedData[1] == maxFilter
      if intensityRange is None: 
        spectrum.estimateNoise()*10
        if selectedData.max() < threshold:
          return peaks
        boolsVal = selectedData[1] > threshold
        boolsPeak = boolsVal & boolsMax
      else:
        boolsPeak = boolsMax
      indices = argwhere(boolsPeak) # True positional indices
      for position in indices:
        peakPosition = [float(selectedData[0][position])]
        height = selectedData[1][position]
        if intensityRange is None or intensityRange[0] <= height <= intensityRange[1]:
          peaks.append(self.newPeak(height=float(height), position=peakPosition))

    finally:
      self._project.resumeNotification()

    return peaks


  def pickPeaks1dFiltered(self, size:int=9, mode:str='wrap', ignoredRegions=None,
                          noiseThreshold=None):
    """
    Pick 1D peaks form data in  self.spectrum
    """
    defaults = collections.OrderedDict(
      ( ('size', 9), ('mode', 'wrap'), ('ignoredRegions', None), ('noiseThreshold', None)
      )
    )

    self._startFunctionCommandBlock('pickPeaks1dFiltered', values=locals(), defaults=defaults)
    ll = []
    try:
      if not ignoredRegions:
        ignoredRegions = [[-20.1,-19.1]]

      peaks = []
      spectrum = self.spectrum

      data = spectrum._apiDataSource.get1dSpectrumData()


      ppmValues = data[0]

      if noiseThreshold == 0:
        noiseThreshold = spectrum.estimateNoise()*5

      masks = []
      for region in ignoredRegions:

        mask = (ppmValues > region[0]) | (ppmValues < region[1])
        masks.append(mask)

      fullmask = [all(mask) for mask in zip(*masks)]
      newArray2 = (numpy.ma.MaskedArray(data, mask=numpy.logical_not((fullmask, fullmask))))

      if (newArray2.size == 0) or (data.max() < noiseThreshold):
       return peaks
      boolsVal = newArray2[1] > noiseThreshold
      maxFilter = maximum_filter(newArray2[1], size=size, mode=mode)


      boolsMax = newArray2[1] == maxFilter
      boolsPeak = boolsVal & boolsMax
      indices = argwhere(boolsPeak) # True positional indices
      for position in indices:
        peakPosition = [float(newArray2[0][position])]
        height = newArray2[1][position]
        peaks.append(self.newPeak(height=float(height), position=peakPosition))

    finally:
      self._project._appBase._endCommandBlock()

    return peaks



  def subtractPeakLists(self, peakList2:'PeakList') -> 'PeakList':
    """
    Subtracts peaks in peakList2 from peaks in peakList1, based on position,
    and puts those in a new peakList3.  Assumes a common spectrum for now.
    """

    def _havePeakNearPosition(values, tolerances, peaks) -> Optional['Peak']:

      for peak in peaks:
        for i, position in enumerate(peak.position):
          if abs(position - values[i]) > tolerances[i]:
            break
        else:
          return peak

    self._startFunctionCommandBlock('subtractPeakLists', values={'peakList2':peakList2},
                                    parName='newPeakList')

    try:

      spectrum = self.spectrum

      assert spectrum is peakList2.spectrum, 'For now requires both peak lists to be in same spectrum'

      # dataDims = spectrum.sortedDataDims()
      tolerances = self.spectrum.assignmentTolerances

      peaks2 = peakList2.peaks
      peakList3 = spectrum.newPeakList()

      for peak1 in self.peaks:
        values1 = [peak1.position[dim] for dim in range(len(peak1.position))]
        if not _havePeakNearPosition(values1, tolerances, peaks2):
          peakList3.newPeak(height=peak1.height, volume=peak1.volume, figureOfMerit=peak1.figureOfMerit,
                            annotation=peak1.annotation, position=peak1.position,
                            pointPosition=peak1.pointPosition)


    finally:
      self._project._appBase._endCommandBlock()

    return peakList3

  # # Removed as not used in project: Rasmus Fogh 21/6/2016
  # def copyPeaks(self, sinkSpectrum:'Spectrum', fitPositions:bool=False):
  #   refAxisCodes = self.spectrum.axisCodes
  #   sinkAxisCodes = sinkSpectrum.axisCodes
  #
  #   if not spectrumLib.doAxisCodesMatch(sinkAxisCodes, refAxisCodes):
  #     print('axis codes of the source and sink peaklists do not match')
  #     return
  #
  #   if not fitPositions:
  #     copySubTree(self, sinkSpectrum)
  #
  #   # else:

  def refit(self, method:str='gaussian'):
    fitExistingPeakList(self._apiPeakList, method)

  def restrictedPick(self, positionCodeDict, doPos, doNeg):

    codes = list(positionCodeDict.keys())
    positions = [positionCodeDict[code] for code in codes]
    axisCodeMapping = spectrumLib._axisCodeMapIndices(codes, self.spectrum.axisCodes)
    tolerances = self.spectrum.assignmentTolerances
    limits = self.spectrum.spectrumLimits
    selectedRegion = []

    for ii, mapping in enumerate(axisCodeMapping):
      if mapping is not None:
        selectedRegion.insert(ii, [positions[mapping]-tolerances[ii], positions[mapping]+tolerances[ii]])
      else:

        selectedRegion.insert(ii, [limits[ii][0], limits[ii][1]])

    regionToPick = list(zip(*selectedRegion))
    peaks = self.pickPeaksNd(regionToPick, self.spectrum._wrappedData.sortedDataDims(), doPos=doPos,
                             doNeg=doNeg)
    return peaks



# Connections to parents:

def _newPeakList(self:Spectrum, title:str=None, comment:str=None,
             isSimulated:bool=False) -> PeakList:
  """Create new empty ccpn.PeakList within ccpn.Spectrum"""

  defaults = collections.OrderedDict((('title', None), ('comment', None), ('isSimulated', False)))

  apiDataSource = self._wrappedData
  self._startFunctionCommandBlock('newPeakList', values=locals(), defaults=defaults,
                                  parName='newPeakList')
  try:
    obj = apiDataSource.newPeakList(name=title, details=comment, isSimulated=isSimulated)
  finally:
    self._project._appBase._endCommandBlock()
  return self._project._data2Obj.get(obj)

Spectrum.newPeakList = _newPeakList
del _newPeakList

# Notifiers:
