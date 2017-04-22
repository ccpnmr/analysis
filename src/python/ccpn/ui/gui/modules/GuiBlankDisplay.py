"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:38 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# from pyqtgraph.dockarea import Dock

from typing import Sequence

from ccpn.core.Spectrum import Spectrum
from ccpn.core.lib.Pid import Pid
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.SpectrumGroupsToolBarWidget import SpectrumGroupsToolBar
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier

from ccpn.util.Logging import getLogger
logger = getLogger()


#TODO:LUCA: remove file when you are done with updating the callbacks elsewhere
class GuiBlankDisplay(CcpnModule):
  includeSettingsWidget = False

  def __init__(self, moduleArea):
    
    self.moduleArea = moduleArea

    CcpnModule.__init__(self, name='Blank Display')
    # moduleArea.addModule(self, 'right')

    self.label2 = Label(self.mainWidget, text='Drag Spectrum Here',
                        textColour='#bec4f3', textSize='32', hPolicy='center', vPolicy='center')

  def processSpectra(self, pids:Sequence[str], event):
    """Display spectra defined by list of Pid strings"""
    for ss in pids:
      try:
        spectrumDisplay = self.moduleArea.guiWindow.createSpectrumDisplay(ss)
        self._appBase.current.strip = spectrumDisplay.strips[0]
        self.moduleArea.guiWindow.deleteBlankDisplay()
        self.moduleArea.guiWindow.pythonConsole.writeConsoleCommand("application.createSpectrumDisplay(spectrum)",
                                               spectrum=ss)
        self.moduleArea.guiWindow.pythonConsole.writeConsoleCommand("application.deleteBlankDisplay()")

        self._appBase.project._logger.info('spectrum = project.getByPid("%s")' % ss)
        self._appBase.project._logger.info('application.createSpectrumDisplay(spectrum)')
        self._appBase.project._logger.info('application.deleteBlankDisplay()')
        self.moduleArea.guiWindow.deleteBlankDisplay()

      except NotImplementedError:
        pass

  def processSamples(self, pids:Sequence[str], event):
    """Display sample spectra defined by list of Pid strings. This function will allow to drop a sample on a
    blankDisplay and display all in once its spectra"""
    for ss in pids:
      spectrumPids = [spectrum.pid for spectrum in self._appBase.project.getByPid(ss).spectra]
      spectrumDisplay = self.moduleArea.guiWindow.createSpectrumDisplay(spectrumPids[0])
      for sp in spectrumPids[1:]:
        spectrumDisplay.displaySpectrum(sp)
      self.moduleArea.guiWindow.deleteBlankDisplay()

    self.moduleArea.guiWindow.deleteBlankDisplay()

  def processSpectrum(self, spectrum:(Spectrum,Pid), event):
    """Process dropped spectrum"""
    spectrumDisplay = self.moduleArea.guiWindow.createSpectrumDisplay(spectrum)
    self.moduleArea.guiWindow.deleteBlankDisplay()
    msg = 'window.createSpectrumDisplay(project.getByPid("%s"))\n' % spectrum
    self.moduleArea.window().pythonConsole.write(msg)
    self.moduleArea.guiWindow.deleteBlankDisplay()


  def processSpectrumGroups(self, pids:Sequence[str], event):

    for ss in pids:
      spectrumPids = [spectrum.pid for spectrum in self._appBase.project.getByPid(ss).spectra]
      if len(spectrumPids)>0:
        spectrumDisplay = self.moduleArea.guiWindow.createSpectrumDisplay(spectrumPids[0])

        for spectrum in spectrumPids[1:]:
          spectrumDisplay.displaySpectrum(spectrum)
        spectrumDisplay.isGrouped = True
        spectrumDisplay.spectrumToolBar.hide()

        self._appBase.current.strip = spectrumDisplay.strips[0]

        spectrumGroupsToolBar = SpectrumGroupsToolBar(spectrumDisplay.module, self._appBase.project, spectrumDisplay.strips[0],ss, grid=(0, 0))

        spectrumDisplay.strips[0].spectrumViews[0].spectrumGroupsToolBar = spectrumGroupsToolBar

        padding = self._appBase.preferences.general.stripRegionPadding
        self._appBase.current.strip.viewBox.autoRange(padding=padding)
        self.moduleArea.guiWindow.deleteBlankDisplay()



  def _closeModule(self):
    """
    Re-implementation of closeModule function from CcpnModule.
    """
    CcpnModule._closeModule(self)
    self._appBase.project._logger.info('Shortcut "ND" to open a new blank display')

    ## No need of this hack anymore. A Blank display can be reopen anytime.
    # if self.window().spectrumDisplays:
    #   CcpnModule._closeModule(self)
    # else:
    #   self._appBase.project._logger.info('Cannot close blank display')

