"""
PulldownList widget

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:43 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtCore, QtGui

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Icon import Icon

from ccpn.util.Logging import getLogger
logger = getLogger()

NULL = object()


class PulldownList(QtGui.QComboBox, Base):

  def __init__(self, parent, texts=None, objects=None,
               icons=None, callback=None, index=0, **kw):

    QtGui.QComboBox.__init__(self, parent)
    Base.__init__(self, **kw)
    
    self.text = None
    self.object = None
    self.texts = []
    self.objects = []
    
    # self.setIconSize(QtCore.QSize(22,22))

    PulldownList.setData(self, texts, objects, index, icons)
    self.setCallback(callback)
    self.setStyleSheet("""
    PulldownList {
      padding-top: 3px;
      padding-bottom: 3px;
      padding-left: 2px;
    }
    """)
    self.connect(self, QtCore.SIGNAL('currentIndexChanged(int)'), self._callback)

  def showPopup(self):
    super(PulldownList, self).showPopup()

  def currentObject(self):

    if self.objects:
      index = self.currentIndex()
      if index >= 0:
        return self.objects[index]

  def currentData(self):

    return (self.currentText(),self.currentObject())
    
  def select(self, item):
    # Works with an object or a text

    index = None
    
    if item in self.texts:
      index = list(self.texts).index(item)

    elif item in self.objects:
      index = list(self.objects).index(item)

    if index is not None:
      self.setCurrentIndex(index)

  def set(self, item):

    self.select(item)

  def setSelected(self, item, doCallback=False):

    print("ccpn.ui.gui.widgets.PulldownList.setSelected is deprecated use; .select()")
    
    self.select(item)

  def setIndex(self, index):

    self.setCurrentIndex(index)
  
  def get(self):
    
    return self.currentObject()

  def getSelected(self):
  
    # print("ccpn.ui.gui.widgets.PulldownList.getSelected is deprecated use; .currentData()")

    return self.currentData()

  def getObject(self):
    
    # print("ccpn.ui.gui.widgets.PulldownList.getObject is deprecated use; .currentObject()")
    
    return self.currentObject()

  def getText(self):
    
    # print("ccpn.ui.gui.widgets.PulldownList.getText is deprecated use; .currentText()")
   
    return self.currentText()

  def getSelectedIndex(self):
    
    # print("ccpn.ui.gui.widgets.PulldownList.getSelectedIndex is deprecated use; .currentIndex()")

    return self.currentIndex()

  def setup(self):
    
    print("ccpn.ui.gui.widgets.PulldownList.setup is deprecated use; .setData")

    return self.currentIndex()
 
  def setData(self, texts=None, objects=None, index=None, icons=None):

    texts = texts or []
    objects = objects or []

    self.texts = []
    self.objects = []
    self.icons = []
    
    n = len(texts)
    
    if objects:
      msg = 'len(texts) = %d, len(objects) = %d'
      assert n == len(objects), msg % (n, len(objects))
      
    else:
      objects = texts[:]
    
    if icons:
      while len(icons) < n:
        icons.append(None)
        
    else:
      icons = [None] * n
    
    self.clear()
    for i, text in enumerate(texts):
      self.addItem(text, objects[i], icons[i])
    
    if index is not None:  
      self.setCurrentIndex(index)

  def addItem(self, text, object=NULL, icon=None):
    
    if icon:
      QtGui.QComboBox.addItem(self, Icon(icon), text)
    else:
      QtGui.QComboBox.addItem(self, text)
    
    if object is NULL:
      object = text
    
    self.texts.append(text)  
    self.objects.append(object)

  def setItemText(self, index, text):
  
    QtGui.QComboBox.setItemText(self, index, text)
    
    self.text[index] = text
  
  def removeItem(self, index):
  
    QtGui.QComboBox.removeItem(self, index)
    
    if index is self.index:
      self.index = None
      self.text = None
      self.object = None
    
    self.texts.pop(index)
    self.objects.pop(index)
    
  def disable(self):

    self.setDisabled(True)

  def enable(self):

    self.setEnabled(True)
  
  def setCallback(self, callback):
    
    self.callback = callback

  def _callback(self, index):
    
    if index < 0:
      return
    self.index = index
    
    if self.objects:
      self.object = self.objects[index]
    else:
      self.object = None
    
    if self.callback:
      if self.objects:
        self.callback(self.objects[index])
      elif self.texts:
        self.callback(self.texts[index])






if __name__ == '__main__':

  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.popups.Dialog import CcpnDialog
  
  app = TestApplication()

  texts =   ['Int','Float','String', '']
  objects = [int, float, str, 'Green']
  icons = [None, None, None, Icon(color='#008000')]

  def callback(object):
    print('callback', object)

  def callback2(object):
    print('callback2', object)

  popup = CcpnDialog(windowTitle='Test PulldownList', setLayout=True)
  #popup.setSize(250,50)
  policyDict = dict(
    vAlign='top',
    hPolicy = 'expanding',
  )
  policyDict = dict(
    vAlign='top',
   # hAlign='left',
  )
  #policyDict = dict(
  #   hAlign='left',
  # )
  #policyDict = {}

  pulldownList = PulldownList(parent=popup, texts=texts, icons=icons,
                              objects=objects, callback=callback, grid=(0,0), **policyDict
                              )
  pulldownList.insertSeparator(2)
  pulldownList.clearEditText()


  popup.show()
  popup.raise_()
  app.start()



