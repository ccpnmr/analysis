from PySide import QtGui, QtCore
import random
from functools import partial

from ccpnmrcore.modules.spectrumPane.Spectrum1dItem import Spectrum1dItem
from ccpnmrcore.modules.SpectrumPane import SpectrumPane
from ccpncore.gui.Button import Button
from ccpncore.gui.ColourDialog import ColorDialog
from ccpncore.gui.Action import Action
from ccpncore.gui.Menu import Menu

class Spectrum1dPane(SpectrumPane):

  def __init__(self, project=None, parent=None, title=None, current=None):
    SpectrumPane.__init__(self, project, parent, title=title)
    # self.contextMenu = None
    self.project = project
    self.parent = parent
    self.viewBox.invertX()
    self.showGrid(x=True, y=True)
    self.gridShown = True
    self.crossHairShown = True
    self.autoIntegration = True
    self.viewBox.menu = self.get1dContextMenu()
    self.current = current
    self.plotItem.setAcceptDrops(True)
    self.title = title
    self.spectrumItems = []
    self.fillToolBar()
    

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
    self.contextMenu.addItem("Peaks", callback=self.peakListToggle)
    self.contextMenu.addSeparator()
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
      self.vLine.hide()
      self.hLine.hide()
      self.crossHairShown = False
    else:
      self.vLine.show()
      self.hLine.show()
      self.crossHairShown = True

  def hideCrossHair(self):
    self.spectrumPane.vLine.hide()
    self.spectrumPane.hLine.hide()


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
    self.storedZoom = self.viewBox.viewRange()

  def restoreZoom(self):
    self.setXRange(self.storedZoom[0][0], self.storedZoom[0][1])
    self.setYRange(self.storedZoom[1][0], self.storedZoom[1][1])

  def addSpectra(self, spectra):
    for spectrum in spectra:
      self.addSpectrum(spectrum)


  def addSpectrum(self, spectrum):

    spectrumItem = Spectrum1dItem(self,spectrum)
    colour = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
    data = spectrumItem.spectralData
    spectrumItem.plot = self.plotItem.plot(data[0],data[1], pen={'color':colour},clickable=True,)
    spectrumItem.colour = QtGui.QColor.fromRgb(colour[0],colour[1],colour[2])
    spectrumItem.name = spectrum.name
    spectrumItem.plot.parent = spectrum
    spectrumItem.plot.curve.setClickable(True)
    spectrumItem.plot.sigClicked.connect(self.clicked)
    spectrumItem.toolBarButton = Button(self.parent,text=spectrum.name)#,action=partial(self.showSpectrumPreferences,spectrum))
    spectrumItem.toolBarButton.setCheckable(True)
    spectrumItem.toolBarButton.setChecked(True)
    palette = QtGui.QPalette(spectrumItem.toolBarButton.palette())
    palette.setColor(QtGui.QPalette.Button,spectrumItem.colour)
    spectrumItem.toolBarButton.setPalette(palette)
    spectrumItem.toolBarButton.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
    spectrumItem.toolBarButton.toggled.connect(spectrumItem.plot.setVisible)

    if self.spectrumIndex < 10:
      shortcutKey = "s,"+str(self.spectrumIndex)
      self.spectrumIndex+=1
    else:
      shortcutKey = None

    spectrumItem.toolBarButton.setShortcut(QtGui.QKeySequence(shortcutKey))
    self.spectrumToolbar.addWidget(spectrumItem.toolBarButton)
    spectrum.spectrumItem = spectrumItem
    for peakList in spectrum.peakLists:
      spectrumItem.addPeaks(self, peakList)
    spectrumItem.addIntegrals(self)
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
    newPushButton.clicked.connect(partial(self.changeSpectrumColour, spectrum.spectrumItem))
    layout.addWidget(newPushButton, i, 0, 1, 2)
    form.setLayout(layout)
    form.exec_()

  def changeSpectrumColour(self, spectrumItem):
    dialog = ColorDialog()
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
