
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList
from ccpnmrcore.modules.GuiTableGenerator import GuiTableGenerator
from PyQt4 import QtGui, QtCore
from ccpncore.gui.ScrollArea import ScrollArea


class PeakListSampleComponent(QtGui.QWidget):

  def __init__(self, parent=None, project=None, callback=None):

    QtGui.QWidget.__init__(self, parent)
    self.project = project
    self.peakLists = project.peakLists
    self.samples = project.samples
    dataPulldownSample = [sample.pid for sample in self.samples if len(sample.spectra) > 1]


    if not project.peakLists:
      peakLists = []

    ##### Set Sample pulldown #####
    labelSelectSample = Label(self, ' Select Sample:', grid=(0, 0), hAlign='r')
    self.samplePulldown = PulldownList(self, grid=(0, 1), callback=self.pulldownSample)
    self.samplePulldown.setData(dataPulldownSample)

    ##### Set Components PL  pulldown #####
    labelSelectComponent = Label(self, 'Select Component:')
    self.layout().addWidget(labelSelectComponent, 0, 2, QtCore.Qt.AlignRight)
    self.peakListPulldown = PulldownList(self, grid=(0, 3))

    #### layout for the component view
    self.scrollArea = ScrollArea(self)
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = QtGui.QWidget()
    self.scene = QtGui.QGraphicsScene(self)
    self.scrollContents = QtGui.QGraphicsView(self.scene, self)
    self.scrollContents.setInteractive(True)
    self.scrollContents.setGeometry(QtCore.QRect(2, 3, 380, 1000))
    self.horizontalLayout2 = QtGui.QHBoxLayout(self.scrollContents)
    self.scrollArea.setWidget(self.scrollContents)
    self.layout().addWidget(self.scrollArea, 3, 3, 3, 3)


  def pulldownSample(self, selection):

    for sample in self.project.samples:
      if sample.pid  == selection:
          pidPl = [peakList.pid for spectrum in sample.spectra for peakList in spectrum.peakLists]
          self.peakListPulldown.setData(pidPl)

          listofPLobjects = []    #this because the peakTable needs to have a list of objects on the selector(pulldown)
          for spectrum in sample.spectra:
            for peakListObject in spectrum.peakLists:
              listofPLobjects.append(peakListObject)

              ##### Set Peak List Table #######
              columns = [('#', 'serial'), ('Height', lambda pk: self._getPeakHeight(pk))]
              tipTexts=['Peak serial number', 'Magnitude of spectrum intensity at peak center (interpolated), unless user edited']
              self.peakTable = GuiTableGenerator(self, objectLists=listofPLobjects, callback=None, columns=columns,
                                      selector=self.peakListPulldown, tipTexts=tipTexts)
              self.layout().addWidget(self.peakTable, 3, 0, 6, 3)

  def _getPeakHeight(self, peak):
    if peak.height:
      return peak.height*peak.peakList.spectrum.scale