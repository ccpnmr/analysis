
from PySide import QtCore, QtGui, QtWebKit

from ccpncore.gui.BasePopup import BasePopup
from ccpncore.gui.Base import Base

# # # #  T D  # # # # 
# Back
# Forward
# Reload
# Find
# Show plain text
#
# Remove HelpPopup

class WebViewPanel(QtWebKit.QWebView, Base):

  def __init__(self, parent, **kw):
  
    QtWebKit.QWebView.__init__(self, parent=parent)
    Base.__init__(self, **kw)
    
class WebViewPopup(BasePopup):

  def __init__(self, parent=None, url=None, **kw):
  
    BasePopup.__init__(self, parent=parent, title='Web View', **kw)

    self.webViewPanel = WebViewPanel(self)
    
    if url:
      self.setUrl(url)
   
  def setUrl(self, urlText):
  
    qUrl = QtCore.QUrl(urlText)
    self.webViewPanel.setUrl(qUrl)

if __name__ == '__main__':
  
  from ccpncore.gui.Application import TestApplication
  
  app = TestApplication()

  popup = WebViewPopup(url='http://www.ccpn.ac.uk')
  
  popup.show()
  popup.raise_()

  app.start()
