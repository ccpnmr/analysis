"""Module Documentation here

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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:52 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"

#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
from PyQt5 import QtGui, QtWidgets, QtCore

from ccpn.ui.gui.widgets.Base import Base


class DoubleSpinbox(QtGui.QDoubleSpinBox, Base):

  # To be done more rigeriously later
  _styleSheet = """
  DoubleSpinbox {
    background-color: #f7ffff;
    color: #122043;
    margin: 0px 0px 0px 0px;
    padding: 2px 2px 2px 2px;
    border: 1px solid #182548;
  }

  DoubleSpinbox::hover {
    background-color: #e4e15b;
  } 
  """
  defaultMinimumSizes = (0,20)

  def __init__(self, parent, value=None, min=None, max=None, step=None, showButtons=True,
               decimals=None, callback=None, **kwds):
    """
    From the QTdocumentation 
    Constructs a spin box with a step value of 1.0 and a precision of 2 decimal places.
    Change the default 0.0 minimum value to -sys.float_info.max
    Change the default 99.99  maximum value to sys.float_info.max      
    The value is default set to 0.00. 
    
    The spin box has the given parent.
    """

    QtGui.QDoubleSpinBox.__init__(self, parent)
    Base.__init__(self, **kwds)

    if value is not None:
      self.setValue(value)

    if min is not None:
      self.setMinimum(min)
    else:
      self.setMinimum(-1.0*sys.float_info.max)

    if max is not None:
      self.setMaximum(max)
    else:
      self.setMaximum(sys.float_info.max)

    self.isSelected = False

    if step is not None:
      self.setSingleStep(step)

    if decimals is not None:
      self.setDecimals(decimals)

    if showButtons is False:
      self.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)

    self._callback = None
    self.setCallback(callback)

    self.setMinimumWidth(self.defaultMinimumSizes[0])
    self.setMinimumHeight(self.defaultMinimumSizes[1])

    self.setStyleSheet(self._styleSheet)

  def setSelected(self):
    self.isSelected = True

  def focusInEvent(self, QFocusEvent):
    self.setSelected()

  def setCallback(self, callback):
    "Sets callback; disconnects if callback=None"
    if self._callback is not None:
      self.disconnect(self, QtCore.SIGNAL('valueChanged(double)'), self._callback)
    if callback:
      self.connect(self, QtCore.SIGNAL("valueChanged(double)"), callback)
    self._callback = callback
