#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-01-22 15:44:48 +0000 (Fri, January 22, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-11-28 10:28:42 +0000 (Tue, Nov 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


import os
from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Frame import ScrollableFrame
from ccpn.ui.gui.lib.GuiPath import PathEdit
from ccpn.ui.gui.guiSettings import BORDERNOFOCUS_COLOUR
from ccpn.framework.lib.Plugin import Plugin
from ccpn.ui.gui.modules.PluginModule import PluginModule
from ccpn.ui.gui.widgets.FileDialog import DataFileDialog
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.util.AttrDict import AttrDict
from xml.etree import ElementTree
from ccpn.util.Path import aPath
from ccpn.util.SafeFilename import getSafeFilename
from ccpn.ui.gui.widgets.MoreLessFrame import MoreLessFrame


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
PROJECTPATH = 'projectPath'
PROJECTFILES = 'projectFiles'
INVALIDFILES = 'invalidFiles'
REMOVETAGS = 'removeTags'


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

        # NOTE:ED - change this to _blankContainer?
        self.obj = AttrDict()
        self.obj[PROJECTPATH] = None
        self.obj[REMOVETAGS] = REMOVETAGLIST

        # correct way to setup a scroll area
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

        self._setWidgets(self._scrollFrame)
        self._populate()

        self.plugin._loggerCallback = self._guiLogger

    def _guiLogger(self, *args):
        self.xmlFilterLogData.append(*args)

    def _setWidgets(self, parent):

        row = 0
        self.userWorkingPathLabel = Label(parent, "Project Path ", grid=(row, 0), )
        self.userWorkingPathData = PathEdit(parent, grid=(row, 1), vAlign='t')
        self.userWorkingPathData.setMinimumWidth(LineEditsMinimumWidth)
        self.userWorkingPathButton = Button(parent, grid=(row, 2), callback=self._getUserWorkingPath,
                                            icon='icons/directory', hPolicy='fixed')
        self.userWorkingPathData.textChanged.connect(self._setUserWorkingPath)

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
        self.plugin.run(**self.obj)
        self._populate()
        self._setUserWorkingPath(self.obj[PROJECTPATH])

    def _populate(self):
        self.xmlFilterData.clear()
        self.xmlFilterData.addItems(REMOVETAGLIST)

    def _getUserWorkingPath(self):
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

    def _setUserWorkingPath(self, value):
        value = aPath(value)
        self.obj[PROJECTPATH] = value
        if self.userWorkingPathData.validator().checkState == QtGui.QValidator.Acceptable:

            self.plugin.setProjectPath(value)
            self.plugin.setRemoveTags(REMOVETAGLIST)
            filePaths = self.plugin.getProjectFiles()

            self.xmlFileData.clear()
            self.xmlFileData.addItems([str(fp) for fp in filePaths])
            if self.plugin.validProjectPath():
                self._validateXmlFiles()
            else:
                self._ignoreXmlFiles()

    def _validateXmlFiles(self):
        """Colour items
        """
        value = self.obj[PROJECTPATH]
        if not (os.path.exists(value / 'memops') and os.path.isdir(value / 'memops')):
            return

        invalidFiles = self.plugin.validateXmlFiles()

        branchFiles = self.xmlFileData.getItems()
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
        value = self.obj[PROJECTPATH]
        if (os.path.exists(value / 'memops') and os.path.isdir(value / 'memops')):
            return

        branchFiles = self.xmlFileData.getItems()
        for item in branchFiles:
            # colour all as grey
            item.setForeground(QtCore.Qt.gray)

    def _toggleWordWrap(self, value):
        if value:
            self.xmlFilterLogData.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        else:
            self.xmlFilterLogData.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)


class FilterLabeledMixturesPlugin(Plugin):
    PLUGINNAME = 'Filter Labeled Mixtures'
    guiModule = FilterLabeledMixturesGuiPlugin

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self._kwds = AttrDict([(PROJECTPATH, None),
                               (PROJECTFILES, None),
                               (INVALIDFILES, None),
                               (REMOVETAGS, REMOVETAGLIST)])
        self._loggerCallback = None

    def _logger(self, *args):
        if self._loggerCallback:
            self._loggerCallback(*args)

    def _containsTags(self, parent) -> bool:
        """Recursively check whether the tree contains bad tags
        """
        if parent.tag in self._kwds[REMOVETAGS]:
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

        tags = self._containsTags(self._root)
        return tags

    def validProjectPath(self):
        projectPath = self._kwds[PROJECTPATH]
        if not projectPath:
            return

        if (os.path.exists(projectPath / 'memops') and os.path.isdir(projectPath / 'memops')):
            return True

    def setProjectPath(self, value):
        self._logger('set project path: {}'.format(value))
        self._kwds[PROJECTPATH] = value

    def setRemoveTags(self, value):
        self._logger('set invalid tags: {}'.format(value))
        self._kwds[REMOVETAGS] = value

    def getProjectFiles(self):
        projectPath = self._kwds[PROJECTPATH]
        if not projectPath:
            return

        filePaths = [(aPath(r) / file) for r, d, f in os.walk(projectPath) for file in f if os.path.splitext(file)[1] == '.xml']
        self._kwds[PROJECTFILES] = filePaths

        return self._kwds[PROJECTFILES]

    def validateXmlFiles(self):
        projectFiles = self._kwds[PROJECTFILES]
        if not projectFiles:
            return

        self._kwds[INVALIDFILES] = []
        for filePath in projectFiles:
            error = self.containsTags(filePath)
            if error:
                self._kwds[INVALIDFILES].append(filePath)

        return self._kwds[INVALIDFILES]

    def _deleteRecurse(self, parent, indent=0):
        """Recursively deletes elements in the tree
        """
        for lm in list(parent):
            self._deleteRecurse(lm, indent + 1)

        for lm in list(parent):
            if lm.tag in self._kwds[REMOVETAGS]:
                parent.remove(lm)
                self._logger('_' * indent + 'DELETE {}'.format(lm.tag.title().strip()))

    def writeFile(self, filePath, tree):
        fileName = filePath.basename
        renameFilePath = (filePath.parent / fileName)  #.assureSuffix('.xml')
        prefix, ext = os.path.splitext(renameFilePath)
        renameFilePath = aPath(prefix).assureSuffix('.xmlOLD')

        # write out the modified file
        safeName = aPath(getSafeFilename(renameFilePath))
        self._logger('Renaming old file {}'.format(safeName))
        os.rename(filePath, safeName)
        self._logger('Writing modified file {}'.format(filePath))
        tree.write(filePath, encoding='UTF-8', xml_declaration=True)

    def removeTags(self, projectPath, projectFiles, invalidFiles, removeTags):
        for invalidFile in invalidFiles:
            parser = ElementTree.XMLParser(target=ElementTree.TreeBuilder(insert_comments=True))
            tree = ElementTree.parse(invalidFile, parser)
            root = tree.getroot()

            # delete tags
            self._logger('Removing bad tags: {}'.format(invalidFile))
            self._deleteRecurse(root)

            # write edited file
            self.writeFile(invalidFile, tree)

    def run(self, **kwargs):

        projectPath = self._kwds[PROJECTPATH]
        projectFiles = self._kwds[PROJECTFILES]
        invalidFiles = self._kwds[INVALIDFILES]
        removeTags = self._kwds[REMOVETAGS]

        self._logger('Running {} - {}'.format(self.PLUGINNAME, invalidFiles))

        if projectPath and projectFiles and removeTags:
            self.removeTags(projectPath, projectFiles, invalidFiles, removeTags)
        return

        from xml.etree import ElementTree
        from ccpn.util.Path import aPath
        from ccpn.util.SafeFilename import getSafeFilename

        # active parser to include comments in import/export
        parser = ElementTree.XMLParser(target=ElementTree.TreeBuilder(insert_comments=True))

        # read in the file
        filePath = aPath(
                '/Users/ejb66/Documents/CcpNmrData/sh3_tutorial_LabPtn.ccpn/ccpnv3/ccp/nmr/Nmr/sh3_tutorial+sh3_tutorial_vicky_2009-04-16-10-58-30-845_00001.xml')
        tree = ElementTree.parse(filePath, parser)

        # list of elements to remove from file
        includeElems = ['LMOL.LabeledMolecule', 'LMOL.LabeledMixture.name', 'NMR.Experiment.labeledMixtures', 'LMOL.exo-LabeledMixture',
                        'NMR.Experiment.refExperiment']

        indent = 0

        def printRecur(parent):
            """Recursively prints the tree
            """
            global indent

            if parent.tag in includeElems:
                print('_' * indent + '{}'.format(parent.tag.title().strip()))

            indent += 4
            for lm in list(parent):
                printRecur(lm)
            indent -= 4

        def deleteRecur(parent):
            """Recursively deletes elements in the tree
            """
            for lm in list(parent):
                deleteRecur(lm)

            for lm in list(parent):
                if lm.tag in includeElems:
                    parent.remove(lm)
                    print('_' * indent + 'DELETE {}'.format(lm.tag.title().strip()))

        # print the tree
        root = tree.getroot()
        printRecur(root)

        # delete tags
        deleteRecur(root)

        # print again to test
        printRecur(root)

        # NOTE:ED - needs swapping round when working
        fileName = filePath.basename
        renameFileName = fileName + '_OLD'
        renameFilePath = (filePath.parent / renameFileName).assureSuffix('.xml')

        # write out the modified file
        safeName = aPath(getSafeFilename(renameFilePath))
        tree.write(safeName, encoding='UTF-8', xml_declaration=True)

        # with open(renameFilePath, "a+") as fp:
        #     # added for completeness
        #     fp.write('\n<!--End of Memops Data-->')


FilterLabeledMixturesPlugin.register()  # Registers the pipe in the pluginList
