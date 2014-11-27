"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
import os

from collections import OrderedDict
from functools import partial

from PySide import QtCore, QtGui, QtOpenGL


import pyqtgraph as pg
from pyqtgraph.dockarea import Dock

from ccpncore.gui import ViewBox
from ccpnmrcore.gui.Axis import Axis

from ccpnmrcore.Base import Base

# abstract class: subclass needs to implement addSpectrum()

SPECTRUM_COLOURS = OrderedDict([('#ff0000','red'),
                                ('#00ffff','cyan'),
                                ('#ff8000','orange'),
                                ('#0080ff','manganese blue'),
                                ('#ffff00','yellow'),
                                ('#0000ff','blue'),
                                ('#80ff00','chartreuse'),
                                ('#8000ff','purple'),
                                ('#00ff00','green'),
                                ('#ff00ff','magenta'),
                                ('#00ff80','spring green'),
                                ('#ff0080','deep pink')])

class SpectrumPane(pg.PlotWidget, Base):

  sigClicked = QtCore.Signal(object, object)

  def __init__(self, project=None, parent=None, spectraVar=None, current=None, title=None, pid=None,
               mainWindow=None, preferences=None, **kw):

    if preferences.general.colourScheme == 'light':
      background = 'w'
      foreground = 'k'
    else:
      background = 'k'
      foreground = 'w'

    pg.setConfigOptions(background=background)
    pg.setConfigOptions(foreground=foreground)
    pg.PlotWidget.__init__(self, parent, viewBox=ViewBox.ViewBox(), axes=None, enableMenu=True,
                           background=background, foreground=foreground)
    Base.__init__(self,project=project, **kw)
    self.axes = self.plotItem.axes
    self.plotItem.setMenuEnabled(enableMenu=True, enableViewBoxMenu=False)
    self.title = title
    self.project = project
    self.mainWindow = mainWindow
    self.current = current
    self.pid = pid
    self.viewBox = self.plotItem.vb
    self.viewBox.parent = self
    self.viewBox.current = current
    self.xAxis = Axis(self, orientation='bottom')
    self.yAxis = Axis(self, orientation='right')
    # self.plotItem.setLabels(right=('Nh', 'ppm'), bottom=('Hn', 'ppm'))
    self.gridShown = None
    self.axes['left']['item'].hide()
    self.axes['right']['item'].show()
    self.axes['bottom']['item'].orientation = 'bottom'
    self.setAcceptDrops(True)
    self.crossHair = self.createCrossHair()
    self.scene().sigMouseMoved.connect(self.mouseMoved)
    self.scene().sigMouseHover.connect(self.setCurrentPane)
    self.storedZooms = []
    self.spectrumItems = []

    # print('parent',parent)
    if parent is None:
      self.dock = Dock(name=self.title, size=(1100,1300))
    elif isinstance(parent, Dock):
      self.dock = parent
    else:
      self.dock = None
    self.spectrumToolbar = QtGui.QToolBar()
    self.spectrumToolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
    self.spectrumToolbar.setMinimumHeight(44)
    self.spectrumToolbar.setMaximumWidth(550)

    self.spectrumUtilToolbar = QtGui.QToolBar()
    # self.spectrumToolbar.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Fixed)
    spectrumToolBarColor = QtGui.QColor(214,215,213)
    palette = QtGui.QPalette(self.spectrumToolbar.palette())
    palette.setColor(QtGui.QPalette.Button,spectrumToolBarColor)
    if self.dock:
      self.dock.addWidget(self.spectrumToolbar, 0, 0, 2, 6)
      self.dock.addWidget(self.spectrumUtilToolbar, 0, 6, 2, 3)

    self.spectrumIndex = 1
    self.viewBox.current = current
    self.positionBox = QtGui.QLabel()
    if self.dock:
      self.dock.addWidget(self.positionBox, 0, 9, 2, 2)
    self.scene().sigMouseMoved.connect(self.showMousePosition)
    if self.dock:
      self.dock.addWidget(self, 2, 0, 1, 11)

    if spectraVar is None:
      spectraVar = []

    self.setSpectra(spectraVar)
  #
  def setCurrentPane(self):
    self.current.pane = self

  def clicked(self, spectrum):
      self.current.spectrum = spectrum
      self.current.spectra.append(spectrum.parent)
      print(self.current.spectrum)
      self.mainWindow.pythonConsole.write('current.spectrum='+str(self.current.spectrum)+'\n')
      self.mainWindow.statusBar().showMessage('current.spectrum='+str(self.current.spectrum.pid))

  def clickedNd(self, spectrum):
    # if event.button() == QtCore.Qt.RightButton and not event.modifiers():
    #   event.accept()
    self.current.spectrum = spectrum
    self.current.spectra.append(spectrum)
    self.mainWindow.pythonConsole.write('current.spectrum='+str(self.current.spectrum.pid)+'\n')
    self.mainWindow.statusBar().showMessage('current.spectrum='+str(self.current.spectrum.pid))

  def createCrossHair(self):
    self.vLine = pg.InfiniteLine(angle=90, movable=False, pen='w')
    self.hLine = pg.InfiniteLine(angle=0, movable=False, pen='w')
    self.addItem(self.vLine, ignoreBounds=True, )
    self.addItem(self.hLine, ignoreBounds=True)


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

  def mouseMoved(self, event):
    position = event
    if self.sceneBoundingRect().contains(position):
        self.mousePoint = self.viewBox.mapSceneToView(position)
        self.vLine.setPos(self.mousePoint.x())
        self.hLine.setPos(self.mousePoint.y())
    return self.mousePoint
    
  def showMousePosition(self, pos):
    position = self.viewBox.mapSceneToView(pos).toTuple()
    self.positionBox.setText("X: %.3f  Y: %.3f" % position)

  def zoomToRegion(self, region):
    self.setXRange(region[0],region[1])
    self.setYRange(region[2],region[3])

  def zoomX(self, region):
    self.setXRange(region[0],region[1])

  def zoomY(self, region):
    self.setYRange(region[0],region[1])

  def zoomAll(self):
    self.autoRange()

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




  ##### functions used externally #####

  def clearSpectra(self):
    
    self.spectrumItems = []
        
  def addSpectrum(self, spectrumVar, dimMapping=None):

    raise Exception('should be implemented in subclass')

  def addSpectra(self, spectrumVars):
    for spectrumVar in spectrumVars:
      self.addSpectrum(spectrumVar)

  def setSpectra(self, spectraVar):

    self.clearSpectra()
    for spectrumVar in spectraVar:
      self.addSpectrum(spectrumVar)

  def dragEnterEvent(self, event):
    event.accept()

  def dropEvent(self,event):
    event.accept()
    # self.current.pane = self
    if isinstance(self.parent, QtGui.QGraphicsScene):
      event.ignore()
      return

    if event.mimeData().urls():

      filePaths = [url.path() for url in event.mimeData().urls()]
      if len(filePaths) == 1:
        for dirpath, dirnames, filenames in os.walk(filePaths[0]):
          if dirpath.endswith('memops') and 'Implementation' in dirnames:
            self.mainWindow.openProject(filePaths[0])
            self.addSpectra(self.project.spectra)

        else:
          print(filePaths[0])
          self.mainWindow.loadSpectra(filePaths[0])


      elif len(filePaths) > 1:
        [self.mainWindow.loadSpectra(filePath) for filePath in filePaths]


    else:
      data = (event.mimeData().retrieveData('application/x-qabstractitemmodeldatalist', str))
      #data = event.mimeData().text()
      print('RECEIVED mimeData: "%s"' % data)
      
      pidData = str(data.data(),encoding='utf-8')
      WHITESPACE_AND_NULL = ['\x01', '\x00', '\n','\x1e','\x02','\x03','\x04','\x0e','\x12', '\x0c', '\x05', '\x10', '\x14']
      pidData2 = [s for s in pidData if s not in WHITESPACE_AND_NULL]
      actualPid = ''.join(map(str, pidData2))
      print(list(actualPid))
      

      spectrum = self.getObject(actualPid)
      print(spectrum)
      self.addSpectrum(spectrum)
      self.current.spectrum = spectrum





  
  
