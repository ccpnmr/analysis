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
__dateModified__ = "$dateModified: 2017-07-07 16:32:51 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets

from ccpn.framework.PathsAndUrls import ccpnUrl

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.BasePopup import BasePopup
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.WebBrowser import WebBrowser
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.util.Logging import getLogger


class ButtonList(Widget):

  def __init__(self, parent=None, texts=None, callbacks=None, icons=None,
               tipTexts=None, direction='h', commands=None, images=None, **kwds):

    super().__init__(parent, setLayout=True, **kwds)     # ejb - added setLayout

    self.buttonNames = {}

    if commands:
      print("qtgui.ButtonList.commands is deprecated; use .callbacks")
      callbacks = commands

    if images:
      print("qtgui.ButtonList.images is deprecated; use .icons")
      icons = images

    if texts is None:
      texts = []

    if callbacks is None:
      callbacks = []

    assert len(texts) == len(callbacks)

    direction = direction.lower()
    self.direction = direction
    
    if tipTexts is None:
      tipTexts = []
      
    if icons is None:
      icons = []

    while len(tipTexts) < len(texts):
      tipTexts.append(None)  

    while len(icons) < len(texts):
      icons.append(None)  

    self.buttons = []
    self.addButtons(texts, callbacks, icons, tipTexts)

    # set focus always on the last button (which is usually the ok, or run button)
    if len(self.buttons)>0:
      lastButton = self.buttons[-1]
      lastButton.setFocus()



  def addButtons(self, texts, callbacks, icons=None, tipTexts=None):
  
    if tipTexts is None:
      tipTexts = []
      
    if icons is None:
      icons = []

    while len(tipTexts) < len(texts):
      tipTexts.append(None)  

    while len(icons) < len(texts):
      icons.append(None)  
    
    j = len(self.buttons)

    for i, text in enumerate(texts):
      if 'h' in self.direction:
        grid = (0,i+j)
      else:
        grid = (i+j,0)
        
      button = Button(self, text, callbacks[i], icons[i],
                      tipText=tipTexts[i], grid=grid)
      # button.setMinimumWidth(20)

      width = button.fontMetrics().boundingRect(text).width() + 7
      button.setMinimumWidth(width*1.5)

      self.buttons.append(button)
      self.buttonNames[text] = i+j

  def setButtonEnabled(self, buttonName:str, enable:bool=True):
    """
    Enable/Disable a button by name
    :param buttonName(str) - name of the button:
    :param enable(bool) - True or False:
    """
    if buttonName in self.buttonNames.keys():
      self.buttons[self.buttonNames[buttonName]].setEnabled(enable)
    else:
      getLogger().warning('Button %s not found in the list' % buttonName)

  def setButtonVisible(self, buttonName:str, visible:bool=True):
    """
    Show/hide a button by name
    :param buttonName(str) - name of the button:
    :param visible(bool) - True or False:
    """
    if buttonName in self.buttonNames.keys():
      if visible:
        self.buttons[self.buttonNames[buttonName]].show()
      else:
        self.buttons[self.buttonNames[buttonName]].hide()
    else:
      getLogger().warning('Button %s not found in the list' % buttonName)


class UtilityButtonList(ButtonList):

  def __init__(self, parent,
               webBrowser=None, helpUrl=None, helpMsg=None,
               doClone=True, doHelp=True, doClose=True,
               cloneText=None, helpText=None, closeText=None,
               cloneCmd=None, helpCmd=None, closeCmd=None,
               cloneTip='Duplicate window', helpTip='Show help', closeTip='Close window',
               *args, **kwds):
    
    ButtonList.__init__(self, parent, *args, **kwds)
    
    self.helpUrl = helpUrl
    self.helpMsg = helpMsg
    
    self.popup = parent.window()
    if not isinstance(self.popup, BasePopup):
      self.popup = None
   
    if self.popup and not webBrowser:
      webBrowser = WebBrowser(self.popup)
 
    self.webBrowser = webBrowser

    _callbacks = []
    _texts    = []
    _icons   = []
    _tipTexts = []
    
    _doActions = [(doClone, cloneCmd, self.duplicatePopup, cloneText, 'icons/window-duplicate.png', cloneTip),
                  (doHelp,   helpCmd, self.launchHelp, helpText,  'icons/system-help.png',       helpTip),
                  (doClose, closeCmd, self.closePopup, closeText, 'icons/window-close.png',     closeTip),]
    
    for doAction, userCmd, defaultCmd, text, image, tipText in _doActions:
      if doAction:
        _callbacks.append(userCmd or defaultCmd)
        _tipTexts.append(tipText)
        _texts.append(text)
        
        if image:
          icon = Icon(image)
        else:
          icon = None  
        
        _icons.append(icon)       

    self.addButtons(_texts, _callbacks, _icons, _tipTexts)

  def duplicatePopup(self):
     
    if self.popup:
      try:
        newPopup = self.popup.__class__(self.popup.parent)
        x,y, w, h = self.getGeometry()
        newPopup.setGeometry(x+25, y+25, w, h)
      
      except:
        pass
  
  def launchHelp(self):
  
    if self.helpUrl and self.webBrowser:
      self.webBrowser.open(self.helpUrl)
      
    elif self.popup:
      from ccpn.ui.gui.widgets.WebView import WebViewPopup
      popup = WebViewPopup(self.popup, url=self.helpMsg or ccpnUrl + '/documentation')
  
  def closePopup(self):
  
    if self.popup:
      self.popup.close()
      
    else:
      self.destroy()  
  

if __name__ == '__main__':

  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.BasePopup import BasePopup
  from ccpn.ui.gui.popups.Dialog import CcpnDialog

  def callback(text):
    print('callback', text)

  texts = ['abc', 'def', 'ghi']
  callbacks = [lambda t=text: callback(t) for text in texts]
  icons = [None, None, 'icons/applications-system.png']

  app = TestApplication()
  popup = CcpnDialog(windowTitle='Test ButtonList')

  # popup.setSize(200,200)
  popup.setGeometry(200,200,200,200)

  buttons = ButtonList(parent=popup, texts=texts, callbacks=callbacks, icons=icons, grid=(2,2))
  # utils = UtilityButtonList(parent=popup, texts=texts, callbacks=callbacks, helpUrl=ccpnUrl+"/software")

  popup.show()
  popup.raise_()

  app.start()

