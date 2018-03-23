"""
This file contains CcpnModule base class
modified by Geerten 1-12/12/2016
"""
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:43 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2016-07-09 14:17:30 +0100 (Sat, 09 Jul 2016) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets
from weakref import ref

from ccpn.ui.gui.widgets.DropBase import DropBase
from pyqtgraph.dockarea.Container import Container
from pyqtgraph.dockarea.DockDrop import DockDrop
from pyqtgraph.dockarea.Dock import DockLabel, Dock
from pyqtgraph.dockarea.DockArea import TempAreaWindow

from ccpn.ui.gui.guiSettings import getColours, CCPNMODULELABEL_BACKGROUND, CCPNMODULELABEL_FOREGROUND
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.guiSettings import moduleLabelFont
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.SideBar import SideBar
from ccpn.ui.gui.widgets.Frame import ScrollableFrame, Frame
from ccpn.ui.gui.widgets.Widget import ScrollableWidget
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.SideBar import OpenObjAction, _openItemObject
from ccpn.util import Logging
from ccpn.util.Logging import getLogger

settingsWidgetPositions = {
                           'top':    {'settings':(0,0), 'widget':(1,0)},
                           'bottom': {'settings':(1,0), 'widget':(0,0)},
                           'left':   {'settings':(0,0), 'widget':(0,1)},
                           'right':  {'settings':(0,1), 'widget':(0,0)},
                           }


class CcpnModule(Dock, DropBase):
  """
  Base class for CCPN modules
  sets self.application, self.current, self.project and self.mainWindow

  Overide parameters for settings widget as needed

  Usage:
    __init__    initialises the module according to the settings given below:

    _closeModule    closing of the module.

                    If addition functionality is required, the correct
                    procedure is to override this method within your class
                    and end your method with super()._closeModule()

                    e.q.
                          def _closeModule(self):
                            # your functions here
                            super(<YourModule>, self)._closeModule()

                    OR __init__ with closeFunc=<your close function>
  """
  moduleName = ''
  HORIZONTAL = 'horizontal'
  VERTICAL   = 'vertical'
  labelOrientation = HORIZONTAL  # toplabel orientation

  # overide in specific module implementations
  includeSettingsWidget = False
  maxSettingsState = 3  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsPosition = 'top'
  settingsMinimumSizes = (100, 50)
  _restored = False

  _instances = set()

  def __init__(self, mainWindow, name, closable=True, closeFunc=None, **kwds):

    #TODO:GEERTEN: make mainWindow actually do something
    self.area = None
    if mainWindow is not None:
      self.area = mainWindow.moduleArea

    Dock.__init__(self, name=name, area=self.area,
                   autoOrientation=False,
                   closable=closable)#, **kwds)   # ejb
    DropBase.__init__(self, acceptDrops=True)
    self.hStyle = """
                  Dock > QWidget {
                      border: 0px solid #000;
                      border-radius: 0px;
                      border-top-left-radius: 0px;
                      border-top-right-radius: 0px;
                      border-top-width: 0px;
                  }"""
    self.vStyle = """
                  Dock > QWidget {
                      border: 0px solid #000;
                      border-radius: 0px;
                      border-top-left-radius: 0px;
                      border-bottom-left-radius: 0px;
                      border-left-width: 0px;
                  }"""
    self.nStyle = """
                  Dock > QWidget {
                      border: 0px solid #000;
                      border-radius: 0px;
                  }"""
    self.dragStyle = """
                  Dock > QWidget {
                      border: 4px solid #00F;
                      border-radius: 0px;
                  }"""

    Logging.getLogger().debug('CcpnModule>>> %s %s' % (type(self), mainWindow))

    # Logging.getLogger().debug('module:"%s"' % (name,))
    self.mainWindow = mainWindow
    self.closeFunc = closeFunc
    self._nameSplitter = ':' #used to create the serial
    self._serial = None
    self._titleName = None # name without serial
    CcpnModule.moduleName = name

    self.widgetArea.setContentsMargins(0,0,0,0)
    # hide original dock label and generate a new CCPN one
    # self._originalLabel = self.label
    # self._originalLabel.hide()

    self.topLayout.removeWidget(self.label)   # remove old label, redefine
    self.label.deleteLater()
    self.label = CcpnModuleLabel(name, self, showCloseButton=closable, closeCallback=self._closeModule,
                                 showSettingsButton=self.includeSettingsWidget, settingsCallback=self._settingsCallback
                                 )
    self.topLayout.addWidget(self.label, 0, 1)   # ejb - swap out the old widget, keeps hierarchy
                                                  # except it doesn't work properly
    self.setOrientation(o='horizontal')
    # self.widgetArea = LayoutWidget()    # ejb - transparent, make normal drops better
    self.setAutoFillBackground(True)


    # ejb - below, True allows normal drops from outside and spectra, False for DockArea drops
    # self.widgetArea.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

    # ejb - add eventFilter for toggling WA_TransparentForMouseEvents

    # main widget area
    #self.mainWidget = Frame(parent=self, fShape='styledPanel', fShadow='plain')
    self.mainWidget = Widget(parent=None, setLayout=True)  #QtWidgets.QWidget(self)
    self.mainWidget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

    #self.mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    # optional settings widget area
    self.settingsState = 0  # current state (not shown)
    self.settingsWidget = None
    if self.includeSettingsWidget:
      # self.settingsWidget = ScrollableWidget(parent=self.widgetArea, setLayout=True,
      #                                       scrollBarPolicies=('always','asNeeded'),
      #                                       minimumSizes=self.settingsMinimumSizes
      #                                      )
      self._settingsScrollArea = ScrollArea(parent=self.widgetArea)
      self.settingsWidget = Frame(showBorder=False)
      # self.settingsWidget.setMinimumWidth(self.settingsMinimumSizes[0])
      # self.settingsWidget.setMinimumHeight(self.settingsMinimumSizes[1])
      self._settingsScrollArea.setWidget(self.settingsWidget)
      #self.settingsWidget.setLayout(QtWidgets.QGridLayout())
      self.settingsWidget.setGridLayout()
      self._settingsScrollArea.setWidgetResizable(True)
      #self._settingsScrollArea.getLayout().addWidget(self.settingsWidget)
      #self.settingsWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

      # if self.settingsOnTop:
      #   # self.addWidget(self.settingsWidget.getScrollArea(), 0, 0)
      #   self.addWidget(self._settingsScrollArea, 0, 0)
      #   self.addWidget(self.mainWidget, 1, 0)
      # else:
      #   # self.addWidget(self.settingsWidget.getScrollArea(), 1, 0)
      #   self.addWidget(self._settingsScrollArea, 1, 0)
      #   self.addWidget(self.mainWidget, 1, 1)
      # # self.settingsWidget._sequenceGraphScrollArea.hide()

      if self.settingsPosition in settingsWidgetPositions:
        hSettings, vSettings = settingsWidgetPositions[self.settingsPosition]['settings']
        hWidget, vWidget = settingsWidgetPositions[self.settingsPosition]['widget']
        self.addWidget(self._settingsScrollArea, hSettings, vSettings)
        self.addWidget(self.mainWidget, hWidget, vWidget)
      else: #default as settings on top and widget below
        self.addWidget(self._settingsScrollArea, 0, 0)
        self.addWidget(self.mainWidget, 1, 0)

      self._settingsScrollArea.hide()

      # testing a splitter to improve settings
      # self._splitter.setChildrenCollapsible(False)
      self.layout.removeWidget(self._settingsScrollArea)
      self.layout.removeWidget(self.mainWidget)

      if self.settingsPosition == 'left':
        self._splitter = Splitter(QtCore.Qt.Horizontal, setLayout=True)
        self._splitter.addWidget(self._settingsScrollArea)
        self._splitter.addWidget(self.mainWidget)
      elif self.settingsPosition == 'right':
        self._splitter = Splitter(QtCore.Qt.Horizontal, setLayout=True)
        self._splitter.addWidget(self.mainWidget)
        self._splitter.addWidget(self._settingsScrollArea)
      elif self.settingsPosition == 'top':
        self._splitter = Splitter(QtCore.Qt.Vertical, setLayout=True)
        self._splitter.addWidget(self._settingsScrollArea)
        self._splitter.addWidget(self.mainWidget)
      elif self.settingsPosition == 'bottom':
        self._splitter = Splitter(QtCore.Qt.Vertical, setLayout=True)
        self._splitter.addWidget(self.mainWidget)
        self._splitter.addWidget(self._settingsScrollArea)

      self.addWidget(self._splitter)

      # #another fix for the stylesheet
      # if hasattr(mainWindow, 'application') and mainWindow.application:
      #   # check that application has been attached - may not be the case for some test modules
      #   self.colourScheme = mainWindow.application.colourScheme
      #   if self.colourScheme == 'dark':
      #     self.setStyleSheet("""QSplitter{
      #                                 background-color: #2a3358;
      #                           }
      #                           QSplitter::handle:horizontal {
      #                                 width: 3px;
      #                           }
      #                           QSplitter::handle:vertical {
      #                                 height: 3px;
      #                           }
      #                           QSplitter::handle { background-color: LightGray }
      #                           """)
      #   elif self.colourScheme == 'light':
      #     self.setStyleSheet("""QSplitter{
      #                                 background-color: #FBF4CC;
      #                           }
      #                           QSplitter::handle:horizontal {
      #                                 width: 3px;
      #                           }
      #                           QSplitter::handle:vertical {
      #                                 height: 3px;
      #                           }
      #                           QSplitter::handle { background-color: DarkGray }
      #                           """)

    else:
      self.settingsWidget = None
      self.addWidget(self.mainWidget, 0, 0)

    # add an event filter to handle transparency
    # and to check when the dock has been floated - it needs to have a callback
    # that fires when the window has been maximised
    self._maximiseFunc = None
    self.eventFilter = self._eventFilter
    self.installEventFilter(self)

    # attach the mouse events to the widget
    # self.mainWidget.dragMoveEvent = self.dragMoveEvent
    # self.mainWidget.mouseMoveEvent = self.mouseMoveEvent
    # self.mainWidget.dragEnterEvent = self.dragEnterEvent
    # self.mainWidget.dragLeaveEvent = self.dragLeaveEvent
    # self.mainWidget.dropEvent = self.dropEvent

    # always explicitly show the mainWidget
    self.mainWidget.show()

    # set parenting relations
    if self.mainWindow is not None:
      self.setParent(self.mainWindow.moduleArea)   # ejb
    self.widgetArea.setParent(self)

  # # Not needed after all - SpectrumDisplay 'name' is renamed to 'title'
  # def getName(self):
  #   "Return name of self; done to allow for override in GuiSpectrumDisplay as that is a wrapper object as well"
  #   return self.name()

    # stop the blue overlay popping up when dragging over a spectrum
    self.allowedAreas = ['top', 'left', 'right', 'bottom']

    self.update()     # ejb - make sure that the widgetArea starts the correct size

    self._instances.add(ref(self))

  @classmethod
  def getInstances(cls):
    dead = set()
    for ref in cls._instances:
      obj = ref()
      if obj is not None:
        # if isinstance(obj, cls):
        if obj.className == cls.className:
          yield obj
      else:
        dead.add(ref)
    cls._instances -= dead

  @property
  def titleName(self):
    'module name without serial'
    moduleName = self.name()
    splits = moduleName.split(self._nameSplitter)
    if len(splits)>1:
      title = splits[0]
      return title
    else:
      return moduleName

  @property
  def serial(self):
    return self._serial

  @serial.setter
  def serial(self, value):
    if isinstance(value, str):
      try:
        value = int(value)
        return
      except Exception as e:
        getLogger().warnig('Cannot set attribute %s' %e)
    if isinstance(value, int):
      self._serial = value
      return
    else:
      getLogger().warning('Cannot set attribute. Serial must be an Int type')


  def rename(self, newName):
    self.label.setText(newName)
    self._name = newName

  def _eventFilter(self, source, event):
    """
    CCPNInternal
    Handle events for switching transparency of modules
    Modules become transparent when dragging to another module.
    Ensure that the dropAreas become active
    """
    if isinstance(source, CcpnModule) or isinstance(source, SideBar):
      if event.type() == QtCore.QEvent.DragEnter:
        data = self.parseEvent(event)
        if DropBase.PIDS in data and not isinstance(data['event'].source(), SideBar):
          self.mainWidget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
        else:

          # make transparent to enable module dragging
          self.mainWidget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

      elif event.type() == QtCore.QEvent.Leave:
        self.mainWidget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

      elif event.type() == QtCore.QEvent.Drop:
        self.mainWidget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

      elif event.type() == QtCore.QEvent.MouseButtonRelease:
        self.mainWidget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

    else:
      if event.type() == QtCore.QEvent.DragLeave:
        self.mainWidget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

      if event.type() == QtCore.QEvent.Enter:
        self.mainWidget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

      if event.type() == QtCore.QEvent.Leave:
        self.mainWidget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

      elif event.type() == QtCore.QEvent.MouseButtonRelease:
        self.mainWidget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

    if event.type() == QtCore.QEvent.ParentChange and self._maximiseFunc:
      try:
        found = False
        searchWidget = self.parent()
        while searchWidget is not None and not found:
          # print (searchWidget)
          if isinstance(searchWidget, TempAreaWindow):
            searchWidget.eventFilter = self._tempAreaWindowEventFilter
            searchWidget.installEventFilter(searchWidget)
            found = True
          else:
            searchWidget = searchWidget.parent()

      except Exception as es:
        getLogger().warning('Error setting maximiseFunc', str(es))

    return False

  # def _transparentAllModules(self, transparency:bool=True):
  #   if self.area:
  #     areaList = self.area.findAll()
  #     for modInArea in areaList:
  #       modInArea.widgetArea.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, transparency)

  # def resizeEvent(self, event):
  #   # self.setOrientation(self.labelOrientation, force=True)
  #   newSize = self.size()
  #   self.resizeOverlay(newSize)
  #   self.widgetArea.resize(newSize)   # ejb - to make the DropArea work properly
  #   self.mainWidget.resize(newSize)   # ejb - to make the DropArea work properly

    # override the default dock settings
    # self.widgetArea.setStyleSheet("""
    # Dock > QWidget {
    #   padding: 0;
    #   margin: 0px 0px 0px 0px;
    #   border: 0px;
    # }
    # """)

  def installMaximiseEventHandler(self, maximiseFunc):
    """
    Attach a maximise function to the parent window.
    This is called when the WindowStateChanges to maximises

    :param maximiseFunc:
    """
    self._maximiseFunc = maximiseFunc

  def removeMaximiseEventHandler(self):
    """
    Clear the attached maximise function
    :return:
    """
    self._maximiseFunc = None

  def _tempAreaWindowEventFilter(self, obj, event):
    """
    Window manager event filter to call the attached maximise function.
    This is required to re-populate the window when it has been maximised
    """
    try:
      if event.type() == QtCore.QEvent.WindowStateChange:
        if event.oldState() & QtCore.Qt.WindowMinimized:

          # TODO:ED check that this is unique if changed to another window
          if self._maximiseFunc:
            self._maximiseFunc()

    except Exception as es:
      print('>>>TEMP Error', obj, event, str(es))
    finally:
      return False

  def _settingsCallback(self):
    """
    Toggles display of settings widget in module.
    """
    if self.includeSettingsWidget:
      self.settingsState = (self.settingsState + 1) % self.maxSettingsState
      if self.settingsState == 0:
        self.mainWidget.show()
        # self.settingsWidget._sequenceGraphScrollArea.hide()
        self._settingsScrollArea.hide()
      elif self.settingsState == 1:
        self.mainWidget.show()
        # self.settingsWidget._sequenceGraphScrollArea.hide()
        self._settingsScrollArea.show()
      elif self.settingsState == 2:
        # self.settingsWidget._sequenceGraphScrollArea.hide()
        self._settingsScrollArea.hide()
        self.mainWidget.hide()
    else:
      RuntimeError('Settings widget inclusion is false, please set includeSettingsWidget boolean to True at class level ')

  def _closeModule(self):
    """
    Close the module
    """
    if self.closeFunc:
      self.closeFunc()

    if ref(self) in self._instances:
      self._instances.remove(ref(self))

    getLogger().debug('Closing %s' % str(self.container()))

    if not self._container:
      area = self.mainWindow.moduleArea
      if area:
        if area._container is None:
          for i in area.children():
            if isinstance(i, Container):
              self._container = i
    try:
      super(CcpnModule, self).close()
      # self.deleteLater()   # ejb - remove recursion when closing table from commandline
    except Exception as es:
      getLogger().debug('>>>delete CcpnModule Error %s' %es)

  def dragMoveEvent(self, *args):
    DockDrop.dragMoveEvent(self, *args)

  def dragLeaveEvent(self, *args):
    DockDrop.dragLeaveEvent(self, *args)

  def dragEnterEvent(self, *args):
    if args:
      ev = args[0]
      # print ('>>>', ev.source())
      data = self.parseEvent(ev)
      if DropBase.PIDS in data and isinstance(data['event'].source(), SideBar):
        if self.widgetArea:

          ld = ev.pos().x()
          rd = self.width() - ld
          td = ev.pos().y()
          bd = self.height() - td

          mn = min(ld, rd, td, bd)
          if mn > 30:
            self.dropArea = "center"
            self.area._dropArea = "center"

          elif (ld == mn or td == mn) and mn > self.height() / 3.:
            self.dropArea = "center"
            self.area._dropArea = "center"
          elif (rd == mn or ld == mn) and mn > self.width() / 3.:
            self.dropArea = "center"
            self.area._dropArea = "center"

          elif rd == mn:
            self.dropArea = "right"
            self.area._dropArea = "right"
            ev.accept()
          elif ld == mn:
            self.dropArea = "left"
            self.area._dropArea = "left"
            ev.accept()
          elif td == mn:
            self.dropArea = "top"
            self.area._dropArea = "top"
            ev.accept()
          elif bd == mn:
            self.dropArea = "bottom"
            self.area._dropArea = "bottom"
            ev.accept()

          if ev.source() is self and self.dropArea == 'center':
            # print "  no self-center"
            self.dropArea = None
            ev.ignore()
          elif self.dropArea not in self.allowedAreas:
            # print "  not allowed"
            self.dropArea = None
            ev.ignore()
          else:
            # print "  ok"
            ev.accept()
          self.overlay.setDropArea(self.dropArea)

          # self.widgetArea.setStyleSheet(self.dragStyle)
          self.update()
          # # if hasattr(self, 'drag'):
          # self.raiseOverlay()
          # self.updateStyle()
          # ev.accept()

      src = ev.source()
      if hasattr(src, 'implements') and src.implements('dock'):
        DockDrop.dragEnterEvent(self, *args)

  def dropEvent(self, *args):
    self.mainWidget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
    if args:
      event = args[0]
      source = event.source()
      data = self.parseEvent(event)
      if DropBase.PIDS in data:
        pids = data[DropBase.PIDS]
        objs = [self.mainWindow.project.getByPid(pid) for pid in pids]
        _openItemObject(self.mainWindow, objs, position=self.dropArea, relativeTo=self)
        event.accept()
        # print('DONE')

        # reset the dock area
        self.dropArea = None
        self.overlay.setDropArea(self.dropArea)

      if hasattr(source, 'implements') and source.implements('dock'):
        DockDrop.dropEvent(self, *args)
      else:
        args[0].ignore()
        return


class CcpnModuleLabel(DockLabel):
  """
  Subclassing DockLabel to modify appearance and functionality
  """

  labelSize = 16

  # TODO:GEERTEN check colours handling
  # defined here, as the updateStyle routine is called from the
  # DockLabel instanciation; changed later on


  def __init__(self, name, module, showCloseButton=True, closeCallback=None, showSettingsButton=False, settingsCallback=None):
    super(CcpnModuleLabel, self).__init__(name, module, showCloseButton=showCloseButton)

    self.module = module
    self.fixedWidth = True
    self.setFont(moduleLabelFont)
    #print('>>', name, self.module.application.colourScheme)

    self.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter)

    if showCloseButton:
      # button is already there because of the DockLabel init
      self.closeButton.setIconSize(QtCore.QSize(self.labelSize, self.labelSize))
      # hardcoded because stylesheet appears not to work
      # self.closeButton.setStyleSheet("""
      #   QToolButton
      #     border-width: 0px;
      #     padding: 0px;
      #   }""")
      if closeCallback is None:
        raise RuntimeError('Requested closeButton without callback')
      else:
        self.closeButton.clicked.connect(closeCallback)

    # Settings
    if showSettingsButton:
      self.settingsButton = QtWidgets.QToolButton(self)
      self.settingsButton.setIcon(Icon('icons/settings'))
      self.settingsButton.setIconSize(QtCore.QSize(self.labelSize, self.labelSize))
      # hardcoded because stylesheet appears not to work
      # colours = getColours()
      # styleSheet = """
      #   QComboBox {
      #     border-width: 0px;
      #     padding: 0px;
      #     background-color : %s;
      #     color : %s;
      #   }""" % (colours[CCPNMODULELABEL_BACKGROUND], colours[CCPNMODULELABEL_FOREGROUND])
      # print(">>>", styleSheet)
      # self.settingsButton.setStyleSheet(styleSheet)
      if settingsCallback is None:
        raise RuntimeError('Requested settingsButton without callback')
      else:
        self.settingsButton.clicked.connect(settingsCallback)

    self.updateStyle()

  # GWV: not sure why this was copied as it is identical to the routine in the parent class
  # def mousePressEvent(self, ev):
  #   if ev.button() == QtCore.Qt.LeftButton:
  #     self.pressPos = ev.pos()
  #     self.startedDrag = False
  #     ev.accept()

  # def updateStyle(self):
  #   """
  #   Copied from the parent class to allow for modification in StyleSheet
  #   However, that appears not to work (fully);
  #
  #   GWV: many calls to the updateStyle are triggered during initialization
  #        probably from paint event
  #   """
  #
  #   # Padding apears not to work; overriden somewhere else?
  #   colours = getColours()
  #   print('>>>', colours)
  #   # retain 'horizontal' and 'vertical' as the underlying PyQtGraph has it
  #   if self.orientation == 'vertical':
  #     self.vStyle = """CcpnModuleLabel {
  #             background-color : %s;
  #             color : %s;
  #             border-width: 0px;
  #         }""" % (colours[CCPNMODULELABEL_BACKGROUND], colours[CCPNMODULELABEL_FOREGROUND])
  #     self.setStyleSheet(self.vStyle)
  #   else:
  #     self.hStyle = """CcpnModuleLabel {
  #             background-color %s;
  #             color : %s;
  #             border-width: 0px;
  #         }""" % (colours[CCPNMODULELABEL_BACKGROUND], colours[CCPNMODULELABEL_FOREGROUND])
  #     print('>>>', self.hStyle)
  #     self.setStyleSheet(self.hStyle)

  def paintEvent(self, ev):
    """
    Copied from the parent VerticalLabel class to allow for modification in StyleSheet
    """
    p = QtGui.QPainter(self)

    # GWV: this moved the label in vertical mode and horizontal, after some trial and error
    # NOTE: A QRect can be constructed with a set of left, top, width and height integers
    if self.orientation == 'vertical':
      added = 2
      p.rotate(-90)
      rgn = QtCore.QRect(-self.height(), 0, self.height(), self.width()+added)
    else:
      rgn = self.contentsRect()
      #print('>>', self.width(), self.height())
      #print(rgn, rgn.left(), rgn.top())
      added = 4
      rgn = QtCore.QRect(rgn.left(), rgn.top(), rgn.width(), rgn.height()+added)

    #align = self.alignment()
    # GWV adjusted
    align  = QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter

    self.hint = p.drawText(rgn, align, self.text())
    p.end()

    if self.orientation == 'vertical':
      self.setMinimumWidth(self.labelSize)
      self.setMaximumWidth(self.labelSize)
    else:
      self.setMinimumHeight(self.labelSize)
      self.setMaximumHeight(self.labelSize)

    # if self.orientation == 'vertical':
    #   self.setMaximumWidth(self.hint.height())
    #   self.setMinimumWidth(0)
    #   self.setMaximumHeight(16777215)
    #   if self.forceWidth:
    #     self.setMinimumHeight(self.hint.width())
    #   else:
    #     self.setMinimumHeight(minSize)
    # else:
    #   self.setMaximumHeight(self.hint.height())
    #   self.setMinimumHeight(0)
    #   self.setMaximumWidth(16777215)
    #   if self.forceWidth:
    #     self.setMinimumWidth(self.hint.width())
    #   else:
    #     self.setMinimumWidth(minSize)

  def mouseMoveEvent(self, ev):
    if hasattr(self, 'pressPos'):
      if not self.startedDrag and (ev.pos() - self.pressPos).manhattanLength() > QtWidgets.QApplication.startDragDistance():
        self.dock.startDrag()
      ev.accept()
