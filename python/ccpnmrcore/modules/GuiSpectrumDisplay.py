__author__ = 'simon'

import importlib, os

from PySide import QtGui, QtCore

from ccpncore.gui.Label import Label
from ccpncore.gui.ToolBar import ToolBar

from ccpnmrcore.gui.Frame import Frame as GuiFrame
from ccpnmrcore.modules.GuiModule import GuiModule

class GuiSpectrumDisplay(GuiModule):

  def __init__(self, dockArea, apiSpectrumDisplay):
    GuiModule.__init__(self, dockArea, apiSpectrumDisplay)
    self.apiSpectrumDisplay = apiSpectrumDisplay # redundancy: this is same as self.apiModule
    self.guiSpectrumViews = []
    self.guiStrips = []
    self.spectrumToolBar = ToolBar(self, grid=(0, 0), gridSpan=(1, 1))
    self.spectrumToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
    screenWidth  = QtGui.QApplication.desktop().screenGeometry().width()
    self.spectrumToolBar.setMaximumWidth(screenWidth*0.6)

    self.spectrumUtilToolBar = ToolBar(self, grid=(0, 1), gridSpan=(1, 1))
    self.spectrumUtilToolBar.setMinimumWidth(screenWidth*0.15)
    toolBarColour = QtGui.QColor(214,215,213)
    palette = QtGui.QPalette(self.spectrumUtilToolBar.palette())
    palette2 = QtGui.QPalette(self.spectrumToolBar.palette())
    palette.setColor(QtGui.QPalette.Button,toolBarColour)
    palette2.setColor(QtGui.QPalette.Button,toolBarColour)

    self.positionBox = Label(self, grid=(0, 2), gridSpan=(1, 1))
    self.positionBox.setFixedWidth(screenWidth*0.08)
    self.stripFrame = GuiFrame(self, appBase=self.appBase, grid=(1, 0), gridSpan=(1, 4))
    self.stripFrame.guiSpectrumDisplay = self


    for n, apiStrip in enumerate(apiSpectrumDisplay.sortedStrips()):   ### probably need orderedStrips() here ?? ask Rasmus
      className = apiStrip.className
      classModule = importlib.import_module('ccpnmrcore.modules.Gui' + className)
      clazz = getattr(classModule, 'Gui'+className)
      guiStrip = clazz(self.stripFrame, apiStrip)

    self.currentStrip = apiSpectrumDisplay.sortedStrips()[0].guiStrip

  def fillToolBar(self):

    self.spectrumUtilToolBar.addAction('+', self.addStrip)
    self.spectrumUtilToolBar.addAction('-', self.removeStrip)


  def addStrip(self):
    pass  # TBD: should raise exception if not implemented in subclass


  def removeStrip(self):
    pass

  def zoomYAll(self):
    self.currentStrip.zoomYAll()

  def zoomXAll(self):
    self.currentStrip.zoomXAll()

  def restoreZoom(self):
    self.currentStrip.restoreZoom()

  def storeZoom(self):
    self.currentStrip.storeZoom()
    
    