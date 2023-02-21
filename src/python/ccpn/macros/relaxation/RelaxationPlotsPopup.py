"""
A  popup to launch several macros that generate various relaxation plots.
These macros require a DataTable containing the results of a Reduced Spectral density Mapping analysis.
See the Dynamics tutorial to learn how to create such a  dataTable.
See each individual macros for details.
All macros are a demo/starting point. Modify as needed.
Macro created for Analysis Version 3.1.1
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
__dateModified__ = "$dateModified: 2023-02-21 22:18:12 +0000 (Tue, February 21, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2023-02-17 14:03:22 +0000 (Fri, February 17, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================


import ccpn.core #this is needed it to avoid circular imports
from PyQt5 import QtCore, QtGui, QtWidgets
import ccpn.ui.gui.widgets.CompoundWidgets as cw
from ccpn.ui.gui.widgets.PulldownListsForObjects import DataTablePulldown
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.MoreLessFrame import MoreLessFrame
from ccpn.util.Path import aPath, fetchDir, joinPath

TIPTEXT = ''' 
A  popup to launch several macros that generate various relaxation plots.
These macros require a DataTable containing the results of a Reduced Spectral density Mapping analysis.
See the Dynamics tutorial to learn how to create such a  dataTable. '''

thisDirPath = aPath(__file__).filepath
SEQUENCE = 'KLILNGKTLKGETTTEAVDAATAEKVFKQYANDNGVDGEWTYDAATKTFTVTE'
SS_SEQUENCE = 'BBBBBCCCCBBBBBBCCCCHHHHHHHHHHHHHHCCCCCBBBBCCCCCBBBBBC'

MINIMUMWIDTHS = (150, 300)

MACROS_DICT = {
                            'Rates': '1_RelaxationRates_plots.py',
                            'Anisotropy Determination': '2_AnisotropyDetermination_plots.py',
                            'Reduced Spectral Density Mapping': '3_ReduceSpectralDensityMapping_plots.py',
                            'T1 vs T2 Contoured Scatter': '4_T1T2_contourScatter_plot.py',
                            }

class RelaxationPlotsPopup(CcpnDialogMainWidget):
    """
    """
    FIXEDWIDTH = True
    FIXEDHEIGHT = False

    title = 'Relaxation Plots Popup (Alpha)'
    def __init__(self, parent=None, mainWindow=None,
                 title=title,  **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title,
                         size=(500, 200), minimumSize=None, **kwds)

        if mainWindow:
            self.mainWindow = mainWindow
            self.application = mainWindow.application
            self.current = self.application.current
            self.project = mainWindow.project

        else:
            self.mainWindow = None
            self.application = None
            self.current = None
            self.project = None

        self._createWidgets()

        # enable the buttons
        self.tipText = TIPTEXT
        self.setOkButton(callback=self._okCallback, tipText =self.tipText, text='Generate', enabled=True)
        self.setCloseButton(callback=self.reject, tipText='Close')
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)

        # initialise the buttons and dialog size
        self._postInit()
        self._okButton = self.dialogButtons.button(self.OKBUTTON)
        # self.dialogButtons.hide()

    def _createWidgets(self):

        row = 0

        self.dtwidget = DataTablePulldown(parent=self.mainWidget,
                                         mainWindow=self.mainWindow,
                                         grid=(row, 0),
                                         showSelectName=True,
                                         minimumWidths=MINIMUMWIDTHS,
                                         # sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                          gridSpan=(1, 2),
                                         callback=None)
        row += 1
        self.filePathW = cw.EntryPathCompoundWidget(self.mainWidget, labelText='Output Dir Path',
                                                     entryText=str(thisDirPath),
                                                    lineEditMinimumWidth=300,
                                                    minimumWidths=MINIMUMWIDTHS,
                                                    compoundKwds = {'fileMode': 'directory'},
                                                    gridSpan=(1, 1),
                                                           grid=(row, 0))
        self.filePathW.entry.lineEdit.setMinimumWidth(MINIMUMWIDTHS[1])

        row += 1
        self.seWidget = cw.EntryCompoundWidget(self.mainWidget, labelText='Sequence',
                                               tipText='One letter code sequence without spaces. Leave empty if not available',
                                               entryText=SEQUENCE,
                                               minimumWidths=MINIMUMWIDTHS,
                                               gridSpan=(1, 1),
                                               grid=(row, 0))
        row += 1
        self.ssWidget = cw.EntryCompoundWidget(self.mainWidget, labelText='Secondary Structure',
                                               tipText='One letter code secondary structure sequence without spaces.  DSSP nomenclature. Leave empty if not available',
                                               entryText=SS_SEQUENCE,
                                               minimumWidths=MINIMUMWIDTHS,
                                               gridSpan=(1, 1),
                                               grid=(row, 0))
        row += 1
        self.optionsCB = cw.CheckBoxesCompoundWidget(self.mainWidget, labelText='Reports',
                                               tipText='',
                                               texts=list(MACROS_DICT.keys()),
                                                compoundKwds= {'direction': 'v',
                                                                      'selectAll': True,
                                                                      'hAlign': 'left'
                                                                      },
                                               minimumWidths=MINIMUMWIDTHS,
                                               gridSpan=(1, 1),
                                               grid=(row, 0))

        self.optionsCB.getLayout().setAlignment(QtCore.Qt.AlignLeft)

        self.mainWidget.getLayout().setAlignment(QtCore.Qt.AlignTop)


    def _okCallback(self):
        dataTableName = None
        if self.project:
            dataTable = self.project.getByPid(self.dtwidget.getText())
            if dataTable is not None:
                dataTableName = dataTable.name

        outputPath = self.filePathW.getText()

        sequence = self.seWidget.getText()
        ss = self.ssWidget.getText()
        selectedOptions = self.optionsCB.getTexts()

        for selectedOption in selectedOptions:
            macroPathName = MACROS_DICT.get(selectedOption, None)
            if macroPathName is not None:

                macroPath = aPath(joinPath(thisDirPath, macroPathName))
                macroName = macroPath.basename
                filePath = aPath(joinPath(outputPath, macroName))
                filePath = filePath.assureSuffix('.pdf')
                commands = [
                                    f'-d {dataTableName}',
                                    f'-o {filePath}',
                                    f'-se {sequence}',
                                    f'-ss {ss}'
                            ]
                if self.application is not None:
                    self.application.runMacro(macroPath, commands)

        self.accept()

if __name__ == '__main__':
    popup = RelaxationPlotsPopup(mainWindow=mainWindow)
    popup.show()
    popup.raise_()
