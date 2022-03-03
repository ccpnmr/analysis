"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-03-03 16:50:20 +0000 (Thu, March 03, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Font import getFontHeight


class Splitter(QtWidgets.QSplitter, Base):
    """CcpNmr widgets: Splitter class
    """

    def __init__(self, parent=None, horizontal=True, collapsible=False, **kwds):

        super().__init__(parent)
        Base._init(self, **kwds)

        if horizontal:
            self.setOrientation(QtCore.Qt.Horizontal)
        else:
            self.setOrientation(QtCore.Qt.Vertical)

        self.setChildrenCollapsible(collapsible)
        self.doResize = False

        _height = 5         #(getFontHeight(size='MEDIUM') or 16) // 3
        _vName = Icon('icons/vertical-split')
        _hName = Icon('icons/horizontal-split')

        self.setStyleSheet("""QSplitter {background-color: transparent; }
                            QSplitter::handle:vertical {background-color: transparent; height: %dpx; image: url(%s); }
                            QSplitter::handle:horizontal {background-color: transparent; height: %dpx; image: url(%s); }
                            """ % (_height, _vName._filePath, _height, _hName._filePath))

    def createHandle(self):

        return SplitterHandle(self, self.orientation())

    def resizeEvent(self, event):
        """Catch resize event
        """
        self.doResize = True
        eventResult = QtWidgets.QSplitter.resizeEvent(self, event)
        self.doResize = False

        return eventResult

    def mouseDoubleClickEvent(self, event):
        """double-click to retrieve a lost splitter bar
        """
        self.setSizes([1, 1])
        event.accept()


class SplitterHandle(QtWidgets.QSplitterHandle):

    def __init__(self, parent, orientation):
        QtWidgets.QSplitterHandle.__init__(self, orientation, parent)

    def mousePressEvent(self, event):
        self.parent().doResize = True
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.parent().doResize = False
        return super().mouseReleaseEvent(event)
