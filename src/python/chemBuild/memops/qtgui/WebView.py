
# from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets
#
# from .BasePopup import BasePopup
# from .Base import Base

# # # #  T D  # # # # 
# Back
# Forward
# Reload
# Find
# Show plain text
#
# Remove HelpPopup

# class WebViewPanel(QtWebEngineWidgets.QWebEngineView, Base):
#
#   def __init__(self, parent, **kw):
#     QtWebEngineWidgets.QWebEngineView.__init__(self, parent=parent)
#     Base.__init__(self, parent, **kw)
    
# class WebViewPopup(BasePopup):
#
#   def __init__(self, url=None, **kw):
#
#     BasePopup.__init__(self, title='Web View', **kw)
#
#     self.webViewPanel = WebViewPanel(self)
#
#     if url:
#       self.setUrl(url)
#
#   def setUrl(self, urlText):
#
#     qUrl = QtCore.QUrl(urlText)
#     self.webViewPanel.setUrl(qUrl)

# if __name__ == '__main__':
#
#   from .Application import Application
#
#   app = Application()
#
#   popup = WebViewPopup('http://www.ccpn.ac.uk')
#
#   app.start()
