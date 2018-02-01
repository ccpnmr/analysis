#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:51 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.util.Constants import ccpnmrJsonData
from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup

from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea, DockDrop
from pyqtgraph.dockarea.Container import Container
from pyqtgraph.dockarea.DockArea import TempAreaWindow
from ccpn.util.Logging import getLogger
import collections
from ccpn.ui.gui.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.widgets.SideBar import OpenObjAction, _openItemObject
from ccpn.ui.gui.widgets.Font import Font
from ccpn.ui.gui.guiSettings import getColourScheme, getColours, LabelFG
from ccpn.util.Colour import  hexToRgb

ModuleArea = DockArea
Module = Dock
DropAreaLabel = 'Drop Area'

class CcpnModuleArea(ModuleArea, DropBase):   #, DropBase):

  def __init__(self, mainWindow):
    # super(CcpnModuleArea, self).__init__(mainWindow)
    ModuleArea.__init__(self, mainWindow)
    DropBase.__init__(self, acceptDrops=True)
    # DropBase.__init__(self, acceptDrops=True)

    # #GWV test to trace gridding issues
    # # remove the existing Vbox layout by transferring to a temp widget
    # QtWidgets.QWidget().setLayout(self.layout)  ## pyqtgraph stored the layout as self.layout
    # self.layout = QtWidgets.QGridLayout(self)
    # self.layout.setContentsMargins(0, 0, 0, 0)
    # self.layout.setSpacing(0)

    self.modules = self.docks
    self.moveModule = self.moveDock
    self.mainWindow = mainWindow  # a link back to the parent MainWindow
    self.setContentsMargins(0, 0, 0, 0)
    self.currentModuleNames = []
    self._modulesNames = {}
    self._ccpnModules = []

    self.setAcceptDrops(True)

    self.textLabel = DropAreaLabel
    self.fontLabel = Font('Helvetica', 36, bold=False)
    colours = getColours()
    textColour = colours[LabelFG]
    self.colourLabel = hexToRgb(textColour)
    self._dropArea  = None # Needed to know where to add a newmodule when dropping a pid from sideBar


  # def dragMoveEvent(self, event:QtGui.QMouseEvent):
  #   event.accept()
  #
  # def dragLeaveEvent(self, event):
  #   # print ('>>>dragLeaveEvent %s' % str(event.type()))
  #   super(CcpnModuleArea, self).dragLeaveEvent(event)
  #   event.accept()
  #

  def dropEvent(self, event, *args):
    data = self.parseEvent(event)
    source = event.source()

    if DropBase.PIDS in data:
      pids = data[DropBase.PIDS]
      objs = [self.mainWindow.project.getByPid(pid) for pid in pids]
      _openItemObject(self.mainWindow, objs, position=self.dropArea)

      # reset the dock area
      self.dropArea = None
      self.overlay.setDropArea(self.dropArea)

    elif DropBase.URLS in data:
      self.mainWindow.sideBar._processDroppedItems(data)

      # reset the dock area
      self.dropArea = None
      self.overlay.setDropArea(self.dropArea)

    if hasattr(source, 'implements') and source.implements('dock'):
      DockArea.dropEvent(self, event, *args)

    event.accept()

  def dragEnterEvent(self, *args):
    event = args[0]
    DockArea.dragEnterEvent(self, *args)
    event.accept()

  def dragLeaveEvent(self, *args):
    event = args[0]
    DockArea.dragLeaveEvent(self, *args)
    event.accept()

  def dragMoveEvent(self, *args):
    event = args[0]
    DockArea.dragMoveEvent(self, *args)
    event.accept()


  # def _handlePid(self, pid):
  #   "handle a; return True in case it is a Spectrum or a SpectrumGroup"
  #   success = False
  #   obj = self.mainWindow.project.getByPid(pid)
  #   print(pid)
  #   if obj is not None and isinstance(obj, Spectrum):
  #     spectrumDisplay = self._createSpectrumDisplay(obj)
  #     self.current.strip = spectrumDisplay.strips[0]
  #     if obj.dimensionCount == 1:
  #       self.current.strip.plotWidget.autoRange()
  #     success = True
  #   elif obj is not None and isinstance(obj, SpectrumGroup):
  #     self._handleSpectrumGroup(obj)
  #     success = True
  #   return success

  # def _createSpectrumDisplay(self, spectrum):
  #   spectrumDisplay = self.mainWindow.createSpectrumDisplay(spectrum)
  #   # TODO:LUCA: the mainWindow.createSpectrumDisplay should do the reporting to console and log
  #   # This routine can then be ommitted and the call above replaced by the one remaining line
  #   self.mainWindow.pythonConsole.writeConsoleCommand(
  #     "application.createSpectrumDisplay(spectrum)", spectrum=spectrum)
  #   self.mainWindow.pythonConsole.writeConsoleCommand("application.deleteBlankDisplay()")
  #   getLogger().info('spectrum = project.getByPid(%r)' % spectrum.id)
  #   getLogger().info('application.createSpectrumDisplay(spectrum)')
  #
  #   return spectrumDisplay
  #
  # def _handleSpectrumGroup(self, spectrumGroup):
  #   '''displays spectrumGroup on spectrumDisplay. It creates the display based on the first spectrum of the group.
  #   Also hides the spectrumToolBar and shows spectrumGroupToolBar '''
  #
  #   if len(spectrumGroup.spectra) > 0:
  #     spectrumDisplay = self.mainWindow.createSpectrumDisplay(spectrumGroup.spectra[0])
  #     for spectrum in spectrumGroup.spectra: # Add the other spectra
  #       spectrumDisplay.displaySpectrum(spectrum)
  #     spectrumDisplay.isGrouped = True
  #     spectrumDisplay.spectrumToolBar.hide()
  #     spectrumDisplay.spectrumGroupToolBar.show()
  #     spectrumDisplay.spectrumGroupToolBar._addAction(spectrumGroup)
  #     self.current.strip = spectrumDisplay.strips[0]
  #     if spectrumGroup.spectra[0].dimensionCount == 1:
  #       self.current.strip.plotWidget.autoRange()

  def paintEvent(self, ev):
    """
    Draws central label
    """

    p = QtGui.QPainter(self)

    # set font
    p.setFont(self.fontLabel)

    # set colour
    p.setPen(QtGui.QColor(*self.colourLabel))

     # set size
    rgn = self.contentsRect()
    rgn = QtCore.QRect(rgn.left(), rgn.top(), rgn.width(), rgn.height())
    align  = QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter
    self.hint = p.drawText(rgn, align, DropAreaLabel)
    p.end()

  def _updateModuleNames(self):
    for module in self.ccpnModules:
      self._setSerial(module)

  def _setSerial(self, module):
    if module.className in self._modulesNames:
      if isinstance(self._modulesNames[module.className], list):
        self._modulesNames[module.className].append(module.name())
    else:
      self._modulesNames.update({module.className: [module.name()]})

    if module.className in self._modulesNames:
      if not module.serial:
        module.serial = len(list(set(self._modulesNames[module.className])))




  @property
  def ccpnModules(self) -> list:
    'return all current modules in area'
    return self._ccpnModules
    # if self is not None:
    #   modules = list(self.findAll()[1].values())
    #   return modules

  @ccpnModules.getter
  def ccpnModules(self):
    if self is not None:
      ccpnModules = list(self.findAll()[1].values())
      return ccpnModules

  def repopulateModules(self):
    """
    Repopulate all modules to globally refresh all pulldowns, etc.
    """
    modules = self.ccpnModules
    for module in modules:
      if hasattr(module, '_repopulateModule'):
        module._repopulateModule()
    pass

  def switchModule(self, module1, module2):
    """
    switch the new module into the blankDisplay
    """
    pass



  def addModule(self, module, position=None, relativeTo=None, **kwds):
    """With these settings the user can close all the modules from the label 'close module' or pop up and
     when re-add a new module it makes sure there is a container available.
    """
    self._updateModuleNames()

    if not module._restored:
      if not isinstance(module, GuiSpectrumDisplay):  #
        self._setSerial(module)
        newName = module.titleName+module._nameSplitter+str(module.serial)
        module.rename(newName)


    # test that only one instance of the module is opened
    if hasattr(type(module), '_alreadyOpened'):
      _alreadyOpened = getattr(type(module), '_alreadyOpened')

      if _alreadyOpened is True:
        if hasattr(type(module), '_onlySingleInstance'):
          getLogger().warning('Only one instance of %s allowed' % str(module.name))
          return
      setattr(type(module), '_alreadyOpened', True)
      setattr(type(module), '_currentModule', module)    # remember the module

    if module is None:
      raise RuntimeError('No module given')

    if position is None:
      position = 'top'

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
    else:
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

    # from ccpn.ui.gui.modules.CcpnModule import CcpnModule
    # self.modules[CcpnModule.name(module)] = module
    self.modules[module.name()] = module                # ejb - testing
    # self.movePythonConsole()
    self.mainWindow.application.ccpnModules = self.ccpnModules
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

  def _closeAll(self):
    for module in self.ccpnModules:
      module._closeModule()

  def saveState(self):
    # FIXME. Crashes if no modules
    """
    Return a serialized (storable) representation of the state of
    all Docks in this DockArea."""
    state = {}
    try:
      state = {'main': self.childState(self.topContainer), 'float': []}
      for a in self.tempAreas:
        if a is not None:
          geo = a.win.geometry()
          geo = (geo.x(), geo.y(), geo.width(), geo.height())
          state['float'].append((a.saveState(), geo))
    except Exception as e:
      getLogger().warning('Impossible to save layout. %s' %e)
    return state

  def childState(self, obj):

    if isinstance(obj, Dock):
      return ('dock', obj.name(), {})
    else:
      childs = []
      if obj is not None:
        for i in range(obj.count()):
          childs.append(self.childState(obj.widget(i)))
        return (obj.type(), childs, obj.saveState())


  def restoreState(self, state):
    """
    Restore Dock configuration as generated by saveState.

    Note that this function does not create any Docks--it will only 
    restore the arrangement of an existing set of Docks.

    """
    if 'main' in state:
      ## 1) make dict of all docks and list of existing containers
      containers, docks = self.findAll()
      oldTemps = self.tempAreas[:]

      # 2) create container structure, move docks into new containers
      self.buildFromState(state['main'], docks, self)

      ## 3) create floating areas, populate
      for s in state['float']:
        a = self.addTempArea()
        a.buildFromState(s[0]['main'], docks, a)
        a.win.setGeometry(*s[1])

      ## 4) Add any remaining docks to the bottom
      for d in docks.values():
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


    if typ != 'dock':
      for o in contents:
        self.buildFromState(o, docks, obj, depth + 1)
      obj.apoptose(propagate=False)
      obj.restoreState(state)  ## this has to be done later?


