"""
Module Documentation here
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-02-09 11:04:17 +0000 (Wed, February 09, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-05-04 17:15:05 +0000 (Mon, May 04, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================
import numpy as np
import os
from functools import partial
from collections import OrderedDict

import pandas as pd

from PyQt5 import QtGui, QtWidgets, QtCore
from contextlib import contextmanager
from dataclasses import dataclass

from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import ImportTreeCheckBoxes, RENAMEACTION, BADITEMACTION
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.GuiTable import GuiTable
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.framework.lib.ccpnNef import CcpnNefIo
from ccpn.framework.lib.ccpnNef.CcpnNefCommon import nef2CcpnClassNames
from ccpn.core.lib.ContextManagers import catchExceptions
from ccpn.core.lib.Pid import Pid
from ccpn.core.Project import Project

from ccpn.util.nef import StarIo
from ccpn.util.nef import NefImporter as Nef
from ccpn.util.Logging import getLogger
from ccpn.util.PrintFormatter import PrintFormatter
from ccpn.util.AttrDict import AttrDict
from ccpn.util.OrderedSet import OrderedSet

from ccpn.ui.gui.widgets.Font import getFontHeight, setWidgetFont, TABLEFONT
from ccpn.ui.gui.guiSettings import getColours, BORDERNOFOCUS
from ccpn.ui.gui.widgets.MoreLessFrame import MoreLessFrame
from ccpn.ui.gui.widgets.TextEditor import TextEditor


INVALIDTEXTROWCHECKCOLOUR = QtGui.QColor('crimson')
INVALIDTEXTROWNOCHECKCOLOUR = QtGui.QColor('darkorange')
INVALIDBUTTONCHECKCOLOUR = QtGui.QColor('lightpink')
INVALIDBUTTONNOCHECKCOLOUR = QtGui.QColor('navajowhite')
INVALIDTABLEFILLCHECKCOLOUR = QtGui.QColor('lightpink')
INVALIDTABLEFILLNOCHECKCOLOUR = QtGui.QColor('navajowhite')

CHAINS = 'chains'
NMRCHAINS = 'nmrChains'
RESTRAINTTABLES = 'restraintTables'
CCPNTAG = 'ccpn'
SKIPPREFIXES = 'skipPrefixes'
EXPANDSELECTION = 'expandSelection'

PulldownListsMinimumWidth = 200
LineEditsMinimumWidth = 195
NotImplementedTipText = 'This option has not been implemented yet'
DEFAULTSPACING = (3, 3)
TABMARGINS = (1, 10, 10, 1)  # l, t, r, b
ZEROMARGINS = (0, 0, 0, 0)  # l, t, r, b
COLOURALLCOLUMNS = False

NEFFRAMEKEY_IMPORT = 'nefObject'
NEFFRAMEKEY_ENABLECHECKBOXES = 'enableCheckBoxes'
NEFFRAMEKEY_ENABLERENAME = 'enableRename'
NEFFRAMEKEY_ENABLEFILTERFRAME = 'enableFilterFrame'
NEFFRAMEKEY_ENABLEMOUSEMENU = 'enableMouseMenu'
NEFFRAMEKEY_PATHNAME = 'pathName'

NEFDICTFRAMEKEYS = {NEFFRAMEKEY_IMPORT           : (Nef.NefImporter, Project),
                    NEFFRAMEKEY_ENABLECHECKBOXES : bool,
                    NEFFRAMEKEY_ENABLERENAME     : bool,
                    NEFFRAMEKEY_ENABLEFILTERFRAME: bool,
                    NEFFRAMEKEY_ENABLEMOUSEMENU  : bool,
                    NEFFRAMEKEY_PATHNAME         : str,
                    }
NEFDICTFRAMEKEYS_REQUIRED = (NEFFRAMEKEY_IMPORT,)


class NefDictFrame(Frame):
    """
    Class to handle a nef dictionary editor
    """
    EDITMODE = True
    handleSaveFrames = {}
    handleParentGroups = {}
    _setBadSaveFrames = {}
    applyCheckBoxes = {}

    DEFAULTMARGINS = (8, 8, 8, 8)  # l, t, r, b

    def __init__(self, parent, mainWindow, nefLoader, pathName,
                 enableCheckBoxes=False, enableRename=False,
                 enableFilterFrame=False, enableMouseMenu=False,
                 showBorder=True, borderColour=None, _splitterMargins=DEFAULTMARGINS,
                 **kwds):
        """Initialise the widget"""
        super().__init__(parent, setLayout=True, spacing=DEFAULTSPACING, **kwds)

        self._parent = parent
        self.mainWindow = mainWindow
        if mainWindow:
            self.mainWindow = mainWindow
            self.application = mainWindow.application
            self.project = mainWindow.project
            self._nefReader = CcpnNefIo.CcpnNefReader(self.application)
            self._nefWriter = CcpnNefIo.CcpnNefWriter(self.project)
        # else:
        #     # to @ED: do not write code that
        #     self.mainWindow = None
        #     self.application = None
        #     self.project = None
        #     self._nefReader = None
        #     self._nefWriter = None

        self._primaryProject = True
        self.showBorder = showBorder
        self._borderColour = borderColour or QtGui.QColor(getColours()[BORDERNOFOCUS])
        self._enableCheckBoxes = enableCheckBoxes
        self._enableRename = enableRename
        self._enableFilterFrame = enableFilterFrame
        self._enableMouseMenu = enableMouseMenu
        self._pathName = pathName
        self._collections = {}

        # self._nefImporterClass = nefImporterClass
        # set the nef object - nefLoader/nefDict
        # self._initialiseNefLoader(nefObject, _ignoreError=True)
        self._nefLoader = nefLoader
        self._nefDict = nefLoader.data
        self._primaryProject = False

        # set up the widgets
        self._setWidgets()
        self._setCallbacks()

        # additional settings
        self._minusIcon = Icon('icons/minus.png')
        self._plusIcon = Icon('icons/plus.png')
        self._nefWidgets = []
        self.valid = None

        # needs to be done this way otherwise _splitterMargins is 'empty' or clashes with frame stylesheet
        self.setContentsMargins(*_splitterMargins)

        # define the list of dicts for comparing object names
        self._contentCompareDataBlocks = ()

        # add the rename action to the treeview actions
        self.nefTreeView.setActionCallback(RENAMEACTION, self._autoRenameItem)

        # add the rename action to the treeview actions
        self.nefTreeView.setActionCallback(BADITEMACTION, self._checkBadItem)

    def paintEvent(self, ev):
        """Paint the border to the screen
        """
        if not self.showBorder:
            return

        # create a rectangle and painter over the widget - shrink by 1 pixel to draw correctly
        p = QtGui.QPainter(self)
        rgn = self.rect()
        rgn = QtCore.QRect(rgn.x(), rgn.y(), rgn.width() - 1, rgn.height() - 1)

        p.setPen(QtGui.QPen(self._borderColour, 1))
        p.drawRect(rgn)
        p.end()

    # def _initialiseProject(self, mainWindow, application, project):
    #     """Intitialise the project setting - ONLY REQUIRED FOR TESTING when mainWindow doesn't exist
    #     """
    #     # set the project
    #     self.mainWindow = mainWindow
    #     self.application = application
    #     self.project = project
    #     if mainWindow is None:
    #         self.mainWindow = AttrDict()
    #
    #     # set the new values for application and project
    #     self.mainWindow.application = application
    #     self.mainWindow.project = project
    #
    #     # initialise the base structure from the project
    #     self.nefTreeView._populateTreeView(project)
    #
    #     self._nefReader = CcpnNefIo.CcpnNefReader(self.application)
    #     self._nefWriter = CcpnNefIo.CcpnNefWriter(self.project)

    # def _initialiseNefLoader(self, nefObject=None, _ignoreError=False):
    #     if not (nefObject or _ignoreError):
    #         raise TypeError('nefObject must be defined')
    #
    #     self._nefLoader = None
    #     self._nefDict = None
    #     if isinstance(nefObject, self._nefImporterClass):
    #         self._nefLoader = nefObject
    #         self._nefDict = nefObject._nefDict
    #         self._primaryProject = False
    #     elif isinstance(nefObject, Project):
    #         self.project = nefObject
    #         self._nefLoader = self._nefImporterClass(errorLogging=Nef.el.NEF_STANDARD, hidePrefix=True)
    #         self._nefWriter = CcpnNefIo.CcpnNefWriter(self.project)
    #         self._nefDict = self._nefLoader._nefDict = self._nefWriter.exportProject(expandSelection=True, pidList=None)

    def _setCallbacks(self):
        """Set the mouse callback for the treeView
        """
        self.nefTreeView.itemClicked.connect(self._nefTreeClickedCallback)

    def _setWidgets(self):
        """Setup the unpopulated widgets for the frame
        """
        self._headerFrameOuter = Frame(self, setLayout=True, showBorder=False, grid=(0, 0),
                                       hAlign='left', hPolicy='ignored', vPolicy='fixed')
        self.headerFrame = Frame(self._headerFrameOuter, setLayout=True,
                                 grid=(0, 0))

        self.headerLabel = Label(self.headerFrame, text='FRAMEFRAME', grid=(0, 0), gridSpan=(1, 3))
        self.verifyButton = Button(self.headerFrame, text='Verify Now', grid=(1, 0),
                                   callback=self._verifyPopulate)
        self.verifyButton.setVisible(not self._primaryProject)

        _verifyLabel = Label(self.headerFrame, 'always verify', grid=(1, 1), hPolicy='minimum', vPolicy='minimum')
        self.verifyCheckBox = CheckBox(self.headerFrame, grid=(1, 2), checked=False, checkable=True)
        _verifyLabel.setVisible(not self._primaryProject)
        self.verifyCheckBox.setVisible(not self._primaryProject)
        self.headerFrame.getLayout().setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)

        # add the pane for the treeview/tables
        self._paneSplitter = Splitter(self, setLayout=True, horizontal=True)

        # add the pane for the treeview/tables
        self._treeSplitter = Splitter(self, setLayout=True, horizontal=False)

        # set the top frames
        self._treeFrame = Frame(self, setLayout=True, showBorder=False, grid=(0, 0))
        self._infoFrame = Frame(self, setLayout=True, showBorder=False, grid=(0, 0))

        # must be added this way to fill the frame
        self.getLayout().addWidget(self._paneSplitter, 1, 0)
        self._paneSplitter.addWidget(self._treeSplitter)
        self._paneSplitter.addWidget(self._infoFrame)
        self._paneSplitter.setChildrenCollapsible(False)
        self._paneSplitter.setStretchFactor(0, 1)
        self._paneSplitter.setStretchFactor(1, 2)
        # self._paneSplitter.setStyleSheet("QSplitter::handle { background-color: gray }")
        self._paneSplitter.setSizes([10000, 15000])

        self._treeSplitter.addWidget(self._treeFrame)
        # self._treeSplitter.addWidget(self._infoFrame)
        self._treeSplitter.setChildrenCollapsible(False)
        self._treeSplitter.setStretchFactor(0, 1)
        self._treeSplitter.setStretchFactor(1, 2)
        # self._treeSplitter.setStyleSheet("QSplitter::handle { background-color: gray }")
        self._treeSplitter.setSizes([10000, 15000])

        # # treeFrame (left frame)
        # self._treeOptionsFrame = Frame(self._treeFrame, setLayout=True, showBorder=False, grid=(0, 0))
        # self.buttonCCPN = CheckBox(self._treeOptionsFrame, checked=True,
        #                            text='include CCPN tags',
        #                            grid=(0, 0), hAlign='l')
        # self.buttonExpand = CheckBox(self._treeOptionsFrame, checked=False,
        #                              text='expand selection',
        #                              grid=(1, 0), hAlign='l')

        self.nefTreeView = ImportTreeCheckBoxes(self._treeFrame, project=self.project, grid=(1, 0),
                                                includeProject=True, enableCheckBoxes=self._enableCheckBoxes,
                                                enableMouseMenu=self._enableMouseMenu,
                                                pathName=os.path.basename(self._pathName) if self._pathName else None,
                                                multiSelect=True)

        # info frame (right frame)
        self._optionsSplitter = Splitter(self._infoFrame, setLayout=True, horizontal=False)
        self._infoFrame.getLayout().addWidget(self._optionsSplitter, 0, 0)

        self.tablesFrame = Frame(self._optionsSplitter, setLayout=True, showBorder=False, grid=(0, 0))
        self._optionsFrame = Frame(self._optionsSplitter, setLayout=True, showBorder=False, grid=(1, 0))
        self._optionsSplitter.addWidget(self.tablesFrame)
        self._optionsSplitter.addWidget(self._optionsFrame)

        self._frameOptionsNested = Frame(self._optionsFrame, setLayout=True, showBorder=False, grid=(1, 0))
        self.frameOptionsFrame = Frame(self._frameOptionsNested, setLayout=True, showBorder=False, grid=(1, 0))  #, vAlign='t')
        self.fileFrame = Frame(self._optionsFrame, setLayout=True, showBorder=False, grid=(2, 0))
        self._filterLogFrame = MoreLessFrame(self._optionsFrame, name='Filter Log', showMore=False, grid=(3, 0), gridSpan=(1, 1))
        self._treeSplitter.addWidget(self._filterLogFrame)

        # self.tablesFrame = Frame(self._infoFrame, setLayout=True, showBorder=False, grid=(0, 0))
        # self._frameOptionsNested = Frame(self._infoFrame, setLayout=True, showBorder=False, grid=(1, 0))
        # self.frameOptionsFrame = Frame(self._frameOptionsNested, setLayout=True, showBorder=False, grid=(1, 0))
        # self.fileFrame = Frame(self._infoFrame, setLayout=True, showBorder=False, grid=(2, 0))
        # self._filterLogFrame = MoreLessFrame(self._infoFrame, name='Filter Log', showMore=False, grid=(3, 0), gridSpan=(1, 1))
        # self._treeSplitter.addWidget(self._filterLogFrame)

        _row = 0
        self.logData = TextEditor(self._filterLogFrame.contentsFrame, grid=(_row, 0), gridSpan=(1, 3), addWordWrap=True)
        self.logData.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.logData.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

        # tables frame
        # add a splitter
        self._tableSplitter = Splitter(self, setLayout=True, horizontal=False)
        self._tableSplitter.setChildrenCollapsible(False)
        self.tablesFrame.getLayout().addWidget(self._tableSplitter, 0, 0)
        Spacer(self.tablesFrame, 3, 3,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(1, 0))
        # increase the stretch for the splitter to make it fill the widget, unless all others are fixed height :)
        self.tablesFrame.getLayout().setRowStretch(0, 2)

        # set the subframe to be ignored and minimum to stop the widgets overlapping - remember this for other places
        self._frameOptionsNested.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Minimum)
        self.frameOptionsFrame.getLayout().setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)

        # options frame
        pass

        # file frame
        pass

    def _populate(self):
        """Fill the treeView from the nef dictionary
        """
        if self.project:
            with self.blockWidgetSignals():
                if self._nefLoader:
                    # populate from the _nefLoader
                    self.nefTreeView.fillTreeView(self._nefLoader._nefDict)
                    self.nefTreeView.expandAll()
                elif self._nefDict:
                    # populate from dict
                    self.nefTreeView.fillTreeView(self._nefLoader._nefDict)
                    self.nefTreeView.expandAll()

                if self._pathName:
                    self.headerLabel.setText(self._pathName)
                elif self.project:
                    self.headerLabel.setText(self.project.name)
                else:
                    self.headerLabel.setText('')
                self._colourTreeView()

    def _colourTreeView(self):
        projectSections = self.nefTreeView.nefToTreeViewMapping
        saveFrameLists = self.nefTreeView.nefProjectToSaveFramesMapping

        projectColour = self.nefTreeView._foregroundColour
        _projectError = False
        treeRoot = self.nefTreeView.invisibleRootItem()
        if not treeRoot.childCount():
            return
        projectItem = treeRoot.child(0)

        # iterate through all the groups in the tree, e.g., chains/samples/peakLists
        for section, (plural, singular) in projectSections.items():
            # find item in treeItem
            pluralItem = self.nefTreeView.findSection(plural)
            if pluralItem:
                pluralItem = pluralItem[0] if isinstance(pluralItem, list) else pluralItem

                sectionColour = self.nefTreeView._foregroundColour

                # iterate through the items in the group, e.g., peakList/integralList/sample
                _sectionError = False
                child_count = pluralItem.childCount()
                for i in range(child_count):
                    childItem = pluralItem.child(i)
                    childColour = self.nefTreeView._foregroundColour

                    # get the saveFrame associated with this item
                    itemName = childItem.data(0, 0)
                    saveFrame = childItem.data(1, 0)
                    parentGroup = childItem.parent().data(0, 0) if childItem.parent() else repr(None)

                    # NOTE:ED - need a final check on this
                    _errorName = getattr(saveFrame, '_rowErrors', None) and saveFrame._rowErrors.get(saveFrame['sf_category'])
                    if _errorName and itemName in _errorName:  # itemName
                        _sectionError = True

                    loops = self._nefReader._getLoops(self.project, saveFrame)
                    _rowError = False
                    for loop in loops:

                        # get the group name add fetch the correct mapping
                        mapping = self.nefTreeView.nefProjectToSaveFramesMapping.get(parentGroup)
                        if mapping and loop.name not in mapping:
                            continue

                        # NOTE:ED - if there are no loops then _sectionError is never set
                        if hasattr(saveFrame, '_rowErrors') and \
                                loop.name in saveFrame._rowErrors and \
                                saveFrame._rowErrors[loop.name]:
                            # _rowError = True
                            _sectionError = True
                            # _projectError = True

                    primaryHandler = self.nefTreeView.nefProjectToHandlerMapping.get(parentGroup) or saveFrame.get('sf_category')
                    if primaryHandler:
                        if primaryHandler in self._setBadSaveFrames:
                            handler = self._setBadSaveFrames[primaryHandler]
                            if handler is not None:
                                _rowError = handler(self, name=itemName, saveFrame=saveFrame, parentGroup=parentGroup)

                    if _rowError:
                        childColour = INVALIDTEXTROWCHECKCOLOUR if childItem.checkState(0) else INVALIDTEXTROWNOCHECKCOLOUR
                    self.nefTreeView.setForegroundForRow(childItem, childColour)

                if _sectionError:
                    sectionColour = INVALIDTEXTROWCHECKCOLOUR if pluralItem.checkState(0) else INVALIDTEXTROWNOCHECKCOLOUR
                    if pluralItem.checkState(0):
                        _projectError = True
                self.nefTreeView.setForegroundForRow(pluralItem, sectionColour)

        if _projectError:
            projectColour = INVALIDTEXTROWCHECKCOLOUR if projectItem.checkState(0) else INVALIDTEXTROWNOCHECKCOLOUR
        self.nefTreeView.setForegroundForRow(projectItem, projectColour)

    def table_nef_molecular_system(self, saveFrame, item):
        itemName = item.data(0, 0)
        primaryCode = 'nef_sequence_chain_code'
        _content = getattr(saveFrame, '_content', None)
        _errors = getattr(saveFrame, '_rowErrors', {})

        numPrimary = _content.get(primaryCode)
        if numPrimary and len(numPrimary) <= 1:
            return

        if _errors:
            _fillColour = INVALIDTABLEFILLCHECKCOLOUR if item.checkState(0) else INVALIDTABLEFILLNOCHECKCOLOUR

            # colour rows by extra colour
            chainErrors = _errors.get('nef_sequence_' + itemName)
            if chainErrors:
                table = self._nefTables.get('nef_sequence')

                with self._tableColouring(table) as setRowBackgroundColour:
                    for rowIndex in chainErrors:
                        setRowBackgroundColour(rowIndex, _fillColour)

    def table_ccpn_assignment(self, saveFrame, item, listName=None):
        tables = ['nmr_chain', 'nmr_residue', 'nmr_atom']
        primaryCode = 'nmr_chain'
        itemName = item.data(0, 0)
        _content = getattr(saveFrame, '_content', None)
        _errors = getattr(saveFrame, '_rowErrors', {})

        numPrimary = _content.get(primaryCode)
        if numPrimary and len(numPrimary) <= 1:
            return

        if _errors:
            _fillColour = INVALIDTABLEFILLCHECKCOLOUR if item.checkState(0) else INVALIDTABLEFILLNOCHECKCOLOUR

            for tableName in tables:
                # colour rows by extra colour
                chainErrors = _errors.get('_'.join([tableName, itemName]))
                if chainErrors:
                    table = self._nefTables.get(tableName)

                    with self._tableColouring(table) as setRowBackgroundColour:
                        for rowIndex in chainErrors:
                            setRowBackgroundColour(rowIndex, _fillColour)

    def table_lists(self, saveFrame, item, listName, postFix='list'):
        itemName = item.data(0, 0)
        primaryCode = '_'.join([listName, postFix])
        _content = getattr(saveFrame, '_content', None)
        _errors = getattr(saveFrame, '_rowErrors', {})

        numPrimary = _content.get(primaryCode)
        if numPrimary and len(numPrimary) <= 1:
            return

        if _errors:
            _fillColour = INVALIDTABLEFILLCHECKCOLOUR if item.checkState(0) else INVALIDTABLEFILLNOCHECKCOLOUR

            # colour rows by extra colour
            chainErrors = _errors.get('_'.join([listName, itemName]))
            if chainErrors:
                table = self._nefTables.get(listName)

                with self._tableColouring(table) as setRowBackgroundColour:
                    for rowIndex in chainErrors:
                        setRowBackgroundColour(rowIndex, _fillColour)
            chainErrors = _errors.get('_'.join([listName, postFix, itemName]))
            if chainErrors:
                table = self._nefTables.get('_'.join([listName, postFix]))

                with self._tableColouring(table) as setRowBackgroundColour:
                    for rowIndex in chainErrors:
                        setRowBackgroundColour(rowIndex, _fillColour)

    def table_peak_lists(self, saveFrame, item, listName=None):
        listItemName = 'nef_peak'
        listName = 'ccpn_peak'
        primaryCode = 'nef_peak'
        itemName = item.data(0, 0)
        _content = getattr(saveFrame, '_content', None)
        _errors = getattr(saveFrame, '_rowErrors', {})

        numPrimary = _content.get(primaryCode)
        if numPrimary and len(numPrimary) <= 1:
            return

        if _errors:
            _fillColour = INVALIDTABLEFILLCHECKCOLOUR if item.checkState(0) else INVALIDTABLEFILLNOCHECKCOLOUR

            # colour rows by extra colour
            chainErrors = _errors.get('_'.join([listItemName, itemName]))
            if chainErrors:
                table = self._nefTables.get(listItemName)

                with self._tableColouring(table) as setRowBackgroundColour:
                    for rowIndex in chainErrors:
                        setRowBackgroundColour(rowIndex, _fillColour)
            chainErrors = _errors.get('_'.join([listName, 'list', itemName]))
            if chainErrors:
                table = self._nefTables.get('_'.join([listName, 'list']))

                with self._tableColouring(table) as setRowBackgroundColour:
                    for rowIndex in chainErrors:
                        setRowBackgroundColour(rowIndex, _fillColour)

    def table_peak_clusters(self, saveFrame, item, listName=None):
        listItemName = 'ccpn_peak_cluster'
        listName = 'ccpn_peak_cluster'
        primaryCode = 'ccpn_peak_cluster'
        itemName = item.data(0, 0)
        _content = getattr(saveFrame, '_content', None)
        _errors = getattr(saveFrame, '_rowErrors', {})

        numPrimary = _content.get(primaryCode)
        if numPrimary and len(numPrimary) <= 1:
            return

        if _errors:
            _fillColour = INVALIDTABLEFILLCHECKCOLOUR if item.checkState(0) else INVALIDTABLEFILLNOCHECKCOLOUR

            # colour rows by extra colour
            chainErrors = _errors.get('_'.join([listItemName, itemName]))
            if chainErrors:
                table = self._nefTables.get(listItemName)

                with self._tableColouring(table) as setRowBackgroundColour:
                    for rowIndex in chainErrors:
                        setRowBackgroundColour(rowIndex, _fillColour)
            chainErrors = _errors.get('_'.join([listName, 'peaks', itemName]))
            if chainErrors:
                table = self._nefTables.get('_'.join([listName, 'peaks']))

                with self._tableColouring(table) as setRowBackgroundColour:
                    for rowIndex in chainErrors:
                        setRowBackgroundColour(rowIndex, _fillColour)

    def table_ccpn_notes(self, saveFrame, item):
        itemName = item.data(0, 0)
        primaryCode = 'ccpn_notes'
        _content = getattr(saveFrame, '_content', None)
        _errors = getattr(saveFrame, '_rowErrors', {})

        numPrimary = _content.get(primaryCode)
        if numPrimary and len(numPrimary) <= 1:
            return

        if _errors:
            _fillColour = INVALIDTABLEFILLCHECKCOLOUR if item.checkState(0) else INVALIDTABLEFILLNOCHECKCOLOUR

            # colour rows by extra colour
            chainErrors = _errors.get('ccpn_note_' + itemName)
            if chainErrors:
                table = self._nefTables.get('ccpn_note')

                with self._tableColouring(table) as setRowBackgroundColour:
                    for rowIndex in chainErrors:
                        setRowBackgroundColour(rowIndex, _fillColour)

    def table_ccpn_collections(self, saveFrame, item):
        itemName = item.data(0, 0)
        primaryCode = 'ccpn_collections'
        _content = getattr(saveFrame, '_content', None)
        _errors = getattr(saveFrame, '_rowErrors', {})

        numPrimary = _content.get(primaryCode)
        if numPrimary and len(numPrimary) <= 1:
            return

        if _errors:
            _fillColour = INVALIDTABLEFILLCHECKCOLOUR if item.checkState(0) else INVALIDTABLEFILLNOCHECKCOLOUR

            # colour rows by extra colour
            chainErrors = _errors.get('ccpn_collection_' + itemName)
            if chainErrors:
                table = self._nefTables.get('ccpn_collection')

                with self._tableColouring(table) as setRowBackgroundColour:
                    for rowIndex in chainErrors:
                        setRowBackgroundColour(rowIndex, _fillColour)

    def table_ccpn_additional_data(self, saveFrame, item):
        itemName = item.data(0, 0)
        primaryCode = 'ccpn_additional_data'
        _content = getattr(saveFrame, '_content', None)
        _errors = getattr(saveFrame, '_rowErrors', {})

        numPrimary = _content.get(primaryCode)
        if numPrimary and len(numPrimary) <= 1:
            return

        if _errors:
            _fillColour = INVALIDTABLEFILLCHECKCOLOUR if item.checkState(0) else INVALIDTABLEFILLNOCHECKCOLOUR

            # colour rows by extra colour
            chainErrors = _errors.get('ccpn_internal_data_' + itemName)
            if chainErrors:
                table = self._nefTables.get('ccpn_internal_data')

                with self._tableColouring(table) as setRowBackgroundColour:
                    for rowIndex in chainErrors:
                        setRowBackgroundColour(rowIndex, _fillColour)

    def _set_bad_saveframe(self, name=None, saveFrame=None, parentGroup=None, prefix=None, mappingCode=None,
                           errorCode=None, tableColourFunc=None):
        # check if the current saveFrame exists; i.e., category exists as row = [0]
        item = self.nefTreeView.findSection(name, parentGroup)
        if not item:
            getLogger().debug2('>>> not found {} {} {}'.format(name, saveFrame, parentGroup))
            return
        if isinstance(item, list):
            # find the correct one from the saveframe
            for itm in item:
                if itm.data(1, 0) == saveFrame:
                    item = itm
                    break
            else:
                getLogger().debug2('>>> not found {} {} {}'.format(name, saveFrame, parentGroup))
                return

        itemName = item.data(0, 0)

        mappingCode = mappingCode or ''
        errorCode = errorCode or ''
        mapping = self.nefTreeView.nefToTreeViewMapping.get(mappingCode)

        _content = getattr(saveFrame, '_content', None)
        _errors = getattr(saveFrame, '_rowErrors', {})
        _bad = False
        if _content and mapping:
            if errorCode in _errors and itemName in _errors[errorCode]:
                _bad = True

        return _bad

    def apply_checkBox_item(self, name=None, saveFrame=None, parentGroup=None, prefix=None, mappingCode=None,
                            checkID='_importRows'):
        # check if the current saveFrame exists; i.e., category exists as row = [0]
        item = self.nefTreeView.findSection(name, parentGroup)
        if not item:
            getLogger().debug2('>>> not found {} {} {}'.format(name, saveFrame, parentGroup))
            return
        if isinstance(item, list):
            # find the correct one from the saveframe
            for itm in item:
                if itm.data(1, 0) == saveFrame:
                    item = itm
                    break
            else:
                getLogger().debug2('>>> not found {} {} {}'.format(name, saveFrame, parentGroup))
                return

        itemName = item.data(0, 0)

        _importList = self._nefReader._importDict.get(saveFrame.name)
        if not _importList:
            _importList = self._nefReader._importDict[saveFrame.name] = {}

        if not _importList.get(checkID):
            _importList[checkID] = (itemName,)
        else:
            _importList[checkID] += (itemName,)

    def _checkParentGroup(self, name, parentGroup, saveFrame):
        """Search for the parentGroup in the treeView
        :return: treeItem
        """
        # check if the current saveFrame exists; i.e., category exists as row = [0]
        item = self.nefTreeView.findSection(name, parentGroup)
        if not item:
            getLogger().debug2('>>> not found {} {} {}'.format(name, saveFrame, parentGroup))
            return
        if isinstance(item, list):
            # find the correct one from the saveframe
            for itm in item:
                if itm.data(1, 0) == saveFrame:
                    item = itm
                    break
            else:
                getLogger().debug2('>>> not found {} {} {}'.format(name, saveFrame, parentGroup))
                return

        return item

    def _handleTreeView(self, name=None, saveFrame=None, parentGroup=None, prefix=None, mappingCode=None,
                        errorCode=None, tableColourFunc=None, _handleAutoRename=False):
        # this is treated as a generator

        # check if the current saveFrame exists; i.e., category exists as row = [0]
        if not (item := self._checkParentGroup(name, parentGroup, saveFrame)):
            return


        # simple class to export variables from the contextmanager
        @dataclass
        class HandleValues:
            item = None
            itemName = None
            saveFrame = None
            mappingCode = None
            errorCode = None
            mapping = None
            _content = None
            _errors = None
            _fillColour = None
            plural = None
            singular = None
            row = None
            ccpnClassName = None


        if _handleAutoRename:
            self._handleItemRename(item, mappingCode, saveFrame)
            return

        _handleValues = HandleValues()
        _handleValues.item = item
        _handleValues.itemName = item.data(0, 0)
        _handleValues.saveFrame = item.data(1, 0)

        _handleValues.mappingCode = mappingCode or ''
        _handleValues.errorCode = errorCode or ''
        _handleValues.mapping = self.nefTreeView.nefToTreeViewMapping.get(mappingCode)
        _handleValues.ccpnClassName = nef2CcpnClassNames.get(mappingCode)

        _handleValues._content = getattr(saveFrame, '_content', None)
        _handleValues._errors = getattr(saveFrame, '_rowErrors', {})
        _handleValues.row = 0

        if _handleValues._content and _handleValues.mapping:
            _handleValues._fillColour = INVALIDBUTTONCHECKCOLOUR if item.checkState(0) else INVALIDBUTTONNOCHECKCOLOUR
            _handleValues.plural, _handleValues.singular = _handleValues.mapping

            # return the values as a generator - only returns once, skipped if no item
            yield _handleValues

            # add comment widgets
            _handleValues.row = self._addCommentWidgets(item, _handleValues.plural, _handleValues.row, saveFrame)

            self._colourTables(item, saveFrame, tableColourFunc)

        self.frameOptionsFrame.setVisible(self._enableRename)
        self._finaliseSelection(_handleValues._content, _handleValues._errors)

    def _handleTreeViewParent(self, parentItem=None, parentItemName=None, mappingCode=None, _handleAutoRename=False):
        # this is treated as a generator

        # simple class to export variables from the contextmanager
        @dataclass
        class HandleValues:
            item = None
            itemName = None
            mappingCode = None
            mapping = None
            row = None
            ccpnClassName = None


        if _handleAutoRename:
            return

        _handleValues = HandleValues()
        _handleValues.parentItem = parentItem
        _handleValues.parentItemName = parentItemName
        _handleValues.mappingCode = mappingCode or ''
        _handleValues.mapping = self.nefTreeView.nefToTreeViewMapping.get(mappingCode)
        _handleValues.ccpnClassName = nef2CcpnClassNames.get(mappingCode)
        _handleValues.row = 0

        # return the values as a generator - only returns once, skipped if no item
        yield _handleValues

        self.frameOptionsFrame.setVisible(self._enableRename)

    def handleTreeViewParentGeneral(self, parentItem=None, parentItemName=None, mappingCode=None, _handleAutoRename=False):

        for _handleValues in self._handleTreeViewParent(parentItem, parentItemName, mappingCode, _handleAutoRename):

            self._makeCollectionParentPulldown(_handleValues)
            _handleValues.row += 1

    def handleTreeViewParentGeneralStructureData(self, parentItem=None, parentItemName=None, mappingCode=None, _handleAutoRename=False):

        for _handleValues in self._handleTreeViewParent(parentItem, parentItemName, mappingCode, _handleAutoRename):

            self._makeCollectionParentStructureDataPulldown(_handleValues)
            _handleValues.row += 1

    def handleTreeViewSelectionGeneral(self, name=None, saveFrame=None, parentGroup=None, prefix=None, mappingCode=None,
                                       errorCode=None, tableColourFunc=None, _handleAutoRename=False):

        for _handleValues in self._handleTreeView(name, saveFrame, parentGroup, prefix, mappingCode, errorCode, tableColourFunc, _handleAutoRename):
            _handleValues.row, saveFrameData = self._addRenameWidgets(_handleValues.item, _handleValues.itemName, _handleValues.plural, _handleValues.row, saveFrame, _handleValues.singular)
            self._colourRenameWidgets(_handleValues._errors, _handleValues._fillColour, errorCode, _handleValues.itemName, saveFrameData)

            self._makeCollectionPulldown(_handleValues)
            _handleValues.row += 1

    def handleTreeViewSelectionGeneralNoCollection(self, name=None, saveFrame=None, parentGroup=None, prefix=None, mappingCode=None,
                                                   errorCode=None, tableColourFunc=None, _handleAutoRename=False):

        for _handleValues in self._handleTreeView(name, saveFrame, parentGroup, prefix, mappingCode, errorCode, tableColourFunc, _handleAutoRename):
            _handleValues.row, saveFrameData = self._addRenameWidgets(_handleValues.item, _handleValues.itemName, _handleValues.plural, _handleValues.row, saveFrame, _handleValues.singular)
            self._colourRenameWidgets(_handleValues._errors, _handleValues._fillColour, errorCode, _handleValues.itemName, saveFrameData)

    def handleTreeViewSelectionCcpnList(self, name=None, saveFrame=None, parentGroup=None, prefix=None, mappingCode=None,
                                        errorCode=None, tableColourFunc=None, _handleAutoRename=False):

        for _handleValues in self._handleTreeView(name, saveFrame, parentGroup, prefix, mappingCode, errorCode, tableColourFunc, _handleAutoRename):
            _handleValues.row, saveFrameData = self._addRenameWidgets(_handleValues.item, _handleValues.itemName, _handleValues.plural, _handleValues.row, saveFrame, _handleValues.singular)
            self._colourRenameWidgets(_handleValues._errors, _handleValues._fillColour, errorCode, _handleValues.itemName, saveFrameData)

            self._makeCollectionPulldown(_handleValues)
            _handleValues.row += 1

    def handleTreeViewSelectionAssignment(self, name=None, saveFrame=None, parentGroup=None, prefix=None, mappingCode=None,
                                          errorCode=None, tableColourFunc=None, _handleAutoRename=False):

        for _handleValues in self._handleTreeView(name, saveFrame, parentGroup, prefix, mappingCode, errorCode, tableColourFunc, _handleAutoRename):
            _handleValues.row, saveFrameData = self._addRenameWidgets(_handleValues.item, _handleValues.itemName, _handleValues.plural, _handleValues.row, saveFrame, _handleValues.singular)
            self._colourRenameWidgets(_handleValues._errors, _handleValues._fillColour, errorCode, _handleValues.itemName, saveFrameData)

            # add widgets to handle assignments
            _handleValues.row = self._addAssignmentWidgets(_handleValues.item, _handleValues.plural, _handleValues.row, saveFrame, saveFrameData)

            self._makeCollectionPulldown(_handleValues)
            _handleValues.row += 1

    def handleTreeViewSelectionStructureDataParent(self, name=None, saveFrame=None, parentGroup=None, prefix=None, mappingCode=None,
                                                   errorCode=None, tableColourFunc=None, _handleAutoRename=False):

        for _handleValues in self._handleTreeView(name, saveFrame, parentGroup, prefix, mappingCode, errorCode, tableColourFunc, _handleAutoRename):
            _handleValues.row, saveFrameData = self._addRenameWidgets(_handleValues.item, _handleValues.itemName, _handleValues.plural, _handleValues.row, saveFrame, _handleValues.singular)
            self._colourRenameWidgets(_handleValues._errors, _handleValues._fillColour, errorCode, _handleValues.itemName, saveFrameData)

            # add widgets to handle linking to structureData parent
            _handleValues.row = self._addStructureDataWidgets(_handleValues.item, _handleValues.plural, _handleValues.row, saveFrame)

            self._makeCollectionStructurePulldown(_handleValues)
            _handleValues.row += 1

    def handleTreeViewSelectionStructureDataParentNoCollection(self, name=None, saveFrame=None, parentGroup=None, prefix=None, mappingCode=None,
                                                               errorCode=None, tableColourFunc=None, _handleAutoRename=False):

        for _handleValues in self._handleTreeView(name, saveFrame, parentGroup, prefix, mappingCode, errorCode, tableColourFunc, _handleAutoRename):
            _handleValues.row, saveFrameData = self._addRenameWidgets(_handleValues.item, _handleValues.itemName, _handleValues.plural, _handleValues.row, saveFrame, _handleValues.singular)
            self._colourRenameWidgets(_handleValues._errors, _handleValues._fillColour, errorCode, _handleValues.itemName, saveFrameData)

            # add widgets to handle linking to structureData parent
            _handleValues.row = self._addStructureDataWidgets(_handleValues.item, _handleValues.plural, _handleValues.row, saveFrame)

    def _addAssignmentWidgets(self, item, plural, row, saveFrame, saveFrameData):

        texts = ('Auto Rename SequenceCodes',)
        callbacks = (partial(self._renameSequenceCode, item=item, parentName=plural, lineEdit=saveFrameData, saveFrame=saveFrame, autoRename=True),)
        tipTexts = ('Automatically rename to the next available',)
        ButtonList(self.frameOptionsFrame, texts=texts, tipTexts=tipTexts, callbacks=callbacks,
                   grid=(row, 1), gridSpan=(1, 2), direction='v',
                   setLastButtonFocus=False)
        row += 1

        return row

    def _addStructureDataWidgets(self, item, plural, row, saveFrame):

        self._makeStructureDataPulldown(item, plural, row, saveFrame, 'ccpn_dataset_id')
        row += 1

        if saveFrame.get('sf_category') in ['ccpn_parameter', ]:
            self._makeSetButton(item, plural, row, saveFrame, 'ccpn_parameter_name', self._editParameterName)
            row += 1

        return row

    def _finaliseSelection(self, _content, _errors):
        self.logData.clear()
        pretty = PrintFormatter()
        self.logData.append(('CONTENTS DICT'))
        self.logData.append(pretty(_content))
        self.logData.append(('ERROR DICT'))
        self.logData.append(pretty(_errors))

    def _colourTables(self, item, saveFrame, tableColourFunc):
        if tableColourFunc is not None:
            tableColourFunc(self, saveFrame, item)

    def _colourRenameWidgets(self, _errors, _fillColour, errorCode, itemName, saveFrameData):
        if saveFrameData and errorCode in _errors and itemName in _errors[errorCode]:
            try:
                palette = saveFrameData.palette()
                palette.setColor(QtGui.QPalette.Base, _fillColour)
                saveFrameData.setPalette(palette)
            except Exception as es:
                getLogger().debug(f'error setting colours {es}')

    def _addCommentWidgets(self, item, plural, row, saveFrame):
        Label(self.frameOptionsFrame, text='Comment', grid=(row, 0), enabled=False)
        self._commentData = TextEditor(self.frameOptionsFrame, grid=(row, 1), gridSpan=(1, 2), enabled=True, addWordWrap=True)
        _comment = saveFrame.get('ccpn_comment')
        if _comment:
            self._commentData.set(_comment)
        self._commentData.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self._commentData.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        _height = getFontHeight()
        self._commentData.setMinimumHeight(_height * 3)
        row += 1
        texts = ('Set Comment',)
        callbacks = (partial(self._editComment, item=item, parentName=plural, lineEdit=self._commentData, saveFrame=saveFrame),)
        tipTexts = ('Set the comment for the saveFrame',)
        ButtonList(self.frameOptionsFrame, texts=texts, tipTexts=tipTexts, callbacks=callbacks,
                   grid=(row, 2), gridSpan=(1, 1), direction='v',
                   setLastButtonFocus=False)
        row += 1
        return row

    def _addRenameWidgets(self, item, itemName, plural, row, saveFrame, singular):
        saveFrameData = None
        if self._renameValid(item=item, saveFrame=saveFrame):

            Label(self.frameOptionsFrame, text=singular, grid=(row, 0))
            saveFrameData = LineEdit(self.frameOptionsFrame, text=str(itemName), grid=(row, 1))

            texts = ('Rename', 'Auto Rename')
            callbacks = (partial(self._rename, item=item, parentName=plural, lineEdit=saveFrameData, saveFrame=saveFrame),
                         partial(self._rename, item=item, parentName=plural, lineEdit=saveFrameData, saveFrame=saveFrame, autoRename=True))
            tipTexts = ('Rename', 'Automatically rename to the next available\n - dependent on saveframe type')
            ButtonList(self.frameOptionsFrame, texts=texts, tipTexts=tipTexts, callbacks=callbacks,
                       grid=(row, 2), gridSpan=(1, 1), direction='v',
                       setLastButtonFocus=False)
            saveFrameData.returnPressed.connect(callbacks[0])
            row += 1

        return row, saveFrameData

    def _handleItemRename(self, item, mappingCode, saveFrame):
        mappingCode = mappingCode or ''
        mapping = self.nefTreeView.nefToTreeViewMapping.get(mappingCode)
        if mapping:
            plural, singular = mapping
            _auto = partial(self._rename, item=item, parentName=plural, lineEdit=None, saveFrame=saveFrame, autoRename=True)
            _auto()

    def _makeSetButton(self, item, plural, row, saveFrame, attribName, func):
        Label(self.frameOptionsFrame, text=attribName, grid=(row, 0))

        # extract the ccpn_parameter_name
        _attrib = saveFrame.get(attribName)
        dataSetData = LineEdit(self.frameOptionsFrame, text=str(_attrib), grid=(row, 1))
        texts = ('Set',)
        callbacks = (partial(func, item=item, parentName=plural, lineEdit=dataSetData, saveFrame=saveFrame),)
        tipTexts = (f'Set the {attribName} for the saveFrame',)
        ButtonList(self.frameOptionsFrame, texts=texts, tipTexts=tipTexts, callbacks=callbacks,
                   grid=(row, 2), gridSpan=(1, 1), direction='v',
                   setLastButtonFocus=False)
        dataSetData.returnPressed.connect(callbacks[0])

    def _makeStructureDataPulldown(self, item, plural, row, saveFrame, attribName):

        Label(self.frameOptionsFrame, text='structureData', grid=(row, 0))
        # extract the ccpn_parameter_name
        _att = str(saveFrame.get(attribName) or '')  # may be None

        sData = self.project.structureData
        sdIds = OrderedSet([''] + [sd.id for sd in sData])
        sdIds.add(_att)

        # search through the saveframes for occurrences of ccpn_dataset_id
        _sfNames = self._nefLoader.getSaveFrameNames()
        for sf in _sfNames:
            sFrame = self._nefLoader.getSaveFrame(sf)
            if sFrame is not None and sFrame._nefFrame and 'ccpn_dataset_id' in sFrame._nefFrame:
                _id = sFrame._nefFrame.get("ccpn_dataset_id") or ''
                sdIds.add(_id)

        funcSelect = self._selectStructureDataId

        # also need list of all dataset_id in nef
        dataSetData = PulldownList(self.frameOptionsFrame,
                                   index=list(sdIds).index(_att) if _att in sdIds else 0,
                                   texts=list(sdIds),
                                   grid=(row, 1), editable=True)
        _itmName = item.data(0, 0)
        _itmParentName = item.parent().data(0, 0) if item.parent() else repr(None)
        callbackSelect = partial(funcSelect, itemName=_itmName, itemParentName=_itmParentName, parentName=plural, pulldownList=dataSetData, saveFrame=saveFrame)
        dataSetData.activated.connect(callbackSelect)

    def _makeCollectionPulldown(self, values):

        attribName, funcSelect = 'collection', self._selectCollectionId

        Label(self.frameOptionsFrame, text=attribName, grid=(values.row, 0))
        # extract the ccpn_parameter_name
        _att = str(values.saveFrame.get(attribName) or '')  # may be None
        _itmName = values.item.data(0, 0)
        _itmParentName = values.item.parent().data(0, 0) if values.item.parent() else repr(None)

        colData = self.project.collections
        colNames = OrderedSet([''] + [co.name for co in colData])

        # read the collections not defined in the project
        for col in self._collections.keys():
            colNames.add(col)
            self._collections.setdefault(col, [])

        # map the className to a pid for the collection
        _itmPid = Pid.new(values.ccpnClassName, _itmName) if values.ccpnClassName else _itmName
        _indexing = set()
        for k, v in self._collections.items():
            if _itmPid in v:
                _indexing.add(list(colNames).index(k))

        collectionPulldown = PulldownList(self.frameOptionsFrame,
                                          index=list(_indexing)[0] if len(_indexing) == 1 else 0,
                                          texts=list(colNames),
                                          grid=(values.row, 1), editable=True)
        callbackSelect = partial(funcSelect, itemName=_itmName, itemPid=_itmPid, pulldownList=collectionPulldown, saveFrame=values.saveFrame)
        collectionPulldown.activated.connect(callbackSelect)

    def _makeCollectionParentPulldown(self, values):

        frame = MoreLessFrame(self, name=values.parentItemName, showMore=True, grid=(0, 0))
        self._tableSplitter.addWidget(frame)
        self._nefWidgets = [frame, ]

        _count = values.parentItem.childCount()
        _children = []
        for i in range(_count):
            itm = values.parentItem.child(i)
            itemName = itm.data(0, 0)
            saveFrame = itm.data(1, 0)
            _children.append((itm, itemName, saveFrame))

        itemListWidget = ListWidget(frame.contentsFrame, grid=(1, 0), gridSpan=(5, 1))
        itemListWidget.addItems([itemName for (_, itemName, _) in _children])

        attribName, funcSelect = 'collection', self._selectCollectionParentId

        Label(self.frameOptionsFrame, text=attribName, grid=(values.row, 0))
        collectionPulldown = PulldownList(self.frameOptionsFrame,
                                          grid=(values.row, 1), editable=True)
        callbackSelect = partial(funcSelect, values=values, pulldownList=collectionPulldown, parent=itemListWidget)
        collectionPulldown.activated.connect(callbackSelect)

        itemListWidget.itemSelectionChanged.connect(partial(self._itemListWidgetCallback, values=values, parent=itemListWidget, collectionPulldown=collectionPulldown))

    @staticmethod
    def _getSelectedChildren(parent, values):
        # get the selection from the widget
        _selection = parent.getSelectedTexts()
        _count = values.parentItem.childCount()
        _children = []
        for i in range(_count):
            itm = values.parentItem.child(i)
            itemName = itm.data(0, 0)
            if itemName in _selection:
                saveFrame = itm.data(1, 0)
                _children.append((itm, itemName, saveFrame))
        return _children, _selection

    def _itemListWidgetCallback(self, values=None, parent=None, collectionPulldown=None):
        """Handle user selection of items in the parent group listWidget
        This is children in each bottom branch of the tree
        Populates collection widget
        """
        _children, _selection = self._getSelectedChildren(parent, values)

        self._populateCollectionPulldown(_children, _selection, collectionPulldown, values)

    def _itemListWidgetStructureCallback(self, values=None, parent=None, collectionPulldown=None, structurePulldown=None):
        """Handle user selection of items in the parent group listWidget
        This is children in each bottom branch of the tree
        Populates collection and structureData widgets
        """
        _children, _selection = self._getSelectedChildren(parent, values)

        self._populateCollectionStructurePulldown(_children, _selection, collectionPulldown, values)
        self._populateStructureDataPulldown(_children, _selection, structurePulldown, values)

    def _populateCollectionPulldown(self, _children, _selection, collectionPulldown, values):

        colData = self.project.collections
        colNames = OrderedSet([''] + [co.name for co in colData])

        # read the collections not defined in the project
        for col in self._collections.keys():
            colNames.add(col)
            self._collections.setdefault(col, [])

        # get the list of common collections for the selection, to set the pulldown
        _indexing = set()
        for (itm, itmName, saveFrame) in _children:
            _itmPid = Pid.new(values.ccpnClassName, itmName) if values.ccpnClassName else itmName
            _count = 0
            for k, v in self._collections.items():
                if _itmPid in v:
                    _indexing.add(list(colNames).index(k))
                    _count += 1
            if not _count:
                _indexing.add(list(colNames).index(''))

        collectionPulldown.setData(list(colNames))
        if len(_indexing) == 1:
            collectionPulldown.setIndex(list(_indexing)[0])
        else:
            collectionPulldown.setIndex(0)

    def _populateCollectionStructurePulldown(self, _children, _selection, collectionPulldown, values):

        colData = self.project.collections
        colNames = OrderedSet([''] + [co.name for co in colData])

        # read the collections not defined in the project
        for col in self._collections.keys():
            colNames.add(col)
            self._collections.setdefault(col, [])

        # get the list of common collections for the selection, to set the pulldown
        _indexing = set()
        for (itm, itmName, saveFrame) in _children:
            _itmStructureData = saveFrame.get('ccpn_dataset_id') or ''
            _itmPid = Pid.new(values.ccpnClassName, _itmStructureData, itmName) if values.ccpnClassName else itmName
            _count = 0
            for k, v in self._collections.items():
                if _itmPid in v:
                    _indexing.add(list(colNames).index(k))
                    _count += 1
            if not _count:
                _indexing.add(list(colNames).index(''))

        collectionPulldown.setData(list(colNames))
        if len(_indexing) == 1:
            collectionPulldown.setIndex(list(_indexing)[0])
        else:
            collectionPulldown.setIndex(0)

    def _populateStructureDataPulldown(self, _children, _selection, structurePulldown, values):

        # get the structureData names from the project
        sData = self.project.structureData
        sdIds = OrderedSet([''] + [sd.id for sd in sData])
        # search through the saveframes for occurrences of ccpn_dataset_id - add to choices
        _sfNames = self._nefLoader.getSaveFrameNames()
        for sf in _sfNames:
            sFrame = self._nefLoader.getSaveFrame(sf)
            if sFrame is not None and sFrame._nefFrame and 'ccpn_dataset_id' in sFrame._nefFrame:
                _id = sFrame._nefFrame.get("ccpn_dataset_id")
                sdIds.add(_id or '')

        # get the list of common structureData for the selection, to set the pulldown
        _indexing = set()
        for (itm, itmName, saveFrame) in _children:
            _itmPid = saveFrame.get("ccpn_dataset_id") or ''
            if _itmPid in sdIds:
                _indexing.add(list(sdIds).index(_itmPid))

        structurePulldown.setData(list(sdIds))
        if len(_indexing) == 1:
            structurePulldown.setIndex(list(_indexing)[0])
        else:
            structurePulldown.setIndex(0)

    def _makeCollectionParentStructureDataPulldown(self, values):

        frame = MoreLessFrame(self, name=values.parentItemName, showMore=True, grid=(0, 0))
        self._tableSplitter.addWidget(frame)
        self._nefWidgets = [frame, ]

        _count = values.parentItem.childCount()
        _children = []
        for i in range(_count):
            itm = values.parentItem.child(i)
            itemName = itm.data(0, 0)
            saveFrame = itm.data(1, 0)
            _children.append((itm, itemName, saveFrame))

        itemListWidget = ListWidget(frame.contentsFrame, grid=(1, 0), gridSpan=(5, 1))
        itemListWidget.addItems([itemName for (_, itemName, _) in _children])

        attribName, funcSelect = 'structureData', self._selectStructureDataParentId

        Label(self.frameOptionsFrame, text='structureData', grid=(values.row, 0))
        structurePulldown = PulldownList(self.frameOptionsFrame,
                                   grid=(values.row, 1), editable=True)
        values.row += 1
        callbackSelect = partial(funcSelect, values=values, pulldownList=structurePulldown, parent=itemListWidget)
        structurePulldown.activated.connect(callbackSelect)

        attribName, funcSelect = 'collection', self._selectCollectionParentStructureId

        Label(self.frameOptionsFrame, text=attribName, grid=(values.row, 0))
        collectionPulldown = PulldownList(self.frameOptionsFrame,
                                          grid=(values.row, 1), editable=True)
        callbackSelect = partial(funcSelect, values=values, pulldownList=collectionPulldown, parent=itemListWidget)
        collectionPulldown.activated.connect(callbackSelect)

        itemListWidget.itemSelectionChanged.connect(partial(self._itemListWidgetStructureCallback, values=values, parent=itemListWidget,
                                                   collectionPulldown=collectionPulldown, structurePulldown=structurePulldown))

    def _makeCollectionStructurePulldown(self, values):

        attribName, funcSelect = 'collection', self._selectCollectionId

        Label(self.frameOptionsFrame, text=attribName, grid=(values.row, 0))

        # extract the ccpn_parameter_name
        _att = str(values.saveFrame.get(attribName) or '')  # may be None
        _itmName = values.item.data(0, 0)
        _itmParentName = values.item.parent().data(0, 0) if values.item.parent() else repr(None)

        colData = self.project.collections
        colNames = OrderedSet([''] + [co.name for co in colData])

        # read the collections not defined in the project
        for col in self._collections.keys():
            colNames.add(col)

        # use the saveFrame loop to store?
        _itmStructureData = values.saveFrame.get('ccpn_dataset_id') or ''
        _itmPid = Pid.new(values.ccpnClassName, _itmStructureData, _itmName) if values.ccpnClassName else _itmName

        _indexing = set()
        # need a saveFrame name to ccpn pid mapping
        for k, v in self._collections.items():
            if _itmPid in v:
                _indexing.add(list(colNames).index(k))

        # also need list of all dataset_id in nef
        collectionPulldown = PulldownList(self.frameOptionsFrame,
                                          index=list(_indexing)[0] if len(_indexing) == 1 else 0,
                                          texts=list(colNames),
                                          grid=(values.row, 1), editable=True)
        callbackSelect = partial(funcSelect, itemName=_itmName, itemPid=_itmPid, pulldownList=collectionPulldown, saveFrame=values.saveFrame)
        collectionPulldown.activated.connect(callbackSelect)

    def _renameValid(self, item=None, saveFrame=None):
        if not item:
            return

        parentGroup = item.parent().data(0, 0) if item.parent() else repr(None)

        # find the primary handler class for the clicked item, .i.e. chains/peakLists etc.
        primaryHandler = self.nefTreeView.nefProjectToHandlerMapping.get(parentGroup) or saveFrame.get('sf_category')
        func = self._nefReader.renames.get(primaryHandler)

        return func

    def _rename(self, item=None, parentName=None, lineEdit=None, saveFrame=None, autoRename=False):
        """Handle clicking a rename button
        """
        if not item:
            return

        itemName = item.data(0, 0)
        parentGroup = item.parent().data(0, 0) if item.parent() else repr(None)
        cat = saveFrame.get('sf_category')

        # find the primary handler class for the clicked item, .i.e. chains/peakLists etc.
        primaryHandler = self.nefTreeView.nefProjectToHandlerMapping.get(parentGroup) or saveFrame.get('sf_category')
        func = self._nefReader.renames.get(primaryHandler)
        if func is not None:

            # NOTE:ED - remember tree checkbox selection
            _checks = [[_itm.data(0, 0), _itm.data(1, 0), _itm.parent().data(0, 0) if _itm.parent() else repr(None)]
                       for _itm in self.nefTreeView.traverseTree()
                       if _itm.checkState(0) == QtCore.Qt.Checked]

            # take from lineEdit if exists, otherwise assume autorename (for the minute)
            newName = lineEdit.get() if lineEdit else None
            try:
                # call the correct rename function based on the item clicked

                # TODO:ED make a new contentCompareDict that contains a merge of left and right windows
                #       don't need to merge, just make a list of dicts to compare against :)

                newName = func(self._nefReader, self.project,
                               self._nefDict, self._contentCompareDataBlocks,
                               saveFrame,
                               itemName=itemName, newName=newName if not autoRename else None)
            except Exception as es:
                showWarning('Rename SaveFrame', str(es))
            else:

                # everything okay - rebuild all for now, could make selective later
                self._repopulateview(_checks, itemName, newName, parentGroup, parentName)

    def _renameSequenceCode(self, item=None, parentName=None, lineEdit=None, saveFrame=None, autoRename=False):
        """Handle clicking a rename button
        """
        if not item:
            return

        itemName = item.data(0, 0)
        parentGroup = item.parent().data(0, 0) if item.parent() else repr(None)
        cat = saveFrame.get('sf_category')

        # find the primary handler class for the clicked item, .i.e. chains/peakLists etc.
        primaryHandler = self.nefTreeView.nefProjectToHandlerMapping.get(parentGroup) or saveFrame.get('sf_category')
        func = self._nefReader.renames.get('nmr_sequence_code')
        if func is not None:

            # NOTE:ED - remember tree checkbox selection
            _checks = [[_itm.data(0, 0), _itm.data(1, 0), _itm.parent().data(0, 0) if _itm.parent() else repr(None)]
                       for _itm in self.nefTreeView.traverseTree()
                       if _itm.checkState(0) == QtCore.Qt.Checked]

            # take from lineEdit if exists, otherwise assume autorename (for the minute)
            newName = lineEdit.get() if lineEdit else None
            try:
                # call the correct rename function based on the item clicked

                # TODO:ED make a new contentCompareDict that contains a merge of left and right windows
                #       don't need to merge, just make a list of dicts to compare against :)

                newName = func(self._nefReader, self.project,
                               self._nefDict, self._contentCompareDataBlocks,
                               saveFrame,
                               itemName=itemName, newName=newName if not autoRename else None)
            except Exception as es:
                showWarning('Rename SaveFrame', str(es))
            else:

                # everything okay - rebuild all for now, could make selective later
                self._repopulateview(_checks, itemName, newName, parentGroup, parentName)

    @contextmanager
    def _editSaveFrameItem(self, item=None, parentName=None, lineEdit=None, saveFrame=None, autoRename=False, parameter=None):
        """Handler for editing values in main saveFrame
        """
        if not item:
            return


        # simple class to export variables from the contextmanager
        @dataclass
        class _editValues:
            newVal: str = ''
            itemName: str = ''


        _data = _editValues()
        _data.itemName = item.data(0, 0)
        parentGroup = item.parent().data(0, 0) if item.parent() else repr(None)

        # find the primary handler class for the clicked item, .i.e. chains/peakLists etc.
        # primaryHandler = self.nefTreeView.nefProjectToHandlerMapping.get(parentGroup) or saveFrame.get('sf_category')

        _data.newVal = lineEdit.get() if lineEdit else None
        # remember tree checkbox selection
        _checks = [[_itm.data(0, 0), _itm.data(1, 0), _itm.parent().data(0, 0) if _itm.parent() else repr(None)]
                   for _itm in self.nefTreeView.traverseTree()
                   if _itm.checkState(0) == QtCore.Qt.Checked]

        # add item to saveframe
        try:
            yield _data

        except Exception as es:
            showWarning(f'Error editing {parameter}', str(es))
        else:
            # everything okay - rebuild all for now, could make selective later
            self._repopulateview(_checks, _data.itemName, None, parentGroup, parentName)

    @contextmanager
    def _editSaveFramePulldown(self, itemName=None, itemParentName=None, parentName=None, pulldownList=None, saveFrame=None, autoRename=False, parameter=None):
        """Handler for editing values in main saveFrame
        """
        if not itemName:
            return


        # simple class to export variables from the contextmanager
        @dataclass
        class _editValues:
            newVal: str = ''
            itemName: str = ''


        _data = _editValues()
        _data.itemName = itemName  # item.data(0, 0)
        parentGroup = itemParentName  # item.parent().data(0, 0) if item.parent() else repr(None)

        # find the primary handler class for the clicked item, .i.e. chains/peakLists etc.
        # primaryHandler = self.nefTreeView.nefProjectToHandlerMapping.get(parentGroup) or saveFrame.get('sf_category')

        _data.newVal = pulldownList.getText() if pulldownList else None
        # remember tree checkbox selection
        _checks = [[_itm.data(0, 0), _itm.data(1, 0), _itm.parent().data(0, 0) if _itm.parent() else repr(None)]
                   for _itm in self.nefTreeView.traverseTree()
                   if _itm.checkState(0) == QtCore.Qt.Checked]

        # add item to saveframe
        try:
            yield _data

        except Exception as es:
            showWarning(f'Error editing {parameter}', str(es))
        else:
            # everything okay - rebuild all for now, could make selective later
            self._repopulateview(_checks, _data.itemName, None, parentGroup, parentName)

    def _selectStructureDataId(self, itemName=None, itemParentName=None, parentName=None, pulldownList=None, saveFrame=None, autoRename=False):
        """Handle clicking rename structureData button
        """
        with self._editSaveFramePulldown(itemName, itemParentName, parentName, pulldownList, saveFrame, autoRename, 'ccpn_dataset_id') as _edit:
            # reads a non-empty string for a value
            if not _edit.newVal and 'ccpn_dataset_id' in saveFrame:
                if saveFrame.get('sf_category') in ['ccpn_parameter', ]:
                    raise ValueError('ccpn_dataset_id cannot be empty')
                else:
                    del saveFrame['ccpn_dataset_id']
            else:
                _oldName = saveFrame.get('ccpn_dataset_id')
                saveFrame['ccpn_dataset_id'] = str(_edit.newVal)
                # rename itemName if a ccpn_parameter
                if saveFrame.get('sf_category') in ['ccpn_parameter', ]:
                    if _edit.itemName and _oldName and _edit.itemName.startswith(_oldName):
                        _edit.itemName = _edit.newVal + _edit.itemName[len(_oldName):]

                for k, v in self._collections.items():
                    if v:
                        ll = []
                        for val in v:
                            ll.append(val.replace(':'+_oldName+'.', ':'+_edit.newVal+'.'))
                        self._collections[k] = ll

    def _selectStructureDataParentId(self, values=None, pulldownList=None, parent=None):
        """Handle clicking rename structureData button
        """
        if not (pulldownList and pulldownList.hasFocus()):
            return

        newName = pulldownList.getText() or None

        # get the selection from the listWidget
        _selection = parent.getSelectedTexts()
        _count = values.parentItem.childCount()
        _children = []
        for i in range(_count):
            itm = values.parentItem.child(i)
            itemName = itm.data(0, 0)
            if itemName in _selection:
                saveFrame = itm.data(1, 0)
                _children.append((itm, itemName, saveFrame))

        for (itm, itmName, saveFrame) in _children:
            _oldName = saveFrame.get('ccpn_dataset_id')
            if 'ccpn_dataset_id' in saveFrame:
                saveFrame['ccpn_dataset_id'] = newName

                # if saveFrame.get('sf_category') in ['ccpn_parameter', ]:
                #     if _edit.itemName and _oldName and _edit.itemName.startswith(_oldName):
                #         _edit.itemName = _edit.newVal + _edit.itemName[len(_oldName):]

                for k, v in self._collections.items():
                    if v:
                        ll = []
                        for val in v:
                            ll.append(val.replace(':'+_oldName+'.', ':'+newName+'.'))
                        self._collections[k] = ll

    def _selectCollectionId(self, itemName=None, itemPid=None, pulldownList=None, saveFrame=None):
        """Handle collection pulldown
        """
        if not (pulldownList and pulldownList.hasFocus()):
            return

        if (newCol := pulldownList.getText()):

            # remove from previous self._collections
            for k, v in list(self._collections.items()):
                if itemPid in v:
                    v.remove(itemPid)
                if not v:
                    self._collections.pop(k)

            self._collections.setdefault(newCol, [])
            self._collections[newCol].append(itemPid)

    def _selectCollectionParentId(self, values=None, pulldownList=None, parent=None):
        """Handle collection pulldown
        """
        if not (pulldownList and pulldownList.hasFocus()):
            return

        if (newCol := pulldownList.getText()):

            _selection = parent.getSelectedTexts()
            _count = values.parentItem.childCount()
            _children = []
            for i in range(_count):
                itm = values.parentItem.child(i)
                itemName = itm.data(0, 0)
                if itemName in _selection:
                    saveFrame = itm.data(1, 0)
                    _children.append((itm, itemName, saveFrame))

            for (itm, itmName, saveFrame) in _children:
                _itmPid = Pid.new(values.ccpnClassName, itmName) if values.ccpnClassName else itmName

                # remove from previous self._collections
                for k, v in list(self._collections.items()):
                    if _itmPid in v:
                        v.remove(_itmPid)
                    if not v:
                        self._collections.pop(k)

                self._collections.setdefault(newCol, [])
                self._collections[newCol].append(_itmPid)

    def _selectCollectionParentStructureId(self, values=None, pulldownList=None, parent=None):
        """Handle collection pulldown
        """
        if not (pulldownList and pulldownList.hasFocus()):
            return

        if (newCol := pulldownList.getText()):

            _selection = parent.getSelectedTexts()
            _count = values.parentItem.childCount()
            _children = []
            for i in range(_count):
                itm = values.parentItem.child(i)
                itemName = itm.data(0, 0)
                if itemName in _selection:
                    saveFrame = itm.data(1, 0)
                    _children.append((itm, itemName, saveFrame))

            for (itm, itmName, saveFrame) in _children:
                _itmStructureData = saveFrame.get('ccpn_dataset_id') or ''
                _itmPid = Pid.new(values.ccpnClassName, _itmStructureData, itmName) if values.ccpnClassName else itmName

                # remove from previous self._collections
                for k, v in list(self._collections.items()):
                    if _itmPid in v:
                        v.remove(_itmPid)
                    if not v:
                        self._collections.pop(k)

                self._collections.setdefault(newCol, [])
                self._collections[newCol].append(_itmPid)

    def _editComment(self, item=None, parentName=None, lineEdit=None, saveFrame=None, autoRename=False):
        """Handle clicking Set Comment button
        """
        with self._editSaveFrameItem(item, parentName, lineEdit, saveFrame, autoRename, 'ccpn_comment') as _edit:
            # reads a non-empty string for a value
            if not _edit.newVal and 'ccpn_comment' in saveFrame:
                del saveFrame['ccpn_comment']
            else:
                saveFrame['ccpn_comment'] = str(_edit.newVal)

    def _editParameterName(self, item=None, parentName=None, lineEdit=None, saveFrame=None, autoRename=False):
        """Handle clicking Set Parameter Name button
        """
        with self._editSaveFrameItem(item, parentName, lineEdit, saveFrame, autoRename, 'ccpn_parameter_name') as _edit:
            # reads a non-empty string for a value
            if not _edit.newVal and 'ccpn_parameter_name' in saveFrame:
                raise ValueError('ccpn_parameter_name cannot be empty')
            else:
                _oldName = saveFrame.get('ccpn_parameter_name')
                saveFrame['ccpn_parameter_name'] = str(_edit.newVal)

                if saveFrame.get('sf_category') in ['ccpn_parameter', ]:
                    if _edit.itemName and _oldName and _edit.itemName.endswith(_oldName):
                        _edit.itemName = _edit.itemName[:-len(_oldName)] + _edit.newVal

    def _repopulateview(self, _checks, itemName, newName, parentGroup, parentName):
        # everything okay - rebuild all for now, could make selective later
        self.nefTreeView._populateTreeView(self.project)
        self._fillPopup(self._nefDict)
        for ii, (_name, _, _treeParent) in enumerate(_checks):
            if _treeParent == parentGroup and _name == itemName and newName is not None:
                _name = newName

            _parent = self.nefTreeView.findSection(_treeParent)
            if _parent:
                # should be a single item
                _checkItem = self.nefTreeView.findSection(_name, _parent)
                if _checkItem:
                    _checkItem = _checkItem[0] if isinstance(_checkItem, list) else _checkItem
                    _checkItem.setCheckState(0, QtCore.Qt.Checked)
        # _parent = self.nefTreeView._contentParent(self.project, saveFrame, cat)\
        _parent = self.nefTreeView.findSection(parentName)
        if _parent:
            # should be a single item
            newItem = self.nefTreeView.findSection(newName or itemName, _parent)
            if newItem:
                newItem = newItem[0] if isinstance(newItem, list) else newItem
                self._nefTreeClickedCallback(newItem, 0)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    handleParentGroups = {'chains'               : partial(handleTreeViewParentGeneral, mappingCode='nef_sequence_chain_code'),
                          'chemicalShiftLists'   : partial(handleTreeViewParentGeneral, mappingCode='nef_chemical_shift_list'),
                          'restraintTables'      : partial(handleTreeViewParentGeneralStructureData, mappingCode='nef_distance_restraint_list'),
                          'peakLists'            : partial(handleTreeViewParentGeneral, mappingCode='nef_peak'),
                          'integralLists'        : partial(handleTreeViewParentGeneral, mappingCode='ccpn_integral_list'),
                          'multipletLists'       : partial(handleTreeViewParentGeneral, mappingCode='ccpn_multiplet_list'),
                          'samples'              : partial(handleTreeViewParentGeneral, mappingCode='ccpn_sample'),
                          'substances'           : partial(handleTreeViewParentGeneral, mappingCode='ccpn_substance'),
                          'nmrChains'            : partial(handleTreeViewParentGeneral, mappingCode='nmr_chain'),
                          'structureData'        : partial(handleTreeViewParentGeneral, mappingCode='ccpn_dataset'),
                          'complexes'            : partial(handleTreeViewParentGeneral, mappingCode='ccpn_complex'),
                          'spectrumGroups'       : partial(handleTreeViewParentGeneral, mappingCode='ccpn_spectrum_group'),
                          'notes'                : partial(handleTreeViewParentGeneral, mappingCode='ccpn_notes'),
                          'peakClusters'         : partial(handleTreeViewParentGeneral, mappingCode='ccpn_peak_cluster_list'),
                          'restraintLinks'       : None,
                          'violationTables'      : partial(handleTreeViewParentGeneralStructureData, mappingCode='ccpn_distance_restraint_violation_list'),
                          'dataTables'           : partial(handleTreeViewParentGeneral, mappingCode='ccpn_datatable'),
                          'additionalData'       : None,
                          'ccpnDataSetParameters': None,
                          'ccpnLogging'          : None,
                          }

    handleSaveFrames['nef_sequence'] = partial(handleTreeViewSelectionGeneral,
                                               prefix='nef_sequence_',
                                               mappingCode='nef_sequence_chain_code',
                                               errorCode='nef_sequence_chain_code',
                                               tableColourFunc=table_nef_molecular_system)

    handleSaveFrames['nef_chemical_shift_list'] = partial(handleTreeViewSelectionGeneral,
                                                          prefix='nef_chemical_shift_',
                                                          mappingCode='nef_chemical_shift_list',
                                                          errorCode='nef_chemical_shift_list',
                                                          tableColourFunc=None)

    handleSaveFrames['nef_distance_restraint_list'] = partial(handleTreeViewSelectionStructureDataParent,
                                                              prefix='nef_distance_restraint_',
                                                              mappingCode='nef_distance_restraint_list',
                                                              errorCode='nef_distance_restraint_list',
                                                              tableColourFunc=None)

    handleSaveFrames['nef_dihedral_restraint_list'] = partial(handleTreeViewSelectionStructureDataParent,
                                                              prefix='nef_dihedral_restraint_',
                                                              mappingCode='nef_dihedral_restraint_list',
                                                              errorCode='nef_dihedral_restraint_list',
                                                              tableColourFunc=None)

    handleSaveFrames['nef_rdc_restraint_list'] = partial(handleTreeViewSelectionStructureDataParent,
                                                         prefix='nef_rdc_restraint_',
                                                         mappingCode='nef_rdc_restraint_list',
                                                         errorCode='nef_rdc_restraint_list',
                                                         tableColourFunc=None)

    handleSaveFrames['ccpn_restraint_list'] = partial(handleTreeViewSelectionGeneral,
                                                      prefix='ccpn_restraint_',
                                                      mappingCode='ccpn_restraint_list',
                                                      errorCode='ccpn_restraint_list',
                                                      tableColourFunc=None)

    handleSaveFrames['nef_peak_restraint_links'] = partial(handleTreeViewSelectionGeneralNoCollection,
                                                           prefix='nef_peak_restraint_',
                                                           mappingCode='nef_peak_restraint_links',
                                                           errorCode='nef_peak_restraint_links',
                                                           tableColourFunc=None)

    handleSaveFrames['ccpn_sample'] = partial(handleTreeViewSelectionGeneral,
                                              prefix='ccpn_sample_component_',
                                              mappingCode='ccpn_sample',
                                              errorCode='ccpn_sample',
                                              tableColourFunc=None)

    handleSaveFrames['ccpn_complex'] = partial(handleTreeViewSelectionGeneral,
                                               prefix='ccpn_complex_chain_',
                                               mappingCode='ccpn_complex',
                                               errorCode='ccpn_complex',
                                               tableColourFunc=None)

    handleSaveFrames['ccpn_spectrum_group'] = partial(handleTreeViewSelectionGeneral,
                                                      prefix='ccpn_group_spectrum_',
                                                      mappingCode='ccpn_spectrum_group',
                                                      errorCode='ccpn_spectrum_group',
                                                      tableColourFunc=None)

    handleSaveFrames['ccpn_note'] = partial(handleTreeViewSelectionGeneral,
                                            prefix='ccpn_note_',
                                            mappingCode='ccpn_notes',
                                            errorCode='ccpn_notes',
                                            tableColourFunc=table_ccpn_notes)

    handleSaveFrames['ccpn_peak_list'] = partial(handleTreeViewSelectionCcpnList,
                                                 prefix='nef_peak_',
                                                 mappingCode='nef_peak',
                                                 errorCode='ccpn_peak_list_serial',
                                                 tableColourFunc=table_peak_lists)

    handleSaveFrames['ccpn_integral_list'] = partial(handleTreeViewSelectionCcpnList,
                                                     prefix='ccpn_integral_',
                                                     mappingCode='ccpn_integral_list',
                                                     errorCode='ccpn_integral_list_serial',
                                                     tableColourFunc=partial(table_lists, listName='ccpn_integral'))

    handleSaveFrames['ccpn_multiplet_list'] = partial(handleTreeViewSelectionCcpnList,
                                                      prefix='ccpn_multiplet_',
                                                      mappingCode='ccpn_multiplet_list',
                                                      errorCode='ccpn_multiplet_list_serial',
                                                      tableColourFunc=partial(table_lists, listName='ccpn_multiplet'))

    handleSaveFrames['ccpn_peak_cluster_list'] = partial(handleTreeViewSelectionGeneralNoCollection,
                                                         prefix='ccpn_peak_cluster_',
                                                         mappingCode='ccpn_peak_cluster',
                                                         errorCode='ccpn_peak_cluster_serial',
                                                         tableColourFunc=table_peak_clusters)

    handleSaveFrames['nmr_chain'] = partial(handleTreeViewSelectionAssignment,
                                            prefix='nmr_chain_',
                                            mappingCode='nmr_chain',
                                            errorCode='nmr_chain_serial',
                                            tableColourFunc=table_ccpn_assignment)

    handleSaveFrames['ccpn_substance'] = partial(handleTreeViewSelectionGeneral,
                                                 prefix='ccpn_substance_synonym_',
                                                 mappingCode='ccpn_substance',
                                                 errorCode='ccpn_substance',
                                                 tableColourFunc=None)

    handleSaveFrames['ccpn_internal_data'] = partial(handleTreeViewSelectionGeneralNoCollection,
                                                     prefix='ccpn_internal_data_',
                                                     mappingCode='ccpn_additional_data',
                                                     errorCode='ccpn_additional_data',
                                                     # tableColourFunc=table_ccpn_additional_data)
                                                     tableColourFunc=None)

    handleSaveFrames['ccpn_distance_restraint_violation_list'] = partial(handleTreeViewSelectionStructureDataParent,
                                                                         prefix='ccpn_distance_restraint_violation_',
                                                                         mappingCode='ccpn_distance_restraint_violation_list',
                                                                         errorCode='ccpn_distance_restraint_violation_list',
                                                                         tableColourFunc=None)

    handleSaveFrames['ccpn_dihedral_restraint_violation_list'] = partial(handleTreeViewSelectionStructureDataParent,
                                                                         prefix='ccpn_dihedral_restraint_violation_',
                                                                         mappingCode='ccpn_dihedral_restraint_violation_list',
                                                                         errorCode='ccpn_dihedral_restraint_violation_list',
                                                                         tableColourFunc=None)

    handleSaveFrames['ccpn_rdc_restraint_violation_list'] = partial(handleTreeViewSelectionStructureDataParent,
                                                                    prefix='ccpn_rdc_restraint_violation_',
                                                                    mappingCode='ccpn_rdc_restraint_violation_list',
                                                                    errorCode='ccpn_rdc_restraint_violation_list',
                                                                    tableColourFunc=None)

    handleSaveFrames['ccpn_datatable'] = partial(handleTreeViewSelectionGeneral,
                                                 prefix='ccpn_datatable_data_',
                                                 mappingCode='ccpn_datatable',
                                                 errorCode='ccpn_datatable',
                                                 tableColourFunc=None)

    handleSaveFrames['ccpn_collection'] = partial(handleTreeViewSelectionGeneralNoCollection,
                                                  prefix='ccpn_collection_',
                                                  mappingCode='ccpn_collections',
                                                  errorCode='ccpn_collections',
                                                  tableColourFunc=table_ccpn_collections)

    handleSaveFrames['ccpn_logging'] = partial(handleTreeViewSelectionGeneralNoCollection,
                                               prefix='ccpn_history_',
                                               mappingCode='ccpn_logging',
                                               errorCode='ccpn_logging',
                                               tableColourFunc=None)

    handleSaveFrames['ccpn_dataset'] = partial(handleTreeViewSelectionGeneral,
                                               prefix='ccpn_calculation_step_',
                                               mappingCode='ccpn_dataset',
                                               errorCode='ccpn_dataset',
                                               tableColourFunc=None)

    handleSaveFrames['ccpn_parameter'] = partial(handleTreeViewSelectionStructureDataParentNoCollection,
                                                 prefix='ccpn_dataframe_',
                                                 mappingCode='ccpn_parameter',
                                                 errorCode='ccpn_parameter',
                                                 tableColourFunc=None)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    _setBadSaveFrames['nef_sequence'] = partial(_set_bad_saveframe,
                                                prefix='nef_sequence_',
                                                mappingCode='nef_sequence_chain_code',
                                                errorCode='nef_sequence_chain_code',
                                                tableColourFunc=table_nef_molecular_system)

    _setBadSaveFrames['nef_chemical_shift_list'] = partial(_set_bad_saveframe,
                                                           prefix='nef_chemical_shift_',
                                                           mappingCode='nef_chemical_shift_list',
                                                           errorCode='nef_chemical_shift_list',
                                                           tableColourFunc=None)

    _setBadSaveFrames['nef_distance_restraint_list'] = partial(_set_bad_saveframe,
                                                               prefix='nef_distance_restraint_',
                                                               mappingCode='nef_distance_restraint_list',
                                                               errorCode='nef_distance_restraint_list',
                                                               tableColourFunc=None)

    _setBadSaveFrames['nef_dihedral_restraint_list'] = partial(_set_bad_saveframe,
                                                               prefix='nef_dihedral_restraint_',
                                                               mappingCode='nef_dihedral_restraint_list',
                                                               errorCode='nef_dihedral_restraint_list',
                                                               tableColourFunc=None)

    _setBadSaveFrames['nef_rdc_restraint_list'] = partial(_set_bad_saveframe,
                                                          prefix='nef_rdc_restraint_',
                                                          mappingCode='nef_rdc_restraint_list',
                                                          errorCode='nef_rdc_restraint_list',
                                                          tableColourFunc=None)

    _setBadSaveFrames['ccpn_restraint_list'] = partial(_set_bad_saveframe,
                                                       prefix='ccpn_restraint_',
                                                       mappingCode='ccpn_restraint_list',
                                                       errorCode='ccpn_restraint_list',
                                                       tableColourFunc=None)

    _setBadSaveFrames['nef_peak_restraint_links'] = partial(_set_bad_saveframe,
                                                            prefix='nef_peak_restraint_',
                                                            mappingCode='nef_peak_restraint_links',
                                                            errorCode='nef_peak_restraint_links',
                                                            tableColourFunc=None)

    _setBadSaveFrames['ccpn_sample'] = partial(_set_bad_saveframe,
                                               prefix='ccpn_sample_component_',
                                               mappingCode='ccpn_sample',
                                               errorCode='ccpn_sample',
                                               tableColourFunc=None)

    _setBadSaveFrames['ccpn_complex'] = partial(_set_bad_saveframe,
                                                prefix='ccpn_complex_chain_',
                                                mappingCode='ccpn_complex',
                                                errorCode='ccpn_complex',
                                                tableColourFunc=None)

    _setBadSaveFrames['ccpn_spectrum_group'] = partial(_set_bad_saveframe,
                                                       prefix='ccpn_group_spectrum_',
                                                       mappingCode='ccpn_spectrum_group',
                                                       errorCode='ccpn_spectrum_group',
                                                       tableColourFunc=None)

    _setBadSaveFrames['ccpn_note'] = partial(_set_bad_saveframe,
                                             prefix='ccpn_note_',
                                             mappingCode='ccpn_notes',
                                             errorCode='ccpn_notes',
                                             tableColourFunc=table_ccpn_notes)

    _setBadSaveFrames['ccpn_peak_list'] = partial(_set_bad_saveframe,
                                                  prefix='nef_peak_',
                                                  mappingCode='nef_peak',
                                                  errorCode='ccpn_peak_list_serial',
                                                  tableColourFunc=table_peak_lists)

    _setBadSaveFrames['ccpn_integral_list'] = partial(_set_bad_saveframe,
                                                      prefix='ccpn_integral_',
                                                      mappingCode='ccpn_integral_list',
                                                      errorCode='ccpn_integral_list_serial',
                                                      tableColourFunc=partial(table_lists, listName='ccpn_integral'))

    _setBadSaveFrames['ccpn_multiplet_list'] = partial(_set_bad_saveframe,
                                                       prefix='ccpn_multiplet_',
                                                       mappingCode='ccpn_multiplet_list',
                                                       errorCode='ccpn_multiplet_list_serial',
                                                       tableColourFunc=partial(table_lists, listName='ccpn_multiplet'))

    _setBadSaveFrames['ccpn_peak_cluster_list'] = partial(_set_bad_saveframe,
                                                          prefix='ccpn_peak_cluster_',
                                                          mappingCode='ccpn_peak_cluster',
                                                          errorCode='ccpn_peak_cluster_serial',
                                                          tableColourFunc=table_peak_clusters)

    _setBadSaveFrames['nmr_chain'] = partial(_set_bad_saveframe,
                                             prefix='nmr_chain_',
                                             mappingCode='nmr_chain',
                                             errorCode='nmr_chain_serial',
                                             tableColourFunc=table_ccpn_assignment)

    _setBadSaveFrames['ccpn_substance'] = partial(_set_bad_saveframe,
                                                  prefix='ccpn_substance_synonym_',
                                                  mappingCode='ccpn_substance',
                                                  errorCode='ccpn_substance',
                                                  tableColourFunc=None)

    _setBadSaveFrames['ccpn_internal_data'] = partial(_set_bad_saveframe,
                                                      prefix='ccpn_internal_data_',
                                                      mappingCode='ccpn_additional_data',
                                                      errorCode='ccpn_additional_data',
                                                      # tableColourFunc=table_ccpn_additional_data)
                                                      tableColourFunc=None)

    _setBadSaveFrames['ccpn_distance_restraint_violation_list'] = partial(_set_bad_saveframe,
                                                                          prefix='ccpn_distance_restraint_violation_',
                                                                          mappingCode='ccpn_distance_restraint_violation_list',
                                                                          errorCode='ccpn_distance_restraint_violation_list',
                                                                          tableColourFunc=None)

    _setBadSaveFrames['ccpn_dihedral_restraint_violation_list'] = partial(_set_bad_saveframe,
                                                                          prefix='ccpn_dihedral_restraint_violation_',
                                                                          mappingCode='ccpn_dihedral_restraint_violation_list',
                                                                          errorCode='ccpn_dihedral_restraint_violation_list',
                                                                          tableColourFunc=None)

    _setBadSaveFrames['ccpn_rdc_restraint_violation_list'] = partial(_set_bad_saveframe,
                                                                     prefix='ccpn_rdc_restraint_violation_',
                                                                     mappingCode='ccpn_rdc_restraint_violation_list',
                                                                     errorCode='ccpn_rdc_restraint_violation_list',
                                                                     tableColourFunc=None)

    _setBadSaveFrames['ccpn_datatable'] = partial(_set_bad_saveframe,
                                                  prefix='ccpn_datatable_data_',
                                                  mappingCode='ccpn_datatable',
                                                  errorCode='ccpn_datatable',
                                                  tableColourFunc=None)

    _setBadSaveFrames['ccpn_collection'] = partial(_set_bad_saveframe,
                                                   prefix='ccpn_collection_',
                                                   mappingCode='ccpn_collections',
                                                   errorCode='ccpn_collections',
                                                   tableColourFunc=table_ccpn_collections)
    _setBadSaveFrames['ccpn_logging'] = partial(_set_bad_saveframe,
                                                prefix='ccpn_history_',
                                                mappingCode='ccpn_logging',
                                                errorCode='ccpn_logging',
                                                tableColourFunc=None)

    _setBadSaveFrames['ccpn_dataset'] = partial(_set_bad_saveframe,
                                                prefix='ccpn_calculation_step_',
                                                mappingCode='ccpn_dataset',
                                                errorCode='ccpn_dataset',
                                                tableColourFunc=None)

    _setBadSaveFrames['ccpn_parameter'] = partial(_set_bad_saveframe,
                                                  prefix='ccpn_dataframe_',
                                                  mappingCode='ccpn_parameter',
                                                  errorCode='ccpn_parameter',
                                                  tableColourFunc=None)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    applyCheckBoxes['nef_sequence'] = partial(apply_checkBox_item,
                                              prefix='nef_sequence_',
                                              mappingCode='nef_sequence_chain_code',
                                              )

    applyCheckBoxes['nef_chemical_shift_list'] = partial(apply_checkBox_item,
                                                         prefix='nef_chemical_shift_',
                                                         mappingCode='nef_chemical_shift_list',
                                                         )

    applyCheckBoxes['nef_distance_restraint_list'] = partial(apply_checkBox_item,
                                                             prefix='nef_distance_restraint_',
                                                             mappingCode='nef_distance_restraint_list',
                                                             )

    applyCheckBoxes['nef_dihedral_restraint_list'] = partial(apply_checkBox_item,
                                                             prefix='nef_dihedral_restraint_',
                                                             mappingCode='nef_dihedral_restraint_list',
                                                             )

    applyCheckBoxes['nef_rdc_restraint_list'] = partial(apply_checkBox_item,
                                                        prefix='nef_rdc_restraint_',
                                                        mappingCode='nef_rdc_restraint_list',
                                                        )

    applyCheckBoxes['ccpn_restraint_list'] = partial(apply_checkBox_item,
                                                     prefix='ccpn_restraint_',
                                                     mappingCode='ccpn_restraint_list',
                                                     )

    applyCheckBoxes['nef_peak_restraint_links'] = partial(apply_checkBox_item,
                                                          prefix='nef_peak_restraint_',
                                                          mappingCode='nef_peak_restraint_links',
                                                          )

    applyCheckBoxes['ccpn_sample'] = partial(apply_checkBox_item,
                                             prefix='ccpn_sample_component_',
                                             mappingCode='ccpn_sample',
                                             )

    applyCheckBoxes['ccpn_complex'] = partial(apply_checkBox_item,
                                              prefix='ccpn_complex_chain_',
                                              mappingCode='ccpn_complex',
                                              )

    applyCheckBoxes['ccpn_spectrum_group'] = partial(apply_checkBox_item,
                                                     prefix='ccpn_group_spectrum_',
                                                     mappingCode='ccpn_spectrum_group',
                                                     )

    applyCheckBoxes['ccpn_note'] = partial(apply_checkBox_item,
                                           prefix='ccpn_note_',
                                           mappingCode='ccpn_notes',
                                           )

    applyCheckBoxes['ccpn_peak_list'] = partial(apply_checkBox_item,
                                                prefix='nef_peak_',
                                                mappingCode='nef_peak',
                                                checkID='_importPeaks',
                                                )

    applyCheckBoxes['ccpn_integral_list'] = partial(apply_checkBox_item,
                                                    prefix='ccpn_integral_',
                                                    mappingCode='ccpn_integral_list',
                                                    checkID='_importIntegrals',
                                                    )

    applyCheckBoxes['ccpn_multiplet_list'] = partial(apply_checkBox_item,
                                                     prefix='ccpn_multiplet_',
                                                     mappingCode='ccpn_multiplet_list',
                                                     checkID='_importMultiplets',
                                                     )

    applyCheckBoxes['ccpn_peak_cluster_list'] = partial(apply_checkBox_item,
                                                        prefix='ccpn_peak_cluster_',
                                                        mappingCode='ccpn_peak_cluster',
                                                        )

    applyCheckBoxes['nmr_chain'] = partial(apply_checkBox_item,
                                           prefix='nmr_chain_',
                                           mappingCode='nmr_chain',
                                           )

    applyCheckBoxes['ccpn_substance'] = partial(apply_checkBox_item,
                                                prefix='ccpn_substance_synonym_',
                                                mappingCode='ccpn_substance',
                                                )

    applyCheckBoxes['nef_peak_restraint_link'] = partial(apply_checkBox_item,
                                                         prefix='nef_peak_restraint_',
                                                         mappingCode='nef_peak_restraint_link',
                                                         )

    applyCheckBoxes['ccpn_internal_data'] = partial(apply_checkBox_item,
                                                    prefix='ccpn_internal_data_',
                                                    mappingCode='ccpn_additional_data',
                                                    )

    applyCheckBoxes['ccpn_distance_restraint_violation_list'] = partial(apply_checkBox_item,
                                                                        prefix='ccpn_distance_restraint_violation_',
                                                                        mappingCode='ccpn_distance_restraint_violation_list',
                                                                        )

    applyCheckBoxes['ccpn_dihedral_restraint_violation_list'] = partial(apply_checkBox_item,
                                                                        prefix='ccpn_dihedral_restraint_violation_',
                                                                        mappingCode='ccpn_dihedral_restraint_violation_list',
                                                                        )

    applyCheckBoxes['ccpn_rdc_restraint_violation_list'] = partial(apply_checkBox_item,
                                                                   prefix='ccpn_rdc_restraint_violation_',
                                                                   mappingCode='ccpn_rdc_restraint_violation_list',
                                                                   )

    applyCheckBoxes['ccpn_datatable'] = partial(apply_checkBox_item,
                                                prefix='ccpn_datatable_data_',
                                                mappingCode='ccpn_datatable',
                                                )

    applyCheckBoxes['ccpn_collection'] = partial(apply_checkBox_item,
                                                 prefix='ccpn_collection_',
                                                 mappingCode='ccpn_collections',
                                                 )

    applyCheckBoxes['ccpn_logging'] = partial(apply_checkBox_item,
                                              prefix='ccpn_history_',
                                              mappingCode='ccpn_logging',
                                              )

    applyCheckBoxes['ccpn_dataset'] = partial(apply_checkBox_item,
                                              prefix='ccpn_calculation_step_',
                                              mappingCode='ccpn_dataset',
                                              )

    applyCheckBoxes['ccpn_parameter'] = partial(apply_checkBox_item,
                                                prefix='ccpn_dataframe_',
                                                mappingCode='ccpn_parameter',
                                                )

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _autoRenameItem(self, name, saveFrame, parentGroup):
        if not saveFrame:
            return

        mapping = self.nefTreeView.nefProjectToSaveFramesMapping.get(parentGroup)
        primaryHandler = self.nefTreeView.nefProjectToHandlerMapping.get(parentGroup) or saveFrame.get('sf_category')
        if primaryHandler:
            handler = self.handleSaveFrames.get(primaryHandler)
            if handler is not None:
                # handler(self, saveFrame, item)
                handler(self, name=name, saveFrame=saveFrame, parentGroup=parentGroup, _handleAutoRename=True)  #, item)

    def _checkBadItem(self, name, saveFrame, parentGroup):
        if not saveFrame:
            return

        mapping = self.nefTreeView.nefProjectToSaveFramesMapping.get(parentGroup)
        primaryHandler = self.nefTreeView.nefProjectToHandlerMapping.get(parentGroup) or saveFrame.get('sf_category')
        if primaryHandler:
            handler = self._setBadSaveFrames.get(primaryHandler)
            if handler is not None:
                # handler(self, saveFrame, item)
                return handler(self, name=name, saveFrame=saveFrame, parentGroup=parentGroup, )  #, item)

    # from ccpn.util.decorators import profile
    #
    # @profile()
    def _nefTreeClickedCallback(self, item, column=0):
        """Handle clicking on an item in the nef tree
        """
        itemName = item.data(0, 0)
        saveFrame = item.data(1, 0)
        if saveFrame and hasattr(saveFrame, '_content'):
            self._itemSelected(item, itemName, saveFrame)

        else:
            self._parentSelected(item, itemName)

    def _itemSelected(self, item, itemName, saveFrame):
        with self._tableSplitter.blockWidgetSignals(recursive=False):
            self._tableSplitter.setVisible(False)

            # reuse the widgets?
            for widg in self._nefWidgets:
                self._removeWidget(widg, removeTopWidget=True)
            self._nefWidgets = []
            self._removeWidget(self.frameOptionsFrame, removeTopWidget=False)

            _fillColour = INVALIDTABLEFILLNOCHECKCOLOUR if item.checkState(0) else INVALIDTABLEFILLNOCHECKCOLOUR

            parentGroup = item.parent().data(0, 0) if item.parent() else repr(None)

            # add the first table from the saveframe attributes
            loop = StarIo.NmrLoop(name=saveFrame.name, columns=('attribute', 'value'))
            for k, v in saveFrame.items():
                if not (k.startswith('_') or isinstance(v, StarIo.NmrLoop)):
                    loop.newRow((k, v))
            _name, _data = saveFrame.name, loop.data

            self._nefTables = {}
            frame, table = self._addTableToFrame(_data, _name.upper())
            self._tableSplitter.addWidget(frame)
            self._nefWidgets = [frame, ]

            # get the group name add fetch the correct mapping
            mapping = self.nefTreeView.nefProjectToSaveFramesMapping.get(parentGroup)
            primaryHandler = self.nefTreeView.nefProjectToHandlerMapping.get(parentGroup) or saveFrame.get('sf_category')

            # add tables from the loops in the saveframe
            loops = self._nefReader._getLoops(self.project, saveFrame)
            for loop in loops:

                if mapping and loop.name not in mapping:
                    continue

                _name, _data = loop.name, loop.data
                frame, table = self._addTableToFrame(_data, _name)
                self._tableSplitter.addWidget(frame)
                self._nefWidgets.append(frame)

                if loop.name in saveFrame._content and \
                        hasattr(saveFrame, '_rowErrors') and \
                        loop.name in saveFrame._rowErrors:
                    badRows = list(saveFrame._rowErrors[loop.name])

                    with self._tableColouring(table) as setRowBackgroundColour:
                        for rowIndex in badRows:
                            setRowBackgroundColour(rowIndex, _fillColour)

            if primaryHandler:
                handler = self.handleSaveFrames.get(primaryHandler)
                if handler is not None:
                    # handler(self, saveFrame, item)
                    handler(self, name=itemName, saveFrame=saveFrame, parentGroup=parentGroup)

            # clicking the checkbox also comes here - above loop may set item._badName
            self._colourTreeView()

            self._filterLogFrame.setVisible(self._enableFilterFrame)
            self.nefTreeView.setCurrentItem(item)
        self._tableSplitter.setVisible(True)

    def _parentSelected(self, parentItem, parentItemName):

        def _depth(item):
            depth = 0
            while item:
                item = item.parent()
                depth += 1
            return depth

        with self._tableSplitter.blockWidgetSignals(recursive=False):
            self._tableSplitter.setVisible(False)

            # show items in listWidget
            # add items to collection
            # add actions from right-mouse menu
            # add parent-specific actions
            #   e.g. set all to same ccpn_structuredata_name

            # depth = 1 -> project
            # depth = 2 -> groups
            # depth = 3 -> saveFrames - either item or object, e.g., restraintList, note

            # reuse the widgets?
            for widg in self._nefWidgets:
                self._removeWidget(widg, removeTopWidget=True)
            self._nefWidgets = []
            self._removeWidget(self.frameOptionsFrame, removeTopWidget=False)

            if _depth(parentItem) != 2:
                return

            # this could be nested if you click on the project
            _count = parentItem.childCount()
            # _children = []
            # for i in range(_count):
            #     itm = parentItem.child(i)
            #
            #     itemName = itm.data(0, 0)
            #     saveFrame = itm.data(1, 0)
            #
            #     _children.append((itm, itemName, saveFrame))

            if _count:
            # if _children:
                # show a parent widget

                # frame = MoreLessFrame(self, name=parentItemName, showMore=True, grid=(0, 0))
                # self._tableSplitter.addWidget(frame)
                # self._nefWidgets = [frame, ]
                #
                # widg = ListWidget(frame.contentsFrame, grid=(1, 0), gridSpan=(5, 1))
                # widg.addItems([itemName for (_, itemName, _) in _children])

                # get details from the first item
                # item, itemName, saveFrame = _children[0]
                # parentGroup = item.parent().data(0, 0) if item.parent() else repr(None)
                #
                # # get the group name add fetch the correct mapping
                # mapping = self.nefTreeView.nefProjectToSaveFramesMapping.get(parentGroup)
                # primaryHandler = self.nefTreeView.nefProjectToHandlerMapping.get(parentGroup) or saveFrame.get('sf_category')
                #
                # if primaryHandler:
                #     handler = self.handleSaveFrames.get(primaryHandler)
                #     if handler is not None:
                #         # NOTE:ED - currently the wrong handler
                #         pass
                #         # handler(self, name=itemName, saveFrame=saveFrame, parentGroup=parentGroup)

                # call the correct parent handler to add the correct widgets
                parentHandler = self.handleParentGroups.get(parentItemName)
                if parentHandler is not None:
                    parentHandler(self, parentItem=parentItem, parentItemName=parentItemName, _handleAutoRename=False)

        self._tableSplitter.setVisible(True)

    @contextmanager
    def _tableColouring(self, table):
        # not sure this is needed now - handled by the pandasModel indexing
        def _setRowBackgroundColour(row, colour):
            # set the colour for the items in the model colour table
            for j in _cols:
                model._colourData[row, j] = QtCore.QVariant(QtGui.QBrush(colour))

        model = table.model()
        _cols = range(model.columnCount())

        yield _setRowBackgroundColour


    class FastTableView(QtWidgets.QTableView):

        styleSheet = """
                        QTableView {
                            background-color: %(GUITABLE_BACKGROUND)s;
                            alternate-background-color: %(GUITABLE_ALT_BACKGROUND)s;
                            border: 1px solid %(BORDER_NOFOCUS)s;
                            border-radius: 2px;
                        }

                        QTableView::item {
                            padding: 2px;
                            color: %(GUITABLE_ITEM_FOREGROUND)s;
                        }

                        QTableView::item:selected {
                            background-color: %(GUITABLE_SELECTED_BACKGROUND)s;
                            color: %(GUITABLE_SELECTED_FOREGROUND)s;
                        }
                    """

        def __init__(self, *args, **kwds):
            super().__init__(*args, **kwds)

            # set stylesheet
            self.colours = getColours()
            self._defaultStyleSheet = self.styleSheet % self.colours
            self.setStyleSheet(self._defaultStyleSheet)
            self.setAlternatingRowColors(True)

            # set the preferred scrolling behaviour
            self.setHorizontalScrollMode(self.ScrollPerPixel)
            self.setVerticalScrollMode(self.ScrollPerPixel)
            self.setSelectionBehavior(self.SelectRows)

            # enable sorting and sort on the first column
            self.setSortingEnabled(True)
            self.sortByColumn(0, QtCore.Qt.AscendingOrder)

            # the resizeColumnsToContents is REALLY slow :|
            _header = self.horizontalHeader()
            # set Interactive and last column to expanding
            _header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
            _header.setStretchLastSection(True)
            # only look at visible section
            _header.setResizeContentsPrecision(1)
            _header.setDefaultAlignment(QtCore.Qt.AlignLeft)
            _header.setMinimumSectionSize(16)
            _header.setHighlightSections(self.font().bold())
            setWidgetFont(self, name=TABLEFONT)
            setWidgetFont(_header, name=TABLEFONT)
            setWidgetFont(self.verticalHeader(), name=TABLEFONT)

            _header = self.verticalHeader()
            # set Interactive and last column to expanding
            _header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
            _header.setStretchLastSection(False)
            # only look at visible section
            _header.setResizeContentsPrecision(1)
            _header.setDefaultAlignment(QtCore.Qt.AlignLeft)
            _header.setMinimumSectionSize(16)
            _header.setVisible(True)
            _header.setFixedWidth(10)  # gives enough of a handle to resize

            _header.setHighlightSections(self.font().bold())
            setWidgetFont(self, name=TABLEFONT)
            setWidgetFont(_header, name=TABLEFONT)
            setWidgetFont(self.verticalHeader(), name=TABLEFONT)

            _height = getFontHeight(name=TABLEFONT, size='MEDIUM')
            self.setMinimumSize(3 * _height, 3 * _height + self.horizontalScrollBar().height())


    class pandasModel(QtCore.QAbstractTableModel):

        def __init__(self, data):
            QtCore.QAbstractTableModel.__init__(self)
            self._data = data
            # create a numpy array to match the data that will hold background colour
            self._colourData = np.zeros(self._data.shape, dtype=np.object)

        def rowCount(self, parent=None):
            return self._data.shape[0]

        def columnCount(self, parent=None):
            return self._data.shape[1]

        def data(self, index, role=QtCore.Qt.DisplayRole):
            if index.isValid():
                if role == QtCore.Qt.DisplayRole:
                    return str(self._data.iat[index.row(), index.column()])

                if role == QtCore.Qt.BackgroundColorRole:
                    # search if the colour has been set in the colour table
                    if (_col := self._colourData[index.row(), index.column()]):
                        return _col

            return None

        def headerData(self, col, orientation, role=None):
            if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
                return self._data.columns[col]
            return None


    def _addTableToFrame(self, _data, _name):
        """Add a new gui table into a moreLess frame to hold a nef loop
        """
        frame = MoreLessFrame(self, name=_name, showMore=True, grid=(0, 0))
        # table = GuiTable(frame.contentsFrame, grid=(0, 0), gridSpan=(1, 1), multiSelect=True)
        # table._hiddenColumns = []

        table = self.FastTableView(frame.contentsFrame)
        frame.contentsFrame.getLayout().addWidget(table, 0, 0)
        _model = self.pandasModel(pd.DataFrame(_data))

        # with table.blockWidgetSignals(root=table, recursive=False):
        #     table.setData(_data)
        table.setModel(_model)

        # table.resizeColumnsToContents()  # these are REALLY slow
        # table.resizeRowsToContents()

        self._nefTables[_name] = table

        return frame, table

    def _fillPopup(self, nefObject=None):
        """Initialise the project setting - only required for testing
        Assumes that the nef loaders may not be initialised if called from outside of Analysis
        """
        if not self._nefLoader:
            self._nefLoader = self._nefImporterClass(errorLogging=Nef.el.NEF_STANDARD, hidePrefix=True)

            if not self.project:
                raise TypeError('Project is not defined')
            self._nefWriter = CcpnNefIo.CcpnNefWriter(self.project)
            self._nefDict = self._nefLoader._nefDict = self._nefWriter.exportProject(expandSelection=True, pidList=None)

        # attach the import/verify/content methods
        self._nefLoader._attachVerifier(self._nefReader.verifyProject)
        self._nefLoader._attachReader(self._nefReader.importExistingProject)
        self._nefLoader._attachContent(self._nefReader.contentNef)
        self._nefLoader._attachClear(self._nefReader.clearSaveFrames)

        # process the contents and verify
        self._nefLoader._clearNef(self.project, self._nefDict)
        self._nefLoader._contentNef(self.project, self._nefDict, selection=None)

        # changed to verify with the button
        if not self._primaryProject and self.verifyCheckBox.isChecked():
            warnings, errors = self._nefLoader._verifyNef(self.project, self._nefDict, selection=None)

        try:
            self.valid = self._nefLoader.isValid
        except Exception as es:
            getLogger().warning(str(es))

        self._populate()

    def _verifyPopulate(self):
        """Respond to clicking the verify button
        """
        from ccpn.core.lib.ContextManagers import notificationEchoBlocking

        if not self._primaryProject:
            with notificationEchoBlocking():
                self.nefTreeView._populateTreeView(self.project)
                warnings, errors = self._nefLoader._verifyNef(self.project, self._nefDict, selection=None)

                try:
                    self.valid = self._nefLoader.isValid
                except Exception as es:
                    getLogger().warning(str(es))

                self._populate()

    def getItemsToImport(self):
        self._nefReader.setImportAll(False)
        treeItems = [item for item in self.nefTreeView.traverseTree() if item.checkState(0) == QtCore.Qt.Checked]
        selection = [item.data(1, 0) for item in treeItems] or [None]

        self._nefReader._importDict = {}
        for item in treeItems:

            itemName = item.data(0, 0)
            saveFrame = item.data(1, 0)
            parentGroup = item.parent().data(0, 0) if item.parent() else repr(None)

            # mapping = self.nefTreeView.nefProjectToSaveFramesMapping.get(parentGroup)
            handlerMapping = self.nefTreeView.nefProjectToHandlerMapping
            if handlerMapping and saveFrame:
                primaryHandler = handlerMapping.get(parentGroup) or saveFrame.get('sf_category')
                if primaryHandler:
                    handler = self.applyCheckBoxes.get(primaryHandler)
                    if handler is not None:
                        # handler(self, saveFrame, item)
                        handler(self, name=itemName, saveFrame=saveFrame, parentGroup=parentGroup)  #, item)

        return selection


class ImportNefPopup(CcpnDialogMainWidget):
    """
    Nef management class
    """
    USESCROLLWIDGET = True
    FIXEDWIDTH = False
    FIXEDHEIGHT = False
    DEFAULTMARGINS = (5, 5, 5, 5)

    def __init__(self, parent, mainWindow, project, nefImporter, **kwds):
        """
        Initialise the main form

        :param parent: calling widget
        :param mainWindow: gui mainWindow class for the application
        :param project: a Project instance
        :param nefImporter: A (CcpNmr) NefImporter instance
        :param kwds: additional parameters to pass to the window
        """
        size = (1000, 700)
        super().__init__(parent, setLayout=True, windowTitle='Import Nef', size=size, **kwds)
        self._size = size  # GWV: this seems to fail if I make this a class attribute

        # nefObjects=({NEFFRAMEKEY_IMPORT: project,
        #             },
        #             {NEFFRAMEKEY_IMPORT           : nefImporter,
        #              NEFFRAMEKEY_ENABLECHECKBOXES : True,
        #              NEFFRAMEKEY_ENABLERENAME     : True,
        #              NEFFRAMEKEY_ENABLEFILTERFRAME: True,
        #              NEFFRAMEKEY_ENABLEMOUSEMENU  : True,
        #              NEFFRAMEKEY_PATHNAME         : str(path),
        #              }
        #             )

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = project

        self._nefImporter = nefImporter
        self._path = nefImporter.path

        # if not isinstance(nefImporterClass, (type(Nef.NefImporter), type(None))):
        #     raise RuntimeError(f'{nefImporterClass} must be of type {Nef.NefImporter}')
        # self._nefImporterClass = nefImporterClass if nefImporterClass else Nef.NefImporter

        # # create a list of nef dictionary objects
        # self.setNefObjects(nefObjects)

        # object to contain items that are to be imported
        self._saveFrameSelection = []
        self._activeImportWindow = None

        # set up the widgets
        self.setWidgets()
        # populate the widgets
        self._populate()

        # enable the buttons
        self.setOkButton(callback=self._okClicked, text='Import', tipText='Import nef file over existing project')
        self.setCancelButton(callback=self.reject, tipText='Cancel import')
        self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)
        self.__postInit__()

        self._okButton = self.getButton(self.OKBUTTON)

        self.fillPopup()

    def setWidgets(self):
        """Initialise the main widgets for the form
        """
        self.paneSplitter = Splitter(self.mainWidget, setLayout=True, horizontal=True)
        self.paneSplitter.setChildrenCollapsible(False)
        self.mainWidget.getLayout().addWidget(self.paneSplitter, 0, 0)

        self._nefWindows = OrderedDict()
        # for nefObj in self.nefObjects:
        #     # for obj, enableCheckBoxes, enableRename in self.nefObjects:
        #
        #     # add a new nefDictFrame for each of the objects in the list (project or nefImporter)
        #     newWindow = NefDictFrame(parent=self,
        #                              mainWindow=self.mainWindow,
        #                              nefLoader=self._nefImporter,
        #                              pathName=self._path,
        #                              grid=(0, 0), showBorder=True,
        #                              **nefObj)
        #
        #     self._nefWindows[nefObj[NEFFRAMEKEY_IMPORT]] = newWindow
        #     self.paneSplitter.addWidget(newWindow)
        _options = {NEFFRAMEKEY_ENABLECHECKBOXES : True,
                    NEFFRAMEKEY_ENABLERENAME     : True,
                    NEFFRAMEKEY_ENABLEFILTERFRAME: True,
                    NEFFRAMEKEY_ENABLEMOUSEMENU  : True,
                    }
        newWindow = NefDictFrame(parent=self,
                                 mainWindow=self.mainWindow,
                                 nefLoader=self._nefImporter,
                                 pathName=self._path,
                                 grid=(0, 0), showBorder=True,
                                 **_options
                                 )

        self._nefWindows[self._nefImporter.getName(prePend=True)] = newWindow
        self.paneSplitter.addWidget(newWindow)
        self.setActiveNefWindow(0)

    def _populate(self):
        """Populate all frames
        """
        for nefWindow in self._nefWindows.values():
            nefWindow._populate()

    def accept(self):
        """Accept the dialog
        """
        # if the mouse is over the ok button and it has focus
        if self._okButton.hasFocus() and self._okButton.underMouse():
            super().accept()

    def setNefObjects(self, nefObjects):
        # create a list of nef dictionary objects here and add to splitter
        # self.nefObjects = tuple(obj for obj in nefObjects if isinstance(obj, tuple)
        #                         and len(obj) == 3
        #                         and isinstance(obj[0], (Nef.NefImporter, Project))
        #                         and isinstance(obj[1], bool)
        #                         and isinstance(obj[2], bool))
        self.nefObjects = ()
        if not isinstance(nefObjects, (tuple, list)):
            raise TypeError('nefObjects {} must be a list/tuple'.format(nefObjects))
        for checkObj in nefObjects:
            if not isinstance(checkObj, dict):
                raise TypeError('nefDictFrame object {} must be a dict'.format(checkObj))

            for k, val in checkObj.items():
                if k not in NEFDICTFRAMEKEYS.keys():
                    raise TypeError('nefDictFrame object {} contains a bad key {}'.format(checkObj, k))
                if not isinstance(val, (NEFDICTFRAMEKEYS[k])):
                    raise TypeError('nefDictFrame key {} must be of type {}'.format(k, NEFDICTFRAMEKEYS[k]))
            missingKeys = list([kk for kk in NEFDICTFRAMEKEYS_REQUIRED if kk not in checkObj.keys()])
            if missingKeys:
                raise TypeError('nefDictFrame missing keys {}'.format(repr(missingKeys)))

            self.nefObjects += (checkObj,)

        if len(self.nefObjects) != len(nefObjects):
            getLogger().warning('nefObjects contains bad items {}'.format(nefObjects))

    def setActiveNefWindow(self, value):
        """Set the number of the current active nef window for returning values from the dialog
        """
        if isinstance(value, int) and 0 <= value < len(self._nefWindows):
            self._activeImportWindow = value
        else:
            ll = len(self._nefWindows)
            raise TypeError('Invalid window number, must be 0{}{}'.format('-' if ll > 1 else '',
                                                                          (ll - 1) if ll > 1 else ''))

    def getActiveNefReader(self):
        """Get the current active nef reader for the dialog
        """
        return list(self._nefWindows.values())[self._activeImportWindow]._nefReader

    def _initialiseProject(self, mainWindow, application, project):
        """Initialise the project setting - only required for testing
        """
        self.mainWindow = mainWindow
        self.application = application
        self.project = project
        if mainWindow is None:
            self.mainWindow = AttrDict()

        # set the new values for application and project
        self.mainWindow.application = application
        self.mainWindow.project = project

        # set the projects for the windows
        for nefWindow in self._nefWindows.values():
            nefWindow._initialiseProject(mainWindow, application, project)

    def fillPopup(self):
        # set the projects for the windows
        for obj, nefWindow in self._nefWindows.items():
            nefWindow._fillPopup(obj)

            for itm in nefWindow.nefTreeView.traverseTree():
                if itm.data(0, 0) not in nefWindow.nefTreeView.nefProjectToSaveFramesMapping:
                    nefWindow._nefTreeClickedCallback(itm, 0)
                    nefWindow.nefTreeView.setCurrentItem(itm)
                    break

        # NOTE:ED - temporary function to create a contentCompare from the two nef windows
        nefDictTuple = ()
        for obj, nefWindow in self._nefWindows.items():
            nefDictTuple += (nefWindow._nefDict,)
        if nefDictTuple:
            for obj, nefWindow in self._nefWindows.items():
                nefWindow._contentCompareDataBlocks = nefDictTuple

    def exec_(self) -> int:
        # NOTE:ED - this will do for the moment
        self.resize(*self._size)
        return super(ImportNefPopup, self).exec_()

    def _createContentCompare(self):
        pass

    def _okClicked(self):
        """Accept the dialog, set the selection list _selectedSaveFrames to the required items
        """
        self._saveFrameSelection = list(self._nefWindows.values())[self._activeImportWindow].getItemsToImport()
        self.accept()


def main():
    """Testing code for the new nef manager
    """

    # from sandbox.Geerten.Refactored.framework import Framework
    # from sandbox.Geerten.Refactored.programArguments import Arguments

    from ccpn.framework.Framework import Framework
    from ccpn.framework.Application import Arguments

    _makeMainWindowVisible = False


    class MyProgramme(Framework):
        """My first app"""
        pass


    myArgs = Arguments()
    myArgs.interface = 'NoUi'
    myArgs.debug = True
    myArgs.darkColourScheme = False
    myArgs.lightColourScheme = True

    application = MyProgramme('MyProgramme', '3.0.1', args=myArgs)
    ui = application.ui
    ui.initialize(ui.mainWindow)  # ui.mainWindow not needed for refactored?

    if _makeMainWindowVisible:
        ui.mainWindow._updateMainWindow(newProject=True)
        ui.mainWindow.show()
        QtWidgets.QApplication.setActiveWindow(ui.mainWindow)

    # register the programme
    from ccpn.framework.Application import ApplicationContainer

    container = ApplicationContainer()
    container.register(application)
    application.useFileLogger = True

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # TESTNEF = '/Users/ejb66/Documents/nefTestProject.nef'
    # TESTNEF2 = '/Users/ejb66/Documents/nefTestProject0.nef'

    # TESTNEF = '/Users/ejb66/Documents/nefTestProject.nef'
    # TESTNEF2 = '/Users/ejb66/Documents/nefTestProject.nef'

    TESTNEF = '/Users/ejb66/Documents/CcpNmrData/nefTestProject.nef'
    TESTNEF2 = '/Users/ejb66/Documents/CcpNmrData/nefTestProject0.nef'

    # TESTNEF = '/Users/ejb66/Documents/TutorialProject2.nef'
    # TESTNEF2 = '/Users/ejb66/Documents/CcpNmrData/nefTestProject0.nef'

    # TESTNEF = '/Users/ejb66/Desktop/Ccpn_v2_testNef_a1.nef'
    # TESTNEF2 = '/Users/ejb66/Desktop/Ccpn_v2_testNef_a1.nef'

    # VALIDATEDICT = '/Users/ejb66/PycharmProjects/Git/AnalysisV3/src/python/ccpn/util/nef/NEF/specification/mmcif_nef_v1_1.dic'
    # VALIDATEDICT = '/Users/ejb66/Desktop/mmcif_nef_v1_1.dic'
    DEFAULTNAME = 'default'

    from ccpn.util.nef import NefImporter as Nef

    # load the file and the validate dict
    _loader = Nef.NefImporter(errorLogging=Nef.el.NEF_STRICT, hidePrefix=True)
    _loader.loadFile(TESTNEF)

    # load the file and the validate dict
    _loader2 = Nef.NefImporter(errorLogging=Nef.el.NEF_STRICT, hidePrefix=True)
    _loader2.loadFile(TESTNEF2)

    # validate
    valid = _loader.isValid
    if not valid:
        errLog = _loader.validErrorLog
        for k, val in errLog.items():
            if val:
                print('>>> {} : {}'.format(k, val))

    valid = _loader2.isValid
    if not valid:
        errLog = _loader2.validErrorLog
        for k, val in errLog.items():
            if val:
                print('>>> {} : {}'.format(k, val))

    # # simple test print of saveframes
    # names = _loader.getSaveFrameNames(returnType=Nef.NEF_RETURNALL)
    # for name in names:
    #     print(name)
    #     saveFrame = _loader.getSaveFrame(name)
    #     print(saveFrame)

    # create a list of which saveframes to load, with a parameters dict for each
    loadDict = {'nef_molecular_system'     : {},
                'nef_nmr_spectrum_cnoesy1' : {},
                'nef_chemical_shift_list_1': {},
                }

    # need a project
    name = _loader.getName()
    project = application.newProject(name or DEFAULTNAME)

    project.shiftAveraging = False

    nefReader = CcpnNefIo.CcpnNefReader(application)
    _loader._attachVerifier(nefReader.verifyProject)
    _loader._attachReader(nefReader.importExistingProject)
    _loader._attachContent(nefReader.contentNef)

    from ccpn.core.lib.ContextManagers import notificationEchoBlocking

    with notificationEchoBlocking():
        with catchExceptions(application=application, errorStringTemplate='Error loading Nef file: %s'):
            nefReader.setImportAll(True)
            _loader._importNef(project, _loader._nefDict, selection=None)

    nefReader.testPrint(project, _loader._nefDict, selection=None)
    nefReader.testErrors(project, _loader._nefDict, selection=None)

    app = QtWidgets.QApplication(['testApp'])
    # run the dialog
    dialog = ImportNefPopup(parent=ui.mainWindow, mainWindow=ui.mainWindow,
                            # nefObjects=(_loader,))
                            nefObjects=({NEFFRAMEKEY_IMPORT: project,
                                         },
                                        {NEFFRAMEKEY_IMPORT           : _loader2,
                                         NEFFRAMEKEY_ENABLECHECKBOXES : True,
                                         NEFFRAMEKEY_ENABLERENAME     : True,
                                         NEFFRAMEKEY_ENABLEFILTERFRAME: True,
                                         NEFFRAMEKEY_ENABLEMOUSEMENU  : True,
                                         NEFFRAMEKEY_PATHNAME         : TESTNEF2,
                                         }
                                        )
                            )

    dialog._initialiseProject(ui.mainWindow, application, project)
    dialog.fillPopup()
    dialog.setActiveNefWindow(1)

    # NOTE:ED - add routines here to set up the mapping between the different nef file loaded
    val = dialog.exec_()
    print('>>> dialog exit {}'.format(val))

    import ccpn.util.nef.nef as NefModule

    # NOTE:ED - by default pidList=None selects everything in the project
    # from ccpn.core.Chain import Chain
    # from ccpn.core.ChemicalShiftList import ChemicalShiftList
    # from ccpn.core.RestraintTable import RestraintTable
    # from ccpn.core.PeakList import PeakList
    # from ccpn.core.IntegralList import IntegralList
    # from ccpn.core.MultipletList import MultipletList
    # from ccpn.core.PeakCluster import PeakCluster
    # from ccpn.core.Sample import Sample
    # from ccpn.core.Substance import Substance
    # from ccpn.core.NmrChain import NmrChain
    # from ccpn.core.StructureData import StructureData
    # from ccpn.core.Complex import Complex
    # from ccpn.core.SpectrumGroup import SpectrumGroup
    # from ccpn.core.Note import Note
    #
    # # set the items in the project that can be exported
    # checkList = [
    #     Chain._pluralLinkName,
    #     ChemicalShiftList._pluralLinkName,
    #     RestraintTable._pluralLinkName,
    #     PeakList._pluralLinkName,
    #     IntegralList._pluralLinkName,
    #     MultipletList._pluralLinkName,
    #     Sample._pluralLinkName,
    #     Substance._pluralLinkName,
    #     NmrChain._pluralLinkName,
    #     StructureData._pluralLinkName,
    #     Complex._pluralLinkName,
    #     SpectrumGroup._pluralLinkName,
    #     Note._pluralLinkName,
    #     PeakCluster._pluralLinkName,
    #     ]
    # # build a complete list of items to grab from the project
    # pidList = []
    # for name in checkList:
    #     if hasattr(project, name):
    #         for obj in getattr(project, name):
    #             pidList.append(obj.pid)

    from ccpn.util.AttrDict import AttrDict

    options = AttrDict()
    options.identical = False
    options.ignoreCase = True
    options.almostEqual = True
    options.maxRows = 5
    options.places = 8

    nefWriter = CcpnNefIo.CcpnNefWriter(project)
    localNefDict = nefWriter.exportProject(expandSelection=True, pidList=None)
    result = NefModule.compareDataBlocks(_loader._nefDict, localNefDict, options)
    # NefModule.printCompareList(result, 'LOADED', 'local', options)


if __name__ == '__main__':
    main()
