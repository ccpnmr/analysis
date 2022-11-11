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
__dateModified__ = "$dateModified: 2022-11-11 15:42:50 +0000 (Fri, November 11, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import os
# import posixpath
# from PyQt5 import QtCore
# from PyQt5.QtWebEngineWidgets import QWebEngineView
# from ccpn.ui.gui.modules.CcpnModule import CcpnModule
# from ccpn.util.Common import isWindowsOS
# from ccpn.util.Path import aPath
# from ccpn.ui.gui.guiSettings import BORDERNOFOCUS_COLOUR


# class CcpnWebView(CcpnModule):
#     className = 'CcpnWebView'
#
#     IGNORE_SHORTCUTS = False
#
#     def __init__(self, mainWindow=None, name='HtmlModule', urlPath=None):
#         """
#         Initialise the Module widgets
#         """
#         super().__init__(mainWindow=mainWindow, name=name)
#
#         self.webView = QWebEngineView()
#         self.mainWidget.getLayout().addWidget(self.webView, 0, 0)
#
#         self.mainWidget.setStyleSheet('border-right: 1px solid %s;'
#                                       'border-left: 1px solid %s;'
#                                       'border-bottom: 1px solid %s;' % (BORDERNOFOCUS_COLOUR, BORDERNOFOCUS_COLOUR, BORDERNOFOCUS_COLOUR))
#
#         # may be a Path object
#         urlPath = str(urlPath) if urlPath is not None else ''
#
#         if (urlPath.startswith('http://') or urlPath.startswith('https://')):
#             pass
#         elif urlPath.startswith('file://'):
#             urlPath = urlPath[len('file://'):]
#             if isWindowsOS():
#                 urlPath = urlPath.replace(os.sep, posixpath.sep)
#             else:
#                 urlPath = 'file://' + urlPath
#         else:
#             if isWindowsOS():
#                 urlPath = urlPath.replace(os.sep, posixpath.sep)
#             else:
#                 urlPath = 'file://' + str(aPath(urlPath))
#
#         self.webView.load(QtCore.QUrl.fromUserInput(urlPath))
#
#
# def main():
#     from ccpn.ui.gui.widgets.Application import newTestApplication
#     from ccpn.framework.Application import getApplication
#
#     # create a new test application
#     app = newTestApplication(interface='Gui')
#     application = getApplication()
#     # mainWindow = application.ui.mainWindow
#     # add a module
#     # _module = CcpnWebView(mainWindow=None, name='My Module', urlPath='http://www.ccpn.ac.uk')
#     # mainWindow.moduleArea.addModule(_module)
#
#     # show the mainWindow
#     app.start()
#
#     # # example on how to use a javascript viewer can be found here
#     # # https://code.tutsplus.com/tutorials/how-to-create-a-pdf-viewer-in-javascript--cms-32505
#     #
#     # # PDFJS = 'file:///path/to/pdfjs-1.9.426-dist/web/viewer.html'
#     # PDFJS = 'file:///Users/ejb66/Downloads/pdfjs-2.4.456-dist/web/viewer.html'
#     # # PDFJS = 'file:///usr/share/pdf.js/web/viewer.html'
#     # PDF = 'file:///path/to/my/sample.pdf'
#     #
#     # class Window(QWebEngineView):
#     #     def __init__(self):
#     #         super(Window, self).__init__()
#     #         self.load(QtCore.QUrl.fromUserInput('{}?file={}'.format(PDFJS, PDF)))
#
#
# if __name__ == '__main__':
#     main()
