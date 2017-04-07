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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:03 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt4 import QtCore, QtGui

from ccpn.ui.gui.Base import Base as GuiBase
from ccpn.ui.gui.modules.CcpnModule import CcpnModule

QtCore.qInstallMsgHandler(lambda *args: None)

class GuiModule(QtGui.QWidget, GuiBase):
  # It used to subclass Dock but that doesn't work because that has a function name() and we have an attribute name
  # So instead create a module

  def __init__(self, position='right'):
    
    QtGui.QWidget.__init__(self)
    self.moduleArea = self.window.moduleArea
    self.module = CcpnModule(name=self._wrappedData.name, size=(1100,1300), autoOrientation=False)
    # self.module.label.hide()
    # self.module.label = ModuleLabel(self._wrappedData.name, self.module)
    # self.module.label.show()
    self.hoverEvent = self._hoverEvent
    self.moduleArea.addModule(self.module, position=position)

    GuiBase.__init__(self, self._project._appBase)


  def _hoverEvent(self, event):
    event.accept()
