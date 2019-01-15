#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:51 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtCore
from ccpn.core.Spectrum import Spectrum
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea, DockDrop
from pyqtgraph.dockarea.Container import Container
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.lib.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.SideBar import NewSideBar      #,SideBar
from ccpn.ui.gui.lib.MenuActions import _openItemObject
from ccpn.ui.gui.widgets.Font import Font
from ccpn.ui.gui.widgets.MainWindow import MainWindow
from ccpn.ui.gui.lib.GuiWindow import GuiWindow
from ccpn.ui.gui.guiSettings import getColours, LABEL_FOREGROUND
from ccpn.util.Colour import hexToRgb
from ccpn.ui.gui.lib.mouseEvents import SELECT
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from ccpn.ui.gui.widgets.PlaneToolbar import _StripLabel
from functools import partial


ModuleArea = DockArea
Module = Dock
DropAreaLabel = 'Drop Area'
Failed = 'Failed'
MODULEAREA_IGNORELIST = (ToolBar, _StripLabel)


class TempAreaWindow(GuiWindow, MainWindow):
    def __init__(self, area, mainWindow=None, **kwargs):
        MainWindow.__init__(self, **kwargs)
        GuiWindow.__init__(self, mainWindow.application)
        self.setCentralWidget(area)
        self.tempModuleArea = area
        self.mainModuleArea = self.tempModuleArea.home

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current
        # self._startCommandEchoBlock = self.project._startCommandEchoBlock
        # self._endCommandEchoBlock = self.project._endCommandEchoBlock

        self._setShortcuts()
        self.setMouseMode(SELECT)

    def closeEvent(self, *args, **kwargs):
        for module in self.tempModuleArea.ccpnModules:
            module._closeModule()
        if self.tempModuleArea in self.mainModuleArea.tempAreas:
            self.mainModuleArea.tempAreas.remove(self.tempModuleArea)
        self.close()
        # MainWindow.closeEvent(self, *args, **kwargs)


class CcpnModuleArea(ModuleArea, DropBase):  #, DropBase):

    def __init__(self, mainWindow, **kwargs):

        ModuleArea.__init__(self, mainWindow, **kwargs)
        DropBase._init(self, acceptDrops=True)

        self.mainWindow = mainWindow  # a link back to the parent MainWindow

        self.modules = self.docks
        self.moveModule = self.moveDock
        self.setContentsMargins(0, 0, 0, 0)
        self.currentModuleNames = []
        self._modulesNames = {}
        self._ccpnModules = []

        # self.setAcceptDrops(True) GWV not needed; handled by DropBase init

        self.textLabel = DropAreaLabel
        self.fontLabel = Font('Helvetica', 36, bold=False)

        colours = getColours()
        self.colourLabel = hexToRgb(colours[LABEL_FOREGROUND])

        self._dropArea = None  # Needed to know where to add a newmodule when dropping a pid from sideBar
        if self._container is None:
            for i in self.children():
                if isinstance(i, Container):
                    self._container = i

        # self.label.sigDragEntered.connect(self._dragEntered)

    # def _dragEntered(self, module):
    #   # print('>>>sigDragEntered from:', module)
    #   # for mod in self.modules.values():
    #   #   mod.setWidgetTransparency(True)
    #
    #   self.update()
    #
    # def _dragFinished(self, ev):
    #   # print('>>>sigDragFinished', self)
    #   # for mod in self.modules.values():
    #   #   mod.setWidgetTransparency(False)
    #   pass

    def dropEvent(self, event, *args):
        data = self.parseEvent(event)
        source = event.source()

        # drop an item from the sidebar onto the drop area
        if DropBase.PIDS in data and isinstance(data['event'].source(), NewSideBar):      #(SideBar, NewSideBar)):
            pids = data[DropBase.PIDS]
            objs = [self.mainWindow.project.getByPid(pid) for pid in pids]
            _openItemObject(self.mainWindow, objs, position=self.dropArea)

            # # reset the dock area
            # self.dropArea = None
            # self.overlay.setDropArea(self.dropArea)

        elif DropBase.URLS in data:
            objs = self.mainWindow._newSideBar._processDroppedItems(data)
            spectra = [obj for obj in objs if isinstance(obj, Spectrum)]
            _openItemObject(self.mainWindow, spectra, position=self.dropArea)

            # # reset the dock area
            # self.dropArea = None
            # self.overlay.setDropArea(self.dropArea)

        if hasattr(source, 'implements') and source.implements('dock'):
            DockArea.dropEvent(self, event, *args)

        # reset the dock area
        self.dropArea = None
        self.overlay.setDropArea(self.dropArea)

        event.accept()

    def dragEnterEvent(self, *args):
        event = args[0]
        data = self.parseEvent(event)

        if DropBase.PIDS in data and isinstance(data['event'].source(), NewSideBar):      #(SideBar, NewSideBar)):
            DockArea.dragEnterEvent(self, *args)
            event.accept()
        else:
            if isinstance(data['source'], MODULEAREA_IGNORELIST):
                event.ignore()
            else:
                DockDrop.dragEnterEvent(self, *args)
                event.accept()

    def dragLeaveEvent(self, *args):
        event = args[0]
        DockArea.dragLeaveEvent(self, *args)
        event.accept()

    def dragMoveEvent(self, *args):
        event = args[0]
        DockArea.dragMoveEvent(self, *args)
        event.accept()

    def _paint(self, ev):
        p = QtGui.QPainter(self)
        # set font
        p.setFont(self.fontLabel)
        # set colour
        p.setPen(QtGui.QColor(*self.colourLabel))

        # set size
        rgn = self.contentsRect()
        rgn = QtCore.QRect(rgn.left(), rgn.top(), rgn.width(), rgn.height())
        align = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter
        self.hint = p.drawText(rgn, align, DropAreaLabel)
        p.end()

    def paintEvent(self, ev):
        """
        Draws central label
        """
        if not self.ccpnModules:
            self._paint(ev)

        elif len(self.ccpnModules) == len(self._tempModules()):
            # means all modules are popuout, so paint the label in the mai module area
            self._paint(ev)

    def _updateModuleNames(self):
        for module in self.ccpnModules:
            self._setSerial(module)

    def _setSerial(self, module):
        if module.className in self._modulesNames:
            if [m.className for m in self.ccpnModules].count(module.className) == 0:
                self._modulesNames[module.className] = []
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

    def _tempModules(self):
        ''':return list of modules in temp Areas '''
        return [a.ccpnModules for a in self.tempAreas]

    def addModule(self, module, position=None, relativeTo=None, **kwds):
        """With these settings the user can close all the modules from the label 'close module' or pop up and
         when re-add a new module it makes sure there is a container available.
        """
        self._updateModuleNames()

        if not module._restored:
            if not isinstance(module, GuiSpectrumDisplay):  #
                self._setSerial(module)
                newName = module.titleName + module._nameSplitter + str(module.serial)
                module.rename(newName)

        # test that only one instance of the module is opened
        if hasattr(type(module), '_alreadyOpened'):
            _alreadyOpened = getattr(type(module), '_alreadyOpened')

            if _alreadyOpened is True:
                if hasattr(type(module), '_onlySingleInstance'):
                    getLogger().warning('Only one instance of %s allowed' % str(module.name))
                    return
            setattr(type(module), '_alreadyOpened', True)
            setattr(type(module), '_currentModule', module)  # remember the module

        if module is None:
            raise RuntimeError('No module given')

        if position is None:
            position = 'top'

        neededContainer = {
            'bottom': 'vertical',
            'top'   : 'vertical',
            'left'  : 'horizontal',
            'right' : 'horizontal',
            'above' : 'tab',
            'below' : 'tab'
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
            'top'   : 'before',
            'left'  : 'before',
            'right' : 'after',
            'above' : 'before',
            'below' : 'after'
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
        self.modules[module.name()] = module  # ejb - testing
        # self.movePythonConsole()
        if self.mainWindow is not None:
            self.mainWindow.application.ccpnModules = self.ccpnModules

        # module.label.sigDragEntered.connect(self._dragEntered)
        return module

    def getContainer(self, obj):
        if obj is None:
            return self
        if obj.container() is None:
            for i in self.children():
                if isinstance(i, Container):
                    self._container = i
        return obj.container()

    def apoptose(self):
        if self.temporary and self.topContainer.count() == 0:
            self.topContainer = None
            if self.home:
                self.home.removeTempArea(self)

    def _closeOthers(self, moduleToClose):
        modules = [module for module in self.ccpnModules if module != moduleToClose]
        for module in modules:
            module._closeModule()

    def _closeAll(self):
        for module in self.ccpnModules:
            module._closeModule()

    def saveState(self):
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
            getLogger().warning('Impossible to save layout. %s' % e)
        return state

    def childState(self, obj):

        if isinstance(obj, Dock):
            return ('dock', obj.name(), obj.widgetsState)
        else:
            childs = []
            if obj is not None:
                for i in range(obj.count()):
                    childs.append(self.childState(obj.widget(i)))
                return (obj.type(), childs, obj.saveState())

    def addTempArea(self):
        if self.home is None:
            area = CcpnModuleArea(mainWindow=self.mainWindow)
            area.temporary = True
            area.home = self
            self.tempAreas.append(area)
            win = TempAreaWindow(area, mainWindow=self.mainWindow)
            area.win = win
            win.show()
        else:
            area = self.home.addTempArea()
        # print "added temp area", area, area.window()
        return area

    def restoreState(self, state):
        """
        Restore Dock configuration as generated by saveState.

        Note that this function does not create any Docks--it will only
        restore the arrangement of an existing set of Docks.

        """
        modulesNames = [m.name() for m in self.ccpnModules]

        if 'main' in state:
            ## 1) make dict of all docks and list of existing containers
            containers, docks = self.findAll()
            oldTemps = self.tempAreas[:]
            if state['main'] is not None:
                # 2) create container structure, move docks into new containers
                self._buildFromState(modulesNames, state['main'], docks, self)

            ## 3) create floating areas, populate
            for s in state['float']:
                a = self.addTempArea()
                # a._buildFromState = self._buildFromState
                a._buildFromState(modulesNames, s[0]['main'], docks, a)
                a.win.setGeometry(*s[1])

            ## 4) Add any remaining docks to the bottom
            for d in docks.values():
                self.moveDock(d, 'below', None)

            # print "\nKill old containers:"
            ## 5) kill old containers
            # if is not none  delete
            if state['main'] is not None:
                for c in containers:
                    if c is not None:
                        c.close()
            for a in oldTemps:
                if a is not None:
                    a.apoptose()

            for d in self.ccpnModules:
                if d:
                    if d.className == Failed:
                        d.close()
                        getLogger().warning('Failed to restore: %s' % d.name())

    def _buildFromState(self, openedModulesNames, state, docks, root, depth=0):
        typ, contents, state = state
        pfx = "  " * depth
        if typ == 'dock':
            # try:
            if contents in openedModulesNames:
                obj = docks[contents]
                obj.restoreWidgetsState(**state)
                del docks[contents]
            else:
                obj = CcpnModule(self.mainWindow, contents)
                obj.className = Failed
                label = Label(obj, 'Failed to restore %s' % contents)
                obj.addWidget(label)
                self.addModule(obj)

            # except KeyError:
            #   raise Exception('Cannot restore dock state; no dock with name "%s"' % contents)
        else:
            obj = self.makeContainer(typ)

        # if issubclass(root, Container):
        if hasattr(root, 'type'):
            root.insert(obj)

        if typ != 'dock':
            for o in contents:
                self._buildFromState(openedModulesNames, o, docks, obj, depth + 1)
            obj.apoptose(propagate=False)
            obj.restoreState(state)  ## this has to be done later?
