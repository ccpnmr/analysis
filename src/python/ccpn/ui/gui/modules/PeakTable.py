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

  className = 'PeakTable'

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

  positionsUnit = UNITS[0] #default

  def __init__(self, parent, moduleParent, application, **kwds):
    self._project = application.project
    self._current = application.current
    self.moduleParent = moduleParent
    self.settingWidgets = None
    self._selectedPeakList = None

    kwds['setLayout'] = True  ## Assure we have a layout with the widget
    self._widget = Widget(parent=parent, **kwds)

    ## create peakList table widget
    ObjectTable.__init__(self, parent=self._widget, setLayout=True, columns=[], objects=[], autoResize=True, multiSelect=True,
                         actionCallback=self._actionCallback, selectionCallback=self._selectionCallback, grid=(1, 0), gridSpan=(1, 6))

    ## create Pulldown for selection of peakList
    gridHPos = 0
    self.pLwidget = PeakListPulldown(parent=self._widget, project=self._project,grid=(0, gridHPos), gridSpan=(1, 1),
                                     minimumWidths=(0, 100),callback=self._pulldownPLcallback)

    ## create widgets for selection of position units
    gridHPos+=1
    self.posUnitPulldownLabel = Label(parent=self._widget, text= ' Position Unit', grid=(0, gridHPos))
    gridHPos += 1
    self.posUnitPulldown = PulldownList(parent=self._widget, texts=UNITS, callback=self._pulldownUnitsCallback, grid=(0, gridHPos))

    ## set notifiers
    self._selectOnTableCurrentPeaksNotifier = Notifier(self._current,[Notifier.CURRENT], targetName='peaks',callback=self._selectOnTableCurrentPeaksNotifierCallback)
    # TODO set notifier to trigger only for the selected peakList.
    self._peakListDeleteNotifier = Notifier(self._project, [Notifier.CREATE, Notifier.DELETE], 'PeakList', self._peakListNotifierCallback)
    self._peakNotifier =  Notifier(self._project,[Notifier.DELETE, Notifier.CREATE, Notifier.CHANGE], 'Peak', self._peakNotifierNotifierCallback)

    ## populate the table if there are peaklists in the project
    self._updateTable()


  def _getTableColumns(self, peakList):
    '''Add default columns  plus the ones according with peakList.spectrum dimension
     format of column = ( Header Name, value, tipText, editOption) 
     editOption allows the user to modify the value content by doubleclick
     '''

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


  ##################   Updates   ##################

  def _updateAllModule(self):
    '''Updates the table and the settings widgets'''
    self._updateTable()
    self._updateSettingsWidgets()

  def _updateTable(self):
    '''Display the peaks on the table for the selected PeakList.
    Obviously, If the peak has not been previously deleted and flagged isDeleted'''

    self.setObjectsAndColumns(objects=[], columns=[]) #clear current table first
    self._selectedPeakList = self._project.getByPid(self.pLwidget.getText())
    if self._selectedPeakList is not None:
      peaks = [peak for peak in self._selectedPeakList.peaks if not peak.isDeleted]
      self.setObjectsAndColumns(objects=peaks, columns=self._getTableColumns(self._selectedPeakList))
      self._selectOnTableCurrentPeaks(self._current.peaks)
    else:
      self.setObjects([]) #if not peaks, make the table empty

  def _updateSettingsWidgets(self):
    ''' update settings Widgets according with the new displayed table '''
    displayColumnWidget = self.moduleParent._getDisplayColumnWidget()
    displayColumnWidget.updateWidgets(self)
    searchWidget = self.moduleParent._getSearchWidget()
    searchWidget.updateWidgets(self)

  ##################   Widgets callbacks  ##################

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

  def _pulldownUnitsCallback(self, unit):
    # update the table with new units
    self._setPositionUnit(unit)
    self._updateAllModule()

  def _pulldownPLcallback(self, data):
    self._updateAllModule()

  ##################   Notifiers callbacks  ##################

  def _peakListNotifierCallback(self, data):
    '''Refreshs the table only if the peakList involved in the notification is the one displayed '''
    if self._selectedPeakList is not None:
      self.pLwidget.select(self._selectedPeakList.pid) #otherwise automatically reset from the compoundWidget pulldown notifiers

    peakList = data['object']
    if self._selectedPeakList != peakList:
      return
    else:
      self._updateAllModule()

  def _peakNotifierNotifierCallback(self, data):
    '''Callback for peak notifier. Refresh the table only if the peak belongs to the peakList displayed
    NB. Currently impossible to register and trigger the notifier dynamically for only the peaks in the peakList displayed.
    This because when deleting a peakList or spectrum from the project, the process starts by deleting one by one the peak and triggering the peak notifier automatically and therefore refreshing the table,
    TODO: better notifier that if a parent object is deleted it suspends all the children notifiers.
   '''
    peak = data['object']
    if peak is not None:
      if self._selectedPeakList != peak.peakList:
        return
      else:
        self._updateAllModule()

  def _selectOnTableCurrentPeaksNotifierCallback(self, data):
    '''callback from a notifier to select the current peaks  '''
    currentPeaks = data['value']
    self._selectOnTableCurrentPeaks(currentPeaks)

  def _selectOnTableCurrentPeaks(self, currentPeaks):
    ''' highlight current peaks on the opened peak table '''

    if len(currentPeaks)>0:
      self._highLightObjs(currentPeaks)
    else:
      self.clearSelection()


  @staticmethod
  def _getCommentText(peak):
    if peak.comment == '' or not peak.comment:
      return ' '
    else:
      return peak.comment

  @staticmethod
  def _setComment(peak, value):
    peak.comment = value

  def _setPositionUnit(self, value):
    if value in UNITS:
      PeakListTableWidget.positionsUnit = value


  def destroy(self):
    "Cleanup of self"
    if self._peakListDeleteNotifier:
      self._peakListDeleteNotifier.unRegister()
    if self._peakNotifier:
      self._peakNotifier.unRegister()
    self._selectOnTableCurrentPeaksNotifier.unRegister()