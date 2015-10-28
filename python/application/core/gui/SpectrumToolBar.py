__author__ = 'simon1'

from PyQt4 import QtCore, QtGui

from ccpncore.gui.Menu import Menu
from ccpncore.gui.ToolBar import ToolBar

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
    from functools import partial
    contextMenu.addAction('Delete', partial(self.removeSpectrum, button))
    return contextMenu

  def removeSpectrum(self, button:QtGui.QToolButton):
    """
    Removes the spectrum from the display and its button from the toolbar.
    """
    self.removeAction(button.actions()[0])
    key = [key for key, value in self.widget.spectrumActionDict.items() if value == button.actions()[0]][0]
    for spectrumView in self.widget.spectrumViews:
      if spectrumView._apiDataSource == key:
        # for strip in self.widget.strips:
        #   spectrumView.removeSpectrumItem(strip)
        spectrumView._wrappedData.spectrumView.delete()