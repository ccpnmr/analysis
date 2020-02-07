"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-02-07 19:17:10 +0000 (Fri, February 07, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister$"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets, QtCore, QtGui
from ccpn.ui.gui.widgets.Base import Base


SCROLLBAR_POLICY_DICT = dict(
        always=QtCore.Qt.ScrollBarAlwaysOn,
        never=QtCore.Qt.ScrollBarAlwaysOff,
        asNeeded=QtCore.Qt.ScrollBarAsNeeded,
        )


class ScrollArea(QtWidgets.QScrollArea, Base):

    def __init__(self, parent, scrollBarPolicies=('asNeeded', 'asNeeded'),
                 setLayout=True, minimumSizes=(50, 50), **kwds):
        super().__init__(parent)

        # kwds['setLayout'] = True  # A scrollable area always needs a layout to function
        Base._init(self, setLayout=setLayout, **kwds)

        self.setScrollBarPolicies(scrollBarPolicies)
        self.setMinimumSizes(minimumSizes)

    def setMinimumSizes(self, minimumSizes):
        """Set (minimumWidth, minimumHeight)
        """
        self.setMinimumWidth(minimumSizes[0])
        self.setMinimumHeight(minimumSizes[1])

    def setScrollBarPolicies(self, scrollBarPolicies=('asNeeded', 'asNeeded')):
        """Set the scrollbar policy: always, never, asNeeded
        """
        hp = SCROLLBAR_POLICY_DICT.get(scrollBarPolicies[0])
        vp = SCROLLBAR_POLICY_DICT.get(scrollBarPolicies[1])
        self.setHorizontalScrollBarPolicy(hp)
        self.setVerticalScrollBarPolicy(vp)

    def setWidget(self, widget):
        """Set the scroll area contents
        """
        super(ScrollArea, self).setWidget(widget)
        self._scrollContents = widget

    def resizeEvent(self, event):
        super(ScrollArea, self).resizeEvent(event)

        rect = self.viewport().geometry()
        try:
            from ccpn.ui.gui.widgets.GLWidgets import Gui1dWidgetAxis, GuiNdWidgetAxis

            children = self.findChildren(GuiNdWidgetAxis)
            if children:
                for child in children:
                    if child._axisType == 0:

                        child.setGeometry(0, rect.height() - 1, rect.width(), child.height())

                    else:

                        child.setGeometry(rect.width(), 0, child.width(), rect.height())

                    child._updateAxes = True
                    child.update()

        except:
            pass
