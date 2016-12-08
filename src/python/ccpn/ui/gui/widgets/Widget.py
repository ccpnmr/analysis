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

from PyQt4 import QtGui
from ccpn.ui.gui.widgets.Base import Base

class Widget(QtGui.QWidget, Base):

  def __init__(self, parent=None, border=None, colourScheme=None, setLayout=False, **kw):

    QtGui.QWidget.__init__(self, parent)
    self.setAcceptDrops(True)
    Base.__init__(self, **kw)
    if setLayout:
      layout = QtGui.QGridLayout()
      self.setLayout(layout)
