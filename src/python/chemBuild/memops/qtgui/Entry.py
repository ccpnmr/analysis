from PyQt5 import QtCore, QtGui, QtWidgets

from .Base import Base

from .Frame import Frame
from .Label import Label

# Width?
# Allow setting of max lengh based on data model?

import re

SPLIT_REG_EXP = re.compile(',?\s*')
SEPARATOR = ', '
MAXINT = 2**31-1
INFINITY = float('Inf')


class Entry(QtWidgets.QLineEdit, Base):

  def __init__(self, parent, text='', callback=None, maxLength=32, 
               listener=None, stripEndWhitespace=True, **kw):
    
    QtWidgets.QLineEdit.__init__(self, parent)
    Base.__init__(self, parent, **kw)
    
    self.setText(self.convertInput(text))
    self.setMaxLength(maxLength)
    
    self._isAltered = False
    self._stripEndWhitespace = stripEndWhitespace
    self.callback = callback
    
    self.textChanged.connect(self._changed)
    self.returnPressed.connect(self._callback)
    self.editingFinished.connect(self._callback)

    # self.connect(self, QtCore.SIGNAL('returnPressed()'), self._callback)
    # self.connect(self, QtCore.SIGNAL('editingFinished()'), self._callback)
      
    if listener:
      if isinstance(listener, (set, list, tuple)):
        for signal in listener:
          signal.connect(self.set)
        
      else:
        listener.connect(self.set)
  
  def _callback(self):
    
    if self.callback and self._isAltered:
      self.callback(self.get())
      self._isAltered = False
  
  def _changed(self):

    self._isAltered = True
  
  def convertText(self, text):
    # Overwritten in subclasses to make float, int etc
    
    if self._stripEndWhitespace:
      text = text.strip()
    
    return text or None

  def convertInput(self, value):
    # Overwritten in subclasses to convert float, int
    
    return value or ''
  
  def get(self):
    
    return self.convertText(self.text())
    
  def set(self, value, doCallback=True):
    
    self.setText(self.convertInput(value))
    
    if doCallback:
      self._callback()

class IntEntry(Entry):

  def __init__(self, parent, text=0, callback=None,
               minValue=-MAXINT, maxValue=MAXINT,  **kw):  
    
    Entry.__init__(self, parent, text, callback, **kw)
   
    valid = QtGui.QIntValidator(minValue, maxValue, self)
    self.setValidator(valid)

  def convertText(self, text):
    
    if not text:
      return None
    else:
      return int(text)

  def convertInput(self, value):
    
    if value is None:
      return ''
    else:
      return str(value)

  def setRange(self, minValue=-MAXINT, maxValue=MAXINT):
  
    valid = QtGui.QIntValidator(minValue, maxValue, self)
    self.setValidator(valid)
    

class FloatEntry(Entry):
  
  decimals = 4
  
  def __init__(self, parent, text=0.0, callback=None,
               minValue=-INFINITY, maxValue=INFINITY,
               decimals=4, **kw):  

    Entry.__init__(self, parent, text, callback, **kw)
    
    self.decimals = decimals
    self.setText(self.convertInput(text))
    
    valid = QtGui.QDoubleValidator(minValue, maxValue, decimals, self)
    self.setValidator(valid)

  def convertText(self, text):
    
    if not text:
      return None
    else:
      return float(text)

  def convertInput(self, value):
    
    if value is None:
      text = ''
    elif value == 0:
      text = '0.0'
    elif abs(value) > 999999 or abs(value) < 0.00001:
      format = '%%.%de' % (self.decimals)
      text = format % value
    else:
      format = '%%.%df' % (self.decimals)
      text = format % value   
       
    return text

  def setRange(self, minValue=-INFINITY, maxValue=INFINITY):
  
    valid = QtGui.QIntValidator(minValue, maxValue, self)
    self.setValidator(valid)

class RegExpEntry(Entry):

  def __init__(self, parent, text='', callback=None, **kw):  
    
    Entry.__init__(self, parent, text, callback, **kw)
    
    self.setValidator(QtGui.QRegExpValidator)


class ArrayEntry(Entry):

  def __init__(self, parent, text='', callback=None, **kw):  
    
    Entry.__init__(self, parent, text, callback, **kw)
  
  def convertText(self, text):
  
    return re.split(SPLIT_REG_EXP, text) or []
  
  def convertInput(self, array):
  
    return SEPARATOR.join(array)


class IntArrayEntry(IntEntry):

  def __init__(self, parent, text='', callback=None, **kw):  
    
    IntEntry.__init__(self, parent, text, callback, **kw)
  
  def convertText(self, text):
  
    array = re.split(SPLIT_REG_EXP, text) or []
    return  [IntEntry.convertText(self, x) for x in array]
  
  def convertInput(self, values):
    
    texts = [IntEntry.convertInput(self, x) for x in values]
    return SEPARATOR.join(texts)


class FloatArrayEntry(FloatEntry):

  def __init__(self, parent, text='', callback=None, **kw):  
    
    FloatEntry.__init__(self, parent, text, callback, **kw)
  
  def convertText(self, text):
  
    array = re.split(SPLIT_REG_EXP, text) or []
    return  [FloatEntry.convertText(self, x) for x in array]
  
  def convertInput(self, values):
    
    texts = [FloatEntry.convertInput(self, x) for x in values]
    return SEPARATOR.join(texts)

class LabeledEntry(Frame):

  def __init__(self, parent, labelText, entryText='', callback=None, maxLength=32,  tipText=None, **kw):  
    
    Frame.__init__(self, parent, tipText=tipText, **kw)
  
    self.label = Label(self, labelText, tipText=tipText, grid=(0,0))
    self.entry = Entry(self, entryText, callback, maxLength,
                       tipText=tipText, grid=(0,1))
    
  def getLabel(self):

    return self.label.get()

  def setLabel(self, text):

    self.label.set(text)

  def getEntry(self):

    return self.entry.get()

  def setEntry(self, text):

    self.entry.set(text)

class LabeledIntEntry(LabeledEntry):

  def __init__(self, parent, labelText, entryText='', callback=None,
               minValue=-MAXINT, maxValue=MAXINT,  tipText=None, **kw):  
    
    Frame.__init__(self, parent, tipText=tipText, **kw)
  
    self.label = Label(self, labelText, tipText=tipText, grid=(0,0))
    self.entry = IntEntry(self, entryText, callback, minValue,
                          maxValue, tipText=tipText, grid=(0,1))


class LabeledFloatEntry(LabeledEntry):

  def __init__(self, parent, labelText, entryText='', callback=None,
               minValue=-MAXINT, maxValue=MAXINT, decimals=4, tipText=None, **kw):  
    
    Frame.__init__(self, parent, tipText=tipText, **kw)
  
    self.label = Label(self, labelText, tipText=tipText, grid=(0,0))
    self.entry = FloatEntry(self, entryText, callback, minValue,
                            maxValue, decimals, tipText=tipText, grid=(0,1))


if __name__ == '__main__':

  from .Application import Application

  app = Application()

  window = QtWidgets.QWidget()
  
  def callback(value):
    print("Callback", value)
  
  Entry(window, 'Start Text', callback)
  
  ArrayEntry(window, ['A','C','D','C'], callback)
  
  IntEntry(window, 123, callback)
  
  IntArrayEntry(window,  [4, 5, 6, 7], callback)
  
  FloatEntry(window, 2.818, callback)
  
  e = FloatArrayEntry(window, [1,2,4], callback, decimals=2)
  e.set([1e12, -0.7e-5, 9.75])
  
  LabeledEntry(window, 'Text:', 'Initial val', callback)
  
  LabeledIntEntry(window, 'Int:', 0, callback)
  
  LabeledFloatEntry(window, 'Float:', 0.7295, callback, decimals=8)
  
  window.show()
  
  app.start()

