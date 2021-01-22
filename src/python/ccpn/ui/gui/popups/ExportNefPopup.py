"""
Module Documentation here
"""
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
__dateModified__ = "$dateModified: 2021-01-22 15:44:49 +0000 (Fri, January 22, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-07-06 15:51:11 +0000 (Thu, July 06, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.Spacer import Spacer
from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import ProjectTreeCheckBoxes
from ccpn.ui.gui.popups.ExportDialog import ExportDialogABC
from ccpn.ui.gui.widgets.MessageDialog import showError


CHAINS = 'chains'
NMRCHAINS = 'nmrChains'
RESTRAINTLISTS = 'restraintLists'
CCPNTAG = 'ccpn'
SKIPPREFIXES = 'skipPrefixes'
EXPANDSELECTION = 'expandSelection'


class ExportNefPopup(ExportDialogABC):
    """
    Class to handle exporting Nef files
    """

    def __init__(self, parent=None, mainWindow=None, title='Export to File',
                 fileMode='anyFile',
                 acceptMode='export',
                 selectFile=None,
                 fileFilter='*.nef',
                 **kwds):
        """
        Initialise the widget
        """
        super().__init__(parent=parent, mainWindow=mainWindow, title=title,
                         fileMode=fileMode, acceptMode=acceptMode,
                         selectFile=selectFile,
                         fileFilter=fileFilter,
                         **kwds)

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
        self.treeView = ProjectTreeCheckBoxes(userFrame, project=None, grid=(3, 0), includeProject=True)

    def populate(self, userframe):
        """Populate the widgets with project
        """
        try:
            self.treeView.populate(self.project)
        except Exception as es:
            showError('{} Error' % self._dialogAcceptMode.capitalize(), str(es))

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

        # new bit to read all the checked pids (contain ':') from the checkboxtreewidget - don't include project name
        self.newList = self.treeView.getSelectedPids(includeRoot=False)

        # return the parameters
        params = {'filename': self.exitFilename,
                  'flags'   : self.flags,
                  'pidList' : self.newList}
        return params

    def exportToFile(self, filename=None, params=None):
        """Export to file
        :param filename: filename to export
        :param params: dict - user defined parameters for export
        """

        # this is empty because the writing is down after
        pass


if __name__ == '__main__':
    # from sandbox.Geerten.Refactored.framework import Framework
    # from sandbox.Geerten.Refactored.programArguments import Arguments

    # from ccpn.framework.Framework import Framework
    # from ccpn.framework.Framework import Arguments
    #
    # _makeMainWindowVisible = False
    #
    #
    # class MyProgramme(Framework):
    #     """My first app"""
    #     pass
    #
    #
    # myArgs = Arguments()
    # myArgs.interface = 'NoUi'
    # myArgs.debug = True
    # myArgs.darkColourScheme = False
    # myArgs.lightColourScheme = True
    #
    # application = MyProgramme('MyProgramme', '3.0.1', args=myArgs)
    # ui = application.ui
    # ui.initialize(ui.mainWindow)  # ui.mainWindow not needed for refactored?
    #
    # if _makeMainWindowVisible:
    #     # ui.mainWindow._updateMainWindow(newProject=True)
    #     ui.mainWindow.show()
    #     QtWidgets.QApplication.setActiveWindow(ui.mainWindow)
    #
    # # register the programme
    # from ccpn.framework.Application import ApplicationContainer
    #
    #
    # container = ApplicationContainer()
    # container.register(application)
    # application.useFileLogger = True
    #
    # app = QtWidgets.QApplication(['testApp'])
    # # run the dialog
    # dialog = ExportNefPopup(parent=ui.mainWindow, mainWindow=ui.mainWindow)
    # result = dialog.exec_()

    from ccpn.ui.gui.widgets.Application import newTestApplication
    from ccpn.framework.Application import getApplication


    app = newTestApplication(interface='NoUi')
    application = getApplication()

    dialog = ExportNefPopup(parent=application.ui.mainWindow if application else None)

    result = dialog.exec_()
