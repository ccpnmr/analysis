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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:47 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-07-25 11:28:58 +0100 (Tue, July 25, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox


Offset = 'Offset Value: '


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

        i = 0
        self.labelOffset = Label(self, Offset, grid=(0, i))
        i += 1
        self.boxOffset = ScientificDoubleSpinBox(self, step=1000, grid=(0, i))

        if self.strip1D is not None:
            self.boxOffset.setValue(self.strip1D.offsetValue)
        self.boxOffset.valueChanged.connect(self._applyOffset)

    def _applyOffset(self):
        if self.strip1D is not None:
            self.strip1D._stack1DSpectra(offSet=self.boxOffset.value())

    def value(self):
        return self.boxOffset.value()

    def setValue(self, value):
        self.boxOffset.set(value)


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog


    app = TestApplication()
    popup = CcpnDialog()
    f = Offset1DWidget(popup)

    popup.show()
    popup.raise_()

    app.start()
