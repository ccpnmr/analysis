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

import os
from ccpn.util import Path
from PyQt4 import QtGui
from ccpn.ui.gui.widgets.Label import Label


class AboutPopup(QtGui.QDialog):
  def __init__(self, parent=None, **kw):
    super(AboutPopup, self).__init__(parent)

    pathPNG = os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'),'About_CcpNmr.png')
    self.label = Label(self)
    self.label.setPixmap(QtGui.QPixmap(pathPNG))
