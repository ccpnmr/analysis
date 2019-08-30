"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-07-06 15:51:11 +0000 (Thu, July 06, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Spacer import Spacer
from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import ProjectTreeCheckBoxes
from ccpn.ui.gui.popups.ExportDialog import ExportDialog


CHAINS = 'chains'
NMRCHAINS = 'nmrChains'
RESTRAINTLISTS = 'restraintLists'
CCPNTAG = 'ccpn'
SKIPPREFIXES = 'skipPrefixes'
EXPANDSELECTION = 'expandSelection'


class ExportNefPopup(ExportDialog):
    def __init__(self, parent=None, mainWindow=None, title='Export to File',
                 fileMode=FileDialog.AnyFile,
                 text='Export File',
                 acceptMode=FileDialog.AcceptSave,
                 preferences=None,
                 selectFile=None,
                 filter='*',
                 **kwds):
        super(ExportNefPopup, self).__init__(parent=parent, mainWindow=mainWindow, title=title,
                                             fileMode=fileMode, text=text, acceptMode=acceptMode,
                                             preferences=preferences, selectFile=selectFile,
                                             filter=filter, **kwds)

    def initialise(self, userFrame):
        self.buttonCCPN = CheckBox(userFrame, checked=True,
                                   text='include CCPN tags',
                                   grid=(0, 0), hAlign='l')
        self.buttonExpand = CheckBox(userFrame, checked=False,
                                     text='expand selection',
                                     grid=(1, 0), hAlign='l')
        self.spacer = Spacer(userFrame, 3, 3,
                             QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                             grid=(2, 0), gridSpan=(1, 1))
        self.treeView = ProjectTreeCheckBoxes(userFrame, project=self.project, grid=(3, 0))

    def buildParameters(self):
        """build parameters dict from the user widgets, to be passed to the export method.
        :return: dict - user parameters
        """

        # build the export dict and flags
        self.flags = {}
        self.flags[SKIPPREFIXES] = []
        if self.buttonCCPN.isChecked() is False:  # these are negated as they are skipped flags
            self.flags[SKIPPREFIXES].append(CCPNTAG)
        self.flags[EXPANDSELECTION] = self.buttonExpand.isChecked()

        # new bit to read all the checked pids (contain ':') from the checkboxtreewidget
        self.newList = []
        for item in self.treeView.findItems(':', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            if item.checkState(0) == QtCore.Qt.Checked:
                self.newList.append(item.text(0))

        # return the parameters
        params = {'filename': self.exitFilename,
                  'flags': self.flags,
                  'pidList': self.newList}
        return params

    def exportToFile(self, filename=None, params=None):
        """Export to file
        :param filename: filename to export
        :param params: dict - user defined paramters for export
        """

        # this is empty because the writing is down after
        pass


if __name__ == '__main__':
    from sandbox.Geerten.Refactored.framework import Framework
    from sandbox.Geerten.Refactored.programArguments import Arguments


    _makeMainWindowVisible = False


    class MyProgramme(Framework):
        "My first app"
        pass


    myArgs = Arguments()
    myArgs.noGui = False
    myArgs.debug = True

    application = MyProgramme('MyProgramme', '3.0.0-beta3', args=myArgs)
    ui = application.ui
    ui.initialize()

    if _makeMainWindowVisible:
        ui.mainWindow._updateMainWindow(newProject=True)
        ui.mainWindow.show()
        QtWidgets.QApplication.setActiveWindow(ui.mainWindow)

    dialog = ExportNefPopup(parent=application.mainWindow, mainWindow=application.mainWindow)
    result = dialog.exec_()
