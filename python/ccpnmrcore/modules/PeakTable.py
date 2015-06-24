"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
from ccpncore.gui.DockLabel import DockLabel
from ccpncore.gui.Font import Font
# from ccpncore.gui.Table import ObjectTable, Column
from ccpnmrcore.modules.GuiTableGenerator import GuiTableGenerator
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Label import Label
from pyqtgraph.dockarea import Dock
import pyqtgraph as pg
import math

from PyQt4 import QtGui, QtCore

UNITS = ['ppm', 'Hz', 'point']

class PeakListSimple(Dock):

  def __init__(self, parent=None, peakLists=None, name='Peak List', **kw):

    if not peakLists:
      peakLists = []
      
    # QtGui.QWidget.__init__(self, parent)
    Dock.__init__(self, name=name)

    self.label.hide()
    self.label = DockLabel(name, self)
    self.label.show()
    # self.initPanel()
    self.peakLists = peakLists
    # label = Label(self, 'Peak List:')
    # self.layout.addWidget(label, 0, 0)
    #
    # self.label.setFont(Font(size=12, bold=True))
    # self.peakListPulldown = PulldownList(self, grid=(0, 1))#,
    # #                                       # callback=self.changePeakList,)
    # #
    # #
    # label = Label(self, ' Position Unit:', grid=(0, 2))
    # #
    # self.posUnitPulldown = PulldownList(self, grid=(0, 3), texts=UNITS,)
    # #                                     # callback=self._updateWhenIdle,)

    columns = [('#', 'serial'),
               ('Height', lambda pk: self._getPeakHeight(pk)),
               ('Volume', lambda pk: self._getPeakVolume(pk)),
                ('Details', 'comment')
    ]
    self.peakTable = GuiTableGenerator(self, peakLists, callback=self.selectPeak, columns=columns)

    self.layout.addWidget(self.peakTable, 2, 0, 1, 4)

    # self.updateContents()
    # self.updatePeakLists()
    # if peakLists:
    #   self.changePeakList(peakLists[0])

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
      return peak

  # def _getColumns(self, numDim):
  #
  #   columns = []
  #   c = (Column('#', 'serial', tipText='Peak serial number'))
  #   columns.append(c)
  #
  #   for i in range(numDim):
  #     j = i + 1
  #     c = Column('Assign\nF%d' % j,
  #                lambda pk, dim=i:self._getPeakAnnotation(pk, dim),
  #                tipText='Resonance assignments of peak in dimension %d' % j)
  #     columns.append(c)
  #
  #   for i in range(numDim):
  #     j = i + 1
  #
  #     sampledDim = self.sampledDims.get(i)
  #     if sampledDim:
  #       text = 'Sampled\n%s' % sampledDim.conditionVaried
  #       tipText='Value of sampled plane'
  #       unit = sampledDim
  #
  #     else:
  #       text = 'Pos\nF%d' % j
  #       tipText='Peak position in dimension %d' % j
  #       unit = 'ppm'
  #
  #     c = Column(text,
  #                lambda pk, dim=i, unit=unit:self._getPeakPosition(pk, dim, unit),
  #                tipText=tipText)
  #     columns.append(c)


    # columns.extend([Column('Height', self._getPeakHeight,
    #                        tipText='Magnitude of spectrum intensity at peak center (interpolated), unless user edited'),
    #                 Column('Volume', self._getPeakVolume,
    #                        tipText='Integral of spectrum intensity around peak location, according to chosen volume method'),
    #                 Column('Details', 'comment',
    #                        tipText='Textual notes about the peak')])
    #
    # return columns

  def _getPeakPosition(self, peak, dim, unit='ppm'):

    # peakDim = peak.position[dim]

    if peak.position[dim] is None:
      value = "*NOT SET*"

    elif unit == 'ppm':
      value = peak.position[dim]

    elif unit == 'point':
      value = peak.pointPosition[dim]

    elif unit == 'Hz':
      value = peak.position[dim]*peak.sortedPeakDims()[dim].dataDimRef.expDimRef.sf

    else: # sampled
      value = unit.pointValues[int(peak.sortedPeakDims()[dim].position)-1]

    return value

  def _getPeakAnnotation(self, peak, dim):

    if len(peak.dimensionNmrAtoms[dim]) > 0:
      return peak.dimensionNmrAtoms[dim][0].pid.id

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
    texts = ['%s:%s:%s' % (peakList.spectrum.apiDataSource.experiment.name, peakList.spectrum.name, peakList.serial) for peakList in self.peakLists]
    self.peakListPulldown.setData(texts=texts, objects=self.peakLists)

  # def updateContents(self):
  #   peakList = self.peakList
  #   if peakList:
  #     columns = self._getColumns(peakList._parent.dimensionCount)
  #     self.peakTable.setObjectsAndColumns(peakList.peaks, columns)
  #def updateContents(self, spectrum):
    # if len(spectrum.peakLists) > 1:
    #   for peakList in spectrum.peakLists:
    #
    #
    #     columns = self._getColumns(peakList._wrappedData.dataSource.numDim)
    #     self.peakTable.setObjectsAndColumns(peakList._wrappedData.sortedPeaks(), columns)

  # def changePeakList(self, peakList):
  #
  #   if peakList is not self.peakList:
  #
  #     if self.peakList:
  #       numDim = self.peakList.spectrum.dimensionCount
  #     else:
  #       numDim = 2
  #
  #     self.sampledDims  = {}
  #
  #     if peakList:
  #       dataDims = peakList.spectrum.apiDataSource.sortedDataDims()
  #       for i, dataDim in enumerate(dataDims):
  #         if dataDim.className == 'SampledDataDim':
  #           self.sampledDims[i] = dataDim
  #
  #     self.peakList = peakList
  #     self.peak = None
  #     #self._updateWhenIdle()
  #     #self.updatePeakLists()
  #     self.updateContents()

      #for func in self.changePeakListCalls:
      #  func(peakList)

