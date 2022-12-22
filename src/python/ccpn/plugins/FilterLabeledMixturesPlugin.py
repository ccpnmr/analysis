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
__dateModified__ = "$dateModified: 2022-12-22 18:51:31 +0000 (Thu, December 22, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-11-28 10:28:42 +0000 (Tue, Nov 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from dataclasses import dataclass
from PyQt5 import QtCore, QtGui, QtWidgets
from xml.etree import ElementTree
from ccpn.core.lib.ContextManagers import progressHandler, busyHandler
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Frame import ScrollableFrame
from ccpn.ui.gui.modules.PluginModule import PluginModule
from ccpn.ui.gui.widgets.FileDialog import DataFileDialog
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.widgets.MoreLessFrame import MoreLessFrame
from ccpn.ui.gui.lib.GuiPath import PathEdit
from ccpn.ui.gui.guiSettings import BORDERNOFOCUS_COLOUR
from ccpn.framework.lib.Plugin import Plugin
from ccpn.util.Path import aPath
from ccpn.util.SafeFilename import getSafeFilename


LineEditsMinimumWidth = 195
DEFAULTSPACING = 3
DEFAULTMARGINS = (14, 14, 14, 14)

# Set some tooltip texts
RUNBUTTON = 'Run'
help = {RUNBUTTON: 'Run the plugin on the specified project', }

# list of elements to remove from file
REMOVETAGLIST = ['LMOL.LabeledMixture.name',
                 'LMOL.LabeledMolecule.labeledMixtures',
                 'LMOL.LabeledMolecule.molLabels',
                 'NMR.Experiment.labeledMixtures',
                 'LMOL.exo-LabeledMixture',
                 ]


# PROJECTPATH = 'projectPath'
# PROJECTFILES = 'projectFiles'
# INVALIDFILES = 'invalidFiles'
# REMOVETAGS = 'removeTags'


#=========================================================================================
# Plugin Gui class
#=========================================================================================

@dataclass
class PluginInfo():
    # small class to hold parameter-set
    projectPath = None
    projectFiles = []
    invalidFiles = []
    removeTags = REMOVETAGLIST


class FilterLabeledMixturesGuiPlugin(PluginModule):
    className = 'FilterLabeledMixtures'

    def __init__(self, mainWindow=None, plugin=None, application=None, **kwds):
        super().__init__(mainWindow=mainWindow, plugin=plugin, application=application)

        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.preferences = mainWindow.application.preferences
        else:
            self.application = None
            self.project = None
            self.preferences = None

        self.obj = PluginInfo()
        self.obj.projectPath = None
        self.obj.removeTags = REMOVETAGLIST

        # set up the widgets
        sf = self._setScrollFrame()
        self._setWidgets(sf)
        self._populate()

        self.plugin._loggerCallback = self._guiLogger

    def _setScrollFrame(self):
        """Set up a scroll frame to contain widgets
        """
        # correct way to set up a scroll area
        self._scrollFrame = ScrollableFrame(parent=self.mainWidget,
                                            showBorder=False, setLayout=True,
                                            acceptDrops=True, grid=(0, 0), gridSpan=(1, 1), spacing=(5, 5))
        self._scrollAreaWidget = self._scrollFrame._scrollArea
        self._scrollAreaWidget.setStyleSheet('ScrollArea { border-right: 1px solid %s;'
                                             'border-bottom: 1px solid %s;'
                                             'background: transparent; }' % (BORDERNOFOCUS_COLOUR, BORDERNOFOCUS_COLOUR))
        self._scrollFrame.insertCornerWidget()
        self._scrollFrame.setContentsMargins(*DEFAULTMARGINS)
        self._scrollFrame.getLayout().setSpacing(DEFAULTSPACING)

        return self._scrollFrame

    def _guiLogger(self, *args):
        """Log the gui information
        """
        self.xmlFilterLogData.append(*args)

    def _setWidgets(self, parent):
        """Set up the main widgets
        """
        row = 0
        self.userWorkingPathLabel = Label(parent, "Project Path ", grid=(row, 0), )
        self.userWorkingPathData = PathEdit(parent, grid=(row, 1), vAlign='t')
        self.userWorkingPathData.setMinimumWidth(LineEditsMinimumWidth)
        self.userWorkingPathButton = Button(parent, grid=(row, 2), callback=self._getUserWorkingPath,
                                            icon='icons/directory', hPolicy='fixed')
        self.userWorkingPathData.textChanged.connect(self._setUserWorkingPath)

        row += 1
        self.validProjectOnly = CheckBoxCompoundWidget(
                parent,
                grid=(row, 0), gridSpan=(1, 2), hAlign='left',
                fixedWidths=(None, 30),
                orientation='left',
                labelText='Valid projects only',
                checked=True,
                callback=self._toggleValidProjects
                )

        row += 1
        _frame = MoreLessFrame(parent, name='Xml Files', showMore=True, grid=(row, 0), gridSpan=(1, 3))
        _row = 0
        self.xmlFileData = ListWidget(_frame.contentsFrame, grid=(_row, 0), gridSpan=(1, 3), hPolicy='minimum', vPolicy='minimum')
        self.xmlFileData.setDragEnabled(False)
        self.xmlFileData.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)

        row += 1
        _frame = MoreLessFrame(parent, name='Filter Tags', showMore=False, grid=(row, 0), gridSpan=(1, 3))
        _row = 0
        self.xmlLabel = Label(_frame.contentsFrame, "Filter Tags ", grid=(_row, 0))
        self.xmlFilterData = ListWidget(_frame.contentsFrame, grid=(_row, 1), gridSpan=(1, 2), hPolicy='minimum', vPolicy='minimum')
        self.xmlFilterData.setDragEnabled(False)
        self.xmlFilterData.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.xmlLabel.setFixedSize(self.xmlLabel.sizeHint())

        row += 1
        _frame = MoreLessFrame(parent, name='Filter Log', showMore=False, grid=(row, 0), gridSpan=(1, 3))

        _row = 0
        self.wordWrapData = CheckBoxCompoundWidget(
                _frame.contentsFrame,
                grid=(_row, 0), hAlign='left',
                fixedWidths=(None, 30),
                orientation='left',
                labelText='Wordwrap:',
                checked=False,
                callback=self._toggleWordWrap
                )

        _row += 1
        self.xmlFilterLogData = TextEditor(_frame.contentsFrame, grid=(_row, 0), gridSpan=(1, 3))
        self.xmlFilterLogData.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.xmlFilterLogData.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

        row += 1
        texts = [RUNBUTTON]
        tipTexts = [help[RUNBUTTON]]
        callbacks = [self.runGui]
        ButtonList(parent=parent, texts=texts, callbacks=callbacks, tipTexts=tipTexts, grid=(row, 0), gridSpan=(1, 3), hAlign='r')

    def runGui(self):
        """Run the non-Gui plugin
        """
        self.plugin.run(self.obj)
        self._populate()
        self._setUserWorkingPath(self.obj.projectPath)

    def _populate(self):
        """Populate the widgets
        """
        self.xmlFilterData.clear()
        self.xmlFilterData.addItems(REMOVETAGLIST)

    def _getUserWorkingPath(self):
        """Return the current working path
        """
        if os.path.exists(os.path.expanduser(self.userWorkingPathData.text())):
            currentDataPath = os.path.expanduser(self.userWorkingPathData.text())
        else:
            currentDataPath = os.path.expanduser('~')
        dialog = DataFileDialog(parent=self, directory=currentDataPath)
        dialog._show()
        directory = dialog.selectedFiles()
        if directory and len(directory) > 0:
            self.userWorkingPathData.setText(directory[0])

        self._setUserWorkingPath(self.userWorkingPathData.get())

    @staticmethod
    def _validProject(value):
        """Return True if the proejct contains the memops folder
        """
        pth = aPath(value)
        return (pth / 'memops').exists() and (pth / 'memops').is_dir()

    def _setUserWorkingPath(self, value):
        """Set the current working path
        """
        value = aPath(value)
        self.obj.projectPath = value
        if self.userWorkingPathData.validator().checkState == QtGui.QValidator.Acceptable:

            self.plugin.setProjectPath(value)
            self.plugin.setRemoveTags(REMOVETAGLIST)
            filePaths = self.plugin.getProjectFiles()

            self.xmlFileData.clear()
            self.xmlFileData.addItems([str(fp) for fp in filePaths])

            # colour the items depending on folder/checkbox state
            if self._validProject(value) or not self.validProjectOnly.isChecked():
                self._validateXmlFiles()
            else:
                self._ignoreXmlFiles()

    def _validateXmlFiles(self):
        """Colour items depending on validity check
        """
        value = self.obj.projectPath
        if not self._validProject(value) and self.validProjectOnly.isChecked():
            return

        branchFiles = self.xmlFileData.getItems()

        # simple progress-bar
        with progressHandler(maximum=len(branchFiles)) as busy:
            for cc, invalidFiles in enumerate(self.plugin.iterateXmlFiles()):
                busy.setValue(cc)

        for item in branchFiles:
            # colour depending on whether contains bad tags
            filePath = aPath(item.text())

            if filePath in invalidFiles:
                item.setForeground(QtCore.Qt.red)
            else:
                item.setForeground(QtCore.Qt.black)

    def _ignoreXmlFiles(self):
        """Colour items as grey
        """
        value = self.obj.projectPath
        if (os.path.exists(value / 'memops') and os.path.isdir(value / 'memops')):
            return

        branchFiles = self.xmlFileData.getItems()
        for item in branchFiles:
            # colour all as grey
            item.setForeground(QtCore.Qt.gray)

    def _toggleWordWrap(self, value):
        """Change the word-wrap state of the text-widget
        """
        if value:
            self.xmlFilterLogData.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        else:
            self.xmlFilterLogData.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

    def _toggleValidProjects(self, value):
        """If True, check only valid proejcts, i.e., those that contain the memops folder
        """
        self._setUserWorkingPath(self.obj.projectPath)


#=========================================================================================
# Plugin non-Gui class
#=========================================================================================

class FilterLabeledMixturesPlugin(Plugin):
    """Non-Gui class to implement functionality
    """
    PLUGINNAME = 'Filter Labeled Mixtures'
    guiModule = FilterLabeledMixturesGuiPlugin

    def __init__(self, *args, **kwds):
        """Initialise the class
        """
        super().__init__(*args, **kwds)

        # create an empty parameter-set
        self._kwds = PluginInfo()

        self._loggerCallback = None

    def _logger(self, *args):
        """Log information to the secified logger
        """
        if self._loggerCallback:
            self._loggerCallback(*args)

    def _containsTags(self, parent) -> bool:
        """Recursively check whether the tree contains bad tags
        """
        if parent.tag in (self._kwds.removeTags or []):
            return True

        for lm in list(parent):
            if self._containsTags(lm):
                return True

    def containsTags(self, filePath) -> bool:
        """Recursively check whether the tree contains bad tags
        """
        self._parser = ElementTree.XMLParser(target=ElementTree.TreeBuilder(insert_comments=True))
        tree = ElementTree.parse(filePath, self._parser)
        self._root = tree.getroot()

        return self._containsTags(self._root)

    def validProjectPath(self):
        """Return True if the project is valid
        """
        projectPath = self._kwds.projectPath
        if not projectPath:
            return

        if (os.path.exists(projectPath / 'memops') and os.path.isdir(projectPath / 'memops')):
            return True

    def setProjectPath(self, value):
        """Set the project
        """
        self._logger(f'set project path: {value}')
        self._kwds.projectPath = value or None

    def setRemoveTags(self, value):
        """Set the list of tags to remove
        """
        self._logger(f'set invalid tags: {value}')
        self._kwds.removeTags = value or []

    def getProjectFiles(self):
        """Read and return the list of valid .xml files in the project folder
        """
        projectPath = self._kwds.projectPath
        if not projectPath:
            return

        filePaths = [(aPath(r) / file) for r, d, f in os.walk(projectPath) for file in f if os.path.splitext(file)[1] == '.xml']
        self._kwds.projectFiles = filePaths

        return self._kwds.projectFiles

    def validateXmlFiles(self):
        """Validate the files in the project folder
        """
        projectFiles = self._kwds.projectFiles or []
        if not projectFiles:
            return

        self._kwds.invalidFiles = []
        for filePath in projectFiles:
            if self.containsTags(filePath):
                self._kwds.invalidFiles.append(filePath)

        return self._kwds.invalidFiles

    def iterateXmlFiles(self):
        """Validate the files in the project folder as iterator
        Can be used with progresshandler
        """
        projectFiles = self._kwds.projectFiles or []
        if not projectFiles:
            return

        self._kwds.invalidFiles = []
        for filePath in projectFiles:
            if self.containsTags(filePath):
                self._kwds.invalidFiles.append(filePath)
            yield

        yield self._kwds.invalidFiles

    def _deleteRecurse(self, parent, indent=0):
        """Recursively delete elements in the tree
        """
        for lm in list(parent):
            self._deleteRecurse(lm, indent + 1)

        for lm in list(parent):
            if lm.tag in (self._kwds.removeTags or []):
                parent.remove(lm)
                self._logger('_' * indent + f'DELETE {lm.tag.title().strip()}')

    def writeFile(self, filePath, tree):
        """Write out the modified .xml file
        """
        fileName = filePath.basename
        renameFilePath = (filePath.parent / fileName)  #.assureSuffix('.xml')
        prefix, ext = os.path.splitext(renameFilePath)
        renameFilePath = aPath(prefix).assureSuffix('.xmlOLD')

        # write out the modified file
        safeName = aPath(getSafeFilename(renameFilePath))
        self._logger(f'Renaming old file {safeName}')
        os.rename(filePath, safeName)
        self._logger(f'Writing modified file {filePath}')
        tree.write(filePath, encoding='UTF-8', xml_declaration=True)

    def removeTags(self, projectPath, projectFiles, invalidFiles, removeTags):
        """Remove the bad tags from the .xml file
        """
        for invalidFile in invalidFiles:
            parser = ElementTree.XMLParser(target=ElementTree.TreeBuilder(insert_comments=True))
            tree = ElementTree.parse(invalidFile, parser)
            root = tree.getroot()

            # delete tags
            self._logger(f'Removing bad tags: {invalidFile}')
            self._deleteRecurse(root)

            # write edited file
            self.writeFile(invalidFile, tree)

    def run(self, *args, **kwargs):
        """Entry-point for the plugin
        """
        # read the parameters, these will have been set by the gui
        projectPath = self._kwds.projectPath
        projectFiles = self._kwds.projectFiles or []
        invalidFiles = self._kwds.invalidFiles or []
        removeTags = self._kwds.removeTags or []

        self._logger(f'Running {self.PLUGINNAME} - {invalidFiles}')

        if projectPath and projectFiles and removeTags:
            self.removeTags(projectPath, projectFiles, invalidFiles, removeTags)

        # from xml.etree import ElementTree
        # from ccpn.util.Path import aPath
        # from ccpn.util.SafeFilename import getSafeFilename
        # 
        # # active parser to include comments in import/export
        # parser = ElementTree.XMLParser(target=ElementTree.TreeBuilder(insert_comments=True))
        # 
        # # read in the file
        # filePath = aPath(
        #         '/Users/ejb66/Documents/CcpNmrData/sh3_tutorial_LabPtn.ccpn/ccpnv3/ccp/nmr/Nmr/sh3_tutorial+sh3_tutorial_vicky_2009-04-16-10-58-30-845_00001.xml')
        # tree = ElementTree.parse(filePath, parser)
        # 
        # # list of elements to remove from file
        # includeElems = ['LMOL.LabeledMolecule', 'LMOL.LabeledMixture.name', 'NMR.Experiment.labeledMixtures', 'LMOL.exo-LabeledMixture',
        #                 'NMR.Experiment.refExperiment']
        # 
        # indent = 0
        # 
        # def printRecur(parent):
        #     """Recursively prints the tree
        #     """
        #     global indent
        # 
        #     if parent.tag in includeElems:
        #         print('_' * indent + '{}'.format(parent.tag.title().strip()))
        # 
        #     indent += 4
        #     for lm in list(parent):
        #         printRecur(lm)
        #     indent -= 4
        # 
        # def deleteRecur(parent):
        #     """Recursively deletes elements in the tree
        #     """
        #     for lm in list(parent):
        #         deleteRecur(lm)
        # 
        #     for lm in list(parent):
        #         if lm.tag in includeElems:
        #             parent.remove(lm)
        #             print('_' * indent + 'DELETE {}'.format(lm.tag.title().strip()))
        # 
        # # print the tree
        # root = tree.getroot()
        # printRecur(root)
        # 
        # # delete tags
        # deleteRecur(root)
        # 
        # # print again to test
        # printRecur(root)
        # 
        # # NOTE:ED - needs swapping round when working
        # fileName = filePath.basename
        # renameFileName = fileName + '_OLD'
        # renameFilePath = (filePath.parent / renameFileName).assureSuffix('.xml')
        # 
        # # write out the modified file
        # safeName = aPath(getSafeFilename(renameFilePath))
        # tree.write(safeName, encoding='UTF-8', xml_declaration=True)
        # 
        # # with open(renameFilePath, "a+") as fp:
        # #     # added for completeness
        # #     fp.write('\n<!--End of Memops Data-->')


FilterLabeledMixturesPlugin.register()  # Registers the pipe in the pluginList
