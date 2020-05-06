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
__dateModified__ = "$dateModified: 2020-05-06 13:20:43 +0100 (Wed, May 06, 2020) $"
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
from ccpn.core.lib.CcpnNefIo import _traverse, nef2CcpnMap, _isALoop

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
        Sample._pluralLinkName       : QtCore.Qt.Checked,
        Substance._pluralLinkName    : QtCore.Qt.Checked,
        DataSet._pluralLinkName      : QtCore.Qt.Checked,
        Complex._pluralLinkName      : QtCore.Qt.Checked,
        SpectrumGroup._pluralLinkName: QtCore.Qt.Checked,
        Note._pluralLinkName         : QtCore.Qt.Checked
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
        self.includeProject = includeProject
        self.header().hide()
        if self.project is not None:
            self._populateTreeView()

        self.itemClicked.connect(self._clicked)

        self._setFocusColour()

    def _populateTreeView(self, project=None):
        if project:
            # set the new project if required
            self.project = project

        if self.includeProject:
            # add the project as the top of the tree - allows to un/select all
            self.projectItem = QtWidgets.QTreeWidgetItem(self.invisibleRootItem())
            self.projectItem.setText(0, self.project.name)
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
        ]

    lockedItems = {
        }

    nefMapping = {
        # 'nef_sequence': Chain._pluralLinkName,
        'chain_code': Chain._pluralLinkName,
        'nef_chemical_shift_list': ChemicalShiftList._pluralLinkName,
        'nef_distance_restraint_list': RestraintList._pluralLinkName,
        'nef_dihedral_restraint_list': RestraintList._pluralLinkName,
        'nef_rdc_restraint_list': RestraintList._pluralLinkName,
        'ccpn_restraint_list': RestraintList._pluralLinkName,
        # 'nef_nmr_spectrum': PeakList._pluralLinkName,
        'nef_peak': PeakList._pluralLinkName,
        'ccpn_integral_list': IntegralList._pluralLinkName,
        'ccpn_multiplet_list': MultipletList._pluralLinkName,
        'ccpn_sample': Sample._pluralLinkName,
        'ccpn_substance': Substance._pluralLinkName,
        # 'ccpn_assignment': NmrChain._pluralLinkName,
        'nmr_chain': NmrChain._pluralLinkName,
        'ccpn_dataset': DataSet._pluralLinkName,
        'ccpn_complex': Complex._pluralLinkName,
        'ccpn_spectrum_group': SpectrumGroup._pluralLinkName,
        'ccpn_notes': Note._pluralLinkName,
        'ccpn_peak_cluster': PeakCluster._pluralLinkName,
        }

    contents = {}

    def _populateTreeView(self, project=None):
        if project:
            # set the new project if required
            self.project = project

        if self.includeProject:
            # add the project as the top of the tree - allows to un/select all
            self.projectItem = QtWidgets.QTreeWidgetItem(self.invisibleRootItem())
            self.projectItem.setText(0, self.project.name)
            self.projectItem.setFlags(self.projectItem.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
            self.projectItem.setExpanded(True)
            self.headerItem = self.projectItem

        for name in self.checkList:
            if hasattr(self.project, name):  # just to be safe
                item = QtWidgets.QTreeWidgetItem(self.headerItem)
                item.setText(0, name)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)

                # for obj in getattr(self.project, name):
                #     child = QtWidgets.QTreeWidgetItem(item)
                #     child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                #     child.setData(1, 0, obj)
                #     child.setText(0, obj.pid)
                #     child.setCheckState(0, QtCore.Qt.Unchecked)

                item.setExpanded(False)
                if name in self.lockedItems:
                    item.setDisabled(True)
                    item.setCheckState(0, self.lockedItems[name])
                else:
                    item.setCheckState(0, QtCore.Qt.Checked)

    # NOTE:ED - define methods here to match CcpnNefIo
    def content_nef_molecular_system(self, project: Project, saveFrame: StarIo.NmrSaveFrame, saveFrameTag):
        self._contentLoops(project, saveFrame, saveFrameTag,  #name=spectrumName, itemLength=saveFrame['num_dimensions'],
                           )
        tag = 'chain_code'
        content = self.contents[tag]
        content(self, project, saveFrame, tag)

    def content_nef_sequence(self, project: Project, loop: StarIo.NmrLoop, parentFrame: StarIo.NmrSaveFrame) -> OrderedSet:
        pass

    def content_nef_covalent_links(self, project: Project, loop: StarIo.NmrLoop, parentFrame: StarIo.NmrSaveFrame) -> OrderedSet:
        pass

    def content_list(self, project: Project, saveFrame: StarIo.NmrSaveFrame, saveFrameTag):
        try:
            category = saveFrameTag     #saveFrame['sf_category']
        except Exception as es:
            pass

        if hasattr(saveFrame, '_content') and category in saveFrame._content:
            thisList = saveFrame._content[category]
            treeItem = self.nefMapping[category]
            found = self.findItems(treeItem, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            if found:
                if len(found) == 1:
                    # add to the tree
                    for listItem in thisList:
                        child = QtWidgets.QTreeWidgetItem(found[0])
                        child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                        child.setData(1, 0, saveFrame)
                        child.setText(0, str(listItem))
                        child.setCheckState(0, QtCore.Qt.Unchecked)

    def _contentLoops(self, project: Project, saveFrame: StarIo.NmrSaveFrame, saveFrameTag=None,
                      addLoopAttribs=None, excludeList=(), **kwds):
        """Iterate over the loops in a saveFrame, and add to results"""
        result = {}
        mapping = nef2CcpnMap[saveFrame.category]
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
        print(saveFrame.name)

    def content_nef_restraint(self, restraintList: RestraintList, loop: StarIo.NmrLoop, parentFrame: StarIo.NmrSaveFrame,
                              itemLength: int = None) -> Optional[OrderedSet]:
        pass

    def content_nef_nmr_spectrum(self, project: Project, saveFrame: StarIo.NmrSaveFrame, saveFrameTag):
        self._contentLoops(project, saveFrame, saveFrameTag, #name=spectrumName, itemLength=saveFrame['num_dimensions'],
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
    contents['chain_code'] = content_list                       # content_nef_sequence
    # contents['nef_covalent_links'] = content_nef_covalent_links
    contents['nef_chemical_shift_list'] = content_list                       # content_nef_chemical_shift_list
    # contents['nef_chemical_shift'] = content_nef_chemical_shift

    contents['nef_distance_restraint_list'] = content_list                       # content_nef_restraint_list  # could be _contentLoops
    contents['nef_dihedral_restraint_list'] = content_list                       # content_nef_restraint_list
    contents['nef_rdc_restraint_list'] = content_list                       # content_nef_restraint_list
    contents['ccpn_restraint_list'] = content_list                       # content_nef_restraint_list

    # contents['nef_distance_restraint'] = partial(content_nef_restraint, itemLength=coreConstants.constraintListType2ItemLength.get('Distance'))
    # contents['nef_dihedral_restraint'] = partial(content_nef_restraint, itemLength=coreConstants.constraintListType2ItemLength.get('Dihedral'))
    # contents['nef_rdc_restraint'] = partial(content_nef_restraint, itemLength=coreConstants.constraintListType2ItemLength.get('Rdc'))
    # contents['ccpn_restraint'] = partial(content_nef_restraint, itemLength=coreConstants.constraintListType2ItemLength.get('Distance'))

    contents['nef_nmr_spectrum'] = content_ccpn_notes                       # content_nef_nmr_spectrum
    contents['nef_peak'] = content_list

    contents['ccpn_integral_list'] = content_list                       # content_ccpn_integral_list
    contents['ccpn_multiplet_list'] = content_list                       # content_ccpn_multiplet_list
    # contents['ccpn_integral'] = content_ccpn_integral
    # contents['ccpn_multiplet'] = content_ccpn_multiplet
    contents['ccpn_peak_cluster_list'] = content_ccpn_peak_cluster_list
    contents['ccpn_peak_cluster'] = content_list

    contents['ccpn_spectrum_group'] = content_list                       # content_ccpn_spectrum_group
    contents['ccpn_complex'] = content_list                       # content_ccpn_complex
    contents['ccpn_sample'] = content_list                       # content_ccpn_sample
    contents['ccpn_substance'] = content_list                       # content_ccpn_substance

    contents['ccpn_assignment'] = content_ccpn_notes
    contents['nmr_chain'] = content_list

    contents['ccpn_notes'] = content_list                       # content_ccpn_notes

    def _fillFunc(self, project, saveFrame, *args, **kwds):
        saveFrameName = saveFrame['sf_category']
        if saveFrameName in self.contents:
            content = self.contents[saveFrameName]
            content(self, project, saveFrame, saveFrame['sf_category'])

    def fillTreeView(self, nefDict):
        _traverse(self.project, nefDict, traverseFunc=self._fillFunc)


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
