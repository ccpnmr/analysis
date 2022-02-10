
"""
Alpha version of a popup for importing selected data from PDB XML reports.
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$Author: Luca Mureddu $"
__dateModified__ = "$Date: 2021-04-27 16:04:57 +0100 (Tue, April 27, 2021) $"
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-08-29 12:32:54 +0100 (Sun, August 29, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2021-04-27 16:04:57 +0100 (Tue, April 27, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets
import ccpn.ui.gui.widgets.CompoundWidgets as cw
from ccpn.ui.gui.widgets.PulldownListsForObjects import PeakListPulldown, ChemicalShiftListPulldown, ChainPulldown
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.ListWidget import ListWidgetPair
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.lib.GuiPath import PathEdit
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets import CheckBox, LineEdit

import os
import shutil

import datetime
from distutils.dir_util import copy_tree
from ccpn.ui.gui.widgets.FileDialog import OtherFileDialog
from ccpn.framework.Application import getApplication
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.framework.Version import applicationVersion
#!/usr/bin/env python3
import argparse
import string

import sys
import pathlib
import re

import pandas as pd
import xml.etree.ElementTree as et
from ccpn.core.DataTable import TableFrame

with undoBlockWithoutSideBar():
    with notificationEchoBlocking():


        if applicationVersion == '3.1.0':
            ccpnVersion310 = True
        else:
            ccpnVersion310 = False


        application = getApplication()


        if application:
            # Path for Xplor NIH executable. Those calculations are
            # Local Mac:
            #xplorPath='/Users/eliza/Projects/xplor-nih-3.2/bin/xplor'
            xplorPath = application.preferences.externalPrograms.get('xplor')

            # This is an example folder from Xplor NIH distribution with scripts necessary for running calculations
            pathToXplorBinary = application.preferences.externalPrograms.get('xplor')
            xplorRootDirectory = os.path.dirname(os.path.dirname(pathToXplorBinary))
            pathToens2pdb = os.path.join(xplorRootDirectory, 'bin','ens2pdb')


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

            title = 'Import PDB data (Alpha)'
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

                row = 0
                self.pathLabel = Label(self.mainWidget, text="Path to PDB XML report", grid=(row, 0))
                self.pathData = PathEdit(self.mainWidget, grid=(row, 1), vAlign='t', )
                self.pathData.setText('/Users/eliza/Documents/structure_workshop/xplorNihData/structure_3f_2021-08-23_done/D_9100063355_val-data_P1.xml')
                self.pathDataButton = Button(self.mainWidget, grid=(row, 2), callback=self._getPathFromDialog,
                                                   icon='icons/directory', hPolicy='fixed')

                row =1
                self.checkLabel = Label(self.mainWidget, text="Get PDB Violated restraints table?", grid=(row, 0))

                self.checkBox = CheckBox.CheckBox(self.mainWidget,grid=(row,1))

                self.violName = LineEdit.LineEdit(self.mainWidget,grid=(row,2))
                self.violName.setText('PDBviolatedRestraints')

                row = 2
                self.checkLabel1 = Label(self.mainWidget, text="Get PDB ramachandran table?", grid=(row, 0))

                self.checkBox1 = CheckBox.CheckBox(self.mainWidget, grid=(row, 1))
                self.ramaName = LineEdit.LineEdit(self.mainWidget,grid=(row,2))
                self.ramaName.setText('PDBRamachandran')

            def _getPathFromDialog(self):
                dialog = OtherFileDialog(parent=self.mainWindow, _useDirectoryOnly=False,)
                dialog._show()
                path = dialog.selectedFile()

                if path:
                    self.pathData.setText(str(path))

            def _okCallback(self):
                if self.project:
                    xml_file = self.pathData.get()

                    if not xml_file:
                        MessageDialog.showWarning('', 'Include path to PDB XML report')
                        return

                    # run the calculation
                    print('Running with File: %s' %(xml_file))

                    xtree = et.parse(xml_file)

                    xroot = xtree.getroot()

                    if self.checkBox.isChecked():
                        _dataA = TableFrame(getViolationTable(xroot))
                        _dataB = TableFrame(getSimpleViolationTable(xroot))
                        self.project.newDataTable(name=self.violName.text(), data=_dataA, comment='violated restraints from PDB')
                        self.project.newDataTable(name=self.violName.text()+'_simple', data=_dataB, comment='simplified violations from PDB')

                    if self.checkBox1.isChecked():
                        tempRama1 = getRamachandranTable(xroot)
                        tempRama2 = getSimpleRamachandranTable(xroot)
                        _data1 = TableFrame(tempRama1)
                        _data2 = TableFrame(tempRama2)
                        # tempGrp = TableFrame(tempRama.groupby(by = ['chain','resnum','said','ent', 'seq','resname'])['rama'].value_counts())

                        self.project.newDataTable(name=self.ramaName.text(), data=_data1, comment='ramachandran data from PDB')
                        self.project.newDataTable(name=self.ramaName.text()+'_simple', data=_data2, comment='Simplified Ramachandran Data')

                    MessageDialog.showWarning('', 'Complete!')
                self.accept()

        if __name__ == '__main__':
            from ccpn.ui.gui.widgets.Application import TestApplication
            # app = TestApplication()
            popup = ImportPDBdataPopup(mainWindow=mainWindow)
            popup.show()
            popup.raise_()
            # app.start()
