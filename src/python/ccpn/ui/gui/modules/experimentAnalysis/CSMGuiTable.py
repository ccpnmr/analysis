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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-07-15 18:10:39 +0100 (Fri, July 15, 2022) $"
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

######## gui/ui imports ########
from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.GuiTable import GuiTable, _getValueByHeader, _selectRowsOnTable, _makeTipText, _getHiddenColumns
import ccpn.ui.gui.widgets.GuiTable as gt
from ccpn.ui.gui.widgets.Column import ColumnClass, Column
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces



class _CSMGuiTableABC(gt.GuiTable):
    """
    Table containing fitting results.
    Wrapper GuiTable built from the backend outputDataTable.
    See SeriesTablesBC: CSMOutputFrame for more information about the underlined dataframe.
    """
    className = guiNameSpaces.CSMTablePanel
    OBJECT = 'object'
    TABLE = 'table'

    _columnsDefs = {
        guiNameSpaces.ASHTAG: {gt.NAME: sv._ROW_UID,
            gt.GETTER: lambda row: _getValueByHeader(row, sv._ROW_UID),
            gt.TIPTEXT: _makeTipText(guiNameSpaces.ASHTAG, "Table enumeration"),
            gt.WIDTH: 30,
            gt.HIDDEN: False
            },
        guiNameSpaces.ColumnID: {gt.NAME: sv.COLLECTIONID,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.COLLECTIONID),
            gt.TIPTEXT: _makeTipText(guiNameSpaces.ColumnID, "Collection ID"),
            gt.WIDTH: 50,
            gt.HIDDEN: True
            },
        sv.COLLECTIONPID: {gt.NAME: sv.COLLECTIONPID,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.COLLECTIONPID),
            gt.TIPTEXT: _makeTipText(sv.COLLECTIONPID, "Pid for collection containg clustered peaks"),
            gt.WIDTH: 50,
            gt.HIDDEN: True
            },
        guiNameSpaces.ColumnChainCode: {gt.NAME: sv.NMRCHAINNAME,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.NMRCHAINNAME),
            gt.TIPTEXT: _makeTipText(guiNameSpaces.ColumnChainCode, "NmrChain code"),
            gt.WIDTH: 50,
            gt.HIDDEN: False
            },
        guiNameSpaces.ColumnResidueCode: {gt.NAME: sv.NMRRESIDUECODE,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.NMRRESIDUECODE),
            gt.TIPTEXT: _makeTipText(guiNameSpaces.ColumnResidueCode, "NmrResidue sequence code"),
            gt.WIDTH: 60,
            gt.HIDDEN: False
            },
        guiNameSpaces.ColumnResidueType: {gt.NAME: sv.NMRRESIDUETYPE,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.NMRRESIDUETYPE),
            gt.TIPTEXT: _makeTipText(guiNameSpaces.ColumnResidueType, "NmrResidue Type"),
            gt.WIDTH: 50,
            gt.HIDDEN: False
            },
        guiNameSpaces.ColumnAtoms: {gt.NAME: sv.NMRATOMNAMES,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.NMRATOMNAMES),
            gt.TIPTEXT: _makeTipText(guiNameSpaces.ColumnAtoms, "Nmr Atom names included in the calculation"),
            gt.WIDTH: 60,
            gt.HIDDEN: False
            },
        guiNameSpaces.ColumnDdelta: {gt.NAME: sv.DELTA_DELTA,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.DELTA_DELTA),
            gt.TIPTEXT: _makeTipText(sv.DELTA_DELTA, "Perturbation value calculated as per Settings"),
            gt.FORMAT: guiNameSpaces._COLUM_FLOAT_FORM,
            gt.WIDTH: 70,
            gt.HIDDEN: False
            },
        ## Fitting definitions
        sv.KD: {gt.NAME: sv.KD,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.KD),
            gt.TIPTEXT: _makeTipText(sv.KD, ""),
            gt.FORMAT: guiNameSpaces._COLUM_FLOAT_FORM,
            gt.WIDTH: 70,
            gt.HIDDEN: False
            },
        sv.KD_ERR:  {gt.NAME: sv.KD_ERR,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.KD_ERR),
            gt.TIPTEXT: _makeTipText(sv.KD_ERR, ""),
            gt.FORMAT: guiNameSpaces._COLUM_FLOAT_FORM,
            gt.WIDTH: 70,
            gt.HIDDEN: True
            },
        sv.BMAX: {gt.NAME: sv.BMAX,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.BMAX),
            gt.FORMAT: guiNameSpaces._COLUM_FLOAT_FORM,
            gt.TIPTEXT: _makeTipText(sv.BMAX, ""),
            gt.WIDTH: 70,
            gt.HIDDEN: False
            },
        sv.BMAX_ERR: {gt.NAME: sv.BMAX_ERR,
            gt.GETTER: lambda row: _getValueByHeader(row,  sv.BMAX_ERR),
            gt.TIPTEXT: _makeTipText(sv.BMAX_ERR, ""),
            gt.WIDTH: 70,
            gt.HIDDEN: True
            },
        sv.MINIMISER_METHOD: {gt.NAME: sv.MINIMISER_METHOD,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.MINIMISER_METHOD),
            gt.TIPTEXT: _makeTipText(sv.MINIMISER_METHOD, "Minimiser used for fitting"),
            gt.WIDTH: 70,
            gt.HIDDEN: True
            },
        guiNameSpaces.ColumnR2: {gt.NAME: sv.R2,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.R2),
            gt.TIPTEXT: _makeTipText(guiNameSpaces.ColumnR2, ""),
            gt.WIDTH: 70,
            gt.HIDDEN: False
            },
        guiNameSpaces.ColumnCHISQUARE: {gt.NAME: sv.CHISQUARE,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.CHISQUARE),
            gt.TIPTEXT: _makeTipText(guiNameSpaces.ColumnCHISQUARE, ""),
            gt.WIDTH: 70,
            gt.HIDDEN: True
            },
        guiNameSpaces.ColumnREDCHISQUARE: {gt.NAME: sv.REDUCEDCHISQUARE,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.REDUCEDCHISQUARE),
            gt.TIPTEXT: _makeTipText(guiNameSpaces.ColumnREDCHISQUARE, ""),
            gt.WIDTH: 70,
            gt.HIDDEN: True
            },
        sv.AKAIKE: {gt.NAME: sv.AKAIKE,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.AKAIKE),
            gt.TIPTEXT: _makeTipText(sv.AKAIKE, ""),
            gt.WIDTH: 70,
            gt.HIDDEN: True
            },
        sv.BAYESIAN: {gt.NAME: sv.BAYESIAN,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.BAYESIAN),
            gt.TIPTEXT: _makeTipText(sv.BAYESIAN, ""),
            gt.WIDTH: 70,
            gt.HIDDEN: True
            },
        sv.FLAG: {gt.NAME: sv.FLAG,
            gt.GETTER: lambda row: _getValueByHeader(row, sv.FLAG),
            gt.TIPTEXT: _makeTipText(sv.FLAG, ""),
            gt.WIDTH: 40,
            gt.HIDDEN: False
            },
        sv._ROW_UID: {gt.NAME: sv._ROW_UID,
            gt.GETTER: lambda row: _getValueByHeader(row, sv._ROW_UID),
            gt.TIPTEXT: _makeTipText(sv._ROW_UID, ""),
            gt.WIDTH: 100,
            gt.HIDDEN: True
            },
        }

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
        for colName, defs in self._columnsDefs.items():
            columnObject = Column(colName,defs.get(gt.GETTER), tipText= defs.get(gt.TIPTEXT),
                                  setEditValue= defs.get(gt.SETTER), format=defs.get(gt.FORMAT))
            self._columns.columns.append(columnObject)
        self._hiddenColumns = _getHiddenColumns(self)
        self._dataFrame = dataFrame
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
        self._selectOverride = True # otherwise very odd behaviour
        gt._resizeColumnWidths(self)
        self.setMinimumWidth(200)

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
            self.dfo = self.getDataFromFrame(table=self, df=dataFrame, colDefs=self._columns)
            self.setTableFromDataFrameObject(dataFrameObject=self.dfo, columnDefs=self._columns)
            self.setHiddenColumns(_getHiddenColumns(self))
            gt._resizeColumnWidths(self)

    def mousePressEvent(self, event):
        if self.itemAt(event.pos()) is None:
            self.clearSelection()
            return
        else:
            GuiTable.mousePressEvent(self, event)

    def clearSelection(self):
        super(_CSMGuiTableABC, self).clearSelection()
        self.current.nmrResidues = []

    def selection(self, data, *args):
        """

        :param args:
        :return:
        """
        seriesList = data['object']
        objs = set()
        for series in seriesList:
            pid = series[sv.COLLECTIONPID]
            objs.add(self.project.getByPid(pid))
        self.current.collections = objs

    def action(self, *args):
        pass

    def actionCheckBox(self, data):
        pass

    def _rebuild(self):
        self.build(self._dataFrame)

    def _setContextMenu(self, enableExport=True, enableDelete=True):
        """Subclass guiTable to add new items to context menu
        """
        super()._setContextMenu(enableExport=enableExport, enableDelete=enableDelete)
        _actions = self.tableMenu.actions()
        if _actions:
            _topMenuItem = _actions[0]
            _topSeparator = self.tableMenu.insertSeparator(_topMenuItem)
            pass

    def _exportRawData(self):
        if self.moduleParent:
            self.moduleParent._exportRawData()


class CSMTablePanel(GuiPanel):

    position = 1
    panelName = guiNameSpaces.CSMTablePanel

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, *args , **Framekwargs)

    def initWidgets(self):

        self.mainTable = _CSMGuiTableABC(self,
                                             dataFrame=pd.DataFrame(),
                                             guiModule = self.guiModule, grid=(0, 0))

    def setInputData(self, dataFrame):
        """Provide a CSMOutputFrame as DataFrame to populate the table."""
        self.mainTable.dataFrame = dataFrame

    def clearData(self):
        self.mainTable.dataFrame = None
        self.mainTable.clearTable()

    def updatePanel(self, *args, **kwargs):
        getLogger().info('Updating CSM table panel')
        dataFrame = self.guiModule.backendHandler._getGroupedOutputDataFrame()
        self.setInputData(dataFrame)

