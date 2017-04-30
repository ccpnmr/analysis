"""
This file contains CcpnModule base class

intial version by Simon;
Extensively modified by Geerten 1-12/12/2016

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:38 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
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

from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.guiSettings import moduleLabelFont
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Frame import ScrollableFrame

from ccpn.util.Logging import getLogger

class CcpnModule(Dock):
  """
  Base class for CCPN modules
  sets self.application, self.current, self.project and self.mainWindow

  Overide parameters for settings widget as needed
  """
  moduleName = ''
  HORIZONTAL = 'horizontal'
  VERTICAL   = 'vertical'
  labelOrientation = HORIZONTAL  # toplabel orientation

  # overide in specific module implementations
  includeSettingsWidget = False
  maxSettingsState = 3  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsOnTop = True
  settingsMinimumSizes = (0, 0)

  def __init__(self, mainWindow, name, closable=True, closeFunc=None, **kwds):

    #TODO:GEERTEN: make mainWindow actually do something

    super(CcpnModule, self).__init__(name=name, area=mainWindow.moduleArea,
                                     closable=closable)#, **kwds)   # ejb
    print('CcpnModule>>>', type(self), mainWindow)

    getLogger().debug('module:"%s"' % (name,))

    self.closeFunc = closeFunc
    CcpnModule.moduleName = name

    # hide original dock label and generate a new CCPN one
    self._originalLabel = self.label
    self._originalLabel.hide()
    self.label = CcpnModuleLabel(name, self, showCloseButton=closable, closeCallback=self._closeModule,
                                 showSettingsButton=self.includeSettingsWidget, settingsCallback=self._settingsCallback
                                 )
    self.label.show()
    self.autoOrientation = False

    # main widget area
    #self.mainWidget = Frame(parent=self, fShape='styledPanel', fShadow='plain')
    self.mainWidget = Widget(parent=self.widgetArea, setLayout=False)  #QtGui.QWidget(self)

    # optional settings widget area
    self.settingsState = 0  # current state (not shown)
    self.settingsWidget = None
    if self.includeSettingsWidget:
      self.settingsWidget = ScrollableFrame(parent=self.widgetArea,
                                            scrollBarPolicies=('always','asNeeded'),
                                            minimumSizes=self.settingsMinimumSizes
                                           )
      if self.settingsOnTop:
        self.addWidget(self.settingsWidget.scrollArea, 0, 0)
        self.addWidget(self.mainWidget, 1, 0)
      else:
        self.addWidget(self.mainWidget, 0, 0)
        self.addWidget(self.settingsWidget.scrollArea, 1, 0)
      self.settingsWidget.scrollArea.hide()

    else:
      self.settingsWidget = None
      self.addWidget(self.mainWidget, 0, 0)

    # always explicitly show the mainWidget
    self.mainWidget.show()

    # set parenting relations
    self.setParent(mainWindow)
    self.widgetArea.setParent(self)

  def getName(self):
    "Return name of self; done to allow for override in GuiSpectrumDisplay as that is a warpper object as well"
    return self.name()

  def resizeEvent(self, event):
    self.setOrientation(self.labelOrientation, force=True)
    self.resizeOverlay(self.size())

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
        self.settingsWidget.scrollArea.hide()
      elif self.settingsState == 1:
        self.mainWidget.show()
        self.settingsWidget.scrollArea.show()
      elif self.settingsState == 2:
        self.settingsWidget.scrollArea.show()
        self.mainWidget.hide()
    else:
      RuntimeError('Settings widget inclusion is false, please set includeSettingsWidget boolean to True at class level ')

  def _closeModule(self):

    if self.closeFunc:
      self.closeFunc()

    self.close()

  def dropEvent(self, *args):
    source = args[0].source()

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




