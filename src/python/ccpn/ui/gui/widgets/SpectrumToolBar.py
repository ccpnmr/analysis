"""Module Documentation here

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
__author__ = "$Author: CCPN $"
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:43 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"

#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon1 $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt4 import QtCore, QtGui

from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.ToolBar import ToolBar

from functools import partial

class SpectrumToolBar(ToolBar):

  def __init__(self, parent=None, widget=None, **kwds):

    ToolBar.__init__(self, parent=parent, **kwds)
    self.widget = widget
    self.parent = parent
    self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)

  def mousePressEvent(self, event:QtGui.QMouseEvent):
    """
    Re-implementation of the Toolbar mouse event so a right mouse context menu can be raised.
    """
    if event.button() == QtCore.Qt.RightButton:
      button = self.childAt(event.pos())
      menu = self._createContextMenu(button)
      if menu:
        menu.move(event.globalPos().x(), event.globalPos().y() + 10)
        menu.exec()

  def _createContextMenu(self, button:QtGui.QToolButton):
    """
    Creates a context menu containing a command to delete the spectrum from the display and its
    button from the toolbar.
    """
    if not button:
      return None
    contextMenu = Menu('', self, isFloatWidget=True)
    peakListViews = self.widget.peakListViews
    action = button.actions()[0]
    keys = [key for key, value in self.widget.spectrumActionDict.items() if value is action]
    if not keys: # if you click on >> button which shows more spectra
      return None
    key = keys[0]
    for peakListView in peakListViews:
      if peakListView.spectrumView._apiDataSource == key:
        action = contextMenu.addAction(peakListView.peakList.id)
        action.setCheckable(True)
        if peakListView.isVisible():
          action.setChecked(True)
        action.toggled.connect(peakListView.setVisible)
    contextMenu.addAction('Remove', partial(self._removeSpectrum, button))
    return contextMenu

  def _removeSpectrum(self, button:QtGui.QToolButton):
    """
    Removes the spectrum from the display and its button from the toolbar.
    """
    self.removeAction(button.actions()[0])
    key = [key for key, value in self.widget.spectrumActionDict.items() if value == button.actions()[0]][0]
    for spectrumView in self.widget.spectrumViews:
      if spectrumView._apiDataSource == key:
        spectrumView._wrappedData.spectrumView.delete()
