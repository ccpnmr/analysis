"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
__author__ = 'simon'

from PySide import QtCore, QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.Icon import Icon

# TBD: Cascading categories, prob via Menu

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
    
    self.setIconSize(QtCore.QSize(22,22))
    
    PulldownList.setData(self, texts, objects, index, icons)
    self.setCallback(callback)

    self.connect(self, QtCore.SIGNAL('currentIndexChanged(int)'), self._callback)

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

    print("ccpncore.gui.PulldownList.setSelected is depecated use; .select()")
    
    self.select(item)

  def setIndex(self, index):

    self.setCurrentIndex(index)
  
  def get(self):
    
    return self.currentObject()

  def getSelected(self):
  
    print("ccpncore.gui.PulldownList.getSelected is depecated use; .currentData()")

    return self.currentData()

  def getObject(self):
    
    print("ccpncore.gui.PulldownList.getObject is depecated use; .currentObject()")
    
    return self.currentObject()

  def getText(self):
    
    print("ccpncore.gui.PulldownList.getText is depecated use; .currentText()")
   
    return self.currentText()

  def getSelectedIndex(self):
    
    print("ccpncore.gui.PulldownList.getSelectedIndex is depecated use; .currentIndex()")

    return self.currentIndex()

  def setup(self):
    
    print("ccpncore.gui.PulldownList.setup is depecated use; .setData")

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

  from ccpncore.gui.Application import TestApplication
  from ccpncore.gui.BasePopup import BasePopup
  
  app = TestApplication()

  texts = ['Int','Float','String', '']
  objects = [int, float, str, 'Green']
  icons = [None, None, None, Icon(color='#008000')]

  def callback(object):
    print('callback', object)

  popup = BasePopup(title='Test PulldownList')
  popup.setSize(250,50)
  pulldownList = PulldownList(parent=popup, texts=texts, icons=icons,
                              objects=objects, callback=callback)
  pulldownList.clearEditText()
  app.start()

