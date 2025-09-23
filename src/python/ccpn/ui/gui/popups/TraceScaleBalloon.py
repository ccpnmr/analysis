from PyQt5 import QtCore

from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.SpeechBalloon import SpeechBalloon

SPINBOX_WIDTH = 150
PADDING = 40


class TraceSpinBox(DoubleSpinbox):
    """A Custom double spin box for the TraceScale Balloon

    Subclass required for allowing very small numbers using scientific notation
    As well as for subclassing stepBy.
    """
    def __init__(self, parent, specView, *args, **kwargs):
        super().__init__(parent, value=1.0, decimals=2, *args, **kwargs)
        self.view = specView
        self.traceScaleDefault = 1.0 / self.view.traceMax
        # first call in case the trace scale has not already been calc'd
        _ = self.view.traceScale
        # needs to be _traceScale to keep independent of the global scale
        boxDefault = (self.view._traceScale / self.traceScaleDefault)
        self.setValue(boxDefault)

    def stepBy(self, step):
        """Subclassed to do the same thing as the TU and TD shortcuts"""
        if step == 1:
            self.setValue(self.get() * 1.4)
            self.update()
        if step == -1:
            self.setValue(self.get() / 1.4)
            self.update()

    def update(self):
        """Refresh the traceScale values in GUI"""
        self.view._traceScale = self.get() * self.traceScaleDefault
        self.view._updateTraceScale()


class TraceScaleBalloon(SpeechBalloon):
    """Balloon containing sliders to change Horizontal
     or vertical trace scales"""

    def __init__(self, parent, mainWindow=None, *args, **kwds):
        super().__init__(*args, **kwds)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
            self.preferences = self.application.preferences
        else:
            self.application = self.project = self.current = None

        self._parent = parent

        # simplest way to make the popup function as modal and disappear as required
        self.setWindowFlags(int(self.windowFlags()) | QtCore.Qt.Popup)
        self._metrics.corner_radius = 3

        self.globalSpinBox = None
        self.spinBoxes = []
        self.largestLabel = 0
        self.tempTraces = {}

        self.setWidgets()

    @property
    def centralWidgetSize(self):
        """Return the sizeHint for the central widget
        """
        return self._central_widget_size()

    def estimateHeight(self):
        """Estimates the height of the speech balloon based on
        number of spinboxes and padding used.

        This only exists because I couldn't get qt to report accurate
        sizes.
        """
        boxNum = len(self.spinBoxes) + 2
        boxHeight = self.globalSpinBox.geometry().height()
        return (boxNum * boxHeight) + PADDING

    def estimateWidth(self):
        """Estimates the width of the speech balloon including pointer
        based on the label and spinbox sizes, padding and pointer width

        This only exists because I couldn't get qt to report accurate
        sizes.
        """
        return self.largestLabel + SPINBOX_WIDTH + PADDING + self._metrics.pointer_width

    def setWidgets(self):
        """add the widgets"""

        _frame = Frame(self, setLayout=True, margins=(10, 10, 10, 10))
        self.setCentralWidget(_frame)

        # Set global slider and label
        label = Label(parent=_frame, text='Trace Multiplier', grid=(0, 0))
        self.globalSpinBox = DoubleSpinbox(parent=_frame, value=self._parent.displayTraceScale,
                                           showButtons=True, grid=(0, 1),
                                           callback=self.globalSpinBoxCallback,
                                           min=0, max=99999, step=0.1, decimal=3)

        for row, view in enumerate(self._parent.spectrumViews):
            row += 1

            Label(parent=_frame, text=view.pid, grid=(row, 0))
            spinBox = TraceSpinBox(parent=_frame, min=-9999, max=9999,
                                          grid=(row, 1), specView=view)

            spinBox.setMinimumWidth(SPINBOX_WIDTH)
            if label.width() > self.largestLabel:
                self.largestLabel = label.width()

            self.spinBoxes.append(spinBox)

    def globalSpinBoxCallback(self):
        self._parent.displayTraceScale = self.globalSpinBox.get()


def main():
    """Popup test
    """
    from ccpn.ui.gui.widgets.Application import TestApplication

    app = TestApplication()

    popup = TraceScaleBalloon(mainWindow=None)
    popup.exec_()


if __name__ == '__main__':
    main()
