"""
Module Documentation here
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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:49 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-07-03 11:28:58 +0100 (Mon, Jul 3, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.popups.Dialog import CcpnDialog


class PPdimensionSelector(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, title='Select Dimension', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.buttons = ButtonList(self, texts=['Cancel', ' 1D ', ' ND '],
                                  callbacks=[self.reject, self._open1DpeakPicker, self._openNDpeakPicker],
                                  grid=(0, 0), hAlign='c')

        self.setMaximumWidth(self.size().width() * 3)
        self.setMaximumSize(self.maximumWidth(), self.maximumHeight())

    def _open1DpeakPicker(self):
        from ccpn.ui.gui.popups.PickPeaks1DPopup import PickPeak1DPopup

        self.reject()
        popup = PickPeak1DPopup(parent=self.mainWindow, mainWindow=self.mainWindow)
        popup.exec_()
        popup.raise_()

    def _openNDpeakPicker(self):
        from ccpn.ui.gui.popups.PeakFind import PeakFindPopup

        self.reject()
        popup = PeakFindPopup(parent=self.mainWindow, mainWindow=self.mainWindow)
        popup.exec_()
        popup.raise_()


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog


    app = TestApplication()
    popup = PPdimensionSelector()

    popup.show()
    popup.raise_()

    app.start()
