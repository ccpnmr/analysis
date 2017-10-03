from PyQt5 import QtCore, QtGui, QtWidgets
from .Base import Base

class RadioButton(QtWidgets.QRadioButton, Base):

  def __init__(self, parent, text='', *args, **kw):
      
    QtWidgets.QRadioButton.__init__(self, text, parent)
    Base.__init__(self, parent, *args, **kw)

