from PySide import QtGui, QtCore
import pyqtgraph as pg
from ccpnmrcore.modules.spectrumPane.Spectrum1dItem import Spectrum1dItem
# from ccpn.lib.Spectrum import getSpectrumFileFormat

from ccpnmrcore.modules.SpectrumPane import SpectrumPane
from ccpncore.gui import ViewBox


class Spectrum1dPane(SpectrumPane):

  def __init__(self):

    pg.setConfigOptions(background='w')
    pg.setConfigOptions(foreground='k')
    self.viewBox = ViewBox.ViewBox()
    self.xAxis = pg.AxisItem(orientation='top')
    self.yAxis = pg.AxisItem(orientation='right')
    self.widget = pg.PlotWidget( viewBox = self.viewBox,
      enableMenu=False, axisItems={
        'bottom':self.xAxis, 'right': self.yAxis})
    # self.dock = pg.dockarea.Dock("Dock1", size=(1, 1))
    # self.dockArea = pg.dockarea.DockArea()

    self.widget.plotItem.setAcceptDrops(True)
    self.widget.dragEnterEvent = self.dragEnterEvent
    self.widget.dropEvent = self.dropEvent
    self.viewBox.invertX()
    self.crossHair = self.createCrossHair()
    # connect cross hair (mouseMoved)
    self.widget.scene().sigMouseMoved.connect(self.mouseMoved)
    self.widget.setAcceptDrops(True)
    self.widget.dropEvent = self.dropEvent
    print(self.widget.setAcceptDrops)
    ## setup axes for display
    self.axes = self.widget.plotItem.axes
    self.axes['left']['item'].hide()
    self.axes['right']['item'].show()
    self.axes['bottom']['item'].orientation = 'bottom'
    # print(isinstance(self.parent, QtGui.QGraphicsScene))


  def addSpectrum(self, spectrumVar, region=None, dimMapping=None):
    spectrumItem = Spectrum1dItem(self, spectrumVar, region, dimMapping)

  def createCrossHair(self):
    self.vLine = pg.InfiniteLine(angle=90, movable=False)
    self.hLine = pg.InfiniteLine(angle=0, movable=False)
    self.widget.addItem(self.vLine, ignoreBounds=True)
    self.widget.addItem(self.hLine, ignoreBounds=True)


  def mouseMoved(self, event):
    position = event
    if self.widget.sceneBoundingRect().contains(position):
        mousePoint = self.viewBox.mapSceneToView(position)
        self.vLine.setPos(mousePoint.x())
        self.hLine.setPos(mousePoint.y())


  def dropEvent(self, event):


    event.accept()
    data = event.mimeData()
    print(data,"dropped")
    print("dropped")
    if isinstance(self.parent, QtGui.QGraphicsScene):
      event.ignore()
      return

    if event.mimeData().urls():
      mods = event.keyboardModifiers()
      haveCtrl = mods & QtCore.Qt.CTRL or mods & QtCore.Qt.META
      haveShift = mods & QtCore.Qt.SHIFT

      if haveShift or haveCtrl:
        replace = False
      else:
        replace = True

      filePaths = [url.path() for url in event.mimeData().urls()]
      if filePaths:
        spectrumFormat = getSpectrumFileFormat(filePaths[0])
        print(filePaths)
        print(spectrumFormat)

        if spectrumFormat:
          event.acceptProposedAction()
          self.openSpectra(filePaths, replace=replace)
          return

        peakListFormat = getPeakListFileFormat(filePaths[0])
        if peakListFormat:
          event.acceptProposedAction()
          self.mainApp.openPeakList(filePaths[0])
          return

        else:
          event.ignore()

      else:
        event.ignore()

    else:
      event.ignore()


###For testing
#
# if __name__ == '__main__':
#
#   def testMain():
#     app = QtGui.QApplication(sys.argv)
#
#     w = QtGui.QWidget()
#     layout = QtGui.QGridLayout()
#     spectrumWidget=Spectrum1dPane()
#     widget=spectrumWidget.widget
#     layout.addWidget(widget)
#     w.setLayout(layout)
#     w.show()
#     sys.exit(app.exec_())
#
#   testMain()