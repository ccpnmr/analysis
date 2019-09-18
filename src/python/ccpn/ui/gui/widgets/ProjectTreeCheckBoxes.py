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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:26 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.Base import Base
from ccpn.core.Chain import Chain
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.RestraintList import RestraintList
from ccpn.core.PeakList import PeakList
from ccpn.core.IntegralList import IntegralList
from ccpn.core.MultipletList import MultipletList
from ccpn.core.PeakCluster import PeakCluster
from ccpn.core.Sample import Sample
from ccpn.core.Substance import Substance
from ccpn.core.NmrChain import NmrChain
from ccpn.core.DataSet import DataSet
from ccpn.core.Complex import Complex
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.Note import Note


# TODO These should maybe be consolidated with the same constants in CcpnNefIo
# (and likely those in Project)
CHAINS = 'chains'
NMRCHAINS = 'nmrChains'
RESTRAINTLISTS = 'restraintLists'
CCPNTAG = 'ccpn'
SKIPPREFIXES = 'skipPrefixes'
EXPANDSELECTION = 'expandSelection'
SPECTRA = 'spectra'


class ProjectTreeCheckBoxes(QtWidgets.QTreeWidget, Base):
    """Class to handle exporting project to Nef file
    """

    # set the items in the project that can be exported
    checkList = [
        Chain._pluralLinkName,
        ChemicalShiftList._pluralLinkName,
        RestraintList._pluralLinkName,
        PeakList._pluralLinkName,
        IntegralList._pluralLinkName,
        MultipletList._pluralLinkName,
        Sample._pluralLinkName,
        Substance._pluralLinkName,
        NmrChain._pluralLinkName,
        DataSet._pluralLinkName,
        Complex._pluralLinkName,
        SpectrumGroup._pluralLinkName,
        Note._pluralLinkName,
        PeakCluster._pluralLinkName,
        ]

    # set which items can be selected/deselected, others are automatically set
    selectableItems = [
        Chain._pluralLinkName,
        ChemicalShiftList._pluralLinkName,
        RestraintList._pluralLinkName,
        NmrChain._pluralLinkName,
        PeakList._pluralLinkName,
        IntegralList._pluralLinkName,
        MultipletList._pluralLinkName,
        PeakCluster._pluralLinkName,
        ]

    lockedItems = {
        Sample._pluralLinkName: QtCore.Qt.Checked,
        Substance._pluralLinkName: QtCore.Qt.Checked,
        DataSet._pluralLinkName: QtCore.Qt.Checked,
        Complex._pluralLinkName: QtCore.Qt.Checked,
        SpectrumGroup._pluralLinkName: QtCore.Qt.Checked,
        Note._pluralLinkName: QtCore.Qt.Checked
        }

    def __init__(self, parent=None, project=None, maxSize=(250, 300), includeProject=False, **kwds):
        """Initialise the widget
        """
        super().__init__(parent)
        Base._init(self, setLayout=False, **kwds)

        # self.setMaximumSize(*maxSize)
        self.headerItem = self.invisibleRootItem()  # QtWidgets.QTreeWidgetItem()
        self.projectItem = None
        self.project = project
        self.header().hide()
        if self.project is not None:

            if includeProject:
                # add the project as the top of the tree - allows to un/select all
                self.projectItem = QtWidgets.QTreeWidgetItem(self.invisibleRootItem())
                self.projectItem.setText(0, project.name)
                self.projectItem.setFlags(self.projectItem.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
                self.projectItem.setExpanded(True)
                self.headerItem = self.projectItem

            for name in self.checkList:
                if hasattr(self.project, name):  # just to be safe
                    item = QtWidgets.QTreeWidgetItem(self.headerItem)
                    item.setText(0, name)
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)

                    for obj in getattr(self.project, name):
                        child = QtWidgets.QTreeWidgetItem(item)
                        child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                        child.setData(1, 0, obj)
                        child.setText(0, obj.pid)
                        child.setCheckState(0, QtCore.Qt.Unchecked)

                    item.setExpanded(False)
                    if name in self.lockedItems:
                        item.setDisabled(True)
                        item.setCheckState(0, self.lockedItems[name])
                    else:
                        item.setCheckState(0, QtCore.Qt.Checked)

        self.itemClicked.connect(self._clicked)

    def getSelectedObjects(self, includeRoot=False):
        """Get selected objects from the check boxes
        """
        selectedObjects = []

        for item in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            if item.checkState(0) == QtCore.Qt.Checked:
                obj = item.data(1, 0)

                # return items in the tree that have a pid
                if hasattr(obj, 'pid'):
                    if self.projectItem and item == self.projectItem and not includeRoot:
                        continue

                    selectedObjects += [obj]

        return selectedObjects

    def getSelectedItems(self, includeRoot=False):
        """Get selected objects from the check boxes
        """
        selectedItems = []

        for item in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            if item.checkState(0) == QtCore.Qt.Checked:
                obj = item.data(1, 0)

                # return items in the tree that are group labels (bottom level should be objects with pids)
                if not hasattr(obj, 'pid'):
                    if self.projectItem and item == self.projectItem and not includeRoot:
                        continue
                    selectedItems += [item.text(0)]

        return selectedItems

    def getSelectedPids(self, includeRoot=False):
        """Get checked text items from the tree for items that have a Pid
        """
        selectedItems = []

        for item in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            if item.checkState(0) == QtCore.Qt.Checked:
                obj = item.data(1, 0)

                # return items in the tree that are group labels (bottom level should be objects with pids)
                if hasattr(obj, 'pid'):
                    if self.projectItem and item == self.projectItem and not includeRoot:
                        continue
                    selectedItems += [item.text(0)]

        return selectedItems

    def getCheckStateItems(self, includeRoot=False):
        """Get checked state of objects
        """
        selectedItems = {}
        for item in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            obj = item.data(1, 0)

            # return checkstate of items in the tree that are group labels (bottom level should be objects with pids)
            if not hasattr(obj, 'pid'):
                if self.projectItem and item == self.projectItem and not includeRoot:
                    continue

                selectedItems[item.text(0)] = item.checkState(0)

        return selectedItems

    def getSelectedObjectsPids(self, includeRoot=False):
        """Get the pids of the selected objects
        """
        pids = []
        for item in self.getSelectedObjects(includeRoot=includeRoot):
            pids += [item.pid]
        return pids

    def selectObjects(self, pids):
        """Handle changing the state of checkboxes
        """
        items = self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive)
        for item in items:
            if item.text(0) in pids:
                item.setCheckState(0, QtCore.Qt.Checked)

    def _clicked(self, *args):
        for item in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            if item.text(0) in self.lockedItems:
                item.setCheckState(0, self.lockedItems[item.text(0)])

    def _uncheckAll(self, includeRoot=False):
        """Clear all selection
        """
        for itemTree in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            for i in range(itemTree.childCount()):
                itemTree.child(i).setCheckState(0, QtCore.Qt.Unchecked)


class PrintTreeCheckBoxes(ProjectTreeCheckBoxes):
    """Class to handle exporting peaks/integrals/multiplets to PDF or SVG files
    """

    # set the items in the project that can be printed
    checkList = []
    # SPECTRA,
    # PeakList._pluralLinkName,
    # IntegralList._pluralLinkName,
    # MultipletList._pluralLinkName,
    # ]

    # all items can be selected
    selectableItems = []

    # SPECTRA,
    # PeakList._pluralLinkName,
    # IntegralList._pluralLinkName,
    # MultipletList._pluralLinkName,
    # ]

    lockedItems = {}

    def __init__(self, parent=None, project=None, maxSize=(250, 300), **kwds):
        super(PrintTreeCheckBoxes, self).__init__(parent=parent, project=project, maxSize=maxSize, **kwds)
