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
__dateModified__ = "$dateModified: 2020-03-09 19:05:49 +0000 (Mon, March 09, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.util.Common import isWindowsOS
import os
import posixpath

class CcpnWebView(CcpnModule):
    className = 'CcpnWebView'

    IGNORE_SHORTCUTS = False

    def __init__(self, mainWindow=None, name='CcpNmr V3 Documentation', urlPath=None):
        """
        Initialise the Module widgets
        """
        super().__init__(mainWindow=mainWindow, name=name)

        self.webView = QWebEngineView()
        self.addWidget(self.webView, 0, 0, 1, 1)  # make it the first item
        # self.webView.loadFinished.connect(self._on_load_finished)

        # NOTE:ED - need to remove windows separators
        urlPath = urlPath.replace(os.sep, posixpath.sep)
        if not isWindowsOS():
            urlPath = 'file://' + urlPath  # webEngine needs to prefix

        self.webView.load(QUrl(urlPath))
        self.webView.show()

    # def _on_load_finished(self, *args):
    #     print('>>>_on_load_finished')
    #     self.webView.show()

    # def _closeModule(self):
    #   """
    #   CCPN-INTERNAL: used to close the module
    #   """
    #   super(CcpnWebView, self)._closeModule()

    def close(self):
        """
        Close the table from the commandline
        """
        self._closeModule()
