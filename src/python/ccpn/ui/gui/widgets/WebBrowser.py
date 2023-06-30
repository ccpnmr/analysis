# """Module Documentation here
#
# """
# #=========================================================================================
# # Licence, Reference and Credits
# #=========================================================================================
# __copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
# __credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
#                "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
# __licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
# __reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
#                  "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
#                  "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
# #=========================================================================================
# # Last code modification
# #=========================================================================================
# __modifiedBy__ = "$modifiedBy: Luca Mureddu $"
# __dateModified__ = "$dateModified: 2023-06-30 13:12:58 +0100 (Fri, June 30, 2023) $"
# __version__ = "$Revision: 3.2.0 $"
# #=========================================================================================
# # Created
# #=========================================================================================
# __author__ = "$Author: CCPN $"
# __date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
# #=========================================================================================
# # Start of code
# #=========================================================================================
#
#
# from ccpn.ui.gui.widgets.Base import Base
# from ccpn.util.Logging import getLogger
# from ccpn.ui.gui.widgets.Widget import Widget
# from ccpn.ui.gui.widgets.ToolBar import ToolBar
# from ccpn.ui.gui.widgets.Action import Action
# from ccpn.ui.gui.widgets.Icon import Icon
# from ccpn.util.Path import aPath
# from ccpn.ui.gui.widgets.MessageDialog import  showMessage, showMulti
# from PyQt5 import QtWidgets, QtWebEngineWidgets
# from  PyQt5 import QtGui, QtCore
#
# class WebEngineView(QtWebEngineWidgets.QWebEngineView, Base):
#
#     def __init__(self, parent=None, htmlFilePath=None,  **kwds):
#         super().__init__(parent)
#         Base._init(self, setLayout=True, **kwds)
#         self.htmlFilePath = htmlFilePath
#         if self.htmlFilePath is not None:
#             self.setFile(self.htmlFilePath)
#
#     def setHtmlFile(self, htmlFilePath):
#         path  = aPath(htmlFilePath)
#         if not path.exists():
#             showMessage('Path not found', f'Could not load {path}')
#             return
#         try:
#             self.setUrl(QtCore.QUrl.fromLocalFile(str(path)))
#         except Exception as err:
#             showMessage('Help file not available', f'Could not load the help browser:  {err}')
#
#     def setUrl(self, url):
#         """
#         :param url: a website url
#         :return:
#         """
#         if isinstance(url, str):
#             url = QtCore.QUrl(url)
#         elif  isinstance(url, QtCore.QUrl):
#             url = url
#         else:
#             raise RuntimeError('Url must be a string or QUrl')
#
#         super().setUrl(url)
#
# class WebBrowserWidget(Widget, Base):
#
#     def __init__(self, parent=None,  htmlFilePath=None, htmlUrl=None,  **kwds):
#         super().__init__(parent)
#         Base._init(self, setLayout=True, **kwds)
#
#         self.toolbar = ToolBar(parent=self, iconSizes=(20, 20), grid=(0, 0), hPolicy='preferred', hAlign='left')
#         self.browser = WebEngineView(self,  grid=(1, 0), gridSpan=(1, 2))
#         self.htmlFilePath = htmlFilePath
#         self.htmlUrl = htmlUrl
#         self._setActions()
#
#     def setHtmlFilePath(self, htmlFilePath):
#         self.htmlFilePath = htmlFilePath
#         self.browser.setHtmlFile(self.htmlFilePath)
#
#     def setUrl(self, url):
#         self.htmlUrl = url
#         self.browser.setUrl(url)
#
#     def goHome(self):
#         if self.htmlFilePath is not None:
#             self.setHtmlFilePath(self.htmlFilePath)
#             return
#         if self.htmlUrl is not None:
#             self.setUrl(self.htmlUrl)
#         else:
#             getLogger().warning('No place to go!')
#
#     def forward(self):
#         self.browser.forward()
#
#     def back(self):
#         self.browser.back()
#
#     def reload(self):
#         self.browser.reload()
#
#     def stop(self):
#         self.browser.stop()
#
#     def _setActions(self):
#         homeAction = Action(self.toolbar, text='Home', callback=self.goHome, shortcut=None, checked=True, checkable=False,
#                  icon=Icon('icons/go-home'), translate=True, enabled=True, toolTip=None, )
#         left = Action(self.toolbar, text='Back', callback=self.back, shortcut=None, checked=True, checkable=False,
#                  icon=Icon('icons/orange-left'), translate=True, enabled=True, toolTip=None, )
#         right = Action(self.toolbar, text='Forward', callback=self.forward, shortcut=None, checked=True, checkable=False,
#                  icon=Icon('icons/orange-right'), translate=True, enabled=True, toolTip=None, )
#         stop = Action(self.toolbar, text='stop', callback=self.stop, shortcut=None, checked=True, checkable=False,
#                  icon=Icon('icons/reset'), translate=True, enabled=True, toolTip=None, )
#         reload = Action(self.toolbar, text='reload', callback=self.reload, shortcut=None, checked=True, checkable=False,
#                  icon=Icon('icons/update'), translate=True, enabled=True, toolTip=None, )
#         self.toolbar.addAction(homeAction)
#         self.toolbar.addAction(left)
#         self.toolbar.addAction(right)
#         self.toolbar.addAction(stop)
#         self.toolbar.addAction(reload)
#
#
# if __name__ == '__main__':
#     from ccpn.ui.gui.widgets.Application import TestApplication
#     from ccpn.ui.gui.popups.Dialog import CcpnDialog
#     from ccpn.ui.gui.widgets.Widget import Widget
#
#     app = TestApplication()
#
#     popup = CcpnDialog(windowTitle='Test widget', setLayout=True)
#     widget = WebBrowserWidget(parent=popup, grid=(0, 0))
#     widget.browser.setUrl("http://www.google.com")
#     popup.show()
#     popup.raise_()
#     app.start()
