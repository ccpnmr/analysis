"""
This file contains CcpnModule base class

intial version by Simon;
Extensively modified by Geerten 1-12/12/2016

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-07-09 14:17:30 +0100 (Sat, 09 Jul 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2016-07-09 14:17:30 +0100 (Sat, 09 Jul 2016) $"
__version__ = "$Revision: 9605 $"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtCore, QtGui
from pyqtgraph.dockarea.DockDrop import DockDrop
from pyqtgraph.dockarea.Dock import DockLabel, Dock
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.guiSettings import moduleLabelFont

from functools import partial

#Module = Dock
#ModuleLabel = DockLabel
from ccpn.util.Logging import getLogger

logger = getLogger()

class CcpnModule(Dock):
  """
  Base class for CCPN modules
  """

  ORIENTATION = 'horizontal' #''vertical'   # toplabel orientation
  includeSettingsWidget = False   # overide in specific module implementations

  def __init__(self, name, logger=None, buttonParent=None, buttonGrid=None, closable=True, closeFunc=None, **kw):
    super(CcpnModule, self).__init__(name, self, closable=closable)
    self.closeFunc = closeFunc

    # hide original dock label and generate a new CCPN one
    self.label.hide()
    self.label = CcpnModuleLabel(name.upper(), self, showCloseButton=closable)
    if closable:
      self.label.closeButton.clicked.connect(self._closeModule)
    self.label.show()

    self.autoOrientation = False
    self.mainWidget = QtGui.QWidget(self)
    self.addWidget(self.mainWidget, 0, 0)

    if self.includeSettingsWidget:
      self.settingsWidget = QtGui.QWidget(self)
      self.addWidget(self.settingsWidget, 1, 0)
      self.settingsWidget.hide()

  def resizeEvent(self, event):
    #self.setOrientation('vertical', force=True)
    self.setOrientation(self.ORIENTATION, force=True)
    self.resizeOverlay(self.size())

  def placeSettingsButton(self, buttonParent, buttonGrid):
    if self.includeSettingsWidget:
      settingsButton = Button(buttonParent, icon='icons/applications-system', grid=buttonGrid, hPolicy='fixed', toggle=True)
      settingsButton.toggled.connect(partial(self.toggleSettingsWidget, settingsButton))
      settingsButton.setChecked(False)

  def toggleSettingsWidget(self, button=None):
    """
    Toggles display of settings widget in module.
    """
    if self.includeSettingsWidget:
      if button.isChecked():
        self.settingsWidget.show()
      else:
        self.settingsWidget.hide()
    else:
      logger.debug('Settings widget inclusion is false, please set includeSettingsWidget boolean to True at class level ')

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
  def __init__(self, name, module, showCloseButton=True):
    super(CcpnModuleLabel, self).__init__(name, module, showCloseButton=showCloseButton)
    self.module = module
    self.fixedWidth = True
    self.setFont(moduleLabelFont)
    self.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter)

    # Tests; not yet there
    if False:
      self.settingsButton = QtGui.QToolButton(self)
      #self.settingsButton.clicked.connect(self.sigCloseClicked)
      self.settingsButton.setIcon(Icon('icons/applications-system'))
      self.settingsButton.setIconSize(QtCore.QSize(16, 16))
      self.settingsButton.setStyleSheet("""
        QPushButton {
          border-width: 0px;
          padding: 0px;
          background-color: #555D85;
          color: #555D85;
        }""")

    #self.update()

    self.updateStyle()
    #self.update()

  # GWV: not sure why this was copied as it is identical to the routine in the parent class
  # def mousePressEvent(self, ev):
  #   if ev.button() == QtCore.Qt.LeftButton:
  #     self.pressPos = ev.pos()
  #     self.startedDrag = False
  #     ev.accept()

  def updateStyle(self):
    """
    Copied from the parent class to allow for modification in StyleSheet
    However, that appears not to work; TODO: this routine needs fixing so that colourschemes
    are taken from the stylesheet
    """
    # GWV: many calls to the updateStyle are triggered during initialization
    # probably from paint event

    #print('>updateStyle>', self)
    #return

    r = '3px'
    fg = '#fdfdfc'
    bg = '#555D85'
    border = bg

    # Padding apears not to work; overriden somewhere else?
    if self.orientation == 'vertical':
      self.vStyle = """DockLabel {
              background-color : %s;
              color : %s;
              border-width: 0px;
          }""" % (bg, fg)
      self.setStyleSheet(self.vStyle)
    else:
      self.hStyle = """DockLabel {
              background-color : %s;
              color : %s;
              border-width: 0px;
          }""" % (bg, fg)
      self.setStyleSheet(self.hStyle)

  def paintEvent(self, ev):
    """
    Copied from the parent VerticlLabel class to allow for modification in StyleSheet
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

    minSize = 16  #GWV parameter
    if self.orientation == 'vertical':
      self.setMinimumWidth(minSize)
      self.setMaximumWidth(minSize)
    else:
      self.setMinimumHeight(minSize)
      self.setMaximumHeight(minSize)

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




