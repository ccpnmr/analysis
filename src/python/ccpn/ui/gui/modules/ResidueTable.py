"""
This file contains ResidueTableModule and ResidueTable classes

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:45 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.lib import CcpnSorting
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.widgets.PulldownListsForObjects import ChainPulldown
from ccpn.ui.gui.widgets.MessageDialog import showInfo, showWarning, showNotImplementedMessage
from ccpn.ui.gui.widgets.GuiTable import GuiTable, GuiTableFrame
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.core.Chain import Chain
from ccpn.core.Residue import Residue
from ccpn.core.Atom import Atom
from PyQt5 import QtWidgets
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.core.lib.CallBack import CallBack
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea

logger = getLogger()
ALL = '<all>'


class ResidueTableModule(CcpnModule):
    """
    This class implements the module by wrapping a ResidueTable instance
    """
    includeSettingsWidget = False
    maxSettingsState = 2
    settingsPosition = 'left'

    className = 'ResidueTableModule'

    def __init__(self, mainWindow=None, name='Residue Table',
                 chain=None, selectFirstItem=False):
        """
        Initialise the Module widgets
        """
        CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        self.residueTable = ResidueTable(parent=self.mainWidget,
                                               mainWindow=self.mainWindow,
                                               moduleParent=self,
                                               setLayout=True,
                                               actionCallback=self.navigateToResidueCallBack,
                                               multiSelect=True,
                                               grid=(0, 0))

        if chain is not None:
            self.selectChain(chain)
        elif selectFirstItem:
            self.residueTable.cWidget.selectFirstItem()

        self.installMaximiseEventHandler(self._maximise, self._closeModule)

    def _maximise(self):
        """
        Maximise the attached table
        """
        self.residueTable._maximise()

    def selectChain(self, chain=None):
        """
        Manually select an Chain from the pullDown
        """
        self.residueTable._selectChain(chain)

    def navigateToResidueCallBack(self, data):
        """
        """
        showNotImplementedMessage()        
        return
        # TODO add callback

    def _closeModule(self):
        """CCPN-INTERNAL: used to close the module
        """
        self.residueTable._close()
        super()._closeModule()

    def close(self):
        """Close the table from the commandline
        """
        self._closeModule()

    def paintEvent(self, event):
        event.ignore()


class ResidueTable(GuiTable):
    """
    Class to present a residue Table and a Chain pulldown list, wrapped in a Widget
    """
    className = 'ResidueTable'
    attributeName = 'chains'

    OBJECT = 'object'
    TABLE = 'table'

    @staticmethod
    def _nmrIndex(res):
        """
        CCPN-INTERNAL: Insert an index into ObjectTable
        """
        try:
            return res.chain.residues.index(res)
        except:
            return None

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, actionCallback=None, selectionCallback=None,
                 checkBoxCallback=None, chain=None, multiSelect=False,
                 **kwds):
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

        parent.getLayout().setHorizontalSpacing(0)
        self._widgetScrollArea = ScrollArea(parent=parent, scrollBarPolicies=('never', 'never'), **kwds)
        self._widgetScrollArea.setWidgetResizable(True)
        self._widget = Widget(parent=self._widgetScrollArea, setLayout=True)
        self._widgetScrollArea.setWidget(self._widget)
        self._widget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)

        self._chain = None
        if actionCallback is None:
            actionCallback = self.defaultActionCallback

        ResidueTable.project = self.project

        # create the column objects
        self.NMRcolumns = ColumnClass([
            # ('#', lambda residue: residue.serial, 'Residue serial number', None),
            ('Index', lambda residue: ResidueTable._nmrIndex(residue), 'Index of Residue in the Chain', None),
            ('Pid', lambda residue: residue.pid, 'Pid of Residue', None),
            ('_object', lambda residue: residue, 'Object', None),
            ('Chain', lambda residue: residue.chain.id, 'Chain containing the Residue', None),
            ('Sequence', lambda residue: residue.sequenceCode, 'Sequence code of Residue', None),
            ('Type', lambda residue: residue.residueType, 'Residue type', None),
            ('Atoms', lambda residue: ResidueTable._getAtomNames(residue), 'Atoms in Residue', None),
            ('Comment', lambda nmr: ResidueTable._getCommentText(nmr), 'Notes',
             lambda nmr, value: ResidueTable._setComment(nmr, value))
            ])

        selectionCallback = self._selectionCallback if selectionCallback is None else selectionCallback

        self.cWidget = ChainPulldown(parent=self._widget,
                                         project=self.project, default=None,  #first Chain in project (if present)
                                         grid=(1, 0), gridSpan=(1, 1), minimumWidths=(0, 100),
                                         showSelectName=True,
                                         sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                         callback=self._selectionPulldownCallback
                                         )
        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(2, 50), gridSpan=(1, 1))
        self._setWidgetHeight(35)
        self.cWidget.setFixedSize(self.cWidget.sizeHint())

        # initialise the currently attached dataFrame
        self._hiddenColumns = ['Pid', 'Chain']
        self.dataFrameObject = None

        # initialise the table
        super().__init__(parent=parent,
                            mainWindow=self.mainWindow,
                            dataFrameObject=None,
                            setLayout=True,
                            autoResize=True, multiSelect=multiSelect,
                            actionCallback=actionCallback,
                            selectionCallback=selectionCallback,
                            checkBoxCallback=checkBoxCallback,
                            grid=(3, 0), gridSpan=(1, 6),
                            enableDelete=True
                            )
        self.moduleParent = moduleParent

        # TODO: see how to handle peaks as this is too costly at present
        # Notifier object to update the table if the peaks change

        if chain is not None:
            self._selectChain(chain)

        self.setTableNotifiers(tableClass=Chain,
                               className=self.attributeName,
                               tableSelection='_chain',  # _chain.residues
                               rowClass=Residue,
                               cellClassNames=[(Atom, 'residue')],  # doesn't change anything
                               tableName='chain', rowName='residue',
                               changeFunc=self.displayTableForChain,
                               updateFunc=self._update,
                               pullDownWidget=self.cWidget,
                               callBackClass=Residue,
                               selectCurrentCallBack=self._selectOnTableCurrentResiduesNotifierCallback,
                               moduleParent=moduleParent)

        self.droppedNotifier = GuiNotifier(self,
                                           [GuiNotifier.DROPEVENT], [DropBase.PIDS],
                                           self._processDroppedItems)

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, Chain, self.cWidget)

    def addWidgetToTop(self, widget, col=2, colSpan=1):
        """
        Convenience to add a widget to the top of the table; col >= 2
        """
        if col < 2:
            raise RuntimeError('Col has to be >= 2')
        self._widget.getLayout().addWidget(widget, 0, col, 1, colSpan)
        widget.setFixedSize(widget.sizeHint())
        self._widget.setFixedSize(self._widget.sizeHint())

    def addWidgetToPos(self, widget, row=0, col=2, rowSpan=1, colSpan=1, overrideMinimum=False):
        """
        Convenience to add a widget to the top of the table; col >= 2
        """
        if col < 2 and not overrideMinimum:
            raise RuntimeError('Col has to be >= 2')
        self._widget.getLayout().addWidget(widget, row, col, rowSpan, colSpan)
        widget.setFixedSize(widget.sizeHint())
        self._widget.setFixedSize(self._widget.sizeHint())

    def _setWidgetHeight(self, height):
        self._widgetScrollArea.setFixedHeight(height)

    def _selectChain(self, chain=None):
        """
        Manually select a Chain from the pullDown
        """
        if chain is None:
            # logger.warning('select: No Chain selected')
            # raise ValueError('select: No Chain selected')
            self.cWidget.selectFirstItem()
        else:
            if not isinstance(chain, Chain):
                logger.warning('select: Object is not of type Chain')
                raise TypeError('select: Object is not of type Chain')
            else:
                for widgetObj in self.cWidget.textList:
                    if chain.pid == widgetObj:
                        self._chain = chain
                        self.cWidget.select(self._chain.pid)

    def defaultActionCallback(self, data, *args):
        """
        """
        objs = data[CallBack.OBJECT]
        if not objs:
            return
        if isinstance(objs, (tuple, list)):
            residue = objs[0]
        else:
            residue = objs

        showNotImplementedMessage()
        return
        # TODO add default Action Callback
       
    def displayTableForChain(self, chain):
        """
        Display the table for all Residue's of chain
        """
        self.cWidget.select(chain.pid)
        self._update(chain)

    def _maximise(self):
        """
        refresh the table on a maximise event
        """
        if self._chain:
            self.displayTableForChain(self._chain)
        else:
            self.clear()

    def _update(self, chain):
        """
        Update the table
        """
        self.populateTable(rowObjects=chain.residues,
                           columnDefs=self.NMRcolumns
                           )

        # self.project.blankNotification()
        # objs = self.getSelectedObjects()
        #
        # self._dataFrameObject = self.getDataFrameFromList(table=self,
        #                                                   buildList=chain.residues,
        #                                                   colDefs=self.NMRcolumns,
        #                                                   hiddenColumns=self._hiddenColumns)
        #
        # # populate from the Pandas dataFrame inside the dataFrameObject
        # self.setTableFromDataFrameObject(dataFrameObject=self._dataFrameObject)
        # self._highLightObjs(objs)
        # self.project.unblankNotification()


    def _selectionCallback(self, data):
        """
        Notifier Callback for selecting a row in the table
        """
        selected = data[Notifier.OBJECT]

        if selected:
            if self.multiSelect:  #In this case selected is a List!!
                if isinstance(selected, list):
                    self.current.residues = selected
            else:
                self.current.residue = selected[0]
        else:
            # TODO:ED this should never be called, and where is it?
            self.current.clearResidues()

        ResidueTableModule.currentCallback = {'object': self._chain, 'table': self}

    def _selectionPulldownCallback(self, item):
        """
        Notifier Callback for selecting Chain
        """
        self._chain = self.project.getByPid(item)
        logger.debug('>selectionPulldownCallback>', item, type(item), self._chain)
        if self._chain is not None:
            self.displayTableForChain(self._chain)
        else:
            self.clearTable()

    def _selectOnTableCurrentResiduesNotifierCallback(self, data):
        """
        callback from a notifier to select the current Residue
        """
        currentResidues = data['value']
        self._selectOnTableCurrentResidues(currentResidues)

    def _selectOnTableCurrentResidues(self, currentResidues):
        """
        highlight  current Residues on the opened table
        """
        self.highlightObjects(currentResidues)
        # if len(currentResidues) > 0:
        #     self._highLightObjs(currentResidues)
        # else:
        #     self.clearSelection()

    @staticmethod
    def _getAtomNames(residue):
        """
        Returns a sorted list of Atom names
        """
        return ', '.join(sorted(set([atom.name for atom in residue.atoms if not atom._flaggedForDelete]),
                                key=CcpnSorting.stringSortKey))

    @staticmethod
    def _getResiduePeakCount(residue):
        """
        Returns peak list count
        """
        l1 = [peak for atom in residue.atoms for peak in atom.assignedPeaks]
        return len(set(l1))

    # def _close(self):
    #     """
    #     Cleanup the notifiers when the window is closed
    #     """
    #     self.clearTableNotifiers()

    def _getPullDownSelection(self):
        return self.cWidget.getText()

    def _selectPullDown(self, value):
        self.cWidget.select(value)
