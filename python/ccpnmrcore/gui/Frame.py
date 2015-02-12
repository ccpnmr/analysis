from PySide import QtGui

from ccpncore.gui.Frame import Frame as CoreFrame
from ccpnmrcore.Base import Base as GuiBase

class Frame(CoreFrame, GuiBase):

  def __init__(self, parent=None, **kw):

    CoreFrame.__init__(self, parent)
    GuiBase.__init__(self, **kw)

