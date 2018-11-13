"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

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
import webbrowser as wb

from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.WebView import WebViewPopup

browserNames = ['firefox','netscape','mozilla','konqueror','kfm','mosaic',
                'grail','w3m','windows-default','internet-config']

class WebBrowser:

  def __init__(self, parent, name=None, url=None):
  
    names = getBrowserList()
    if names and (not name):
      name = names[0]
    
    self.name   = name
    
    if url:
      self.open(url)
  
  def open(self, url):
    
    try:
      browser = wb.get(self.name)
      browser.open(url)
      
    except:
      WebViewPopup(url)


class WebBrowserPulldown(PulldownList):

  def __init__(self, parent, browser=None, **kwds):

    super().__init__(parent, **kwds)

    self.browserList = getBrowserList()

    if not browser:
      browser = getDefaultBrowser()

    if self.browserList:
      if (not browser) or (browser not in self.browserList):
        browser = self.browserList[0]
    self.browser = browser

    if self.browserList:
      self.setup(self.browserList, self.browserList, self.browserList.index(self.browser))
    
    self.callback = self.setWebBrowser

  def setWebBrowser(self, name):

    if name != self.browser:
      self.browser = name

  def destroy(self):

    pass


def getBrowserList():

  browsers = []
  default  = getDefaultBrowser()
  if default:
    browsers = [default,]
  
  for name in browserNames:
    if name == default:
      continue
  
    try:
      wb.get(name)
      browsers.append(name)
    except:
      
      try:
        if wb._iscommand(name):
          wb.register(name, None, wb.Netscape(name))
          wb.get(name)
          browsers.append(name)
      except:
        continue

  return browsers


def getDefaultBrowser():

  try:
    br = wb.get()
  except:
    return
  
  if not hasattr(br, 'name'):
    # Max OS X
    return
  
  try:
    wb.get(br.name)
  except:
    wb.register(br.name, None, br)
  
  return br.name
