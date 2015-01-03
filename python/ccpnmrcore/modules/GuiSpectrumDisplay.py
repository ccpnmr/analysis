__author__ = 'simon'

from PySide import QtGui, QtCore

from ccpncore.gui.Label import Label
from ccpncore.gui.ToolBar import ToolBar

from ccpnmrcore.modules import GuiModule

class GuiSpectrumDisplay(GuiModule):

  def __init__(self, dockArea, module):
    GuiModule.__init__(self, dockArea, module)
    self.guiSpectrumViews = []
    self.guiStrips = {}


    self.spectrumToolBar = ToolBar(self, grid=(0, 0), gridSpan=(2, 6))
    self.spectrumToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
    self.spectrumToolBar.setMinimumHeight(44)
    self.spectrumToolBar.setMaximumWidth(550)

    self.spectrumUtilToolBar = ToolBar(self, grid=(0, 6), gridSpan=(2, 3))
    toolBarColour = QtGui.QColor(214,215,213)
    palette = QtGui.QPalette(self.spectrumUtilToolBar.palette())
    palette2 = QtGui.QPalette(self.spectrumToolBar.palette())
    palette.setColor(QtGui.QPalette.Button,toolBarColour)
    palette2.setColor(QtGui.QPalette.Button,toolBarColour)

    self.positionBox = Label(self, grid=(0, 9), gridSpan=(2, 2))

  def addStrip(self):
    pass