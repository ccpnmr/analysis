"""
A Pre-alpha BMRB Chemical Shift List Importer from NMR-STAR v3.1.
This is not a full BMRB importer to Analysis V3.
Please, read warnings and info message

Usage:
    UI
    - Menu Menus > Macro > Run... > Select this file.py
    - select BMRB file  of interest
    - select entries
    - Create
    Non-UI:
    - scroll down to "Init the macro section"
    - replace filename path and axesCodesMap accordingly
    - run the macro within V3

1) Menu Menus > Macro > Run... > Select this file.py
2) Menu Menus > View PythonConsole (space-space)
                %run -i your/path/to/this/file.py (without quotes)

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:21 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca M $"
__date__ = "$Date: 2019-06-12 10:28:40 +0000 (Wed, Jun 12, 2019) $"
#=========================================================================================
# Start of code
#=========================================================================================

_UI = True  # Default opens a popup for selecting the input and run the macro

Warnings = "Warning: This is a beta version of the NMR-Star (BMRB) Importer. It might not work or work partially. Always inspect the results!"

InfoMessage = """
        This popup will create a new chemical shift list from the NMR-STAR v3.1 file selected.
        A new simulated Spectrum from the selected axesCodes and new simulated peakList from the selected BMRB Atom_ID. 
        Once the new assigned peaks are correctly imported, copy the new peakList to your target spectrum.
        
        >>> BMRB Atom_ID: Insert the NmrAtom which you want to import as appears in the BMRB file, comma separated. 
            You will find these on the "Assigned chemical shift lists" table in the BMRB 3.1 Star file as:
             _Atom_chem_shift.Atom_ID e.g. CA or HA 

        >>> Assign To Axis: Insert to which axis you want to assign the corresponding NmrAtom. 1:1
            These axes will be used to create a Simulated Spectrum. Specifying the axes is important for V3 for creating a new assignment,
             especially for ambiguous assignemnts: e.g   
             NmrAtom    -->   Axis Code
              HA        -->     H1
              HB        -->     H2

        
        Limitations: 
        - Import multiple combination of nmrAtoms for same axisCode. 
          Work-around: import twice.
          E.g. first H,N,CA after H,N,CB, copy the two peakList to the target spectrum
        - Peaks and assignments will be created only if all the selected nmrAtoms are present for the nmrResidue in the BMRB.
          E.g  if select Atom_ID: N,H for this BMRB entry:
          >>1 . 1 1   1   1 MET H  C 13  53.890 0.05 . 1 . . . . . . . . 5493 1 >> 
            4 . 1 1   2   2 ILE N  N 15 126.655 0.04 . 1 . . . . . . . . 5493 1
            5 . 1 1   2   2 ILE H  H  1  10.051 0.02 . 1 . . . . . . . . 5493 1
           The residue 1 MET will be skipped as only the Atom_ID H is found.  
            
    """


#######################################
##############  GUI POPUP #############
#######################################
from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.MessageDialog import showWarning, showInfo
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.FileDialog import LineEditButtonDialog
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.CheckBox import CheckBox
import pandas as pd
import os
import glob
import numpy as np
from collections import OrderedDict as od
from ccpn.util.Common import getAxisCodeMatchIndices
from ccpn.framework.PathsAndUrls import macroPath as mp
from ccpn.core.lib.ContextManagers import undoBlock


assigned_chem_shift_list = 'assigned_chem_shift_list'
shift_set = 'shift_set'
recognisedValues = [assigned_chem_shift_list, shift_set]

defaultAxesCodesMap = od([                           #                   replace with the atom and axes of interest
                            ("N", "N"),
                            ("H", "H"),
                            # ("CA", "C"),
                            ])


class TreeCheckBoxes(QtWidgets.QTreeWidget, Base):
    def __init__(self, parent=None, orderedDataDict=None,checkList=None,selectableItems=None, maxSize=(250, 300), **kwds):
        """Initialise the widget
        """
        super().__init__(parent)
        Base._init(self, setLayout=False, **kwds)

        # self.setMaximumSize(*maxSize)
        self.checkList = checkList or []
        self.selectableItems = selectableItems or []
        self.headerItem = QtWidgets.QTreeWidgetItem()
        self.item = QtWidgets.QTreeWidgetItem()
        self.orderedDataDict = orderedDataDict or {}
        # self.header().hide()
        if self.orderedDataDict is not None:
            for name in self.checkList:
                if name in self.orderedDataDict:
                    item = QtWidgets.QTreeWidgetItem(self)
                    item.setText(0, name)
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
                    if isinstance(self.orderedDataDict.get(name), (list,tuple)):
                        for obj in self.orderedDataDict.get(name):
                            child = QtWidgets.QTreeWidgetItem(item)
                            child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                            child.setData(1, 0, obj)
                            child.setText(0, obj.pid)
                            child.setCheckState(0, QtCore.Qt.Unchecked)

                    item.setCheckState(0, QtCore.Qt.Checked)
                    item.setExpanded(False)
                    item.setDisabled(name not in self.selectableItems)

        self.itemClicked.connect(self._clicked)

    def getSelectedObjects(self):
        """Get selected objects from the check boxes
        """
        selectedObjects = []
        for item in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            if item.checkState(0) == QtCore.Qt.Checked:
                obj = item.data(1, 0)
                selectedObjects += [obj]
        return selectedObjects

    def getSelectedItems(self):
        """Get selected objects from the check boxes
        """
        selectedItems = []
        for item in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            if item.checkState(0) == QtCore.Qt.Checked:
                obj = item.data(1, 0)
                selectedItems += [item.text(0)]
        return selectedItems

    def getItems(self):
        """Get checked state of objects
        """
        selectedItems = {}
        for item in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            obj = item.data(1, 0)
            selectedItems[item.text(0)] = item.checkState(0)
        return selectedItems

    def getSelectedObjectsPids(self):
        """Get the pids of the selected objects
        """
        pids = []
        for item in self.getSelectedObjects():
            pids += [item.pid]
        return pids

    def selectObjects(self, texts):
        """handle changing the state of checkboxes
        """
        items = self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive)
        for item in items:
            if item.text(0) in texts:
                item.setCheckState(0, QtCore.Qt.Checked)

    def _clicked(self, *args):
        pass

    def _uncheckAll(self):
        """Clear all selection
        """
        for itemTree in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            itemTree.setCheckState(0, QtCore.Qt.Unchecked)
            for i in range(itemTree.childCount()):
                itemTree.child(i).setCheckState(0, QtCore.Qt.Unchecked)

class StarImporterPopup(CcpnDialog):

    def __init__(self, parent=None, axesCodesMap=None, bmrbFilePath = None, project=None, directory=None,
                 dataBlock=None, title='Import From NMRSTAR', **kw):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)
        self.bmrbFilePath = bmrbFilePath or ''
        self._axesCodesMap  = axesCodesMap or defaultAxesCodesMap # Ordered dict as od([("HA","H")]) see info for more
        self.directory = directory or ''
        self.project = project
        self.dataBlock = dataBlock or {}
        row = 0
        bmrbFileLabel = Label(self, text="BMRB File", grid=(row, 0))
        self.fileName = LineEdit(self, text=os.path.basename(self.bmrbFilePath), grid=(row, 1))
        self.fileName.setEnabled(False)
        # self.inputDialog = LineEditButtonDialog(self,textLineEdit=self.bmrbFilePath, directory=self.directory, grid=(row, 1))
        row += 1
        tree = Label(self, text="Frames", grid=(row, 0))
        self.treeView = TreeCheckBoxes(self,orderedDataDict=dataBlock, checkList=list(dataBlock.keys()),  grid=(row, 1))
        self._limititedFunctionalities()

        row += 1
        self.dynamicsWidgets = []
        createSimulatedPeakList = Label(self, text="Simulate Peaks From Atoms", grid=(row, 0))
        self.simulatePLCheckBox = CheckBox(self, checked=False, callback=self._showMapLabel, grid=(row, 1))

        row +=1
        self.bmrbCodes = Label(self, text="BMRB Atom_ID", grid=(row,0))
        self.bmrbCodesEntry = LineEdit(self, text=','.join(self._axesCodesMap.keys()), grid=(row, 1))
        row += 1
        self.assignToSpectumCodesLabel = Label(self, text="Assign To Axis", grid=(row,0))
        self.assignToSpectumCodes = LineEdit(self, text=','.join(self._axesCodesMap.values()), grid=(row, 1))
        self.dynamicsWidgets.extend([self.bmrbCodes, self.bmrbCodesEntry,
                                      self.assignToSpectumCodesLabel, self.assignToSpectumCodes])
        row += 1
        self.buttonList = ButtonList(self, ['Info','Cancel', 'Import'], [self._showInfo, self.reject, self._okButton], grid=(row, 1))

        self._showMapLabel(False)

    def _limititedFunctionalities(self):
        self.treeView._uncheckAll()
        chemicalShiftListOnly = []
        for i in list(self.dataBlock.keys()):
            if assigned_chem_shift_list in i:
                chemicalShiftListOnly.append(i)
            if shift_set in i:
                chemicalShiftListOnly.append(i)
        self.treeView.selectObjects(chemicalShiftListOnly)

    def _showMapLabel(self, value):
        self._togleVisibility(self.dynamicsWidgets, value)

    def _togleVisibility(self, ll:list=[], value:bool=True):
        for l in ll:
            l.setVisible(value)

    def _showInfo(self):
        showWarning(Warnings, InfoMessage)

    def _okButton(self):
        from ccpn.core.lib.CcpnStarIo import _importAndCreateV3Objs
        self._axesCodesMap.clear()
        bmrbFile = self.bmrbFilePath
        simulateSpectra = self.simulatePLCheckBox.get()
        bmrbCodes = self.bmrbCodesEntry.get().replace(" ","").split(',')
        assignToSpectumCodes = self.assignToSpectumCodes.get().replace(" ","").split(',')
        for bmrbCode, sac in zip(bmrbCodes,assignToSpectumCodes):
          self._axesCodesMap[bmrbCode]=sac
        success = _importAndCreateV3Objs(self.project, bmrbFile, self._axesCodesMap, simulateSpectra=simulateSpectra)
        if not success:
            showWarning('Import Failed', 'Check the log file/outputs for more info')
        self.accept()

############################################
##############  INIT the Macro  ############
############################################


if __name__ == "__main__":
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog
    from ccpn.util.nef import StarIo

    app = TestApplication()

    relativePath = os.path.join(mp, 'nmrStar3_1Examples')
    fileName = 'bmr17285.str'


    mybmrb = os.path.join(relativePath, fileName) # if not using UI:  replace with the full bmrb file path  of interest
    axesCodesMap = od([                           #                   replace with the atom and axes of interest
                            ("N", "N"),
                            ("H", "H"),
                            ("CA", "C"),
                            ])
    nmrDataExtent = StarIo.parseNmrStarFile(mybmrb)
    dataBlocks = list(nmrDataExtent.values())
    dataBlock = dataBlocks[0]

    if _UI:
        popup = StarImporterPopup(axesCodesMap=axesCodesMap, bmrbFilePath=mybmrb,dataBlock=dataBlock, directory=relativePath)
        popup.show()
        popup.raise_()
        app.start()