"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

__author__ = 'simon1'

from PyQt4 import QtCore, QtGui

from ccpncore.gui.Menu import Menu
from ccpncore.gui.ToolBar import ToolBar

from functools import partial

class SpectrumToolBar(ToolBar):

  def __init__(self, parent, widget=None, **kw):

    ToolBar.__init__(self, parent)
    self.widget = widget
    self.parent = parent

  def mousePressEvent(self, event:QtGui.QMouseEvent):
    """
    Re-implementation of the Toolbar mouse event so a right mouse context menu can be raised.
    """
    if event.button() == QtCore.Qt.RightButton:
      button = self.childAt(event.pos())
      menu = self.createContextMenu(button)
      menu.popup(event.globalPos())

  def createContextMenu(self, button:QtGui.QToolButton):
    """
    Creates a context menu containing a command to delete the spectrum from the display and its
    button from the toolbar.
    """
    contextMenu = Menu('', self, isFloatWidget=True)
    peakListViews = self.widget.peakListViews
    key = [key for key, value in self.widget.spectrumActionDict.items() if value == button.actions()[0]][0]
    for peakListView in peakListViews:
      if peakListView.spectrumView._apiDataSource == key:
        action = contextMenu.addAction(peakListView.peakList.id)
        action.setCheckable(True)
        if peakListView.isVisible():
          action.setChecked(True)
        action.toggled.connect(peakListView.setVisible)
    contextMenu.addAction('Remove', partial(self.removeSpectrum, button))
    return contextMenu

  def removeSpectrum(self, button:QtGui.QToolButton):
    """
    Removes the spectrum from the display and its button from the toolbar.
    """
    self.removeAction(button.actions()[0])
    key = [key for key, value in self.widget.spectrumActionDict.items() if value == button.actions()[0]][0]
    for spectrumView in self.widget.spectrumViews:
      if spectrumView._apiDataSource == key:
        spectrumView._wrappedData.spectrumView.delete()