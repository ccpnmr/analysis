__author__ = 'simon'

from PySide import QtGui, QtCore, QtOpenGL

from ccpnmrcore.modules import GuiStrip

class GuiNdStrip(GuiStrip):

  def __init__(self, *args, **kw):

    GuiNdStrip.__init__(self, *args, **kw)

    self.plotItem.setAcceptDrops(True)
    self.setViewport(QtOpenGL.QGLWidget())
    self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
    self.viewBox.menu = self.get2dContextMenu()
    self.viewBox.invertX()
    self.viewBox.invertY()
    self.region = None
    self.planeLabel = None
    self.axesSwapped = False
    self.setShortcuts()

  def showSpectrum(self, guiSpectrumView):
    orderedAxes = self.strip.orderedAxes
    self.xAxis = orderedAxes[0]
    self.yAxis = orderedAxes[1]
    self.zAxis = orderedAxes[2:]
    apiSpectrum = guiSpectrumView.dataSource

    newItem = self.scene().addItem(spectrumItem)