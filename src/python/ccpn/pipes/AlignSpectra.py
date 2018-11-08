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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:38 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


#### GUI IMPORTS
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe , _getWidgetByAtt
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox, DoubleSpinbox
from ccpn.ui.gui.widgets.GLLinearRegionsPlot import GLTargetButtonSpinBoxes


#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe
from scipy import signal
import numpy as np
from scipy import stats
from ccpn.util.Logging import getLogger , _debug3
from collections import OrderedDict

########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

ReferenceSpectrum = 'Reference_Spectrum'
PipeName = 'Align Spectra'
HeaderText = '-- Select Spectrum --'
ReferenceRegion = 'Reference_Region'
DefaultReferenceRegion = (0.5, -0.5)
EnginesVar = 'Engines'
IndividualMode = 'individual'
Median ='median'
Mode = 'mode'
Mean = 'mean'
Engines = [IndividualMode, Mean, Mode,Median]
EnginesCallables = OrderedDict([
                    ('median',np.median),
                    ('mode',stats.mode),
                    ('mean',np.mean),
                    ])

DefaultEngine = 'median'
NotAvailable = 'Not Available'
########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


def _getShift(ref_x, ref_y, target_y):
  '''
  :param ref_x: X array of the reference spectra (positions)
  :param ref_y: Y array of the reference spectra (intensities)
  :param target_y: Y array of the target spectra (intensities)
  :return: the shift needed to align the two spectra.
  Global alignment. This can give unpredictable results if the signal intensities are very different
  To align the target spectrum to its reference: add the shift to the x array.
  E.g. target_y += shift
  '''
  return (np.argmax(signal.correlate(ref_y, target_y)) - len(target_y)) * np.mean(np.diff(ref_x))


def _getShiftForSpectra(referenceSpectrum, spectra, referenceRegion=(3, 2), engine='median'):
  '''
  :param referenceSpectrum:
  :param spectra:
  :param referenceRegion:
  :param intensityFactor:
  :param engine: one of 'median', 'mode', 'mean'
  :return: shift float
  alignment of spectra. It aligns based on a specified region of the reference spectrum
  '''

  shifts = []
  point1, point2 = max(referenceRegion), min(referenceRegion)
  xRef, yRef = referenceSpectrum.positions, referenceSpectrum.intensities
  ref_x_filtered = np.where((xRef <= point1) & (xRef >= point2)) #only the region of interest for the reference spectrum

  ref_y_filtered = yRef[ref_x_filtered]
  maxYRef = max(ref_y_filtered) #Find the highest signal in the region of interest for the reference spectrum. All spectra will be aligned to this point.
  boolsRefMax = yRef == maxYRef
  refIndices = np.argwhere(boolsRefMax)
  if len(refIndices) > 0:
    refPos = float(xRef[refIndices[0]])

  #  find the shift for each spectrum for the selected region
  for sp in spectra:
    xTarg, yTarg = sp.positions, sp.intensities
    x_TargetFilter = np.where((xTarg <= point1) & (xTarg >= point2)) # filter only the region of interest for the target spectrum

    y_TargetValues = yTarg[x_TargetFilter]
    maxYTarget = max(y_TargetValues)
    boolsMax = yTarg == maxYTarget  #Find the highest signal in the region of interest
    indices = np.argwhere(boolsMax)
    if len(indices)>0:
      tarPos = float(xTarg[indices[0]])
      shift =tarPos-refPos
      shifts.append(shift)


  if len(shifts) == len(spectra):
    if engine == IndividualMode:
      return shifts

  # get a common shift from all the shifts found
  if engine in EnginesCallables.keys():
    shift = EnginesCallables[engine](shifts)
    if isinstance(shift, stats.stats.ModeResult):
      shift = shift.mode[0]
      return float(shift)


def addIndividualShiftToSpectra(spectra, shifts):
  alignedSpectra=[]
  for sp, shift in zip(spectra, shifts):
      sp.positions -= shift
      alignedSpectra.append(sp)
  return alignedSpectra

def addShiftToSpectra(spectra, shift):
  alignedSpectra=[]
  for sp in spectra:
      sp.positions -= shift
      alignedSpectra.append(sp)
  return alignedSpectra

########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class AlignSpectraGuiPipe(GuiPipe):

  preferredPipe = True
  pipeName = PipeName

  def __init__(self, name=pipeName, parent=None, project=None,   **kw):
    super(AlignSpectraGuiPipe, self)
    GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw )
    self.parent = parent

    row = 0
    #  Reference Spectrum
    self.spectrumLabel = Label(self.pipeFrame, ReferenceSpectrum,  grid=(row,0))
    setattr(self, ReferenceSpectrum, PulldownList(self.pipeFrame, headerText=HeaderText,
                                                  headerIcon=self._warningIcon, callback=self._estimateShift, grid=(row,1)))
    row += 1

    # target region
    self.tregionLabel = Label(self.pipeFrame, text=ReferenceRegion, grid=(row, 0))
    setattr(self, ReferenceRegion, GLTargetButtonSpinBoxes(self.pipeFrame, application=self.application,
                                                                    values=DefaultReferenceRegion, orientation='v',
                                                                    grid=(row, 1)))

    row += 1
    #  Engines
    self.enginesLabel = Label(self.pipeFrame, EnginesVar, grid=(row, 0))
    setattr(self, EnginesVar, PulldownList(self.pipeFrame, texts=Engines, grid=(row, 1)))

    row += 1
    estimateShiftLabel =  Label(self.pipeFrame, 'Estimated_shift', grid=(row, 0))
    self.estimateShift = Label(self.pipeFrame, NotAvailable, grid=(row, 1))
    row += 1


    self._updateWidgets()

  def _estimateShift(self, *args):
      '''Only to show on the Gui pipe '''
      referenceRegion= getattr(self, ReferenceRegion).get()
      engine = getattr(self, EnginesVar).getText()
      referenceSpectrum = getattr(self, ReferenceSpectrum).get()
      if not isinstance(referenceSpectrum, str):
        spectra = [sp for sp in self.parent.inputData if sp != referenceSpectrum]
        if engine == IndividualMode:
          self.estimateShift.clear()
          self.estimateShift.setText(str(NotAvailable))
        else:
          shift = _getShiftForSpectra(referenceSpectrum, spectra,
                                          referenceRegion=referenceRegion, engine=engine)
          self.estimateShift.clear()
          self.estimateShift.setText(str(shift))



  def _updateWidgets(self):
    self._setDataReferenceSpectrum()


  def _setDataReferenceSpectrum(self):
    data = list(self.parent.inputData)

    if len(data)>0:
      _getWidgetByAtt(self,ReferenceSpectrum).setData(texts=[sp.pid for sp in data], objects=data, index=1,
                                                      headerText=HeaderText, headerIcon=self._warningIcon)
    else:
      _getWidgetByAtt(self, ReferenceSpectrum)._clear()



########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################




class AlignSpectra(SpectraPipe):

  guiPipe = AlignSpectraGuiPipe
  pipeName = PipeName

  _kwargs  =   {
               ReferenceSpectrum: 'spectrum.pid',
               ReferenceRegion  :DefaultReferenceRegion,
               EnginesVar       :DefaultEngine
               }



  def runPipe(self, spectra):
    '''
    :param spectra: inputData
    :return: aligned spectra
    '''
    referenceRegion = self._kwargs[ReferenceRegion]
    engine = self._kwargs[EnginesVar]
    if self.project is not None:
      referenceSpectrumPid = self._kwargs[ReferenceSpectrum]
      referenceSpectrum = self.project.getByPid(referenceSpectrumPid)
      if referenceSpectrum is not None:
        spectra = [spectrum for spectrum in spectra if spectrum != referenceSpectrum]
        if spectra:
          if engine == IndividualMode:
            shifts =  _getShiftForSpectra(referenceSpectrum, spectra,
                                                      referenceRegion=referenceRegion,  engine=engine)
            addIndividualShiftToSpectra(spectra, shifts)
            getLogger().info('Alignment: applied individual shift to all spectra')

          else:
            shift =  _getShiftForSpectra(referenceSpectrum, spectra,
                                                      referenceRegion=referenceRegion,  engine=engine)
            addShiftToSpectra(spectra, shift)
            getLogger().info('Alignment: applied shift to all spectra of %s' %shift)

          return spectra
        else:
          getLogger().warning('Spectra not Aligned. Returned original spectra')
          return spectra
      else:
        getLogger().warning('Spectra not Aligned. Returned original spectra')
        return spectra

AlignSpectra.register() # Registers the pipe in the pipeline
