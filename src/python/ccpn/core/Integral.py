"""Module Documentation here

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

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.IntegralList import IntegralList
from ccpn.core.Peak import Peak
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from typing import Optional, Tuple, Sequence, List

class Integral(AbstractWrapperObject):
  """n-dimensional Integral. Includes values for per-dimension values.
  """
  
  #: Short class name, for PID.
  shortClassName = 'IT'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Integral'

  #: Name of plural link to instances of class
  _pluralLinkName = 'integrals'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class - NB shared with Peak class
  _apiClassQualifiedName = Nmr.Peak._metaclass.qualifiedName()

  # Notifiers are handled through the Peak class (which shares the ApiPeak wrapped object)
  _registerClassNotifiers = False
  

  # CCPN properties  
  @property
  def _apiPeak(self) -> Nmr.Peak:
    """ API peaks matching Integral"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number of Integral, used in Pid and to identify the Integral. """
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> IntegralList:
    """IntegralList containing Integral."""
    return  self._project._data2Obj[self._wrappedData.peakList]
  
  integralList = _parent

  @property
  def value(self) -> Optional[float]:
    """value of Integral"""
    return self._wrappedData.volume

  @value.setter
  def value(self, value:float):
    self._wrappedData.volume = value

  @property
  def valueError(self) -> Optional[float]:
    """value error of Integral"""
    return self._wrappedData.volumeError

  @valueError.setter
  def valueError(self, value:float):
    self._wrappedData.volumeError = value

  @property
  def bias(self) -> float:
    """Baseplane offset used in calculating integral value"""
    return self._wrappedData.offset

  @bias.setter
  def bias(self, value:float):
    self._wrappedData.offset = value

  @property
  def figureOfMerit(self) -> Optional[float]:
    """figureOfMerit of Integral, between 0.0 and 1.0 inclusive."""
    return self._wrappedData.figOfMerit

  @figureOfMerit.setter
  def figureOfMerit(self, value:float):
    self._wrappedData.figOfMerit = value

  @property
  def slopes(self) -> List[float]:
    """slope (in dimension order) used in calculating integral value

    The slope is defined as the intensity in point i+1 minus the intensity in point i"""
    return [x.slope for x in self._wrappedData.sortedPeakDims()]

  @slopes.setter
  def slopes(self, value):
    peakDims = self._wrappedData.sortedPeakDims()
    if len(value) == len(peakDims):
      for tt in zip(peakDims, value):
        tt[0].slope = tt[1]
    else:
      raise ValueError("The slopes value %s does not match the dimensionality of the spectrum, %s"
                       % value, len(peakDims))


  @figureOfMerit.setter
  def figureOfMerit(self, value:float):
    self._wrappedData.figOfMerit = value

  @property
  def annotation(self) -> Optional[str]:
    """Integral text annotation"""
    return self._wrappedData.annotation
    
  @annotation.setter
  def annotation(self, value:str):
    self._wrappedData.annotation = value

  @property
  def comment(self) -> Optional[str]:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def axisCodes(self) -> Tuple[str, ...]:
    """Spectrum axis codes in dimension order matching position."""
    return self.peakList.spectrum.axisCodes

  @property
  def limits(self) -> List[Tuple[float,float]]:
    """Integration limits in axis value (ppm), per dimension, with lowest value first

    For Fid or sampled dimensions the individual limit values will be points"""
    result = []
    dataDimRefs = self.integralList.spectrum._mainDataDimRefs()
    for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
      dataDimRef = dataDimRefs[ii]
      if dataDimRef is None:
        value = peakDim.position
        halfWidth = 0.5 * (peakDim.boxWidth or 0)
      else:
        value = peakDim.value
        halfWidth = abs(0.5 * (peakDim.boxWidth or 0) * dataDimRef.valuePerPoint)
      result.append(value - halfWidth, value + halfWidth)
    #
    return result

  @limits.setter
  def limits(self, value):
    dataDimRefs = self.integralList.spectrum._mainDataDimRefs()
    for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
      dataDimRef = dataDimRefs[ii]
      limit1, limit2 = value[ii]
      if None in value[ii]:
        peakDim.position = None
        peakDim.boxWidth = None
      elif dataDimRef is None:
        peakDim.position = 0.5 * (limit1 + limit2)
        peakDim.boxWidth = abs(limit1 - limit2)
      else:
        peakDim.value = 0.5 * (limit1 + limit2)
        peakDim.boxWidth = abs((limit1 - limit2)/ dataDimRef.valuePerPoint)

  @property
  def pointlimits(self) -> List[Tuple[float,float]]:
    """Integration limits in points, per dimension, with lowest value first"""
    result = []
    for peakDim in self._wrappedData.sortedPeakDims():
      position = peakDim.position
      halfWidth = 0.5 * (peakDim.boxWidth or 0)
      result.append(position - halfWidth, position + halfWidth)
    #
    return result

  @pointlimits.setter
  def pointlimits(self, value):
    peakDims = self._wrappedData.sortedPeakDims()
    if len(value) == len(peakDims):
      for ii, peakDim in enumerate(peakDims):
        if None in value[ii]:
          peakDim.position = None
          peakDim.boxWidth = None
        else:
          limit1, limit2 = value[ii]
          peakDim.position = 0.5 * (limit1 + limit2)
          peakDim.boxWidth = abs(limit1 - limit2)
    else:
      raise ValueError("The slopes value %s does not match the dimensionality of the spectrum, %s"
                       % value, len(peakDims))

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: IntegralList)-> Tuple[Nmr.Peak, ...]:
    """get wrappedData (Peaks) for all Integral children of parent IntegralList"""
    return parent._wrappedData.sortedPeaks()

# Connections to parents:
IntegralList._childClasses.append(Integral)

def _newIntegral(self:IntegralList, value:List[float]=None,
                 valueError:List[float]=None, bias:float=0, slopes:List[float]=None,
                 figureOfMerit:float=1.0, annotation:str=None, comment:str=None,
                 limits:Sequence[Tuple[float,float]]=(),
                 pointLimits:Sequence[Tuple[float,float]]=()) -> Integral:
  """Create new ccpn.Integral within ccpn.IntegralList"""

  undo = self._project._undo
  if undo is not None:
    undo.increaseBlocking()
  self._project.blankNotification()
  try:
    apiPeakList = self._apiPeakList
    apiPeak = apiPeakList.newPeak(volume=value, volumeError=valueError, figOfMerit=figureOfMerit,
                                offset=bias,annotation=annotation, details=comment)

    result = self._project._data2Obj.get(apiPeak)
    if pointLimits:
      result.pointLimits = pointLimits
    elif limits:
      result.limits = limits
    if slopes:
      result.slopes = slopes

  finally:
    self._project.unblankNotification()
    if undo is not None:
      undo.decreaseBlocking()

  if undo is not None:
    undo.newItem(apiPeak.delete, self.newIntegral, redoKwargs={
       'value':value, 'valueError':valueError,'figureOfMerit':figureOfMerit,
      'annotation':annotation, 'comment':comment, 'limits':limits,
      'pointLimits':pointLimits, 'bias':bias, 'slopes':slopes})

  # Do creation notifications
  result._finaliseAction('create')

  return result

IntegralList.newIntegral = _newIntegral
del _newIntegral


def _factoryFunction(project:Project, wrappedData:Nmr.Peak) -> AbstractWrapperObject:
  """create Peak or Integral from API Peak"""
  if wrappedData.peakList.dataType == 'Peak':
    return Peak(project, wrappedData)
  elif wrappedData.peakList.dataType == 'Integral':
    return Integral(project, wrappedData)
  else:
    raise ValueError("API Peak object has illegal parent dataType: %s. Must be 'Peak' or 'Integral"
                     % wrappedData.dataType)


Integral._factoryFunction = staticmethod(_factoryFunction)
Peak._factoryFunction = staticmethod(_factoryFunction)

# Additional Notifiers:
# NB API level notifiers are defined in the Peak file for API Peaks
# They will have the same effect for integrals