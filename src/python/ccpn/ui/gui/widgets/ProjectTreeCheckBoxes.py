#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-12-03 10:01:42 +0000 (Thu, December 03, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt5 import QtGui, QtWidgets, QtCore
from functools import partial
from typing import List, Union, Optional, Sequence, Tuple
from collections import OrderedDict as OD
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
from ccpn.core.Project import Project
from ccpn.ui.gui.guiSettings import getColours, BORDERFOCUS, BORDERNOFOCUS
from ccpn.util.nef import Specification
from ccpn.util.nef import StarIo
from ccpn.util.OrderedSet import OrderedSet
from ccpnmodel.ccpncore.lib import Constants as coreConstants
from ccpn.core.lib.CcpnNefCommon import _traverse, nef2CcpnMap, _isALoop
from ccpn.ui.gui.widgets.Menu import Menu


# TODO These should maybe be consolidated with the same constants in CcpnNefIo
# (and likely those in Project)
CHAINS = 'chains'
NMRCHAINS = 'nmrChains'
RESTRAINTLISTS = 'restraintLists'
CCPNTAG = 'ccpn'
SKIPPREFIXES = 'skipPrefixes'
EXPANDSELECTION = 'expandSelection'
SPECTRA = 'spectra'
RENAMEACTION = 'rename'
BADITEMACTION = 'badItem'


class ProjectTreeCheckBoxes(QtWidgets.QTreeWidget, Base):
    """Class to handle a tree view created from a project
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
        # Sample._pluralLinkName       : QtCore.Qt.Checked,
        # Substance._pluralLinkName    : QtCore.Qt.Checked,
        # DataSet._pluralLinkName      : QtCore.Qt.Checked,
        # Complex._pluralLinkName      : QtCore.Qt.Checked,
        # SpectrumGroup._pluralLinkName: QtCore.Qt.Checked,
        # Note._pluralLinkName         : QtCore.Qt.Checked
        }

    def __init__(self, parent=None, project=None, maxSize=(250, 300),
                 includeProject=False, enableCheckBoxes=True, multiSelect=False,
                 enableMouseMenu=False, pathName=None,
                 **kwds):
        """Initialise the widget
        """
        super().__init__(parent)
        Base._init(self, setLayout=False, **kwds)

        # self.setMaximumSize(*maxSize)
        self.headerItem = self.invisibleRootItem()  # QtWidgets.QTreeWidgetItem()
        self.projectItem = None
        self.project = project
        self.includeProject = includeProject
        self._enableCheckBoxes = enableCheckBoxes
        self._enableMouseMenu = enableMouseMenu
        self._pathName = pathName
        self._currentContextMenu = None

        self.multiSelect = multiSelect
        if self.multiSelect:
            self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.header().hide()
        if self.project is not None:
            self._populateTreeView()

        self.itemClicked.connect(self._clicked)

        self._actionCallbacks = {}

        self._setFocusColour()
        self._backgroundColour = self.invisibleRootItem().background(0)
        self._foregroundColour = self.invisibleRootItem().foreground(0)

    def setActionCallback(self, name, func=None):
        """Add an action to the callback dict
        """
        if name:
            if func:
                self._actionCallbacks[name] = func
            else:
                if name in self._actionCallbacks:
                    del self._actionCallbacks[name]

    def clearActionCallbacks(self):
        """Clear the action callback dict
        """
        self._actionCallback = {}

    def setBackgroundForRow(self, item, colour):
        """Set the background colour for all items in the row
        """
        # NOTE:ED - this works for most of the row, not the left-hand side yet
        for col in range(self.columnCount()):
            item.setBackground(col, colour)

    def setForegroundForRow(self, item, colour):
        """Set the foreground colour for all items in the row
        """
        # NOTE:ED - this works for most of the row, not the left-hand side yet
        for col in range(self.columnCount()):
            item.setForeground(col, colour)

    def _populateTreeView(self, project=None):
        if project:
            # set the new project if required
            self.project = project

        checkable = QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable
        if self.includeProject:
            # add the project as the top of the tree - allows to un/select all
            self.projectItem = QtWidgets.QTreeWidgetItem(self.invisibleRootItem())
            self.projectItem.setText(0, self.project.name)
            if self._enableCheckBoxes:
                self.projectItem.setFlags(self.projectItem.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
            else:
                self.projectItem.setFlags(self.projectItem.flags() & ~(QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable))
            self.projectItem.setExpanded(True)
            self.headerItem = self.projectItem

        for name in self.checkList:
            if hasattr(self.project, name):  # just to be safe
                item = QtWidgets.QTreeWidgetItem(self.headerItem)
                item.setText(0, name)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)

                for obj in getattr(self.project, name):
                    child = QtWidgets.QTreeWidgetItem(item)
                    if self._enableCheckBoxes:
                        child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                    else:
                        child.setFlags(child.flags() & ~QtCore.Qt.ItemIsUserCheckable)
                    child.setData(1, 0, obj)
                    child.setText(0, obj.pid)
                    if self._enableCheckBoxes:
                        child.setCheckState(0, QtCore.Qt.Unchecked)

                item.setExpanded(False)
                if name in self.lockedItems:
                    item.setDisabled(True)
                    if self._enableCheckBoxes:
                        item.setCheckState(0, self.lockedItems[name])
                else:
                    if self._enableCheckBoxes:
                        item.setCheckState(0, QtCore.Qt.Checked)

    def _setFocusColour(self, focusColour=None, noFocusColour=None):
        """Set the focus/noFocus colours for the widget
        """
        focusColour = getColours()[BORDERFOCUS]
        noFocusColour = getColours()[BORDERNOFOCUS]
        styleSheet = "QTreeWidget { " \
                     "border: 1px solid;" \
                     "border-radius: 1px;" \
                     "border-color: %s;" \
                     "} " \
                     "QTreeWidget:focus { " \
                     "border: 1px solid %s; " \
                     "border-radius: 1px; " \
                     "}" % (noFocusColour, focusColour)
        self.setStyleSheet(styleSheet)

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
        if self._enableCheckBoxes:
            items = self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive)
            for item in items:
                if item.text(0) in pids:
                    item.setCheckState(0, QtCore.Qt.Checked)

    def _clicked(self, *args):
        if self._enableCheckBoxes:
            for item in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
                if item.text(0) in self.lockedItems:
                    item.setCheckState(0, self.lockedItems[item.text(0)])

    def _uncheckAll(self, includeRoot=False):
        """Clear all selection
        """
        if self._enableCheckBoxes:
            for itemTree in self.findItems('', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
                for i in range(itemTree.childCount()):
                    itemTree.child(i).setCheckState(0, QtCore.Qt.Unchecked)

    def traverseTree(self, root=None, preOrder=True, childrenOnly=True):
        """Traverse the tree items in preOrder/postOrder
        InOrder does not apply as the tree currently does not have left/right branches

        :param root: root of the tree, if None defaults to the invisibleRootItem
        :param preOrder: True/False; True yields the nodes first
        :param childrenOnly: True/False; only yield items that are at the bottom of a branch,
                            i.e., no further descendents
        :return: yields tree items at each iteration
        """

        def recurse(parent):
            for chCount in range(parent.childCount()):
                child = parent.child(chCount)
                # if preOrder then yield the node first
                if preOrder and (child.childCount() == 0 or not childrenOnly):
                    yield child
                if child.childCount():
                    yield from recurse(child)
                # if preOrder then yield the node last
                if not preOrder and (child.childCount() == 0 or not childrenOnly):
                    yield child

        root = root or self.invisibleRootItem()
        if root is not None:
            yield from recurse(root)

    def mouseReleaseEvent(self, event):
        """Re-implementation of the mouse press event so right click can be used to delete items from the
        sidebar.
        """
        if event.button() == QtCore.Qt.RightButton and self._enableMouseMenu:
            self.raiseContextMenu(event)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def raiseContextMenu(self, ev):
        """Handle raising  context menu for a treeview object
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")


class ExportTreeCheckBoxes(ProjectTreeCheckBoxes):
    """Class to handle exporting peaks/integrals/multiplets to nef files
    """
    pass


class ImportTreeCheckBoxes(ProjectTreeCheckBoxes):
    """Class to handle importing peaks/integrals/multiplets from nef files
    """
    # set which items can be selected/deselected, others are automatically set
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
        'restraintLinks',
        ]

    lockedItems = {
        }

    nefToTreeViewMapping = {
        # 'nef_sequence': Chain._pluralLinkName,
        'nef_sequence_chain_code'    : (Chain._pluralLinkName, Chain.className),
        'nef_chemical_shift_list'    : (ChemicalShiftList._pluralLinkName, ChemicalShiftList.className),
        'nef_distance_restraint_list': (RestraintList._pluralLinkName, RestraintList.className),
        'nef_dihedral_restraint_list': (RestraintList._pluralLinkName, RestraintList.className),
        'nef_rdc_restraint_list'     : (RestraintList._pluralLinkName, RestraintList.className),
        'ccpn_restraint_list'        : (RestraintList._pluralLinkName, RestraintList.className),
        # 'nef_nmr_spectrum': PeakList._pluralLinkName,XXXXX.className),
        'nef_peak'                   : (PeakList._pluralLinkName, PeakList.className),
        'ccpn_integral_list'         : (IntegralList._pluralLinkName, IntegralList.className),
        'ccpn_multiplet_list'        : (MultipletList._pluralLinkName, MultipletList.className),
        'ccpn_sample'                : (Sample._pluralLinkName, Sample.className),
        'ccpn_substance'             : (Substance._pluralLinkName, Substance.className),
        # 'ccpn_assignment': NmrChain._pluralLinkName,XXXXX.className),
        'nmr_chain'                  : (NmrChain._pluralLinkName, NmrChain.className),
        'ccpn_dataset'               : (DataSet._pluralLinkName, DataSet.className),
        'ccpn_complex'               : (Complex._pluralLinkName, Complex.className),
        'ccpn_spectrum_group'        : (SpectrumGroup._pluralLinkName, SpectrumGroup.className),
        'ccpn_notes'                 : (Note._pluralLinkName, Note.className),
        'ccpn_peak_cluster'          : (PeakCluster._pluralLinkName, PeakCluster.className),
        # 'ccpn_peak_cluster_serial'          : (PeakCluster._pluralLinkName, PeakCluster.className),
        'nef_peak_restraint_links'   : ('restraintLinks','RestraintLink')
        }

    # defines the names of the saveframe loops that are displayed
    nefProjectToSaveFramesMapping = {
        # Chain._pluralLinkName : [],
        Chain._pluralLinkName            : ['nef_sequence'],
        ChemicalShiftList._pluralLinkName: ['nef_chemical_shift_list', 'nef_chemical_shift'],
        RestraintList._pluralLinkName    : ['nef_distance_restraint_list', 'nef_distance_restraint',
                                            'nef_dihedral_restraint_list', 'nef_dihedral_restraint',
                                            'nef_rdc_restraint_list', 'nef_rdc_restraint',
                                            'ccpn_restraint_list', 'ccpn_restraint'],
        PeakList._pluralLinkName         : ['ccpn_peak_list', 'nef_peak', 'nef_spectrum_dimension', 'nef_spectrum_dimension_transfer'],
        IntegralList._pluralLinkName     : ['ccpn_integral_list', 'ccpn_integral'],
        MultipletList._pluralLinkName    : ['ccpn_multiplet_list', 'ccpn_multiplet', 'ccpn_multiplet_peaks'],
        Sample._pluralLinkName           : ['ccpn_sample', 'ccpn_sample_component'],
        Substance._pluralLinkName        : ['ccpn_substance'],
        NmrChain._pluralLinkName         : ['nmr_chain', 'nmr_residue', 'nmr_atom'],
        # TODO:ED - not done yet
        DataSet._pluralLinkName          : [],
        Complex._pluralLinkName          : ['ccpn_complex', 'ccpn_complex_chain'],
        SpectrumGroup._pluralLinkName    : ['ccpn_spectrum_group', 'ccpn_group_spectrum'],
        Note._pluralLinkName             : ['ccpn_note'],
        PeakCluster._pluralLinkName      : ['ccpn_peak_cluster_list', 'ccpn_peak_cluster', 'ccpn_peak_cluster_peaks'],
        'restraintLinks'                 : ['nef_peak_restraint_link'],
        }

    nefProjectToHandlerMapping = {
        # Chain._pluralLinkName : [],
        Chain._pluralLinkName            : 'nef_sequence',
        ChemicalShiftList._pluralLinkName: None,
        RestraintList._pluralLinkName    : None,
        PeakList._pluralLinkName         : 'ccpn_peak_list',
        IntegralList._pluralLinkName     : 'ccpn_integral_list',
        MultipletList._pluralLinkName    : 'ccpn_multiplet_list',
        Sample._pluralLinkName           : None,
        Substance._pluralLinkName        : None,
        NmrChain._pluralLinkName         : 'nmr_chain',
        # TODO:ED - not done yet
        DataSet._pluralLinkName          : None,
        Complex._pluralLinkName          : None,
        SpectrumGroup._pluralLinkName    : None,
        Note._pluralLinkName             : 'ccpn_note',
        PeakCluster._pluralLinkName      : None,
        'restraintLinks'                 : None,
        }

    contents = {}

    def _populateTreeView(self, project=None):
        # clear old items - needed for testing without mainWindow
        self.clear()

        if project:
            # set the new project if required
            self.project = project

        if self.includeProject:
            # add the project as the top of the tree - allows to un/select all
            self.projectItem = QtWidgets.QTreeWidgetItem(self.invisibleRootItem())
            if self._pathName:
                self.projectItem.setText(0, self._pathName)
            else:
                self.projectItem.setText(0, self.project.name)
            if self._enableCheckBoxes:
                self.projectItem.setFlags(self.projectItem.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
                # self.projectItem.setCheckState(0, QtCore.Qt.Unchecked)
            else:
                self.projectItem.setFlags(self.projectItem.flags() & ~(QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable))
            self.projectItem.setExpanded(True)
            self.headerItem = self.projectItem

        for name in self.checkList:
            if hasattr(self.project, name) or True:  # just to be safe
                item = QtWidgets.QTreeWidgetItem(self.headerItem)
                item.setText(0, name)
                if self._enableCheckBoxes:
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
                    # self.headerItem.setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.setFlags(item.flags() & ~(QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable))

                # # keep for future reference
                # for obj in getattr(self.project, name):
                #     child = QtWidgets.QTreeWidgetItem(item)
                #     child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                #     child.setData(1, 0, obj)
                #     child.setText(0, obj.pid)
                #     child.setCheckState(0, QtCore.Qt.Unchecked)

                item.setExpanded(False)
                if name in self.lockedItems:
                    item.setDisabled(True)
                    if self._enableCheckBoxes:
                        item.setCheckState(0, self.lockedItems[name])
                else:
                    if self._enableCheckBoxes:
                        item.setCheckState(0, QtCore.Qt.Unchecked)

    # NOTE:ED - define methods here to match CcpnNefIo
    def content_nef_molecular_system(self, project: Project, saveFrame: StarIo.NmrSaveFrame, saveFrameTag):
        self._contentLoops(project, saveFrame, saveFrameTag,  #name=spectrumName, itemLength=saveFrame['num_dimensions'],
                           )
        tag = 'nef_sequence_chain_code'
        content = self.contents[tag]
        content(self, project, saveFrame, tag)

    def content_nef_sequence(self, project: Project, loop: StarIo.NmrLoop, parentFrame: StarIo.NmrSaveFrame) -> OrderedSet:
        pass

    def content_nef_covalent_links(self, project: Project, loop: StarIo.NmrLoop, parentFrame: StarIo.NmrSaveFrame) -> OrderedSet:
        pass

    def _contentParent(self, project: Project, saveFrame: StarIo.NmrSaveFrame, saveFrameTag):
        try:
            category = saveFrameTag  #saveFrame['sf_category']
        except Exception as es:
            pass

        if hasattr(saveFrame, '_content') and category in saveFrame._content:
            thisList = saveFrame._content[category]
            treeItem, _ = self.nefToTreeViewMapping[category]
            found = self.findItems(treeItem, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            if found:
                if len(found) == 1:
                    return found[0]

    def content_list(self, project: Project, saveFrame: StarIo.NmrSaveFrame, saveFrameTag):
        try:
            category = saveFrameTag  #saveFrame['sf_category']
        except Exception as es:
            pass

        if hasattr(saveFrame, '_content') and category in saveFrame._content:
            thisList = saveFrame._content[category]
            treeItem, _ = self.nefToTreeViewMapping[category]
            found = self.findItems(treeItem, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            if found:
                if len(found) == 1:
                    # add to the tree

                    if self._enableCheckBoxes:
                        found[0].setCheckState(0, QtCore.Qt.Unchecked)

                    # NOTE:ED - this defines the list of items that are added to each plural group in the tree
                    #           i.e. Chains = saveFrame._content['chain_code'] from nefToTreeViewMapping
                    for listItem in thisList:
                        child = QtWidgets.QTreeWidgetItem(found[0])
                        if self._enableCheckBoxes:
                            child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                        else:
                            child.setFlags(child.flags() & ~QtCore.Qt.ItemIsUserCheckable)
                        child.setData(1, 0, saveFrame)
                        child.setText(0, str(listItem))
                        if self._enableCheckBoxes:
                            child.setCheckState(0, QtCore.Qt.Unchecked)

    def _contentLoops(self, project: Project, saveFrame: StarIo.NmrSaveFrame, saveFrameTag=None,
                      addLoopAttribs=None, excludeList=(), **kwds):
        """Iterate over the loops in a saveFrame, and add to results"""
        result = {}
        mapping = nef2CcpnMap.get(saveFrame.category) or {}
        for tag, ccpnTag in mapping.items():
            if tag not in excludeList and ccpnTag == _isALoop:
                loop = saveFrame.get(tag)
                if loop and tag in self.contents:
                    content = self.contents[tag]
                    if addLoopAttribs:
                        dd = []
                        for name in addLoopAttribs:
                            dd.append(saveFrame.get(name))
                        content(self, project, saveFrame, tag, *dd, **kwds)
                    else:
                        content(self, project, saveFrame, tag, **kwds)

    def content_nef_chemical_shift(self, parent: ChemicalShiftList, loop: StarIo.NmrLoop, parentFrame: StarIo.NmrSaveFrame) -> OrderedSet:
        # ll = parentFrame._content[parentFrame['sf_category']]
        pass

    def content_nef_restraint_list(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        pass

    def content_nef_restraint(self, restraintList: RestraintList, loop: StarIo.NmrLoop, parentFrame: StarIo.NmrSaveFrame,
                              itemLength: int = None) -> Optional[OrderedSet]:
        pass

    def content_nef_nmr_spectrum(self, project: Project, saveFrame: StarIo.NmrSaveFrame, saveFrameTag):
        self._contentLoops(project, saveFrame, saveFrameTag,  #name=spectrumName, itemLength=saveFrame['num_dimensions'],
                           )

    def content_ccpn_integral_list(self, project: Project, loop: StarIo.NmrLoop, parentFrame: StarIo.NmrSaveFrame,
                                   name=None, itemLength=None):
        pass

    def content_ccpn_multiplet_list(self, project: Project, loop: StarIo.NmrLoop, parentFrame: StarIo.NmrSaveFrame,
                                    name=None, itemLength=None):
        pass

    def content_ccpn_integral(self, project: Project, loop: StarIo.NmrLoop, parentFrame: StarIo.NmrSaveFrame,
                              name=None, itemLength=None):
        pass

    def content_ccpn_multiplet(self, project: Project, loop: StarIo.NmrLoop, parentFrame: StarIo.NmrSaveFrame,
                               name=None, itemLength=None):
        pass

    def content_ccpn_peak_cluster_list(self, project: Project, saveFrame: StarIo.NmrSaveFrame, saveFrameTag):
        self._contentLoops(project, saveFrame, saveFrameTag,  #name=spectrumName, itemLength=saveFrame['num_dimensions'],
                           )

    def content_nef_peak(self, peakList: PeakList, loop: StarIo.NmrLoop, parentFrame: StarIo.NmrSaveFrame,
                         name=None, itemLength: int = None):
        pass

    def content_ccpn_spectrum_group(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        pass

    def content_ccpn_complex(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        pass

    def content_ccpn_sample(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        pass

    def content_ccpn_substance(self, project: Project, saveFrame: StarIo.NmrSaveFrame):
        pass

    def content_ccpn_assignment(self, project: Project, saveFrame: StarIo.NmrSaveFrame, saveFrameTag):
        self._contentLoops(project, saveFrame, saveFrameTag,  #name=spectrumName, itemLength=saveFrame['num_dimensions'],
                           )

    def content_ccpn_notes(self, project: Project, saveFrame: StarIo.NmrSaveFrame, saveFrameTag):
        self._contentLoops(project, saveFrame, saveFrameTag,  #name=spectrumName, itemLength=saveFrame['num_dimensions'],
                           )

    contents['nef_molecular_system'] = content_nef_molecular_system
    # contents['nef_sequence'] = content_nef_sequence
    # NOTE:ED - to match nefmapping
    contents['nef_sequence_chain_code'] = content_list  # content_nef_sequence
    # contents['nef_covalent_links'] = content_nef_covalent_links
    contents['nef_chemical_shift_list'] = content_list  # content_nef_chemical_shift_list
    # contents['nef_chemical_shift'] = content_nef_chemical_shift

    contents['nef_distance_restraint_list'] = content_list  # content_nef_restraint_list  # could be _contentLoops
    contents['nef_dihedral_restraint_list'] = content_list  # content_nef_restraint_list
    contents['nef_rdc_restraint_list'] = content_list  # content_nef_restraint_list
    contents['ccpn_restraint_list'] = content_list  # content_nef_restraint_list

    # contents['nef_distance_restraint'] = partial(content_nef_restraint, itemLength=coreConstants.constraintListType2ItemLength.get('Distance'))
    # contents['nef_dihedral_restraint'] = partial(content_nef_restraint, itemLength=coreConstants.constraintListType2ItemLength.get('Dihedral'))
    # contents['nef_rdc_restraint'] = partial(content_nef_restraint, itemLength=coreConstants.constraintListType2ItemLength.get('Rdc'))
    # contents['ccpn_restraint'] = partial(content_nef_restraint, itemLength=coreConstants.constraintListType2ItemLength.get('Distance'))

    contents['nef_nmr_spectrum'] = content_ccpn_notes  # content_nef_nmr_spectrum
    contents['nef_peak'] = content_list

    contents['ccpn_integral_list'] = content_list  # content_ccpn_integral_list
    contents['ccpn_multiplet_list'] = content_list  # content_ccpn_multiplet_list
    # contents['ccpn_integral'] = content_ccpn_integral
    # contents['ccpn_multiplet'] = content_ccpn_multiplet
    contents['ccpn_peak_cluster_list'] = content_ccpn_peak_cluster_list
    contents['ccpn_peak_cluster'] = content_list
    # NOTE:ED - to match nefmapping
    # contents['ccpn_peak_cluster_serial'] = content_list

    contents['ccpn_spectrum_group'] = content_list  # content_ccpn_spectrum_group
    contents['ccpn_complex'] = content_list  # content_ccpn_complex
    contents['ccpn_sample'] = content_list  # content_ccpn_sample
    contents['ccpn_substance'] = content_list  # content_ccpn_substance

    contents['ccpn_assignment'] = content_ccpn_notes
    contents['nmr_chain'] = content_list

    contents['ccpn_notes'] = content_list  # content_ccpn_notes

    contents['nef_peak_restraint_links'] = content_list  # content_ccpn_notes

    def _fillFunc(self, project, saveFrame, *args, **kwds):
        saveFrameName = saveFrame['sf_category']
        if saveFrameName in self.contents:
            content = self.contents[saveFrameName]
            content(self, project, saveFrame, saveFrame['sf_category'])

    def fillTreeView(self, nefDict):
        _traverse(self, self.project, nefDict, traverseFunc=self._fillFunc)

    def findSection(self, value, _parent=None):
        """Find the required section in the tree
        """
        found = self.findItems(value, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
        if _parent:
            found = [item for item in found
                     if (isinstance(_parent, str) and item.parent() and item.parent().data(0, 0) == _parent) or
                     (isinstance(_parent, QtWidgets.QTreeWidgetItem) and item.parent() == _parent)]
        if found and len(found) == 1:
            return found[0]

    def getFirstChild(self):
        pass

    def raiseContextMenu(self, event: QtGui.QMouseEvent):
        """Creates and raises a context menu enabling items to be deleted from the sidebar.
        """
        menu = self._getContextMenu(event)
        if menu:
            menu.move(event.globalPos().x(), event.globalPos().y() + 10)
            menu.exec()

    def _getContextMenu(self, event):
        """Build a menu for renaming tree items
        """
        contextMenu = Menu('', self, isFloatWidget=True)

        _itemPressed = self.itemAt(event.pos())
        if _itemPressed.childCount() != 0 and len(self.selectedItems()) == 1:
            contextMenu.addItem("Autorename All Conflicts in Group", callback=partial(self._autoRenameAllConflicts, _itemPressed), enabled=True)
            contextMenu.addSeparator()
            contextMenu.addItem("Autorename All in Group", callback=partial(self._autoRenameAll, _itemPressed))
            contextMenu.addItem("Autorename Checked in Group", callback=partial(self._autoRenameSelected, _itemPressed))
            contextMenu.addSeparator()
        elif _itemPressed.childCount() == 0 and len(self.selectedItems()) == 1:
            contextMenu.addItem("Autorename", callback=partial(self._autoRenameSingle, _itemPressed), enabled=True)
            contextMenu.addSeparator()

        contextMenu.addItem("Check All Conflicts in Selection", callback=partial(self._checkSelected, True, conflictsOnly=True), enabled=True)
        contextMenu.addItem("Uncheck All Conflicts in Selection", callback=partial(self._checkSelected, False, conflictsOnly=True), enabled=True)
        contextMenu.addSeparator()
        contextMenu.addItem("Check Selected", callback=partial(self._checkSelected, True))
        contextMenu.addItem("Uncheck Selected", callback=partial(self._checkSelected, False))

        return contextMenu

    def _autoRename(self, groupItems, conflictsOnly=False):
        """Call the rename action on the child nodes
        """
        if RENAMEACTION in self._actionCallbacks:
            for childItem in groupItems:
                name, saveFrame, treeParent = childItem
                conflictCheck = True
                if conflictsOnly and BADITEMACTION in self._actionCallbacks:
                    conflictCheck = self._actionCallbacks[BADITEMACTION](name, saveFrame, treeParent)

                if conflictCheck:
                    self._actionCallbacks[RENAMEACTION](name, saveFrame, treeParent)

    def _autoRenameSingle(self, treeItem):
        """Tree item autorename all conflicts in subtree
        """
        children = [(child.data(0, 0), child.data(1, 0), child.parent().data(0, 0)) for child in (treeItem,)]
        self._autoRename(children)

    def _autoRenameAllConflicts(self, treeItem):
        """Tree item autorename all conflicts in subtree
        """
        children = [(child.data(0, 0), child.data(1, 0), child.parent().data(0, 0)) for child in self.traverseTree(treeItem)]
        self._autoRename(children, conflictsOnly=True)

    def _autoRenameAll(self, treeItem):
        """Tree item autorename all in subtree
        """
        children = [(child.data(0, 0), child.data(1, 0), child.parent().data(0, 0)) for child in self.traverseTree(treeItem)]
        self._autoRename(children)

    def _autoRenameSelected(self, treeItem):
        """Tree item autorename selected in subtree
        """
        children = [(child.data(0, 0), child.data(1, 0), child.parent().data(0, 0)) for child in self.traverseTree(treeItem) if
                    child.checkState(0) == QtCore.Qt.Checked]
        self._autoRename(children)

    def _checkSelected(self, checked, conflictsOnly=False):
        """Tree item check/uncheck selected
        """
        for item in self.selectedItems():
            conflictCheck = True
            if conflictsOnly and BADITEMACTION in self._actionCallbacks:
                name, saveFrame, treeParent = item.data(0, 0), item.data(1, 0), item.parent().data(0, 0) if item.parent() else repr(None)
                conflictCheck = self._actionCallbacks[BADITEMACTION](name, saveFrame, treeParent)

            if conflictCheck:
                item.setCheckState(0, QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)

    # def setContextMenu(self, menu):
    #     if isinstance(menu, Menu):
    #         self._currentContextMenu = menu
    #         return menu
    #     else:
    #         raise TypeError('not a correct menu type')


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
