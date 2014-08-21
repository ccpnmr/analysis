from PySide import QtGui, QtCore
import random
from functools import partial

from ccpnmrcore.modules.spectrumPane.Spectrum1dItem import Spectrum1dItem
from ccpnmrcore.modules.SpectrumPane import SpectrumPane, SPECTRUM_COLOURS
from ccpncore.gui.Button import Button
from ccpncore.gui.ColourDialog import ColourDialog
from ccpncore.gui.Action import Action
from ccpncore.gui.Menu import Menu
from ccpncore.util import Logging


class Spectrum1dPane(SpectrumPane):

  def __init__(self, project=None, parent=None, title=None, current=None, pid=None, preferences=None):
    SpectrumPane.__init__(self, project, parent, title=title, pid=pid, preferences=preferences)
    # self.contextMenu = None
    self.project = project
    self.pid = pid
    self.parent = parent
    self.viewBox.invertX()
    self.showGrid(x=True, y=True)
    self.gridShown = True
    self.crossHairShown = True
    self.autoIntegration = True
    self.current = current
    self.viewBox.menu = self.get1dContextMenu()
    self.plotItem.setAcceptDrops(True)
    self.title = title
    self.spectrumItems = []
    self.fillToolBar()
    self.storedZooms = []
    self.colourIndex = 0

  def fillToolBar(self):

    self.spectrumUtilToolbar.addAction("AutoScale", self.zoomYAll)
    self.spectrumUtilToolbar.addAction("Full", self.zoomXAll)
    self.spectrumUtilToolbar.addAction("Store Zoom", self.storeZoom)
    self.spectrumUtilToolbar.addAction("Restore Zoom", self.restoreZoom)
    self.spectrumUtilToolbar.addAction("Undo", self.zoomXAll)
    self.spectrumUtilToolbar.addAction("Redo", self.zoomXAll)
    #

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
    self.contextMenu.addAction(self.gridAction, isFloatWidget=True)
    self.contextMenu.addSeparator()
    self.peakAction = QtGui.QAction("Peaks", self, triggered=self.peakListToggle, checkable=True)
    # if self.current.spectrum is not None:
    #   if self.current.spectrum.spectrumItem.peakListItems[self.current.spectrum.peakLists[0].pid].displayed == True:
    #     self.peakAction.setChecked(True)
    #   else:
    #     print("self.current.spectrum is None")
    #     self.peakAction.setChecked(False)
    self.contextMenu.addAction(self.peakAction, isFloatWidget=True)
    self.contextMenu.addItem("Integrals", callback=self.integralToggle)
    self.autoIntegrationAction = QtGui.QAction("Automatic", self,
                                               triggered=self.toggleIntegrationMethod, checkable=True, )
    self.manualIntegrationAction = QtGui.QAction("Manual", self,
                                                 triggered=self.toggleIntegrationMethod, checkable=True)
    if self.autoIntegration == True:
      self.autoIntegrationAction.setChecked(True)
      self.manualIntegrationAction.setChecked(False)
    if self.autoIntegration == False:
      self.autoIntegrationAction.setChecked(False)
      self.manualIntegrationAction.setChecked(True)
    self.contextMenu.addAction(self.autoIntegrationAction, isFloatWidget=True)
    self.contextMenu.addAction(self.manualIntegrationAction, isFloatWidget=True)

      # self.integrationAction = Action(self, self.integrationMethod, self.toggleIntegrationMethod)
      # self.contextMenu.addAction(self.integrationAction)

    self.contextMenu.addSeparator()
    self.contextMenu.addItem("Print", callback=self.raisePrintMenu)
    return self.contextMenu

  def toggleIntegrationMethod(self):
    if self.autoIntegration == True:
      self.autoIntegration = False
    else:
      self.autoIntegration = True

  def toggleCrossHair(self):
    if self.crossHairShown ==True:
      self.hideCrossHair()
    else:
      self.showCrossHair()
      self.crossHairShown = True

  def showCrossHair(self):
      self.vLine.show()
      self.hLine.show()
      self.crossHairAction.setChecked(True)
      self.crossHairShown = True

  def hideCrossHair(self):
    self.vLine.hide()
    self.hLine.hide()
    self.crossHairAction.setChecked(False)
    self.crossHairShown = False


  def toggleGrid(self):
    if self.gridShown == True:
      self.showGrid(x=False, y=False)
      self.gridShown = False
    else:
      self.showGrid(x=True, y=True)
      self.gridShown = True

  def raisePrintMenu(self):
    pass

  def zoomYAll(self):
    y2 = self.viewBox.childrenBoundingRect().top()
    y1 = y2 + self.viewBox.childrenBoundingRect().height()
    self.viewBox.setYRange(y2,y1)

  def zoomXAll(self):
    x2 = self.viewBox.childrenBoundingRect().left()
    x1 = x2 + self.viewBox.childrenBoundingRect().width()
    self.viewBox.setXRange(x2,x1)

  def zoomTo(self, x1, x2, y1, y2):
    self.zoomToRegion([float(x1.text()),float(x2.text()),float(y1.text()),float(y2.text())])
    self.zoomPopup.close()

  def raiseZoomPopup(self):
    self.zoomPopup = QtGui.QDialog()
    layout = QtGui.QGridLayout()
    layout.addWidget(QtGui.QLabel(text='x1'), 0, 0)
    x1 = QtGui.QLineEdit()
    layout.addWidget(x1, 0, 1, 1, 1)
    layout.addWidget(QtGui.QLabel(text='x2'), 0, 2)
    x2 = QtGui.QLineEdit()
    layout.addWidget(x2, 0, 3, 1, 1)
    layout.addWidget(QtGui.QLabel(text='y1'), 1, 0,)
    y1 = QtGui.QLineEdit()
    layout.addWidget(y1, 1, 1, 1, 1)
    layout.addWidget(QtGui.QLabel(text='y2'), 1, 2)
    y2 = QtGui.QLineEdit()
    layout.addWidget(y2, 1, 3, 1, 1)
    okButton = QtGui.QPushButton(text="OK")
    okButton.clicked.connect(partial(self.zoomTo,x1,x2,y1,y2))
    cancelButton = QtGui.QPushButton(text='Cancel')
    layout.addWidget(okButton,2, 1)
    layout.addWidget(cancelButton, 2, 3)
    cancelButton.clicked.connect(self.zoomPopup.close)
    self.zoomPopup.setLayout(layout)
    self.zoomPopup.exec_()


  def storeZoom(self):
    self.storedZooms.append(self.viewBox.viewRange())

  def restoreZoom(self):
    if len(self.storedZooms) != 0:
      restoredZoom = self.storedZooms.pop()
      self.setXRange(restoredZoom[0][0], restoredZoom[0][1])
      self.setYRange(restoredZoom[1][0], restoredZoom[1][1])


  def addSpectrum(self, spectrum):

    spectrumItem = Spectrum1dItem(self,spectrum)
    colour = list(SPECTRUM_COLOURS.keys())[self.colourIndex]
    data = spectrumItem.spectralData
    spectrumItem.plot = self.plotItem.plot(data[0],data[1], pen={'color':colour},clickable=True,)
    spectrumItem.colour = QtGui.QColor(colour)
    spectrumItem.name = spectrum.name
    spectrumItem.plot.parent = spectrum
    spectrumItem.plot.curve.setClickable(True)
    spectrumItem.plot.sigClicked.connect(self.clicked)
    # spectrumItem.toolBarButton = QtGui.QToolButton(self.parent,text=spectrum.name)
    # spectrumItem.toolBarButton.setCheckable(True)
    # spectrumItem.toolBarButton.setChecked(True)
    # # print(spectrumItem.toolBarButton.actions())
    # palette = QtGui.QPalette(spectrumItem.toolBarButton.palette())
    # palette.setColor(QtGui.QPalette.Button,colour)
    # spectrumItem.toolBarButton.setPalette(palette)
    # spectrumItem.toolBarButton.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
    # spectrumItem.toolBarButton.toggled.connect(spectrumItem.plot.setVisible)

    self.parent.pythonConsole.write("current.pane.addSpectrum(%s)" % (spectrum))
    if self.colourIndex != len(SPECTRUM_COLOURS) - 1:
      self.colourIndex +=1
    else:
      self.colourIndex = 0

    if self.spectrumIndex < 10:
      shortcutKey = "s,"+str(self.spectrumIndex)
      self.spectrumIndex+=1
    else:
      shortcutKey = None

    # spectrumItem.toolBarButton.setShortcut(QtGui.QKeySequence(shortcutKey))
    newAction = self.spectrumToolbar.addAction(spectrumItem.name, QtGui.QToolButton)
    newAction.setCheckable(True)
    newAction.setChecked(True)
    newAction.setShortcut(QtGui.QKeySequence(shortcutKey))
    palette = QtGui.QPalette(newAction.associatedWidgets()[1].palette())
    palette.setColor(QtGui.QPalette.ColorRole(0), spectrumItem.colour)
    # print(dir(newAction.associatedWidgets()[1]))
    print(newAction.associatedWidgets()[1].palette().color(QtGui.QPalette.ColorRole(0)))
    newAction.associatedWidgets()[1].palette().setColor(QtGui.QPalette.Button, spectrumItem.colour)
    print(newAction.associatedWidgets()[1].palette().color(QtGui.QPalette.ColorRole(0)))
    # newAction.associatedWidgets()[1].setPalette(palette)
    newAction.toggled.connect(spectrumItem.plot.setVisible)
    self.spectrumToolbar.addAction(newAction)




    spectrum.spectrumItem = spectrumItem
    # for peakList in spectrum.peakLists:
    #   spectrumItem.addPeaks(self, peakList)
    # spectrumItem.addIntegrals(self)
    self.spectrumItems.append(spectrumItem)
    return spectrum


  def showSpectrumPreferences(self,spectrum):
    form = QtGui.QDialog()
    layout = QtGui.QGridLayout()
    layout.addWidget(QtGui.QLabel(text='Peak Lists'))
    i=1
    for peakList in spectrum.peakLists:
      label = QtGui.QLabel(form)
      label.setText(str(peakList.pid))
      checkBox = QtGui.QCheckBox()
      if spectrum.spectrumItem.peakListItems[peakList.pid].displayed == True:
        checkBox.setChecked(True)
      else:
        checkBox.setChecked(False)

      checkBox.stateChanged.connect(lambda: self.peakListToggle(spectrum.spectrumItem, checkBox.checkState(),peakList))
      layout.addWidget(checkBox, i, 0)
      layout.addWidget(label, i, 1)
      i+=1

    layout.addWidget(QtGui.QLabel(text='Integrals'), 2, 0)
    i+=1

    newLabel = QtGui.QLabel(form)
    newLabel.setText(str(spectrum.pid)+' Integrals')
    newCheckBox = QtGui.QCheckBox()
    newCheckBox.setChecked(True)
    layout.addWidget(newCheckBox, i, 0)
    layout.addWidget(newLabel, i, 1)
    if spectrum.spectrumItem.integralListItems[0].displayed == True:
      newCheckBox.setChecked(True)
    else:
      newCheckBox.setChecked(False)
    newCheckBox.stateChanged.connect(lambda: self.integralToggle(newCheckBox.checkState(),spectrum.spectrumItem))
    i+=1
    newPushButton = QtGui.QPushButton('Colour')

    layout.addWidget(newPushButton, i, 0, 1, 2)
    form.setLayout(layout)
    form.exec_()

  def changeSpectrumColour(self, spectrumItem):
    dialog = ColourDialog()
    spectrumItem.colour = dialog.getColor()
    palette = QtGui.QPalette(spectrumItem.toolBarButton.palette())
    palette.setColor(QtGui.QPalette.Button,spectrumItem.colour)
    spectrumItem.toolBarButton.setPalette(palette)
    spectrumItem.plot.setPen(spectrumItem.colour)


  def peakListToggle(self):
    pass

  def integralToggle(self, state, spectrumItem):
    if state == QtCore.Qt.Checked:
      spectrumItem.showIntegrals()
    if state == QtCore.Qt.Unchecked:
      spectrumItem.hideIntegrals()

  def removeSpectrum(self, spectrum):
    pass

  def findPeaks(self, spectrum):
    peakList = spectrum.spectrumItem.findPeaks()
    self.addPeaks(spectrum.spectrumItem, peakList)

  def showSpectrum(self, spectrum):
    spectrum.spectrumItem.plot.show()

  def hideSpectrum(self, spectrum):
    spectrum.spectrumItem.plot.hide()

  def addPeaks(self,spectrumItem, peakList):
    spectrumItem.addPeaks(self, peakList)

  def showPeaks(self, spectrumItem, peakList):
    spectrumItem.showPeaks(peakList)

  def showIntegrals(self, spectrumItem):
    spectrumItem.showIntegrals()

  def hideIntegrals(self, spectrumItem):
    spectrumItem.hideIntegrals()

  def hidePeaks(self, spectrumItem, peakList):

    spectrumItem.hidePeaks(peakList)
