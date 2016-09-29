
from PyQt4 import QtGui

from ccpn.ui.gui.widgets.Base import Base

class GroupBox(QtGui.QGroupBox, Base):

  def __init__(self, parent=None, border=None, **kw):

    QtGui.QGroupBox.__init__(self, parent)
    Base.__init__(self, **kw)

    if border:
      self.setObjectName("borderedGroupBox")
