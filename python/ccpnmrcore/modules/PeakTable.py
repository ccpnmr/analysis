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
from ccpncore.gui.Base import Base
from ccpncore.gui.Table import ObjectTable, Column
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Label import Label
from pyqtgraph.dockarea import Dock
import pyqtgraph as pg
import math

from PySide import QtGui, QtCore

UNITS = ['ppm', 'Hz', 'point']

#class PeakListSimple(Dock):
class PeakListSimple(Dock):

  def __init__(self, parent=None, peakLists=None, name='Peak List', referenceSpectrumDisplay=None, **kw):

    if not peakLists:
      peakLists = []
      
    # QtGui.QWidget.__init__(self, parent)
    Dock.__init__(self, name=name)
    # Base.__init__(self, **kw)

    self.initPanel()
    self.peakLists = peakLists
    self.referenceSpectrumDisplay = referenceSpectrumDisplay
    #self.initPanel()
    label = Label(self, 'Peak List:', grid=(0, 0))
    self.peakListPulldown = PulldownList(self, grid=(0, 1),
                                          callback=self.changePeakList,)

    label = Label(self, ' Position Unit:', grid=(0, 2))
    self.posUnitPulldown = PulldownList(self, grid=(0, 3), texts=UNITS,)
                                        # callback=self._updateWhenIdle,)

    self.peakTable = ObjectTable(self, self._getColumns(2), [],
                                 callback=self.selectPeak, grid=(1, 0),
                                 gridSpan=(1, 5))

    # self.layout().setColumnStretch(4, 1)
    self.updateContents()
    self.updatePeakLists()
    if peakLists:
      self.changePeakList(peakLists[0])

  def initPanel(self):
    # Overwrites superclass

    self.peakList = None
    self.peak = None
    self.sampledDims = {}
    self.changePeakListCalls = []
    self.selectPeakCalls = []
    self.selectPeaksCalls = []

  def selectPeak(self, peak, row, col):
    if not peak:
      return
    else:

      position1 = self._getPeakPosition(peak, 1)
      position2 = self._getPeakPosition(peak, 0)
      self.referenceSpectrumDisplay.strips[0].changeZPlane(position=position1)
      peakList = self.referenceSpectrumDisplay.spectrumViews[0].spectrum.peakLists[0]
      for peak in peakList.peaks:
        if abs(peak.position[2] - position1) < 0.05 and abs(peak.position[0] - position2) < 0.02:
          print(peak.position)

      # self.referenceSpectrumDisplay.strips[0].addLine(position)



  def _getColumns(self, numDim):

    columns = []
    c = (Column('#', 'serial', tipText='Peak serial number'))
    columns.append(c)

    for i in range(numDim):
      j = i + 1
      c = Column('Assign\nF%d' % j,
                 lambda pk, dim=i:self._getPeakAnnotation(pk, dim),
                 tipText='Resonance assignments of peak in dimension %d' % j)
      columns.append(c)

    for i in range(numDim):
      j = i + 1

      sampledDim = self.sampledDims.get(i)
      if sampledDim:
        text = 'Sampled\n%s' % sampledDim.conditionVaried
        tipText='Value of sampled plane'
        unit = sampledDim

      else:
        text = 'Pos\nF%d' % j
        tipText='Peak position in dimension %d' % j
        unit = 'ppm'

      c = Column(text,
                 lambda pk, dim=i, unit=unit:self._getPeakPosition(pk, dim, unit),
                 tipText=tipText)
      columns.append(c)


    columns.extend([Column('Height', self._getPeakHeight,
                           tipText='Magnitude of spectrum intensity at peak center (interpolated), unless user edited'),
                    Column('Volume', self._getPeakVolume,
                           tipText='Integral of spectrum intensity around peak location, according to chosen volume method'),
                    Column('Details', 'details',
                           tipText='Textual notes about the peak')])

    return columns

  def _getPeakPosition(self, peak, dim, unit='ppm'):

    peakDim = peak.sortedPeakDims()[dim]

    if peakDim.position is None:
      value = "*NOT SET*"

    elif unit == 'ppm':
      value = peakDim.value

    elif unit == 'point':
      value = peakDim.dataDimRef.valueToPoint(peakDim.value)

    elif unit == 'Hz':
      value = peakDim.value*peakDim.dataDimRef.expDimRef.sf

    else: # sampled
      value = unit.pointValues[int(peakDim.position)-1]

    return value

  def _getPeakAnnotation(self, peak, dim):

    return peak.annotation

  def _getPeakVolume(self, peak):

    if peak.volume:
      return peak.volume

  def _getPeakHeight(self, peak):

    if peak.height:
      return peak.height


  def updatePeakLists(self):

    #self._updatePulldownList(self.peakListPulldown, self.peakLists,
    #                         self.changePeakList, self.peakList,
    #                         self._getPeakListName)
    texts = ['%s:%s:%s' % (peakList._parent.apiDataSource.experiment.name, peakList._parent.apiDataSource.name, peakList.serial) for peakList in self.peakLists]
    self.peakListPulldown.setData(texts=texts, objects=self.peakLists)

  def updateContents(self):
    peakList = self.peakList
    if peakList:
      columns = self._getColumns(peakList._parent.apiDataSource.numDim)
      self.peakTable.setObjectsAndColumns(peakList.apiPeakList.sortedPeaks(), columns)
  #def updateContents(self, spectrum):
    # if len(spectrum.peakLists) > 1:
    #   for peakList in spectrum.peakLists:
    # 
    # 
    #     columns = self._getColumns(peakList._wrappedData.dataSource.numDim)
    #     self.peakTable.setObjectsAndColumns(peakList._wrappedData.sortedPeaks(), columns)

  def changePeakList(self, peakList):

    if peakList is not self.peakList:

      if self.peakList:
        numDim = self.peakList._parent.apiDataSource.numDim
      else:
        numDim = 2

      self.sampledDims  = {}

      if peakList:
        dataDims = peakList._parent.apiDataSource.sortedDataDims()
        for i, dataDim in enumerate(dataDims):
          if dataDim.className == 'SampledDataDim':
            self.sampledDims[i] = dataDim

      self.peakList = peakList
      self.peak = None
      #self._updateWhenIdle()
      #self.updatePeakLists()
      self.updateContents()

      #for func in self.changePeakListCalls:
      #  func(peakList)

if __name__ == '__main__':

  import sys
  
  from ccpncore.gui.Application import TestApplication
  from ccpncore.util.Io import loadProject

  peakLists = []
  if len(sys.argv) == 2:
    projectPath = sys.argv[1]
    project = loadProject(projectPath)
    nmrProject = project.findFirstNmrProject()
    for experiment in nmrProject.sortedExperiments():
      for dataSource in experiment.sortedDataSources():
        peakLists.extend(dataSource.sortedPeakLists())
    
  app = TestApplication()
  peakTable = PeakListSimple(peakLists=peakLists)
  w = QtGui.QWidget()
  layout = QtGui.QGridLayout()
  layout.addWidget(peakTable)
  w.setLayout(layout)
  w.show()
  w.raise_()
  app.start()



