from PySide import QtGui, QtCore
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock
import random
import os
from functools import partial

from ccpnmrcore.modules.spectrumPane.Spectrum1dItem import Spectrum1dItem
from ccpnmrcore.modules.SpectrumPane import SpectrumPane
from ccpncore.gui import ViewBox
from ccpncore.gui.Button import Button
from ccpncore.gui.Colors import ColorDialog

class Spectrum1dPane(SpectrumPane):

  def __init__(self, project=None, parent=None, title=None, current=None):
    SpectrumPane.__init__(self, parent, project)
    pg.setConfigOptions(background='w')
    pg.setConfigOptions(foreground='k')
    self.project = project
    self.title = title
    self.viewBox = ViewBox.ViewBox()
    self.viewBox.parent = self
    self.viewBox.current = current
    self.xAxis = pg.AxisItem(orientation='top')
    self.yAxis = pg.AxisItem(orientation='right')
    self.widget = pg.PlotWidget( viewBox = self.viewBox,
      enableMenu=False, axisItems={
        'bottom':self.xAxis, 'right': self.yAxis})
    self.parent = parent
    self.widget.plotItem.setAcceptDrops(True)
    self.widget.dragEnterEvent = self.dragEnterEvent
    self.widget.dropEvent = self.dropEvent
    self.current = current
    self.viewBox.invertX()
    self.crossHair = self.createCrossHair()
    self.widget.scene().sigMouseMoved.connect(self.mouseMoved)
    self.widget.setAcceptDrops(True)
    self.widget.dropEvent = self.dropEvent
    ## setup axes for display
    self.axes = self.widget.plotItem.axes
    self.axes['left']['item'].hide()
    self.axes['right']['item'].show()
    self.axes['bottom']['item'].orientation = 'bottom'
    self.dock = Dock(name=self.title, size=(1000,1000))
    self.spectrumToolbar = QtGui.QToolBar()
    self.spectrumToolbar.setMovable(True)
    self.spectrumToolbar.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
    self.dock.addWidget(self.spectrumToolbar, 0, 0, 2, 9)
    self.spectrumIndex = 1
    self.viewBox.current = current
    self.positionBox = QtGui.QPushButton()
    self.dock.addWidget(self.positionBox, 0, 10, 2, 1)
    self.widget.scene().sigMouseMoved.connect(self.showMousePosition)
    self.dock.addWidget(self.widget, 2, 1, 1, 10)


  # def addSpectrum(self, spectrumVar, region=None, dimMapping=None):
  #   spectrumItem = Spectrum1dItem(self, spectrumVar, region, dimMapping)

  # def addModule(self):
  #   newDock = Dock("Module 1", size=(1000,1000))
  #   spectrumToolbar = QtGui.QToolBar()
  #   newDock.addWidget(spectrumToolbar)
  #   newDock.addWidget(self.widget)


  def createCrossHair(self):
    self.vLine = pg.InfiniteLine(angle=90, movable=False)
    self.hLine = pg.InfiniteLine(angle=0, movable=False)
    self.widget.addItem(self.vLine, ignoreBounds=True)
    self.widget.addItem(self.hLine, ignoreBounds=True)


  def showMousePosition(self, pos):

    position = self.viewBox.mapSceneToView(pos).toTuple()
    self.positionBox.setText("X: %.3f  I: %.2E" % position)

  def mouseMoved(self, event):
    position = event
    if self.widget.sceneBoundingRect().contains(position):
        mousePoint = self.viewBox.mapSceneToView(position)
        self.vLine.setPos(mousePoint.x())
        self.hLine.setPos(mousePoint.y())

  def clicked(self, spectrum):
    self.current.spectrum = spectrum.parent
    self.current.spectra.append(spectrum.parent)
    self.parent.pythonConsole.write('######current.spectrum='+str(self.current.spectrum)+'\n')


  def addSpectra(self, spectra):
    for spectrum in spectra:
      self.addSpectrum(spectrum)


  def addSpectrum(self, spectrum):

    spectrumItem = Spectrum1dItem(self,spectrum)
    colour = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
    # spectrumItem = self.widget.plotItem
    data = spectrumItem.spectralData
    spectrumItem.plot = self.widget.plotItem.plot(data[0],data[1], pen={'color':colour},clickable=True,)
    spectrumItem.colour = QtGui.QColor.fromRgb(colour[0],colour[1],colour[2])
    spectrumItem.name = spectrum.name
    spectrumItem.plot.parent = spectrum
    spectrumItem.plot.curve.setClickable(True)
    spectrumItem.plot.sigClicked.connect(self.clicked)
    spectrumItem.toolBarButton = Button(self.parent,text=spectrum.name,action=partial(self.showSpectrumPreferences,spectrum))
    spectrumItem.toolBarButton.setCheckable(True)
    spectrumItem.toolBarButton.setChecked(True)
    palette = QtGui.QPalette(spectrumItem.toolBarButton.palette())
    # print(spectrum.colour)
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
    # pass


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
      # checkBox.toggle()
      layout.addWidget(checkBox, i, 0)
      layout.addWidget(label, i, 1)
      i+=1

    layout.addWidget(QtGui.QLabel(text='Integrals'), 2, 0)
    i+=1
    # Set dialog layout

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
    # newPushButton = Button(self.parent,text="Colour",action=self.changeSpectrumColour)
    newPushButton = QtGui.QPushButton('Colour')
    newPushButton.clicked.connect(partial(self.changeSpectrumColour, spectrum.spectrumItem))
    layout.addWidget(newPushButton, i, 0, 1, 2)
    # okButton = QtGui.QPushButton("OK")
    # layout.addWidget(okButton, i+1, 0, 1, 2)


    form.setLayout(layout)

    form.exec_()

  def changeSpectrumColour(self, spectrumItem):
    dialog = ColorDialog()
    # print(dir(spectrumItem))
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

  def showSpectrum(self, spectrum):
    spectrum.spectrumItem.plot.show()

  def hideSpectrum(self, spectrum):
    spectrum.spectrumItem.plot.hide()

  def showPeaks(self, spectrumItem, peakList):
    spectrumItem.showPeaks(peakList)

  def showIntegrals(self, spectrumItem):
    spectrumItem.showIntegrals()

  def hideIntegrals(self, spectrumItem):
    spectrumItem.hideIntegrals()

  def hidePeaks(self, spectrumItem, peakList):

    spectrumItem.hidePeaks(peakList)


  def hideIntegrals(self, spectrum):

    for marking in spectrum.spectrumItem.integralMarkings:
      marking.hide()
      self.integralMarkings.displayed = False


  def createIntegralMarkings(self, spectrum):

    for integral in spectrum.spectrumItem.integrals:
        spectrum.spectrumItem.integralMarkings.displayed = False
        position = (integral.lastPoint+integral.firstPoint)/2
        text = pg.TextItem(html=("%.1f&#x222b" % round(integral.volume*spectrum.ccpnSpectrum.integralFactor,2)),color='k')
        roi = pg.LineSegmentROI([[integral.firstPoint,0],[integral.lastPoint,0]], pen='k')
        # roi.addItem(text)
        self.widget.addItem(text)
        self.widget.addItem(roi)
        text.setPos(float(position),-3)
        spectrum.spectrumItem.integralMarkings.append(roi)
        spectrum.spectrumItem.integralMarkings.append(text)


  def zoomToRegion(self, region):
    self.widget.setXRange(region[0],region[1])
    self.widget.setYRange(region[2],region[3])

  def zoomX(self, region):
    self.widget.setXRange(region[0],region[1])

  def zoomY(self, region):
    self.widget.setYRange(region[0],region[1])

  def zoomAll(self):
    self.widget.autoRange()

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
      for peakList in spectrum.peakLists:
        self.createPeakMarkings(peakList)
      self.createIntegralMarkings(spectrum)
