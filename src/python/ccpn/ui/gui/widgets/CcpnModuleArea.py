#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:07 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui, QtCore

from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from pyqtgraph.dockarea.Container import Container

ModuleArea = DockArea
Module = Dock

class CcpnModuleArea(ModuleArea):

  def __init__(self, mainWindow):
    super(CcpnModuleArea, self).__init__(mainWindow)
    # #GWV test to trace gridding issues
    # # remove the existing Vbox layout by transferring to a temp widget
    # QtGui.QWidget().setLayout(self.layout)  ## pyqtgraph stored the layout as self.layout
    # self.layout = QtGui.QGridLayout(self)
    # self.layout.setContentsMargins(0, 0, 0, 0)
    # self.layout.setSpacing(0)

    self.modules = self.docks
    self.moveModule = self.moveDock
    self.mainWindow = mainWindow  # a link back to the parent MainWindow
    self.setContentsMargins(0, 0, 0, 0)

  @property
  def currentModules(self) -> list:
    'return all current modules in area'
    if self is not None:
      modules = list(self.findAll()[1].values())
      return modules

  @property
  def currentModulesNames(self) -> list:
    'return the name of all current modules in area'
    if self is not None:
      modules = list(self.findAll()[1].keys())
      return modules

  @property
  def currentModulesDict(self):
    ''' returns {Class name : Name } of currently opened Modules. Used in restoring Layout '''
    modules = {}
    for moduleName, moduleObj in self.findAll()[1].items():
      # modules.update({moduleObj.__class__.__name__: moduleName})
      modules.update({moduleObj.className: moduleName})
    return modules

  @property
  def layoutState(self):
    ''' Returns a list in which the first argument is the current modules dict (see method) and the second argument 
    is the stase as pyqtGraph  '''
    return [self.currentModulesDict, self.saveState()]

  def switchModule(self, module1, module2):
    """
    switch the new module into the blankDisplay
    """
    pass

  def addModule(self, module, position=None, relativeTo=None, **kwds):
    """With these settings the user can close all the modules from the label 'close module' or pop up and
     when re-add a new module it makes sure there is a container available.
    """
    if module is None:
      raise RuntimeError('No module given')

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
#    self.modules[module.getName()] = module
    # explicitly calling the CcpnModule.name() method as GuiDisplay modules have their name masked by

    # ejb - I think there is a logic error here when adding a module
    #       that leaves the blank display without a parent

    from ccpn.ui.gui.modules.CcpnModule import CcpnModule
    self.modules[CcpnModule.name(module)] = module
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

  def _closeAll(self):
    for module in self.currentModules:
      module._closeModule()

  def saveState(self):
    """
    Return a serialized (storable) representation of the state of
    all Docks in this DockArea."""
    state = {'main': self.childState(self.topContainer), 'float': []}
    for a in self.tempAreas:
      geo = a.win.geometry()
      geo = (geo.x(), geo.y(), geo.width(), geo.height())
      state['float'].append((a.saveState(), geo))
    return state

  def childState(self, obj):
    if isinstance(obj, Dock):
      return ('dock', obj.name(), {})
    else:
      childs = []
      for i in range(obj.count()):
        childs.append(self.childState(obj.widget(i)))
      return (obj.type(), childs, obj.saveState())

  def restoreState(self, state):
    """
    Restore Dock configuration as generated by saveState.

    Note that this function does not create any Docks--it will only 
    restore the arrangement of an existing set of Docks.

    """

    ## 1) make dict of all docks and list of existing containers
    containers, docks = self.findAll()
    oldTemps = self.tempAreas[:]
    print ("found docks:", docks)

    # 2) create container structure, move docks into new containers
    self.buildFromState(state['main'], docks, self)

    ## 3) create floating areas, populate
    for s in state['float']:
      a = self.addTempArea()
      a.buildFromState(s[0]['main'], docks, a)
      a.win.setGeometry(*s[1])

    ## 4) Add any remaining docks to the bottom
    for d in docks.values():
      print('moduleName', d.moduleName)
      self.moveDock(d, 'below', None)

    # print "\nKill old containers:"
    ## 5) kill old containers
    for c in containers:
      if c is not None:
        c.close()
    for a in oldTemps:
      if a is not None:
        a.apoptose()

  def buildFromState(self, state, docks, root, depth=0):
    typ, contents, state = state
    pfx = "  " * depth
    if typ == 'dock':
      try:
        obj = docks[contents]
        del docks[contents]
      except KeyError:
        raise Exception('Cannot restore dock state; no dock with name "%s"' % contents)
    else:
      obj = self.makeContainer(typ)

    # if issubclass(root, Container):
    if hasattr(root, 'type'):
      root.insert(obj)
      print (pfx+"Add:", obj, " -> ", root)

    if typ != 'dock':
      for o in contents:
        self.buildFromState(o, docks, obj, depth + 1)
      obj.apoptose(propagate=False)
      obj.restoreState(state)  ## this has to be done later?

