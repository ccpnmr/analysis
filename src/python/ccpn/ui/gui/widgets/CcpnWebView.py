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
__dateModified__ = "$dateModified: 2020-07-14 15:39:06 +0100 (Tue, July 14, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.util.Common import isWindowsOS
from ccpn.util.Path import aPath


class CcpnWebView(CcpnModule):
    className = 'CcpnWebView'

    IGNORE_SHORTCUTS = False

    def __init__(self, mainWindow=None, name='CcpNmr V3 Documentation', urlPath=None):
        """
        Initialise the Module widgets
        """
        super().__init__(mainWindow=mainWindow, name=name)

        self.webView = QWebEngineView()
        self.mainWidget.getLayout().addWidget(self.webView, 0, 0)

        urlPath = urlPath or ''
        # if not isWindowsOS():
        if (urlPath.startswith('http://') or urlPath.startswith('https://')):
            pass
        elif urlPath.startswith('file://'):
            # urlPath = urlPath[len('file://'):]
            # urlPath = urlPath if isWindowsOS() else 'file://'+urlPath
            pass
        else:
            if os.path.exists(aPath(urlPath)):
                # urlPath = urlPath if isWindowsOS() else 'file://'+urlPath
                urlPath = 'file://'+urlPath

        self.webView.load(QUrl(urlPath))
        self.webView.show()

    def close(self):
        """
        Close the table from the commandline
        """
        self._closeModule()


if __name__ == '__main__':
    from PyQt5 import QtWidgets
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea


    app = TestApplication()
    win = QtWidgets.QMainWindow()

    moduleArea = CcpnModuleArea(mainWindow=None)
    module = CcpnWebView(mainWindow=None, name='My Module')
    moduleArea.addModule(module)

    win.setCentralWidget(moduleArea)
    win.resize(1000, 500)
    win.setWindowTitle('Testing %s' % module.moduleName)
    win.show()

    app.start()
    win.close()

    # # example on how to use a javascript viewer can be found here
    # # https://code.tutsplus.com/tutorials/how-to-create-a-pdf-viewer-in-javascript--cms-32505
    #
    # # PDFJS = 'file:///path/to/pdfjs-1.9.426-dist/web/viewer.html'
    # PDFJS = 'file:///Users/ejb66/Downloads/pdfjs-2.4.456-dist/web/viewer.html'
    # # PDFJS = 'file:///usr/share/pdf.js/web/viewer.html'
    # PDF = 'file:///path/to/my/sample.pdf'
    #
    # class Window(QWebEngineView):
    #     def __init__(self):
    #         super(Window, self).__init__()
    #         self.load(QtCore.QUrl.fromUserInput('{}?file={}'.format(PDFJS, PDF)))
