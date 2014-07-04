from PySide import QtGui, QtCore
import pyqtgraph as pg
from ccpnmrcore.modules.spectrumPane.Spectrum1dItem import Spectrum1dItem
# from ccpn.lib.Spectrum import getSpectrumFileFormat
from ccpn import openProject
from ccpncore.util import Io as Io
from ccpnmrcore.modules.SpectrumPane import SpectrumPane
from ccpncore.gui import ViewBox
import random


class Spectrum1dPane(SpectrumPane):

  def __init__(self):
    SpectrumPane.__init__(self)
    pg.setConfigOptions(background='w')
    pg.setConfigOptions(foreground='k')
    self.viewBox = ViewBox.ViewBox()
    self.xAxis = pg.AxisItem(orientation='top')
    self.yAxis = pg.AxisItem(orientation='right')
    self.widget = pg.PlotWidget( viewBox = self.viewBox,
      enableMenu=False, axisItems={
        'bottom':self.xAxis, 'right': self.yAxis})
    self.widget.plotItem.setAcceptDrops(True)
    self.widget.dragEnterEvent = self.dragEnterEvent
    self.widget.dropEvent = self.dropEvent
    self.viewBox.invertX()
    self.crossHair = self.createCrossHair()
    # connect cross hair (mouseMoved)
    self.widget.scene().sigMouseMoved.connect(self.mouseMoved)
    self.widget.setAcceptDrops(True)
    self.widget.dropEvent = self.dropEvent
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

  def dropEvent(self,event):
    event.accept()
    data = event.mimeData()
    print(data,"dropped")
    print("dropped")
    if isinstance(self.parent, QtGui.QGraphicsScene):
      event.ignore()
      return

    if event.mimeData().urls():


      filePaths = [url.path() for url in event.mimeData().urls()]

      if len(filePaths) == 1:
          global current
          currentProjectDir = filePaths[0]

          current = Io.loadProject(currentProjectDir)
          # self.statusBar().showMessage(msg)
          # self.pythonConsole.write("openProject('"+currentProjectDir+"')\n")
          msg  = (current.name)+' opened'
          print(msg)
          print(current)
          for experiment in current.currentNmrProject.findAllExperiments():
            print(experiment)
            # experimentItem = QtGui.QTreeWidgetItem(self.spectrumItem)
            # experimentItem.setText(0,str(experiment.name))
            # experimentItem.setData(0, QtCore.Qt.UserRole, experiment)
            # experimentItem.data(0, QtCore.Qt.UserRole).toPyObject()
            dataSource = experiment.findFirstDataSource()
            if dataSource is not None:
              if dataSource.numDim == 1:
                data = Spectrum1dItem(self,dataSource).spectralData
                # print(data)
                self.widget.plot(data, pen={'color':(random.randint(0,255),random.randint(0,255),random.randint(0,255))})
              # for peakList in dataSource.findAllPeakLists():
              #   peakListItem = QtGui.QTreeWidgetItem(self.peaksItem)
              #   peakListItem.setText(0, str(peakList))
                # peakListItem.setData(0, QtCore.Qt.UserRole + 1, peakList)
                # peakListItem.setData(1, QtCore.Qt.DisplayRole, str(peakList))
          # self.statusBar().showMessage(msg)
          # self.pythonConsole.write("openProject('"+currentProjectDir.name+"')\n")
          # list1 = self.spectrumItem.takeChildren()
          # for item in list1:
          #   print((item.data()))

      else:
         pass

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