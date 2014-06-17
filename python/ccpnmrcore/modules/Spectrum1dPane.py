from PySide import QtGui
import pyqtgraph as pg
import sys
from ccpnmrcore.modules.spectrumPane.Spectrum1dItem import Spectrum1dItem
from ccpnmrcore.modules.SpectrumPane import SpectrumPane
from ccpncore.gui import ViewBox


class Spectrum1dPane(SpectrumPane):

  def __init__(self):

    pg.setConfigOptions(background='w')
    pg.setConfigOptions(foreground='k')
    self.viewBox = ViewBox.ViewBox()
    self.xAxis = pg.AxisItem(orientation='top')
    self.yAxis = pg.AxisItem(orientation='right')
    self.widget = pg.PlotWidget(
      viewBox=self.viewBox, enableMenu=False, axisItems={
        'bottom':self.xAxis, 'right': self.yAxis})

    self.viewBox.invertX()
    self.widget.plotItem.vb.state['background'] = None
    self.widget.plotItem.vb.updateBackground()
    self.createCrossHair()
    # connect cross hair (mouseMoved)
    self.widget.scene().sigMouseMoved.connect(self.mouseMoved)

    ## setup axes for display
    self.axes = self.widget.plotItem.axes
    self.axes['left']['item'].hide()
    self.axes['right']['item'].show()
    # orientation left to put text on left of axis and same for top
    self.axes['right']['item'].orientation = 'left'
    self.axes['bottom']['item'].orientation = 'top'


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


###For testing
if __name__ == '__main__':

  def testMain():
    app = QtGui.QApplication(sys.argv)
    w = QtGui.QWidget()
    layout = QtGui.QGridLayout()
    spectrumWidget=Spectrum1dPane()
    widget=spectrumWidget.widget
    layout.addWidget(widget)
    w.setLayout(layout)
    w.show()
    sys.exit(app.exec_())

  testMain()
