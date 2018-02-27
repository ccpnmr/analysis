"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.CcpnOpenGL import CcpnGLWidget


class Gui1dWidget(CcpnGLWidget):
  def __init__(self, parent=None, mainWindow=None, rightMenu=None, stripIDLabel=None):
    super(Gui1dWidget, self).__init__(parent=parent,
                                      mainWindow=mainWindow,
                                      rightMenu=rightMenu,
                                      stripIDLabel=stripIDLabel)

class GuiNdWidget(CcpnGLWidget):
  def __init__(self, parent=None, mainWindow=None, rightMenu=None, stripIDLabel=None):
    super(GuiNdWidget, self).__init__(parent=parent,
                                      mainWindow=mainWindow,
                                      rightMenu=rightMenu,
                                      stripIDLabel=stripIDLabel)
