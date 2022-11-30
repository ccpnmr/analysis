"""Module Documentation here

"""
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
__dateModified__ = "$dateModified: 2022-11-30 11:22:08 +0000 (Wed, November 30, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import webbrowser as wb
#
# from ccpn.ui.gui.widgets.PulldownList import PulldownList
# from ccpn.ui.gui.widgets.WebView import WebViewPopup
#
#
# browserNames = ['firefox', 'netscape', 'mozilla', 'konqueror', 'kfm', 'mosaic',
#                 'grail', 'w3m', 'windows-default', 'internet-config']
#
#
# class WebBrowser:
#
#     def __init__(self, parent, name=None, url=None):
#
#         names = getBrowserList()
#         if names and (not name):
#             name = names[0]
#
#         self.name = name
#
#         if url:
#             self.open(url)
#
#     def open(self, url):
#
#         try:
#             browser = wb.get(self.name)
#             browser.open(url)
#
#         except Exception:
#             WebViewPopup(url)
#
#
# class WebBrowserPulldown(PulldownList):
#
#     def __init__(self, parent, browser=None, **kwds):
#
#         super().__init__(parent, **kwds)
#
#         self.browserList = getBrowserList()
#
#         if not browser:
#             browser = getDefaultBrowser()
#
#         if self.browserList:
#             if (not browser) or (browser not in self.browserList):
#                 browser = self.browserList[0]
#         self.browser = browser
#
#         if self.browserList:
#             self.setup(self.browserList, self.browserList, self.browserList.index(self.browser))
#
#         self.callback = self.setWebBrowser
#
#     def setWebBrowser(self, name):
#
#         if name != self.browser:
#             self.browser = name
#
#     def destroy(self):
#
#         pass
#
#
# def getBrowserList():
#     browsers = []
#     default = getDefaultBrowser()
#     if default:
#         browsers = [default, ]
#
#     for name in browserNames:
#         if name == default:
#             continue
#
#         try:
#             wb.get(name)
#             browsers.append(name)
#         except Exception:
#             try:
#                 if wb._iscommand(name):
#                     wb.register(name, None, wb.Netscape(name))
#                     wb.get(name)
#                     browsers.append(name)
#             except Exception:
#                 continue
#
#     return browsers
#
#
# def getDefaultBrowser():
#     try:
#         br = wb.get()
#     except Exception:
#         return
#
#     if not hasattr(br, 'name'):
#         # Max OS X
#         return
#
#     try:
#         wb.get(br.name)
#     except Exception:
#         wb.register(br.name, None, br)
#
#     return br.name
