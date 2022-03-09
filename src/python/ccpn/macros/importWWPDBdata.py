
"""
Alpha version of a popup for importing selected data from PDB XML reports.
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
__modifiedBy__ = "$Author: Luca Mureddu $"
__dateModified__ = "$Date: 2021-04-27 16:04:57 +0100 (Tue, April 27, 2021) $"
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-03-09 11:05:56 +0000 (Wed, March 09, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2021-04-27 16:04:57 +0100 (Tue, April 27, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
import xml.etree.ElementTree as et

from PyQt5 import QtCore, QtGui, QtWidgets

from ccpn.ui.gui.widgets.PulldownListsForObjects import PeakListPulldown, ChemicalShiftListPulldown, ChainPulldown
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.ListWidget import ListWidgetPair
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.lib.GuiPath import PathEdit
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets import CheckBox, LineEdit
from ccpn.ui.gui.widgets.FileDialog import OtherFileDialog
from ccpn.ui.gui.widgets.HLine import LabeledHLine

from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.core.DataTable import TableFrame

from ccpn.framework.Application import getApplication
from ccpn.framework.Version import applicationVersion

from ccpn.util.Path import aPath


if applicationVersion == '3.1.0':
    ccpnVersion310 = True
else:
    ccpnVersion310 = False


# application = getApplication()


# if application:
#     # Path for Xplor NIH executable. Those calculations are
#     # Local Mac:
#     #xplorPath='/Users/eliza/Projects/xplor-nih-3.2/bin/xplor'
#     xplorPath = application.preferences.externalPrograms.get('xplor')
#
#     # This is an example folder from Xplor NIH distribution with scripts necessary for running calculations
#     pathToXplorBinary = application.preferences.externalPrograms.get('xplor')
#     xplorRootDirectory = os.path.dirname(os.path.dirname(pathToXplorBinary))
#     pathToens2pdb = os.path.join(xplorRootDirectory, 'bin','ens2pdb')


def removeSpaces(txt):
    return ','.join(txt.split())


def getViolationTable(xroot):
    rows = []
    for LineInTheRoot in xroot.iter('violated_distance_restraint'):
        rows.append(LineInTheRoot.attrib)

    pdbViolatedRestrTable = pd.DataFrame(rows)

    # I do not need those columns at the moment:
    columnsToDropOff = ['altcode_1', 'altcode_2', 'chain_1', 'chain_2', 'ent_1', 'ent_2', 'said_1', 'said_2',
                          'icode_1', 'icode_2', ]
    pdbViolatedRestrTable = pdbViolatedRestrTable.drop(columns=columnsToDropOff, axis=1)

    pdbViolatedRestrTable['violation'] = pd.to_numeric(pdbViolatedRestrTable['violation'], errors='coerce')

    return pdbViolatedRestrTable


def getSimpleViolationTable(xroot):
    rows = []
    for LineInTheRoot in xroot.iter('violated_distance_restraint'):
        rows.append(LineInTheRoot.attrib)

    pdbViolatedRestrTable = pd.DataFrame(rows)

    violatedSimplified_dict = {'restraintList':[], 'restraint_id': [], 'resname_1': [], 'resnum_1': [], 'atom_1': [], 'resname_2': [], 'resnum_2': [], 'atom_2': [], 'model': [], 'violation': []}
    violatedSimplified_dict = {'restraintList':[], 'restraint_id': [], 'model': [], 'violation': []}

    count = 0
    for eachRestraintList in pdbViolatedRestrTable['rlist_id'].unique():
        for eachRestraint in pdbViolatedRestrTable.loc[(pdbViolatedRestrTable['rlist_id'] == eachRestraintList)]['rest_id']:  # .unique():
            count = count +1
            # print(eachRestraintList, eachRestraint)

            for model in pdbViolatedRestrTable.loc[(pdbViolatedRestrTable['rest_id'] == eachRestraint) & (pdbViolatedRestrTable['rlist_id'] == eachRestraintList), 'model'].unique():
                violatedSimplified_dict["restraintList"].append(eachRestraintList)
                violatedSimplified_dict["restraint_id"].append(eachRestraint)
                violatedSimplified_dict["model"].append(model)

                violatedSimplified_dict["violation"].append(pdbViolatedRestrTable.loc[(pdbViolatedRestrTable['rest_id'] == eachRestraint) & (pdbViolatedRestrTable['rlist_id'] == eachRestraintList) & (pdbViolatedRestrTable['model'] == model), 'violation'].iloc[0])
                # violatedSimplified_dict["violation"].append(pdbViolatedRestrTable.loc[(pdbViolatedRestrTable['rest_id'] == eachRestraint) & (pdbViolatedRestrTable['rlist_id'] == eachRestraintList)] ['violation'].unique())#.iloc[0])
            if count > 100:
                break

    violatedSimplified_DataFrame = pd.DataFrame.from_dict(violatedSimplified_dict)

    violatedSimplified_DataFrame['violation'] = pd.to_numeric(violatedSimplified_DataFrame['violation'], errors='coerce')

    return violatedSimplified_DataFrame


def getRamachandranTable(xroot):
    rows = []
    for LineInTheRoot in xroot.iter('ModelledSubgroup'):
        rows.append(LineInTheRoot.attrib)

    ramachandranTable = pd.DataFrame(rows)

    # I do not need those columns at the moment:
    #             columnsToDropOff = ['altcode', 'chain', 'ent', 'said','icode', ]
    #             ramachandranTable = ramachandranTable.drop(columns=columnsToDropOff, axis=1)

    ramachandranTable['resnum'] = pd.to_numeric(ramachandranTable['resnum'], downcast="integer",
                                                errors='coerce')
    ramachandranTable['phi'] = pd.to_numeric(ramachandranTable['phi'], errors='coerce')
    ramachandranTable['psi'] = pd.to_numeric(ramachandranTable['psi'], errors='coerce')

    return ramachandranTable


def getSimpleRamachandranTable(xroot):
    rows = []
    ramaSimplified_dict = {'residue': [], 'favored': [], 'allowed': [], 'outlier': []}
    for LineInTheRoot in xroot.iter('ModelledSubgroup'):
        rows.append(LineInTheRoot.attrib)

    ramachandranTable = pd.DataFrame(rows)

    # I do not need those columns at the moment:
#             columnsToDropOff = ['altcode', 'chain', 'ent', 'said','icode', ]
#             ramachandranTable = ramachandranTable.drop(columns=columnsToDropOff, axis=1)

    ramachandranTable['resnum'] = pd.to_numeric(ramachandranTable['resnum'], downcast="integer",
                                                errors='coerce')
    ramachandranTable['phi'] = pd.to_numeric(ramachandranTable['phi'], errors='coerce')
    ramachandranTable['psi'] = pd.to_numeric(ramachandranTable['psi'], errors='coerce')

    for residue in ramachandranTable['resnum'].unique():
        ramaSimplified_dict["residue"].append(residue)
        ramaSimplified_dict["favored"].append(ramachandranTable.loc[(ramachandranTable['resnum'] == residue) & (
                    ramachandranTable['rama'] == 'Favored')]['model'].count())
        ramaSimplified_dict["allowed"].append(ramachandranTable.loc[(ramachandranTable['resnum'] == residue) & (
                    ramachandranTable['rama'] == 'Allowed')]['model'].count())
        ramaSimplified_dict["outlier"].append(ramachandranTable.loc[(ramachandranTable['resnum'] == residue) & (
                    ramachandranTable['rama'] == 'OUTLIER')]['model'].count())

    ramaSimplified_DataFrame = pd.DataFrame.from_dict(ramaSimplified_dict)

    return ramaSimplified_DataFrame


class ImportPDBdataPopup(CcpnDialogMainWidget):
    """

    """
    FIXEDWIDTH = True
    FIXEDHEIGHT = False

    _GREY = '#888888'

    title = 'Import wwPDB data (Alpha)'

    def __init__(self, parent=None, mainWindow=None, title=title,  **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title,
                         size=(500, 10), minimumSize=None, **kwds)

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
        self.tipText = ''
        self.setOkButton(callback=self._okCallback, tipText =self.tipText, text='Import data', enabled=True)
        self.setCloseButton(callback=self.reject, tipText='Close')
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)
        self.__postInit__()
        self._okButton = self.dialogButtons.button(self.OKBUTTON)

    def _createWidgets(self):

        _height = 30
        row = -1


        row += 1
        self.pathLabel = Label(self.mainWidget, text="Path to wwPDB XML report", grid=(row, 0), hAlign='right')
        self.pathData = PathEdit(self.mainWidget, grid=(row, 1), vAlign='t', )
        self.pathData.setMinimumWidth(400)
        # self.pathData.setText('/Users/eliza/Documents/structure_workshop/xplorNihData/structure_3f_2021-08-23_done/D_9100063355_val-data_P1.xml')
        self.pathDataButton = Button(self.mainWidget, grid=(row, 2), callback=self._getPathFromDialog,
                                           icon='icons/directory', hPolicy='fixed')

        row += 1
        LabeledHLine(self.mainWidget, text='Violated Restraints Table', grid=(row,0), gridSpan=(1,2),
                     style='DashLine', colour=self._GREY)

        row += 1
        self.checkLabel = Label(self.mainWidget, text="Import", grid=(row, 0), hAlign='right')
        self.checkBox = CheckBox.CheckBox(self.mainWidget,grid=(row,1), checked=True,
                                          callback=self._updateCallback)

        row += 1
        Label(self.mainWidget, text="Use name", grid=(row, 0), hAlign='right')
        self.violName = LineEdit.LineEdit(self.mainWidget, text='wwPDB_violatedRestraints', grid=(row,1),
                                          textAlignment='left')
        self.violName.setMinimumWidth(400)

        row += 1
        LabeledHLine(self.mainWidget, text='Ramachandran Table', grid=(row,0), gridSpan=(1,2),
                     style='DashLine', colour=self._GREY)

        row += 1
        self.checkLabel1 = Label(self.mainWidget, text="Import", grid=(row, 0), hAlign='right')
        self.checkBox1 = CheckBox.CheckBox(self.mainWidget, grid=(row, 1), checked=True,
                                           callback=self._updateCallback)

        row += 1
        Label(self.mainWidget, text="Use name", grid=(row, 0), hAlign='right')
        self.ramaName = LineEdit.LineEdit(self.mainWidget, text='wwPDB_Ramachandran', grid=(row,1),
                                          textAlignment='left')
        self.ramaName.setMinimumWidth(400)

        # Try to set a sensible initial path
        _path = self.project.application.dataPath
        _runs = [str(p) for p in _path.glob('*/*/*.xml') if p.is_file()]
        if len(_runs) > 0:
            self.pathData.setText(str(_runs[-1]))

        self._updateCallback()

    def _getPathFromDialog(self):

        _currentPath = self.pathData.get()
        if len(_currentPath) > 0:

            _directory = aPath(_currentPath).parent.asString()
        dialog = OtherFileDialog(parent=self.mainWindow, _useDirectoryOnly=False,)
        dialog._show()
        if (path := dialog.selectedFile()) is not None:
            self.pathData.setText(str(path))

    def _updateCallback(self):
        """Update the entry boxes"""
        self.ramaName.setEnabled(self.checkBox1.get())
        self.violName.setEnabled(self.checkBox.get())

    def _okCallback(self):

        if self.project:
            xml_file = self.pathData.get()

            if not xml_file:
                MessageDialog.showWarning('', 'Include path to PDB XML report')
                return

            # run the calculation
            # print('Running with File: %s' %(xml_file))
            with undoBlockWithoutSideBar():
                with notificationEchoBlocking():

                    xtree = et.parse(xml_file)
                    xroot = xtree.getroot()

                    if self.checkBox.isChecked():
                        _dataA = TableFrame(getViolationTable(xroot))
                        # _dataB = TableFrame(getSimpleViolationTable(xroot))
                        self.project.newDataTable(name=self.violName.text(), data=_dataA, comment='violated restraints from PDB')
                        # self.project.newDataTable(name=self.violName.text()+'_simple', data=_dataB, comment='simplified violations from PDB')

                    if self.checkBox1.isChecked():
                        tempRama1 = getRamachandranTable(xroot)
                        tempRama2 = getSimpleRamachandranTable(xroot)
                        _data1 = TableFrame(tempRama1)
                        _data2 = TableFrame(tempRama2)
                        # tempGrp = TableFrame(tempRama.groupby(by = ['chain','resnum','said','ent', 'seq','resname'])['rama'].value_counts())

                        self.project.newDataTable(name=self.ramaName.text(), data=_data1, comment='ramachandran data from PDB')
                        self.project.newDataTable(name=self.ramaName.text()+'_short', data=_data2, comment='Simplified Ramachandran Data')

                    MessageDialog.showInfo(self.title, f'Completed importing {xml_file}')

        self.accept()

if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    # app = TestApplication()
    popup = ImportPDBdataPopup(mainWindow=mainWindow)
    popup.show()
    popup.raise_()
    # app.start()
