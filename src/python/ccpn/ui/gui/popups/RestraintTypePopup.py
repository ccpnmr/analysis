"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-10 15:35:09 +0100 (Mon, April 10, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialog      # ejb


restraintTypes = [
  'Distance',
  'Dihedral',
  'Rdc',
  'Csa',
  'ChemicalShift',
  'JCoupling'
]

# class RestraintTypePopup(QtGui.QDialog, Base):
class RestraintTypePopup(CcpnDialog):
  def __init__(self, parent=None, peakList=None, title='Restraints', **kw):
    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)
    # super(RestraintTypePopup, self).__init__(parent)
    # Base.__init__(self, **kw)

    self.restraintTypeLabel = Label(self, "Restraint Type ", grid=(0, 0))
    self.restraintTypeList = PulldownList(self, grid=(0, 1))
    self.restraintTypeList.setData(restraintTypes)
    buttonList = ButtonList(self, ['Cancel', 'OK'], [self.reject, self._setRestraintType], grid=(1, 1))

  def _setRestraintType(self):
    self.restraintType = self.restraintTypeList.currentText()
    self.accept()