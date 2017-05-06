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

  def __init__(self, project, mainWindow, name='PeakList Table'):

    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    # Derive application, project, and current from mainWindow
    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = project
    self.current = mainWindow.application.current


    # mainWidget
    self.peakListTable = PeakListTableWidget(parent=self.mainWidget, moduleParent=self, setLayout=True,
                                             application=self.application, grid=(0, 0))

    # settingsWidget
    self.displayColumnWidget = ColumnViewSettings(parent=self.settingsWidget, table=self.peakListTable, grid=(0, 0))
    self.searchWidget = ObjectTableFilter(parent=self.settingsWidget, table=self.peakListTable, grid=(1, 0))


  def _closeModule(self):
    """Re-implementation of closeModule function from CcpnModule to unregister notification """
    # FIXME is this needed?
    self.peakListTable.destroy()
    self.close()


class PeakListTableWidget(ObjectTable):

  positionsUnit = UNITS[0] #default

  def initColumns(self, peakList):
    '''Add default columns  plus the ones according with peakList.spectrum dimension
     format of column = ( Header Name, value, tipText, editOption) 
     editOption allows the user to modify the value content by doubleclick
     '''

    self.columnDefs = []

    if peakList is not None:
      serialTipText = 'Peak serial number'
      serial = ('#', 'serial', serialTipText, None)
      self.columnDefs.append(serial)

      numDim = peakList.spectrum.dimensionCount
      # Assign
      for i in range(numDim):
        j = i + 1
        assignTipText = 'NmrAtom assignments of peak in dimension %d' % j
        assign =  ('Assign F%d' % j, lambda pk, dim=i: getPeakAnnotation(pk, dim), assignTipText, None)
        self.columnDefs.append(assign)

      # Peak positions
      for i in range(numDim):
        j = i + 1
        positionTipText = 'Peak position in dimension %d' % j
        position = ('Pos F%d' % j, lambda pk, dim=i, unit=self.positionsUnit: getPeakPosition(pk, dim, unit), positionTipText, None)
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
      comment = ('Comment', lambda pk: self._getCommentText(pk), commentsTipText, lambda pk, value: self._setComment(pk, value))
      self.columnDefs.append(comment)

      self._setColumns()

  def _setColumns(self):
    '''set the columns on the table from the list of tuples "columnDefs"  '''
    columns = [Column(colName, func, tipText=tipText, setEditValue=editValue) for colName, func, tipText, editValue in self.columnDefs]
    self.setColumns(columns)

  def _getCommentText(self, peak):
    if peak.comment == '' or not peak.comment:
      return ' '
    else:
      return peak.comment

  def _setComment(self, peak, value):
    peak.comment = value


  def __init__(self, parent, moduleParent, application, **kwds):
    self._project = application.project
    self._current = application.current
    self.peakTableModule = moduleParent
    kwds['setLayout'] = True  ## Assure we have a layout with the widget
    self._widget = Widget(parent=parent, **kwds)

    # create the table; objects are added later via the displayTableForPeakList method
    ObjectTable.__init__(self, parent=self._widget, setLayout=True, columns=[], objects=[], autoResize=True, multiSelect=True,
                         actionCallback=self._actionCallback, selectionCallback=self._selectionCallback, grid=(1, 0), gridSpan=(1, 6))
    gridHPos = 0
    self.ncWidget = PeakListPulldown(parent=self._widget,
                                     project=self._project, default=0,  # first peakList in project (if present)
                                     grid=(0, gridHPos), gridSpan=(1, 1), minimumWidths=(0, 100),
                                     callback=self._selectionPulldownCallback
                                     )
    gridHPos+=1
    self.posUnitPulldownLabel = Label(parent=self._widget, text= ' Position Unit', grid=(0, gridHPos))
    gridHPos += 1
    self.posUnitPulldown = PulldownList(parent=self._widget, texts=UNITS, callback=self.updateUnits,
                                        grid=(0, gridHPos))

    self._peakNotifier = None
    self._updateSilence = False  # flag to silence updating of the table

    if len(self._project.peakLists) > 0:
      self.displayTableForPeakList(self._project.peakLists[0])

    # register current notifier to select on the table the current peaks
    self._current.registerNotify(self._selectOnTableCurrentPeaks, 'peaks')

  def updateUnits(self, unit):
    self.positionsUnit = unit
    if self.objects:
      peakList = self.objects[0].peakList
      self.displayTableForPeakList(peakList) #update the table with new units

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
    self.initColumns(peakList)


    if self._peakNotifier is not None:
      # we have a new peak and hence need to unregister the previous notifier
      self._peakNotifier.unRegister()
    # register a notifier for this peakList
    self._peakNotifier = Notifier(peakList, [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME], 'Peak', self._updateCallback)
    self._updateSettingsWidgets()

    self.ncWidget.select(peakList.pid)
    self._update(peakList)

  def setUpdateSilence(self, silence):
    "Silences/unsilences the update of the table until switched again"
    self._updateSilence = silence

  def _updateSettingsWidgets(self):
    # FIXME do the proper way for updating setting widget when refreshing the table contents. LM
    if hasattr(self.peakTableModule, 'displayColumnWidget'):
      self.peakTableModule.displayColumnWidget.updateWidgets(self)
    if hasattr(self.peakTableModule, 'searchWidget'):
      self.peakTableModule.searchWidget.updateColumnOption(self)

  def _update(self, peakList):
    "Update the table "
    if not self._updateSilence:
      self.clearTable()
      self._silenceCallback = True
      self.setObjects(peakList.peaks)
      self._silenceCallback = False
      self.show()
      self._updateSettingsWidgets()

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
    self._current.unRegisterNotify(self._selectOnTableCurrentPeaks, 'peaks')

#