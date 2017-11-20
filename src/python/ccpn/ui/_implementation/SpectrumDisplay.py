"""GUI SpectrumDisplay class

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:41 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Tuple, Optional
import collections

from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.ui._implementation.Window import Window
from ccpn.util import Common as commonUtil
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import ResonanceGroup as ApiResonanceGroup
from ccpnmodel.ccpncore.api.ccpnmr.gui.Window import Window as ApiWindow
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import BoundDisplay as ApiBoundDisplay
from ccpn.util.Logging import getLogger

logger = getLogger()

# _ccpnInternalData references
# SV_TITLE = className  # may not be needed
ORDEREDSPECTRA = '_orderedSpectra'


class SpectrumDisplay(AbstractWrapperObject):
  """Spectrum display for 1D or nD spectrum"""
  
  #: Short class name, for PID.
  shortClassName = 'GD'
  # Attribute it necessary as subclasses must use superclass className
  className = 'SpectrumDisplay'

  _parentClass = Project

  #: Name of plural link to instances of class
  _pluralLinkName = 'spectrumDisplays'
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiBoundDisplay._metaclass.qualifiedName()

  # CCPN properties  
  @property
  def _apiSpectrumDisplay(self) -> ApiBoundDisplay:
    """ CCPN SpectrumDisplay matching SpectrumDisplay"""
    return self._wrappedData
  
  @property
  def _key(self) -> str:
    """short form of name, corrected to use for id"""
    return self._wrappedData.name.translate(Pid.remapSeparators)

  @property
  def title(self) -> str:
    """SpectrumDisplay title

    (corresponds to its name, but the name 'name' is taken by PyQt"""
    return self._wrappedData.name

  @property
  def _parent(self) -> Project:
    """Project containing spectrumDisplay."""
    return self._project

  project = _parent

  @property
  def stripDirection(self) -> str:
    """Strip axis direction ('X', 'Y', None) - None only for non-strip plots"""
    return self._wrappedData.stripDirection

  @property
  def stripCount(self) -> str:
    """Number of strips"""
    return self._wrappedData.stripCount

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def axisCodes(self) -> Tuple[str, ...]:
    """Fixed string Axis codes in original display order (X, Y, Z1, Z2, ...)"""
    # TODO axisCodes shold be unique, but I am not sure this is enforced
    return self._wrappedData.axisCodes

  @property
  def axisOrder(self) ->  Tuple[str, ...]:
    """String Axis codes in display order (X, Y, Z1, Z2, ...), determine axis display order"""
    return self._wrappedData.axisOrder

  @axisOrder.setter
  def axisOrder(self, value:Sequence):
    self._wrappedData.axisOrder = value

  @property
  def is1D(self) -> bool:
    """True if this is a 1D display."""
    tt = self.axisCodes
    return bool(tt and tt[1] == 'intensity')

  @property
  def window(self) -> Window:
    """Gui window showing SpectrumDisplay"""
    # TODO: RASMUS window clashes with a Qt attribute.
    # This should be renamed, but that also requires refactoring
    # possibly with a model change that modifies the Task/Window/Module relationship
    return self._project._data2Obj.get(self._wrappedData.window)

  @window.setter
  def window(self, value:Window):
    value = self.getByPid(value) if isinstance(value, str) else value
    self._wrappedData.window = value and value._wrappedData

  @property
  def nmrResidue(self) -> NmrResidue:
    """NmrResidue attached to SpectrumDisplay"""
    return  self._project._data2Obj.get(self._wrappedData.resonanceGroup)

  @nmrResidue.setter
  def nmrResidue(self, value:NmrResidue):
    value = self.getByPid(value) if isinstance(value, str) else value
    self._wrappedData.resonanceGroup = value and value._wrappedData

  @property
  def positions(self) ->  Tuple[float, ...]:
    """Axis centre positions, in display order"""
    return self._wrappedData.positions

  @positions.setter
  def positions(self, value):
    self._wrappedData.positions = value

  @property
  def widths(self) ->  Tuple[float, ...]:
    """Axis display widths, in display order"""
    return self._wrappedData.widths

  @widths.setter
  def widths(self, value):
    self._wrappedData.widths = value

  @property
  def units(self) ->  Tuple[str, ...]:
    """Axis units, in display order"""
    return self._wrappedData.units

  @property
  def parameters(self) -> dict:
    """Keyword-value dictionary of parameters.
    NB the value is a copy - modifying it will not modify the actual data.

    Values can be anything that can be exported to JSON,
    including OrderedDict, numpy.ndarray, ccpn.util.Tensor,
    or pandas DataFrame, Series, or Panel"""
    return dict((x.name, x.value) for x in self._wrappedData.parameters)

  def setParameter(self, name:str, value):
    """Add name:value to parameters, overwriting existing entries"""
    apiData = self._wrappedData
    parameter = apiData.findFirstParameter(name=name)
    if parameter is None:
      apiData.newParameter(name=name, value=value)
    else:
      parameter.value = value

  def deleteParameter(self, name:str):
    """Delete parameter named 'name'"""
    apiData = self._wrappedData
    parameter = apiData.findFirstParameter(name=name)
    if parameter is None:
      raise KeyError("No parameter named %s" % name)
    else:
      parameter.delete()

  def clearParameters(self):
    """Delete all parameters"""
    for parameter in self._wrappedData.parameters:
      parameter.delete()

  def updateParameters(self, value:dict):
    """update parameters"""
    for key,val in value.items():
      self.setParameter(key, val)

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData (ccp.gui.Module) for all SpectrumDisplay children of Project"""

    apiGuiTask = (parent._wrappedData.findFirstGuiTask(nameSpace='user', name='View') or
                  parent._wrappedData.root.newGuiTask(nameSpace='user', name='View'))
    return [x for x in apiGuiTask.sortedModules() if isinstance(x, ApiBoundDisplay)]

  # CCPN functions
  def resetAxisOrder(self):
    """Reset display to original axis order"""

    self._startCommandEchoBlock('resetAxisOrder')
    try:
      self._wrappedData.resetAxisOrder()
    finally:
      self._endCommandEchoBlock()

  def findAxis(self, axisCode):
    """Find axis """
    return self._project._data2Obj.get(self._wrappedData.findAxis(axisCode))

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # ejb - orderedSpectrumViews, orderedSpectra
  # store the current orderedSpectrumViews in the internal data store
  # so it is hidden from external users
  def _retrieveOrderedSpectrumViews(self):
    if isinstance(self._ccpnInternalData, dict) and ORDEREDSPECTRA in self._ccpnInternalData:
      return self._ccpnInternalData[ORDEREDSPECTRA]
    else:
      return None

  def _storeOrderedSpectrumViews(self, spectra):
    if isinstance(self._ccpnInternalData, dict):
      self._ccpnInternalData[ORDEREDSPECTRA] = spectra

    setattr(self, ORDEREDSPECTRA, spectra)

  def orderedSpectra(self) -> Optional[Tuple[Spectrum, ...]]:
    """The spectra attached to the strip (ordered)"""

    if hasattr(self, ORDEREDSPECTRA):
      return tuple(x.spectrum for x in getattr(self, ORDEREDSPECTRA) if 'Deleted' not in x.pid)
    else:
      # create a dataset with the spectrumViews attached (will be alphabetical) if doesn't exist
      # store by pids

      values = self._retrieveOrderedSpectrumViews()
      if values is None:
        self._storeOrderedSpectrumViews(tuple(x.pid for x in self.spectrumViews))
        values = tuple(x for x in self.spectrumViews)
      else:
        values = tuple(self._project.getByPid(x) for x in values if self._project.getByPid(x))

        # this should be the first read from loading the project, so write back without bad pids
        self._storeOrderedSpectrumViews(tuple(x.pid for x in values))

      setattr(self, ORDEREDSPECTRA, values)
      return tuple(x.spectrum for x in values)

  def orderedSpectrumViews(self, includeDeleted=False) -> Optional[Tuple]:
    """The spectra attached to the strip (ordered)"""

    if hasattr(self, ORDEREDSPECTRA):
      return getattr(self, ORDEREDSPECTRA)
    else:
      # create a dataset with the spectrumViews attached (will be alphabetical) if doesn't exist
      # store by pid
      values = self._retrieveOrderedSpectrumViews()
      if values is None:
        self._storeOrderedSpectrumViews(tuple(x.pid for x in self.spectrumViews))
        values = tuple(x for x in self.spectrumViews)
      else:
        values = tuple(self._project.getByPid(x) for x in values if self._project.getByPid(x))

        # this should be the first read from loading the project, so write back without bad pids
        self._storeOrderedSpectrumViews(tuple(x.pid for x in values))

      setattr(self, ORDEREDSPECTRA, values)
      return values

  def appendSpectrumView(self, spectrumView):
    # retrieve the list from the dataset
    # append to the end
    # write back to the dataset
    if hasattr(self, ORDEREDSPECTRA):
      spectra = (getattr(self, ORDEREDSPECTRA), (spectrumView,))
      spectra = tuple(j for i in spectra for j in i)
    else:
      spectra = tuple(spectrumView,)

    self._storeOrderedSpectrumViews(tuple(x.pid for x in spectra))

    values = tuple(x for x in spectra)
    setattr(self, ORDEREDSPECTRA, values)

  def removeSpectrumView(self, spectrumView):
    # TODO:ED handle deletion
    # do I need to update the deleted object in _ccpnInternalData
    if hasattr(self, ORDEREDSPECTRA):
      spectra = getattr(self, ORDEREDSPECTRA)
      # self._storeOrderedSpectrumViews(tuple(x.pid for x in spectra))

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# newSpectrumDisplay functions
def _newSpectrumDisplay(self:Project, axisCodes:(str,), stripDirection:str='Y',
                        title:str=None, window:Window=None, comment:str=None,
                       independentStrips=False, nmrResidue=None):

  defaults = collections.OrderedDict((('stripDirection', 'Y'), ('title', None),
                                     ('window', None), ('comment', None),
                                     ('independentStrips', False), ('nmrResidue', None)))

  window = self.getByPid(window) if isinstance(window, str) else window
  nmrResidue = self.getByPid(nmrResidue) if isinstance(nmrResidue, str) else nmrResidue

  apiTask = (self._wrappedData.findFirstGuiTask(nameSpace='user', name='View') or
             self._wrappedData.root.newGuiTask(nameSpace='user', name='View'))

  if len(axisCodes) <2:
    raise ValueError("New SpectrumDisplay must have at least two axisCodes")

  # set parameters for display
  window = window or apiTask.sortedWindows()[0]
  displayPars = dict(
    stripDirection=stripDirection, window=window,
    details=comment, resonanceGroup=nmrResidue and nmrResidue._wrappedData
  )
  # Add name, setting and insuring uniqueness if necessary
  if title is None:
    if 'intensity' in axisCodes:
      title = ''.join(['1D:', axisCodes[0]] + list(axisCodes[2:]))
    else:
      title = ''.join([str(x) for x in axisCodes])
  elif Pid.altCharacter in title:
    raise ValueError("Character %s not allowed in gui.core.SpectrumDisplay.name" % Pid.altCharacter)
  while apiTask.findFirstModule(name=title):
    title = commonUtil.incrementName(title)
  displayPars['name'] = title

  self._startCommandEchoBlock('newSpectrumDisplay', axisCodes, values=locals(), defaults=defaults,
                              parName='newSpectrumDisplay')
  try:
    # Create SpectrumDisplay
    if independentStrips:
      # Create FreeStripDisplay
      apiSpectrumDisplay = apiTask.newFreeDisplay(**displayPars)
    else:
      # Create Boundstrip/Nostrip display and first strip
      displayPars['axisCodes'] = displayPars['axisOrder'] = axisCodes
      apiSpectrumDisplay = apiTask.newBoundDisplay(**displayPars)

    # Create axes
    for ii, code in enumerate(axisCodes):
      # if (ii == 0 and stripDirection == 'X' or ii == 1 and stripDirection == 'Y' or
      #    not stripDirection):
      # Reactivate this code if we reintroduce non-strip displays (stripDirection == None)
      if (ii == 0 and stripDirection == 'X' or ii == 1 and stripDirection == 'Y'):
        stripSerial = 0
      else:
        stripSerial = 1

      if code[0].isupper():
        apiSpectrumDisplay.newFrequencyAxis(code=code, stripSerial=stripSerial)
      elif code == 'intensity':
        apiSpectrumDisplay.newIntensityAxis(code=code, stripSerial=stripSerial)
      elif code.startswith('fid'):
        apiSpectrumDisplay.newFidAxis(code=code, stripSerial=stripSerial)
      else:
        apiSpectrumDisplay.newSampledAxis(code=code, stripSerial=stripSerial)

    # Create first strip
    if independentStrips:
      apiStrip = apiSpectrumDisplay.newFreeStrip(axisCodes=axisCodes, axisOrder=axisCodes)
    else:
      apiStrip = apiSpectrumDisplay.newBoundStrip()
    #
    result = self._project._data2Obj.get(apiSpectrumDisplay)
  finally:
    self._endCommandEchoBlock()

  return result
Project.newSpectrumDisplay = _newSpectrumDisplay
del _newSpectrumDisplay


def _createSpectrumDisplay(window:Window, spectrum:Spectrum, displayAxisCodes:Sequence[str]=(),
                          axisOrder:Sequence[str]=(), title:str=None, positions:Sequence[float]=(),
                          widths:Sequence[float]=(), units:Sequence[str]=(),
                          stripDirection:str='Y', is1D:bool=False,
                          independentStrips:bool=False):

  """
  :param \*str, displayAxisCodes: display axis codes to use in display order - default to spectrum axisCodes in heuristic order
  :param \*str axisOrder: spectrum axis codes in display order - default to spectrum axisCodes in heuristic order
  :param \*float positions: axis positions in order - default to heuristic
  :param \*float widths: axis widths in order - default to heuristic
  :param \*str units: axis units in display order - default to heuristic
  :param str stripDirection: if 'X' or 'Y' set strip axis
  :param bool is1D: If True, or spectrum passed in is 1D, do 1D display
  :param bool independentStrips: if True do freeStrip display.
  """

  inputValues = locals()

  defaults = collections.OrderedDict((('displayAxisCodes', ()), ('axisOrder', ()), ('title', None),
                                     ('positions', ()), ('widths', ()), ('units', ()),
                                      ('stripDirection', 'Y'), ('is1D', False),
                                     ('independentStrips', False)))

  if title and Pid.altCharacter in title:
    raise ValueError("Character %s not allowed in gui.core.SpectrumDisplay.name" % Pid.altCharacter)

  spectrum = window.getByPid(spectrum) if isinstance(spectrum, str) else spectrum

  dataSource = spectrum._wrappedData

  project = window._project

  spectrumAxisCodes = spectrum.axisCodes

  mapIndices = ()
  if axisOrder:
    mapIndices = commonUtil._axisCodeMapIndices(spectrumAxisCodes, axisOrder)
    if displayAxisCodes:
      if not commonUtil.doAxisCodesMatch(axisOrder, displayAxisCodes):
        raise ValueError("AxisOrder %s do not match display axisCodes %s"
                         % (axisOrder, displayAxisCodes))
    else:
      displayAxisCodes = axisOrder
  elif displayAxisCodes:
    mapIndices = commonUtil._axisCodeMapIndices(spectrumAxisCodes, displayAxisCodes)
  else:
    displayAxisCodes = list(spectrumAxisCodes)
    mapIndices = list(range(dataSource.numDim))
    if is1D:
      displayAxisCodes.insert(1, 'intensity')
      mapIndices.insert(1,None)

  # Make DataDim ordering
  sortedDataDims = dataSource.sortedDataDims()
  orderedDataDims = []
  for index in mapIndices:
    if index is None:
      orderedDataDims.append(None)
    else:
      orderedDataDims.append(sortedDataDims[index])

  # Make dimensionOrdering
  dimensionOrdering = [(0 if x is None else x.dim) for x in orderedDataDims]

  # Add intensity dimension for 1D if necessary
  if dataSource.numDim == 1 and len(displayAxisCodes) ==1:
    displayAxisCodes.append('intensity')
    dimensionOrdering.append(0)

  if dataSource.findFirstDataDim(className='SampledDataDim') is not None:
    # logger.warning( "Display of sampled dimension spectra is not implemented yet")
    # showWarning("createSpectrumDisplay", "Display of sampled dimension spectra is not implemented yet")
    # return
    raise NotImplementedError(
      "Display of sampled dimension spectra is not implemented yet")
    # # NBNB TBD FIXME

  window._startCommandEchoBlock('createSpectrumDisplay', spectrum, values=inputValues,
                                defaults=defaults, parName='newSpectrumDisplay')
  try:
    display = project.newSpectrumDisplay(axisCodes=displayAxisCodes,stripDirection=stripDirection,
                                      independentStrips=independentStrips,
                                      title=title)

    # Set unit, position and width
    orderedApiAxes = display._wrappedData.orderedAxes
    for ii, dataDim in enumerate(orderedDataDims):

      if dataDim is not None:
        # Set values only if we have a spectrum axis

        # Get unit, position and width
        dataDimRef = dataDim.primaryDataDimRef
        if dataDimRef:
          # This is a FreqDataDim
          unit = dataDimRef.expDimRef.unit
          position = dataDimRef.pointToValue(1) - dataDimRef.spectralWidth/2
          if ii < 2:
            width = dataDimRef.spectralWidth
          else:
            width = dataDimRef.valuePerPoint

        elif dataDim.className == 'SampledDataDim':

          unit = dataDim.unit
          width = len(dataDim.pointValues)
          position = 1 + width // 2
          if ii >= 2:
            width = 1
          # NBNB TBD this may not work, once we implement sampled axes

        else:
          # This is a FidDataDim
          unit = dataDim.unit
          width = dataDim.maxValue - dataDim.firstValue
          position = width / 2
          if ii >= 2:
            width = dataDim.valuePerPoint

        # Set values
        apiAxis = orderedApiAxes[ii]
        apiAxis.unit = unit
        apiAxis.position = position
        apiAxis.width = width
  finally:
    window._endCommandEchoBlock()

  # Make spectrumView. NB We need notifiers on for these
  stripSerial = 1 if independentStrips else 0
  display._wrappedData.newSpectrumView(spectrumName=dataSource.name,
                                       stripSerial=stripSerial,dataSource=dataSource,
                                       dimensionOrdering=dimensionOrdering)

  return display
Window.createSpectrumDisplay = _createSpectrumDisplay
del _createSpectrumDisplay

# Window.spectrumDisplays property
def getter(window:Window):
  ll = [x for x in window._wrappedData.sortedModules() if isinstance(x, ApiBoundDisplay)]
  return tuple(window._project._data2Obj[x] for x in ll)
Window.spectrumDisplays = property(getter, None, None,
                                   "SpectrumDisplays shown in Window")
del getter

# Notifiers:

# crosslinks window, nmrResidue
# TODO change to calling _setupApiNotifier
Project._apiNotifiers.append(
  ('_modifiedLink', {'classNames':('Window','SpectrumDisplay')},
  ApiBoundDisplay._metaclass.qualifiedName(), 'setWindow'),
)
Project._apiNotifiers.append(
  ('_modifiedLink', {'classNames':('NmrResidue','SpectrumDisplay')},
  ApiBoundDisplay._metaclass.qualifiedName(), 'setResonanceGroup'),
)
className = ApiWindow._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_modifiedLink', {'classNames':('SpectrumDisplay','Window')}, className, 'addModule'),
    ('_modifiedLink', {'classNames':('SpectrumDisplay','Window')}, className, 'removeModule'),
    ('_modifiedLink', {'classNames':('SpectrumDisplay','Window')}, className, 'setModules'),
  )
)

# WARNING link notifiers for both Window <-> Module and Window<->SpectrumDisplay
# are triggered together when  the change is on the Window side.
# Programmer take care that your notified function will work for both inputs !!!
className = ApiResonanceGroup._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_modifiedLink', {'classNames':('SpectrumDisplay','NmrResidue')}, className,
     'addSpectrumDisplay'),
    ('_modifiedLink', {'classNames':('SpectrumDisplay','NmrResidue')}, className,
     'removeSpectrumDisplay'),
    ('_modifiedLink', {'classNames':('SpectrumDisplay','NmrResidue')}, className,
     'setSpectrumDisplays'),
  )
)

# Drag-n-drop functions:
# SpectrumDisplay.processSpectrum = SpectrumDisplay.displaySpectrum     # ejb moved to GuiSpectrumDisplay
