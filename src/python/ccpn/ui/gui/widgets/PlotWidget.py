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
__author__ = "$Author: CCPN $"
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:43 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"

#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence

import pyqtgraph as pg
from PyQt4 import QtGui, QtOpenGL

from ccpn.ui.gui.widgets.SpectrumGroupsToolBarWidget import SpectrumGroupsWidget
from ccpn.ui.gui import ViewBox
from ccpn.ui.gui.widgets.Base import Base

#TODO:WAYNE: this class could be moved into GuiStrip
# as it is only there and is just a small wrapper arount a pyqtgraph class
# goes together with AxisTextItem
#TODO:WAYNE: should this inherit from Base!! is layout in pyqtgraph is different to Base???
class PlotWidget(pg.PlotWidget, Base):

  def __init__(self, parent=None, appBase=None, useOpenGL=False, strip=None, **kw):

    pg.PlotWidget.__init__(self, parent=parent,
                           viewBox=ViewBox.ViewBox(current=appBase.current, parent=parent),
                           axes=None, enableMenu=True)
    Base.__init__(self, acceptDrops=True, **kw)
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

  def __getattr__(self, attr):
    """
    Wrap pyqtgraph PlotWidget __getattr__, which raises wrong error and so makes hasattr fail.
    """
    try:
      return super().__getattr__(attr)
    except NameError:
      raise AttributeError(attr)

  def addItem(self, item:QtGui.QGraphicsObject):
    """
    Adds specified graphics object to the Graphics Scene of the PlotWidget.
    """
    self.scene().addItem(item)
    # # self.plotItem.axes['top']['item'].hide()
    # self.plotItem.axes['bottom']['item'].show()
    # self.plotItem.axes['right']['item'].show()

  # def processSpectra(self, pids:Sequence[str], event:QtGui.QMouseEvent):
  #   """Display spectra defined by list of Pid strings"""
  #   guiSpectrumDisplay = self.parent.guiSpectrumDisplay
  #   displayPid = guiSpectrumDisplay.pid
  #   if guiSpectrumDisplay.isGrouped:
  #     print('single spectra cannot be dropped onto grouped displays. Open another Blank Display (N,D)')
  #     return
  #
  #   for ss in pids:
  #     guiSpectrumDisplay.displaySpectrum(ss)
  #     # self._appBase.mainWindow.pythonConsole.writeCompoundCommand(['spectrum', 'module'],
  #     #                            'module.displaySpectrum', 'spectrum', [ss, displayPid])
  #
  #     if self._appBase.ui.mainWindow is not None:
  #       mainWindow = self._appBase.ui.mainWindow
  #     else:
  #       mainWindow = self._appBase._mainWindow
  #     mainWindow.pythonConsole.writeConsoleCommand(
  #       "module.displaySpectrum(spectrum)", module=displayPid, spectrum=ss
  #     )
  #     self._appBase.project._logger.info("module = ui.getByGid(%s)" % displayPid)
  #     self._appBase.project._logger.info("module.displaySpectrum(spectrum)")
  #
  # def processSpectrumGroups(self, pids:Sequence[str], event:QtGui.QMouseEvent):
  #   '''
  #   Plots spectrumGroups in a grouped display if not already plotted and create its button on spectrumGroups toolBar.
  #   If a spectrum is already plotted in a display and a group is dropped, all its spectra will be displayed except the
  #   one already in.
  #   '''
  #   if len(self._appBase.project.getByPid(pids[0]).spectra)>0:
  #     guiSpectrumDisplay = self.parent.guiSpectrumDisplay
  #     for spectrumView in guiSpectrumDisplay.spectrumViews:
  #       if len(spectrumView.spectrum.spectrumGroups)>0:
  #         displayedSpectrumGroups = [spectrumView.spectrum.spectrumGroups[0]
  #                                    for spectrumView in guiSpectrumDisplay.spectrumViews]
  #
  #         spectrumGroups = [spectrumGroup for spectrumGroup in self._appBase.project.spectrumGroups
  #                      if spectrumGroup not in displayedSpectrumGroups and spectrumGroup.pid == pids[0]]
  #
  #       else:
  #         for spectrum in self._appBase.project.getByPid(pids[0]).spectra:
  #           guiSpectrumDisplay.displaySpectrum(spectrum)
  #
  #       if hasattr(guiSpectrumDisplay, 'isGrouped'):
  #         if guiSpectrumDisplay.isGrouped:
  #           if len(spectrumGroups)>0:
  #
  #             spectrumGroupsToolBar = guiSpectrumDisplay.strips[0].spectrumViews[0].spectrumGroupsToolBar
  #             spectrumGroupButton = SpectrumGroupsWidget(self, self._appBase.project, guiSpectrumDisplay.strips[0], pids[0])
  #             spectrumGroupsToolBar.addWidget(spectrumGroupButton)
  #             for spectrum in spectrumGroups[0].spectra:
  #               guiSpectrumDisplay.displaySpectrum(spectrum)
  #         else:
  #           print("SpectrumGroups cannot be displayed in a display with already spectra in it."
  #                 "\nSpectrumGroup's spectra are added as single item in the display  ")
  #
  #
  # def processSamples(self, pids:Sequence[str], event):
  #   """Display sample spectra defined by list of Pid strings"""
  #   for ss in pids:
  #     spectrumPids = [spectrum.pid for spectrum in self._appBase.project.getByPid(ss).spectra]
  #     self.processSpectra(spectrumPids, event)
  #
  # def processSampleComponents(self, pids:Sequence[str], event):
  #   """Display sampleComponent spectrum defined by its Pid string"""
  #   sampleComponent = self._appBase.project.getByPid(pids[0])
  #   self.processSpectra([sampleComponent.substance.referenceSpectra[0].pid], event)
