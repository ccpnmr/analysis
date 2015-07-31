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
__author__ = 'simon'


from ccpncore.gui.Base import Base
from ccpncore.gui.Menu import Menu

from PyQt4 import QtGui, QtCore

class ToolBar(QtGui.QToolBar, Base):

  def __init__(self, parent, widget=None, callback=None, **kw):
    QtGui.QToolBar.__init__(self, parent)
    Base.__init__(self, **kw)
    self.parent = parent
    self.widget = widget


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
      if spectrumView.apiDataSource == key:
        for strip in self.widget.strips:
          spectrumView.removeSpectrumItem(strip)

