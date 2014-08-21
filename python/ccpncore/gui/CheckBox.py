__author__ = 'simon'

import ast

from PySide import QtGui, QtCore

from ccpncore.gui.Base import Base

class CheckBox(QtGui.QCheckBox, Base):

  def __init__(self, parent, checked=False, **kw):

    QtGui.QCheckBox.__init__(self, parent, checked)
    self.setChecked(ast.literal_eval(checked))
    Base.__init__(self, **kw)

