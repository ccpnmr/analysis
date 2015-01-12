__author__ = 'simon'

from PySide import QtGui, QtCore, QtOpenGL

from ccpnmrcore.modules.GuiStrip import GuiStrip

class GuiStripNd(GuiStrip):

  def __init__(self, guiSpectrumDisplay, apiStrip, **kw):
    GuiStrip.__init__(self, guiSpectrumDisplay, apiStrip)

    self.plotItem.setAcceptDrops(True)
    self.setViewport(QtOpenGL.QGLWidget())
    self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
    ###self.viewBox.menu = self.get2dContextMenu()
    self.viewBox.invertX()
    self.viewBox.invertY()
    ###self.region = guiSpectrumDisplay.defaultRegion()
    self.planeLabel = None
    self.axesSwapped = False
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