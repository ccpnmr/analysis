__author__ = 'simon'

from PySide import QtGui, QtCore, QtOpenGL

from ccpncore.gui.Icon import Icon

from ccpnmrcore.modules.GuiStrip import GuiStrip

class GuiStripNd(GuiStrip):

  def __init__(self, guiFrame, apiStrip, **kw):
    GuiStrip.__init__(self, guiFrame, apiStrip)

    self.plotItem.setAcceptDrops(True)
    self.setViewport(QtOpenGL.QGLWidget())
    self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
    ###self.viewBox.menu = self.get2dContextMenu()
    self.viewBox.invertX()
    self.viewBox.invertY()
    ###self.region = guiSpectrumDisplay.defaultRegion()
    self.planeLabel = None
    self.axesSwapped = False
    # print(guiSpectrumDisplay)
    # self.fillToolBar()
    ###self.setShortcuts()

  """
  def showSpectrum(self, guiSpectrumView):
    orderedAxes = self.strip.orderedAxes
    self.xAxis = orderedAxes[0]
    self.yAxis = orderedAxes[1]
    self.zAxis = orderedAxes[2:]
    apiSpectrum = guiSpectrumView.dataSource

    newItem = self.scene().addItem(guiSpectrumView)
"""
  def addSpectrum(self, spectrum, guiSpectrumView):

    # resetAllAxisCodes(self.project._wrappedData)
    # spectrum = self.getObject(spectrumVar)
    # if spectrum.dimensionCount < 1:
    #   # TBD: logger message
    #   return
    #
    # # TBD: check if dimensions make sense
    # self.posColors = list(SPECTRUM_COLOURS.keys())[self.colourIndex]
    # self.negColors = list(SPECTRUM_COLOURS.keys())[self.colourIndex+1]
    # # if len(self.spectrumItems) >= 1:
    # #   if self.spectrumItems[0].spectrum.axisCodes == spectrum.axisCodes:
    # #     spectrumItem = SpectrumNdItem(self, spectrum, self.spectrumItems[0].dimMapping, self.region, self.posColors, self.negColors)
    # #     self.spectrumItems[0].spectrum.axisCodes
    # #   else:
    # #     print('Axis codes do not match pane')
    # #     return
    # #
    # # else:
    # spectrumItem = GuiSpectrumViewNd(self, spectrum, dimMapping, self.region, self.posColors, self.negColors)
    newItem = self.scene().addItem(guiSpectrumView)


  # def fillToolBar(self):
  #   spectrumUtilToolBar =  self.guiSpectrumDisplay.spectrumUtilToolBar
  #   plusOneAction = spectrumUtilToolBar.addAction("+1", self.addOne)
  #   plusOneIcon = Icon('icons/contourAdd')
  #   plusOneAction.setIcon(plusOneIcon)
  #   plusOneAction.setToolTip('Add One Level')
  #   minusOneAction = spectrumUtilToolBar.addAction("+1", self.subtractOne)
  #   minusOneIcon = Icon('icons/contourRemove')
  #   minusOneAction.setIcon(minusOneIcon)
  #   minusOneAction.setToolTip('Remove One Level ')
  #   upBy2Action = spectrumUtilToolBar.addAction("*1.4", self.upBy2)
  #   upBy2Icon = Icon('icons/contourBaseUp')
  #   upBy2Action.setIcon(upBy2Icon)
  #   upBy2Action.setToolTip('Raise Contour Base Level')
  #   downBy2Action = spectrumUtilToolBar.addAction("*1.4", self.downBy2)
  #   downBy2Icon = Icon('icons/contourBaseDown')
  #   downBy2Action.setIcon(downBy2Icon)
  #   downBy2Action.setToolTip('Lower Contour Base Level')
  #   storeZoomAction = spectrumUtilToolBar.addAction("Store Zoom", self.storeZoom)
  #   storeZoomIcon = Icon('icons/zoom-store')
  #   storeZoomAction.setIcon(storeZoomIcon)
  #   storeZoomAction.setToolTip('Store Zoom')
  #   restoreZoomAction = spectrumUtilToolBar.addAction("Restore Zoom", self.restoreZoom)
  #   restoreZoomIcon = Icon('icons/zoom-restore')
  #   restoreZoomAction.setIcon(restoreZoomIcon)
  #   restoreZoomAction.setToolTip('Restore Zoom')

  def upBy2(self):
    for spectrumItem in self.spectrumItems:
      spectrumItem.baseLevel*=1.4
      spectrumItem.levels = spectrumItem.getLevels()

  def downBy2(self):
    for spectrumItem in self.spectrumItems:
      spectrumItem.baseLevel/=1.4
      spectrumItem.levels = spectrumItem.getLevels()

  def addOne(self):
    self.current.spectrum.spectrumItem.numberOfLevels +=1
    self.current.spectrum.spectrumItem.levels = self.current.spectrum.spectrumItem.getLevels()


  def subtractOne(self):
    self.current.spectrum.spectrumItem.numberOfLevels -=1
    self.current.spectrum.spectrumItem.levels = self.current.spectrum.spectrumItem.getLevels()