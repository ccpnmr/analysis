__author__ = 'simon'

import importlib, os

from PySide import QtGui, QtCore

from ccpncore.gui.Label import Label
from ccpncore.gui.ToolBar import ToolBar

from ccpnmrcore.modules.GuiModule import GuiModule

class GuiSpectrumDisplay(GuiModule):

  def __init__(self, dockArea, apiSpectrumDisplay):
    GuiModule.__init__(self, dockArea, apiSpectrumDisplay)
    self.apiSpectrumDisplay = apiSpectrumDisplay # redundancy: this is same as self.apiModule
    self.guiSpectrumViews = []
    self.guiStrips = []
    self.spectrumToolBar = ToolBar(self, grid=(0, 0), gridSpan=(1, 6))
    self.spectrumToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
    # self.spectrumToolBar.setMinimumHeight(44)
    #
    screenWidth  = QtGui.QApplication.desktop().screenGeometry().width()
    print(screenWidth*0.5)
    self.spectrumToolBar.setMaximumWidth(screenWidth*0.6)

    self.spectrumUtilToolBar = ToolBar(self, grid=(0, 7), gridSpan=(1, 2))
    self.spectrumUtilToolBar.setMinimumWidth(screenWidth*0.15)
    toolBarColour = QtGui.QColor(214,215,213)
    palette = QtGui.QPalette(self.spectrumUtilToolBar.palette())
    palette2 = QtGui.QPalette(self.spectrumToolBar.palette())
    palette.setColor(QtGui.QPalette.Button,toolBarColour)
    palette2.setColor(QtGui.QPalette.Button,toolBarColour)

    self.positionBox = Label(self, grid=(0, 9), gridSpan=(1, 1))
    self.positionBox.setFixedWidth(screenWidth*0.08)

    for apiStrip in apiSpectrumDisplay.strips:   ### probably need orderedStrips() here ?? ask Rasmus
      className = apiStrip.className
      classModule = importlib.import_module('ccpnmrcore.modules.Gui' + className)
      clazz = getattr(classModule, 'Gui'+className)
      guiStrip = clazz(self, apiStrip)
      self.guiStrips.append(guiStrip)  ##needs looking at



  def addStrip(self):
    pass
