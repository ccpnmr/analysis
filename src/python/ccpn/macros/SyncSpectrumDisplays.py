"""
A macro to create a module which allows users to synchronise axes among different spectrumDisplays.

Requirements:
    - CcpNmrAnalysis 3.1.1 +
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-07-26 12:15:24 +0100 (Wed, July 26, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author:  Luca Mureddu $"
__date__ = "$Date: 2023-07-20 12:45:48 +0100 (Thu, July 20, 2023) $"
#=========================================================================================
__title__ = "Synchronise axes among different spectrumDisplays"

# Start of code
#=========================================================================================

import uuid
import pandas as pd
from functools import partial
from collections import defaultdict
from ccpn.util.decorators import singleton
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.core.lib.Notifiers import Notifier
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
from ccpn.ui.gui.widgets.MessageDialog import showWarning, showMessage, showError, showMulti, showYesNo
from ccpn.framework.Application import getApplication, getProject, getMainWindow, getCurrent
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Column import Column
from ccpn.ui.gui.widgets.table.CustomPandasTable import CustomDataFrameTable
from ccpn.ui.gui.widgets.table._TableDelegates import _SmallPulldown as PulldownDelegate
from ccpn.ui.gui.widgets.table._TableDelegates import _SimplePulldownTableDelegate as PulldownDelegateModel
from ccpn.ui.gui.modules.CcpnModule import CcpnModule

ROWUID = 'UID'
SOURCESPECTRUMDISPLAYPID = 'sourceSpectrumDisplayPid'
TARGETSPECTRUMDISPLAYPID = 'targetSpectrumDisplayPid'
SOURCEAXISCODE = 'sourceAxisCode'
TARGETAXISCODE = 'targetAxisCode'
_SIGNALS = '_signal'
_CONNECTIONS = 'connections'

## GUI placeholder/variables
_DCTE = 'Double Click to edit'

@singleton
class SpectrumDisplaySyncHandler(object):
    """
    An object to handle the synchronisation of Axes between SpectrumDisplays through notifiers.
    This object will facilitate adding new syncs, removing them and avoiding circular feedbacks from notifiers.
    Data about which SpectrumDisplays/axes are being sync is stored inside a singleton dataFrame.

    DataFrame Columns:
    - sourceSpectrumDisplayPid
    - targetSpectrumDisplayPid
    - sourceAxisCode
    - targetAxisCode
    - ROWUID

    DataFrame Index: same as the ROWUID column
    Internal columns:
    - ROWUID: a unique random str of 13 characters for identify the row in the dataframe.

   IMPORTANT:  _signalsDict:
   _signalsDict is a dictionary of key:dict .
    _signalsDict = { ROWUID   : {
                                                'signals':[..., ],
                                                'connections':[..., ]
                                                 }
                            }
    Key: dataframe index.   inner dict: contains  the (GL) signals and  their active connections.
    This is required so that we can disconnect only what is required. It is not included in the main data, has is not serialisable and only needed at run time.
    """

    columns = [
        SOURCESPECTRUMDISPLAYPID,
        TARGETSPECTRUMDISPLAYPID,
        SOURCEAXISCODE,
        TARGETAXISCODE,
        ROWUID
        ]

    def __init__(self):
        self._data = pd.DataFrame(columns=self.columns)
        self.project = getProject()
        self._signalsDict = {} ##

    @property
    def data(self):
        """The dataframe containing the syncs """
        return self._data

    @property
    def isEmpty(self):
        """Check if the data is empty and does not contain any syncs """
        return self.data.empty

    def syncSpectrumDisplays(self, **kwargs):
        """
        :param kwargs: key-value. Key argument to be the column name  as defined in self.columns.
        E.g. usage:
            myKwargs = {
                                    SOURCESPECTRUMDISPLAYPID : 'theSourceSpectrumDisplayPid',
                                    TARGETSPECTRUMDISPLAYPID : 'theTargetSpectrumDisplayPid',
                                    SOURCEAXISCODE                      : 'theSourceSpectrumDisplayAxisCode',
                                    TARGETAXISCODE                      : 'theTargetSpectrumDisplayAxisCode',
                                    }
            # add the values to the handler:
            SpectrumDisplaySyncHandler().syncSpectrumDisplays(**myKwargs)
        :return: A Pandas Series object representing the new added row to the data.
        """
        newRow = self._addSync(**kwargs)
        return newRow

    def _unsyncByIndex(self, rowIndex):
        """ Remove the row from the data and any signals. """
        ## disconnect signals first
        mask = self._data[ROWUID].eq(rowIndex)
        dataToDisconnect = self._data[mask]
        self._removeGUIConnectionSignals(dataToDisconnect)
        ## Remove defs from data
        self._data = self._data[~mask]
        return self._data

    def unsyncSpectrumDisplay(self, spectrumDisplayPid):
        """ Remove the spectrumDisplay from any synchronisation (whether is a target or the source). """
        ## disconnect signals first
        mask = self.data[SOURCESPECTRUMDISPLAYPID].eq(spectrumDisplayPid) | \
               self.data[TARGETSPECTRUMDISPLAYPID].eq(spectrumDisplayPid)
        data = self.data[mask]
        for i in list(data.index):
            self._unsyncByIndex(i)
        return self._data

    def fetchEmptyEntry(self, placeHolderValue:str=None):
        """ Get or create a row to use as placeholder to start a new sync"""
        df = self.data
        mask = df[SOURCESPECTRUMDISPLAYPID].eq(placeHolderValue) & \
               df[TARGETSPECTRUMDISPLAYPID].eq(placeHolderValue)
        if len(mask)>0:
            filteredData = df[mask]
            if len(filteredData)>0:
                index = list(filteredData.index)[-1]
                return self._data.loc[index]
        index = str(uuid.uuid4()).split('-')[-1]
        self._data.loc[index, self.columns] = [placeHolderValue] * len(self.columns)
        self._data.loc[index, ROWUID] = index
        return self._data.loc[index]

    def cloneSync(self, index):
        row = self._data.loc[index]
        if row is None:
            getLogger().warn(f'Nothing to clone. {index} not in data')
            return
        newIndex = str(uuid.uuid4()).split('-')[-1]
        self._data.loc[newIndex, self.columns] = row.values
        self._data.loc[newIndex, ROWUID] = newIndex
        return self._data.loc[newIndex]

    def clearAll(self):
        """Remove all sync from the table.
        """
        self._removeGUIConnectionSignals()
        self._data.drop(index=self._data.index, inplace=True, errors='ignore')
        return self._data

    ## Private helper methods  ##

    def _addSync(self,  **kwargs):
        """Fill the dataFrame with the Column/Value definitions """
        dd = {k: kwargs[k] for k in self.columns if k in kwargs} ## make sure we have only needed columns, discard the rest
        index = str(uuid.uuid4()).split('-')[-1] ## random unique identifier
        self._data.loc[index, list(dd.keys())] = list(dd.values())
        return self._data.loc[index]

    def _inverseFilterByHeadValue(self, df, header, value):
      return df[~df[header].eq(value)]

    def _syncAxes(self, callbackDict, *, signal, rowIndex:str=None, exactAxisCodeMatch:bool=False, ):
        """Callback from GLWidget signals. """
        if rowIndex not in self.data.index:
            try:
                signal.disconnect()
            except Exception as err:
                getLogger().warning(f'Cannot disconnect {signal} for row {rowIndex}. Error: {err}')
            self._addGUIConnectionSignals(exactAxisCodeMatch=exactAxisCodeMatch) #this is needed to ensure it hasn't disconnected too much!
            return

        firstSourceStrip = callbackDict.get('strip')
        firingSpectrumDisplay = callbackDict.get('spectrumDisplay')

        # do the sync only for the row
        row = self.data.loc[rowIndex]
        sourceDisplayPid = row[SOURCESPECTRUMDISPLAYPID]
        targetDisplayPid = row[TARGETSPECTRUMDISPLAYPID]
        sourceAxisCode = row[SOURCEAXISCODE]
        targetAxisCode = row[TARGETAXISCODE]
        sharingAxis = None
        sourceDisplay = self.project.getByPid(sourceDisplayPid)
        targetDisplay = self.project.getByPid(targetDisplayPid)
        if sourceDisplay is None:
            return
        if targetDisplay is None:
            return
        if firstSourceStrip is None:
            firstSourceStrip = sourceDisplay.strips[0]
        if firingSpectrumDisplay is not None and firingSpectrumDisplay not in [sourceDisplay, targetDisplay]:
            return

        otherStrips = [s for s in sourceDisplay.strips if s != firstSourceStrip]
        otherStrips += [s for s in targetDisplay.strips if s != firstSourceStrip]

        for axis in firstSourceStrip.axes:
            if exactAxisCodeMatch:
                if axis.code == sourceAxisCode:
                    sharingAxis = axis
                    break
            else:
                if len(sourceAxisCode)>0:
                    if axis.code.startswith(sourceAxisCode[0]):
                        sharingAxis = axis
                        break
        if sharingAxis is None:
            return
        sourceRegion = sharingAxis.region

        for otherStrip in otherStrips:
            dd = {}
            for en, targetAxis in enumerate(otherStrip.orderedAxes):
                if exactAxisCodeMatch:
                    if targetAxis.code == targetAxisCode:
                        dd[en] = sourceRegion
                else:
                    if len(targetAxisCode) > 0:
                        if targetAxis.code.startswith(targetAxisCode[0]):
                            dd[en] = sourceRegion
            for index, region in dd.items(): #should be only 1 really
                otherStrip.setAxisRegion(index, region)

    def _getStripsBySpectrumDisplayPid(self, spectrumDisplayPid):
        if spectrumDisplay := self.project.getByPid(spectrumDisplayPid):
            return spectrumDisplay.strips
        return []

    def _getAllAvailableStrips(self, data):
        """Get all strips based on the SpectrumDiplays Pids available in the dataFrame """
        strips = []
        for i, row in data.iterrows():
            targetDisplayPid = row[TARGETSPECTRUMDISPLAYPID]
            sourceDisplayPid = row[SOURCESPECTRUMDISPLAYPID]
            strips += self._getStripsBySpectrumDisplayPid(sourceDisplayPid)
            strips += self._getStripsBySpectrumDisplayPid(targetDisplayPid)
        return list(set(strips))

    def _addGUIConnectionSignals(self, data=None, exactAxisCodeMatch=False):
        """
        Connect the GL widget to a custom method to syncronise the spectrumDisplays.
        :return:
        """
        if data is None:
            data = self.data
        # add all the row id as identifier, so we can check for recycled SpectrumDisplay pids etc
        for index, row in data.iterrows():
            ## Could check is already connected and skip
            strips = self._getStripsBySpectrumDisplayPid(row[SOURCESPECTRUMDISPLAYPID])
            strips += self._getStripsBySpectrumDisplayPid(row[TARGETSPECTRUMDISPLAYPID])
            connections = []
            connectedSignals = []
            for strip in strips:
                # need to find a better way to define these signals without  exposing  _CcpnGLWidget
                #  RowIndex is extremely important so to ensure precise firing and avoid duplicates/circles.
                glWidget = strip.getGLWidget()
                signals = [ glWidget.GLSignals.glXAxisChanged,
                                glWidget.GLSignals.glYAxisChanged,
                                glWidget.GLSignals.glAllAxesChanged ]
                for signal in signals:
                   slot = partial(self._syncAxes, signal=signal, rowIndex=index, exactAxisCodeMatch=exactAxisCodeMatch)
                   connection = signal.connect(slot)
                   connections.append(connection)
                   connectedSignals.append(signal)
            self._signalsDict[index] = {_SIGNALS : connectedSignals,
                                                    _CONNECTIONS: connections}

    def _removeGUIConnectionSignals(self, data=None):
        """
        disconnect the GL widgets which synchronise the spectrumDisplays.
        :param strips: list of strips to be disconnected. If None, it will disconnect all in the data
        :return:
        """
        if data is None:
            data = self.data
        for index, row in data.iterrows():
            signalDict = self._signalsDict.get(index)
            if signalDict is not None:
                signals = signalDict.get(_SIGNALS)
                connections = signalDict.get(_CONNECTIONS)
                for signal, connection in zip(signals, connections):
                    try: # it has to be a try/except because the signal might be already disconnected.
                        signal.disconnect(connection)
                    except Exception as err:
                        getLogger().debug(f'Sync Handler. Cannot disconnect {signal}, index: {index}. Signal might have been already disconnected. {err}')

    def __repr__(self):
        return f'<< SpectrumDisplays Sync Handler >>'

class _PulldownDelegate(PulldownDelegate):
    """ A delegate which fires a signal when the text is highlighted. (Note the native textHighlighted pyqtSignal doesn't work on Pull"""
    def __init__(self, parent, mainWindow=None, textHighlightedCallback=None, *args, **kwds):
        super().__init__(parent, *args, **kwds)
        self.textHighlightedCallback = textHighlightedCallback
        self._list.entered.connect(self._textHighlighted)

    def _textHighlighted(self, qitem):
        text = qitem.data()
        if self.textHighlightedCallback is not None:
            self.textHighlightedCallback(text)

    def paintEvent(self, e: QtGui.QPaintEvent) -> None:
        """Set the colour of the selected pulldown-text
        """
        try:
            if (model := self.model()):
                palette = self.palette()
                if (item := model.item(self.currentIndex())) is not None and item.text():
                    # use the palette to change the colour of the selection text - may not match for other themes
                    palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.Text, item.foreground().color())
                    if self.textHighlightedCallback is not None:
                        self.textHighlightedCallback(item.text())
                else:
                    palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.Text, QtGui.QColor('black'))
                self.setPalette(palette)
        except Exception:
            pass
        finally:
            super(PulldownDelegate, self).paintEvent(e)

    def hidePopup(self) -> None:
        """Hide the popup if event occurs after the double-click interval
        """
        if self.textHighlightedCallback is not None:
            self.textHighlightedCallback('')
        return super().hidePopup()

class SyncSpectrumDisplaysTable(CustomDataFrameTable):
    """A Gui table to contain the list of  synchronised SpectrumDisplays and axisCodes
    """
    defaultTableDelegate = PulldownDelegateModel
    INVALIDCOLOUR = '#f05454'
    VALIDCOLOUR = '#f7f2f2'

    def __init__(self, parent, *args, **kwds):
        super().__init__(parent, *args, **kwds)
        self.project = getProject()
        self.mainWindow = getMainWindow()
        self.application = getApplication()
        self.current = getCurrent()
        # define the column definitions
        ## columnMap -> key: the rowdata column name. Value: the displayed text
        self.columnMap = {
            SOURCESPECTRUMDISPLAYPID: 'Source Display',
            TARGETSPECTRUMDISPLAYPID: 'Target Display',
            SOURCEAXISCODE: 'Source AxisCode',
            TARGETAXISCODE: 'Target AxisCode',
            }
        columns = [
            Column(headerText = self.columnMap[SOURCESPECTRUMDISPLAYPID],
                        getValue = SOURCESPECTRUMDISPLAYPID,
                        rawDataHeading = SOURCESPECTRUMDISPLAYPID,
                        editClass = _PulldownDelegate,
                        tipText = 'Double click to select the Source SpectrumDisplay from where you want to share an axis.',
                        editKw = {
                            'texts': [''],
                            'clickToShowCallback': partial(self._updateSpectrumDisplayPulldownCallback, SOURCESPECTRUMDISPLAYPID),
                            'callback': partial(self._tableSelectionChanged, SOURCESPECTRUMDISPLAYPID),
                            'textHighlightedCallback': self._selectionTextChanged,
                            'objectName':SOURCESPECTRUMDISPLAYPID,
                            },
                        columnWidth=200,
                        ),
            Column(headerText=self.columnMap[SOURCEAXISCODE],
                       getValue=SOURCEAXISCODE,
                       rawDataHeading=SOURCEAXISCODE,
                       editClass=_PulldownDelegate,
                       tipText='Double click to select the Source AxisCode you want to sync',
                       editKw={
                           'texts'              : [''],
                           'clickToShowCallback': partial(self._updateAxisCodeCallback, SOURCESPECTRUMDISPLAYPID, SOURCEAXISCODE),
                           'callback' : partial(self._tableSelectionChanged, SOURCEAXISCODE),
                           'objectName': SOURCEAXISCODE,
                           },
                       columnWidth=150,
                       ),
            Column(headerText = self.columnMap[TARGETSPECTRUMDISPLAYPID],
                       getValue = TARGETSPECTRUMDISPLAYPID,
                       rawDataHeading = TARGETSPECTRUMDISPLAYPID,
                       editClass = _PulldownDelegate,
                       tipText='Double click to select the Target SpectrumDisplay you want to sync with the source SpectrumDisplay Axis.',
                       editKw = {
                            'texts': [''],
                            'clickToShowCallback':partial(self._updateSpectrumDisplayPulldownCallback, TARGETSPECTRUMDISPLAYPID),
                            'callback': partial(self._tableSelectionChanged, TARGETSPECTRUMDISPLAYPID),
                           'textHighlightedCallback': self._selectionTextChanged,
                            'objectName': TARGETSPECTRUMDISPLAYPID,
                        },
                    columnWidth = 200,
                        ),
            Column(headerText= self.columnMap[TARGETAXISCODE],
                   getValue = TARGETAXISCODE,
                   rawDataHeading = TARGETAXISCODE,
                   editClass = _PulldownDelegate,
                   tipText = 'Double click to select the Target AxisCode you want to sync with the source',
                   editKw = {
                            'texts': [''],
                            'clickToShowCallback': partial(self._updateAxisCodeCallback, TARGETSPECTRUMDISPLAYPID, TARGETAXISCODE),
                            'callback':partial(self._tableSelectionChanged, TARGETAXISCODE),
                            'objectName': TARGETAXISCODE,
                            },
                        columnWidth = 100,
                        ),
            Column(headerText=ROWUID, getValue=ROWUID, rawDataHeading=ROWUID,
                   isInternal=True,
                   ),
            ]

        self._columnDefs.setColumns(columns)
        self._rightClickedTableIndex = None  # last selected item in a table before raising the context menu. Enabled with mousePress event filter

        ## Add an empty row to start if not any
        if self.backend.isEmpty:
            self._newSync()

    @property
    def backend(self):
        return SpectrumDisplaySyncHandler()
    
    @property
    def dataFrame(self):
        """ Get the dataframe exactly as displayed on the Table. """
        data = self.model()._getVisibleDataFrame(includeHiddenColumns=True)
        if data.empty:
            return data
        data.set_index(ROWUID, inplace=True, drop=False)
        return data

    def updateTable(self):
        """
        Set the data on the table as it appears on the backend
        :return: the displayed dataframe
        """
        self.setDataFrame(self.backend.data)
        return self.dataFrame

    #=========================================================================================
    # Callbacks from selections
    #=========================================================================================

    def _updateSpectrumDisplayPulldownCallback(self, header):
        currentSelected = self._getSelectedSeries()
        if currentSelected is None:
            return
        rowIndex = currentSelected.name
        pulldown = self.sender()
        tableHeader = self.columnMap.get(header)
        currentSelection = self._getValueByHeader(rowIndex, tableHeader)
        data = self.project.getPidsByObjects(self.project.spectrumDisplays)
        index = data.index(currentSelection) if currentSelection in data else None
        pulldown.setData(data, index=index, headerText=_DCTE, headerEnabled=False,)

    def _updateAxisCodeCallback(self, spectrumDisplayHeader, axisCodeHeader):
        """Callback when changed the axisCode pulldown from table """
        currentSelected = self._getSelectedSeries()
        if currentSelected is None:
            return
        rowIndex = currentSelected.name
        spectrumDisplayTableHeader = self.columnMap.get(spectrumDisplayHeader)
        axisCodeTableHeader = self.columnMap.get(axisCodeHeader)
        currentAc = self._getValueByHeader(rowIndex, axisCodeTableHeader)
        display = self._getDisplayByHeader(rowIndex, spectrumDisplayTableHeader)
        if display is None:
            return
        # update the data
        pulldown = self.sender()
        axisCodes = list(display.axisCodes)
        index = axisCodes.index(currentAc) if currentAc in axisCodes else None
        pulldown.setData(axisCodes, index=index, headerText=_DCTE, headerEnabled=False,)

    def _tableSelectionChanged(self, headerName, value, *args, **kwargs):
        """ Callback after any pulldown is changed.
        This interacts with the backend And amends the data """
        selection = self._getSelectedSeries()
        if selection is None:
            return
        self._amendBackendData(selection.name, headerName, value)
        self.tableChanged.emit()

    def _removeModuleOverlay(self):
        for mo in self.mainWindow.moduleArea.ccpnModules:
            mo._selectedOverlay.setDropArea(None)

    def _selectionTextChanged(self, text):
        self._removeModuleOverlay()
        spectrumDisplay = self.project.getByPid(text)
        if spectrumDisplay is None:
            return
        module = self.mainWindow.ui.getByGid(text)
        if module is not None:
            module._raiseSelectedOverlay()

    def _amendBackendData(self, index, header, value):
        """Given an index, header and value, amend the backend data. Index and header must obviously be in the dataframe"""
        backend = self.backend
        data = backend.data
        data.loc[index, header] = value

    def _getTableColumIndex(self, header,):
        for columIndex, columClass in enumerate(self._columnDefs.columns):
            rawDataHeading = columClass.rawDataHeading
            if header == rawDataHeading:
                return columIndex

    def _validateTable(self):
        """Check if all entry in the table are correct.
         :return: tuple of lists, same length of dataFrame.
                    List one:  bools of True/False for valid/invalid rows;
                    List  two: list of error messages (if any) for each row.
        """
        allValues = []
        allMsgs = []
        for rowNumber, (rowIndex, row) in enumerate(self.dataFrame.iterrows()):
            isValid, msg = self._isValidRow(rowNumber, rowIndex)
            allValues.append(isValid)
            allMsgs.append(msg)
        return allValues, allMsgs

    def _isValidRow(self, rowNumber, rowIndex):
        """
        Check all entries are ok
        :return: tuple of two items: Bool and str. isValid and error text.
        """
        spectrumDisplayTableHeader =  self.columnMap.get(SOURCESPECTRUMDISPLAYPID)
        targetDisplayTableHeader =  self.columnMap.get(TARGETSPECTRUMDISPLAYPID)
        sourceAxisCodeTableHeader = self.columnMap.get(SOURCEAXISCODE)
        targetAxisCodeTableHeader = self.columnMap.get(TARGETAXISCODE)

        sourceDisplay = self._getDisplayByHeader(rowIndex, spectrumDisplayTableHeader)
        targetDisplay = self._getDisplayByHeader(rowIndex, targetDisplayTableHeader)
        sourceAxis = self._getValueByHeader(rowIndex, sourceAxisCodeTableHeader)
        targetAxis = self._getValueByHeader(rowIndex, targetAxisCodeTableHeader)

        sourceDisplayColumIndex = self._getTableColumIndex(SOURCESPECTRUMDISPLAYPID)
        targetDisplayColumIndex = self._getTableColumIndex(TARGETSPECTRUMDISPLAYPID)
        sourceAxisColumIndex = self._getTableColumIndex(SOURCEAXISCODE)
        targetAxisColumIndex = self._getTableColumIndex(TARGETAXISCODE)
        valids = []
        msg = f'Inspect Row: {rowNumber+1} at Column(s): '
        ## Check the source Display Widgets
        if sourceDisplay is None:
            self.setBackground(rowNumber, sourceDisplayColumIndex, self.INVALIDCOLOUR)
            self.setBackground(rowNumber, sourceAxisColumIndex, self.INVALIDCOLOUR)
            valids += [False]
            msg += f' {spectrumDisplayTableHeader}, {sourceAxisCodeTableHeader}; '
        else:
            self.setBackground(rowNumber, sourceDisplayColumIndex, self.VALIDCOLOUR)
            if sourceAxis not in sourceDisplay.axisCodes:
                self.setBackground(rowNumber, sourceAxisColumIndex, self.INVALIDCOLOUR)
                valids += [False]
                msg += f'{sourceAxisCodeTableHeader}. '
            else:
                self.setBackground(rowNumber, sourceAxisColumIndex, self.VALIDCOLOUR)
                valids += [True]

        ## Check the target Display Widgets
        if targetDisplay is None:
            self.setBackground(rowNumber, targetDisplayColumIndex,self.INVALIDCOLOUR)
            self.setBackground(rowNumber, targetAxisColumIndex, self.INVALIDCOLOUR)
            valids += [False]
            msg += f'{targetDisplayTableHeader}, {targetAxisCodeTableHeader}; '
        else:
            self.setBackground(rowNumber, targetDisplayColumIndex, self.VALIDCOLOUR)
            if targetAxis not in targetDisplay.axisCodes:
                self.setBackground(rowNumber, targetAxisColumIndex, self.INVALIDCOLOUR)
                valids += [False]
                msg += f'{targetAxisCodeTableHeader}.'
            else:
                self.setBackground(rowNumber, targetAxisColumIndex, self.VALIDCOLOUR)
                valids += [True]
        return all(valids), msg

    #=========================================================================================
    # convenient methods
    #=========================================================================================

    def _getDisplayByHeader(self, index, header):
        if self.project is None:
            return
        pid = self._getValueByHeader(index, header)
        return self.project.getByPid(pid)

    def _getValueByHeader(self, index, header):
        if header not in self.dataFrame:
            return
        if index not in self.dataFrame.index:
            return
        return self.dataFrame.loc[index, header]

    def _getSelectedSeries(self):
        ll = self.getSelectedObjects()
        if len(ll)>0:
            return ll[-1]
        return

    def populateTable(self):
        """Populate the table
        """
        df = self.backend.data
        self.setDataFrame(df)
        self.setTableEnabled(True)

    def setTableEnabled(self, value):
        """Enable/Disable the table.
        :param value: True/False.
        :return:
        """
        self.setEnabled(value)
        # not sure whether to disable the table or just disable the editing and menu items
        self.setEditable(value)
        for action in self._actions:
            action.setEnabled(value)

    def selectionCallback(self, selected, deselected, selection, lastItem):
        """
        Selection could highlight the sync-ed spectrumDisplays
        """
        row = self._getSelectedSeries()
        if row is None:
            self._removeModuleOverlay()
            return
        sourceDisplayPid = row[SOURCESPECTRUMDISPLAYPID]
        targetDisplayPid = row[TARGETSPECTRUMDISPLAYPID]
        sourceSpectrumDisplay = self.project.getByPid(sourceDisplayPid)
        targetSpectrumDisplay = self.project.getByPid(targetDisplayPid)

        if sourceSpectrumDisplay is not None and targetSpectrumDisplay is not None:
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self._removeTimer)
            self.timer.start(500)
            sourceSpectrumDisplay._raiseSelectedOverlay()
            targetSpectrumDisplay._raiseSelectedOverlay()

    def  _removeTimer(self):
        self._removeModuleOverlay()
        self.timer.stop()

    #=========================================================================================
    # Table context menu
    #=========================================================================================

    def addTableMenuOptions(self, menu):
        """Add options to the right-mouse menu
        """
        menu = self._thisTableMenu
        self._actions = [
                                menu.addAction('New Sync', self._newSync),
                                menu.addAction('Duplicate Selected', self._duplicateSelectedSync),
                                menu.addAction('Duplicate Opposite Axis', self._duplicateOppositeAxis),

                                menu.addSeparator(),
                                menu.addAction('Remove Selected', self._removeSelectedSync),
                                menu.addAction('Remove All', self._removeAllSyncs),
                                menu.addSeparator(),
                                menu.addAction('Clear Selection', self.clearSelection),
                                ]
        return menu

    def _newSync(self):
        """Add new sync to the table.
        """
        dcte = 'Double Click to edit'
        newRow = self.backend.fetchEmptyEntry(dcte)
        self.populateTable()
        self.selectRowsByValues(values=[dcte], headerName=SOURCESPECTRUMDISPLAYPID)

    def _duplicateSelectedSync(self):
        sel = self.getSelectedObjects()
        if len(sel) == 0:
            showWarning('Nothing to duplicate', 'Select a row first')
            return
        for i in sel:
            newRow = self.backend.cloneSync(i.name)
        self.updateTable()

    def _duplicateOppositeAxis(self):
        """Duplicate rows but with Opposite Axis """

        sel = self.getSelectedObjects()
        if len(sel) == 0:
            showWarning('Nothing to duplicate', 'Select a row first')
            return
        for i in sel:
            row = self.backend.cloneSync(i.name)
            sourceDisplayPid = row[SOURCESPECTRUMDISPLAYPID]
            targetDisplayPid = row[TARGETSPECTRUMDISPLAYPID]
            sourceAxisCode = row[SOURCEAXISCODE]
            targetAxisCode = row[TARGETAXISCODE]
            sourceDisplay = self.project.getByPid(sourceDisplayPid)
            targetDisplay = self.project.getByPid(targetDisplayPid)
            if sourceDisplay is not None:
                axes = sourceDisplay.axisCodes
                newAxis = [ax for ax in axes if ax != sourceAxisCode][0]
                self._amendBackendData(i.name, SOURCEAXISCODE, newAxis)
            if targetDisplay is not None:
                axes = targetDisplay.axisCodes
                newAxis = [ax for ax in axes if ax != targetAxisCode][0]
                self._amendBackendData(i.name, TARGETAXISCODE, newAxis)
        self.updateTable()

    def _removeSelectedSync(self):
        """Remove the selected sync from the table.
        """
        rows = self.getSelectedObjects()
        if len(rows) == 0:
            showWarning('Nothing to remove', 'Select a row first')
            return
        for row in rows:
            index = row.name
            self.backend._unsyncByIndex(index)
        self.updateTable()

    def _removeAllSyncs(self):
        """Remove all sync from the table.
        """
        yesRemoveAll = showYesNo('Delete All', 'Do you want delete all data?')
        if yesRemoveAll:
            self.backend.clearAll()
            self.updateTable()

class SpectrumDisplaysSyncEditorModule(CcpnModule):
    """
    """
    includeSettingsWidget = False
    _includeInLastSeen = False  # whether to restore or not after closing it (in the same project)
    _allowRename = False
    className = 'SyncSpectrumDisplays'

    def __init__(self, mainWindow, name= 'SpectrumDisplay Sync Editor (Alpha)'):
        super().__init__(mainWindow=mainWindow, name=name)

        self.mainWindow = getMainWindow()
        self.application = getApplication()
        self.current = getCurrent()
        self.project = getProject()

        ## Add GUI
        hgrid = 0
        self.table = SyncSpectrumDisplaysTable(self.mainWidget,  grid=(hgrid, 0), gridSpan=(2,2))
        self.editButtons = ButtonList(self.mainWidget, texts=['', '', ''],
                                  icons=['icons/list-add', 'icons/list-remove', 'icons/window-duplicate', ],
                                  tipTexts=['Add new sync', 'Remove selected', 'Clone single selected row'],
                                  callbacks=[
                                             self.table._newSync,
                                             self.table._removeSelectedSync,
                                             self.table._duplicateSelectedSync,
                                            ],
                                 direction = 'v',
                                 setMinimumWidth=False,
                                 grid=(hgrid, 2),
                                 vAlign='t')
        self.editButtons.setFixedWidth(30)
        hgrid += 1
        self.syncButtons = ButtonList(self.mainWidget, texts=['', ''],
                                  icons=['icons/link_done', 'icons/unlink'],
                                  tipTexts = ['Re-Sync All SpectrumDisplays', 'Unsync All but keep data '],
                                  callbacks=[
                                             self._syncAll,
                                             self._unsyncAll
                                            ],
                                      direction='v',
                                      setMinimumWidth=False,
                                      grid=(hgrid, 2),
                                      vAlign='b')
        self._updateButton = self.syncButtons.buttons[0]
        self.table.setMinimumHeight(100)
        # self.table.setMinimumWidth(self._minimumWidth)
        self.table.tableChanged.connect(self._tableHasChanged)
        self.mainWidget.setContentsMargins(5, 5, 5, 5)

        ## Add core notifiers
        if self.project:
            self._spectrumDisplayNotifier = Notifier(self.project, [Notifier.DELETE], 'SpectrumDisplay', self._onSpectrumDisplayDeleted)

    @property
    def backendHandler(self):
        return SpectrumDisplaySyncHandler()

    ################################################
    ################ Notification callbacks ###############
    ################################################

    def _updateData(self):
        newData = self.table.dataFrame
        backend = self.backendHandler
        backend._data = newData
        self.table.populateTable()

    def _onSpectrumDisplayDeleted(self, callbackDict, *args):
        """Disconnect any existing signals from the deleted  spectrumDisplay"""
        spectrumDisplay = callbackDict.get(Notifier.OBJECT)
        backend = self.backendHandler
        if self.table.dataFrame.empty:
            return
        if spectrumDisplay is None:
            return
        if not spectrumDisplay.pid in self.table.dataFrame.values:
            return
        backend.unsyncSpectrumDisplay(spectrumDisplay.pid)
        self.table.updateTable()

    def _tableHasChanged(self, *args, **kwargs):
        icon = Icon('icons/link_needsUpdate')
        self._updateButton.setIcon(icon)

    def _syncAll(self):
        if self.backendHandler.isEmpty:
            showWarning('Nothing to sync', 'Add a row first')
            return
        allValid, msgs = self.table._validateTable()
        if all(allValid):
            self.backendHandler._addGUIConnectionSignals()
            self._updateButton.setIcon(Icon('icons/link_done'))
        else:
            text = '\n'.join(msgs)
            showWarning('Could not sync', text)
            return

    def _unsyncAll(self):
        if self.backendHandler.isEmpty:
            showWarning('Nothing to unsync', 'The table data is already empty')
            return
        self.backendHandler._removeGUIConnectionSignals()
        self._updateButton.setIcon(Icon('icons/link_suspended'))

    def _closeModule(self):
        # Do all clean up
        # open a popup to close and remove all data or preserve for next time
        self.backendHandler.clearAll()
        super()._closeModule()

if __name__ == '__main__':
    from ccpn.framework.Application import getApplication

    def _start(moduleArea):
        currentModules = [m for m in moduleArea.ccpnModules if m.className == SpectrumDisplaysSyncEditorModule.className]
        if len(currentModules)>0:
            yesToNew = showYesNo('Already opened.', 'Do you want close the existing module and open a new empty module?')
            if yesToNew:
                for currentModule in currentModules:
                    currentModule._closeModule()
            else:
                return
        module = SpectrumDisplaysSyncEditorModule(mainWindow=moduleArea.mainWindow)
        moduleArea.addModule(module)

    ccpnApplication = getApplication()
    if ccpnApplication:
        _start(ccpnApplication.ui.mainWindow.moduleArea)
    else:
        from ccpn.ui.gui.widgets.Application import TestApplication
        app = TestApplication()
        win = QtWidgets.QMainWindow()
        moduleArea = CcpnModuleArea(mainWindow=None)
        _start(moduleArea)
        win.setCentralWidget(moduleArea)
        win.resize(1000, 500)
        win.setWindowTitle('Testing Module')
        win.show()
        app.start()
