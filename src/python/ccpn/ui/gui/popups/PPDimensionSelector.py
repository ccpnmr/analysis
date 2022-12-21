"""
Module Documentation here
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
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-12-21 12:16:46 +0000 (Wed, December 21, 2022) $"
__version__ = "$Revision: 3.1.0 $"
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
        # popup.raise_()

    def _openNDpeakPicker(self):
        from ccpn.ui.gui.popups.PeakFind import PeakFindPopup

        self.reject()
        popup = PeakFindPopup(parent=self.mainWindow, mainWindow=self.mainWindow)
        popup.exec_()
        # popup.raise_()


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog


    app = TestApplication()
    popup = PPdimensionSelector()

    popup.show()
    popup.raise_()

    app.start()
