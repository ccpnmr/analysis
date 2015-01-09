__author__ = 'simon'


from PySide import QtGui, QtCore
import random
from functools import partial

from ccpnmrcore.modules.GuiStrip import GuiStrip
# from ccpncore.gui.Button import Button
# from ccpncore.gui.Icon import Icon
# from ccpncore.gui.ColourDialog import ColourDialog
# from ccpncore.gui.Action import Action
from ccpncore.gui.Menu import Menu
# from ccpncore.util import Logging

class GuiStrip1d(GuiStrip):

  def __init__(self, guiSpectrumDisplay, spectraVar, **kw):
    GuiStrip.__init__(self, guiSpectrumDisplay, spectraVar)
    # self.contextMenu = None
    self.viewBox.invertX()
    self.showGrid(x=True, y=True)
    self.gridShown = True
    self.crossHairShown = True
    self.autoIntegration = True
    self.viewBox.menu = self.get1dContextMenu()
    self.plotItem.setAcceptDrops(True)
    self.spectrumItems = []
    # self.fillToolBar()
    self.colourIndex = 0

  def get1dContextMenu(self):
    self.contextMenu = Menu(self, isFloatWidget=True)
    self.contextMenu.addItem("Auto Scale", callback=self.zoomYAll)
    self.contextMenu.addSeparator()
    self.contextMenu.addItem("Full", callback=self.zoomXAll)
    # self.contextMenu.addItem("Zoom", callback=self.raiseZoomPopup)
    # self.contextMenu.addItem("Store Zoom", callback=self.storeZoom)
    # self.contextMenu.addItem("Restore Zoom", callback=self.restoreZoom)
    # self.contextMenu.addSeparator()
    # self.crossHairAction = QtGui.QAction("Crosshair", self, triggered=self.toggleCrossHair,
    #                                      checkable=True)
    # if self.crossHairShown == True:
    #   self.crossHairAction.setChecked(True)
    # else:
    #   self.crossHairAction.setChecked(False)
    # self.contextMenu.addAction(self.crossHairAction, isFloatWidget=True)
    # self.gridAction = QtGui.QAction("Grid", self, triggered=self.toggleGrid, checkable=True)
    # if self.gridShown == True:
    #   self.gridAction.setChecked(True)
    # else:
    #   self.gridAction.setChecked(False)
    # self.contextMenu.addAction(self.gridAction, isFloatWidget=True)
    # self.contextMenu.addSeparator()
    # self.peakAction = QtGui.QAction("Peaks", self, triggered=self.peakListToggle, checkable=True)
    # # if self.current.spectrum is not None:
    # #   if self.current.spectrum.spectrumItem.peakListItems[self.current.spectrum.peakLists[0].pid].displayed == True:
    # #     self.peakAction.setChecked(True)
    # #   else:
    # #     print("self.current.spectrum is None")
    # #     self.peakAction.setChecked(False)
    # self.contextMenu.addAction(self.peakAction, isFloatWidget=True)
    # self.contextMenu.addItem("Integrals", callback=self.integralToggle)
    # self.autoIntegrationAction = QtGui.QAction("Automatic", self,
    #                                            triggered=self.toggleIntegrationMethod, checkable=True, )
    # self.manualIntegrationAction = QtGui.QAction("Manual", self,
    #                                              triggered=self.toggleIntegrationMethod, checkable=True)
    # if self.autoIntegration == True:
    #   self.autoIntegrationAction.setChecked(True)
    #   self.manualIntegrationAction.setChecked(False)
    # if self.autoIntegration == False:
    #   self.autoIntegrationAction.setChecked(False)
    #   self.manualIntegrationAction.setChecked(True)
    # self.contextMenu.addAction(self.autoIntegrationAction, isFloatWidget=True)
    # self.contextMenu.addAction(self.manualIntegrationAction, isFloatWidget=True)
    #
    # self.contextMenu.addSeparator()
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

    colour = (0, 0, 255)  ## TBD
    data = guiSpectrumView.spectralData
    self.plot = self.plotItem.plot(data[0],data[1], pen={'color':colour},clickable=True,)
    # self.colour = QtGui.QColor(colour)
    # self.name = spectrum.name
    # self.plot.parent = spectrum
    self.plot.curve.setClickable(True)
    # guiSpectrumView.plot.sigClicked.connect(self.clicked)
    # palette = QtGui.QPalette()
    # palette.setColor(QtGui.QPalette.Button,spectrumView.colour)

    # spectrumView.toolBarButton = QtGui.QToolButton(self.parent,text=spectrum.name)
    # spectrumView.toolBarButton.setCheckable(True)
    # spectrumView.toolBarButton.setChecked(True)
    # # print(spectrumView.toolBarButton.actions())
    # palette.setColor(QtGui.QPalette.Button,colour)
    # spectrumView.toolBarButton.
    # spectrumView.toolBarButton.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
    # spectrumView.toolBarButton.toggled.connect(spectrumView.plot.setVisible)

    self.appBase.mainWindow.pythonConsole.write("current.pane.addSpectrum(%s)" % (spectrum))
    # if self.colourIndex != len(SPECTRUM_COLOURS) - 1:
    #   self.colourIndex +=1
    # else:
    #   self.colourIndex = 0
    #
    # if self.spectrumIndex < 10:
    #   shortcutKey = "s,"+str(self.spectrumIndex)
    #   self.spectrumIndex+=1
    # else:
    #   shortcutKey = None

    # pix=QtGui.QPixmap(60,10)
    # pix.fill(QtGui.QColor(guiSpectrumView.colour))
    # guiSpectrumView.newAction = self.spectrumToolbar.addAction(guiSpectrumView.name, QtGui.QToolButton)
    # newIcon = QtGui.QIcon(pix)
    # guiSpectrumView.newAction.setIcon(newIcon)
    # guiSpectrumView.newAction.setCheckable(True)
    # guiSpectrumView.newAction.setChecked(True)
    # # spectrumView.newAction.setShortcut(QtGui.QKeySequence(shortcutKey))
    # guiSpectrumView.newAction.toggled.connect(guiSpectrumView.plot.setVisible)
    # self.spectrumToolbar.addAction(guiSpectrumView.newAction)
    # guiSpectrumView.widget = self.spectrumToolbar.widgetForAction(guiSpectrumView.newAction)
    # guiSpectrumView.widget.setFixedSize(60,30)
    # self.current.spectrum = spectrum
    # spectrum.spectrumView = guiSpectrumView
