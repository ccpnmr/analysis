from PyQt4 import QtCore, QtGui
from .Base import Base

class RadioButton(QtGui.QRadioButton, Base):

  def __init__(self, parent, text='', *args, **kw):
      
    QtGui.QRadioButton.__init__(self, text, parent)
    Base.__init__(self, parent, *args, **kw)

