"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
from PyQt4 import QtCore

# from pyqtgraph.dockarea import Dock

from ccpn import Spectrum
from ccpn import SpectrumGroup

from ccpn.util.Pid import Pid
from typing import Sequence
from application.core.widgets.Dock import CcpnDockLabel, CcpnDock
from application.core.widgets.Label import Label
# from ccpncore.lib.Io.Fasta import parseFastaFile, isFastaFormat

from application.core.DropBase import DropBase
from application.metabolomics.SpectrumGroupsWidget import SpectrumGroupsToolBar

# def _findPpmRegion(spectrum, axisDim, spectrumDim):
#
#   pointCount = spectrum.pointCounts[spectrumDim]
#   if axisDim < 2: # want entire region
#     region = (0, pointCount)
#   else:
#     n = pointCount // 2
#     region = (n, n+1)
#
#   firstPpm, lastPpm = spectrum.getDimValueFromPoint(spectrumDim, region)
#
#   return 0.5*(firstPpm+lastPpm), abs(lastPpm-firstPpm)

class GuiBlankDisplay(DropBase, CcpnDock): # DropBase needs to be first, else the drop events are not processed

  def __init__(self, dockArea):
    
    self.dockArea = dockArea

    CcpnDock.__init__(self, name='Blank Display')
    dockArea.addDock(self, 'right')

    self.label2 = Label(self.widget1, text='Drag Spectrum Here', textColor='#bec4f3')
    self.label2.setAlignment(QtCore.Qt.AlignCenter)
    self.widget2.hide()

    DropBase.__init__(self, dockArea.guiWindow._appBase)

  def setOrientation(self, o='vertical', force=True):
    """
    Sets the orientation of the title bar for this Dock.
    Must be one of 'auto', 'horizontal', or 'vertical'.
    By default ('auto'), the orientation is determined
    based on the aspect ratio of the Dock.
    """
    #print self.name(), "setOrientation", o, force
    if o == 'auto' and self.autoOrient:
      if self.container().type() == 'tab':
        o = 'horizontal'
      elif self.width() > self.height()*1.5:
        o = 'vertical'
      else:
        o = 'horizontal'
    if force or self.orientation != o:
      self.orientation = o
      self.label.setOrientation(o)
      self.updateStyle()

  def processSpectra(self, pids:Sequence[str], event):
    """Display spectra defined by list of Pid strings"""
    for ss in pids:
      try:
        spectrumDisplay = self.dockArea.guiWindow.createSpectrumDisplay(ss)
        self._appBase.current.strip = spectrumDisplay.strips[0]
        self.dockArea.guiWindow.deleteBlankDisplay()
        self.dockArea.guiWindow.pythonConsole.writeConsoleCommand("application.createSpectrumDisplay(spectrum)",
                                               spectrum=ss)
        self.dockArea.guiWindow.pythonConsole.writeConsoleCommand("application.deleteBlankDisplay()")

        self._appBase.project._logger.info('spectrum = project.getByPid("%s")' % ss)
        self._appBase.project._logger.info('application.createSpectrumDisplay(spectrum)')
        self._appBase.project._logger.info('application.deleteBlankDisplay()')
        self.dockArea.guiWindow.deleteBlankDisplay()

      except NotImplementedError:
        pass

  def processSamples(self, pids:Sequence[str], event):
    """Display sample spectra defined by list of Pid strings. This function will allow to drop a sample on a
    blankDisplay and display all in once its spectra"""
    for ss in pids:
      spectrumPids = [spectrum.pid for spectrum in self._appBase.project.getByPid(ss).spectra]
      spectrumDisplay = self.dockArea.guiWindow.createSpectrumDisplay(spectrumPids[0])
      for sp in spectrumPids[1:]:
        spectrumDisplay.displaySpectrum(sp)
      self.dockArea.guiWindow.deleteBlankDisplay()
      self.dockArea.window().pythonConsole.writeCommand('spectrum', 'application.createSpectrumDisplay',
                                                        'sample', pid=ss)
    self.dockArea.guiWindow.deleteBlankDisplay()

  def processSpectrum(self, spectrum:(Spectrum,Pid), event):
    """Process dropped spectrum"""
    spectrumDisplay = self.dockArea.guiWindow.createSpectrumDisplay(spectrum)
    self.dockArea.guiWindow.deleteBlankDisplay()
    msg = 'window.createSpectrumDisplay(project.getByPid("%s"))\n' % spectrum
    self.dockArea.window().pythonConsole.write(msg)
    self.dockArea.guiWindow.deleteBlankDisplay()


  def processSpectrumGroups(self, pids:Sequence[str], event):

    for ss in pids:
      spectrumPids = [spectrum.pid for spectrum in self._appBase.project.getByPid(ss).spectra]
      spectrumDisplay = self.dockArea.guiWindow.createSpectrumDisplay(spectrumPids[0])

      for spectrum in spectrumPids[1:]:
        spectrumDisplay.displaySpectrum(spectrum)
      spectrumDisplay.isGrouped = True
      spectrumDisplay.spectrumToolBar.hide()
      SpectrumGroupsToolBar(spectrumDisplay.dock, self._appBase.project, spectrumDisplay.strips[0],ss, grid=(0, 0))

      self._appBase.current.strip = spectrumDisplay.strips[0]
      self._appBase.current.strip.viewBox.autoRange()

    self.dockArea.guiWindow.deleteBlankDisplay()


  def closeDock(self):
    """
    Re-implementation of closeDock function from CcpnDock.
    """
    self._appBase.project._logger.info('Cannot close blank display')

