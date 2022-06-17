"""
A BMRB Chemical Shift List Importer from NMR-STAR v3.1.
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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-06-17 10:49:42 +0100 (Fri, June 17, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca M $"
__date__ = "$Date: 2019-06-12 10:28:40 +0000 (Wed, Jun 12, 2019) $"
#=========================================================================================
# Start of code
#=========================================================================================



import os
from PyQt5 import QtWidgets, QtCore
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.Base import Base
from ccpn.framework.PathsAndUrls import macroPath as mp


ASSIGNED_CHEMICAL_SHIFTS = 'assigned_chemical_shifts'
sf_categories =  (ASSIGNED_CHEMICAL_SHIFTS,)

InfoMessage = "This popup will create a new chemical shift list from the selected NMR-STAR v3.1 file."

class TreeCheckBoxes(QtWidgets.QTreeWidget, Base):
    def __init__(self, parent=None, orderedDataDict=None, checkList=None, selectableItems=None, **kwds):
        super().__init__(parent)
        Base._init(self, setLayout=False, **kwds)
        self.checkList = checkList or []
        self.selectableItems = selectableItems or []
        self.headerItem = QtWidgets.QTreeWidgetItem()
        self.item = QtWidgets.QTreeWidgetItem()
        self.orderedDataDict = orderedDataDict or {}
        if self.orderedDataDict is not None:
            for name in self.checkList:
                if name in self.orderedDataDict:
                    item = QtWidgets.QTreeWidgetItem(self)
                    item.setText(0, name)
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
                    if isinstance(self.orderedDataDict.get(name), (list, tuple)):
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
        selectedObjects = []
        for item in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            if item.checkState(0) == QtCore.Qt.Checked:
                obj = item.data(1, 0)
                selectedObjects += [obj]
        return selectedObjects

    def getSelectedItems(self):
        selectedItems = []
        for item in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            if item.checkState(0) == QtCore.Qt.Checked:
                obj = item.data(1, 0)
                selectedItems += [item.text(0)]
        return selectedItems

    def getItems(self):
        selectedItems = {}
        for item in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            obj = item.data(1, 0)
            selectedItems[item.text(0)] = item.checkState(0)
        return selectedItems

    def getSelectedObjectsPids(self):
        pids = []
        for item in self.getSelectedObjects():
            pids += [item.pid]
        return pids

    def selectObjects(self, texts):
        items = self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive)
        for item in items:
            if item.text(0) in texts:
                item.setCheckState(0, QtCore.Qt.Checked)

    def _clicked(self, *args):
        pass

    def _uncheckAll(self):
        """Clear all selection"""
        for itemTree in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            itemTree.setCheckState(0, QtCore.Qt.Unchecked)
            for i in range(itemTree.childCount()):
                itemTree.child(i).setCheckState(0, QtCore.Qt.Unchecked)


class StarImporterPopup(CcpnDialog):

    def __init__(self, parent=None, bmrbFilePath=None, project=None, directory=None,
                 dataBlock=None, title='Import From NMRSTAR', **kw):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)
        self.bmrbFilePath = bmrbFilePath or ''
        self.directory = directory or ''
        self.project = project
        self.dataBlock = dataBlock or {}

        row = 0
        bmrbFileLabel = Label(self, text="BMRB File", grid=(row, 0))
        self.fileName = LineEdit(self, text=os.path.basename(self.bmrbFilePath), grid=(row, 1))
        self.fileName.setEnabled(False)

        row += 1
        tree = Label(self, text="Frames", grid=(row, 0))
        selectableItems = [key for key, value in dataBlock.items() if value.category in sf_categories]
        self.treeView = TreeCheckBoxes(self, orderedDataDict=dataBlock,
                                       checkList=list(dataBlock.keys()),
                                       selectableItems=selectableItems,
                                       grid=(row, 1))
        self._limitFunctionalities()
        row += 1
        self.buttonList = ButtonList(self, ['Cancel', 'Import'], [self.reject, self._okButton], grid=(row, 1))

    def _limitFunctionalities(self):
        """Only check the boxes that current are supported"""
        self.treeView._uncheckAll()
        chemicalShiftListOnly = []
        for key, value in self.dataBlock.items():
            if value.category == ASSIGNED_CHEMICAL_SHIFTS:
                chemicalShiftListOnly.append(key)
        self.treeView.selectObjects(chemicalShiftListOnly)

    def _okButton(self):
        """Prepare the datablock for the loading. Keep only what selected from the gui.
        The actual data loading doesn't happen here but in the DataLoader."""
        selectedItems = self.treeView.getSelectedItems()
        keysToDelete = [key for key in self.dataBlock.keys() if key not in selectedItems]
        for key in keysToDelete:
            del(self.dataBlock[key])
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
    mybmrb = os.path.join(relativePath, fileName)
    nmrDataExtent = StarIo.parseNmrStarFile(mybmrb)
    dataBlocks = list(nmrDataExtent.values())
    dataBlock = dataBlocks[0]

    popup = StarImporterPopup(bmrbFilePath=mybmrb, dataBlock=dataBlock, directory=relativePath)
    popup.show()
    popup.raise_()
    app.start()
