"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
from ccpn.core.Peak import Peak

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Module import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList

from ccpn.ui.gui.DropBase import DropBase
from ccpn.ui.gui.modules.GuiTableGenerator import GuiTableGenerator
from ccpn.ui.gui.modules.peakUtils import getPeakPosition, getPeakAnnotation

from ccpn.ui.gui.popups.SelectObjectsPopup import SelectObjectsPopup


from PyQt4 import QtGui, QtCore

UNITS = ['ppm', 'Hz', 'point']

class PeakTable(CcpnModule):
  def __init__(self, project, selectedList=None):
    CcpnModule.__init__(self, name='Peak List')

    if not project.peakLists:
      project._logger.warn('Project has no peaklists. Peak table cannot be displayed')
      return

    self.peakList = PeakListSimple(self, project, selectedList=selectedList)
    self.layout.addWidget(self.peakList)
    self.current = project._appBase.current
    # self.current.registerNotify(self.peakList._selectPeakInTable, 'peak')
    self.closeModule = self._closeModule
    if self.current.strip:
      peakList = self.current.strip.spectrumViews[0].spectrum.peakLists[0]
      self.peakList.peakListPulldown.setCurrentIndex(self.peakList.peakListPulldown.findText(peakList.pid))

  def _closeModule(self):
    """
    Re-implementation of closeModule function from CcpnModule to unregister notification on current.peaks
    """
    self.current.unRegisterNotify(self.peakList._selectPeakInTable, 'peak')
    self.close()



class PeakListSimple(QtGui.QWidget, DropBase, Base):

  def __init__(self, parent=None, project=None,  callback=None, selectedList=None, **kw):

      
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    # self.label.hide()
    # self.label = DockLabel(name, self)
    # self.label.show()
    self.project = project
    self.sampledDims = {}
    if not selectedList and project.peakLists:
      self.selectedList = self.project.peakLists[0]
    elif not selectedList:
      self.peakLists = []
    else:
      self.selectedList = selectedList
    self.peakLists = project.peakLists
    self.label = Label(self, 'Peak List:')

    widget1 = QtGui.QWidget(self)
    l = QtGui.QGridLayout()
    widget1.setLayout(l)
    widget1.layout().addWidget(self.label, 0, 0, QtCore.Qt.AlignLeft)
    self.peakListPulldown = PulldownList(self)
    widget1.layout().addWidget(self.peakListPulldown, 0, 1)
    self.layout().addWidget(widget1, 0, 0)
    if callback is None:
      callback=self._selectPeak

    widget2 = QtGui.QWidget(self)
    l2 = QtGui.QGridLayout()
    widget2.setLayout(l2)
    label = Label(self, ' Position Unit:')
    widget2.layout().addWidget(label, 0, 0, QtCore.Qt.AlignLeft)
    self.posUnitPulldown = PulldownList(self, texts=UNITS, callback=self._refreshTable)
    widget2.layout().addWidget(self.posUnitPulldown, 0, 1, QtCore.Qt.AlignLeft)
    self.layout().addWidget(widget2, 0, 1)

    self.subtractPeakListsButton = Button(self, text='Subtract PeakLists',
                                          callback=self._subtractPeakLists)

    self.deletePeakButton = Button(self, 'Delete Selected', callback=self._deleteSelectedPeaks)
    self.widget3 = QtGui.QWidget(self)
    l3 = QtGui.QGridLayout()
    self.widget3.setLayout(l3)
    self.widget3.layout().addWidget(self.subtractPeakListsButton, 0, 0)
    self.widget3.layout().addWidget(self.deletePeakButton, 0, 1)
    self.layout().addWidget(self.widget3, 0, 6, 1, 2)
    #
    # columns = [('#', 'serial'), ('Height', lambda pk: self._getPeakHeight(pk)),
    #            ('Volume', lambda pk: self._getPeakVolume(pk))]
    #
    # tipTexts=['Peak serial number',
    #           'Magnitude of spectrum intensity at peak center (interpolated), unless user edited',
    #           'Integral of spectrum intensity around peak location, according to chosen volume method',
    #           'Textual notes about the peak']

    self.peakTable = GuiTableGenerator(self, objectLists=self.peakLists, actionCallback=callback, selectionCallback=self._selectPeak,
                                       getColumnsFunction=self.getExtraColumns, selector=self.peakListPulldown,
                                       multiSelect=True, unitPulldown=self.posUnitPulldown)

    self.layout().addWidget(self.peakTable, 1, 0, 1, 8)
    if selectedList is not None:
      self.peakListPulldown.setCurrentIndex(selectedList)

    self.__registerNotifiers()

  def getExtraColumns(self, peakList):

      columns = [('#', 'serial'), ('Height', lambda pk: self._getPeakHeight(pk)),
               ('Volume', lambda pk: self._getPeakVolume(pk))]

      tipTexts=['Peak serial number',
              'Magnitude of spectrum intensity at peak center (interpolated), unless user edited',
              'Integral of spectrum intensity around peak location, according to chosen volume method',
              'Textual notes about the peak']
      k = 1
      numDim = peakList.spectrum.dimensionCount
      for i in range(numDim):
        j = i + 1
        c = ('Assign F%d' % j, lambda pk, dim=i:getPeakAnnotation(pk, dim))
        columns.insert(k, c)
        tipTexts.insert(k, 'NmrAtom assignments of peak in dimension %d' % j)
        k+=1
      for i in range(numDim):
        j = i + 1

        sampledDim = self.sampledDims.get(i)
        if sampledDim:
          text = 'Sampled\n%s' % sampledDim.conditionVaried
          tipText='Value of sampled plane'
          unit = sampledDim

        else:
          text = 'Pos F%d' % j
          tipText='Peak position in dimension %d' % j
          unit = self.posUnitPulldown.currentText()
        c = (text, lambda pk, dim=i, unit=unit:getPeakPosition(pk, dim, unit))
        columns.insert(k, c)
        tipTexts.insert(k, tipText)
        k+=1

      return columns, tipTexts


  def __registerNotifiers(self):

    self.project.registerNotifier('Peak', 'create', self._refreshPeakTable, onceOnly=True)
    self.project.registerNotifier('Peak', 'modify', self._refreshPeakTable, onceOnly=True)
    self.project.registerNotifier('Peak', 'rename', self._refreshPeakTable, onceOnly=True)
    self.project.registerNotifier('Peak', 'delete', self._refreshPeakTable, onceOnly=True)
    self.project.registerNotifier('PeakList', 'create', self._updatePeakLists, onceOnly=True)
    self.project.registerNotifier('PeakList', 'modify', self._updatePeakLists, onceOnly=True)
    self.project.registerNotifier('PeakList', 'rename', self._updatePeakLists, onceOnly=True)
    self.project.registerNotifier('PeakList', 'delete', self._updatePeakLists, onceOnly=True)


  def __del__(self):
    self.project.unRegisterNotifier('Peak', 'create', self._refreshPeakTable)
    self.project.unRegisterNotifier('Peak', 'modify', self._refreshPeakTable)
    self.project.unRegisterNotifier('Peak', 'rename', self._refreshPeakTable)
    self.project.unRegisterNotifier('Peak', 'delete', self._refreshPeakTable)
    self.project.unRegisterNotifier('PeakList', 'create', self._updatePeakLists)
    self.project.unRegisterNotifier('PeakList', 'modify', self._updatePeakLists)
    self.project.unRegisterNotifier('PeakList', 'rename', self._updatePeakLists)
    self.project.unRegisterNotifier('PeakList', 'delete', self._updatePeakLists)


  def _updatePeakLists(self, value):
    self.peakTable.objectLists = self.project.peakLists
    self.peakTable._updateSelectorContents()


  def _subtractPeakLists(self):
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
      peakList1._subtractPeakLists(self.project.getByPid(peakList))
    self.peakTable._updateSelectorContents()

  def _deleteSelectedPeaks(self):

    for peakObject in self.peakTable.table.getSelectedObjects():
      peakObject.delete()
    self._refreshTable()


  def _selectPeak(self, peak:Peak, row:int, col:int):
    """
    Sets current.peak to selected peak.
    """
    if not peak:
      return
    else:
    #   self.project._appBase.current.unRegisterNotify(self._selectPeakInTable, 'peaks')
      self.project._appBase.current.peak = peak
      # self.project._appBase.current.registerNotify(self._selectPeakInTable, 'peaks')

  def _getPeakVolume(self, peak:Peak):
    """
    Returns the volume of the specified peak.
    """
    if peak.volume:
      return '%7.2E' % float(peak.volume*peak.peakList.spectrum.scale)

  def _selectPeakInTable(self, peaks=None):
    peakList = self.project.getByPid(self.peakListPulldown.currentText())
    if peaks and peaks[-1] in peakList.peaks:
      self.peakTable.table.selectObject(peaks[-1])

  def _getPeakHeight(self, peak:Peak):
    """
    Returns the height of the specified peak.
    """
    if peak.height:
      return '%7.2E' % float(peak.height*peak.peakList.spectrum.scale)


  def _refreshTable(self, item=None):
    self.peakTable.updateTable()


  def _refreshPeakTable(self, peak):
    self.peakTable.updateTable()



