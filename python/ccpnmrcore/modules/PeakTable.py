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
from ccpncore.gui.Button import Button
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList

from ccpnmrcore.modules.GuiTableGenerator import GuiTableGenerator
from ccpnmrcore.popups.SelectObjectsPopup import SelectObjectsPopup


from PyQt4 import QtGui, QtCore

UNITS = ['ppm', 'Hz', 'point']

class PeakTable(CcpnDock):
  def __init__(self, project):
    CcpnDock.__init__(self, name='Peak List')

    self.layout.addWidget(PeakListSimple(project, parent=self))



class PeakListSimple(QtGui.QWidget, Base):

  def __init__(self, project, parent=None, callback=None, **kw):

    if not project.peakLists:
      peakLists = []
      
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    # self.label.hide()
    # self.label = DockLabel(name, self)
    # self.label.show()
    self.project = project
    self.peakLists = project.peakLists
    label = Label(self, 'Peak List:', grid=(1, 0))
    # self.label.setFont(Font(size=12, bold=True))
    self.peakListPulldown = PulldownList(self, grid=(1, 1))
    if callback is None:
      callback=self.selectPeak

    label = Label(self, ' Position Unit:', grid=(1, 2), hAlign='r')

    self.posUnitPulldown = PulldownList(self, grid=(1, 3), texts=UNITS,)

    self.subtractPeakListsButton = Button(self, text='Subtract PeakLists', grid=(1, 5),
                                          callback=self.subtractPeakLists)
    #                                     # callback=self._updateWhenIdle,)

    columns = [('#', 'serial'), ('Height', lambda pk: self._getPeakHeight(pk)),
               ('Volume', lambda pk: self._getPeakVolume(pk)),
               ('Details', 'comment')]

    tipTexts=['Peak serial number', 'Magnitude of spectrum intensity at peak center (interpolated), unless user edited',
              'Integral of spectrum intensity around peak location, according to chosen volume method',
              'Textual notes about the peak']
    self.peakTable = GuiTableGenerator(self, self.peakLists, callback=callback, columns=columns,
                                       selector=self.peakListPulldown, tipTexts=tipTexts)

    # self.updatePeakLists()
    # newLabel = Label(self, '', grid=(2, 0))
    # newLabel.setFixedHeight(8)
    self.layout().addWidget(self.peakTable, 3, 0, 1, 8)

  def subtractPeakLists(self):
    peakList1 = self.project.getById(self.peakListPulldown.currentText())


    availablePeakLists = [peakList for peakList in peakList1.spectrum.peakLists
                         if peakList is not peakList1]

    selectPeakListPopup = SelectObjectsPopup(self, project=self.project, objects=availablePeakLists)
    selectPeakListPopup.exec_()
    print(self.objects)
    for peakList in self.objects:
      peakList1.subtractPeakLists(self.project.getById(peakList))
    self.peakTable.updateSelectorContents()

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
      return peak.volume*peak.peakList.spectrum.scale

  def _getPeakHeight(self, peak):

    if peak.height:
      return peak.height*peak.peakList.spectrum.scale


  # def updatePeakLists(self):
  #
  #   texts = ['%s:%s:%s' % (peakList.spectrum.apiDataSource.experiment.name, peakList.spectrum.name, peakList.serial) for peakList in self.peakLists]
  #   self.peakListPulldown.setData(texts=texts, objects=self.peakLists)



