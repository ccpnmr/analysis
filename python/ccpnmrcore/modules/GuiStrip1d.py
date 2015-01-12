__author__ = 'simon'


from PySide import QtGui, QtCore
import random
from functools import partial

from ccpnmrcore.modules.GuiStrip import GuiStrip
# from ccpncore.gui.Button import Button
from ccpncore.gui.Icon import Icon
from ccpncore.gui.ColourDialog import ColourDialog
from ccpncore.util.Colour import spectrumColours
# from ccpncore.gui.Action import Action
from ccpncore.gui.Menu import Menu
# from ccpncore.util import Logging

class GuiStrip1d(GuiStrip):

  def __init__(self, guiSpectrumDisplay, apiStrip, **kw):
    GuiStrip.__init__(self, guiSpectrumDisplay, apiStrip)
    # self.contextMenu = None
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
    self.guiSpectrumDisplay = guiSpectrumDisplay
    self.fillToolBar()
    print(guiSpectrumDisplay.spectrumToolBar)
    print(guiSpectrumDisplay.spectrumUtilToolBar)


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
    if self.crossHairShown == True:
      self.crossHairAction.setChecked(True)
    else:
      self.crossHairAction.setChecked(False)
    self.contextMenu.addAction(self.crossHairAction, isFloatWidget=True)
    self.gridAction = QtGui.QAction("Grid", self, triggered=self.toggleGrid, checkable=True)
    if self.gridShown == True:
      self.gridAction.setChecked(True)
    else:
      self.gridAction.setChecked(False)
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

  def fillToolBar(self):
    autoScaleAction = self.guiSpectrumDisplay.spectrumUtilToolBar.addAction("AutoScale", self.zoomYAll)
    autoScaleActionIcon = Icon('icons/zoom-fit-best')
    # autoScaleActionIcon.actualSize(QtCore.QSize(10, 10))
    autoScaleAction.setIcon(autoScaleActionIcon)
    # autoScaleAction.setText("AutoScale")
    fullZoomAction = self.guiSpectrumDisplay.spectrumUtilToolBar.addAction("Full", self.zoomXAll)
    fullZoomIcon = Icon('icons/zoom-full')
    fullZoomAction.setIcon(fullZoomIcon)
    storeZoomAction = self.guiSpectrumDisplay.spectrumUtilToolBar.addAction("Store Zoom", self.storeZoom)
    storeZoomIcon = Icon('icons/zoom-store')
    storeZoomAction.setIcon(storeZoomIcon)
    storeZoomAction.setToolTip('Store Zoom')
    restoreZoomAction = self.guiSpectrumDisplay.spectrumUtilToolBar.addAction("Restore Zoom", self.restoreZoom)
    restoreZoomIcon = Icon('icons/zoom-restore')
    restoreZoomAction.setIcon(restoreZoomIcon)
    restoreZoomAction.setToolTip('Restore Zoom')

  # def showSpectrumPreferences(self, spectrum):
  #   form = QtGui.QDialog()
  #   layout = QtGui.QGridLayout()
  #   layout.addWidget(QtGui.QLabel(text='Peak Lists'))
  #   i=1
  #   # for peakList in spectrum.peakLists:
  #   #   label = QtGui.QLabel(form)
  #   #   label.setText(str(peakList.pid))
  #   #   checkBox = QtGui.QCheckBox()
  #   #   if spectrum.spectrumItem.peakListItems[peakList.pid].displayed == True:
  #   #     checkBox.setChecked(True)
  #   #   else:
  #   #     checkBox.setChecked(False)
  #   #
  #   #   checkBox.stateChanged.connect(lambda: self.peakListToggle(spectrum.spectrumItem, checkBox.checkState(),peakList))
  #   #   layout.addWidget(checkBox, i, 0)
  #   #   layout.addWidget(label, i, 1)
  #   #   i+=1
  #   #
  #   # layout.addWidget(QtGui.QLabel(text='Integrals'), 2, 0)
  #   # i+=1
  #
  #   newLabel = QtGui.QLabel(form)
  #   newLabel.setText(str(spectrum.pid)+' Integrals')
  #   newCheckBox = QtGui.QCheckBox()
  #   newCheckBox.setChecked(True)
  #   layout.addWidget(newCheckBox, i, 0)
  #   layout.addWidget(newLabel, i, 1)
  #   if spectrum.spectrumItem.integralListItems[0].displayed == True:
  #     newCheckBox.setChecked(True)
  #   else:
  #     newCheckBox.setChecked(False)
  #   newCheckBox.stateChanged.connect(lambda: self.integralToggle(newCheckBox.checkState(),spectrum.spectrumItem))
  #   i+=1
  #   newPushButton = QtGui.QPushButton('Colour')
  #
  #   layout.addWidget(newPushButton, i, 0, 1, 2)
  #   form.setLayout(layout)
  #   form.exec_()

  def addSpectrum(self, spectrum, guiSpectrumView):

    colour = QtGui.QColor(list(spectrumColours.keys())[self.colourIndex])
    data = guiSpectrumView.spectralData
    # if self.colourScheme == 'dark':
    #   colour = colour.lighter(f=120)
    # elif self.colourScheme == 'light':
    #   colour = colour.lighter(f=85)

    guiSpectrumView.plot = self.plotItem.plot(data[0],data[1], pen={'color':colour},clickable=True,)
    guiSpectrumView.plot.curve.setClickable(True)
    self.appBase.mainWindow.pythonConsole.write("current.pane.addSpectrum(%s)" % (spectrum))
    if self.colourIndex != len(spectrumColours) - 1:
      self.colourIndex +=1
    else:
      self.colourIndex = 0

    if self.spectrumIndex < 10:
      shortcutKey = "s,"+str(self.spectrumIndex)
      self.spectrumIndex+=1
    else:
      shortcutKey = None

    print(shortcutKey)
    pix=QtGui.QPixmap(60,10)
    pix.fill(QtGui.QColor(colour))
    guiSpectrumView.newAction = self.guiSpectrumDisplay.spectrumToolBar.addAction(guiSpectrumView.name, QtGui.QToolButton)
    newIcon = QtGui.QIcon(pix)
    guiSpectrumView.newAction.setIcon(newIcon)
    guiSpectrumView.newAction.setCheckable(True)
    guiSpectrumView.newAction.setChecked(True)
    guiSpectrumView.newAction.setShortcut(QtGui.QKeySequence(shortcutKey))
    guiSpectrumView.newAction.toggled.connect(guiSpectrumView.plot.setVisible)
    self.guiSpectrumDisplay.spectrumToolBar.addAction(guiSpectrumView.newAction)
    guiSpectrumView.widget = self.guiSpectrumDisplay.spectrumToolBar.widgetForAction(guiSpectrumView.newAction)
    guiSpectrumView.widget.setFixedSize(60,30)
    spectrum.spectrumView = guiSpectrumView