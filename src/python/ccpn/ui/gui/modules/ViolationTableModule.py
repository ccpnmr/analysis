"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-04-21 18:53:46 +0100 (Thu, April 21, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-10-29 16:38:09 +0100 (Fri, October 29, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
import pandas as pd
from ccpn.core.ViolationTable import ViolationTable as KlassTable

from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownListsForObjects import ViolationTablePulldown as KlassPulldown, RestraintTablePulldown
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.lib._SimplePandasTable import _SimplePandasTableView, _updateSimplePandasTable
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar

from ccpn.util.Logging import getLogger


ALL = '<all>'
_RESTRAINTTABLE = 'restraintTable'


#=========================================================================================
# ViolationTableModule
#=========================================================================================

class ViolationTableModule(CcpnModule):
    """
    This class implements the module by wrapping a ViolationTable instance
    """
    includeSettingsWidget = False
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'left'

    includePeakLists = False
    includeNmrChains = False
    includeSpectrumTable = False

    className = f'{KlassTable.className}Module'
    _allowRename = True

    activePulldownClass = None
    _includeInLastSeen = False

    def __init__(self, mainWindow=None, name=f'{KlassTable.className} Module',
                 table=None, selectFirstItem=False):
        """
        Initialise the Module widgets
        """
        super().__init__(mainWindow=mainWindow, name=name)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = self.project = self.current = None
        self._table = None

        # add the widgets
        self._setWidgets()

        if table is not None:
            self._selectTable(table)
        elif selectFirstItem:
            self._modulePulldown.selectFirstItem()

    def _setWidgets(self):
        """Set up the widgets for the module
        """
        # make the main splitter
        self._splitter = Splitter(None, horizontal=False, grid=(0, 0), isFloatWidget=True)
        self._splitter.setContentsMargins(0, 0, 0, 0)
        self.mainWidget.getLayout().addWidget(self._splitter, 0, 0)  # MUST be inserted this way

        _topWidget = self._topFrame = Frame(None, setLayout=True,  #grid=(0, 0),
                                            )  #scrollBarPolicies=('never', 'asNeeded'))
        _bottomWidget = self._bottomFrame = Frame(None, setLayout=True,  #grid=(1, 0),
                                                  )  #scrollBarPolicies=('never', 'asNeeded'))
        self._splitter.addWidget(self._topFrame)
        self._splitter.addWidget(_bottomWidget)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setSizes([1000, 2000])

        # add the guiTable to the bottom
        self._tableWidget = _TableWidget(parent=_bottomWidget,
                                         mainWindow=self.mainWindow,
                                         moduleParent=self,
                                         setLayout=True,
                                         grid=(0, 0))

        # main widgets at the top
        row = 0
        Spacer(_topWidget, 5, 5,
               QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
               grid=(0, 0), gridSpan=(1, 1))
        row += 1
        self._modulePulldown = KlassPulldown(parent=_topWidget,
                                             mainWindow=self.mainWindow, default=None,
                                             grid=(row, 0), gridSpan=(1, 2), minimumWidths=(0, 100),
                                             showSelectName=True,
                                             sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                             callback=self._selectionPulldownCallback,
                                             )
        # fixed height
        self._modulePulldown.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

        row += 1
        HLine(parent=_topWidget, grid=(row, 0), gridSpan=(1, 4), height=16, colour=getColours()[DIVIDER])

        row += 1
        self.rtWidget = RestraintTablePulldown(parent=_topWidget,
                                               mainWindow=self.mainWindow, default=None,
                                               grid=(row, 0), gridSpan=(1, 2), minimumWidths=(0, 100),
                                               showSelectName=True,
                                               sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                               callback=self._rtPulldownCallback,
                                               )
        self.rtWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

        row += 1
        Label(_topWidget, text='\nmetadata', grid=(row, 0), hAlign='r', vAlign='t')
        self._metadata = _SimplePandasTableView(_topWidget, showVerticalHeader=False)
        _topWidget.getLayout().addWidget(self._metadata, row, 1, 1, 3)
        self._metadata.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        row += 1
        self.labelComment = Label(_topWidget, text='comment', grid=(row, 0), hAlign='r')
        self.lineEditComment = LineEdit(_topWidget, grid=(row, 1), gridSpan=(1, 3),
                                        textAlignment='l', backgroundText='> Optional <')
        self.lineEditComment.editingFinished.connect(self._applyComment)

        row += 1
        Spacer(_topWidget, 5, 5,
               QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
               grid=(row, 3), gridSpan=(1, 1))
        _topWidget.getLayout().setColumnStretch(3, 1)

    def _maximise(self):
        """
        Maximise the attached table
        """
        if self._table:
            pass
        else:
            self.clear()

    def _closeModule(self):
        """
        CCPN-INTERNAL: used to close the module
        """
        self._tableWidget._close()
        super()._closeModule()

    def _selectTable(self, table=None):
        """
        Manually select a ViolationTable from the pullDown
        """
        if not isinstance(table, KlassTable):
            getLogger().warning(f'select: Object {table} is not of type {KlassTable.className}')
            return
        else:
            for widgetObj in self._modulePulldown.textList:
                if table.pid == widgetObj:
                    self._table = table
                    self._modulePulldown.select(self._table.pid)

    def _selectionPulldownCallback(self, item):
        """
        Notifier Callback for selecting violationTable from the pull down menu
        """
        if item is not None:
            self._table = self.project.getByPid(item)
            if self._table is not None:
                self._update(self._table)
            else:
                _updateSimplePandasTable(self._tableWidget, pd.DataFrame({}))
                self.lineEditComment.setText('')

                _df = pd.DataFrame({'name'     : [],
                                    'parameter': []})
                _updateSimplePandasTable(self._metadata, _df, _resize=True)

    def _rtPulldownCallback(self, item):
        """
        Notifier Callback for selecting restraintTable from the pull down menu
        """
        try:
            with undoBlockWithoutSideBar():
                if (_rTable := self.project.getByPid(item)):
                    self._table.setMetadata(_RESTRAINTTABLE, item)
                else:
                    self._table.setMetadata(_RESTRAINTTABLE, None)

        except Exception as es:
            # need to immediately set back to stop error on loseFocus which also fires editingFinished
            showWarning('Violation Table', str(es))

        _df = pd.DataFrame({'name'     : self._table.metadata.keys(),
                            'parameter': self._table.metadata.values()})
        _updateSimplePandasTable(self._metadata, _df, _resize=True)

    def _update(self, table):
        """
        Update the table
        """
        df = table.data
        if len(table.data) > 0:
            _updateSimplePandasTable(self._tableWidget, df, _resize=False)
        else:
            _updateSimplePandasTable(self._tableWidget, pd.DataFrame({}))

        _rTablePid = table.getMetadata(_RESTRAINTTABLE)
        self.rtWidget.select(_rTablePid)
        self.lineEditComment.setText(table.comment if table.comment else '')

        _df = pd.DataFrame({'name'     : table.metadata.keys(),
                            'parameter': table.metadata.values()})
        _updateSimplePandasTable(self._metadata, _df, _resize=True)

    def _applyComment(self):
        """Set the values in the violationTable
        """
        if self._table:
            comment = self.lineEditComment.text()
            try:
                with undoBlockWithoutSideBar():
                    self._table.comment = comment

            except Exception as es:
                # need to immediately set back to stop error on loseFocus which also fires editingFinished
                showWarning('Data Table', str(es))


#=========================================================================================
# _TableWidget
#=========================================================================================

class _TableWidget(_SimplePandasTableView):
    """
    Class to present a ViolationTable
    """
    className = '_TableWidget'
    attributeName = KlassTable._pluralLinkName

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, **kwds):
        """
        Initialise the widgets for the module.
        """
        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        kwds['setLayout'] = True

        # Initialise the scroll widget and common settings
        self._initTableCommonWidgets(parent, **kwds)

        # initialise the currently attached dataFrame
        self._hiddenColumns = []
        self.dataFrameObject = None

        # initialise the table
        super().__init__(parent=parent,
                         showHorizontalHeader=True,
                         showVerticalHeader=False,
                         grid=(3, 0), gridSpan=(1, 6))
        self.moduleParent = moduleParent

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

        # may refactor the remaining modules so this isn't needed
        self._widgetScrollArea.setFixedHeight(self._widgetScrollArea.sizeHint().height())

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, KlassTable, self.moduleParent._modulePulldown)

    def _close(self):
        """
        Cleanup the notifiers when the window is closed
        """
        pass

    def _handleDroppedItems(self, pids, objType, pulldown):
        """
        :param pids: the selected objects pids
        :param objType: the instance of the obj to handle, E.g. PeakList
        :param pulldown: the pulldown of the module wich updates the table
        :return: Actions: Select the dropped item on the table or/and open a new modules if multiple drops.
        If multiple different obj instances, then asks first.
        """
        from ccpn.ui.gui.lib.MenuActions import _openItemObject

        objs = [self.project.getByPid(pid) for pid in pids]

        selectableObjects = [obj for obj in objs if isinstance(obj, objType)]
        others = [obj for obj in objs if not isinstance(obj, objType)]
        if len(selectableObjects) > 0:
            _openItemObject(self.mainWindow, selectableObjects[1:])
            pulldown.select(selectableObjects[0].pid)

        else:
            from ccpn.ui.gui.widgets.MessageDialog import showYesNo

            othersClassNames = list(set([obj.className for obj in others if hasattr(obj, 'className')]))
            if len(othersClassNames) > 0:
                if len(othersClassNames) == 1:
                    title, msg = 'Dropped wrong item.', 'Do you want to open the %s in a new module?' % ''.join(othersClassNames)
                else:
                    title, msg = 'Dropped wrong items.', 'Do you want to open items in new modules?'
                openNew = showYesNo(title, msg)
                if openNew:
                    _openItemObject(self.mainWindow, others)


#=========================================================================================
# main
#=========================================================================================

def main():
    """Show the dataTableModule
    """
    from ccpn.ui.gui.widgets.Application import newTestApplication
    from ccpn.framework.Application import getApplication

    # create a new test application
    app = newTestApplication(interface='Gui')
    application = getApplication()
    mainWindow = application.ui.mainWindow

    # add a module
    _module = ViolationTableModule(mainWindow=mainWindow)
    mainWindow.moduleArea.addModule(_module)

    # show the mainWindow
    app.start()


if __name__ == '__main__':
    """Call the test function
    """
    main()
