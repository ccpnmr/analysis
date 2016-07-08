"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
__author__ = 'simon'


from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Menu import Menu

from PyQt4 import QtGui, QtCore

class ToolBar(QtGui.QToolBar, Base):

  def __init__(self, parent, **kw):
    QtGui.QToolBar.__init__(self, parent)
    Base.__init__(self, **kw)
    self.hidden = False

  def hideToolbar(self):
    "Hide the toolbar"
    self.hide()
    self.hidden = True

  def showToolbar(self):
    "Show the toolbar"
    self.show()
    self.hidden = False

  def toggleToolbar(self):
    "Toogle the toolbar"
    if self.hidden:
      self.showToolbar()
    else:
      self.hideToolbar()