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
__author__ = 'simon'
from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.widgets.Base import Base
from ccpn.util.Translation import translator

class LineEdit(QtGui.QLineEdit, Base):

  def __init__(self, parent, text='', textColor=None, **kw):

    #text = translator.translate(text)

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

    #text = translator.translate(text)
    self.setText(text)