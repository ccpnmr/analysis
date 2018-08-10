"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
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
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import ProjectTreeCheckBoxes
from ccpn.ui.gui.popups.ExportDialog import ExportDialog
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning, showWarning


exportPDF = 'PDF'
exportSVG = 'SVG'
exportPDFFilter = 'pdf files (*.pdf)'
exportSVGFilter = 'svg files (*.svg)'
exportTypes = [exportPDF, exportSVG]
exportFilters = exportPDFFilter


class ExportStripToFilePopup(ExportDialog):
    def __init__(self, parent=None, mainWindow=None, title='Export Strip to File',
                 fileMode=FileDialog.AnyFile,
                 text='Export File',
                 acceptMode=FileDialog.AcceptSave,
                 preferences=None,
                 selectFile=None,
                 filter=exportFilters,
                 strips=None,
                 **kw):

        # initialise attributes
        self.strips = strips

        super(ExportStripToFilePopup, self).__init__(parent=parent, mainWindow=mainWindow, title=title,
                                                     fileMode=fileMode, text=text, acceptMode=acceptMode,
                                                     preferences=preferences, selectFile=selectFile,
                                                     filter=filter, **kw)

        if not strips:
            showWarning(str(self.windowTitle()), 'No strips selected')
            self.reject()

    def initialise(self, userFrame):
        self.stripIds = [sd.id for sd in self.strips]
        self.stripPids = [sd.pid for sd in self.strips]

        # create radio buttons to choose the strip to print
        row = 0
        if len(self.strips) > 1:
            Label(userFrame, text='Select Strip to Print', grid=(row, 0),
                  hAlign='centre', vAlign='centre')
            row += 1

        self.stripToExport = RadioButtons(userFrame, self.stripIds,
                                          grid=(row, 0), direction='v')
        if self.current.strip:
            self.stripToExport.set(self.current.strip.id)
        self.stripToExport.setMinimumSize(self.stripToExport.sizeHint())

        # add a spacer to separate from the common save widgets
        row += 1
        HLine(userFrame, grid=(row, 0), gridSpan=(1, 1), colour=getColours()[DIVIDER], height=20)
        row += 1
        Label(userFrame, text='Select Print Type', grid=(row, 0),
              hAlign='centre', vAlign='centre')

        row += 1
        self.exportType = RadioButtons(userFrame, exportTypes,
                                       grid=(row, 0), direction='v',
                                       callback=self._changePrintType)
        self.exportType.set(exportPDF)

    def _changePrintType(self):
        selected = self.exportType.get()
        if selected == exportPDF:
            self._dialogFilter = exportPDFFilter
            self.updateDialog()

        elif selected == exportSVG:
            self._dialogFilter = exportSVGFilter
            self.updateDialog()

    def buildParameters(self):
        """build parameters dict from the user widgets, to be passed to the export method.
        :return: dict - user parameters
        """

        # build the export dict and flags

        pIndex = self.stripToExport.getIndex()
        thisPid = self.stripPids[pIndex]
        strip = self.project.getByPid(thisPid)

        prIndex = self.exportType.getIndex()
        prType = exportTypes[prIndex]

        if strip:
            # return the parameters
            params = {'filename': self.exitFilename,
                      'strip': strip,
                      'glWidget': strip._CcpnGLWidget,
                      'prType': prType}
            return params

    def exportToFile(self, filename=None, params=None):
        """Export to file
        :param filename: filename to export
        :param params: dict - user defined paramters for export
        """

        if params:
            filename = params['filename']
            glWidget = params['glWidget']
            prType = params['prType']

            if prType == exportPDF:
                pdfExport = glWidget.exportToPDF(filename, params)
                if pdfExport:
                    pdfExport.writePDFFile()
            elif prType == exportSVG:
                svgExport = glWidget.exportToSVG(filename, params)
                if svgExport:
                    svgExport.writeSVGFile()


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

    dialog = ExportStripToFilePopup(parent=application.mainWindow, mainWindow=application.mainWindow, strips=[])
    result = dialog.exec_()
