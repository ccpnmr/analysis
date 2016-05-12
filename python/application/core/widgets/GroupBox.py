
from PyQt4 import QtGui

from application.core.widgets.Base import Base

class GroupBox(QtGui.QGroupBox, Base):

  def __init__(self, parent=None, **kw):

    QtGui.QGroupBox.__init__(self, parent)
    Base.__init__(self, **kw)

