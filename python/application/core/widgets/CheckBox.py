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

class CheckBox(QtGui.QCheckBox, Base):

  def __init__(self, parent, checked=False, text='', callback=None, **kw):

    QtGui.QCheckBox.__init__(self, parent)
    self.setChecked(checked)
    if text:
      self.setText(text)
    Base.__init__(self, **kw)

    if callback:
      self.connect(self, QtCore.SIGNAL('clicked()'), callback)

  def get(self):

    return self.isChecked()
