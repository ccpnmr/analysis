__author__ = 'simon'

import pyqtgraph as pg

from PySide import QtGui, QtCore

from ccpncore.gui import ViewBox

from ccpnmrcore.Base import Base as GuiBase

from ccpnmrcore.gui.Axis import Axis



class GuiStrip(pg.PlotWidget, GuiBase):

  sigClicked = QtCore.Signal(object, object)

  def __init__(self, guiSpectrumDisplay, spectraVar, **kw):
    self.guiSpectrumDisplay = guiSpectrumDisplay
    # self.strip = strip
    background = 'k'
    foreground = 'w'

    pg.setConfigOptions(background=background)
    pg.setConfigOptions(foreground=foreground)
    pg.PlotWidget.__init__(self, viewBox=ViewBox.ViewBox(), axes=None, enableMenu=True,
                           background=background, foreground=foreground)

    GuiBase.__init__(self, guiSpectrumDisplay.appBase)
    self.axes = self.plotItem.axes
    self.plotItem.setMenuEnabled(enableMenu=True, enableViewBoxMenu=False)
    self.viewBox = self.plotItem.vb
    # self.viewBox.parent = self
    # self.viewBox.current = self.current
    self.xAxis = Axis(self, orientation='top')
    self.yAxis = Axis(self, orientation='left')
    self.gridShown = True
    self.axes['left']['item'].hide()
    self.axes['right']['item'].show()
    self.axes['bottom']['item'].orientation = 'top'
    self.axes['right']['item'].orientation = 'left'
    self.grid = pg.GridItem()
    self.addItem(self.grid)
    self.setAcceptDrops(True)
    # self.crossHair = self.createCrossHair()
    # self.scene().sigMouseMoved.connect(self.mouseMoved)
    # self.scene().sigMouseHover.connect(self.setCurrentPane)
    self.storedZooms = []
    self.spectrumItems = []
    if spectraVar is None:
      spectraVar = []
    guiSpectrumDisplay.addWidget(self)
    # self.setSpectra(spectraVar)

  def showSpectrum(self, guiSpectrumView):
    raise Exception('should be implemented in subclass')