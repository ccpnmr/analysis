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
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-10-12 15:27:12 +0100 (Wed, October 12, 2022) $"
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
import string
from PyQt5 import QtWidgets, QtCore

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Base import Base
from ccpn.framework.PathsAndUrls import macroPath as mp

# getting the currently implemented saveFrames for import
from ccpn.framework.lib.ccpnNmrStarIo.SaveFrameABC import getSaveFrames
sf_categories = getSaveFrames().keys()

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
    """
    A popup for the Star importer; allows for selection of saveFrames to be imported
    """

    CANCEL_PRESSED = 'cancel_pressed'
    IMPORT_PRESSED = 'import_pressed'

    def __init__(self, dataLoader, parent=None, title='Import From NMRSTAR', **kwds):

        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.dataLoader = dataLoader
        self.dataBlock = dataLoader.dataBlock or {}

        row = 0
        bmrbFileLabel = Label(self, text="NmrStar File", grid=(row, 0))
        self.fileName = LineEdit(self, text=str(dataLoader.path), grid=(row, 1),
                                 textAlignment='l', editable=False
                                 )

        row += 1
        tree = Label(self, text="Frames", grid=(row, 0))
        selectableItems = [key for key, value in self.dataBlock.items() if value.category in sf_categories]
        self.treeView = TreeCheckBoxes(self,
                                       orderedDataDict=self.dataBlock,
                                       checkList=list(self.dataBlock.keys()),
                                       selectableItems=selectableItems,
                                       grid=(row, 1))
        self._limitFunctionalities()

        row += 1
        # Make a list of possible chainCodes, removing those already in use for Chain and NmrChain
        _chains = list(
                  set(string.ascii_uppercase) - \
                  set(chain.name for chain in dataLoader.project.chains) - \
                  set(chain.name for chain in dataLoader.project.nmrChains)
        )
        _chains.sort()
        _chains = [''] + _chains

        Label(self, text="Set NmrChain/Chain", grid=(row, 0))
        self._chainCodeEdit = PulldownList(self,
                                           texts=_chains,
                                           grid=(row, 1)
                                          )

        row += 1
        self.buttonList = ButtonList(self, ['Cancel', 'Import'], [self._cancelButtonCallback, self._importButtonCallback], grid=(row, 1))

        self.chainCode = None  # set from the _chainCodeEdit widget
        self.result = None  # set by button callback functions

    def _limitFunctionalities(self):
        """Only check the boxes that current are supported"""
        self.treeView._uncheckAll()
        selectedOnly = []
        for key, value in self.dataBlock.items():
            if value.category in sf_categories:
                selectedOnly.append(key)
        self.treeView.selectObjects(selectedOnly)

    def _importButtonCallback(self):
        """Pressed Import
        Prepare the datablock for the loading. Keep only what selected from the gui; i.e. deleting all non-selected
        saveFrame's from the dataBlock
        The actual data loading doesn't happen here but in the DataLoader..
        """
        selectedItems = self.treeView.getSelectedItems()
        keysToDelete = [key for key in self.dataBlock.keys() if key not in selectedItems]
        for key in keysToDelete:
            del(self.dataBlock[key])

        if (chainCode := self._chainCodeEdit.getText()) and len(chainCode) > 0:
            self.dataLoader.starReader.setChainCode(chainCode)

        self.result = self.IMPORT_PRESSED
        self.accept()

    def _cancelButtonCallback(self):
        """Pressed cancel
        """
        self.result = self.CANCEL_PRESSED
        self.reject()

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
