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
__dateModified__ = "$dateModified: 2022-06-27 13:23:36 +0100 (Mon, June 27, 2022) $"
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
    Table containing reference information. Scores and values are calculated on the fly from the main dataframe
    stored in datasets.
    """
    className = guiNameSpaces.CSMTablePanel
    OBJECT = 'object'
    TABLE = 'table'

    _columnsDefs = {
        guiNameSpaces.ASHTAG: {gt.NAME: sv.SERIAL,
                gt.GETTER: lambda row: _getValueByHeader(row, sv.SERIAL),
                gt.TIPTEXT: _makeTipText(guiNameSpaces.ASHTAG, "Table enumeration"),
                gt.WIDTH: 30,
                gt.HIDDEN: False
                },
        guiNameSpaces.ColumnChainCode: {gt.NAME: sv.CHAIN_CODE,
              gt.GETTER: lambda row: _getValueByHeader(row, sv.CHAIN_CODE),
              gt.TIPTEXT: _makeTipText(guiNameSpaces.ColumnChainCode, "NmrChain code"),
              gt.WIDTH: 50,
              gt.HIDDEN: False
              },
        guiNameSpaces.ColumnResidueCode: {gt.NAME: sv.RESIDUE_CODE,
              gt.GETTER: lambda row: _getValueByHeader(row, sv.RESIDUE_CODE),
              gt.TIPTEXT: _makeTipText(guiNameSpaces.ColumnResidueCode, "NmrResidue sequence code"),
              gt.WIDTH: 60,
              gt.HIDDEN: False
              },
        guiNameSpaces.ColumnAtoms: {gt.NAME: sv.ATOM_NAMES,
              gt.GETTER: lambda row: _getValueByHeader(row, sv.ATOM_NAMES),
              gt.TIPTEXT: _makeTipText(guiNameSpaces.ColumnAtoms, "Nmr Atom names included in the calculation"),
              gt.WIDTH: 60,
              gt.HIDDEN: False
              },
        guiNameSpaces.ColumnDdelta: {gt.NAME: sv.DELTA_DELTA,
              gt.GETTER: lambda row: _getValueByHeader(row, sv.DELTA_DELTA_MEAN),
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
        sv.KD+sv.ERROR:  {gt.NAME: sv.KD+sv._ERR,
                gt.GETTER: lambda row: _getValueByHeader(row, sv.KD+sv._ERR),
                gt.TIPTEXT: _makeTipText(sv.KD+sv._ERR, ""),
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
        sv.BMAX+sv.ERROR: {gt.NAME: sv.BMAX+sv._ERR,
                gt.GETTER: lambda row: _getValueByHeader(row,  sv.BMAX+sv._ERR),
                gt.TIPTEXT: _makeTipText(sv.BMAX+sv._ERR, ""),
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

    @property
    def dataFrame(self):
        return self._dataFrame

    @dataFrame.setter
    def dataFrame(self, dataFrame):
        self._dataFrame = dataFrame
        self.build(dataFrame)

    def build(self, dataFrame):
        self.clear()
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
        selection to set current nmrResidue
        :param args:
        :return:
        """
        seriesList = data['object']
        objs = set()
        for series in seriesList:
            pid = series[sv._ROW_UID]
            obj = self.project.getByPid(pid)
            objs.add(obj)
        self.current.nmrResidues = list(objs)



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
        row = 0
        Label(self, 'Test TablePanel', grid=(row, 0))
        self.mainTable = _CSMGuiTableABC(self,
                                             dataFrame=pd.DataFrame(),
                                             guiModule = self.guiModule, grid=(0, 0))
        self.mainTable.dataFrame = pd.DataFrame([1, 2, 3, 4], columns=['#'])

    def setInputData(self, dataFrame):
        self.mainTable.dataFrame = dataFrame
