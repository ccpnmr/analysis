__author__ = 'simon'


from PyQt4 import QtGui, QtCore

from ccpnmrcore.modules.GuiStrip import GuiStrip
from ccpncore.gui.Icon import Icon
from ccpncore.util.Colour import spectrumColours
from ccpncore.gui.Menu import Menu
# from ccpncore.util import Logging

class GuiStrip1d(GuiStrip):

  def __init__(self):
    GuiStrip.__init__(self)
    self.viewBox.invertX()
    self.plotWidget.showGrid(x=True, y=True)
    self.gridShown = True
    self.crossHairShown = True
    self.autoIntegration = True
    # self.viewBox.menu = self.get1dContextMenu()
    self.plotWidget.plotItem.setAcceptDrops(True)
    self.colourIndex = 0
    self.spectrumIndex = 0
    for spectrumView in self.spectrumViews:
      print(spectrumView)
      self.plotWidget.plotItem.plot(spectrumView.data[0], spectrumView.data[1], pen=spectrumView.spectrum.sliceColour)


  def get1dContextMenu(self):
    self.contextMenu = Menu(self, isFloatWidget=True)
    self.contextMenu.addItem("Auto Scale", callback=self.zoomYAll)
    self.contextMenu.addSeparator()
    self.contextMenu.addItem("Full", callback=self.zoomXAll)
    self.contextMenu.addItem("Zoom", callback=self.raiseZoomPopup)
    self.contextMenu.addItem("Store Zoom", callback=self.storeZoom)
    self.contextMenu.addItem("Restore Zoom", callback=self.restoreZoom)
    self.contextMenu.addSeparator()
    self.crossHairAction = QtGui.QAction("Crosshair", self, triggered=self.toggleCrossHair,
                                         checkable=True)
    if self.crossHairShown:
      self.crossHairAction.setChecked(True)
    else:
      self.crossHairAction.setChecked(False)
    self.contextMenu.addAction(self.crossHairAction, isFloatWidget=True)
    self.gridAction = QtGui.QAction("Grid", self, triggered=self.toggleGrid, checkable=True)
    if self.gridShown:
      self.gridAction.setChecked(True)
    else:
      self.gridAction.setChecked(False)
    self.contextMenu.addAction(self.gridAction, isFloatWidget=True)
    self.contextMenu.addSeparator()
    # self.contextMenu.addItem("Print", callback=self.raisePrintMenu)
    return self.contextMenu

  def zoomYAll(self):
    y2 = self.viewBox.childrenBoundingRect().top()
    y1 = y2 + self.viewBox.childrenBoundingRect().height()
    self.viewBox.setYRange(y2,y1)

  def zoomXAll(self):
    x2 = self.viewBox.childrenBoundingRect().left()
    x1 = x2 + self.viewBox.childrenBoundingRect().width()
    self.viewBox.setXRange(x2,x1)
