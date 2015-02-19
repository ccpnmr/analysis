__author__ = 'simon'


from PySide import QtGui, QtCore

from ccpnmrcore.modules.GuiStrip import GuiStrip
from ccpncore.gui.Icon import Icon
from ccpncore.util.Colour import spectrumColours
from ccpncore.gui.Menu import Menu
# from ccpncore.util import Logging

class GuiStrip1d(GuiStrip):

  def __init__(self):
    GuiStrip.__init__(self)
    self.viewBox.invertX()
    self.showGrid(x=True, y=True)
    self.gridShown = True
    self.crossHairShown = True
    self.autoIntegration = True
    self.viewBox.menu = self.get1dContextMenu()
    self.plotItem.setAcceptDrops(True)
    self.spectrumItems = []
    self.colourIndex = 0
    self.spectrumIndex = 0

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

  def addSpectrum(self, spectrum, guiSpectrumView):

    apiSpectrum = spectrum.apiSpectrum
    if not guiSpectrumView.sliceColour:
      apiSpectrum.sliceColour = list(spectrumColours.keys())[self.colourIndex]
      self.colourIndex += 1
      self.colourIndex %= len(spectrumColours)

    colour = guiSpectrumView.sliceColour
    # spectrum.apiSpectrum.setSliceColour(colour)
    data = guiSpectrumView.getSliceData()
    # if self.colourScheme == 'dark':
    #   colour = colour.lighter(f=120)
    # elif self.colourScheme == 'light':
    #   colour = colour.lighter(f=85)
    # print(spectrum.ccpnSpectrum.spectrumViews)
    guiSpectrumView.plot = self.plotItem.plot(data[0],data[1], pen={'color':QtGui.QColor(colour)},clickable=True,)
    guiSpectrumView.plot.curve.setClickable(True)
    self._appBase.mainWindow.pythonConsole.write("current.pane.addSpectrum(%s)" % (spectrum))

    if self.spectrumIndex < 10:
      shortcutKey = "s,"+str(self.spectrumIndex)
      self.spectrumIndex+=1
    else:
      shortcutKey = None

    pix=QtGui.QPixmap(60,10)
    pix.fill(QtGui.QColor(colour))
    guiSpectrumView.newAction = self.guiSpectrumDisplay.spectrumToolBar.addAction(spectrum.ccpnSpectrum.getName(), QtGui.QToolButton)
    newIcon = QtGui.QIcon(pix)
    guiSpectrumView.newAction.setIcon(newIcon)
    guiSpectrumView.newAction.setCheckable(True)
    guiSpectrumView.newAction.setChecked(True)
    guiSpectrumView.newAction.setShortcut(QtGui.QKeySequence(shortcutKey))
    guiSpectrumView.newAction.toggled.connect(guiSpectrumView.plot.setVisible)
    self.guiSpectrumDisplay.spectrumToolBar.addAction(guiSpectrumView.newAction)
    guiSpectrumView.widget = self.guiSpectrumDisplay.spectrumToolBar.widgetForAction(guiSpectrumView.newAction)
    guiSpectrumView.widget.setFixedSize(60,30)
