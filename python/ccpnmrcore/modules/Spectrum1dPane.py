from PySide import QtGui, QtCore
import random
import os
from functools import partial

from ccpnmrcore.modules.spectrumPane.Spectrum1dItem import Spectrum1dItem
from ccpnmrcore.modules.SpectrumPane import SpectrumPane
from ccpncore.gui.Button import Button
from ccpncore.gui.Colors import ColorDialog

class Spectrum1dPane(SpectrumPane):

  def __init__(self, project=None, parent=None, title=None, current=None):
    SpectrumPane.__init__(self, parent, project)
    self.project = project
    self.parent = parent
    self.viewBox.invertX()
    self.current = current
    self.plotItem.setAcceptDrops(True)
    self.title = title
    print(self.title)


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
    spectrumItem.toolBarButton = Button(self.parent,text=spectrum.name,action=partial(self.showSpectrumPreferences,spectrum))
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


  def peakListToggle(self, spectrumItem, state, peakList):
    if state == QtCore.Qt.Checked:
      self.showPeaks(spectrumItem, peakList)
    if state == QtCore.Qt.Unchecked:
      self.hidePeaks(spectrumItem, peakList)

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
    print(peakList)
    spectrumItem.addPeaks(self, peakList)

  def showPeaks(self, spectrumItem, peakList):
    spectrumItem.showPeaks(peakList)

  def showIntegrals(self, spectrumItem):
    spectrumItem.showIntegrals()

  def hideIntegrals(self, spectrumItem):
    spectrumItem.hideIntegrals()

  def hidePeaks(self, spectrumItem, peakList):

    spectrumItem.hidePeaks(peakList)


  def dropEvent(self,event):
    event.accept()
    if isinstance(self.parent, QtGui.QGraphicsScene):
      event.ignore()
      return

    if event.mimeData().urls():

      filePaths = [url.path() for url in event.mimeData().urls()]
      print(filePaths)
      print(len(filePaths))
      if len(filePaths) == 1:
        for dirpath, dirnames, filenames in os.walk(filePaths[0]):
          if dirpath.endswith('memops') and 'Implementation' in dirnames:
            self.parent.openProject(filePaths[0])
            self.addSpectra(self.project.spectra)

    else:
      data = (event.mimeData().retrieveData('application/x-qabstractitemmodeldatalist', str))
      pidData = str(data.data(),encoding='utf-8')
      WHITESPACE_AND_NULL = ['\x01', '\x00', '\n','\x1e','\x02','\x03','\x04']
      pidData2 = [s for s in pidData if s not in WHITESPACE_AND_NULL]
      actualPid = ''.join(map(str, pidData2))
      spectrum = self.project.getById(actualPid)
      print(actualPid, spectrum)
      spectrum = self.addSpectrum(spectrum)
      self.current.spectrum = spectrum
      self.current.pane = self