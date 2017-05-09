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


from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.modules.peakUtils import getPeakPosition, getPeakAnnotation, getPeakLinewidth
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Table import ObjectTable, Column , ColumnViewSettings,  ObjectTableFilter
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

  def __init__(self, mainWindow, name='PeakList Table'):

    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    # Derive application, project, and current from mainWindow
    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = self.mainWindow.project
    self.current = mainWindow.application.current


    # mainWidget
    self.peakListTable = PeakListTableWidget(parent=self.mainWidget, moduleParent=self, setLayout=True,
                                             application=self.application, grid=(0, 0))

    # settingsWidget
    self.displayColumnWidget = ColumnViewSettings(parent=self.settingsWidget, table=self.peakListTable, grid=(0, 0))
    self.searchWidget = ObjectTableFilter(parent=self.settingsWidget, table=self.peakListTable, grid=(1, 0))


  def _getPeakTable(self):
    " CCPN-INTERNAL: used to get peakListTable"
    return self.peakListTable


  def _getDisplayColumnWidget(self):
    " CCPN-INTERNAL: used to get displayColumnWidget"
    return self.displayColumnWidget

  def _getSearchWidget(self):
    " CCPN-INTERNAL: used to get searchWidget"
    return self.searchWidget

  def _closeModule(self):
    """Re-implementation of closeModule function from CcpnModule to unregister notification """
    self.peakListTable.destroy()
    self.close()


class PeakListTableWidget(ObjectTable):

  positionsUnit = UNITS[0] #default, updated by a pulldownList


  def __init__(self, parent, moduleParent, application, **kwds):
    self._project = application.project
    self._current = application.current
    self.moduleParent = moduleParent
    self.settingWidgets = None
    self._selectedPeakList = None

    kwds['setLayout'] = True  ## Assure we have a layout with the widget
    self._widget = Widget(parent=parent, **kwds)

    # create the table; objects are added later via the displayTableForPeakList method
    ObjectTable.__init__(self, parent=self._widget, setLayout=True, columns=[], objects=[], autoResize=True, multiSelect=True,
                         actionCallback=self._actionCallback, selectionCallback=self._selectionCallback, grid=(1, 0), gridSpan=(1, 6))
    gridHPos = 0
    self.pLwidget = PeakListPulldown(parent=self._widget,
                                     project=self._project, default=0,  # first peakList in project (if present)
                                     grid=(0, gridHPos), gridSpan=(1, 1), minimumWidths=(0, 100),
                                     callback=self._pulldownPLcallback
                                     )
    gridHPos+=1
    self.posUnitPulldownLabel = Label(parent=self._widget, text= ' Position Unit', grid=(0, gridHPos))
    gridHPos += 1
    self.posUnitPulldown = PulldownList(parent=self._widget, texts=UNITS, callback=self.updateUnits,
                                        grid=(0, gridHPos))



    self._selectOnTableCurrentPeaksNotifier = Notifier(self._current,[Notifier.CURRENT],
                                                       targetName='peaks',
                                                       callback=self._selectOnTableCurrentPeaksNotifierCallback)

    self._spectrumDeleteNotifier = Notifier(self._project,
                                            [Notifier.DELETE], 'Spectrum',
                                            self._deleteCallback
                                            )
    self._peakListDeleteNotifier =  Notifier(self._project,
                                             [Notifier.DELETE], 'PeakList',
                                             self._deleteCallback
                                             )

    self._displayTable()




  def _getTableColumns(self, peakList):
    '''Add default columns  plus the ones according with peakList.spectrum dimension
     format of column = ( Header Name, value, tipText, editOption) 
     editOption allows the user to modify the value content by doubleclick
     '''

    print('Getting columns ')
    columnDefs = []

    # Serial column
    columnDefs.append(('#', 'serial', 'Peak serial number', None))

    # Assignment column
    for i in range(peakList.spectrum.dimensionCount):
      assignTipText = 'NmrAtom assignments of peak in dimension %s' % str(i + 1)
      columnDefs.append(
        ('Assign F%s' % str(i + 1), lambda pk, dim=i: getPeakAnnotation(pk, dim), assignTipText, None))

    # Peak positions column
    for i in range(peakList.spectrum.dimensionCount):
      positionTipText = 'Peak position in dimension %s' % str(i + 1)
      columnDefs.append(('Pos F%s' % str(i + 1),
                         lambda pk, dim=i, unit=PeakListTableWidget.positionsUnit: getPeakPosition(pk, dim, unit),
                         positionTipText, None))

    # linewidth column TODO remove hardcoded Hz unit
    for i in range(peakList.spectrum.dimensionCount):
      linewidthTipTexts = 'Peak line width %s' % str(i + 1)
      columnDefs.append(
        ('LW F%s (Hz)' % str(i + 1), lambda pk, dim=i: getPeakLinewidth(pk, dim), linewidthTipTexts, None))

    # height column
    heightTipText = 'Magnitude of spectrum intensity at peak center (interpolated), unless user edited'
    columnDefs.append(('Height', lambda pk: pk.height, heightTipText, None))

    # volume column
    volumeTipText = 'Integral of spectrum intensity around peak location, according to chosen volume method'
    columnDefs.append(('Volume', lambda pk: pk.volume, volumeTipText, None))

    # comment column
    commentsTipText = 'Textual notes about the peak'
    columnDefs.append(('Comment', lambda pk: PeakListTableWidget._getCommentText(pk), commentsTipText,
                       lambda pk, value: PeakListTableWidget._setComment(pk, value)))

    return [Column(colName, func, tipText=tipText, setEditValue=editValue) for colName, func, tipText, editValue in
            columnDefs]

  def updateUnits(self, unit):
    #update the table with new units
    self._setPositionUnit(unit)
    self._updateAllModule()


  def _pulldownPLcallback(self, data):

    print('_pulldownPLcallback')
    self._updateAllModule()



  def _updateAllModule(self, *kw):
    self._displayTable()
    self._updateSettingsWidgets()

    if self._selectedPeakList is not None:
      self._peakNotifier = Notifier(self._selectedPeakList,
                                              [Notifier.DELETE], 'Peak',
                                              self._peakNotifierCallback
                                              )

  def _peakNotifierCallback(self, data):
    if data['trigger'] == 'delete':
      print('deleting Peak ')
      self._updateAllModule()


  def _deleteCallback(self, *kw):
    print('$$$$' * 1000)
    print('Deleting Spectrum')

    if self._selectedPeakList is not None:
      self.pLwidget.select(self._selectedPeakList.pid)

    self._updateAllModule()


  def _displayTable(self):
    print('@@@@'*1000)
    print('_displayTable')

    self._silenceCallback = True
    self.setObjectsAndColumns(objects=[], columns=[])
    self._selectedPeakList = self._project.getByPid(self.pLwidget.getText())
    if self._selectedPeakList is not None:
      peaks = [peak for peak in self._selectedPeakList.peaks if not peak._wrappedData.isDeleted]
      deletedPeaks = [peak for peak in self._selectedPeakList.peaks if  peak._wrappedData.isDeleted]
      print('deletedPeaks', deletedPeaks)

      self.setObjectsAndColumns(objects=peaks, columns=self._getTableColumns(self._selectedPeakList))
      self._selectOnTableCurrentPeaks(self._current.peaks)

    else:
      self.setObjects([])

    print('_displayTable done')


  def _updateSettingsWidgets(self):
    ''' update settings Widgets according with the new displayed table '''
    displayColumnWidget = self.moduleParent._getDisplayColumnWidget()
    displayColumnWidget.updateWidgets(self)
    searchWidget = self.moduleParent._getSearchWidget()
    searchWidget.updateWidgets(self)

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

  def _selectOnTableCurrentPeaksNotifierCallback(self, data):
    currentPeaks = data['value']
    self._selectOnTableCurrentPeaks(currentPeaks)

  def _selectOnTableCurrentPeaks(self, currentPeaks):
    ''' highlight current peaks on the opened peak table '''

    if len(currentPeaks)>0:
      self._highLightObjs(currentPeaks)
    else:
      self.clearSelection()

  def _setPositionUnit(self, value):
    if value in UNITS:
      PeakListTableWidget.positionsUnit = value

  @staticmethod
  def _getCommentText(peak):
    if peak.comment == '' or not peak.comment:
      return ' '
    else:
      return peak.comment

  @staticmethod
  def _setComment(peak, value):
    peak.comment = value

  @property
  def _selectedPeakList(self):
    return self.__selectedPeakList

  @_selectedPeakList.setter
  def _selectedPeakList(self, value):
    self.__selectedPeakList = value

  def destroy(self):
    "Cleanup of self"
    if self._peakListDeleteNotifier:
      self._peakListDeleteNotifier.unRegister()
    if self._spectrumDeleteNotifier:
      self._spectrumDeleteNotifier.unRegister()
    if self._peakNotifier is not None:
      self._peakNotifier.unRegister()
    self._selectOnTableCurrentPeaksNotifier.unRegister()