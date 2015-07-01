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
from ccpnmrcore.modules.GuiTableGenerator import GuiTableGenerator
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Label import Label

from PyQt4 import QtGui, QtCore

UNITS = ['ppm', 'Hz', 'point']


class PeakListSimple(QtGui.QWidget, Base):

  def __init__(self, parent=None, peakLists=None, name='Peak List', **kw):

    if not peakLists:
      peakLists = []
      
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    # self.label.hide()
    # self.label = DockLabel(name, self)
    # self.label.show()
    self.peakLists = peakLists
    label = Label(self, 'Peak List:')
    self.layout().addWidget(label, 0, 0, QtCore.Qt.AlignRight)
    self.setContentsMargins(4, 4, 4, 4,)
    # self.label.setFont(Font(size=12, bold=True))
    self.peakListPulldown = PulldownList(self, grid=(0, 1))


    label = Label(self, ' Position Unit:', grid=(0, 2), hAlign='r')

    self.posUnitPulldown = PulldownList(self, grid=(0, 3), texts=UNITS,)
    #                                     # callback=self._updateWhenIdle,)

    columns = [('#', 'serial'), ('Height', lambda pk: self._getPeakHeight(pk)),
               ('Volume', lambda pk: self._getPeakVolume(pk)),
               ('Details', 'comment')]

    tipTexts=['Peak serial number', 'Magnitude of spectrum intensity at peak center (interpolated), unless user edited',
              'Integral of spectrum intensity around peak location, according to chosen volume method',
              'Textual notes about the peak']
    self.peakTable = GuiTableGenerator(self, peakLists, callback=self.selectPeak, columns=columns,
                                       selector=self.peakListPulldown, tipTexts=tipTexts)

    # self.updatePeakLists()
    # newLabel = Label(self, '', grid=(2, 0))
    # newLabel.setFixedHeight(8)
    self.layout().addWidget(self.peakTable, 3, 0, 1, 8)

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

  def _getPeakVolume(self, peak):

    if peak.volume:
      return peak.volume

  def _getPeakHeight(self, peak):

    if peak.height:
      return peak.height


  # def updatePeakLists(self):
  #
  #   texts = ['%s:%s:%s' % (peakList.spectrum.apiDataSource.experiment.name, peakList.spectrum.name, peakList.serial) for peakList in self.peakLists]
  #   self.peakListPulldown.setData(texts=texts, objects=self.peakLists)



