__author__ = 'simon1'

from PyQt4 import QtCore

from ccpncore.gui.Menu import Menu
from ccpncore.gui.ToolBar import ToolBar

class SpectrumToolBar(ToolBar):

  def __init__(self, parent, widget=None, **kw):

    ToolBar.__init__(self, parent)
    self.widget = widget
    self.parent = parent

  def mousePressEvent(self, event):
    if event.button() == QtCore.Qt.RightButton:
      button = self.childAt(event.pos())
      menu = self.raiseContextMenu(button)
      menu.popup(event.globalPos())

  def raiseContextMenu(self, button):
    contextMenu = Menu('', self, isFloatWidget=True)
    from functools import partial
    contextMenu.addAction('Delete', partial(self.removeSpectrum, button))
    return contextMenu

  def removeSpectrum(self, button):
    self.removeAction(button.actions()[0])
    key = [key for key, value in self.widget.spectrumActionDict.items() if value == button.actions()[0]][0]
    for spectrumView in self.widget.spectrumViews:
      if spectrumView._apiDataSource == key:
        for strip in self.widget.strips:
          spectrumView.removeSpectrumItem(strip)