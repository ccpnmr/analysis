#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-09-05 11:51:23 +0100 (Mon, September 05, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================


import pandas as pd
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.util.Logging import getLogger
from ccpn.core.Peak import Peak
######## gui/ui imports ########
from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Column import ColumnClass, Column
import ccpn.ui.gui.widgets.GuiTable as gt
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces


class _ExperimentalAnalysisTableABC(gt.GuiTable):
    """
    Table containing fitting results.
    Wrapper GuiTable built from the backend outputDataTable.
    See SeriesTablesBC for more information about the underlined dataframe.
    """
    className = guiNameSpaces.CSMTablePanel
    OBJECT = 'object'
    TABLE = 'table'

    _commonColumnsDefs = {
        guiNameSpaces.ASHTAG: {gt.NAME: sv._ROW_UID,
            gt.GETTER: lambda row: gt._getValueByHeader(row, sv._ROW_UID),
            gt.TIPTEXT: gt._makeTipText(guiNameSpaces.ASHTAG, "Table enumeration"),
            gt.WIDTH: 30,
            gt.HIDDEN: False
            },
        guiNameSpaces.ColumnID: {gt.NAME: sv.COLLECTIONID,
            gt.GETTER: lambda row: gt._getValueByHeader(row, sv.COLLECTIONID),
            gt.TIPTEXT: gt._makeTipText(guiNameSpaces.ColumnID, "Collection ID"),
            gt.WIDTH: 50,
            gt.HIDDEN: True
            },
        sv.COLLECTIONPID: {gt.NAME: sv.COLLECTIONPID,
            gt.GETTER: lambda row: gt._getValueByHeader(row, sv.COLLECTIONPID),
            gt.TIPTEXT: gt._makeTipText(sv.COLLECTIONPID, "Pid for collection containg clustered peaks"),
            gt.WIDTH: 50,
            gt.HIDDEN: True
            },
        guiNameSpaces.ColumnChainCode: {gt.NAME: sv.NMRCHAINNAME,
            gt.GETTER: lambda row: gt._getValueByHeader(row, sv.NMRCHAINNAME),
            gt.TIPTEXT: gt._makeTipText(guiNameSpaces.ColumnChainCode, "NmrChain code"),
            gt.WIDTH: 50,
            gt.HIDDEN: False
            },
        guiNameSpaces.ColumnResidueCode: {gt.NAME: sv.NMRRESIDUECODE,
            gt.GETTER: lambda row: gt._getValueByHeader(row, sv.NMRRESIDUECODE),
            gt.TIPTEXT: gt._makeTipText(guiNameSpaces.ColumnResidueCode, "NmrResidue sequence code"),
            gt.WIDTH: 60,
            gt.HIDDEN: False
            },
        guiNameSpaces.ColumnResidueType: {gt.NAME: sv.NMRRESIDUETYPE,
            gt.GETTER: lambda row: gt._getValueByHeader(row, sv.NMRRESIDUETYPE),
            gt.TIPTEXT: gt._makeTipText(guiNameSpaces.ColumnResidueType, "NmrResidue Type"),
            gt.WIDTH: 50,
            gt.HIDDEN: False
            },
        guiNameSpaces.ColumnAtoms: {gt.NAME: sv.NMRATOMNAMES,
            gt.GETTER: lambda row: gt._getValueByHeader(row, sv.NMRATOMNAMES),
            gt.TIPTEXT: gt._makeTipText(guiNameSpaces.ColumnAtoms, "Nmr Atom names included in the calculation"),
            gt.WIDTH: 60,
            gt.HIDDEN: False
            },

        sv._ROW_UID: {gt.NAME: sv._ROW_UID,
                      gt.GETTER: lambda row: gt._getValueByHeader(row, sv._ROW_UID),
                      gt.TIPTEXT: gt._makeTipText(sv._ROW_UID, ""),
                      gt.WIDTH: 100,
                      gt.HIDDEN: True
                      }}

    ## Fitting definitions
    _fittingColumnsDefs = {} #autogenerated based on the Fitting Model params. defined in _getFittingColumnDefs

    ## Model definitions
    _modelColumnsDefs = {
        sv.MINIMISER_METHOD: {gt.NAME: sv.MINIMISER_METHOD,
            gt.GETTER: lambda row: gt._getValueByHeader(row, sv.MINIMISER_METHOD),
            gt.TIPTEXT: gt._makeTipText(sv.MINIMISER_METHOD, "Minimiser used for fitting"),
            gt.WIDTH: 70,
            gt.HIDDEN: True
            },
        guiNameSpaces.ColumnR2: {gt.NAME: sv.R2,
            gt.GETTER: lambda row: gt._getValueByHeader(row, sv.R2),
            gt.TIPTEXT: gt._makeTipText(guiNameSpaces.ColumnR2, ""),
            gt.WIDTH: 70,
            gt.HIDDEN: False
            },
        guiNameSpaces.ColumnCHISQUARE: {gt.NAME: sv.CHISQUARE,
            gt.GETTER: lambda row: gt._getValueByHeader(row, sv.CHISQUARE),
            gt.TIPTEXT: gt._makeTipText(guiNameSpaces.ColumnCHISQUARE, ""),
            gt.WIDTH: 70,
            gt.HIDDEN: True
            },
        guiNameSpaces.ColumnREDCHISQUARE: {gt.NAME: sv.REDUCEDCHISQUARE,
            gt.GETTER: lambda row: gt._getValueByHeader(row, sv.REDUCEDCHISQUARE),
            gt.TIPTEXT: gt._makeTipText(guiNameSpaces.ColumnREDCHISQUARE, ""),
            gt.WIDTH: 70,
            gt.HIDDEN: True
            },
        sv.AKAIKE: {gt.NAME: sv.AKAIKE,
            gt.GETTER: lambda row: gt._getValueByHeader(row, sv.AKAIKE),
            gt.TIPTEXT: gt._makeTipText(sv.AKAIKE, ""),
            gt.WIDTH: 70,
            gt.HIDDEN: True
            },
        sv.BAYESIAN: {gt.NAME: sv.BAYESIAN,
            gt.GETTER: lambda row: gt._getValueByHeader(row, sv.BAYESIAN),
            gt.TIPTEXT: gt._makeTipText(sv.BAYESIAN, ""),
            gt.WIDTH: 70,
            gt.HIDDEN: True
            },
        }
    _othersColumnsDefs = {}

    def __init__(self, parent, guiModule, dataFrame, **kwds):
        self.mainWindow = guiModule.mainWindow
        self.dataFrameObject = None

        super().__init__(parent=parent, mainWindow=self.mainWindow, dataFrameObject=None,  # class collating table and objects and headings,
                        setLayout=True, autoResize=True, multiSelect=True,
                        enableMouseMoveEvent=False,
                        selectionCallback=self.selection,
                        actionCallback=self.selection,
                        checkBoxCallback=self.actionCheckBox,  grid=(0, 0))
        self.guiModule = guiModule
        self.current = self.guiModule.current
        self._columns = ColumnClass([])
        self._hiddenColumns = gt._getHiddenColumns(self)
        self._dataFrame = dataFrame
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
        self._selectOverride = True # otherwise very odd behaviour
        gt._resizeColumnWidths(self)
        self.setMinimumWidth(200)

    def buildColumns(self):
        """build columns on the fly from the definitions """
        self._columns = ColumnClass([])
        for colName, defs in self._columnsDefs.items():
            columnObject = Column(colName, defs.get(gt.GETTER), tipText= defs.get(gt.TIPTEXT),
                                  setEditValue= defs.get(gt.SETTER), format=defs.get(gt.FORMAT))
            self._columns.columns.append(columnObject)

    @property
    def _columnsDefs(self) -> dict:
        dd = dict()
        dd.update(self._commonColumnsDefs)
        dd.update(self.fittingColumnsDefs)
        dd.update(self._modelColumnsDefs)
        dd.update(self._othersColumnsDefs)
        return dd

    def _getFittingColumnDefs(self):
        """Create the fitting Columns based on the function arguments defined in the FittingModel.
         Most of the time are 2 columns + the corresponding error column. E.g.: decay, decay_err, amplitude, amplitude_err
         But it might be more in future implementations """
        backend = self.guiModule.backendHandler
        model = backend.currentFittingModel
        params = model.getFittingArgumentNames()
        defs = {}
        for param in params:
            hidden = True if sv._ERR in param else False # don't show the error column as default
            dd = {param :{gt.NAME: param,
                   gt.GETTER: lambda row: gt._getValueByHeader(row, param),
                   gt.TIPTEXT: gt._makeTipText(param, ""),
                   gt.FORMAT: guiNameSpaces._COLUM_FLOAT_FORM,
                   gt.WIDTH: 70,
                   gt.HIDDEN: hidden
                   }}
            defs.update(dd)
        return defs

    @property
    def fittingColumnsDefs(self) -> dict:
        """ Populate the columns from the FittingModel parameters """
        if self._fittingColumnsDefs is not None and len(self._fittingColumnsDefs) > 0:
            fittingColumnsDefs = self._fittingColumnsDefs
        else:
            fittingColumnsDefs = self._getFittingColumnDefs()
        return fittingColumnsDefs

    @fittingColumnsDefs.setter
    def fittingColumnsDefs(self, dd):
        self._fittingColumnsDefs = dd

    @property
    def dataFrame(self):
        return self._dataFrame

    @dataFrame.setter
    def dataFrame(self, dataFrame):
        self._dataFrame = dataFrame
        self.build(dataFrame)

    def build(self, dataFrame):
        self.clear()
        if dataFrame is not None:
            self.buildColumns()
            self.dfo = self.getDataFromFrame(table=self, df=dataFrame, colDefs=self._columns)
            self.setTableFromDataFrameObject(dataFrameObject=self.dfo, columnDefs=self._columns)
            self.setHiddenColumns(gt._getHiddenColumns(self))
            gt._resizeColumnWidths(self)

    def mousePressEvent(self, event):
        if self.itemAt(event.pos()) is None:
            self.clearSelection()
            return
        else:
            super().mousePressEvent(event)

    def clearSelection(self):
        super().clearSelection()
        self.current.collections = []

    def getSelectedCollections(self):
        selectedObjs = self.getSelectedObjects()
        collections = set()
        for selectedRow in selectedObjs:
            coPid = selectedRow[sv.COLLECTIONPID]
            co = self.project.getByPid(coPid)
            collections.add(co)
        return list(collections)

    def getPeaksFromCollection(self, collection):
        peaks = set()
        for item in collection.items:
            if isinstance(item, Peak):
                peaks.add(item)
        return list(peaks)

    def selection(self, data, *args):
        """

        :param args:
        :return:
        """
        collections = self.getSelectedCollections()
        peaks = set()
        for collection in collections:
            peaks.update(self.getPeaksFromCollection(collection))
        self.current.collections = collections
        self.current.peaks = list(peaks)

    def action(self, *args):
        pass

    def actionCheckBox(self, data):
        pass

    def _rebuild(self):
        self.build(self._dataFrame)

    def _setContextMenu(self):
        """Subclass guiTable to add new items to context menu
        """
        super()._setContextMenu()

        _actions = self.tableMenu.actions()
        if _actions:
            _topMenuItem = _actions[0]
            self.tableMenu.insertSeparator(_topMenuItem)
            editCollection = self.tableMenu.addAction('Edit Collection', self._editCollection)
            self.tableMenu.moveActionAboveName(editCollection, 'Export Visible Table')

    def _editCollection(self):
        from ccpn.ui.gui.popups.CollectionPopup import CollectionPopup
        collections = self.getSelectedCollections()
        if len(collections)>0:
            co = collections[-1]
            if co is not None:
                popup = CollectionPopup(self, mainWindow=self.mainWindow, obj=co, editMode=True)
                popup.exec()
                popup.raise_()


class TablePanel(GuiPanel):

    position = 1
    panelName = 'TablePanel'
    TABLE = _ExperimentalAnalysisTableABC

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, *args , **Framekwargs)


    def initWidgets(self):
        row = 0
        Label(self, 'TablePanel', grid=(row, 0))
        self.mainTable = self.TABLE(self,
                                     dataFrame=pd.DataFrame(),
                                     guiModule = self.guiModule, grid=(0, 0))

    
    def setInputData(self, dataFrame):
        """Provide the DataFrame to populate the table."""
        self.mainTable.dataFrame = dataFrame

    def updatePanel(self, *args, **kwargs):
        getLogger().info('Updating Relaxation table panel')
        dataFrame = self.guiModule.backendHandler._getGuiOutputDataFrame()
        self.setInputData(dataFrame)

    def clearData(self):
        self.mainTable.dataFrame = None
        self.mainTable.clearTable()
