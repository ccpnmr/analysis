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
__dateModified__ = "$dateModified: 2021-02-04 12:07:38 +0000 (Thu, February 04, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2020-05-15 09:30:25 +0000 (Fri, May 15, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt5 import QtGui
from PyQt5 import QtPrintSupport
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.FileDialog import MacrosFileDialog
from pyqode.python.widgets import PyCodeEdit
from ccpn.ui.gui.modules.macroEditorUtil import MacroEditorServer
from ccpn.ui.gui.modules.macroEditorUtil import MacroEditorNativeServer
from pyqode.python import panels as pypanels
from pyqode.core import api
from pyqode.python.modes.calltips import CalltipsMode
from ccpn.ui.gui.modules.macroEditorUtil.workers import CcpnQuickDocPanel, CcpnCalltipsMode

marginColour = QtGui.QColor('lightgrey')
marginPosition = 100
import sys
#########################################################################################
################################  Editor Widget  ########################################
#########################################################################################

class PyCodeEditor(PyCodeEdit, Base):

    useNativeCompletion = False # use the original completion without Ccpn Namespace and icons

    def __init__(self, parent=None, application=None, **kwds):

        if self.useNativeCompletion:
            serverScript = MacroEditorNativeServer.__file__
        else:
            serverScript = MacroEditorServer.__file__
        super().__init__(parent,  server_script=serverScript)
        Base._init(self, **kwds)
        self.rightMarginMode = self.modes.get('RightMarginMode')
        if self.rightMarginMode:
            self.rightMarginMode.color = marginColour
            self.rightMarginMode.position = marginPosition

        self.application = application
        #     ## removing the default completion and the replacing ccpnCompletion for live namespaces breaks the completer and Gui.
        #     self.modes.remove(modes.CodeCompletionMode)
        #     namespace = self.application.mainWindow.namespace
        #     ccpnNamespaceCompletionMode = CcpnNamespaceCompletionMode()
        #     ccpnNamespaceCompletionMode.namespace = namespace
        #     self.modes.append(ccpnNamespaceCompletionMode)
        self.panels.remove(pypanels.QuickDocPanel)
        self.panels.append(CcpnQuickDocPanel(), api.Panel.Position.BOTTOM)
        self.modes.remove(CalltipsMode)
        self.modes.append(CcpnCalltipsMode())



    def get(self):
        return self.toPlainText()

    def set(self, value):
        self.setPlainText(value)

    def saveToPDF(self, fileName=None):
        fType = '*.pdf'
        dialog = MacrosFileDialog(parent=self, acceptMode='save', selectFile=fileName, fileFilter=fType)
        dialog.exec()
        filename = dialog.selectedFile()
        if filename:
            printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
            printer.setPageSize(QtPrintSupport.QPrinter.A4)
            printer.setColorMode(QtPrintSupport.QPrinter.Color)
            printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            self.document().print_(printer)

    def enterEvent(self, event):
        self.setFocus()
        super(PyCodeEditor, self).enterEvent(event)


if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.popups.Dialog import CcpnDialog

  app = TestApplication()
  popup = CcpnDialog(windowTitle='Test widget', setLayout=True)
  editor = PyCodeEditor(popup, grid=[0,0])
  editor.set('print("Hello")')
  editor.get()


  popup.show()
  popup.raise_()
  app.start()



