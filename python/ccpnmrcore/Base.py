from ccpncore.gui.Base import Base as GuiBase

class Base(GuiBase):
  
  def __init__(self, project, *args, **kw):
    
    self.project = project
    
    GuiBase.__init__(self, *args, **kw)
    
  def getById(self, pid):

    print(pid)
    return self.project.getById(pid)

  def getObject(self, pidOrObject):
    
    return self.getById(pidOrObject) if type(pidOrObject) is type('') else pidOrObject
      