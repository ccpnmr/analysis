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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2020-05-15 09:32:25 +0000 (Fri, May 15, 2020) $"
__version__ = "$Revision: 3.0.1 $"
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
from ccpn.ui.gui.widgets.FileDialog import FileDialog, USERMACROSPATH
from pyqode.python.widgets import PyCodeEdit

# import warnings
# with warnings.catch_warnings():
#     warnings.filterwarnings("ignore", message='Unimplemented completion icon_type:')

marginColour = QtGui.QColor('lightgrey')
marginPosition = 100
#########################################################################################
################################  Editor Widget  ########################################
#########################################################################################

class PyCodeEditor(PyCodeEdit, Base):
    def __init__(self, parent=None, **kwds):
        super().__init__(parent)
        Base._init(self, **kwds)
        self.rightMarginMode = self.modes.get('RightMarginMode')
        if self.rightMarginMode:
            self.rightMarginMode.color = marginColour
            self.rightMarginMode.position = marginPosition

    def get(self):
        return self.toPlainText()

    def set(self, value):
        self.setPlainText(value)

    def saveToPDF(self, fileName=None):

        dialog = FileDialog(self, fileMode=FileDialog.AnyFile, text='Save Macro As...',
                            acceptMode=FileDialog.AcceptSave, selectFile=fileName,
                            filter='*.pdf',
                            pathID=USERMACROSPATH)
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
  editor.saveToPDF()
  editor.get()


  popup.show()
  popup.raise_()
  app.start()



