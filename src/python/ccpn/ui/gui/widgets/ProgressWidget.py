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
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-04-13 19:23:20 +0100 (Wed, April 13, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-04-11 21:54:44 +0100 (Mon, April 11, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets.Base import Base


class ProgressDialog(QtWidgets.QProgressDialog):

    def __init__(self, parent=None, text='', minimum=0, maximum=99):
        super().__init__(parent=None)

        self.setText(text)
        self.setRange(minimum, maximum)
        self.setAutoReset(True)
        self.setAutoClose(True)
        self.setMinimumDuration(1000)

    def setText(self, text):
        self.setLabel(QtWidgets.QLabel(text, self))

    def increment(self, n=1):
        self.setValue(self.value() + n)

    def getValue(self):
        return self.value()

    def getProportion(self):
        a = self.minimum()
        b = self.maximum()
        return (self.value() - a) / (b - a)

    # setRange() inbuilt
    # reset() inbuilt
    # setText() inbuilt

    def set(self, value):
        if (value not in (0, 1)) and value <= 1.0:
            a = self.minimum()
            b = self.maximum()
            value = float(value) * (b - a)
            value += a

        self.setValue(int(value))


class ProgressWidget(QtWidgets.QProgressBar, Base):

    def __init__(self, parent=None, minimum=0,
                 maximum=99, total=None, **kw):
        QtWidgets.QProgressBar.__init__(self, parent=None)
        Base.__init__(self, parent, **kw)

        self.setRange(minimum, maximum)
        self.show()

    def increment(self, n=1):
        self.setValue(self.value() + n)

    def getValue(self):
        return self.value()

    def getProportion(self):
        a = self.minimum()
        b = self.maximum()
        return (self.value() - a) / (b - a)

    def set(self, value):
        if (value not in (0, 1)) and value <= 1.0:
            a = self.minimum()
            b = self.maximum()
            value = float(value) * (b - a)
            value += a

        self.setValue(int(value))


if __name__ == '__main__':

    import time
    from .Application import Application
    from .BasePopup import BasePopup


    app = Application()

    window = BasePopup()
    window.setSize(200, 50)
    window.show()

    pb1 = ProgressDialog(window, text='Increments')
    pb2 = ProgressWidget(window)

    for i in range(100):
        time.sleep(0.1)
        pb1.setValue(i)
        #pb1.increment()

    for i in range(100):
        time.sleep(0.1)
        pb2.setValue(100 - i)

    app.start()

    from ccpn.ui.gui.widgets.Application import newTestApplication
    from ccpn.framework.Application import getApplication


    # create a new test application
    app = newTestApplication(interface='Gui')
    application = getApplication()
    mainWindow = application.ui.mainWindow

    # add a module
    _module = ProgressWidget(mainWindow=mainWindow)
    mainWindow.moduleArea.addModule(_module)

    # show the mainWindow
    app.start()
