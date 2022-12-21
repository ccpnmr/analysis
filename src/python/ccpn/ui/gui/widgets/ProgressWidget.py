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
__dateModified__ = "$dateModified: 2022-12-21 12:16:47 +0000 (Wed, December 21, 2022) $"
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


#=========================================================================================
# Gui progress-dialog
#=========================================================================================

class ProgressDialog(QtWidgets.QProgressDialog):
    class ProgressCancelled(Exception):
        """Exception to catch cancelled progress/busy dialogs
        """
        pass


    def __init__(self, parent, title='Progress Dialog', text='busy...', minimum=0, maximum=100,
                 delay=1000, steps=100, closeDelay=250, autoClose=True, hideCancelButton=False):
        super().__init__(parent=parent)

        self.setWindowTitle(title)
        self.setText(text)
        self.setAutoReset(autoClose)
        self.setAutoClose(autoClose)
        self.setMinimumDuration(delay)
        self._closeDelay = closeDelay / 1000 if isinstance(closeDelay, (int, float)) else 0
        self._cancelled = False
        self._error = None

        self.setRange(minimum, maximum)
        self.steps = steps

        # give full control to the dialog
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        # hide the cancel-button
        if hideCancelButton:
            self.setCancelButton(None)

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def steps(self):
        """Return number of steps for the progress-bar
        """
        return self._steps

    @steps.setter
    def steps(self, value):
        """Set the number of steps
        Use 0 or None to disable and update on every iteration
        """
        if not isinstance(value, (int, type(None))):
            raise TypeError(f'{self.__class__.__name__}.steps must be an int or None')
        if isinstance(value, int) and value < 0:
            raise ValueError(f'{self.__class__.__name__}.steps must be a positive int')

        if value:
            self._steps = value
            self._step = int((self.maximum() - self.minimum()) // value) + 1
        else:
            # stepping is disabled, updates for every iteration
            self._steps = None
            self._step = 1

    @property
    def step(self):
        """Return interval based on number of required steps
        Returns 0 if disabled
        """
        return self._step

    @property
    def cancelled(self):
        """Return True if the dialog was cancelled"""
        return self._cancelled

    @property
    def error(self):
        """Return the last error
        """
        return self._error

    @error.setter
    def error(self, value):
        """Set the error
        """
        self._error = value

    #=========================================================================================
    # Methods
    #=========================================================================================

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

    def percent(self, decimals=0):
        return round(100.0 * self.getProportion(), decimals)

    # setRange() inbuilt
    # reset() inbuilt
    # setText() inbuilt

    def set(self, value, force=False):
        """Set the current value.
        Updates the progress-bar if the value matches the current number of steps to show.
        value if a fraction in the range[0, 1]
        Set force = True to manually update the progress-bar.
        :param value: value to set
        :param force: True/False
        """
        if (value not in (0, 1)) and value <= 1.0:
            a = self.minimum()
            b = self.maximum()
            value = float(value) * (b - a)
            value += a

        self.setValue(int(value), force=force)

    def setValue(self, value, force=False):
        """Set the current value.
        Updates the progress-bar if the value matches the current number of steps to show.
        Set force = True to manually update the progress-bar.
        :param value: value to set
        :param force: True/False
        """
        if force or value % self._step == 0:
            super().setValue(value)

    def setMinimum(self, minimum: int) -> None:
        """Set the minimum value
        """
        super().setMinimum(minimum)

        self._updateSteps()

    def setMaximum(self, maximum: int) -> None:
        """Set the maximum value
        """
        super().setMaximum(maximum)

        self._updateSteps()

    def setRange(self, minimum: int, maximum: int) -> None:
        """Set the minimum/maximum values
        """
        super().setRange(minimum, maximum)

        self._updateSteps()

    def _updateSteps(self):
        """Update internal properties
        """
        if getattr(self, '_steps', None):
            self._step = int((self.maximum() - self.minimum()) // self._steps) + 1
        else:
            # stepping is disabled, updates for every iteration
            self._step = 1

    #=========================================================================================
    # Implementation
    #=========================================================================================

    def cancel(self):
        """Cancel the progress-bar or closure
        """
        self._cancelled = True
        raise self.ProgressCancelled

    def finalise(self):
        """Set the progress to 100%
        """
        super().setValue(self.maximum())

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

    def checkCancelled(self):
        """Raise a ProgressCancelled exception if the cancel button is pressed
        """
        if self.wasCanceled():
            self.cancel()


#=========================================================================================
# Gui progress-widget
#=========================================================================================

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


#=========================================================================================
# non-gui progress-widget
#=========================================================================================

class ProgressTextBar(tqdm):
    class ProgressCancelled(Exception):
        """Exception to catch cancelled progress/busy dialogs
        """
        pass


    def __init__(self, parent, title='Progress Dialog', text='busy...', minimum=0, maximum=100,
                 delay=1000, closeDelay=250, steps=100,
                 autoClose=True, hideCancelButton=True):

        self._minimum = minimum
        self._maximum = maximum
        self.steps = steps
        self._cancelled = False
        self._error = None

        miniters = ((maximum - minimum) / self._steps) if self._steps else 0
        super().__init__(initial=0, total=maximum - minimum, delay=delay / 1000,
                         ncols=120, miniters=miniters
                         )
        # for compatibility with ProgressDialog above - perform no operation
        self._closeDelay = closeDelay
        self._autoClose = autoClose

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def minimum(self):
        return self._minimum

    @property
    def maximum(self):
        return self._maximum

    @property
    def steps(self):
        """Return number of steps for the progress-bar
        """
        return self._steps

    @steps.setter
    def steps(self, value):
        """Set the number of steps
        Use 0 or None to disable and update on every iteration
        """
        if not isinstance(value, (int, type(None))):
            raise TypeError(f'{self.__class__.__name__}.steps must be an int or None')
        if isinstance(value, int) and value < 0:
            raise ValueError(f'{self.__class__.__name__}.steps must be a positive int')

        if value:
            self._steps = value
            self._step = int((self._maximum - self._minimum) // value) + 1
        else:
            # stepping is disabled, updates for every iteration
            self._steps = None
            self._step = 1

    @property
    def step(self):
        """Return interval based on number of required steps
        Returns 0 if disabled
        """
        return self._step

    @property
    def cancelled(self):
        """Return True if the dialog was cancelled"""
        return self._cancelled

    @property
    def error(self):
        """Return the last error
        """
        return self._error

    @error.setter
    def error(self, value):
        """Set the error
        """
        self._error = value

    #=========================================================================================
    # Methods
    #=========================================================================================

    def setText(self, text):
        self.set_description(text)

    def increment(self, n=1):
        self.update(n)

    def getValue(self):
        return self.n

    def getProportion(self):
        return self.n / (self.total or 1)

    def percent(self, decimals=0):
        frac = self.n / (self.total or 1)
        percent = frac * 100
        return round(percent, decimals)

    # setRange() inbuilt
    # reset() inbuilt
    # setText() inbuilt

    def set(self, value, force=False):
        if (value not in (0, 1)) and value <= 1.0:
            a = self.initial
            b = self.total
            value = float(value) * (b - a)
            value += a

        self.setValue(int(value), force=force)

    def setValue(self, value, force=False):
        """Increment the counter to the required value
        """
        val = value - self.n - self._minimum
        if force or val % self._step == 0:
            self.update(val)

    #=========================================================================================
    # Implementation
    #=========================================================================================

    def cancel(self):
        """Cancel the progress-bar or closure
        """
        self.disable = True
        self._cancelled = True
        raise self.ProgressCancelled

    @staticmethod
    def wasCanceled():
        return False

    def checkCancelled(self):
        if self.wasCanceled():
            self.cancel()

    def finalise(self):
        """Set the progress to 100%
        """
        self.setValue(self._maximum, force=True)

    def waitForEvents(self):
        """Process events and sleep if visible (to stop quick popup)
        """
        self.close()


#=========================================================================================
# Busy progress
#=========================================================================================

class BusyDialog(ProgressDialog):
    """A progress-dialog that pops up immediately without a cancel button or progress-bar
    """

    def __init__(self, parent, hideBar=True, hideCancelButton=True, *args, **kwds):
        """Initialise the dialog
        """
        # show the dialog immediately
        kwds.pop('delay', 0)
        super().__init__(parent, delay=0, *args, **kwds)

        # hide the progress-bar
        if hideBar and (ch := self.findChildren(QtWidgets.QProgressBar)):
            for cc in ch:
                cc.setVisible(False)

        # hide the cancel-button
        if hideCancelButton:
            self.setCancelButton(None)


#=========================================================================================
# Testing
#=========================================================================================

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
    from ccpn.core.lib.ContextManagers import progressHandler, busyHandler
    from time import sleep

    # create a new test application
    app = newTestApplication(interface='Gui')
    application = getApplication()
    mainWindow = application.ui.mainWindow

    # add a module
    # _module = ProgressDialog(parent=mainWindow)
    # mainWindow.moduleArea.addModule(_module)

    with busyHandler():
        for _ in range(10):
            sleep(1)
    # show the mainWindow
    app.start()


if __name__ == '__main__':
    main()
