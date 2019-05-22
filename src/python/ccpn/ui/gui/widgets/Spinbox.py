"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:56 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Label import Label


class Spinbox(QtWidgets.QSpinBox, Base):

    def __init__(self, parent, prefix=None, value=None, step=None, min=None, max=None, showButtons=True, **kwds):

        super().__init__(parent)
        Base._init(self, **kwds)

        if min is not None:
            self.setMinimum(min)
        if max is not None:
            self.setMaximum(max)
        if value is not None:  #set Value only after you set min and max
            self.setValue(value)
        if step is not None:
            self.setSingleStep(step)
        if prefix:
            self.setPrefix(prefix + ' ')
        if showButtons is False:
            self.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)

    def get(self):
        return self.value()

    def set(self, p_int):
        self.setValue(p_int)


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog


    app = TestApplication()
    popup = CcpnDialog()
    sb = Spinbox(popup, step=10, grid=(0, 0))
    sb.setPrefix('H Weight ')

    popup.show()
    popup.raise_()

    app.start()
