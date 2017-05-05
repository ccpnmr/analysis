"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:40 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui, QtCore
from ccpn.ui.gui.modules.GuiTableGenerator import GuiTableGenerator
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.modules.peakUtils import getPeakPosition, getPeakAnnotation, getPeakLinewidth
from ccpn.ui.gui.popups.SelectObjectsPopup import SelectObjectsPopup
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Frame import ScrollableFrame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Table import ObjectTable, Column
from ccpn.ui.gui.widgets.PulldownListsForObjects import PeakListPulldown

from ccpn.core.lib.Notifiers import Notifier
UNITS = ['ppm', 'Hz', 'point']

class PeakTable(CcpnModule):
  '''
  This class implements the module by wrapping a PeakListTable instance
  '''

  includeSettingsWidget = True
  maxSettingsState = 2
  settingsOnTop = True

  className = 'PeakListTableModule'

  def __init__(self, project, mainWindow, name='PeakList Table', selectedList=None):

    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    # Derive application, project, and current from mainWindow
    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current


    # mainWidget
    self.peakListTable = PeakListTableWidget(parent=self.mainWidget, setLayout=True,
                                             application=self.application, grid=(0, 0))

    # settingsWidget
    self._PLTSettingsWidget = PeakListSettingsWidget(parent=self.settingsWidget,table=self.peakListTable, grid=(0,0))


  def _closeModule(self):
    """Re-implementation of closeModule function from CcpnModule to unregister notification on current.peaks"""
    # TODO deregister notifiers for " self._selectOnTableCurrentPeaks, 'peaks' "
    self.close()


class PeakListSettingsWidget(ScrollableFrame):
  ''' class conteining all settings widgets for the module peakTable '''

  def __init__(self, table, parent=None, **kw):
    ScrollableFrame.__init__(self,parent, setLayout=True, **kw)
    # Base.__init__(self, **kw)

    self.table = table
    columns = self.table.columns
    for i, colum in enumerate(columns):
      CheckBox(self, text=colum.heading, grid=(1, i), callback=self.checkBoxCallBack, hAlign='l',checked=True)

  def checkBoxCallBack(self):
    checkBox = self.sender()
    name = checkBox.text()
    if checkBox.isChecked():
      self.table._showColumn(name)
    else:
      self.table._hideColumn(name)

class PeakListTableWidget(ObjectTable):





  columnDefs = []

  def createColumns(self, peakList):
    '''Add default columns  plus the ones according with peakList.spectrum dimension '''
    self.columnDefs = []

    if peakList is not None:

      serialTipText = 'Peak serial number'
      serial = ('#', 'serial', serialTipText, None)
      self.columnDefs.append(serial)

      numDim = peakList.spectrum.dimensionCount

      # Assign
      for i in range(numDim):
        j = i + 1
        assignTipTexts = 'NmrAtom assignments of peak in dimension %d' % j
        assign =  ('Assign F%d' % j, lambda pk, dim=i: getPeakAnnotation(pk, dim), assignTipTexts, None)
        self.columnDefs.append(assign)

      # Peak positions
      for i in range(numDim):
        j = i + 1
        positionTipText = 'Peak position in dimension %d' % j
        unit = UNITS[0] #self.posUnitPulldown.currentText()
        position = ('Pos F%d' % j, lambda pk, dim=i, unit=unit: getPeakPosition(pk, dim, unit), positionTipText, None)
        self.columnDefs.append(position)

      # linewidth TODO remove hardcoded Hz unit
      for i in range(numDim):
        j = i + 1
        linewidthTipTexts = 'Peak line width %d' % j

        linewidth = ('LW F%d (Hz)' % j, lambda pk, dim=i: getPeakLinewidth(pk, dim), linewidthTipTexts, None)
        self.columnDefs.append(linewidth)

      # height
      heightTipText = 'Magnitude of spectrum intensity at peak center (interpolated), unless user edited'
      height = ('Height', lambda pk: pk.height, heightTipText, None)
      self.columnDefs.append(height)

      # volume
      volumeTipText = 'Integral of spectrum intensity around peak location, according to chosen volume method'
      volume = ('Volume', lambda pk: pk.volume, volumeTipText, None)
      self.columnDefs.append(volume)

      # comment
      commentsTipText = 'Textual notes about the peak'
      comment = ('Comment', lambda pk: pk.comment, commentsTipText, lambda pk, value: self._setObjectDetails(pk, value))
      # setEditValue
      self.columnDefs.append(comment)

      self._setColumns()

  def _setColumns(self):
    '''set the columns on the table from the list of tuples "columnDefs"  '''
    columns = [Column(colName, func, tipText=tipText, setEditValue=editValue) for colName, func, tipText, editValue in self.columnDefs]
    self.setColumns(columns)

  def _setComment(self, peak, value):
    peak.comment = value



  def __init__(self, parent, application, **kwds):
    self._project = application.project
    self._current = application.current
    kwds['setLayout'] = True  ## Assure we have a layout with the widget
    self._widget = Widget(parent=parent, **kwds)

    # create the column objects

    columns = [Column(colName, func, tipText=tipText, setEditValue=editValue) for colName, func, tipText, editValue in self.columnDefs]

    # create the table; objects are added later via the displayTableForPeakList method
    ObjectTable.__init__(self, parent=self._widget, setLayout=True,
                         columns=columns, objects=[],
                         autoResize=True, multiSelect=True,
                         actionCallback=self._actionCallback, selectionCallback=self._selectionCallback,
                         grid=(1, 0), gridSpan=(1, 6))
    gridHPos = 0
    self.ncWidget = PeakListPulldown(parent=self._widget,
                                     project=self._project, default=0,  # first peakList in project (if present)
                                     grid=(0, gridHPos), gridSpan=(1, 1), minimumWidths=(0, 100),
                                     callback=self._selectionPulldownCallback
                                     )
    gridHPos+=1
    self.posUnitPulldownLabel = Label(parent=self._widget, text= ' Position Unit', grid=(0, gridHPos))
    gridHPos += 1
    self.posUnitPulldown = PulldownList(parent=self._widget, texts=UNITS, callback=None,
                                        grid=(0, gridHPos))
    self.posUnitPulldown.setDisabled(True) #TODO

    self._peakNotifier = None
    self._updateSilence = False  # flag to silence updating of the table

    if len(self._project.peakLists) > 0:
      self.displayTableForPeakList(self._project.peakLists[0])

    # register current notifier to select on the table the current peaks
    self._current.registerNotify(self._selectOnTableCurrentPeaks, 'peaks')


  def _hideColumn(self, name):
    self.hideColumn(self.getColumnInt(columnName=name))

  def _showColumn(self, name):
    self.showColumn(self.getColumnInt(columnName=name))


  def _selectionPulldownCallback(self, item):
    "Callback for selecting NmrChain"
    peakList = self._project.getByPid(item)
    if peakList is not None:
      self.displayTableForPeakList(peakList)
      self._selectOnTableCurrentPeaks(currentPeaks=self._current.peaks)

  def displayTableForPeakList(self, peakList):
    "Display the table for all peakLists"

    # update the columns table based on the spectrum dim
    self.createColumns(peakList)

    if self._peakNotifier is not None:
      # we have a new peak and hence need to unregister the previous notifier
      self._peakNotifier.unRegister()
    # register a notifier for this peakList
    self._peakNotifier = Notifier(peakList,
                                   [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME], 'Peak',
                                    self._updateCallback
                                  )

    self.ncWidget.select(peakList.pid)
    self._update(peakList)

  def setUpdateSilence(self, silence):
    "Silences/unsilences the update of the table until switched again"
    self._updateSilence = silence

  def _update(self, peakList):
    "Update the table "
    if not self._updateSilence:
      self.clearTable()
      self._silenceCallback = True
      self.setObjects(peakList.peaks)
      self._silenceCallback = False
      self.show()

  def _updateCallback(self, data):
    "callback for updating the table"
    peakList = data['theObject']
    if peakList is not None:
      self._update(peakList)

  def _actionCallback(self, peak, *args):
    ''' If current strip contains the double clicked peak will navigateToPositionInStrip '''
    from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip

    if self._current.strip is not None:
        navigateToPositionInStrip(strip = self._current.strip, positions=peak.position)
    else:
      self._project._logger.warn('Impossible to navigate to peak position. Set a current strip first')


  def _selectionCallback(self, peaks, *args):
    """
    set as current the selected peaks on the table
    """
    if peaks is None:
      self._current.clearPeaks()
    else:
      self._current.peaks = peaks

  def _selectOnTableCurrentPeaks(self, currentPeaks):
    ''' highlight current peaks on the opened peak table '''

    if len(currentPeaks)>0:
      self._highLightObjs(currentPeaks)
    else:
      self.clearSelection()

  def destroy(self):
    "Cleanup of self"
    if self._peakNotifier is not None:
      self._peakNotifier.unRegister()






class PeakListSimple(QtGui.QWidget, Base):

  def __init__(self, parent=None, selectedList=None, columnSettings=None, **kw):

      
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    self.setMinimumWidth(500)
    self.application = QtCore.QCoreApplication.instance()._ccpnApplication
    self.project = self.application.project
    self.columnSettings = columnSettings

    self.sampledDims = {}
    if not selectedList and self.project.peakLists:
      self.selectedList = self.project.peakLists[0]
    elif not selectedList:
      self.peakLists = []
    else:
      self.selectedList = selectedList
    self.peakLists = self.project.peakLists
    self.label = Label(self, 'Peak List')

    widget1 = QtGui.QWidget(self)
    l = QtGui.QGridLayout()
    widget1.setLayout(l)
    widget1.layout().addWidget(self.label, 0, 0, QtCore.Qt.AlignLeft)
    self.peakListPulldown = PulldownList(self)
    widget1.layout().addWidget(self.peakListPulldown, 0, 1)
    self.layout().addWidget(widget1, 0, 0)

    widget2 = QtGui.QWidget(self)
    l2 = QtGui.QGridLayout()
    widget2.setLayout(l2)
    label = Label(self, ' Position Unit')
    widget2.layout().addWidget(label, 0, 0, QtCore.Qt.AlignLeft)
    self.posUnitPulldown = PulldownList(self, texts=UNITS, callback=self._refreshTable)
    widget2.layout().addWidget(self.posUnitPulldown, 0, 1, QtCore.Qt.AlignLeft)
    self.layout().addWidget(widget2, 0, 1)

    self.subtractPeakListsButton = Button(self, text='Subtract \nPeakLists',
                                          callback=self._subtractPeakLists)

    self.deletePeakButton = Button(self, 'Delete \nSelected', callback=self._deleteSelectedPeaks)
    self.widget3 = QtGui.QWidget(self)
    l3 = QtGui.QGridLayout()
    self.widget3.setLayout(l3)
    self.widget3.layout().addWidget(self.subtractPeakListsButton, 0, 0)
    self.widget3.layout().addWidget(self.deletePeakButton, 0, 1)
    self.layout().addWidget(self.widget3, 0, 2)

    self.peakTable = GuiTableGenerator(self, objectLists=self.peakLists, actionCallback=self._actionCallback, selectionCallback=self._selectionCallback,
                                       getColumnsFunction=self.getExtraColumns, selector=self.peakListPulldown,
                                       multiSelect=True, unitPulldown=self.posUnitPulldown)

    self.layout().addWidget(self.peakTable, 1, 0, 1, 5)
    if selectedList is not None:
      self.peakListPulldown.setCurrentIndex(selectedList)

    self.__registerNotifiers()

    self.peakListPulldown.activated[str].connect(self.updateSelectionOnTable)




  def updateSelectionOnTable(self):

    self._selectOnTableCurrentPeaks(self.application.current.peaks)


  def getExtraColumns(self, peakList):

      columns = []

      if self.columnSettings['serial'].isChecked():
        columns.append(('#', 'serial'))

      if self.columnSettings['height'].isChecked():
        columns.append(('Height', lambda pk: pk.height))

      if self.columnSettings['volume'].isChecked():
        columns.append(('Volume', lambda pk: pk.volume))

      tipTexts=['Peak serial number',
              'Magnitude of spectrum intensity at peak center (interpolated), unless user edited',
              'Integral of spectrum intensity around peak location, according to chosen volume method',
              'Textual notes about the peak']
      k = 1
      numDim = peakList.spectrum.dimensionCount

      if self.columnSettings['assign'].isChecked():
        for i in range(numDim):
          j = i + 1
          c = ('Assign F%d' % j, lambda pk, dim=i:getPeakAnnotation(pk, dim))
          columns.insert(k, c)
          tipTexts.insert(k, 'NmrAtom assignments of peak in dimension %d' % j)
          k+=1


      if self.columnSettings['position'].isChecked():
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

      if self.columnSettings['linewidth'].isChecked():
        for i in range(numDim):
          j = i + 1
          c = ('LW F%d (Hz)' % j, lambda pk, dim=i:getPeakLinewidth(pk, dim))
          columns.insert(k, c)
          tipTexts.insert(k, 'NmrAtom assignments of peak in dimension %d' % j)
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
    self.application.current.registerNotify(self._selectOnTableCurrentPeaks, 'peaks')

  def _deregisterNotifiers(self):
    self.project.unRegisterNotifier('Peak', 'create', self._refreshPeakTable)
    self.project.unRegisterNotifier('Peak', 'modify', self._refreshPeakTable)
    self.project.unRegisterNotifier('Peak', 'rename', self._refreshPeakTable)
    self.project.unRegisterNotifier('Peak', 'delete', self._refreshPeakTable)
    self.project.unRegisterNotifier('PeakList', 'create', self._updatePeakLists)
    self.project.unRegisterNotifier('PeakList', 'modify', self._updatePeakLists)
    self.project.unRegisterNotifier('PeakList', 'rename', self._updatePeakLists)
    self.project.unRegisterNotifier('PeakList', 'delete', self._updatePeakLists)
    self.application.current.unRegisterNotify(self._selectOnTableCurrentPeaks, 'peaks')

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

  def _actionCallback(self, peak, *args):
    ''' If current strip contains the double clicked peak will navigateToPositionInStrip '''
    from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip

    if self.application.current.strip is not None:
        navigateToPositionInStrip(strip = self.application.current.strip, positions=peak.position)
    else:
      self.project._logger.warn('Impossible to navigate to peak position. Set a current strip first')


  def _selectionCallback(self, peaks, *args):
    """
    set as current the selected peaks on the table
    """

    if peaks is None:
      self.application.current.clearPeaks()
    else:
      self.application.current.peaks = peaks

    # if peaks is not None :
    #   self.application.current.peaks = peaks
    #   self._deselectNonCurrentPeaks()
    #   self._selectCurrentPeaks()
    #
    # if peaks is None:
    #   self.application.current.clearPeaks()
    #   self._deselectNonCurrentPeaks()

  #
  # def _selectCurrentPeaks(self):
  #   if len(self.application.current.peaks) >0:
  #     for peak in self.application.current.peaks:
  #       peak.isSelected = True

  # def _deselectNonCurrentPeaks(self):
  #   for peak in self.project.peaks:
  #     if peak not in self.application.current.peaks:
  #       peak.isSelected = False


  def _selectOnTableCurrentPeaks(self, currentPeaks):
    ''' highlight current peaks on the opened peak table '''

    if len(currentPeaks)>0:
      self.peakTable.table._highLightObjs(currentPeaks)
    else:
      self.peakTable.table.clearSelection()


  def _refreshTable(self, item=None):
    # TODO: filter calls to only update if changes to the currently displayed peaklist
    self.peakTable.updateTable()


  def _refreshPeakTable(self, peak, dummy=None):
    # Dummy argument needed as the function is called for rename notifiers
    self.peakTable.updateTable()



