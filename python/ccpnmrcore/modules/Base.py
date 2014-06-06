from ccpncore.gui.Base import Base as GuiBase

class Base(GuiBase):
  
  def __init__(self, project, *args, **kw):
    
    self.project = project
    
    GuiBase.__init__(self, *args, **kw)
    
