"""Module Documentation here

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:57 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtWebEngineWidgets
from ccpn.framework.PathsAndUrls import ccpnUrl
from ccpn.ui.gui.widgets.BasePopup import BasePopup
from ccpn.ui.gui.widgets.Base import Base


# # # #  T D  # # # #
# Back
# Forward
# Reload
# Find
# Show plain text
#
# Remove HelpPopup

class WebViewPanel(QtWebEngineWidgets.QWebEngineView, Base):

    def __init__(self, parent, **kwds):
        super().__init__(parent=parent)
        Base._init(self, **kwds)


class WebViewPopup(BasePopup):

    def __init__(self, parent=None, url=None, **kwds):
        BasePopup.__init__(self, parent=parent, title='Web View', **kwds)

        self.webViewPanel = WebViewPanel(self)

        if url:
            self.setUrl(url)

    def setUrl(self, urlText):
        qUrl = QtCore.QUrl(urlText)
        self.webViewPanel.setUrl(qUrl)


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication


    app = TestApplication()

    popup = WebViewPopup(url=ccpnUrl)

    popup.show()
    popup.raise_()

    app.start()
