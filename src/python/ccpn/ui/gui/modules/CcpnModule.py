"""
This file contains CcpnModule base class

initial version by Simon;
Extensively modified by Geerten 1-12/12/2016

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
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2016-07-09 14:17:30 +0100 (Sat, 09 Jul 2016) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtCore, QtGui

from pyqtgraph.dockarea.DockDrop import DockDrop
from pyqtgraph.dockarea.Dock import DockLabel, Dock
from pyqtgraph.widgets.LayoutWidget import LayoutWidget   # ejb - allows better dropping

from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.guiSettings import moduleLabelFont
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Frame import ScrollableFrame, Frame
from ccpn.ui.gui.widgets.Widget import ScrollableWidget
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea

from ccpn.util import Logging
from ccpn.util.Logging import getLogger

settingsWidgetPositions = {
                           'top':    {'settings':(0,0), 'widget':(1,0)},
                           'bottom': {'settings':(1,0), 'widget':(0,0)},
                           'left':   {'settings':(0,0), 'widget':(0,1)},
                           'right':  {'settings':(0,1), 'widget':(0,0)},
                           }

class CcpnModule(Dock):
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

  def __init__(self, mainWindow, name, closable=True, closeFunc=None, **kwds):

    #TODO:GEERTEN: make mainWindow actually do something
    area = None
    if mainWindow is not None:
      area = mainWindow.moduleArea

    Dock.__init__(self, name=name, area=area,
                   autoOrientation=False,
                   closable=closable)#, **kwds)   # ejb

    Logging.getLogger().debug('CcpnModule>>> %s %s' % (type(self), mainWindow))

    Logging.getLogger().debug('module:"%s"' % (name,))
    self.mainWindow = mainWindow
    self.closeFunc = closeFunc
    CcpnModule.moduleName = name

    # hide original dock label and generate a new CCPN one
    self._originalLabel = self.label
    self._originalLabel.hide()
    self.label = CcpnModuleLabel(name, self, showCloseButton=closable, closeCallback=self._closeModule,
                                 showSettingsButton=self.includeSettingsWidget, settingsCallback=self._settingsCallback
                                 )

    ###self.label.show()
    # self.autoOrientation = False
    self.setOrientation(o='horizontal')
    self.widgetArea = LayoutWidget()    # ejb - transparent, make normal drops better

    # ejb - below, True allows normal drops from outside and spectra, False for DockArea drops
    self.widgetArea.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

    # ejb - add eventFilter for toggling WA_TransparentForMouseEvents
    self.eventFilter = self._eventFilter
    self.installEventFilter(self)

    # main widget area
    #self.mainWidget = Frame(parent=self, fShape='styledPanel', fShadow='plain')
    self.mainWidget = Widget(parent=self, setLayout=True)  #QtGui.QWidget(self)
    #self.mainWidget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

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
      #self.settingsWidget.setLayout(QtGui.QGridLayout())
      self.settingsWidget.setGridLayout()
      self._settingsScrollArea.setWidgetResizable(True)
      #self._settingsScrollArea.getLayout().addWidget(self.settingsWidget)
      #self.settingsWidget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

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

    else:
      self.settingsWidget = None
      self.addWidget(self.mainWidget, 0, 0)

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

    self.update()     # ejb - make sure that the widgetArea starts the correct size

  def _eventFilter(self, source, event):
    """
    CCPNInternal
    """
    if isinstance(source, CcpnModule):
      if event.type() == QtCore.QEvent.DragEnter:
        self.widgetArea.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
        # print ('>>>CcpnModule - dragEnterEvent')

      elif event.type() == QtCore.QEvent.Leave:
        self.widgetArea.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        # print ('>>>CcpnModule - leaveEvent')

      elif event.type() == QtCore.QEvent.Drop:
        self.widgetArea.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        # print ('>>>CcpnModule - dropEvent')
    else:
      if event.type() == QtCore.QEvent.DragLeave:
        self.widgetArea.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        # print ('>>>CcpnModule - dragLeaveEvent')

    return super(CcpnModule, self).eventFilter(source,event)

  def resizeEvent(self, event):
    # self.setOrientation(self.labelOrientation, force=True)
    newSize = self.size()
    self.resizeOverlay(newSize)
    self.widgetArea.resize(newSize)   # ejb - to make the DropArea work properly

    # override the default dock settings
    # self.widgetArea.setStyleSheet("""
    # Dock > QWidget {
    #   padding: 0;
    #   margin: 0px 0px 0px 0px;
    #   border: 0px;
    # }
    # """)

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

    if self.closeFunc:
      self.closeFunc()

    getLogger().debug('Closing %s' % str(self.container()))
    super(CcpnModule, self).close()   # ejb - remove recursion when closing table from commandline

  def dropEvent(self, *args):
    self.widgetArea.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
    source = args[0].source()

    if hasattr(source, 'implements') and source.implements('dock'):
      DockDrop.dropEvent(self, *args)
      # super(CcpnModule, self).dropEvent(*args)    # ejb?
    else:
      args[0].ignore()
      return

  # def dragEnterEvent(self, event):
  #   t = event.type()    # DragEnter so okay
  #   pass

  # def dragEnterEvent(self, event):
  #   if isinstance(event.widget(), CcpnModule):
  #     self.widgetArea.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
  #   print ('>>>CcpnModule - dragEnterEvent')
  #   super(CcpnModule, self).dragEnterEvent(event)
  #
  # def dragLeaveEvent(self, event):
  #   if isinstance(event.widget(), CcpnModule):
  #     self.widgetArea.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
  #   print ('>>>CcpnModule - dragLeaveEvent')
  #   super(CcpnModule, self).dragLeaveEvent(event)

      # def dragMoveEvent(self, *args):
  #   cursor = QtGui.QCursor()
  #   print('>>> CcpnModule %s' % cursor.pos())
  #   super(CcpnModule, self).dragMoveEvent(*args)


class CcpnModuleLabel(DockLabel):
  """
  Subclassing DockLabel to modify appearance and functionality
  """

  labelSize = 16

  # TODO:GEERTEN remove colours from here
  # defined here, as the updateStyle routine is called from the
  # DockLabel instanciation; changed later on
  backgroundColour = '#555D85'
  foregroundColour = '#fdfdfc'

  def __init__(self, name, module, showCloseButton=True, closeCallback=None, showSettingsButton=False, settingsCallback=None):
    super(CcpnModuleLabel, self).__init__(name, module, showCloseButton=showCloseButton)

    self.module = module
    self.fixedWidth = True
    self.setFont(moduleLabelFont)
    #print('>>', name, self.module.application.colourScheme)

    from ccpn.ui.gui.guiSettings import getColourScheme
    self.colourScheme = getColourScheme()
    if self.colourScheme == 'light':
      self.backgroundColour = '#bd8413'
      #self.backgroundColour = '#EDC151'
      self.foregroundColour = '#fdfdfc'
    else:
      self.backgroundColour = '#555D85'
      self.foregroundColour = '#fdfdfc'
    self.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter)

    if showCloseButton:
      # button is already there because of the DockLabel init
      self.closeButton.setIconSize(QtCore.QSize(self.labelSize, self.labelSize))
      # hardcoded because stylesheet appears not to work
      self.closeButton.setStyleSheet("""
        QToolButton {
          border-width: 0px;
          padding: 0px;
        }""")
      if closeCallback is None:
        raise RuntimeError('Requested closeButton without callback')
      else:
        self.closeButton.clicked.connect(closeCallback)

    # Settings
    if showSettingsButton:
      self.settingsButton = QtGui.QToolButton(self)
      self.settingsButton.setIcon(Icon('icons/settings'))
      self.settingsButton.setIconSize(QtCore.QSize(self.labelSize, self.labelSize))
      # hardcoded because stylesheet appears not to work
      self.settingsButton.setStyleSheet("""
        QToolButton {
          border-width: 0px;
          padding: 0px;
        }""")
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

  def updateStyle(self):
    """
    Copied from the parent class to allow for modification in StyleSheet
    However, that appears not to work;

    TODO: this routine needs fixing so that colourschemes
    are taken from the stylesheet
    """
    # GWV: many calls to the updateStyle are triggered during initialization
    # probably from paint event

    #print('>updateStyle>', self)
    #return

    #r = '3px'
    #fg = '#fdfdfc'
    #bg = '#555D85'
    #border = bg

    # Padding apears not to work; overriden somewhere else?
    if self.orientation == 'vertical':
      self.vStyle = """DockLabel {
              background-color : %s;
              color : %s;
              border-width: 0px;
          }""" % (self.backgroundColour, self.foregroundColour)
      self.setStyleSheet(self.vStyle)
    else:
      self.hStyle = """DockLabel {
              background-color : %s;
              color : %s;
              border-width: 0px;
          }""" % (self.backgroundColour, self.foregroundColour)
      self.setStyleSheet(self.hStyle)

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
      added = 2
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
      if not self.startedDrag and (ev.pos() - self.pressPos).manhattanLength() > QtGui.QApplication.startDragDistance():
        self.dock.startDrag()
      ev.accept()

