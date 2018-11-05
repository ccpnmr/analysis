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
__dateModified__ = "$dateModified: 2017-07-07 16:32:56 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets

from ccpn.ui.gui.widgets.Base import Base

class Splitter(QtWidgets.QSplitter, Base):

  def __init__(self, parent=None, **kw):

    super().__init__(parent)
    Base._init(self, parent, **kw)

    self.doResize = False

  def createHandle(self):

    return SplitterHandle(self, self.orientation())

  def resizeEvent(self, event):

    self.doResize = True
    eventResult = QtWidgets.QSplitter.resizeEvent(self, event)
    self.doResize = False

    return eventResult

  def mouseDoubleClickEvent(self, event):
    # double-click to retrieve a lost splitter bar
    self.setSizes([1, 1])

    event.accept()

class SplitterHandle(QtWidgets.QSplitterHandle):

  def __init__(self, parent, orientation):

    QtWidgets.QSplitterHandle.__init__(self, orientation, parent)

  def mousePressEvent(self, event):

    self.parent().doResize = True
    return QtWidgets.QSplitter.mousePressEvent(self, event)

  def mouseReleaseEvent(self, event):

    self.parent().doResize = False
    return QtWidgets.QSplitter.mouseReleaseEvent(self, event)
