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
from ccpn import Peak

from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList

from application.core.modules.GuiTableGenerator import GuiTableGenerator
from application.core.popups.SelectObjectsPopup import SelectObjectsPopup


from PyQt4 import QtGui, QtCore

UNITS = ['ppm', 'Hz', 'point']

class PeakTable(CcpnDock):
  def __init__(self, project, selectedList=None):
    CcpnDock.__init__(self, name='Peak List')

    self.layout.addWidget(PeakListSimple(self, project, selectedList=selectedList))



class PeakListSimple(QtGui.QWidget, Base):

  def __init__(self, parent=None, project=None,  callback=None, selectedList=None, **kw):

    if not project.peakLists:
      peakLists = []
      
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    # self.label.hide()
    # self.label = DockLabel(name, self)
    # self.label.show()
    self.project = project

    self.peakLists = project.peakLists
    label = Label(self, 'Peak List:')
    self.layout().addWidget(label, 0, 0, QtCore.Qt.AlignRight)
    self.setContentsMargins(0, 4, 0, 4,)
    # self.label.setFont(Font(size=12, bold=True))
    self.peakListPulldown = PulldownList(self, grid=(0, 1))
    if callback is None:
      callback=self.selectPeak

    label = Label(self, ' Position Unit:', grid=(0, 2), hAlign='r')

    self.posUnitPulldown = PulldownList(self, grid=(0, 3), texts=UNITS,)

    self.subtractPeakListsButton = Button(self, text='Subtract PeakLists', grid=(0, 4),
                                          callback=self.subtractPeakLists)
    #                                     # callback=self._updateWhenIdle,)

    columns = [('#', 'serial'), ('Height', lambda pk: self.getPeakHeight(pk)),
               ('Volume', lambda pk: self.getPeakVolume(pk))]


    tipTexts=['Peak serial number', 'Magnitude of spectrum intensity at peak center (interpolated), unless user edited',
              'Integral of spectrum intensity around peak location, according to chosen volume method',
              'Textual notes about the peak']
    self.peakTable = GuiTableGenerator(self, objectLists=self.peakLists, callback=callback, columns=columns,
                                       selector=self.peakListPulldown, tipTexts=tipTexts)

    # self.updatePeakLists()
    # newLabel = Label(self, '', grid=(2, 0))
    # newLabel.setFixedHeight(8)
    self.layout().addWidget(self.peakTable, 3, 0, 1, 8)
    if selectedList is not None:
      self.peakListPulldown.setCurrentIndex(self.peakListPulldown.findText(selectedList.pid))
      # print(self.peakListPulldown.currentIndex(),self.peakListPulldown.currentIndex().text())

  def subtractPeakLists(self):
    """
    Subtracts a selected peak list from the peak list currently displayed in the peak table and
    produces a new peak list attached to the spectrum of the selected peak list.
    """

    peakList1 = self.project.getByPid(self.peakListPulldown.currentText())


    availablePeakLists = [peakList for peakList in peakList1.spectrum.peakLists
                         if peakList is not peakList1]

    selectPeakListPopup = SelectObjectsPopup(self, project=self.project, objects=availablePeakLists)
    selectPeakListPopup.exec_()
    for peakList in self.objects:
      peakList1.subtractPeakLists(self.project.getByPid(peakList))
    self.peakTable.updateSelectorContents()

  def _initPanel(self):
    """
    Instantiates the various settings required for the peak table to function.
    """
    # Overwrites superclass

    self.peakList = None
    self.peak = None
    self.sampledDims = {}
    self.changePeakListCalls = []
    self.selectPeakCalls = []
    self.selectPeaksCalls = []

  def selectPeak(self, peak:Peak, row:int, col:int):
    """
    Sets current.peak to selected peak.
    """
    if not peak:
      return
    else:
      self.project._appBase.current.peak = peak

  def getPeakVolume(self, peak:Peak):
    """
    Returns the volume of the specified peak.
    """
    if peak.volume:
      return '%7.2E' % float(peak.volume*peak.peakList.spectrum.scale)

  def getPeakHeight(self, peak:Peak):
    """
    Returns the height of the specified peak.
    """
    if peak.height:
      return '%7.2E' % float(peak.height*peak.peakList.spectrum.scale)




