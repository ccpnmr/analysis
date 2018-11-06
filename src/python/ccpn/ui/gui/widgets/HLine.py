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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:46 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.util.Colour import hexToRgb

class HLine(Widget):
  def __init__(self, parent=None, style='SolidLine', colour=QtCore.Qt.black, height=10, **kwds):
    """
    :param style: Options: 
                          'SolidLine';
                           'DashLine'; 
                           'DashDotLine';
                           'DashDotDotLine'
    """

    super().__init__(parent, **kwds)
    self._parent = parent
    self.style = style
    self.colour = colour
    self.height = height
    self.lineHeight = int(height/3)

    self.styles = {
      'SolidLine':          QtCore.Qt.SolidLine,
      'DashLine':           QtCore.Qt.DashLine,
      'DashDotLine':        QtCore.Qt.DashDotLine,
      'DashDotDotLine':    QtCore.Qt.DashDotDotLine,
    }

    # self.setMaximumHeight(10)
    self.setFixedHeight(height)

  def paintEvent(self, e):
    qp = QtGui.QPainter()
    qp.begin(self)
    self.drawLine(qp, self.style)
    qp.end()

  def drawLine(self, qp, style=None, colour=None):

    if style in self.styles:
      style = self.styles[style]
      try:
        pen = QtGui.QPen(self.colour, 2, style)
      except:
        pen = QtGui.QPen(QtGui.QColor(*hexToRgb(self.colour)), 2, style)

      qp.setPen(pen)
      qp.drawLine(0, self.lineHeight, self.geometry().right(), self.lineHeight)

def main():
  app = QtWidgets.QApplication(sys.argv)
  ex = HLine()
  sys.exit(app.exec_())


if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.popups.Dialog import CcpnDialog
  from ccpn.ui.gui.widgets.Slider import SliderSpinBox

  app = TestApplication()
  popup = CcpnDialog(windowTitle='Test slider', setLayout=True)
  slider = SliderSpinBox(parent=popup, startVal=0, endVal=100, value=5, grid=(0 ,0))
  line = HLine(parent=popup, grid=(1 ,0))
  slider2 = SliderSpinBox(parent=popup, startVal=0, endVal=100, value=5, grid=(2, 0))
  popup.show()
  popup.raise_()
  app.start()


