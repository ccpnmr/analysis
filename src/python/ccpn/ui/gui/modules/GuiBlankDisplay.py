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

# from pyqtgraph.dockarea import Dock

from typing import Sequence

from ccpn.core.Spectrum import Spectrum
from ccpn.core.lib.Pid import Pid
from ccpn.ui.gui.DropBase import DropBase
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.SpectrumGroupsToolBarWidget import SpectrumGroupsToolBar

class GuiBlankDisplay(DropBase, CcpnModule): # DropBase needs to be first, else the drop events are not processed

  includeSettingsWidget = False

  def __init__(self, moduleArea):
    
    self.moduleArea = moduleArea

    CcpnModule.__init__(self, name='Blank Display')
    # moduleArea.addModule(self, 'right')

    self.label2 = Label(self.mainWidget, text='Drag Spectrum Here',
                        textColour='#bec4f3', textSize='32', hPolicy='center', vPolicy='center')

    DropBase.__init__(self, moduleArea.guiWindow._appBase)

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

