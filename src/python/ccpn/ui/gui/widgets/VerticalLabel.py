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
from ccpn.ui.gui.widgets.Base import Base
from ccpn.util.Translation import translator


class VerticalLabel(QtGui.QWidget, Base):

    def __init__(self, parent, text, **kwargs):

      text = translator.translate(text)

      QtGui.QWidget.__init__(self, parent)
      self.text = text
      self.setText(text)
      self.height = parent.height()
      Base.__init__(self, **kwargs)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(QtCore.Qt.black)
        painter.translate(20, 200)
        painter.rotate(-90)
        painter.drawText(0, 0, self.text)
        painter.end()

    def setText(self, text):

      text = translator.translate(text)

      self.text = text
      self.repaint()