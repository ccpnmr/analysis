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
__dateModified__ = "$dateModified: 2017-04-07 11:41:06 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"

#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister$"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.widgets.Base import Base

SCROLLBAR_POLICY_DICT = dict(
    always   = QtCore.Qt.ScrollBarAlwaysOn,
    never    = QtCore.Qt.ScrollBarAlwaysOff,
    asNeeded = QtCore.Qt.ScrollBarAsNeeded,
)

class ScrollArea(QtGui.QScrollArea, Base):

  def __init__(self, parent, scrollBarPolicies=('asNeeded','asNeeded'),
                     minimumSizes=(50, 50), **kwds):

    QtGui.QScrollArea.__init__(self, parent)
    Base.__init__(self, **kwds)
    self.setScrollBarPolicies(scrollBarPolicies)
    self.setMinimumSizes(minimumSizes)

  def setMinimumSizes(self, minimumSizes):
    "Set (minimumWidth, minimumHeight)"
    self.setMinimumWidth(minimumSizes[0])
    self.setMinimumHeight(minimumSizes[1])

  def setScrollBarPolicies(self, scrollBarPolicies=('asNeeded','asNeeded')):
    "Set the scrolbar policy: always, never, asNeeded"

    hp = SCROLLBAR_POLICY_DICT.get(scrollBarPolicies[0])
    vp = SCROLLBAR_POLICY_DICT.get(scrollBarPolicies[1])
    self.setHorizontalScrollBarPolicy(hp)
    self.setVerticalScrollBarPolicy(vp)