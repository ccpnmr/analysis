"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
__author__ = 'simon'
from PyQt4 import QtGui, QtCore

from ccpncore.gui.Base import Base

class LineEdit(QtGui.QLineEdit, Base):

  def __init__(self, parent, text='', textColor=None, **kw):

    QtGui.QLineEdit.__init__(self, text, parent)
    Base.__init__(self, **kw)

    if textColor:
      self.setStyleSheet('QLabel {color: %s;}' % textColor)

    self.setAlignment(QtCore.Qt.AlignHCenter)
    self.setMinimumWidth(150)
    self.setFixedHeight(25)

  def get(self):

    return self.text()

  def set(self, text=''):

    self.setText(self.translate(text))