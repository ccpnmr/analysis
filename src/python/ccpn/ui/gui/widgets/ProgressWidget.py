"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-07-04 18:52:00 +0100 (Thu, July 04, 2024) $"
__version__ = "$Revision: 3.2.5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-04-11 21:54:44 +0100 (Mon, April 11, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import time
from tqdm import tqdm
from time import sleep, perf_counter
from PyQt5 import QtWidgets, QtCore, QtGui
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Label import Label


#=========================================================================================
# Gui progress-dialog
#=========================================================================================

class ProgressDialog(QtWidgets.QProgressDialog):

    def __init__(self, parent=None, *, title: str = 'Progress Dialog',
                 text: str = 'Busy...', cancelButtonText: str = 'Cancel',
                 minimum: int = 0, maximum: int = 100, steps: int = 100,
                 delay: int = 1000, closeDelay: int = 250,
                 hideBar: bool = False, hideCancelButton: bool = False):

        from ccpn.framework.Application import getMainWindow

        # get the top-level window to attach the dialog to
        #   this cause major issue if attached to a window other than the current modal
        #   can still be set with parent
        parent = (parent or
                  QtWidgets.QApplication.activeModalWidget() or
                  QtWidgets.QApplication.activeWindow() or
                  getMainWindow())
        # remove the borders/buttons
        super().__init__(text, cancelButtonText, minimum, maximum, parent,
                         QtCore.Qt.CustomizeWindowHint)
        self.setWindowTitle(title)
        self.setAutoReset(False)  # reset on maximum-value
        self.setAutoClose(True)  # close when reset
        self.setMinimumDuration(delay)
        self._closeDelay = closeDelay / 1000 if isinstance(closeDelay, (int, float)) else 0  # changes ms->s
        self._delay = delay / 1000.0
        self._cancelled = False
        self._error = None
        self._hideCancelButton = hideCancelButton
        self.steps = steps
        # give full control to the dialog
        self.setWindowModality(QtCore.Qt.WindowModal)
        # self.setAttribute(QtCore.Qt.WA_AlwaysStackOnTop)
        # hide the cancel-button
        if hideCancelButton:
            self.setCancelButton(None)
        # hide the progress-bar
        self._hideBar = hideBar
        if hideBar and (ch := self.findChildren(QtWidgets.QProgressBar)):
            for cc in ch:
                cc.hide()
        if not delay:
            self.forceShow()
        self._start = time.perf_counter()

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
            # stepping is disabled, updates every iteration
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
        self.setLabelText(text)

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
        if force or (value % self._step == 0):
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
        super().cancel()
        self.checkCancel()

    def checkCancel(self):
        """Raise a StopIteration exception if the cancel button has been pressed
        """
        if self.wasCanceled():
            self._cancelled = True
            raise StopIteration

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
        #   (timers are in seconds)
        eTime = perf_counter() - sTime
        if (eTime < self._closeDelay) and self.isVisible():
            sleep(self._closeDelay - eTime)
        self.close()


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

    def __init__(self, parent=None, *,
                 minimum: int = 0, maximum: int = 100, steps: int = 100,
                 delay: int = 1000, **kwds):
        # other parameters from ProgressDialog are ignored (harvested by **kwds if required)
        self._minimum = minimum
        self._maximum = maximum
        self.steps = steps
        self._cancelled = False
        self._error = None
        super().__init__(initial=0, total=maximum - minimum + 1, delay=delay / 1000,
                         ncols=120, miniters=None
                         )

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
            # stepping is disabled, updates every iteration
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
        return self.value()

    def value(self):
        return self.n

    def getProportion(self):
        return self.n / (self.total or 1)

    def percent(self, decimals=0):
        return round(100.0 * self.getProportion(), decimals)

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

    def setValue(self, value=0, force=False):
        """Increment the counter to the required value
        """
        self.update(value - self.n - self._minimum + 1)

    def setRange(self, minimum: int, maximum: int) -> None:
        """Set the minimum/maximum values
        """
        self.reset(total=maximum - minimum + 1)

    #=========================================================================================
    # Implementation
    #=========================================================================================

    def cancel(self):
        """Cancel the progress-bar or closure
        """
        self._cancelled = True
        self.checkCancel()

    def wasCanceled(self):
        return self._cancelled

    def checkCancel(self):
        if self.wasCanceled():
            self.disable = True
            self._cancelled = True
            self.close()
            raise StopIteration

    def finalise(self):
        """Set the progress to 100%
        """
        self.update(self.total)

    def waitForEvents(self):
        """Process events and sleep if visible (to stop quick popup)
        """
        ...


#=========================================================================================
# Busy progress
#=========================================================================================

class BusyDialog(ProgressDialog):
    """A progress-dialog that pops up immediately without a cancel button or progress-bar
    """

    def __init__(self, parent=None, *args, delay: int = 0,
                 hideBar: bool = True, hideCancelButton: bool = True,
                 **kwds):
        """Initialise the dialog
        """
        # show the dialog immediately - or small delay to allow child-widgets to hide
        super().__init__(parent, delay=delay,
                         hideBar=hideBar, hideCancelButton=hideCancelButton,
                         *args, **kwds)


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
