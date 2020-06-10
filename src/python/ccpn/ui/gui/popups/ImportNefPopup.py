"""
Module Documentation here
"""
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
__dateModified__ = "$dateModified: 2020-06-11 12:10:38 +0100 (Thu, June 11, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-05-04 17:15:05 +0000 (Mon, May 04, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
from functools import partial
from collections import OrderedDict as OD
from ccpn.util.Common import PrintFormatter
from ccpn.util.OrderedSet import OrderedSet
from ccpn.ui.gui.widgets.FileDialog import FileDialog, USERNEFPATH
from ccpn.ui.gui.widgets.Spacer import Spacer
from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import ImportTreeCheckBoxes
from ccpn.ui.gui.popups.ExportDialog import ExportDialog
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.GuiTable import GuiTable
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.Label import Label, ActiveLabel
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.nef import StarIo
from ccpn.core.lib import CcpnNefIo
from ccpn.core.lib.ContextManagers import undoBlock, notificationEchoBlocking, catchExceptions
from ccpn.core.Project import Project
from ccpn.util.nef import NefImporter as Nef
from ccpn.util.AttrDict import AttrDict
from ccpn.ui.gui.widgets.Frame import ScrollableFrame
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.Base import SignalBlocking
from ccpn.ui.gui.guiSettings import getColours, BORDERNOFOCUS
from ccpn.ui.gui.widgets.MoreLessFrame import MoreLessFrame
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.TextEditor import TextEditor


INVALIDTEXTROWSELECTCOLOUR = QtGui.QColor('crimson')
INVALIDTEXTROWNOSELECTCOLOUR = QtGui.QColor('darkorange')
INVALIDTABLEFILLCOLOUR = QtGui.QColor('lightpink')
INVALIDTABLEFILLSELECTCOLOUR = QtGui.QColor('salmon')

CHAINS = 'chains'
NMRCHAINS = 'nmrChains'
RESTRAINTLISTS = 'restraintLists'
CCPNTAG = 'ccpn'
SKIPPREFIXES = 'skipPrefixes'
EXPANDSELECTION = 'expandSelection'

VALIDATEDICT = '/Users/ejb66/Desktop/mmcif_nef_v1_1.dic'

PulldownListsMinimumWidth = 200
LineEditsMinimumWidth = 195
NotImplementedTipText = 'This option has not been implemented yet'
DEFAULTSPACING = (3, 3)
TABMARGINS = (1, 10, 10, 1)  # l, t, r, b
ZEROMARGINS = (0, 0, 0, 0)  # l, t, r, b
COLOURALLCOLUMNS = False


class NefDictFrame(Frame):
    """
    Class to handle a nef dictionary editor
    """
    EDITMODE = True
    handleSaveFrames = {}
    _setBadSaveFrames = {}
    DEFAULTMARGINS = (8, 8, 8, 8)  # l, t, r, b

    def __init__(self, parent=None, mainWindow=None, nefObject=None, enableCheckboxes=False,
                 showBorder=True, borderColour=None, _splitterMargins=DEFAULTMARGINS, **kwds):
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
        else:
            self.mainWindow = None
            self.application = None
            self.project = None
            self._nefReader = None
            self._nefWriter = None
        self._primaryProject = True
        self.showBorder = showBorder
        self._borderColour = borderColour or QtGui.QColor(getColours()[BORDERNOFOCUS])
        self._enableCheckboxes = enableCheckboxes

        # set the nef object - nefLoader/nefDict
        self._initialiseNefLoader(nefObject, _ignoreError=True)

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

    def _initialiseProject(self, mainWindow, application, project):
        """Intitialise the project setting - ONLY REQUIRED FOR TESTING when mainWindow doesn't exist
        """
        # set the project
        self.mainWindow = mainWindow
        self.application = application
        self.project = project
        if mainWindow is None:
            self.mainWindow = AttrDict()

        # set the new values for application and project
        self.mainWindow.application = application
        self.mainWindow.project = project

        # initialise the base structure from the project
        self.nefTreeView._populateTreeView(project)

        self._nefReader = CcpnNefIo.CcpnNefReader(self.application)
        self._nefWriter = CcpnNefIo.CcpnNefWriter(self.project)

    def _initialiseNefLoader(self, nefObject=None, _ignoreError=False):
        if not (nefObject or _ignoreError):
            raise TypeError('nefObject must be defined')

        self._nefLoader = None
        self._nefDict = None
        if isinstance(nefObject, Nef.NefImporter):
            self._nefLoader = nefObject
            self._nefDict = nefObject._nefDict
            self._primaryProject = False
        elif isinstance(nefObject, Project):
            self.project = nefObject
            self._nefLoader = Nef.NefImporter(errorLogging=Nef.el.NEF_STANDARD, hidePrefix=True)
            self._nefWriter = CcpnNefIo.CcpnNefWriter(self.project)
            self._nefDict = self._nefLoader._nefDict = self._nefWriter.exportProject(expandSelection=True, pidList=None)

    def _setCallbacks(self):
        """Set the mouse callback for the treeView
        """
        self.nefTreeView.itemClicked.connect(self._nefTreeClickedCallback)

    def _setWidgets(self):
        """Setup the unpopulated widgets for the frame
        """
        self._paneSplitter = Splitter(self, setLayout=True, horizontal=True)

        # set the top frames
        self._treeFrame = Frame(self, setLayout=True, showBorder=False, grid=(0, 0))
        self._infoFrame = Frame(self, setLayout=True, showBorder=False, grid=(0, 0))

        # must be added this way to fill the frame
        self.getLayout().addWidget(self._paneSplitter, 0, 0)
        self._paneSplitter.addWidget(self._treeFrame)
        self._paneSplitter.addWidget(self._infoFrame)
        self._paneSplitter.setChildrenCollapsible(False)
        self._paneSplitter.setStretchFactor(0, 1)
        self._paneSplitter.setStretchFactor(1, 2)
        # self._paneSplitter.setStyleSheet("QSplitter::handle { background-color: gray }")
        self._paneSplitter.setSizes([10000, 15000])

        # treeFrame (left frame)
        self._treeOptionsFrame = Frame(self._treeFrame, setLayout=True, showBorder=False, grid=(0, 0))
        self.buttonCCPN = CheckBox(self._treeOptionsFrame, checked=True,
                                   text='include CCPN tags',
                                   grid=(0, 0), hAlign='l')
        self.buttonExpand = CheckBox(self._treeOptionsFrame, checked=False,
                                     text='expand selection',
                                     grid=(1, 0), hAlign='l')
        self.nefTreeView = ImportTreeCheckBoxes(self._treeFrame, project=self.project, grid=(1, 0),
                                                includeProject=True, enableCheckboxes=self._enableCheckboxes,
                                                multiSelect=True)

        # info frame (right frame)
        self.tablesFrame = Frame(self._infoFrame, setLayout=True, showBorder=False, grid=(0, 0))
        self._frameOptionsNested = Frame(self._infoFrame, setLayout=True, showBorder=False, grid=(1, 0))
        self.frameOptionsFrame = Frame(self._frameOptionsNested, setLayout=True, showBorder=False, grid=(1, 0))
        self.fileFrame = Frame(self._infoFrame, setLayout=True, showBorder=False, grid=(2, 0))
        _frame = MoreLessFrame(self._infoFrame, name='Filter Log', showMore=False, grid=(3, 0), gridSpan=(1, 1))

        _row = 0
        self.wordWrapData = CheckBoxCompoundWidget(
                _frame.contentsFrame,
                grid=(_row, 0), hAlign='left',
                #minimumWidths=(colwidth, 0),
                fixedWidths=(None, 30),
                orientation='left',
                labelText='Wordwrap:',
                checked=False,
                callback=lambda val: self.logData.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth if val else QtWidgets.QTextEdit.NoWrap)
                #self._toggleWordWrap,
                )
        _row += 1
        self.logData = TextEditor(_frame.contentsFrame, grid=(_row, 0), gridSpan=(1, 3))
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
            with self.blockWidgetSignals(projectBlanking=False):
                if self._nefLoader:
                    # populate from the _nefLoader
                    self.nefTreeView.fillTreeView(self._nefLoader._nefDict)
                    self.nefTreeView.expandAll()
                elif self._nefDict:
                    # populate from dict
                    self.nefTreeView.fillTreeView(self._nefLoader._nefDict)
                    self.nefTreeView.expandAll()

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
                sectionColour = self.nefTreeView._foregroundColour

                # iterate through the items in the group, e.g., peakList/integralList/sample
                _sectionError = False
                child_count = pluralItem.childCount()
                for i in range(child_count):
                    childItem = pluralItem.child(i)
                    childColour = self.nefTreeView._foregroundColour

                    # get the saveFrame associated with this item
                    saveFrame = childItem.data(1, 0)

                    # NOTE:ED - need a final check on this
                    _errorName = getattr(saveFrame, '_rowErrors', None) and saveFrame._rowErrors.get(saveFrame['sf_category'])
                    if _errorName and childItem.data(0, 0) in _errorName:  # itemName
                        _sectionError = True

                    loops = self._nefReader._getLoops(self.project, saveFrame)
                    _rowError = False
                    for loop in loops:

                        # get the group name add fetch the correct mapping
                        mapping = self.nefTreeView.nefProjectToSaveFramesMapping.get(childItem.parent().data(0, 0))
                        if mapping and loop.name not in mapping:
                            continue

                        # NOTE:ED - if there are no loops then _sectionError is never set
                        if hasattr(saveFrame, '_rowErrors') and \
                                loop.name in saveFrame._rowErrors and \
                                saveFrame._rowErrors[loop.name]:
                            # _rowError = True
                            _sectionError = True
                            # _projectError = True

                    primaryHandler = self.nefTreeView.nefProjectToHandlerMapping.get(childItem.parent().data(0, 0)) or saveFrame.get('sf_category')
                    if primaryHandler:
                        if primaryHandler in self._setBadSaveFrames:
                            handler = self._setBadSaveFrames[primaryHandler]
                            if handler is not None:
                                _rowError = handler(self, saveFrame, childItem)

                    if _rowError:
                        childColour = INVALIDTEXTROWSELECTCOLOUR if childItem.checkState(0) else INVALIDTEXTROWNOSELECTCOLOUR
                    self.nefTreeView.setForegroundForRow(childItem, childColour)

                if _sectionError:
                    sectionColour = INVALIDTEXTROWSELECTCOLOUR if pluralItem.checkState(0) else INVALIDTEXTROWNOSELECTCOLOUR
                    if pluralItem.checkState(0):
                        _projectError = True
                self.nefTreeView.setForegroundForRow(pluralItem, sectionColour)

        if _projectError:
            projectColour = INVALIDTEXTROWSELECTCOLOUR if projectItem.checkState(0) else INVALIDTEXTROWNOSELECTCOLOUR
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
            # colour rows by extra colour
            chainErrors = _errors.get('nef_sequence_' + itemName)
            if chainErrors:
                table = self._nefTables.get('nef_sequence')
                for rowIndex in chainErrors:
                    table.setRowBackgroundColour(rowIndex, INVALIDTABLEFILLSELECTCOLOUR)

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
            for tableName in tables:
                # colour rows by extra colour
                chainErrors = _errors.get('_'.join([tableName, itemName]))
                if chainErrors:
                    table = self._nefTables.get(tableName)
                    for rowIndex in chainErrors:
                        table.setRowBackgroundColour(rowIndex, INVALIDTABLEFILLSELECTCOLOUR)

    def table_lists(self, saveFrame, item, listName, postFix='list'):
        itemName = item.data(0, 0)
        primaryCode = '_'.join([listName, postFix])
        _content = getattr(saveFrame, '_content', None)
        _errors = getattr(saveFrame, '_rowErrors', {})

        numPrimary = _content.get(primaryCode)
        if numPrimary and len(numPrimary) <= 1:
            return

        if _errors:
            # colour rows by extra colour
            chainErrors = _errors.get('_'.join([listName, itemName]))
            if chainErrors:
                table = self._nefTables.get(listName)
                for rowIndex in chainErrors:
                    table.setRowBackgroundColour(rowIndex, INVALIDTABLEFILLSELECTCOLOUR)
            chainErrors = _errors.get('_'.join([listName, postFix, itemName]))
            if chainErrors:
                table = self._nefTables.get('_'.join([listName, postFix]))
                for rowIndex in chainErrors:
                    table.setRowBackgroundColour(rowIndex, INVALIDTABLEFILLSELECTCOLOUR)

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
            # colour rows by extra colour
            chainErrors = _errors.get('_'.join([listItemName, itemName]))
            if chainErrors:
                table = self._nefTables.get(listItemName)
                for rowIndex in chainErrors:
                    table.setRowBackgroundColour(rowIndex, INVALIDTABLEFILLSELECTCOLOUR)
            chainErrors = _errors.get('_'.join([listName, 'list', itemName]))
            if chainErrors:
                table = self._nefTables.get('_'.join([listName, 'list']))
                for rowIndex in chainErrors:
                    table.setRowBackgroundColour(rowIndex, INVALIDTABLEFILLSELECTCOLOUR)

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
            # colour rows by extra colour
            chainErrors = _errors.get('_'.join([listItemName, itemName]))
            if chainErrors:
                table = self._nefTables.get(listItemName)
                for rowIndex in chainErrors:
                    table.setRowBackgroundColour(rowIndex, INVALIDTABLEFILLSELECTCOLOUR)
            chainErrors = _errors.get('_'.join([listName, 'peaks', itemName]))
            if chainErrors:
                table = self._nefTables.get('_'.join([listName, 'peaks']))
                for rowIndex in chainErrors:
                    table.setRowBackgroundColour(rowIndex, INVALIDTABLEFILLSELECTCOLOUR)

    def table_ccpn_notes(self, saveFrame, item):
        itemName = item.data(0, 0)
        primaryCode = 'ccpn_notes'
        _content = getattr(saveFrame, '_content', None)
        _errors = getattr(saveFrame, '_rowErrors', {})

        numPrimary = _content.get(primaryCode)
        if numPrimary and len(numPrimary) <= 1:
            return

        if _errors:
            # colour rows by extra colour
            chainErrors = _errors.get('ccpn_note_' + itemName)
            if chainErrors:
                table = self._nefTables.get('ccpn_note')
                for rowIndex in chainErrors:
                    table.setRowBackgroundColour(rowIndex, INVALIDTABLEFILLSELECTCOLOUR)

    def _set_bad_saveframe(self, saveFrame, item, prefix=None, mappingCode=None,
                           errorCode=None, tableColourFunc=None):
        # check if the current saveFrame exists; i.e., category exists as row = [0]
        mappingCode = mappingCode or ''
        errorCode = errorCode or ''

        mapping = self.nefTreeView.nefToTreeViewMapping.get(mappingCode)
        itemName = item.data(0, 0)

        _content = getattr(saveFrame, '_content', None)
        _errors = getattr(saveFrame, '_rowErrors', {})
        _bad = False
        if _content and mapping:
            if errorCode in _errors and itemName in _errors[errorCode]:
                _bad = True

        return _bad

    # def handle_nef_chemical_shift_list(self, saveFrame, item):
    # def handle_nef_molecular_system(self, saveFrame, item):
    def handle_treeView_selection(self, saveFrame, item, prefix=None, mappingCode=None,
                                  errorCode=None, tableColourFunc=None):
        # check if the current saveFrame exists; i.e., category exists as row = [0]
        cat = saveFrame.get('sf_category')
        prefix = prefix or ''
        mappingCode = mappingCode or ''
        errorCode = errorCode or ''

        mapping = self.nefTreeView.nefToTreeViewMapping.get(mappingCode)
        itemName = item.data(0, 0)

        _content = getattr(saveFrame, '_content', None)
        _errors = getattr(saveFrame, '_rowErrors', {})
        if _content and mapping:
            plural, singular = mapping

            row = 0
            # editFrame = Frame(self.frameOptionsFrame, setLayout=True, grid=(row, 0), showBorder=False)
            saveFrameLabel = Label(self.frameOptionsFrame, text=singular, grid=(row, 0))
            saveFrameData = LineEdit(self.frameOptionsFrame, text=str(itemName), grid=(row, 1))
            # editFrame.setFixedHeight(24)

            if errorCode in _errors and itemName in _errors[errorCode]:
                palette = saveFrameData.palette()
                palette.setColor(QtGui.QPalette.Base, INVALIDTABLEFILLCOLOUR)
                saveFrameData.setPalette(palette)

            texts = ('Rename', 'Auto Rename')
            callbacks = (partial(self._rename, item=item, parentName=plural, lineEdit=saveFrameData, saveFrame=saveFrame),
                         partial(self._rename, item=item, parentName=plural, lineEdit=saveFrameData, saveFrame=saveFrame, autoRename=True))
            tipTexts = ('Rename', 'Automatically rename to the next available\n - dependent on saveframe type')
            self.buttonList = ButtonList(self.frameOptionsFrame, texts=texts, tipTexts=tipTexts, callbacks=callbacks,
                                         grid=(row, 2), gridSpan=(1, 1), direction='v')
            row += 1

            if tableColourFunc is not None:
                tableColourFunc(self, saveFrame, item)

        self.logData.clear()
        pretty = PrintFormatter()
        self.logData.append(('CONTENTS DICT'))
        self.logData.append(pretty(_content))
        self.logData.append(('ERROR DICT'))
        self.logData.append(pretty(_errors))

    def _rename(self, item=None, parentName=None, lineEdit=None, saveFrame=None, autoRename=False):
        """Handle clicking a rename button
        """
        if not (lineEdit and item):
            return

        itemName = item.data(0, 0)
        cat = saveFrame.get('sf_category')

        # find the primary handler class for the clicked item, .i.e. chains/peakLists etc.
        primaryHandler = self.nefTreeView.nefProjectToHandlerMapping.get(item.parent().data(0, 0)) or saveFrame.get('sf_category')
        func = self._nefReader.renames.get(primaryHandler)
        if func is not None:

            newName = lineEdit.get()
            try:
                # call the correct rename function based on the item clicked
                newName = func(self._nefReader, self.project, self._nefDict, saveFrame,
                               itemName=itemName, newName=newName if not autoRename else None)
            except Exception as es:
                showWarning('Rename', str(es))
            else:

                # everything okay - rebuild all for now, could make selective later
                self.nefTreeView._populateTreeView(self.project)
                self._fillPopup(self._nefDict)

                # _parent = self.nefTreeView._contentParent(self.project, saveFrame, cat)
                _parent = self.nefTreeView.findSection(parentName)
                if _parent:
                    newItem = self.nefTreeView.findSection(newName, _parent)
                    if newItem:
                        self._nefTreeClickedCallback(newItem, 0)

    handleSaveFrames['nef_sequence'] = partial(handle_treeView_selection,
                                               prefix='nef_sequence_',
                                               mappingCode='nef_sequence_chain_code',
                                               errorCode='nef_sequence_chain_code',
                                               tableColourFunc=table_nef_molecular_system)

    handleSaveFrames['nef_chemical_shift_list'] = partial(handle_treeView_selection,
                                                          prefix='nef_chemical_shift_',
                                                          mappingCode='nef_chemical_shift_list',
                                                          errorCode='nef_chemical_shift_list',
                                                          tableColourFunc=None)

    handleSaveFrames['nef_distance_restraint_list'] = partial(handle_treeView_selection,
                                                              prefix='nef_distance_restraint_',
                                                              mappingCode='nef_distance_restraint_list',
                                                              errorCode='nef_distance_restraint_list',
                                                              tableColourFunc=None)

    handleSaveFrames['nef_dihedral_restraint_list'] = partial(handle_treeView_selection,
                                                              prefix='nef_dihedral_restraint_',
                                                              mappingCode='nef_dihedral_restraint_list',
                                                              errorCode='nef_dihedral_restraint_list',
                                                              tableColourFunc=None)

    handleSaveFrames['nef_rdc_restraint_list'] = partial(handle_treeView_selection,
                                                         prefix='nef_rdc_restraint_',
                                                         mappingCode='nef_rdc_restraint_list',
                                                         errorCode='nef_rdc_restraint_list',
                                                         tableColourFunc=None)

    handleSaveFrames['ccpn_restraint_list'] = partial(handle_treeView_selection,
                                                      prefix='ccpn_restraint_',
                                                      mappingCode='ccpn_restraint_list',
                                                      errorCode='ccpn_restraint_list',
                                                      tableColourFunc=None)

    handleSaveFrames['ccpn_sample'] = partial(handle_treeView_selection,
                                              prefix='ccpn_sample_component_',
                                              mappingCode='ccpn_sample',
                                              errorCode='ccpn_sample',
                                              tableColourFunc=None)

    handleSaveFrames['ccpn_complex'] = partial(handle_treeView_selection,
                                               prefix='ccpn_complex_chain_',
                                               mappingCode='ccpn_complex',
                                               errorCode='ccpn_complex',
                                               tableColourFunc=None)

    handleSaveFrames['ccpn_spectrum_group'] = partial(handle_treeView_selection,
                                                      prefix='ccpn_group_spectrum_',
                                                      mappingCode='ccpn_spectrum_group',
                                                      errorCode='ccpn_spectrum_group',
                                                      tableColourFunc=None)

    handleSaveFrames['ccpn_note'] = partial(handle_treeView_selection,
                                            prefix='ccpn_note_',
                                            mappingCode='ccpn_notes',
                                            errorCode='ccpn_notes',
                                            tableColourFunc=table_ccpn_notes)

    handleSaveFrames['ccpn_peak_list'] = partial(handle_treeView_selection,
                                                 prefix='nef_peak_',
                                                 mappingCode='nef_peak',
                                                 errorCode='ccpn_peak_list_serial',
                                                 tableColourFunc=table_peak_lists)

    handleSaveFrames['ccpn_integral_list'] = partial(handle_treeView_selection,
                                                     prefix='ccpn_integral_',
                                                     mappingCode='ccpn_integral_list',
                                                     errorCode='ccpn_integral_list_serial',
                                                     tableColourFunc=partial(table_lists, listName='ccpn_integral'))

    handleSaveFrames['ccpn_multiplet_list'] = partial(handle_treeView_selection,
                                                      prefix='ccpn_multiplet_',
                                                      mappingCode='ccpn_multiplet_list',
                                                      errorCode='ccpn_multiplet_list_serial',
                                                      tableColourFunc=partial(table_lists, listName='ccpn_multiplet'))

    handleSaveFrames['ccpn_peak_cluster_list'] = partial(handle_treeView_selection,
                                                         prefix='ccpn_peak_cluster_',
                                                         mappingCode='ccpn_peak_cluster',
                                                         errorCode='ccpn_peak_cluster_serial',
                                                         tableColourFunc=table_peak_clusters)

    handleSaveFrames['nmr_chain'] = partial(handle_treeView_selection,
                                            prefix='nmr_chain_',
                                            mappingCode='nmr_chain',
                                            errorCode='nmr_chain_serial',
                                            tableColourFunc=table_ccpn_assignment)

    handleSaveFrames['ccpn_substance'] = partial(handle_treeView_selection,
                                                 prefix='ccpn_substance_synonym_',
                                                 mappingCode='ccpn_substance',
                                                 errorCode='ccpn_substance',
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

    def _nefTreeClickedCallback(self, item, column):
        """Handle clicking on an item in the nef tree
        """
        self._nefTables = {}
        for widg in self._nefWidgets:
            self._removeWidget(widg, removeTopWidget=True)
        self._nefWidgets = []
        self._removeWidget(self.frameOptionsFrame, removeTopWidget=False)

        # # clicking the checkbox also comes here
        # self._colourTreeView()
        #
        saveFrame = item.data(1, 0)
        if saveFrame:
            if hasattr(saveFrame, '_content'):

                # add a table from the saveframe attributes
                loop = StarIo.NmrLoop(name=saveFrame.name, columns=('attribute', 'value'))
                for k, v in saveFrame.items():
                    if not (k.startswith('_') or isinstance(v, StarIo.NmrLoop)):
                        loop.newRow((k, v))
                _name, _data = saveFrame.name, loop.data
                frame, table = self._addTableToFrame(_data, _name)
                self._tableSplitter.addWidget(frame)
                self._nefWidgets.append(frame)

                # get the group name add fetch the correct mapping
                mapping = self.nefTreeView.nefProjectToSaveFramesMapping.get(item.parent().data(0, 0))
                primaryHandler = self.nefTreeView.nefProjectToHandlerMapping.get(item.parent().data(0, 0)) or saveFrame.get('sf_category')

                # add tables from the loops in the saveframe
                loops = self._nefReader._getLoops(self.project, saveFrame)
                for loop in loops:

                    if mapping and loop.name not in mapping:
                        continue

                    _name, _data = loop.name, loop.data
                    # if self.nefTreeView.nefProjectToSaveFramesMapping
                    # add new tables
                    frame, table = self._addTableToFrame(_data, _name)

                    if loop.name in saveFrame._content and \
                            hasattr(saveFrame, '_rowErrors') and \
                            loop.name in saveFrame._rowErrors:
                        badRows = list(saveFrame._rowErrors[loop.name])

                        for rowIndex in badRows:
                            table.setRowBackgroundColour(rowIndex, INVALIDTABLEFILLCOLOUR)

                    self._tableSplitter.addWidget(frame)
                    self._nefWidgets.append(frame)

                if primaryHandler:
                    handler = self.handleSaveFrames.get(primaryHandler)
                    if handler is not None:
                        handler(self, saveFrame, item)

        # clicking the checkbox also comes here - above loop may set item._badName
        self._colourTreeView()

    def _addTableToFrame(self, _data, _name):
        """Add a new gui table into a moreLess frame to hold a nef loop
        """
        frame = MoreLessFrame(self, name=_name, showMore=True, grid=(0, 0))
        table = GuiTable(frame.contentsFrame, grid=(0, 0), gridSpan=(1, 1), _applyPostSort=False, multiSelect=True)
        table._hiddenColumns = []
        table.setData(_data)
        table.resizeColumnsToContents()
        self._nefTables[_name] = table
        return frame, table

    def _fillPopup(self, nefObject=None):
        """Initialise the project setting - only required for testing
        Assumes that the nef loaders may not be initialised if called from outside of Analysis
        """
        if not self._nefLoader:
            self._nefLoader = Nef.NefImporter(errorLogging=Nef.el.NEF_STANDARD, hidePrefix=True)
            if not self.project:
                raise TypeError('Project is not defined')
            self._nefWriter = CcpnNefIo.CcpnNefWriter(self.project)
            self._nefDict = self._nefLoader._nefDict = self._nefWriter.exportProject(expandSelection=True, pidList=None)

        # attach the import/verify/content methods
        self._nefLoader._attachVerifier(self._nefReader.verifyProject)
        self._nefLoader._attachReader(self._nefReader.importExistingProject)
        self._nefLoader._attachContent(self._nefReader.contentNef)
        self._nefLoader._attachClear(self._nefReader.clearSaveFrames)
        self._nefLoader._clearNef(self.project, self._nefDict)
        self._nefLoader._contentNef(self.project, self._nefDict, selection=None)
        if not self._primaryProject:
            warnings, errors = self._nefLoader._verifyNef(self.project, self._nefDict, selection=None)

        try:
            self.valid = self._nefLoader.isValid
        except Exception as es:
            getLogger().warning(str(es))

        self._populate()


class ImportNefPopup(CcpnDialogMainWidget):
    """
    Nef management class
    """
    USESCROLLWIDGET = True
    FIXEDWIDTH = False
    FIXEDHEIGHT = False
    DEFAULTMARGINS = (5, 5, 5, 5)

    def __init__(self, parent=None, mainWindow=None, title='Import Nef', size=(1000, 700),
                 nefObjects=(), **kwds):
        """
        Initialise the main form

        :param parent: calling widget
        :param mainWindow: gui mainWindow class for the application
        :param title: window title
        :param size: initial size of the window
        :param nefObjects: a tuple of tuples of the form ((nefImporter | project, checkboxes visible),)
        :param kwds: additional parameters to pass to the window
        """
        super().__init__(parent, setLayout=True, windowTitle=title, size=size, **kwds)

        if mainWindow:
            self.mainWindow = mainWindow
            self.application = mainWindow.application
            self.project = mainWindow.project
        else:
            self.mainWindow = None
            self.application = None
            self.project = None
        self._size = size

        # create a list of nef dictionary objects
        self.setNefObjects(nefObjects)

        # set up the widgets
        self.setWidgets()

        # populate the widgets
        self._populate()

        # enable the buttons
        self.setOkButton(callback=self._okClicked, tipText='Okay')
        self.setCloseButton(callback=self.reject, tipText='Close')
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)
        self.__postInit__()

    def setWidgets(self):
        """Initialise the main widgets for the form
        """
        self.paneSplitter = Splitter(self.mainWidget, setLayout=True, horizontal=True)
        self.paneSplitter.setChildrenCollapsible(False)
        self.mainWidget.getLayout().addWidget(self.paneSplitter, 0, 0)

        self._nefWindows = OD()
        for obj, enableCheckboxes in self.nefObjects:
            # add a new nefDictFrame for each of the objects in the list (project or nefImporter)
            newWindow = NefDictFrame(self, mainWindow=self.mainWindow, nefObject=obj, grid=(0, 0), showBorder=True, enableCheckboxes=enableCheckboxes)
            self._nefWindows[obj] = newWindow
            self.paneSplitter.addWidget(newWindow)

    def _populate(self):
        """Populate all frames
        """
        for nefWindow in self._nefWindows.values():
            nefWindow._populate()

    def setNefObjects(self, nefObjects):
        # create a list of nef dictionary objects here and add to splitter
        self.nefObjects = tuple(obj for obj in nefObjects if isinstance(obj, tuple)
                                and len(obj) == 2
                                and isinstance(obj[0], (Nef.NefImporter, Project))
                                and isinstance(obj[1], bool))
        if len(self.nefObjects) != len(nefObjects):
            getLogger().warning('nefObjects contains bad items {}'.format(nefObjects))

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

    def exec_(self) -> int:
        # NOTE:ED - this will do for the moment
        self.resize(*self._size)
        return super(ImportNefPopup, self).exec_()


if __name__ == '__main__':
    """Testing code for the new nef manager
    """

    # from sandbox.Geerten.Refactored.framework import Framework
    # from sandbox.Geerten.Refactored.programArguments import Arguments

    from ccpn.framework.Framework import Framework
    from ccpn.framework.Framework import Arguments


    _makeMainWindowVisible = False


    class MyProgramme(Framework):
        "My first app"
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

    TESTNEF = '/Users/ejb66/Documents/nefTestProject.nef'
    TESTNEF2 = '/Users/ejb66/Documents/nefTestProject0.nef'

    # TESTNEF = '/Users/ejb66/Documents/nefTestProject.nef'
    # TESTNEF2 = '/Users/ejb66/Documents/nefTestProject.nef'

    # TESTNEF = '/Users/ejb66/Documents/CcpNmrData/nefTestProject.nef'
    # TESTNEF2 = '/Users/ejb66/Documents/CcpNmrData/nefTestProject.nef'

    # TESTNEF = '/Users/ejb66/Desktop/Ccpn_v2_testNef_a1.nef'
    # TESTNEF2 = '/Users/ejb66/Desktop/Ccpn_v2_testNef_a1.nef'

    # VALIDATEDICT = '/Users/ejb66/PycharmProjects/Git/NEF/specification/mmcif_nef.dic'
    VALIDATEDICT = '/Users/ejb66/Desktop/mmcif_nef_v1_1.dic'
    DEFAULTNAME = 'default'

    from ccpn.util.nef import NefImporter as Nef


    # load the file and the validate dict
    _loader = Nef.NefImporter(errorLogging=Nef.el.NEF_STRICT, hidePrefix=True)
    _loader.loadFile(TESTNEF)
    _loader.loadValidateDictionary(VALIDATEDICT)

    # load the file and the validate dict
    _loader2 = Nef.NefImporter(errorLogging=Nef.el.NEF_STRICT, hidePrefix=True)
    _loader2.loadFile(TESTNEF2)
    _loader2.loadValidateDictionary(VALIDATEDICT)

    # validate
    print(_loader.name, _loader.isValid)
    print(_loader2.name, _loader2.isValid)

    # simple test print of saveframes
    names = _loader.getSaveFrameNames(returnType=Nef.NEF_RETURNALL)
    for name in names:
        print(name)
        saveFrame = _loader.getSaveFrame(name)
        print(saveFrame)

    # create a list of which saveframes to load, with a parameters dict for each
    loadDict = {'nef_molecular_system'     : {},
                'nef_nmr_spectrum_cnoesy1' : {},
                'nef_chemical_shift_list_1': {},
                }

    # need a project
    name = _loader.getName()
    project = application.newProject(name or DEFAULTNAME)

    project._wrappedData.shiftAveraging = False
    # with suspendSideBarNotifications(project=self.project):

    from ccpn.core.lib import CcpnNefIo


    nefReader = CcpnNefIo.CcpnNefReader(application)
    _loader._attachVerifier(nefReader.verifyProject)
    _loader._attachReader(nefReader.importExistingProject)
    _loader._attachContent(nefReader.contentNef)

    from ccpn.core.lib.ContextManagers import undoBlock, notificationEchoBlocking


    with notificationEchoBlocking():
        with catchExceptions(application=application, errorStringTemplate='Error loading Nef file: %s'):
            # need datablock selector here, with subset selection dependent on datablock type

            _loader._importNef(project, _loader._nefDict, selection=None)
            # warnings, errors = _loader._verifyNef(project, _loader2._nefDict, selection=None)
            # if not (warnings or errors):
            #     _loader._importNef(project, _loader2._nefDict, selection=None)
            # else:
            #     # for msg in warnings or ('','',''):
            #     #     print('  >>', msg)
            #     for msg in errors or ('', '', ''):
            #         print(msg[0])
            #
            # result = _loader._contentNef(project, _loader2._nefDict, selection=None)

    nefReader.testPrint(project, _loader._nefDict, selection=None)
    nefReader.testErrors(project, _loader._nefDict, selection=None)

    from ccpn.ui.gui.popups.ImportNefPopup import ImportNefPopup


    app = QtWidgets.QApplication(['testApp'])
    # run the dialog
    dialog = ImportNefPopup(parent=ui.mainWindow, mainWindow=ui.mainWindow,
                            # nefObjects=(_loader,))
                            nefObjects=((project, False),
                                        (_loader2, True),))

    dialog._initialiseProject(ui.mainWindow, application, project)
    dialog.fillPopup()

    # NOTE:ED - add routines here to set up the mapping between the different nef file loaded
    dialog.exec_()

    import ccpn.util.nef.nef as Nef


    # NOTE:ED - by default pidList=None selects everything in the project
    # from ccpn.core.Chain import Chain
    # from ccpn.core.ChemicalShiftList import ChemicalShiftList
    # from ccpn.core.RestraintList import RestraintList
    # from ccpn.core.PeakList import PeakList
    # from ccpn.core.IntegralList import IntegralList
    # from ccpn.core.MultipletList import MultipletList
    # from ccpn.core.PeakCluster import PeakCluster
    # from ccpn.core.Sample import Sample
    # from ccpn.core.Substance import Substance
    # from ccpn.core.NmrChain import NmrChain
    # from ccpn.core.DataSet import DataSet
    # from ccpn.core.Complex import Complex
    # from ccpn.core.SpectrumGroup import SpectrumGroup
    # from ccpn.core.Note import Note
    #
    # # set the items in the project that can be exported
    # checkList = [
    #     Chain._pluralLinkName,
    #     ChemicalShiftList._pluralLinkName,
    #     RestraintList._pluralLinkName,
    #     PeakList._pluralLinkName,
    #     IntegralList._pluralLinkName,
    #     MultipletList._pluralLinkName,
    #     Sample._pluralLinkName,
    #     Substance._pluralLinkName,
    #     NmrChain._pluralLinkName,
    #     DataSet._pluralLinkName,
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

    nefWriter = CcpnNefIo.CcpnNefWriter(project)
    localNefDict = nefWriter.exportProject(expandSelection=True, pidList=None)

    from ccpn.util.AttrDict import AttrDict


    options = AttrDict()
    options.identical = False
    options.ignoreCase = True
    options.almostEqual = True
    options.maxRows = 5
    options.places = 8

    # sys.setrecursionlimit(10000)
    result = Nef.compareDataBlocks(_loader._nefDict, localNefDict, options)
    Nef.printCompareList(result, 'LOADED', 'local', options)

    # # NOTE:ED - extract information from the saveframes as sets and dicts
    # frame = _loader.getSaveFrame('ccpn_assignment')
    # if frame is not None:
    #     nmrChains, nmrResidues, nmrAtoms = nefReader.content_ccpn_assignment(project, frame._nefFrame)
    #     print('nmrChains: ')
    #     for val in nmrChains:
    #         print(val)
    #     print('nmrResidues: ')
    #     for val in list(nmrResidues)[:4]:
    #         print(val)
    #     print('nmrAtoms: ')
    #     for val in list(nmrAtoms)[:4]:
    #         print(val)
    #
    # frame = _loader.getSaveFrame('nef_molecular_system')
    # if frame is not None:
    #     data = nefReader.content_nef_molecular_system(project, frame._nefFrame)
    #     chains, residues = data['nef_sequence']
    #     print('chains: ')
    #     for val in chains:
    #         print(val)
    #     print('residues: ')
    #     for val in list(residues)[:4]:
    #         print(val)

    # set up a test dict
    testDict1 = {
        "Boolean1"  : True,
        "Boolean2"  : True,
        "DictOuter" : {
            "String1"    : 'This is a string',
            "ListSet"    : [[0, {1, 2, 3, 4, 5.00, 'More strings'}],
                            [0, 1000000],
                            ['Another string', 0]],
            "nestedLists": [[0, 0],
                            [0, 1 + 2j],
                            [0, (1, 2, 3, 4, 5, 6), {
                                "nestedListsInner": [[0, 0],
                                                     [0, 1 + 2.00000001j],
                                                     [0, (1, 2, 3, 4, 5, 6)]],
                                "ListSetInner"    : [[0, {1, 2, 3, 4, 5, 'more INNER strings'}],
                                                     [0, 1000000.0],
                                                     ['Another inner string', 0.0]],
                                "String1Inner"    : 'this is a inner string',
                                }
                             ]]
            },
        "nestedDict": {
            "nestedDictItems": {
                "floatItem": 1.23
                }
            }
        }

    testDict2 = {
        "Boolean2"  : True,
        "DictOuter" : {
            "ListSet"    : [[0, {1, 2, 3, 4, 5.00000000001, 'more strings'}],
                            [0, 1000000.0],
                            ['Another string', 0.0]],
            "String1"    : 'this is a string',
            "nestedLists": [[0, 0],
                            [0, 1 + 2.00000001j],
                            [0, (1, 2, 3, 4, 5, 6), OD((
                                ("ListSetInner", [[0, OrderedSet([1, 2, 3, 4, 5.00000001, 'more inner strings'])],
                                                  [0, 1000000.0],
                                                  {'Another inner string', 0.0}]),
                                ("String1Inner", 'this is a inner string'),
                                ("nestedListsInner", [[0, 0],
                                                      [0, 1 + 2.00000001j],
                                                      [0, (1, 2, 3, 4, 5, 6)]])
                                ))
                             ]]
            },
        "nestedDict": {
            "nestedDictItems": {
                "floatItem": 1.23000001
                }
            },
        "Boolean1"  : True,
        }

    options.identical = False
    options.ignoreCase = True
    options.almostEqual = True
    options.maxRows = 5
    options.places = 8
    print(Nef._compareObjects(testDict1, testDict2, options))
    print('{} {}'.format(testDict1, testDict2))

    import re


    pos = re.search('[<>]', str(testDict2), re.MULTILINE)
    if pos:
        print("Error: data cannot contain xml tags '{}' at pos {}".format(pos.group(), pos.span()))


    # class PythonObjectEncoder(json.JSONEncoder):
    #     """
    #     Class to allow the serialisation of sets/OrderedSets/complex/OrderedDicts
    #     """
    #
    #     def default(self, obj):
    #         """Default method for encoding to json
    #         """
    #         from base64 import b64encode
    #         import pickle
    #
    #         if isinstance(obj, OrderedSet):
    #             return {"__orderedSet": list(obj)}
    #         # elif isinstance(obj, OD):
    #         #     return {"__orderedDict": [(k, val) for k, val in obj.items()]}
    #         elif isinstance(obj, set):
    #             return {"__set": list(obj)}
    #         elif isinstance(obj, complex):
    #             return {"__complex": str(obj)}
    #         elif isinstance(obj, (list, dict, str, int, float, bool, type(None))):
    #             return super().default(obj)
    #         return {'__python_object': b64encode(pickle.dumps(obj)).decode('utf-8')}
    #
    #     @staticmethod
    #     def as_python_object(dct):
    #         """Method to decode contents of Json files with sets/OrderedSets/complex/OrderedDicts
    #         In here so that I don't lose it :)
    #
    #         # NOTE:ED - keep this is it may be the reverse of Formatter class above
    #
    #         """
    #         from base64 import b64decode
    #         import pickle
    #
    #         if '__set' in dct:
    #             return set(dct['__set'])
    #         elif '__orderedSet' in dct:
    #             return OrderedSet(dct['__orderedSet'])
    #         elif '__complex' in dct:
    #             return complex(dct['__complex'])
    #         elif '__orderedDict' in dct:
    #             return OD(dct['__orderedDict'])
    #         elif '__python_object' in dct:
    #             return pickle.loads(b64decode(dct['__python_object'].encode('utf-8')))
    #         return dct
    #
    # dd = json.dumps(OD([('help', 12.0)]), indent=4, cls=PythonObjectEncoder)
    # dd = json.dumps(testDict2, indent=4, cls=PythonObjectEncoder)
    # # print(dd)
    # recover = json.loads(dd, object_hook=PythonObjectEncoder.as_python_object)
    # print(recover)

    pretty = PrintFormatter()
    print(pretty(testDict2))
