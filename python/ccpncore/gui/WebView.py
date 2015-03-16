"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtCore, QtGui, QtWebKit

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
