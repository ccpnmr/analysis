"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

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

from PyQt4 import QtGui, QtCore

from application.core.widgets.Base import Base

class DoubleSpinbox(QtGui.QDoubleSpinBox, Base):

  def __init__(self, parent, value=None, min=None, max=None, showButtons=True, **kw):

    QtGui.QDoubleSpinBox.__init__(self, parent)
    if value is not None:
      self.setValue(value)
    if min is not None:
      self.setMinimum(min)
    if max is not None:
      self.setMaximum(max)
    Base.__init__(self, **kw)
    self.isSelected = False


    if showButtons is False:
      self.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)

  def setSelected(self):
    self.isSelected = True

  def focusInEvent(self, QFocusEvent):
    self.setSelected()
