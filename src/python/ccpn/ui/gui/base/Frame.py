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

from ccpn.ui.gui.widgets.Frame import Frame as CoreFrame
from ccpn.ui.gui.Base import Base as GuiBase

class Frame(CoreFrame, GuiBase):

  def __init__(self, parent=None, **kw):

    CoreFrame.__init__(self, parent)
    GuiBase.__init__(self, **kw)


  def _widthsChangedEnough(self, r1, r2, tol=1e-5):
    r1 = sorted(r1)
    r2 = sorted(r2)
    minDiff = abs(r1[0] - r2[0])
    maxDiff = abs(r1[1] - r2[1])
    return (minDiff > tol) or (maxDiff > tol)


  def updateY(self, strip):
    yRange = list(strip.viewBox.viewRange()[1])
    for s in strip.guiSpectrumDisplay.strips:
      sYRange = list(s.viewBox.viewRange()[1])
      if self._widthsChangedEnough(sYRange, yRange):
        s.viewBox.setYRange(*yRange, padding=0)


