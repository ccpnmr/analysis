"""

Frame(QtGui.QFrame, Base)


  From: http://pyqt.sourceforge.net/Docs/PyQt4/qframe.html#details

  The QFrame class is the base class of widgets that can have a frame. More...

  Inherits QWidget.

  Inherited by QAbstractScrollArea, QLabel, QLCDNumber, QSplitter, QStackedWidget and QToolBox.

  Types

  enum Shadow { Plain, Raised, Sunken }
  enum Shape { NoFrame, Box, Panel, WinPanel, ..., StyledPanel }
  enum StyleMask { Shadow_Mask, Shape_Mask }
  Methods

  __init__ (self, QWidget parent = None, Qt.WindowFlags flags = 0)
  changeEvent (self, QEvent)
  drawFrame (self, QPainter)
  bool event (self, QEvent e)
  QRect frameRect (self)
  Shadow frameShadow (self)
  Shape frameShape (self)
  int frameStyle (self)
  int frameWidth (self)
  int lineWidth (self)
  int midLineWidth (self)
  paintEvent (self, QPaintEvent)
  setFrameRect (self, QRect)
  setFrameShadow (self, Shadow)
  setFrameShape (self, Shape)
  setFrameStyle (self, int)
  setLineWidth (self, int)
  setMidLineWidth (self, int)
  QSize sizeHint (self)

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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:05 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui

from ccpn.ui.gui.widgets.Base import Base

class Frame(QtGui.QFrame, Base):

  def __init__(self, parent=None, **kw):

    QtGui.QFrame.__init__(self, parent)
    Base.__init__(self, **kw)

if __name__ == '__main__':

  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.BasePopup import BasePopup

  class TestPopup(BasePopup):
    def body(self, parent):
      frame = Frame(parent=parent, bgColor=QtGui.QColor(255, 255, 0))

  app = TestApplication()
  popup = TestPopup(title='Test Frame')
  popup.resize(400, 400)
  app.start()

