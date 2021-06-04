"""

Basic Usage:
  Example of a popup with 1 tab:
  
  tabWidget = Tabs(self, grid=(0,0), gridSpan=(1,3))
  
  ## create a frame. This will be the container with all the widgets that will go in the first tab
  
  tab1Frame = Frame(self, setLayout=True)
  
  ## add all the children to the frame
  
  label = Label(tab1Frame, "Example tab 1", grid=(0, 0))
  
  ## add the frame to the TabsWidget to activate as a new tab
  
  tabWidget.addTab(tab1Frame, 'Tab1')
  
  
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-06-04 19:38:31 +0100 (Fri, June 04, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.widgets.Base import Base


class Tabs(QtWidgets.QTabWidget, Base):
    def __init__(self, parent, **kwds):
        super().__init__(parent)
        Base._init(self, **kwds)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self._tabBarClickCallback = None
        self.tabBarClicked.connect(self._tabBarClicked)

    def setTabClickCallback(self, callback):
        if callback and callable(callback):
            self._tabBarClickCallback = callback

    def clearTabClickCallback(self):
        self._tabBarClickCallback = None

    def _tabBarClicked(self, index):
        if self._tabBarClickCallback and callable(self._tabBarClickCallback):
            self._tabBarClickCallback(index)

    @property
    def tabs(self):
        return self.children()


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.Frame import Frame
    from ccpn.ui.gui.widgets.Label import Label
    from ccpn.ui.gui.popups.Dialog import CcpnDialog


    app = TestApplication()
    popup = CcpnDialog()

    tabWidget = Tabs(popup, grid=(0, 0), gridSpan=(1, 3))

    tab1Frame = Frame(popup, setLayout=True)
    for i in range(5):
        Label(tab1Frame, "Example tab 1", grid=(i, 0))

    tabWidget.addTab(tab1Frame, 'Tab1')

    tab2Frame = Frame(popup, setLayout=True)
    for i in range(5):
        Label(tab2Frame, "Example tab 2", grid=(i, 0))
    tabWidget.addTab(tab2Frame, 'Tab2')


    popup.show()
    popup.raise_()

    app.start()
