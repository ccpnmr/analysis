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
__author__ = 'simon'

from PyQt4 import QtGui, QtOpenGL, QtCore

from ccpn import Spectrum

from ccpncore.gui.Base import Base
from ccpn.util.Pid import Pid
from typing import Sequence, Union

from application.core.base import ViewBox
from application.core.DropBase import DropBase
from application.metabolomics.SpectrumGroupsWidget import SpectrumGroupsWidget

import pyqtgraph as pg

class PlotWidget(DropBase, pg.PlotWidget, Base):

  def __init__(self, parent=None, appBase=None, useOpenGL=False, strip=None, **kw):
  # def __init__(self, parent=None, appBase=None, dropCallback=None, useOpenGL=False, **kw):

    #pg.PlotWidget.__init__(self, parent=parent, viewBox=ViewBox.ViewBox(appBase=appBase, parent=parent), axes=None, enableMenu=True)
    pg.PlotWidget.__init__(self, parent=parent, viewBox=ViewBox.ViewBox(current=appBase.current, parent=parent), axes=None, enableMenu=True)
    Base.__init__(self, **kw)
    DropBase.__init__(self, appBase)
    # DropBase.__init__(self, appBase, dropCallback)
    self.setInteractive(True)
    self.strip = strip
    self.plotItem.setAcceptHoverEvents(True)
    self.parent = parent
    self.plotItem.setAcceptDrops(True)
    self.plotItem.axes['left']['item'].hide()
    self.plotItem.axes['right']['item'].show()
    self.hideButtons()



    if useOpenGL:
      self.setViewport(QtOpenGL.QGLWidget())
      self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)

  def addItem(self, item:QtGui.QGraphicsObject):
    """
    Adds specified graphics object to the Graphics Scene of the PlotWidget.
    """
    self.scene().addItem(item)
    # # self.plotItem.axes['top']['item'].hide()
    # self.plotItem.axes['bottom']['item'].show()
    # self.plotItem.axes['right']['item'].show()

  def processSpectra(self, pids:Sequence[str], event:QtGui.QMouseEvent):
    """Display spectra defined by list of Pid strings"""
    guiSpectrumDisplay = self.parent.guiSpectrumDisplay
    displayPid = guiSpectrumDisplay.pid
    if guiSpectrumDisplay.isGrouped:
      print('single spectra cannot be dropped onto grouped displays')
      return


    for ss in pids:
      print(ss)
      guiSpectrumDisplay.displaySpectrum(ss)
      # self._appBase.mainWindow.pythonConsole.writeCompoundCommand(['spectrum', 'module'],
      #                            'module.displaySpectrum', 'spectrum', [ss, displayPid])
      self._appBase.mainWindow.pythonConsole.writeConsoleCommand(
        "module.displaySpectrum(spectrum)", module=displayPid, spectrum=ss
      )
      self._appBase.project._logger.info("module = project.getByPid(%s)" % displayPid)
      self._appBase.project._logger.info("module.displaySpectrum(spectrum)")

  def processSpectrumGroups(self, pids:Sequence[str], event:QtGui.QMouseEvent):
    '''
    Plots spectrumGroups in a grouped display if not already plotted and create its button on spectrumGroups toolBar.
    If a spectrum is already plotted in a display and a group is dropped, all its spectra will be displayed except the
    one already in.
    '''
    guiSpectrumDisplay = self.parent.guiSpectrumDisplay
    displayedSpectrumGroups = [spectrumView.spectrum.spectrumGroups[0]
                               for spectrumView in guiSpectrumDisplay.spectrumViews]

    for spectrum in self._appBase.project.getByPid(pids[0]).spectra:
      guiSpectrumDisplay.displaySpectrum(spectrum)

    spectrumGroups = [spectrumGroup for spectrumGroup in self._appBase.project.spectrumGroups
                 if spectrumGroup not in displayedSpectrumGroups and spectrumGroup.pid == pids[0]]

    if hasattr(guiSpectrumDisplay, 'isGrouped'):
      if len(spectrumGroups)>0:
        spectrumGroupToolBar = guiSpectrumDisplay.strips[0].spectrumDisplay.dock.children()[2].children()[-1]
        spectrumGroupButton = SpectrumGroupsWidget(self, self._appBase.project, guiSpectrumDisplay.strips[0], pids[0])
        spectrumGroupToolBar.addWidget(spectrumGroupButton)
        for spectrum in spectrumGroups[0].spectra:
          guiSpectrumDisplay.displaySpectrum(spectrum)


  def processSamples(self, pids:Sequence[str], event):
    """Display sample spectra defined by list of Pid strings"""
    for ss in pids:
      spectrumPids = [spectrum.pid for spectrum in self._appBase.project.getByPid(ss).spectra]
      self.processSpectra(spectrumPids, event)

  def processSampleComponents(self, pids:Sequence[str], event):
    """Display sampleComponent spectrum defined by its Pid string"""
    sampleComponent = self._appBase.project.getByPid(pids[0])
    self.processSpectra([sampleComponent.substance.referenceSpectra[0].pid], event)
