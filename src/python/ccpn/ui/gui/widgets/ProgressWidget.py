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
__dateModified__ = "$dateModified: 2022-07-05 13:20:42 +0100 (Tue, July 05, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-04-11 21:54:44 +0100 (Mon, April 11, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from tqdm import tqdm
from time import sleep, perf_counter
from PyQt5 import QtWidgets, QtCore
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Label import Label


class ProgressDialog(QtWidgets.QProgressDialog):

    def __init__(self, parent, title='Progress Dialog', text='busy...', minimum=0, maximum=100,
                 delay=1000, closeDelay=250, autoClose=True):
        super().__init__(parent=parent)

        self.setWindowTitle(title)
        self.setText(text)
        self.setRange(minimum, maximum)
        self.setAutoReset(autoClose)
        self.setAutoClose(autoClose)
        self.setMinimumDuration(delay)
        self._closeDelay = closeDelay / 1000 if isinstance(closeDelay, (int, float)) else 0

        # give full control to the dialog
        self.setWindowModality(QtCore.Qt.ApplicationModal)

    def setText(self, text):
        self._label = Label(self, text=text, margins=(8, 16, 8, 8))
        self.setLabel(self._label)

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

    def finalise(self):
        """Set the progress to 100%
        """
        self.setValue(self.maximum())

    def waitForEvents(self):
        """Process events and sleep if visible (to stop quick popup)
        """
        sTime = perf_counter()

        # wait for threads to complete
        _threads = QtCore.QThreadPool.globalInstance()
        _threads.waitForDone()

        # process any remaining events
        QtWidgets.QApplication.processEvents()

        # pause so that the counter doesn't flicker if too quick
        eTime = perf_counter() - sTime
        if (eTime < self._closeDelay) and self.isVisible():
            sleep(self._closeDelay)

        self.close()


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


class ProgressTextBar(tqdm):

    def __init__(self, parent, title='Progress Dialog', text='busy...', minimum=0, maximum=100, delay=1000, closeDelay=250, autoClose=True):
        super().__init__(initial=minimum, total=maximum - minimum, delay=delay / 1000,
                         ncols=120, miniters=(maximum - minimum) / 100)
        # for compatibility with ProgressDialog above - perform no operation
        self._closeDelay = closeDelay
        self._autoClose = autoClose

    def setText(self, text):
        self.set_description(text)

    def increment(self, n=1):
        self.update(n)

    def getValue(self):
        return self.n

    def getProportion(self):
        a = self.initial
        b = self.total
        return (self.n - a) / (b - a)

    # setRange() inbuilt
    # reset() inbuilt
    # setText() inbuilt

    def set(self, value):
        if (value not in (0, 1)) and value <= 1.0:
            a = self.initial
            b = self.total
            value = float(value) * (b - a)
            value += a

        self.setValue(int(value))

    def setValue(self, value):
        """Increment the counter to the required value
        """
        val = value - self.n - self.initial
        self.update(val)

    @staticmethod
    def wasCanceled():
        return False

    def finalise(self):
        """Set the progress to 100%
        """
        self.setValue(self.total + self.initial)

    def waitForEvents(self):
        """Process events and sleep if visible (to stop quick popup)
        """
        self.close()


def main():
    # import time
    # from .Application import Application
    # from .BasePopup import BasePopup
    #
    #
    # app = Application()
    #
    # window = BasePopup()
    # window.setSize(200, 50)
    # window.show()
    #
    # pb1 = ProgressDialog(window, text='Increments')
    # pb2 = ProgressWidget(window)
    #
    # for i in range(100):
    #     time.sleep(0.1)
    #     pb1.setValue(i)
    #     #pb1.increment()
    #
    # for i in range(100):
    #     time.sleep(0.1)
    #     pb2.setValue(100 - i)
    #
    # app.start()

    from ccpn.ui.gui.widgets.Application import newTestApplication
    from ccpn.framework.Application import getApplication

    # create a new test application
    app = newTestApplication(interface='Gui')
    application = getApplication()
    mainWindow = application.ui.mainWindow

    # add a module
    _module = ProgressDialog(parent=mainWindow)
    mainWindow.moduleArea.addModule(_module)

    # show the mainWindow
    app.start()


if __name__ == '__main__':
    main()
