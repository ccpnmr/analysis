from PyQt4 import QtGui
from pyqtgraph.dockarea.DockArea import DockArea
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.Container import Container, TContainer, HContainer, VContainer
from ccpn.ui.gui.widgets.Module import CcpnModule


ModuleArea = DockArea
Module = Dock

class CcpnModuleArea(ModuleArea):
  def __init__(self, **kw):
    super(CcpnModuleArea, self).__init__(self)
    self.modules = self.docks
    self.moveModule = self.moveDock
    # self.closeModule = self.closeDock


  def addModule(self, module=None, position=None, relativeTo=None, **kwds):
    """With these settings the user can close all the modules from the label 'close module' or pop up and
     when re-add a new module it makes sure there is a container available.
    """

    if module is None:
      module = CcpnModule(name='New Module',**kwds)

    if position is None:
      position = 'top'

    if position == 'bottom':
      self.checkPythonConsole()


    neededContainer = {
        'bottom': 'vertical',
        'top': 'vertical',
        'left': 'horizontal',
        'right': 'horizontal',
        'above': 'tab',
        'below': 'tab'
        }[position]




    if relativeTo is None:
      neighbor = None
      container = self.addContainer(neededContainer, self.topContainer)

    ## Determine the container to insert this module into.
    ## If there is no neighbor, then the container is the top.
    if relativeTo is None or relativeTo is self:
      if self.topContainer is None:
        container = self
        neighbor = None
      else:
        container = self.topContainer
        neighbor = None
    else:
      if isinstance(relativeTo, str):
          relativeTo = self.modules[relativeTo]
      container = self.getContainer(relativeTo)
      neighbor = relativeTo


    if neededContainer != container.type() and container.type() == 'tab':
        neighbor = container
        container = container.container()

    if neededContainer != container.type():

        if neighbor is None:
          container = self.addContainer(neededContainer, self.topContainer)
        else:
          container = self.addContainer(neededContainer, neighbor)

    insertPos = {
        'bottom': 'after',
        'top': 'before',
        'left': 'before',
        'right': 'after',
        'above': 'before',
        'below': 'after'
    }[position]
    if container is not None:
      container.insert(module, insertPos, neighbor)
    else:
      container = self.topContainer
      container.insert(module, insertPos, neighbor)
    module.area = self
    self.modules[module.name()] = module
    # self.movePythonConsole()
    return module

  # def movePythonConsole(self):
  #   if 'PYTHON CONSOLE' in self.findAll()[1]:
  #     pythonConsole = self.findAll()[1]['PYTHON CONSOLE']
  #     for container in self.findAll()[0]:
  #       if container and pythonConsole is not None:
  #         self.moveModule(pythonConsole, 'bottom', container)
  #
  # def makeContainer(self, typ):
  #   if typ == 'vertical':
  #     new = VContainer(self)
  #   elif typ == 'horizontal':
  #     new = HContainer(self)
  #   elif typ == 'tab':
  #     new = TContainer(self)
  #   return new


  def apoptose(self):
    if self.temporary and self.topContainer.count() == 0:
      self.topContainer = None
      if self.home:
        self.home.removeTempArea(self)

  def checkPythonConsole(self):
    if 'PYTHON CONSOLE' in self.findAll()[1]:
      pythonConsole = self.findAll()[1]['PYTHON CONSOLE']
      # for c in self.findAll()[0]:
      #   if c and pythonConsole is not None:
      #     print(c, 'Testing')

