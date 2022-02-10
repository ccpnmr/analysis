
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

            pdbRestrTable = pd.DataFrame(rows)

            # I do not need those columns at the moment:
            columnsToDropOff = ['altcode_1', 'altcode_2', 'chain_1', 'chain_2', 'ent_1', 'ent_2', 'said_1', 'said_2',
                                  'icode_1', 'icode_2', ]
            pdbRestrTable = pdbRestrTable.drop(columns=columnsToDropOff, axis=1)

            pdbRestrTable['violation'] = pd.to_numeric(pdbRestrTable['violation'], errors='coerce')

            return pdbRestrTable


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
                self.pathData.setText('/Users/eliza/Documents/e_projects/NEF-work/wwpdb_validation/it3/1pqx/D_9100060832_val-data_P1.xml')
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
                        _data = TableFrame(getViolationTable(xroot))
                        self.project.newDataTable(name=self.violName.text(), data=_data, comment='violated restraints from PDB')

                    if self.checkBox1.isChecked():
                        tempRama = getRamachandranTable(xroot)
                        _data = TableFrame(tempRama)
                        tempGrp = TableFrame(tempRama.groupby(by = ['chain','resnum','said','ent', 'seq','resname'])['rama'].value_counts())

                        self.project.newDataTable(name=self.ramaName.text(), data=_data, comment='ramachandran data from PDB')
                        self.project.newDataTable(name=self.ramaName.text()+'_process', data=tempGrp,
                                              comment='GroupedRamachandranData')

                    MessageDialog.showWarning('', 'Complete!')
                self.accept()

        if __name__ == '__main__':
            from ccpn.ui.gui.widgets.Application import TestApplication
            # app = TestApplication()
            popup = ImportPDBdataPopup(mainWindow=mainWindow)
            popup.show()
            popup.raise_()
            # app.start()
