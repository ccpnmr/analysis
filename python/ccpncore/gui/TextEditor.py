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
import sys
import os
from PyQt4 import QtGui

from ccpncore.gui.Base import Base

class TextEditor(QtGui.QTextEdit, Base):

  def __init__(self, parent=None, filename=None, **kw):
    super(TextEditor, self).__init__(parent)
    Base.__init__(self, **kw)
    #font = QFont("Courier", 11)
    #self.setFont(font)
    self.filename = filename
    # if self.filename is not None:
    #
    #   fileData = self.filename.read()
    #   print(fileData)
    #   self.setText(fileData)
    #
    # self.show()

  def get(self):
    return self.toPlainText()
