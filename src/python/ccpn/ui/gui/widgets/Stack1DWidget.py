"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2020-09-11 19:09:41 +0100 (Fri, September 11, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-07-25 11:28:58 +0100 (Tue, July 25, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox, DoubleSpinbox
from ccpn.ui.gui.widgets.Spacer import Spacer


OffsetX = 'X Offset: '
OffsetY = 'Y Offset: '


class Offset1DWidget(Frame):
    def __init__(self, parent=None, mainWindow=None, strip1D=None, **kwds):
        super().__init__(parent, setLayout=True, **kwds)

        if mainWindow is None:  # This allows opening the popup for graphical tests
            self.mainWindow = None
            self.project = None
        else:
            self.mainWindow = mainWindow
            self.project = self.mainWindow.project
            self.application = self.mainWindow.application
            self.current = self.application.current

        self.offset = None
        self.strip1D = strip1D

        ii = 0
        self.labelOffset = Label(self, OffsetX, grid=(0, ii))
        ii += 1
        self.boxXOffset = ScientificDoubleSpinBox(self, step=0.0001, grid=(0, ii), min=-10000, max=10000, decimals=5)

        ii += 1
        self.labelOffset = Label(self, OffsetY, grid=(0, ii))
        ii += 1
        self.boxYOffset = ScientificDoubleSpinBox(self, step=0.1, grid=(0, ii), min=-1e100, max=1e100)

        ii += 1
        Spacer(self, 2, 2,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum,
               grid=(0, ii), gridSpan=(1, 1))
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Minimum)

        self.boxXOffset.setFixedWidth(100)
        self.boxYOffset.setFixedWidth(150)

        if self.strip1D is not None:
            self.boxXOffset.setValue(self.strip1D.offsetValue[0])
            self.boxYOffset.setValue(self.strip1D.offsetValue[1])

        self.boxXOffset.valueChanged.connect(self._applyOffset)
        self.boxYOffset.valueChanged.connect(self._applyOffset)

    def _applyOffset(self):
        if self.strip1D is not None:
            self.strip1D._stack1DSpectra(offSet=(self.boxXOffset.value(), self.boxYOffset.value()))

    def value(self):
        return (self.boxXOffset.value(), self.boxYOffset.value())

    def setValue(self, value):
        self.boxXOffset.set(value[0])
        self.boxYOffset.set(value[1])


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog


    app = TestApplication()
    popup = CcpnDialog()
    f = Offset1DWidget(popup)

    popup.show()
    popup.raise_()

    app.start()
