"""
SideBar setup

This module is built on a definition of the sidebar tree that includes dynamic additions and deletions initiated by
notifiers on the various project objects.

The tree can be constructed using 4 item types:

SidebarTree: A static tree item, displaying either a name or the pid of the associated V3 core object
SidebarItem: A static item, displaying either a name or the pid of the associated V3 core object
SidebarClassItems: A number of dynamically added items of type V3 core 'klass'
SidebarClassTreeItems: A Tree with a number of dynamically added items of type V3 core 'klass'


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
__dateModified__ = "$dateModified: 2017-07-07 16:32:55 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Wayne Boucher $"
__date__ = "$Date: 2017-03-23 16:50:22 +0000 (Thu, March 23, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets

from ccpn.core import _coreClassMap
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.core.MultipletList import MultipletList
from ccpn.core.Spectrum import Spectrum
from ccpn.core.PeakList import PeakList
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.Note import Note
from ccpn.core.Sample import Sample
from ccpn.core.IntegralList import IntegralList
from ccpn.core.NmrChain import NmrChain
from ccpn.core.Chain import Chain
from ccpn.core.StructureEnsemble import StructureEnsemble
from ccpn.core.RestraintList import RestraintList
from ccpn.ui.gui.guiSettings import sidebarFont
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.popups.ChemicalShiftListPopup import ChemicalShiftListPopup
from ccpn.ui.gui.popups.DataSetPopup import DataSetPopup
from ccpn.ui.gui.popups.NmrAtomPopup import NmrAtomPopup
from ccpn.ui.gui.popups.NmrChainPopup import NmrChainPopup
from ccpn.ui.gui.popups.NmrResiduePopup import NmrResiduePopup
from ccpn.ui.gui.popups.NotesPopup import NotesPopup
from ccpn.ui.gui.popups.PeakListPropertiesPopup import PeakListPropertiesPopup
from ccpn.ui.gui.popups.IntegralListPropertiesPopup import IntegralListPropertiesPopup
from ccpn.ui.gui.popups.MultipletListPropertiesPopup import MultipletListPropertiesPopup
from ccpn.ui.gui.popups.RestraintTypePopup import RestraintTypePopup
from ccpn.ui.gui.popups.SampleComponentPropertiesPopup import EditSampleComponentPopup
from ccpn.ui.gui.popups.SamplePropertiesPopup import SamplePropertiesPopup
from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor
from ccpn.ui.gui.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup
from ccpn.ui.gui.popups.StructurePopup import StructurePopup
from ccpn.ui.gui.popups.SubstancePropertiesPopup import SubstancePropertiesPopup

from PyQt5 import QtWidgets, QtCore
from collections import OrderedDict
from functools import partial
from typing import Callable, Any

from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.core.PeakList import PeakList
from ccpn.core.MultipletList import MultipletList
from ccpn.core.IntegralList import IntegralList
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.NmrChain import NmrChain
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.Sample import Sample
from ccpn.core.SampleComponent import SampleComponent
from ccpn.core.Substance import Substance
from ccpn.core.Chain import Chain
from ccpn.core.Residue import Residue
from ccpn.core.StructureEnsemble import StructureEnsemble
from ccpn.core.Complex import Complex
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.DataSet import DataSet
from ccpn.core.Model import Model
from ccpn.core.Restraint import Restraint, RestraintList
from ccpn.core.Note import Note

from ccpn.ui.gui.popups.ChemicalShiftListPopup import ChemicalShiftListPopup
from ccpn.ui.gui.popups.DataSetPopup import DataSetPopup
from ccpn.ui.gui.popups.NmrAtomPopup import NmrAtomPopup
from ccpn.ui.gui.popups.NmrChainPopup import NmrChainPopup
from ccpn.ui.gui.popups.NmrResiduePopup import NmrResiduePopup
from ccpn.ui.gui.popups.NotesPopup import NotesPopup
from ccpn.ui.gui.popups.PeakListPropertiesPopup import PeakListPropertiesPopup
from ccpn.ui.gui.popups.IntegralListPropertiesPopup import IntegralListPropertiesPopup
from ccpn.ui.gui.popups.MultipletListPropertiesPopup import MultipletListPropertiesPopup
from ccpn.ui.gui.popups.RestraintTypePopup import RestraintTypePopup
from ccpn.ui.gui.popups.SampleComponentPropertiesPopup import EditSampleComponentPopup
from ccpn.ui.gui.popups.SamplePropertiesPopup import SamplePropertiesPopup
from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor
from ccpn.ui.gui.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup
from ccpn.ui.gui.popups.StructurePopup import StructurePopup
from ccpn.ui.gui.popups.SubstancePropertiesPopup import SubstancePropertiesPopup
from ccpn.ui.gui.popups.EditMultipletPopup import EditMultipletPopup

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.widgets.MessageDialog import showInfo, showWarning, progressManager, showNotImplementedMessage
from ccpn.util.Constants import ccpnmrJsonData
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.popups.CreateChainPopup import CreateChainPopup
from ccpn.ui.gui.popups.CreateNmrChainPopup import CreateNmrChainPopup
# from ccpn.ui.gui.modules.NotesEditor import NotesEditorModule
from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
from ccpn.core.lib.Notifiers import Notifier, NotifierBase
from ccpn.core.lib.ContextManagers import catchExceptions, notificationBlanking

from ccpn.core.lib.Notifiers import NotifierBase, Notifier
from ccpn.core.lib.Pid import Pid

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.widgets.MessageDialog import showInfo, showWarning, progressManager
from ccpn.util.Constants import ccpnmrJsonData
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.popups.CreateChainPopup import CreateChainPopup
from ccpn.ui.gui.popups.CreateNmrChainPopup import CreateNmrChainPopup
# from ccpn.ui.gui.modules.NotesEditor import NotesEditorModule
from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
from ccpn.core.lib.Notifiers import Notifier, NotifierBase
from ccpn.core.lib.ContextManagers import catchExceptions
from ccpn.ui.gui.lib.MenuActions import _openNote, _openIntegralList, _openPeakList, _openMultipletList, _openChemicalShiftList, _openRestraintList, \
    _openStructureTable, _openNmrResidueTable, _openResidueTable, _openItemObject, _openSpectrumDisplay, _openSpectrumGroup, _openSampleSpectra, \
    _createSpectrumGroup

from ccpn.ui.gui.widgets.Menu import Menu
from functools import partial


# NB the order matters!
# NB 'SG' must be before 'SP', as SpectrumGroups must be ready before Spectra
# Also parents must appear before their children

# _classNamesInSidebar = ['SpectrumGroup', 'Spectrum', 'PeakList', 'IntegralList', 'MultipletList',
#                         'Sample', 'SampleComponent', 'Substance', 'Complex', 'Chain',
#                         'Residue', 'NmrChain', 'NmrResidue', 'NmrAtom', 'ChemicalShiftList',
#                         'StructureEnsemble', 'Model', 'DataSet', 'RestraintList', 'Note', ]
#
# Pids = 'pids'
#
# # TODO Add Residue
#
#
# # ll = [_coreClassMap[x] for x in _classNamesInSidebar]
# # classesInSideBar = OrderedDict(((x.shortClassName, x) for x in ll))
# classesInSideBar = OrderedDict(((x.shortClassName, x) for x in _coreClassMap.values()
#                                 if x.className in _classNamesInSidebar))
# # classesInSideBar = ('SG', 'SP', 'PL', 'SA', 'SC', 'SU', 'MC', 'NC', 'NR', 'NA',
# #                     'CL', 'SE', 'MO', 'DS',
# #                     'RL', 'NO')
#
# classesInTopLevel = ('SG', 'SP', 'SA', 'SU', 'MC', 'MX', 'NC', 'CL', 'SE', 'DS', 'NO')

# NBNB TBD FIXME
# 1)This function (and the NEW_ITEM_DICT) it uses gets the create_new
# function from the shortClassName of the PARENT!!!
# This is the only way to do it if the create_new functions are attributes of the PARENT!!!
#
# 2) <New> in makes a new SampleComponent. This is counterintuitive!
# Anyway, how do you make a new Sample?
# You use the <New> under sample, this comment is completely inaccurate!
#
# Try putting in e.g. <New PeakList>, <New SampleComponent> etc. Done in version 9855.

# NEW_ITEM_DICT = {
#
#     'SP'                : 'newPeakList',
#     'NC'                : 'newNmrResidue',
#     'NR'                : 'newNmrAtom',
#     'DS'                : 'newRestraintList',
#     'RL'                : 'newRestraint',
#     'SE'                : 'newModel',
#     'Notes'             : 'newNote',
#     'StructureEnsembles': 'newStructureEnsemble',
#     'Samples'           : 'newSample',
#     'NmrChains'         : 'newNmrChain',
#     'Chains'            : 'newChain',
#     'Substances'        : 'newSubstance',
#     'ChemicalShiftLists': 'newChemicalShiftList',
#     'DataSets'          : 'newDataSet',
#     'SpectrumGroups'    : 'newSpectrumGroup',
#     'Complexes'         : 'newComplex',
#     }

# OPEN_ITEM_DICT = {
#     Spectrum.className         : _openSpectrumDisplay,
#     PeakList.className         : showPeakTable,
#     IntegralList.className     : showIntegralTable,
#     MultipletList.className    : showMultipletTable,
#     NmrChain.className         : showNmrResidueTable,
#     Chain.className            : showResidueTable,
#     SpectrumGroup.className    : _openSpectrumGroup,
#     Sample.className           : _openSampleSpectra,
#     ChemicalShiftList.className: showChemicalShiftTable,
#     RestraintList.className    : showRestraintTable,
#     Note.lastModified          : showNotesEditor,
#     StructureEnsemble.className: showStructureTable
#     }


OpenObjAction = {
    Spectrum         : _openSpectrumDisplay,
    PeakList         : _openPeakList,
    MultipletList    : _openMultipletList,
    NmrChain         : _openNmrResidueTable,
    Chain            : _openResidueTable,
    SpectrumGroup    : _openSpectrumGroup,
    Sample           : _openSampleSpectra,
    ChemicalShiftList: _openChemicalShiftList,
    RestraintList    : _openRestraintList,
    Note             : _openNote,
    IntegralList     : _openIntegralList,
    StructureEnsemble: _openStructureTable
    }

NEWPEAKLIST = 'newPeakList'
NEWINTEGRALLIST = 'newIntegralList'
NEWMULTIPLETLIST = 'newMultipletList'
NEWNMRRESIDUE = 'newNmrResidue'
NEWNMRATOM = 'newNmrAtom'
NEWRESTRAINTLIST = 'newRestraintList'
NEWRESTRAINT = 'newRestraint'
NEWMODEL = 'newModel'
NEWNOTE = 'newNote'
NEWSTRUCTUREENSEMBLE = 'newStructureEnsemble'
NEWSAMPLE = 'newSample'
NEWNMRCHAIN = 'newNmrChain'
NEWCHAIN = 'newChain'
NEWSUBSTANCE = 'newSubstance'
NEWCHEMICALSHIFTLIST = 'newChemicalShiftList'
NEWDATASET = 'newDataSet'
NEWSPECTRUMGROUP = 'newSpectrumGroup'
NEWCOMPLEX = 'newComplex'

NEW_ITEM_DICT = {

    PeakList.className         : NEWPEAKLIST,
    IntegralList.className     : NEWINTEGRALLIST,
    MultipletList.className    : NEWMULTIPLETLIST,
    NmrChain.className         : CreateNmrChainPopup,
    NmrResidue.className       : NEWNMRRESIDUE,
    NmrAtom.className          : NEWNMRATOM,
    RestraintList.className    : RestraintTypePopup,
    Restraint.className        : NEWRESTRAINT,
    StructureEnsemble.className: NEWSTRUCTUREENSEMBLE,
    Sample.className           : NEWSAMPLE,
    SampleComponent.className  : EditSampleComponentPopup,
    Chain.className            : CreateChainPopup,
    Substance.className        : SubstancePropertiesPopup,
    ChemicalShiftList.className: NEWCHEMICALSHIFTLIST,
    DataSet.className          : NEWDATASET,
    SpectrumGroup.className    : SpectrumGroupEditor,
    Complex.className          : NEWCOMPLEX,
    Model.className            : NEWMODEL,
    Note.className             : NEWNOTE,
    }

EDIT_ITEM_DICT = {

    Spectrum.className         : SpectrumPropertiesPopup,
    PeakList.className         : PeakListPropertiesPopup,
    IntegralList.className     : IntegralListPropertiesPopup,
    MultipletList.className    : MultipletListPropertiesPopup,
    SpectrumGroup.className    : SpectrumGroupEditor,
    Sample.className           : SamplePropertiesPopup,
    SampleComponent.className  : EditSampleComponentPopup,
    Substance.className        : SubstancePropertiesPopup,
    NmrChain.className         : NmrChainPopup,
    NmrResidue.className       : NmrResiduePopup,
    NmrAtom.className          : NmrAtomPopup,
    ChemicalShiftList.className: ChemicalShiftListPopup,
    StructureEnsemble.className: StructurePopup,
    DataSet.className          : DataSetPopup,
    Note.className             : NotesPopup,
    }

OPEN_ITEM_DICT = {
    Spectrum.className         : '_openSpectrumDisplay',
    PeakList.className         : 'showPeakTable',
    IntegralList.className     : 'showIntegralTable',
    MultipletList.className    : 'showMultipletTable',
    NmrChain.className         : 'showNmrResidueTable',
    Chain.className            : 'showResidueTable',
    SpectrumGroup.className    : '_openSpectrumGroup',
    Sample.className           : '_openSampleSpectra',
    ChemicalShiftList.className: 'showChemicalShiftTable',
    RestraintList.className    : 'showRestraintTable',
    Note.lastModified          : 'showNotesEditor',
    StructureEnsemble.className: 'showStructureTable'
    }


### Flag example code removed in revision 7686


# class SideBar(QtWidgets.QTreeWidget, Base, NotifierBase):
#     def __init__(self, parent=None, mainWindow=None, multiSelect=True):
#
#         super().__init__(parent)
#         Base._init(self, acceptDrops=True)
#
#         self.multiSelect = multiSelect
#         if self.multiSelect:
#             self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
#
#         self.mainWindow = parent  # ejb - needed for moduleArea
#         self.application = self.mainWindow.application
#         # self._typeToItem = dd = {}
#         self._sidebarBlockingLevel = 0
#         self._sideBarState = []
#
#         self.setFont(sidebarFont)
#         self.header().hide()
#         self.setDragEnabled(True)
#         self.setExpandsOnDoubleClick(False)
#         self.setDragDropMode(self.InternalMove)
#         self.setMinimumWidth(200)
#
#         self.mousePressEvent = self._mousePressEvent
#         self.mouseReleaseEvent = self._mouseReleaseEvent
#         # self.mouseMoveEvent = self._mouseMoveEvent
#         self.dragMoveEvent = self._dragMoveEvent
#         # self.dragEnterEvent = self._dragEnterEvent
#
#         self.setDragDropMode(self.DragDrop)
#         self.setAcceptDrops(True)
#
#         # self.eventFilter = self._eventFilter  # ejb - doesn't work
#         # self.installEventFilter(self)  # ejb
#
#         self.droppedNotifier = GuiNotifier(self,
#                                            [GuiNotifier.DROPEVENT], [DropBase.URLS, DropBase.PIDS],
#                                            self._processDroppedItems)
#
#         self.itemDoubleClicked.connect(self._raiseObjectProperties)
#
#     @property
#     def sidebarBlocked(self):
#         """Sidebar blocking. If true (non-zero) sidebar updates are blocked.
#         Allows multiple external functions to set blocking without trampling each other
#         Modify with increaseBlocking/decreaseBlocking only"""
#         return self._sidebarBlockingLevel > 0
#
#     def increaseSidebarBlocking(self):
#         """increase level of blocking"""
#         self._sidebarBlockingLevel += 1
#
#     def decreaseSidebarBlocking(self):
#         """Reduce level of blocking - when level reaches zero, Sidebar is unblocked"""
#         if self.sidebarBlocked:
#             self._sidebarBlockingLevel -= 1
#         else:
#             raise RuntimeError('Error: cannot decrease blocking below 0')
#
#     def _populateSidebar(self):
#         self._clearQTreeWidget(self)
#
#         self._typeToItem = dd = {}
#
#         self.projectItem = dd['PR'] = QtWidgets.QTreeWidgetItem(self)
#         self.projectItem.setFlags(self.projectItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.projectItem.setText(0, "Project")
#         self.projectItem.setExpanded(True)
#
#         self.spectrumItem = dd['SP'] = QtWidgets.QTreeWidgetItem(self.projectItem)
#         self.spectrumItem.setFlags(self.spectrumItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.spectrumItem.setText(0, "Spectra")
#
#         self.spectrumGroupItem = dd['SG'] = QtWidgets.QTreeWidgetItem(self.projectItem)
#         self.spectrumGroupItem.setFlags(self.spectrumGroupItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.spectrumGroupItem.setText(0, "SpectrumGroups")
#
#         self.newSpectrumGroup = QtWidgets.QTreeWidgetItem(self.spectrumGroupItem)
#         self.newSpectrumGroup.setFlags(self.newSpectrumGroup.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.newSpectrumGroup.setText(0, "<New SpectrumGroup>")
#
#         self.samplesItem = dd['SA'] = QtWidgets.QTreeWidgetItem(self.projectItem)
#         self.samplesItem.setFlags(self.samplesItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.samplesItem.setText(0, 'Samples')
#
#         self.newSample = QtWidgets.QTreeWidgetItem(self.samplesItem)
#         self.newSample.setFlags(self.newSample.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.newSample.setText(0, "<New Sample>")
#
#         self.substancesItem = dd['SU'] = QtWidgets.QTreeWidgetItem(self.projectItem)
#         self.substancesItem.setFlags(self.substancesItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.substancesItem.setText(0, "Substances")
#
#         self.newSubstance = QtWidgets.QTreeWidgetItem(self.substancesItem)
#         self.newSubstance.setFlags(self.newSubstance.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.newSubstance.setText(0, "<New Substance>")
#
#         self.chainItem = dd['MC'] = QtWidgets.QTreeWidgetItem(self.projectItem)
#         self.chainItem.setFlags(self.chainItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.chainItem.setText(0, "Chains")
#
#         self.newChainItem = QtWidgets.QTreeWidgetItem(self.chainItem)
#         self.newChainItem.setFlags(self.newChainItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.newChainItem.setText(0, '<New Chain>')
#
#         self.complexItem = dd['MX'] = QtWidgets.QTreeWidgetItem(self.projectItem)
#         self.complexItem.setFlags(self.complexItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.complexItem.setText(0, "Complexes")
#
#         # TODO make COmplexEditor, install it in _createNewObject, and uncomment this
#         # self.newComplex = QtWidgets.QTreeWidgetItem(self.complexItem)
#         # self.newComplex.setFlags(self.newComplex.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         # self.newComplex.setText(0, "<New Complex>")
#
#         self.nmrChainItem = dd['NC'] = QtWidgets.QTreeWidgetItem(self.projectItem)
#         self.nmrChainItem.setFlags(self.nmrChainItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.nmrChainItem.setText(0, "NmrChains")
#
#         self.newNmrChainItem = QtWidgets.QTreeWidgetItem(self.nmrChainItem)
#         self.newNmrChainItem.setFlags(self.newNmrChainItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.newNmrChainItem.setText(0, '<New NmrChain>')
#
#         self.chemicalShiftListsItem = dd['CL'] = QtWidgets.QTreeWidgetItem(self.projectItem)
#         self.chemicalShiftListsItem.setFlags(self.chemicalShiftListsItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.chemicalShiftListsItem.setText(0, "ChemicalShiftLists")
#
#         self.newChemicalShiftListItem = QtWidgets.QTreeWidgetItem(self.chemicalShiftListsItem)
#         self.newChemicalShiftListItem.setFlags(self.newChemicalShiftListItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.newChemicalShiftListItem.setText(0, '<New ChemicalShiftList>')
#
#         self.structuresItem = dd['SE'] = QtWidgets.QTreeWidgetItem(self.projectItem)
#         self.structuresItem.setFlags(self.structuresItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.structuresItem.setText(0, "StructureEnsembles")
#
#         self.newStructuresListItem = QtWidgets.QTreeWidgetItem(self.structuresItem)  # ejb
#         self.newStructuresListItem.setFlags(self.newStructuresListItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.newStructuresListItem.setText(0, '<New StructureEnsemble>')
#
#         self.dataSetsItem = dd['DS'] = QtWidgets.QTreeWidgetItem(self.projectItem)
#         self.dataSetsItem.setFlags(self.dataSetsItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.dataSetsItem.setText(0, "DataSets")
#
#         self.newDataSetItem = QtWidgets.QTreeWidgetItem(self.dataSetsItem)
#         self.newDataSetItem.setFlags(self.newDataSetItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.newDataSetItem.setText(0, '<New DataSet>')
#
#         self.notesItem = dd['NO'] = QtWidgets.QTreeWidgetItem(self.projectItem)
#         self.notesItem.setFlags(self.notesItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.notesItem.setText(0, "Notes")
#
#         self.newNoteItem = QtWidgets.QTreeWidgetItem(self.notesItem)
#         self.newNoteItem.setFlags(self.newNoteItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#         self.newNoteItem.setText(0, '<New Note>')
#
#     def _raiseObjectProperties(self, item):
#         """get object from Pid and dispatch call depending on type
#
#         NBNB TBD How about refactoring so that we have a shortClassName:Popup dictionary?"""
#         dataPid = item.data(0, QtCore.Qt.DisplayRole)
#         project = self.project
#
#         # trap creation of new items form sideBar
#         obj = project.getByPid(dataPid) if Pid.Pid.isValid(dataPid) else None
#
#         if obj is not None:
#             self.raisePopup(obj, item)
#         elif dataPid.startswith('<New'):
#             self._createNewObject(item)
#
#         else:
#             project._logger.error("Double-click activation not implemented for Pid %s, object %s"
#                                   % (dataPid, obj))
#
#     def selectPid(self, pid):
#
#         ws = self._findItems(pid)  #not sure why this returns a list!
#         for i in ws:
#             self.setCurrentItem(i)
#
#     def _processDroppedItems(self, data):
#         "Handle the dropped urls"
#         # CCPN INTERNAL. Called also from module area and GuiStrip. They should have same behaviours
#         objs = []
#         for url in data.get('urls', []):
#             getLogger().debug('>>> dropped: ' + str(url))
#
#             dataType, subType, usePath = ioFormats.analyseUrl(url)
#             if dataType == 'Project' and subType in (ioFormats.CCPN,
#                                                      ioFormats.NEF,
#                                                      ioFormats.NMRSTAR,
#                                                      ioFormats.SPARKY):
#
#                 okToContinue = self.mainWindow._queryCloseProject(title='Load %s project' % subType,
#                                                                   phrase='create a new')
#                 if okToContinue:
#                     with progressManager(self.mainWindow, 'Loading project... ' + url):
#                         with catchExceptions():
#                             obj = self.application.loadProject(url)
#                         # try:
#                         #     obj = self.application.loadProject(url)
#                         # except Exception as es:
#                         #     getLogger().warning('loadProject Error: %s' % str(es))
#                         #     obj = None
#
#                         if isinstance(obj, Project):
#                             try:
#                                 obj._mainWindow.sideBar.fillSideBar(obj)
#                                 obj._mainWindow.show()
#                                 QtWidgets.QApplication.setActiveWindow(obj._mainWindow)
#
#                             except Exception as es:
#                                 getLogger().warning('Error: %s' % str(es))
#
#             else:
#                 # with progressManager(self.mainWindow, 'Loading data... ' + url):
#                 try:  #  Why do we need this try?
#                     data = self.project.loadData(url)
#                     if data:
#                         objs.extend(data)
#                 except Exception as es:
#                     getLogger().warning('loadData Error: %s' % str(es))
#             # #   try:
#
#             # except Exception as es:
#             #   getLogger().warning('loadData Error: %s' % str(es))
#
#             # if objects is not None:
#             #   # TODO:ED added here to make new instances of project visible, they are created hidden to look cleaner
#             #   for obj in objects:
#
#             # if objects is None or len(objects) == 0:
#             #   showWarning('Invalid File', 'Cannot handle "%s"' % url)
#         return objs
#
#     def setProject(self, project: Project):
#         """
#         Sets the specified project as a class attribute so it can be accessed from elsewhere
#         """
#         self.project = project
#         self._registerNotifiers()
#
#     def _registerNotifiers(self):
#         self._notifierList = []
#
#         # Register notifiers to maintain sidebar
#         for cls in classesInSideBar.values():
#             className = cls.className
#
#             self._notifierList.append(self.setNotifier(self.project,
#                                                        [Notifier.DELETE],
#                                                        className,
#                                                        self._removeItem,
#                                                        onceOnly=True))
#
#             if className != 'NmrResidue':
#                 self._notifierList.append(self.setNotifier(self.project,
#                                                            [Notifier.CREATE],
#                                                            className,
#                                                            self._createItem))
#
#                 self._notifierList.append(self.setNotifier(self.project,
#                                                            [Notifier.RENAME],
#                                                            className,
#                                                            self._renameItem,
#                                                            onceOnly=True))
#
#         self._notifierList.append(self.setNotifier(self.project,
#                                                    [Notifier.CREATE],
#                                                    'NmrResidue',
#                                                    self._refreshParentNmrChain,
#                                                    onceOnly=True))
#
#         self._notifierList.append(self.setNotifier(self.project,
#                                                    [Notifier.RENAME],
#                                                    'NmrResidue',
#                                                    self._renameNmrResidueItem,
#                                                    onceOnly=True))
#
#         self._notifierList.append(self.setNotifier(self.project,
#                                                    [Notifier.CHANGE, Notifier.CREATE, Notifier.DELETE],
#                                                    'SpectrumGroup',
#                                                    self._refreshSidebarSpectra))
#
#         # TODO:ED Add similar set of notifiers, and similar function for Complex/Chain
#
#     def _unregisterNotifiers(self):
#         for notifier in self._notifierList:
#             if notifier:
#                 notifier.unRegister()
#
#     def _refreshSidebarSpectra(self, data):  # dummy:Project):
#         """Reset spectra in sidebar - to be called from notifiers
#         """
#         self._saveExpandedState()
#
#         for spectrum in self.project.spectra:
#             # self._removeItem( self.project, spectrum)
#             self._removeItem({Notifier.OBJECT: spectrum})
#             self._createItem({Notifier.OBJECT: spectrum})
#             for obj in spectrum.peakLists + spectrum.integralLists:
#                 self._createItem({Notifier.OBJECT: obj})
#
#         self._restoreExpandedState()
#
#     def _createSpectrumGroup(self, spectra=None or []):
#         popup = SpectrumGroupEditor(parent=self.mainWindow, mainWindow=self.mainWindow, addNew=True, spectra=spectra)
#         popup.exec_()
#         popup.raise_()
#
#     def _refreshParentNmrChain(self, data):  #nmrResidue:NmrResidue, oldPid:Pid=None):     # ejb - catch oldName
#         """Reset NmrChain sidebar - needed when NmrResidue is created or renamed to trigger re-sort
#
#         Replaces normal _createItem notifier for NmrResidues"""
#
#         nmrResidue = data[Notifier.OBJECT]
#         # oldPid = data[Notifier.OLDPID]
#
#         self._saveExpandedState()
#
#         nmrChain = nmrResidue._parent
#
#         # Remove NmrChain item and contents
#         self._removeItem({Notifier.OBJECT: nmrChain})
#
#         # Create NmrResidue items again - this gives them in correctly sorted order
#         self._createItem({Notifier.OBJECT: nmrChain})
#         for nr in nmrChain.nmrResidues:
#             self._createItem({Notifier.OBJECT: nr})
#             for nmrAtom in nr.nmrAtoms:
#                 self._createItem({Notifier.OBJECT: nmrAtom})
#
#         self._restoreExpandedState()
#
#         # nmrChain = nmrResidue._parent     # ejb - just insert the 1 item
#         # for nr in nmrChain.nmrResidues:
#         #   if (nr.pid == nmrResidue.pid):
#         #     self._createItem(nr)
#         #
#         # newPid = nmrChain.pid                   # ejb - expand the tree again from nmrChain
#         # for item in self._findItems(newPid):
#         #   item.setExpanded(True)
#
#     def _addItem(self, item: QtWidgets.QTreeWidgetItem, pid: str):
#         """
#         Adds a QTreeWidgetItem as a child of the item specified, which corresponds to the data object
#         passed in.
#         """
#
#         newItem = QtWidgets.QTreeWidgetItem(item)
#         newItem.setFlags(newItem.flags() & ~(QtCore.Qt.ItemIsDropEnabled))
#         newItem.setData(0, QtCore.Qt.DisplayRole, str(pid))
#         newItem.mousePressEvent = self.mousePressEvent
#         return newItem
#
#     #
#     # def renameItem(self, pid):
#     #   # item = FindItem
#     #   pass
#
#     def processText(self, text, event=None):
#         newNote = self.project.newNote()
#         newNote.text = text
#
#     def _deleteItemObject(self, objs):
#         """Removes the specified item from the sidebar and deletes it from the project.
#         NB, the clean-up of the side bar is done through notifiers
#         """
#         from ccpn.core.lib.ContextManagers import undoBlockManager
#
#         try:
#             with undoBlockManager():
#                 for obj in objs:
#                     if obj:
#                         if isinstance(obj, Spectrum):
#                             # # need to delete all peakLists and integralLists first, treat as single undo
#                             # for peakList in obj.peakLists:
#                             #     peakList.delete()
#                             # for integralList in obj.integralLists:
#                             #     integralList.delete()
#                             # for multipletList in obj.multipletLists:
#                             #     multipletList.delete()
#                             obj.delete()
#                         else:
#                             # just delete the object
#                             obj.delete()
#
#         except Exception as es:
#             showWarning('Delete', str(es))
#
#         #  Force redrawing
#         from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
#
#         GLSignals = GLNotifier(parent=self)
#         GLSignals.emitEvent(triggers=[GLNotifier.GLALLPEAKS, GLNotifier.GLALLINTEGRALS, GLNotifier.GLALLMULTIPLETS])
#
#     def _cloneObject(self, objs):
#         """Clones the specified objects"""
#         for obj in objs:
#             obj.clone()
#
#     def _createItem(self, data):  #obj:AbstractWrapperObject):
#         """Create a new sidebar item from a new object.
#         Called by notifier when a new object is created or undeleted (so need to check for duplicates).
#         NB Obj may be of a type that does not have an item"""
#
#         obj = data[Notifier.OBJECT]
#
#         if not isinstance(obj, AbstractWrapperObject):
#             return
#
#         shortClassName = obj.shortClassName
#         parent = obj._parent
#         project = obj._project
#
#         if shortClassName in classesInSideBar:
#
#             if parent is project:
#
#                 if shortClassName == 'SP':
#                     # Spectrum - special behaviour - put them under SpectrumGroups, if any
#                     spectrumGroups = obj.spectrumGroups
#                     if spectrumGroups:
#                         for sg in spectrumGroups:
#
#                             # # ejb - search for the spectrumGroup, if not there then create it
#                             # sglist = self._findItems(str(sg.pid))
#                             # if not sglist:
#                             #   # have not found the group
#                             #   newTempSpectrumGroup = QtWidgets.QTreeWidgetItem(self.spectrumGroupItem)
#                             #   newTempSpectrumGroup.setFlags(
#                             #     newTempSpectrumGroup.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#                             #   newTempSpectrumGroup.setText(0, str(sg.pid))
#                             #
#                             #   # sglist = self._findItems('SpectrumGroups')
#                             #   # for sgitem in self._findItems('SpectrumGroups'):
#                             #   #   newSpectrumGroup = QtWidgets.QTreeWidgetItem(sgitem)
#                             #   #   newSpectrumGroup.setFlags(
#                             #   #     newSpectrumGroup.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#                             #   #   newSpectrumGroup.setText(0, str(sg.pid))
#                             #
#                             # # now carry on and insert the new groups
#
#                             for sgitem in self._findItems(str(sg.pid)):  # add '<new spectrumGroup>'
#                                 newItem = self._addItem(sgitem, str(obj.pid))
#                                 newObjectItem = QtWidgets.QTreeWidgetItem(newItem)
#                                 newObjectItem.setFlags(newObjectItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#                                 newObjectItem.setText(0, "<New %s>" % classesInSideBar[shortClassName].className)
#
#                         # return
#
#                 itemParent = self._typeToItem.get(shortClassName)
#                 newItem = self._addItem(itemParent, obj.pid)
#                 # itemParent.sortChildren(0, QtCore.Qt.AscendingOrder)
#                 if shortClassName in ['SA', 'NC', 'DS']:
#                     newObjectItem = QtWidgets.QTreeWidgetItem(newItem)
#                     newObjectItem.setFlags(newObjectItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#                     newObjectItem.setText(0, "<New %s>" % classesInSideBar[shortClassName]._childClasses[0].className)
#
#                 if shortClassName == 'SP':
#                     newPeakListObjectItem = QtWidgets.QTreeWidgetItem(newItem)
#                     newPeakListObjectItem.setFlags(newPeakListObjectItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#                     newPeakListObjectItem.setText(0, "<New PeakList>")
#
#                     newMultipletListObjectItem = QtWidgets.QTreeWidgetItem(newItem)
#                     newMultipletListObjectItem.setFlags(newMultipletListObjectItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#                     newMultipletListObjectItem.setText(0, "<New MultipletList>")
#
#                     newIntegralListObjectItem = QtWidgets.QTreeWidgetItem(newItem)
#                     newIntegralListObjectItem.setFlags(newIntegralListObjectItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#                     newIntegralListObjectItem.setText(0, "<New IntegralList>")
#
#             else:
#                 for itemParent in self._findItems(parent.pid):
#                     newItem = self._addItem(itemParent, obj.pid)
#
#                     if shortClassName == 'NR':
#                         newObjectItem = QtWidgets.QTreeWidgetItem(newItem)
#                         newObjectItem.setFlags(newObjectItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
#                         newObjectItem.setText(0, "<New NmrAtom>")
#                     # for i in range(itemParent.childCount()):
#                     #   itemParent.child(i).sortChildren(0, QtCore.Qt.AscendingOrder)
#
#         else:
#             # Object type is not in sidebar
#             return None
#
#     def _itemObjects(self, item, recursive=False):
#
#         objects = [self.project.getByPid(item.data(0, QtCore.Qt.DisplayRole))]
#
#         if recursive:
#             for i in range(item.childCount()):
#                 child = item.child(i)
#                 if child.data(0, QtCore.Qt.DisplayRole)[:2] in classesInSideBar:
#                     objects.extend(self._itemObjects(child, recursive=True))
#
#         return objects
#
#     def _renameItem(self, data):  #obj:AbstractWrapperObject, oldPid:str):
#         """rename item(s) from previous pid oldPid to current object pid"""
#
#         obj = data[Notifier.OBJECT]
#         oldPid = data[Notifier.OLDPID]
#
#         self._saveExpandedState()
#
#         import sip
#
#         newPid = obj.pid
#         for item in self._findItems(oldPid):
#             # item.setData(0, QtCore.Qt.DisplayRole, str(obj.pid))    # ejb - rename instead of delete
#
#             if Pid.IDSEP not in oldPid or oldPid.split(Pid.PREFIXSEP, 1)[1].startswith(obj._parent._id + Pid.IDSEP):
#                 # Parent unchanged, just rename
#                 item.setData(0, QtCore.Qt.DisplayRole, str(newPid))
#             else:
#                 # parent has changed - we must move and rename the entire item tree.
#                 # NB this is relevant for NmrAtom (NmrResidue is handled elsewhere)
#                 objects = self._itemObjects(item, recursive=True)
#                 # print(objects, '$$$')
#                 sip.delete(item)  # this also removes child items
#
#                 # NB the first object cannot be found from its pid (as it has already been renamed)
#                 # So we do it this way
#                 self._createItem({Notifier.OBJECT: obj})
#                 for xx in objects[1:]:
#                     self._createItem({Notifier.OBJECT: xx})
#
#         self._restoreExpandedState()
#
#     def _getExpanded(self, item, data: list):
#         """Add the name of expanded item to the data list
#         """
#         if item.isExpanded():
#             data.append(item.text(0))
#
#     def _setExpanded(self, item, data: list):
#         """Set the expanded flag if item is in data
#         """
#         if item.text(0) in data:
#             item.setExpanded(True)
#
#     def _traverseNode(self, item, func, data):
#         """Traverse the child elements of the sideBar
#         :param item: item to traverse
#         :param func: function to perform on this element
#         :param data: optional data storage to pass to <func>
#         """
#         # process this element
#         func(item, data)
#
#         # find the other children
#         childCount = item.childCount()
#         for childNum in range(childCount):
#             self._traverseNode(item.child(childNum), func, data)
#
#     def _traverseTree(self, func, data):
#         """Traverse the top elements of the Sidebar
#         :param func: function to perform on all elements of the tree
#         :param data: optional data storage to pass to <func>
#         """
#         topCount = self.topLevelItemCount()
#         for itemNum in range(topCount):
#             item = self.topLevelItem(itemNum)
#             self._traverseNode(item, func, data)
#
#     def _blockSideBarEvents(self):
#         """Block all updates/signals/notifiers on the sidebar
#         """
#         self.setUpdatesEnabled(False)
#         self.blockSignals(True)
#         self.setBlankingAllNotifiers(True)
#
#     def _unblockSideBarEvents(self):
#         """Unblock all updates/signals/notifiers on the sidebar
#         """
#         self.setBlankingAllNotifiers(False)
#         self.blockSignals(False)
#         self.setUpdatesEnabled(True)
#
#     def _saveExpandedState(self):
#         """Save the current expanded state of items in the sideBar
#         """
#         if not self.sidebarBlocked:
#             self._blockSideBarEvents()
#             self._sideBarState = []
#             self._traverseTree(self._getExpanded, self._sideBarState)
#         self.increaseSidebarBlocking()
#
#     def _restoreExpandedState(self):
#         """Restore the current expanded state of items in the sideBar
#         """
#         self.decreaseSidebarBlocking()
#         if not self.sidebarBlocked:
#             self._fillSideBar(self.project)
#             self._traverseTree(self._setExpanded, self._sideBarState)
#             self._unblockSideBarEvents()
#
#     def _renameNmrResidueItem(self, data):  #obj:NmrResidue, oldPid:str):
#         """rename NmrResidue(s) from previous pid oldPid to current object pid"""
#
#         self._saveExpandedState()
#
#         obj = data[Notifier.OBJECT]
#         oldPid = data[Notifier.OLDPID]
#
#         if not oldPid.split(Pid.PREFIXSEP, 1)[1].startswith(obj._parent._id + Pid.IDSEP):
#             # Parent has changed - remove items from old location
#             import sip
#
#             for item in self._findItems(oldPid):
#                 sip.delete(item)  # this also removes child items
#
#         #    # item.setData(0, QtCore.Qt.DisplayRole, str(obj.pid))    # ejb - rename instead of delete
#         # else:
#         #   pass        # ejb - here just for a breakpoint
#
#         self._refreshParentNmrChain({Notifier.OBJECT: obj, Notifier.OLDPID: oldPid})  #obj, oldPid)
#
#         # for item in self._findItems(oldPid):
#         #   item.setData(0, QtCore.Qt.DisplayRole, str(obj.pid))    # ejb - rename instead of delete
#
#         self._restoreExpandedState()
#
#     def _removeItem(self, data):  # wrapperObject:AbstractWrapperObject):
#         """Removes sidebar item(s) for object with pid objPid, but does NOT delete the object.
#         Called when objects are deleted."""
#         import sip
#
#         obj = data[Notifier.OBJECT]
#         for item in self._findItems(obj.pid):
#             sip.delete(item)
#
#     def _findItems(self, objPid: str) -> list:  #QtGui.QTreeWidgetItem
#         """Find items that match objPid - returns empty list if no matches"""
#
#         if objPid[:2] in classesInSideBar:
#             result = self.findItems(objPid, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive, 0)
#
#         else:
#             result = []
#
#         return result
#
#     def setProjectName(self, project: Project):
#         """
#         (re)set project name in sidebar header.
#         """
#
#         self.projectItem.setText(0, project.name)
#
#     def _clearQTreeWidget(self, tree):
#         # clear contents of the sidebar and rebuild
#         iterator = QtGui.QTreeWidgetItemIterator(tree, QtGui.QTreeWidgetItemIterator.All)
#         while iterator.value():
#             iterator.value().takeChildren()
#             iterator += 1
#         i = tree.topLevelItemCount()
#         while i > -1:
#             tree.takeTopLevelItem(i)
#             i -= 1
#
#     def fillSideBar(self, project: Project):
#         """
#         Fills the sidebar with the relevant data from the project.
#         """
#
#         # disable updating/redrawing of the sideBar
#         self._saveExpandedState()
#
#         self._fillSideBar(project)
#
#         # re-enable updating/redrawing of the sideBar
#         self._restoreExpandedState()
#
#     def _fillSideBar(self, project: Project):
#         """
#         Fills the sidebar with the relevant data from the project.
#         """
#
#         self._populateSidebar()
#         self.setProjectName(project)
#
#         listOrder = [ky for ky in classesInSideBar.keys()]
#         tempKy = listOrder[0]
#         listOrder[0] = listOrder[1]
#         listOrder[1] = tempKy
#         new_dict = OrderedDict()
#         for ky in listOrder:
#             new_dict[ky] = classesInSideBar[ky]
#
#         for className, cls in new_dict.items():  # ejb - classesInSideBar.items()
#             objs = getattr(project, cls._pluralLinkName)
#             for obj in objs:
#                 self._createItem({Notifier.OBJECT: obj})
#             # dd = pid2Obj.get(className)
#             # if dd:
#             #   for obj in sorted(dd.values()):
#             #     self._createItem(obj)
#
#     #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#     # mouse events
#
#     # def _eventFilter(self, obj, event):
#     #     return super(SideBar, self).eventFilter(obj, event)
#
#     def dragEnterEvent(self, event, enter=True):
#         # if event.mimeData().hasFormat(ccpnmrJsonData):
#         #   data = event.mimeData().data(ccpnmrJsonData)
#         #   if 'test' in data:
#         #     print ('>>>_dragEnterEvent has ccpnmrJsonData')
#         #   else:
#         #     print ('>>>_dragEnterEvent empty')
#         # else:
#         #   print('>>>_dragEnterEvent ---')
#         # super(SideBar, self).dragEnterEvent(event)
#
#         if event.mimeData().hasUrls():
#             event.accept()
#         else:
#             pids = []
#             for item in self.selectedItems():
#                 if item is not None:
#                     objFromPid = self.project.getByPid(item.data(0, QtCore.Qt.DisplayRole))
#                     if objFromPid is not None:
#                         pids.append(objFromPid.pid)
#
#             itemData = json.dumps({'pids': pids})
#
#             # ejb - added so that itemData works with PyQt5
#             tempData = QtCore.QByteArray()
#             stream = QtCore.QDataStream(tempData, QtCore.QIODevice.WriteOnly)
#             stream.writeQString(itemData)
#             event.mimeData().setData(ccpnmrJsonData, tempData)
#
#             # event.mimeData().setData(ccpnmrJsonData, itemData)
#             event.mimeData().setText(itemData)
#             event.accept()
#
#     # def _startDrag(self, dropActions):
#     #   item = self.currentItem()
#     #   icon = item.icon()
#     #   data = QByteArray()
#     #   stream = QDataStream(data, QIODevice.WriteOnly)
#     #   stream << item.text() << icon
#     #   mimeData = QMimeData()
#     #   mimeData.setData("application/x-icon-and-text", data)
#     #   drag = QDrag(self)
#     #   drag.setMimeData(mimeData)
#     #   pixmap = icon.pixmap(24,24)
#     #   drag.setHotSpot(QPoint(12,12))
#     #   drag.setPixmap(pixmap)
#     #   if drag.start(Qt.MoveAction) == Qt.moveAction:
#     #     self.takeItem(self.row(item))
#
#     def _dragMoveEvent(self, event: QtGui.QMouseEvent):
#         """
#         Required function to enable dragging and dropping within the sidebar.
#         """
#         # super(SideBar, self).dragMoveEvent(event)
#         event.accept()
#
#     # def dragLeaveEvent(self, event):
#     #   # print ('>>>dragLeaveEvent %s' % str(event.type()))
#     #   super(SideBar, self).dragLeaveEvent(event)
#     #   # event.accept()
#
#     def _mouseMoveEvent(self, event):
#         event.accept()
#
#     def _mousePressEvent(self, event):
#         """
#         Re-implementation of the mouse press event so right click can be used to delete items from the
#         sidebar.
#         """
#
#         # if event.button() == QtCore.Qt.LeftButton:
#         #   pids = []
#         #   for item in self.selectedItems():
#         #     if item is not None:
#         #       objFromPid = self.project.getByPid(item.data(0, QtCore.Qt.DisplayRole))
#         #       if objFromPid is not None:
#         #         pids.append(objFromPid.pid)
#         #
#         #   itemData = json.dumps({'pids':pids, 'test':'thisDrag'})
#         #   mimeData = QtCore.QMimeData()
#         #   mimeData.setData(ccpnmrJsonData, itemData)
#         #   mimeData.setText(itemData)
#         #
#         #   drag = QtGui.QDrag(self)
#         #   drag.setMimeData(mimeData)
#         #   dropAction = drag.exec_(QtCore.Qt.CopyAction | QtCore.Qt.MoveAction, QtCore.Qt.CopyAction)
#
#         # if event.button() == QtCore.Qt.RightButton:
#         #   self._raiseContextMenu(event)
#         #   event.accept()
#         # else:
#         # item = self.itemAt(event.pos())
#         # if item:
#         #   text = item.text(0)
#         #   if ':' in text:
#         #
#         #     itemData = json.dumps({'pids':[text]})
#         #     mimeData = QtCore.QMimeData()
#         #     mimeData.setData(ccpnmrJsonData, itemData)
#         #     # mimeData.setText(itemData)
#         #     # pixmap = QtGui.QPixmap.grabWidget(item)
#         #     # pixmap = QtGui.QPixmap(item)
#         #     # item.render(pixmap)
#         #
#         #     drag = QtGui.QDrag(self)
#         #     drag.setMimeData(mimeData)
#         #     # drag.setPixmap(pixmap)
#         #
#         #     dropAction = drag.exec_(QtCore.Qt.CopyAction | QtCore.Qt.MoveAction, QtCore.Qt.CopyAction)
#         #   else:
#         #     super(SideBar, self).mousePressEvent(event)
#
#         # else:
#         # if self.multiSelect:
#         #   self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
#
#         event.accept()
#         super().mousePressEvent(event)
#
#     def _mouseReleaseEvent(self, event):
#         """
#         Re-implementation of the mouse press event so right click can be used to delete items from the
#         sidebar.
#         """
#         if event.button() == QtCore.Qt.RightButton:
#             self._raiseContextMenu(event)  # ejb - moved the context menu to button release
#             event.accept()
#         else:
#             QtWidgets.QTreeWidget.mouseReleaseEvent(self, event)
#
#     def _raiseContextMenu(self, event: QtGui.QMouseEvent):
#         """
#         Creates and raises a context menu enabling items to be deleted from the sidebar.
#         """
#         from ccpn.ui.gui.widgets.Menu import Menu
#
#         contextMenu = Menu('', self, isFloatWidget=True)
#         from functools import partial
#
#         # contextMenu.addAction('Delete', partial(self.removeItem, item))
#         objs = []
#         for item in self.selectedItems():
#             if item is not None:
#                 objFromPid = self.project.getByPid(item.data(0, QtCore.Qt.DisplayRole))
#                 if objFromPid is not None:
#                     objs.append(objFromPid)
#
#         if len(objs) > 0:
#             openableObjs = [obj for obj in objs if isinstance(obj, tuple(OpenObjAction.keys()))]
#             if len(openableObjs) > 0:
#                 contextMenu.addAction('Open as a module', partial(_openItemObject, self.mainWindow, openableObjs))
#                 spectra = [o for o in openableObjs if isinstance(o, Spectrum)]
#                 if len(spectra) > 0:
#                     contextMenu.addAction('Make SpectrumGroup From Selected', partial(self._createSpectrumGroup, spectra))
#
#             contextMenu.addAction('Delete', partial(self._deleteItemObject, objs))
#             canBeCloned = True
#             for obj in objs:
#                 if not hasattr(obj, 'clone'):  # TODO: possibly should check that is a method...
#                     canBeCloned = False
#                     break
#             if canBeCloned:
#                 contextMenu.addAction('Clone', partial(self._cloneObject, objs))
#             contextMenu.move(event.globalPos().x(), event.globalPos().y() + 10)
#             contextMenu.exec()
#
#     #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#     def raisePopup(self, obj, item):
#         # TODO move in a dict
#         if obj.shortClassName == 'SP':
#             popup = SpectrumPropertiesPopup(parent=self.mainWindow, mainWindow=self.mainWindow, spectrum=obj)
#             popup.exec_()
#             popup.raise_()
#         elif obj.shortClassName == 'PL':
#             popup = PeakListPropertiesPopup(parent=self.mainWindow, mainWindow=self.mainWindow, peakList=obj)
#             popup.exec_()
#             popup.raise_()
#         elif obj.shortClassName == 'IL':
#             popup = IntegralListPropertiesPopup(parent=self.mainWindow, mainWindow=self.mainWindow, integralList=obj)
#             popup.exec_()
#             popup.raise_()
#         elif obj.shortClassName == 'ML':
#             popup = MultipletListPropertiesPopup(parent=self.mainWindow, mainWindow=self.mainWindow, multipletList=obj)
#             popup.exec_()
#             popup.raise_()
#         elif obj.shortClassName == 'SG':
#             popup = SpectrumGroupEditor(parent=self.mainWindow, mainWindow=self.mainWindow, spectrumGroup=obj)
#             popup.exec_()
#             popup.raise_()
#         elif obj.shortClassName == 'SA':
#             popup = SamplePropertiesPopup(parent=self.mainWindow, mainWindow=self.mainWindow, sample=obj)
#             popup.exec_()
#             popup.raise_()
#         elif obj.shortClassName == 'SC':
#             popup = EditSampleComponentPopup(parent=self.mainWindow, mainWindow=self.mainWindow, sampleComponent=obj)
#             popup.exec_()
#             popup.raise_()
#         elif obj.shortClassName == 'SU':
#             popup = SubstancePropertiesPopup(parent=self.mainWindow, mainWindow=self.mainWindow, substance=obj)
#             popup.exec_()
#             # popup.raise_()
#         elif obj.shortClassName == 'NC':
#             popup = NmrChainPopup(parent=self.mainWindow, mainWindow=self.mainWindow, nmrChain=obj)
#             popup.exec_()
#             popup.raise_()
#         elif obj.shortClassName == 'NR':
#             popup = NmrResiduePopup(parent=self.mainWindow, mainWindow=self.mainWindow, nmrResidue=obj)
#             popup.exec_()
#             popup.raise_()
#         elif obj.shortClassName == 'NA':
#             popup = NmrAtomPopup(parent=self.mainWindow, mainWindow=self.mainWindow, nmrAtom=obj)
#             popup.exec_()
#             popup.raise_()
#         elif obj.shortClassName == 'CL':
#             popup = ChemicalShiftListPopup(parent=self.mainWindow, mainWindow=self.mainWindow, chemicalShiftList=obj)
#             popup.exec_()
#             popup.raise_()
#         elif obj.shortClassName == 'SE':
#             popup = StructurePopup(parent=self.mainWindow, mainWindow=self.mainWindow, structureEnsemble=obj)
#             popup.exec_()
#             popup.raise_()
#
#             # if self.mainWindow:
#             #   from ccpn.ui.gui.modules.StructureTable import StructureTableModule
#             #
#             #   self.structureTableModule = StructureTableModule(self.mainWindow, itemPid=obj.pid)
#             #   self.mainWindow.moduleArea.addModule(self.structureTableModule, position='bottom',
#             #                                   relativeTo=self.mainWindow.moduleArea)
#             #   self.mainWindow.pythonConsole.writeConsoleCommand("application.showStructureTable()")
#             #   self.project._logger.info("application.showStructureTable()")
#             #
#             # else:
#             #   showInfo('No mainWindow?', '')
#
#         elif obj.shortClassName == 'MC':
#             #to be decided when we design structure
#             info = showInfo('Not implemented yet!',
#                             'This function has not been implemented in the current version')
#         elif obj.shortClassName == 'MD':
#             #to be decided when we design structure
#             showInfo('Not implemented yet!',
#                      'This function has not been implemented in the current version')
#         elif obj.shortClassName == 'DS':
#             popup = DataSetPopup(parent=self.mainWindow, mainWindow=self.mainWindow, dataSet=obj)
#             popup.exec_()
#             popup.raise_()
#
#             # ejb - test DataSet
#             # if self.mainWindow:
#             #
#             #   # Use StructureTable for the moment
#             #
#             #   if obj.title is 'ensembleCCPN':
#             #     from ccpn.ui.gui.modules.StructureTable import StructureTableModule
#             #
#             #     self.structureTableModule = StructureTableModule(self.mainWindow, itemPid=obj.pid)
#             #     self.mainWindow.moduleArea.addModule(self.structureTableModule, position='bottom',
#             #                                     relativeTo=self.mainWindow.moduleArea)
#             #     self.mainWindow.pythonConsole.writeConsoleCommand("application.showDataSetStructureTable()")
#             #     self.project._logger.info("application.showDataSetStructureTable()")
#             #   else:
#             #     showInfo('Not implemented yet!',
#             #              'This function has not been implemented in the current version',
#             #              colourScheme=self.colourScheme)
#
#
#         elif obj.shortClassName == 'RL':
#             #to be decided when we design structure
#             showInfo('Not implemented yet!',
#                      'This function has not been implemented in the current version')
#         elif obj.shortClassName == 'RE':
#             #to be decided when we design structure
#             showInfo('Not implemented yet!',
#                      'This function has not been implemented in the current version')
#         # elif obj.shortClassName == 'IL':
#         #   # to be decided when we design structure
#         #
#         #   # popup = IntegralListPopup(parent=self.mainWindow, mainWindow=self.mainWindow, integralList=obj)   # ejb - temp
#         #   # popup.exec_()
#         #   # popup.raise_()
#         #
#         #   showInfo('Not implemented yet!',
#         #            'This function has not been implemented in the current version')
#         elif obj.shortClassName == 'NO':
#             popup = NotesPopup(parent=self.mainWindow, mainWindow=self.mainWindow, note=obj)
#             popup.exec_()
#             popup.raise_()
#
#             # if self._application.ui.mainWindow is not None:
#             #   mainWindow = self._application.ui.mainWindow
#             # else:
#             #   mainWindow = self._application._mainWindow
#             # self.notesEditor = NotesEditor(mainWindow.moduleArea, self.project,
#             #                                name='Notes Editor', note=obj)
#
#             # #FIXME:ED should be a popup or consistency
#             # if self.mainWindow:
#             #   self.notesEditor = NotesEditor(mainWindow=self.mainWindow, name='Notes Editor', note=obj)
#             #   self.mainWindow.moduleArea.addModule(self.notesEditor, position='bottom',
#             #                                   relativeTo=self.mainWindow.moduleArea)
#             #   self.mainWindow.pythonConsole.writeConsoleCommand("application.showNotesEditor()")
#             #   self.project._logger.info("application.showNotesEditor()")
#             # else:
#             #   showInfo('No mainWindow?', '', colourScheme=self.colourScheme)
#
#     def _createNewObject(self, item):
#         """Create new object starting from the <New> item
#         """
#         if item.text(0) in ["<New IntegralList>", "<New PeakList>", "<New MultipletList>", ]:
#             spectrum = self.project.getByPid(item.parent().text(0))
#             if item.text(0) == "<New PeakList>":
#                 spectrum.newPeakList()
#             elif item.text(0) == "<New IntegralList>":
#                 spectrum.newIntegralList()
#             elif item.text(0) == "<New MultipletList>":
#                 spectrum.newMultipletList()
#
#             # item.parent().sortChildren(0, QtCore.Qt.AscendingOrder)
#
#         else:
#
#             itemParent = self.project.getByPid(item.parent().text(0)) if Pid.Pid.isValid(item.parent().text(0)) else None
#
#             funcName = None
#             if itemParent is None:
#                 # Top level object - parent is project
#                 if item.parent().text(0) == 'Chains':
#                     popup = CreateChainPopup(parent=self.mainWindow, mainWindow=self.mainWindow)
#                     popup.exec_()
#                     popup.raise_()
#                     return
#                 elif item.parent().text(0) == 'Substances':
#                     popup = SubstancePropertiesPopup(parent=self.mainWindow, mainWindow=self.mainWindow,
#                                                      newSubstance=True)  # ejb - application=self.application,
#                     popup.exec_()
#                     # popup.raise_()        # included setModal(True) in the above as was not modal???
#                     return
#                 elif item.parent().text(0) == 'SpectrumGroups':
#                     popup = SpectrumGroupEditor(parent=self.mainWindow, mainWindow=self.mainWindow, addNew=True)
#                     popup.exec_()
#                     popup.raise_()
#                     return
#                 if item.parent().text(0) == 'NmrChains':
#                     popup = CreateNmrChainPopup(parent=self.mainWindow, mainWindow=self.mainWindow)
#                     popup.exec_()
#                     popup.raise_()
#                     return
#                 else:
#                     itemParent = self.project
#                     funcName = NEW_ITEM_DICT.get(item.parent().text(0))
#
#
#             else:
#                 # Lower level object - get parent from parentItem
#                 if itemParent.shortClassName == 'DS':
#                     popup = RestraintTypePopup(parent=self.mainWindow, mainWindow=self.mainWindow)
#                     popup.exec_()
#                     popup.raise_()
#                     restraintType = popup.restraintType
#                     if restraintType:
#
#                         # ejb - added here because not sure whether to put it in the popup yet
#                         try:
#                             ff = NEW_ITEM_DICT.get(itemParent.shortClassName)
#                             getattr(itemParent, ff)(restraintType)
#                         except Exception as es:
#                             showWarning('Restraints', 'Error modifying restraint type')
#
#                     return
#                 elif itemParent.shortClassName == 'SA':
#                     popup = EditSampleComponentPopup(parent=self.mainWindow, mainWindow=self.mainWindow, sample=itemParent, newSampleComponent=True)
#                     popup.exec_()
#                     popup.raise_()
#                     return
#                 else:
#                     funcName = NEW_ITEM_DICT.get(itemParent.shortClassName)
#
#                 # for i in range(item.childCount()):
#
#             if funcName is not None:
#                 newItem = getattr(itemParent, funcName)()
#                 # if funcName == 'newNmrResidue':
#                 #   newItem.parent().sortChildren(0, QtCore.Qt.AscendingOrder)
#
#             else:
#                 info = showInfo('Not implemented yet!',
#                                 'This function has not been implemented in the current version')


#===========================================================================================================
# SideBar handling class for handling tree structure
#===========================================================================================================

class _sidebarWidgetItem(QtWidgets.QTreeWidgetItem):
    """TreeWidgetItem for the new sidebar structure.
    Contains a link to the sidebar item.
    """

    def __init__(self, treeWidgetItem, sidebarItem):
        """Initialise the widget and set the link to the sidebar item.
        """
        super().__init__(treeWidgetItem)
        self._parent = treeWidgetItem
        self.sidebarItem = sidebarItem


class SidebarABC(NotifierBase):
    """
    Abstract base class defining various sidebar item types and methods
    """

    # subclassing
    itemType = None

    # ids
    _nextIndx = 0

    REBUILD = 'rebuild'
    RENAME = 'rename'
    _postBlockingActions = [None, REBUILD, RENAME]

    def __init__(self, name=None, usePidForName=False, klass=None, addNotifier=False, closed=True, add2NodesUp=False,
                 rebuildOnRename=None, callback=None, children=[], **kwds):
        super().__init__()

        self._indx = SidebarABC._nextIndx
        SidebarABC._nextIndx += 1

        if name is None and not usePidForName:
            raise ValueError('Either name needs to be defined or usePidForName needs to be True')
        self.name = name
        self.usePidForName = usePidForName  # flag; if True show pid rather then name

        self.klass = klass
        self.addNotifier = addNotifier  # add notifier for rename, delete, create of klass
        self.callback = callback  # callback for double click
        self.kwds = kwds  # kwd arguments passed to callback

        self.widget = None  # widget object
        self.closed = closed  # State of the tree widget
        self.add2NodesUp = add2NodesUp  # flag to indicate a widget that needs adding two nodes up in the tree
        self._postBlockingAction = None  # attribute to indicate action required post blocking the sidebar
        self.rebuildOnRename = rebuildOnRename  # Name of node up in the tree to rebuild on rename; not used when None

        self.sidebar = None  # reference to SideBar instance; set by buildTree
        self.obj = None  # reference to obj, e.g. a Project, Spectrum, etc instance; set by buildTree
        self.children = children
        self._children = []  # used by SidebarClassTreeItems methods
        self._parent = None  # connection to parent node
        self.level = 0  # depth level of the sidebar tree; increased for every node down, except children of 'class' nodes

    @property
    def givenName(self):
        """Return either obj.pid (depending on usePidForName), name or id (in that order)
        """
        if self.usePidForName and self.obj is not None:
            return self.obj.pid
        if self.name is not None:
            return self.name
        return self.id

    @property
    def id(self):
        """An unique identifier for self
        """
        id = '%s-%d' % (self.itemType, self._indx)
        return id

    @property
    def root(self):
        """Return the root of the tree
        """
        node = self
        while node._parent is not None:
            node = node._parent
        return node

    def get(self, *names):
        """traverse down the tree to get node defined by names.
        Skips over in 'class'-based nodes.
        """
        if len(names) == 0:
            return None

        if isinstance(self, (SidebarClassItems, SidebarClassTreeItems)):
            for child in self.children:
                if child.get(*names):
                    return child
            return None

        if self.name == names[0]:
            if len(names) == 1:
                return self
            elif len(names) >= 2:
                for child in self.children:
                    if child.get(*names[1:]):
                        return child

        return None

    def _getKlassChildren(self, obj, klass):
        """Get the children of <obj> by class type <klass>.
        """
        return obj._getChildrenByClass(klass)

    def _findParentNode(self, name):
        """Find the node up in the tree whose self.name == name or return self if name == 'self'
        """
        if name == 'self':
            return self
        # find the node
        node = self
        while node is not None and node.name != name:
            node = node._parent
        if node is None:
            raise RuntimeError('Failed to find parent node with name "%s" starting from %s' % (name, self))
        return node

    def _findChildNode(self, name):
        """Find the node across the tree whose self.name == name or return self if name == 'self'
        """
        if name == 'self' or self.name == name:
            return self

        # find the node
        for itm in self.children:
            node = itm._findChildNode(name)
            if node:
                return node

    def findChildNode(self, name):
        node = self._findChildNode(name)
        if node is None:
            raise RuntimeError('Failed to find child node with name "%s" starting from %s' % (name, self))
        return node

    def buildTree(self, parent, parentWidget, sidebar, obj, level=0):
        """Builds the tree from self downward
        """
        self._parent = parent
        self._parentWidget = parentWidget
        self.sidebar = sidebar
        self.obj = obj
        self.level = level

        if self.addNotifier and self.klass:
            # add the create/delete/rename notifiers to the parent
            triggers = self.kwds['triggers'] if 'triggers' in self.kwds else [Notifier.DELETE, Notifier.CREATE, Notifier.RENAME]

            # quick integrity test to make the tree is building correctly
            if not self.searchNotifiers(theObject=parent.obj, triggers=triggers, targetName=self.klass.className):
                self.setNotifier(parent.obj, triggers, targetName=self.klass.className, callback=self._update)

        # code like this needs to be in the sub-classes:
        # # make the widget
        # self.widget = self.givenName
        #
        # for itm in self.children:
        #     itm.buildTree(parent=self, sidebar=self.sidebar, obj=self.obj, level=self.level+1)

    def rebuildTree(self):
        """Rebuilds the tree starting from self
        """
        self.reset()
        self.buildTree(parent=self._parent, parentWidget=self._parentWidget, sidebar=self.sidebar, obj=self.obj, level=self.level)

    def printTree(self, string=None):
        """Print the tree from self downward
        """
        if string is not None:
            print(string)

        tabs = self._tabs
        name = self.givenName
        # Create a mark for 'characterization' of the node
        mark = ''
        if isinstance(self, (SidebarTree, SidebarClassTreeItems)):
            mark = '()' if self.closed else '(..)'
        if isinstance(self, (SidebarItem, SidebarClassItems)):
            mark = '&&'
        if isinstance(self, (SidebarClassItems, SidebarClassTreeItems)):
            mark = '>' + mark
            name = '[..%s..]' % name
        if self.add2NodesUp:
            mark = '^' + mark

        tabs = '    ' * len(tabs)
        string1 = '%s%3s %s' % (tabs, mark, name)
        print('(%1d) %-65s  %3d: %-14s obj=%-40s    widget=%s self=%s parent=%s' % (
            self.level, string1, self._indx, self.itemType, self.obj, self.widget, self, self._parent))
        for itm in self.children:
            itm.printTree()

    def _getExpanded(self, item, data: list):
        """Add the name of expanded item to the data list
        """
        if item.widget:
            expandedState = item.widget.isExpanded()
            item.closed = not expandedState
            if expandedState:
                data.append(item.widget.text(0))

    def _setExpanded(self, item, data: list):
        """Set the expanded flag if item is in data
        """
        if item.widget:
            if item.widget.text(0) in data:
                item.widget.setExpanded(True)
                item.closed = False

    def _storeExpandedStates(self):
        """Test storing the expanded items.
        """
        self._expandedState = []
        self._traverseTree(func=self._getExpanded, data=self._expandedState)

    def _restoreExpandedStates(self):
        """Test restoring the expanded items.
        """
        self._traverseTree(func=self._setExpanded, data=self._expandedState)
        self._expandedState = []

    def _setBlankingAllNotifiers(self, value):
        """Set the blanking state of all notifiers in the tree.
        """
        self.setBlankingAllNotifiers(value)

    def _traverseTree(self, sidebar=None, func=None, data=None):
        """Traverse the tree, applying <func> to all nodes

        :param sidebar: sidebar top level object
        :param func: function to perform on this element
        :param data: optional data storage to pass to <func>
        """
        if self.widget and func:
            # process the sidebarItem
            func(self, data)

        # if self._children:
        #     for child in self._children:
        #         child._traverseTree(sidebar, func, data)
        if self.children:
            for child in self.children:
                child._traverseTree(sidebar, func, data)

    def _traverseKlassTree(self, sidebar=None, func=None, data=None):
        """Traverse the tree, applying <func> to all nodes

        :param sidebar: sidebar top level object
        :param func: function to perform on this element
        :param data: optional data storage to pass to <func>
        """
        if self.klass and func:
            # process the sidebarItem
            func(self, data)

        if self.children:
            for child in self.children:
                child._traverseKlassTree(sidebar, func, data)

    def makeWidget(self, treeWidgetItem, givenName, dragEnabled=True):
        """Create the required widget here
        """
        newItem = None

        # Creation of QTreeWidgetItems, needs to be commented out if testing from the __main__ function
        # newItem = QtWidgets.QTreeWidgetItem(treeWidgetItem)
        newItem = _sidebarWidgetItem(treeWidgetItem, self)

        klass = self._parent.klass if self._parent else None
        _children = self._parent._children if self._parent else None
        if _children:
            newItem.setFlags(newItem.flags() & ~QtCore.Qt.ItemIsDropEnabled)
        else:
            newItem.setFlags(newItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
        newItem.setData(0, QtCore.Qt.DisplayRole, str(givenName))
        newItem.setData(1, QtCore.Qt.UserRole, self)
        newItem.setExpanded(not self.closed)

        return newItem if newItem else givenName

    def duplicate(self):
        """Return a duplicate of self
        """
        # Cannot use copy.copy() or deepcopy as it overwrites the indx
        result = self.__class__(name=self.name, usePidForName=self.usePidForName, klass=self.klass)

        for attr in 'addNotifier closed add2NodesUp callback sidebar obj _parent _postBlockingAction rebuildOnRename'.split():
            value = getattr(self, attr)
            setattr(result, attr, value)

        # recursively copy children and _children
        result.children = []
        for child in self.children:
            result.children.append(child.duplicate())
        result._children = []
        for child in self._children:
            result._children.append(child.duplicate())

        return result

    def rename(self, newName=None):
        """This function needs to rename the widget
        """
        self.oldName = self.name
        if newName is None:
            newName = self.givenName
        # rename the widget
        # self.widget = newName
        self.widget.setData(0, QtCore.Qt.DisplayRole, str(newName))
        self.name = newName

    def _getChildWidgets(self, widgets=[]):
        for itm in self.children:
            widg = itm.widget

            if widg and widg not in widgets:
                widgets.append(widg)

            widgets = itm._getChildWidgets(widgets)

        return widgets

    def _getChildren(self, children):
        for itm in self.children:
            widg = itm.widget

            # only add children with widgets
            if widg and itm not in children:
                children.append(itm)

            # children = itm._getChildren(children)

        return children

    def _reorderClassObjs(self, classObjs):
        """Reorder the classObjs into the tree.
        To be subclassed as required.
        """
        return classObjs

    def reset(self):
        """Resets the tree from self downward, deleting widget and notifiers
        """
        if (self.children):

            # recurse into the tree, otherwise just delete the notifiers
            for itm in self.children:
                itm.reset()

            # thisItem = self
            #
            # # if no widget then traverse up the tree until widget is found or no more parents
            # while thisItem and not thisItem.widget:
            #     thisItem = thisItem._parent
            #
            # children = self._getChildren([])
            # for itm in children:
            #     if thisItem and thisItem.widget:
            #         thisItem.widget.removeChild(itm.widget)

        if self.hasNotifier():
            getLogger().info('>>>reset deleteAllNotifiers %s' % str(self))
        self.deleteAllNotifiers()

        # remove the widgets associated with the sidebar items
        if self.widget and self.widget.parent():
            self.widget.parent().removeChild(self.widget)
            self.widget = None

        self._postBlockingAction = None

    def _update(self, cDict):
        """Callback for updating the node
        """

        trigger = cDict[Notifier.TRIGGER]

        # Define the actions
        if trigger == Notifier.RENAME and self.rebuildOnRename in [None, 'self']:
            # Just rename the node
            oldPid = cDict[Notifier.OLDPID]

            node = self.findChildNode(oldPid)
            rebuildOrRename = self.RENAME

        elif trigger == Notifier.RENAME:
            # Find the node to rebuild
            node = self._findParentNode(self.rebuildOnRename)
            rebuildOrRename = self.REBUILD

        elif trigger == Notifier.DELETE:
            # For now: we just rebuild from here on down the tree
            node = self
            rebuildOrRename = self.REBUILD

        elif trigger == Notifier.CREATE:
            # For now: we just rebuild from here on down the tree
            node = self
            rebuildOrRename = self.REBUILD

        elif trigger == Notifier.CHANGE:
            # For now: we just rebuild from here on down the tree
            node = self
            rebuildOrRename = self.REBUILD

        else:
            raise RuntimeError('Update callback: invalid trigger "%s"' % trigger)

        # do the action or tag the node for later
        if self.sidebar.isBlocked:
            node._postBlockingAction = rebuildOrRename

        elif rebuildOrRename == self.REBUILD:
            # rebuild the tree starting from node

            # store tree open/closed structure, process and restore
            node._storeExpandedStates()
            node.rebuildTree()
            node._restoreExpandedStates()

        elif rebuildOrRename == self.RENAME:
            # rename node

            # store tree open/closed structure, process and restore
            node._storeExpandedStates()
            node.rename()
            node._restoreExpandedStates()

    def _postBlockingUpdate(self):
        """Do the required action post-blocking; uses self._postBlockingAction
        """

        if self._postBlockingAction == self.REBUILD:
            self.rebuildTree()
            return  # all the children have been visited, reset and rebuild; we are done
        elif self._postBlockingAction == self.RENAME:
            self.rename()
            self._postBlockingAction = None
        # check the children
        for child in self.children:
            child._postBlockingUpdate()
        # _postBlockingAction would already be None here; however, for clarity
        self._postBlockingAction = None
        return

    @property
    def _tabs(self):
        "Number of tabs depending in self.level"
        return '\t' * self.level

    def __str__(self):
        return '<%s:%r>' % (self.id, self.name)

    def __repr__(self):
        return str(self)


class SidebarTree(SidebarABC):
    """
    A tree item that is fixed, displaying either a name or the pid of the associated V3 core object
    """
    itemType = 'Tree'

    def buildTree(self, parent, parentWidget, sidebar, obj, level=0):
        """Builds the tree from self downward
        """
        super().buildTree(parent=parent, parentWidget=parentWidget, sidebar=sidebar, obj=obj, level=level)  # this will do all the common things
        # make the widget
        # self.widget = self.givenName
        self.widget = self.makeWidget(parentWidget, self.givenName)

        # Build the children
        for itm in self.children:
            itm.buildTree(parent=self, parentWidget=self.widget, sidebar=self.sidebar, obj=self.obj, level=self.level + 1)



class SidebarItem(SidebarTree):
    """
    A static item, displaying either a name or the pid of the associated V3 core object
    Similar to Tree above, but different label
    """
    itemType = 'Item'


class SidebarClassABC(SidebarABC):
    """
    ABC to dynamically add type klass items
    """

    def buildTree(self, parent, parentWidget, sidebar, obj=None, level=0):
        """Builds the tree from self downward
        """
        super().buildTree(parent=parent, parentWidget=parentWidget, sidebar=sidebar, obj=obj, level=level)  # this will do all the common things

        # The node does not make a widget but adds the classobjects
        # classObjs = obj._getChildrenByClass(self.klass)
        classObjs = self._getKlassChildren(obj, self.klass)

        # Now dynamically change the tree and add and build the children
        self.children = []
        for classObj in classObjs:

            # skip the objects if they are due to be deleted
            if classObj._flaggedForDelete:
                continue

            if 'ClassTreeItems' in self.itemType:
                # if isinstance(self, SidebarClassTreeItems):
                # make a duplicate of the stored children to pass to the new SidebarItem
                children = [child.duplicate() for child in self._children]
                itm = SidebarTree(
                        name=classObj.pid, usePidForName=True, addNotifier=False,
                        callback=self.callback, add2NodesUp=True, children=children
                        )

            else:
                itm = SidebarItem(
                        name=classObj.pid, usePidForName=True, addNotifier=False,
                        callback=self.callback, add2NodesUp=True, children=[]
                        )
            self.children.append(itm)

            # pass the parent widget down the tree
            itm.buildTree(parent=self, parentWidget=self._parentWidget, sidebar=self.sidebar, obj=classObj, level=level)  # class items get same level as parent

    def reset(self):
        """Resets the tree from self downward
        """
        super().reset()
        self.children = []


class SidebarClassItems(SidebarClassABC):
    """A number of dynamically added items of type V3 core 'klass'
    """
    itemType = 'ClassItems'

    def __init__(self, name=None, klass=None, addNotifier=True, closed=True,
                 rebuildOnRename='self', callback=None, children=[], **kwds):
        if klass is None:
            raise ValueError('Undefined klass; definition is required for %s to function' % self.__class__.__name__)
        if len(children) > 0:
            raise ValueError('Sidebar "%s" cannot have children' % self.__class__.__name__)

        name = '%s-ClassItems' % klass.className
        super().__init__(name=name, klass=klass, addNotifier=addNotifier, closed=closed, rebuildOnRename=rebuildOnRename,
                         callback=callback, children=children, **kwds)

    def reset(self):
        super().reset()


class SidebarClassTreeItems(SidebarClassABC):
    """A Tree with a number of dynamically added items of type V3 core 'klass'
    """
    itemType = 'ClassTreeItems'

    def __init__(self, name=None, klass=None, addNotifier=True, closed=True,
                 rebuildOnRename='self', callback=None, children=[], **kwds):
        if klass is None:
            raise ValueError('Undefined klass; is required for %s item' % self.__class__.__name__)

        name = '%s-ClassTreeItems' % klass.className
        super().__init__(name=name, klass=klass, addNotifier=addNotifier, closed=closed, rebuildOnRename=rebuildOnRename,
                         callback=callback, children=children, **kwds)
        self._children = self.children  # Save them for reset/create, as we will dynamically change the tree on building


class SidebarClassSpectrumTreeItems(SidebarClassABC):
    """A Tree with a number of dynamically added items of type V3 core 'klass'
    """
    itemType = 'SpectrumClassTreeItems'

    def __init__(self, name=None, klass=None, addNotifier=True, closed=True,
                 rebuildOnRename='self', callback=None, children=[], **kwds):
        if klass is None:
            raise ValueError('Undefined klass; is required for %s item' % self.__class__.__name__)

        name = '%s-%s' % (self.itemType, klass.className)
        super().__init__(name=name, klass=klass, addNotifier=addNotifier, closed=closed, rebuildOnRename=rebuildOnRename,
                         callback=callback, children=children, **kwds)
        self._children = self.children  # Save them for reset/create, as we will dynamically change the tree on building

    def setNotifier(self, theObject: 'AbstractWrapperObject', triggers: list, targetName: str, callback: Callable[..., str], **kwds) -> Notifier:
        """subclass setNotifier to override classType for spectrumGroups.
        """
        if type(theObject) is SpectrumGroup:

            # special case needs to put the notifier on <project> for <spectra> belonging to spectrumGroups
            theObject = self.sidebar.project
            targetName = self.klass.className
            return super().setNotifier(theObject=theObject, triggers=triggers, targetName=targetName, callback=callback, **kwds)
        else:
            raise RuntimeError('Object is not of type SpectrumGroup')

    def _getKlassChildren(self, obj, klass):
        """Get the children of <obj> by class type <klass>.
        Get the spectra belonging to spectrumGroup.
        """
        return obj._getSpectrumGroupChildrenByClass(klass)


class SidebarClassNmrResidueTreeItems(SidebarClassABC):
    """A Tree with a number of dynamically added items of type V3 core 'klass'
    """
    itemType = 'NmrResidueClassTreeItems'

    def __init__(self, name=None, klass=None, addNotifier=True, closed=True,
                 rebuildOnRename='self', callback=None, children=[], **kwds):
        if klass is None:
            raise ValueError('Undefined klass; is required for %s item' % self.__class__.__name__)

        name = '%s-%s' % (self.itemType, klass.className)
        super().__init__(name=name, klass=klass, addNotifier=addNotifier, closed=closed, rebuildOnRename=rebuildOnRename,
                         callback=callback, children=children, **kwds)
        self._children = self.children  # Save them for reset/create, as we will dynamically change the tree on building

    def _getKlassChildren(self, obj, klass):
        """Get the children of <obj> by class type <klass>.
        Reorder the children according to the order in the nmrChain.
        """
        classObjs = obj._getChildrenByClass(klass)
        classObjs = self._reorderClassObjs(classObjs)

        return classObjs

    def _reorderClassObjs(self, classObjs):
        """Reorder the nmrResidues according to the order in the nmrChain.
        """
        if classObjs:
            nmrChain = classObjs[0].nmrChain
            return nmrChain.nmrResidues

        return classObjs


def NYI(*args, **kwds):
    print('>>>NYI: Not implemented yet', *args, **kwds)


def _rightMousePopup(className, dataPid, sideBarItem, *args, **kwds):
    """Perform action from the rightMouse menu for the specified class type.
    """
    if className is not None:
        popupFunc = NEW_ITEM_DICT.get(className)
        if popupFunc:
            project = sideBarItem.sidebar._project
            application = project.application
            application.popupFunc(position=None, relativeTo=None,  # put into a dict above
                                  *args, **kwds)


def _createNewObject(className, dataPid, sideBarItem):
    """Create a new object of instance className
    """
    itemParent = sideBarItem.obj
    if className is not None:
        funcName = NEW_ITEM_DICT.get(className)
        if funcName:
            newObject = getattr(itemParent, funcName)()
            return newObject


def _createNewObjectPopup(className, dataPid, sideBarItem, *args, **kwds):
    """Create a new object of instance className from a popup
    """
    if className is not None:
        popupFunc = NEW_ITEM_DICT.get(className)
        if popupFunc:
            project = sideBarItem.sidebar._project
            application = project.application
            popup = popupFunc(parent=application.ui.mainWindow, mainWindow=application.ui.mainWindow,
                              *args, **kwds)

            # make the popup appear in the middle of mainWindow
            popup.exec_()
            popup.raise_()


def _createNewRestraintListPopup(className, dataPid, sideBarItem):
    """Create a new object of instance className from a popup
    """
    if className is not None:
        popupFunc = NEW_ITEM_DICT.get(className)
        if popupFunc:
            project = sideBarItem.sidebar._project
            application = project.application
            popup = popupFunc(parent=application.ui.mainWindow, mainWindow=application.ui.mainWindow)

            # make the popup appear in the middle of mainWindow
            popup.exec_()
            popup.raise_()

            # specific to restraintList
            restraintType = popup.restraintType
            if restraintType:

                # ejb - added here because not sure whether to put it in the popup yet
                try:
                    itemParent = sideBarItem.obj
                    getattr(itemParent, NEWRESTRAINTLIST)(restraintType)
                except Exception as es:
                    showWarning('Restraints', 'Error modifying restraint type')


def _createNewSampleComponentPopup(className, dataPid, sideBarItem):
    """Create a new object of instance className from a popup
    """
    if className is not None:
        popupFunc = NEW_ITEM_DICT.get(className)
        if popupFunc:
            project = sideBarItem.sidebar._project
            application = project.application

            itemParent = sideBarItem.obj
            popup = popupFunc(parent=application.ui.mainWindow, mainWindow=application.ui.mainWindow,
                              sample=itemParent, newSampleComponent=True)

            # make the popup appear in the middle of mainWindow
            popup.exec_()
            popup.raise_()


def _raisePopup(dataPid, sideBarItem):
    """Raise an editor popup for the sideBar item
    """
    lowerCase = lambda s: s[:1].lower() + s[1:] if s else None

    obj = sideBarItem.obj
    className = obj.className
    if className is not None:
        popupFunc = EDIT_ITEM_DICT.get(className)
        if popupFunc:
            project = sideBarItem.sidebar._project
            application = project.application

            # make first letter a lowerCase and use for the popup
            objectDict = {lowerCase(className): obj}
            popup = popupFunc(parent=application.ui.mainWindow, mainWindow=application.ui.mainWindow,
                              **objectDict)

            # make the popup appear in the middle of mainWindow
            popup.exec_()
            popup.raise_()

        else:
            info = showInfo('Not implemented yet!',
                            'This function has not been implemented in the current version')


class SideBarStructure(object):
    """
    A class to manage the sidebar
    """

    _sidebarData = (  # "(" just to be able to continue on a new line; \ seems not to work

        SidebarTree('Project', usePidForName=False, klass=Project, closed=False, children=[

            #------ Spectra, PeakLists, MultipletLists, IntegralLists ------
            SidebarTree('Spectra', closed=True, children=[
                SidebarClassTreeItems(klass=Spectrum, children=[
                    SidebarTree('PeakLists', closed=True, children=[
                        SidebarItem('<New PeakList>', callback=partial(_createNewObject, PeakList.className)),
                        SidebarClassItems(klass=PeakList, callback=_raisePopup),
                        ]),
                    SidebarTree('MultipletLists', children=[
                        SidebarItem('<New MultipletList>', callback=partial(_createNewObject, MultipletList.className)),
                        SidebarClassItems(klass=MultipletList, callback=_raisePopup),
                        ]),
                    SidebarTree('IntegralLists', children=[
                        SidebarItem('<New IntegralList>', callback=partial(_createNewObject, IntegralList.className)),
                        SidebarClassItems(klass=IntegralList, callback=_raisePopup),
                        ]),
                    ], callback=_raisePopup),
                ]),

            #------ SpectrumGroups ------
            SidebarTree('SpectrumGroups', closed=True, children=[
                SidebarItem('<New SpectrumGroup>', callback=partial(_createNewObjectPopup, SpectrumGroup.className, addNew=True)),
                SidebarClassTreeItems(klass=SpectrumGroup, triggers=[Notifier.DELETE, Notifier.CREATE, Notifier.RENAME, Notifier.CHANGE], children=[
                    # SidebarClassItems(klass=Spectrum, rebuildOnRename='SpectrumGroup-ClassTreeItems', addNotifier=False, callback=_raisePopup),
                    # ], callback=_raisePopup),
                    SidebarClassSpectrumTreeItems(klass=Spectrum, children=[
                        SidebarTree('PeakLists', closed=True, children=[
                            SidebarItem('<New PeakList>', callback=partial(_createNewObject, PeakList.className)),
                            SidebarClassItems(klass=PeakList, callback=_raisePopup),
                            ]),
                        SidebarTree('MultipletLists', children=[
                            SidebarItem('<New MultipletList>', callback=partial(_createNewObject, MultipletList.className)),
                            SidebarClassItems(klass=MultipletList, callback=_raisePopup),
                            ]),
                        SidebarTree('IntegralLists', children=[
                            SidebarItem('<New IntegralList>', callback=partial(_createNewObject, IntegralList.className)),
                            SidebarClassItems(klass=IntegralList, callback=_raisePopup),
                            ]),
                        ], callback=_raisePopup),
                    ], callback=_raisePopup),
                ]),

            #------ Samples, SampleComponents ------
            SidebarTree('Samples', closed=True, children=[
                SidebarItem('<New Sample>', callback=partial(_createNewObject, Sample.className)),
                SidebarClassTreeItems(klass=Sample, rebuildOnRename='Sample-ClassTreeItems', children=[
                    SidebarItem('<New SampleComponent>', callback=partial(_createNewSampleComponentPopup, SampleComponent.className)),
                    SidebarClassItems(klass=SampleComponent, rebuildOnRename='Sample-ClassTreeItems', callback=_raisePopup),
                    ], callback=_raisePopup),
                ]),

            #------ Substances ------
            SidebarTree('Substances', closed=True, children=[
                SidebarItem('<New Substance>', callback=partial(_createNewObjectPopup, Substance.className, newSubstance=True)),
                SidebarClassItems(klass=Substance, callback=_raisePopup),
                ]),

            #------ Chains, Residues ------
            SidebarTree('Chains', closed=True, children=[
                SidebarItem('<New Chain>', callback=partial(_createNewObjectPopup, Chain.className)),
                SidebarClassTreeItems(klass=Chain, rebuildOnRename='Chain-ClassTreeItems', children=[
                    SidebarClassTreeItems(klass=Residue, rebuildOnRename='Chain-ClassTreeItems', callback=_raisePopup),
                    ], callback=_raisePopup),
                ]),

            #------ Complexes ------
            SidebarTree('Complexes', closed=True),

            #------ NmrChains, NmrResidues, NmrAtoms ------
            SidebarTree('NmrChains', closed=True, children=[
                SidebarItem('<New NmrChain>', callback=partial(_createNewObjectPopup, NmrChain.className)),
                SidebarClassTreeItems(klass=NmrChain, rebuildOnRename='NmrChain-ClassTreeItems', children=[
                    SidebarItem('<New NmrResidue>', callback=partial(_createNewObject, NmrResidue.className)),
                    SidebarClassNmrResidueTreeItems(klass=NmrResidue, rebuildOnRename='NmrChain-ClassTreeItems', children=[
                        SidebarItem('<New NmrAtom>', callback=partial(_createNewObject, NmrAtom.className)),
                        SidebarClassItems(klass=NmrAtom, rebuildOnRename='NmrChain-ClassTreeItems', callback=_raisePopup),
                        ], callback=_raisePopup),
                    ], callback=_raisePopup),
                ]),

            #------ ChemicalShiftLists ------
            SidebarTree('ChemicalShiftLists', closed=True, children=[
                SidebarItem('<New ChemicalShiftList>', callback=partial(_createNewObject, ChemicalShiftList.className)),
                SidebarClassTreeItems(klass=ChemicalShiftList, callback=_raisePopup),
                ]),

            #------ StructureEnsembles ------
            SidebarTree('StructureEnsembles', closed=True, children=[
                SidebarItem('<New StructureEnsemble>', callback=partial(_createNewObject, StructureEnsemble.className)),
                SidebarClassItems(klass=StructureEnsemble, callback=_raisePopup),
                ]),

            #------ DataSets ------
            SidebarTree('DataSets', closed=True, children=[
                SidebarItem('<New DataSet>', callback=partial(_createNewObject, DataSet.className)),
                SidebarClassTreeItems(klass=DataSet, rebuildOnRename='DataSet-ClassTreeItems', children=[
                    SidebarItem('<New ResidueList>', callback=partial(_createNewRestraintListPopup, RestraintList.className)),
                    SidebarClassTreeItems(klass=RestraintList, rebuildOnRename='DataSet-ClassTreeItems', callback=_raisePopup),
                    ], callback=_raisePopup),
                ]),

            #------ Notes ------
            SidebarTree('Notes', closed=True, children=[
                SidebarItem('<New Note>', callback=partial(_createNewObject, Note.className)),
                SidebarClassItems(klass=Note, callback=_raisePopup),
                ]),

            ])
    )  # end _sidebarData

    def _init(self):
        self._sidebarBlockingLevel = 0
        self._project = None
        self._sidebar = None

    def reset(self):
        """Resets all
        """
        self._sidebarData.reset()

    def clearSideBar(self):
        """Clear the sideBar if widgets and notifiers.
        """
        self._sidebarData.reset()

    def buildTree(self, project):
        """Builds the tree from project; returns self
        """
        self._project = project
        self.reset()
        self._sidebarData.buildTree(parent=None, parentWidget=self._sidebar, sidebar=self._sidebar, obj=self._project)  # This is the root

        # set the tree name to the id (not pid)
        self.setProjectName(project)
        return self

    def setProjectName(self, project: Project):
        """(re)Set project name in sidebar header.
        """
        self._sidebarData.widget.setText(0, project.name)
        self._sidebarData.name = project.name

    def rebuildTree(self):
        """Rebuilds the Tree
        """
        self.buildTree(self._project)

    def setSidebar(self, sidebar):
        """Set the sidebar widget
        """
        self._sidebar = sidebar

    def printTree(self, string=None):
        """prints the tree; optionally prints string
        """
        self._sidebarData.printTree(string=string)

    @property
    def isBlocked(self):
        """True if sidebar is blocked
        """
        return self._sidebarBlockingLevel > 0

    def increaseSidebarBlocking(self):
        """increase level of blocking
        """
        if self._sidebarBlockingLevel == 0:
            self._blockSideBarEvents()
            self._sidebarData._storeExpandedStates()
        self._sidebarBlockingLevel += 1

    def decreaseSidebarBlocking(self):
        """Reduce level of blocking - when level reaches zero, Sidebar is unblocked
        """
        if self._sidebarBlockingLevel > 0:
            self._sidebarBlockingLevel -= 1
            # check if we arrived at level zero; if so call post-blocking update
            if self._sidebarBlockingLevel == 0:
                self._sidebarData._postBlockingUpdate()
                self._sidebarData._restoreExpandedStates()
                self._unblockSideBarEvents()
        else:
            raise RuntimeError('Error: cannot decrease sidebar blocking below 0')

    def getSideBarItem(self, name):
        """Search for a named item in the tree
        """
        return self._sidebarData.get(name)

    @staticmethod
    def _setBlankingState(self, value):
        """Set the blanking state of the nodes.
        """
        self.setBlankingAllNotifiers(value)

    def setBlankingAllNotifiers(self, value):
        self._sidebarData._traverseKlassTree(self, self._setBlankingState, value)

#===========================================================================================================
# New sideBar to handle new notifiers
#===========================================================================================================


class NewSideBar(QtWidgets.QTreeWidget, SideBarStructure, Base, NotifierBase):
    """
    New sideBar class with new sidebar tree handling
    """
    def __init__(self, parent=None, mainWindow=None, multiSelect=True):

        super().__init__(parent)
        Base._init(self, acceptDrops=True)
        SideBarStructure._init(self)

        self.multiSelect = multiSelect
        if self.multiSelect:
            self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.mainWindow = parent
        self.application = self.mainWindow.application

        self.setFont(sidebarFont)
        self.header().hide()
        self.setDragEnabled(True)
        self.setExpandsOnDoubleClick(False)
        self.setMinimumWidth(200)

        self.setDragDropMode(self.DragDrop)
        self.setAcceptDrops(True)

        self.setGuiNotifier(self, [GuiNotifier.DROPEVENT], [DropBase.URLS, DropBase.PIDS],
                            self._processDroppedItems)

        self.itemDoubleClicked.connect(self._raiseObjectProperties)

    def _clearQTreeWidget(self, tree):
        """Clear contents of the sidebar.
        """
        iterator = QtWidgets.QTreeWidgetItemIterator(tree, QtWidgets.QTreeWidgetItemIterator.All)
        while iterator.value():
            iterator.value().takeChildren()
            iterator += 1
        i = tree.topLevelItemCount()
        while i > -1:
            tree.takeTopLevelItem(i)
            i -= 1

    def buildTree(self, project):
        """Build the new tree structure from the project.
        """
        # self._clearQTreeWidget(self)
        self.clearSideBar()
        self.project = project
        self.setSidebar(sidebar=self)
        super().buildTree(project)

    def _raiseObjectProperties(self, item):
        """Get object from Pid and dispatch call depending on type.
        """
        dataPid = item.data(0, QtCore.Qt.DisplayRole)
        sideBarObject = item.data(1, QtCore.Qt.UserRole)
        callback = sideBarObject.callback

        if callback:
            callback(dataPid, sideBarObject)

    def clearSideBar(self):
        """Completely clear and reset the sidebar of widgets and notifiers.
        """
        super().clearSideBar()
        self._clearQTreeWidget(self)

    def mouseReleaseEvent(self, event):
        """Re-implementation of the mouse press event so right click can be used to delete items from the
        sidebar.
        """
        if event.button() == QtCore.Qt.RightButton:
            self._raiseContextMenu(event)  # ejb - moved the context menu to button release
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        """Handle drag enter event to create a new drag/drag item.
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            pids = []
            for item in self.selectedItems():
                if item is not None:

                    dataPid = item.data(0, QtCore.Qt.DisplayRole)
                    sideBarObject = item.data(1, QtCore.Qt.UserRole)

                    if sideBarObject.obj:
                        pids.append(str(sideBarObject.obj.pid))

            itemData = json.dumps({'pids': pids})

            tempData = QtCore.QByteArray()
            stream = QtCore.QDataStream(tempData, QtCore.QIODevice.WriteOnly)
            stream.writeQString(itemData)
            event.mimeData().setData(ccpnmrJsonData, tempData)
            event.mimeData().setText(itemData)

            event.accept()

    def dragMoveEvent(self, event):
        """Required function to enable dragging and dropping within the sidebar.
        """
        if event.mimeData().hasUrls():
            # accept external events
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            if isinstance(event.source(), NewSideBar):      #(SideBar, NewSideBar)):
                # disable/ignore internal move events
                event.ignore()
            else:
                super().dragMoveEvent(event)

    def _cloneObject(self, objs):
        """Clones the specified objects.
        """
        for obj in objs:
            obj.clone()

    def _raiseContextMenu(self, event: QtGui.QMouseEvent):
        """Creates and raises a context menu enabling items to be deleted from the sidebar.
        """
        contextMenu = Menu('', self, isFloatWidget=True)

        objs = []
        for item in self.selectedItems():
            if item is not None:

                dataPid = item.data(0, QtCore.Qt.DisplayRole)
                sideBarObject = item.data(1, QtCore.Qt.UserRole)

                objFromPid = self.project.getByPid(dataPid)
                if objFromPid is not None:
                    objs.append(objFromPid)

        if len(objs) > 0:
            openableObjs = [obj for obj in objs if isinstance(obj, tuple(OpenObjAction.keys()))]
            if len(openableObjs) > 0:
                contextMenu.addAction('Open as a module', partial(_openItemObject, self.mainWindow, openableObjs))
                spectra = [o for o in openableObjs if isinstance(o, Spectrum)]
                if len(spectra) > 0:
                    contextMenu.addAction('Make SpectrumGroup From Selected', partial(_createSpectrumGroup, spectra))

            contextMenu.addAction('Delete', partial(self._deleteItemObject, objs))
            canBeCloned = True
            for obj in objs:
                if not hasattr(obj, 'clone'):  # TODO: possibly should check that is a method...
                    canBeCloned = False
                    break
            if canBeCloned:
                contextMenu.addAction('Clone', partial(self._cloneObject, objs))
            contextMenu.move(event.globalPos().x(), event.globalPos().y() + 10)
            contextMenu.exec()

    def _deleteItemObject(self, objs):
        """Removes the specified item from the sidebar and deletes it from the project.
        NB, the clean-up of the side bar is done through notifiers
        """
        from ccpn.core.lib.ContextManagers import undoBlockManager

        try:
            with undoBlockManager():
                for obj in objs:
                    if obj:
                        # just delete the object
                        obj.delete()

        except Exception as es:
            showWarning('Delete', str(es))

        #  Force repaint if GL windows
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitEvent(triggers=[GLNotifier.GLALLPEAKS, GLNotifier.GLALLINTEGRALS, GLNotifier.GLALLMULTIPLETS])

    def _processDroppedItems(self, data):
        """Handle the dropped urls
        """
        # CCPN INTERNAL. Called also from module area and GuiStrip. They should have same behaviour

        objs = []
        for url in data.get('urls', []):
            getLogger().debug('>>> dropped: ' + str(url))

            dataType, subType, usePath = ioFormats.analyseUrl(url)
            if dataType == 'Project' and subType in (ioFormats.CCPN,
                                                     ioFormats.NEF,
                                                     ioFormats.NMRSTAR,
                                                     ioFormats.SPARKY):

                okToContinue = self.mainWindow._queryCloseProject(title='Load %s project' % subType,
                                                                  phrase='create a new')
                if okToContinue:
                    with progressManager(self.mainWindow, 'Loading project... ' + url):
                        with catchExceptions():
                            obj = self.application.loadProject(url)

                        if isinstance(obj, Project):
                            try:
                                # obj._mainWindow._newSideBar.fillSideBar(obj)
                                obj._mainWindow._newSideBar.buildTree(obj)
                                obj._mainWindow.show()
                                QtWidgets.QApplication.setActiveWindow(obj._mainWindow)

                            except Exception as es:
                                getLogger().warning('Error: %s' % str(es))

            else:
                # with progressManager(self.mainWindow, 'Loading data... ' + url):
                try:  #  Why do we need this try?
                    data = self.project.loadData(url)
                    if data:
                        objs.extend(data)
                except Exception as es:
                    getLogger().warning('loadData Error: %s' % str(es))
        return objs

    def _blockSideBarEvents(self):
        """Block all updates/signals/notifiers on the sidebar
        """
        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        # self.setBlankingAllNotifiers(True)

    def _unblockSideBarEvents(self):
        """Unblock all updates/signals/notifiers on the sidebar
        """
        # self.setBlankingAllNotifiers(False)
        self.blockSignals(False)
        self.setUpdatesEnabled(True)

    def selectPid(self, pid):

        ws = self._findItems(pid)  #not sure why this returns a list!
        for i in ws:
            self.setCurrentItem(i)


#------------------------------------------------------------------------------------------------------------------
# Emulate V3 objects
#------------------------------------------------------------------------------------------------------------------

class Obj():
    def __init__(self, klass, *ids):
        self.klass = klass
        self.pid = Pid.new(klass.shortClassName, *ids)

    def _getChildrenByClass(self, klass):
        # emulate klass objs
        classObjs = []
        for i in range(2):
            id = '%s_%s' % (klass.className, i)
            classObjs.append(Obj(klass, self.pid.id, id))
        return classObjs

    def __str__(self):
        return '<Obj:%r>' % self.pid

    def __repr__(self):
        return str(self)


#------------------------------------------------------------------------------------------------------------------
# Testing
#------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    print('\n')

    # pid = Pid.new('PR','test')
    project = Obj(Project, 'test')

    sidebar = SideBarStructure()
    sidebar.printTree('\n==> before building')

    sidebar.buildTree(project)
    sidebar.printTree('\n==> after building')

    project.pid = Pid.new('PR', 'test2')
    sidebar._sidebarData.rename()
    sidebar.printTree('\n==> after project rename')

    # sidebar.reset()
    # sidebar.printTree('\n==> after reset')
    # sidebar.buildTree(project)

    subTree = sidebar._sidebarData.get('Project', 'Spectra')
    subTree.printTree('\n--- subtree ---')
    subTree.reset()
    sidebar.printTree('\n==> after subtree reset')
    sidebar.increaseSidebarBlocking()
    subTree._update({'trigger': 'create'})
    sidebar.printTree('\n==> after blocked update')
    sidebar.decreaseSidebarBlocking()
    sidebar.printTree('\n==> after decrease blocking')
