import re
from functools import partial
from PyQt5 import QtCore, QtWidgets
from math import isclose

from ccpn.ui.gui.widgets.CompoundWidgets import SpinBoxCompoundWidget
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox, VariableScientificSpinBox

from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.SpeechBalloon import SpeechBalloon
from ccpn.ui.gui.widgets.Spinbox import Spinbox


class SmallScienceSpinBox(VariableScientificSpinBox):
    def __init__(self, parent, specView, precision, *args, **kwargs):
        self.view = specView
        self.precision = precision

        super().__init__(parent, *args, **kwargs)

    def textFromValue(self, value):
        return self.formatFloat(value)

    def formatFloat(self, value):
        string = self._qLocale.toString(float(value), 'g', self.precision)
        return re.sub(r"e(-|\+?)0*(\d+)", r"e\1\2", string.replace("e+", "e"))

    def stepBy(self, step):
        if step == 1:
            self.view.traceScale *= 1.4
            self.update()
        if step == -1:
            self.view.traceScale /= 1.4
            self.update()

    def update(self):
        # added to refresh global trace scale.
        self.view._updateTraceScale()
        self.setValue(self.view.traceScale)


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
        self._metrics.pointer_height = 0

        self.globalSpinBox = None
        self.spinBoxes = []

        self.setWidgets()

    @property
    def centralWidgetSize(self):
        """Return the sizeHint for the central widget
        """
        return self._central_widget_size()

    def setWidgets(self):
        """add the widgets"""

        _frame = Frame(self, setLayout=True, margins=(10, 10, 10, 10))
        self.setCentralWidget(_frame)

        # Set global slider and label
        prefsValue = self.preferences.general.traceGlobalScale * 100
        Label(parent=_frame, text='Global Trace Multiplier', grid=(0, 0))
        self.globalSpinBox = Spinbox(parent=_frame, value=int(prefsValue),
                                     showButtons=True, grid=(0, 1),
                                     callback=self.globalSpinBoxCallback,
                                     min=0, max=99999, step=10)

        for row, view in enumerate(self.project.spectrumViews):
            row += 1

            label = Label(parent=_frame, text=view.pid, grid=(row, 0))
            spinBox = SmallScienceSpinBox(parent=_frame, value=view.traceScale, min=-1e11, max=1e11,
                                          grid=(row, 1), specView=view, precision=4)
            spinBox.setValue(view.traceScale)  # from call arg doesnt work for some reason.
            spinBox.setMinimumWidth(250)

            self.spinBoxes.append(spinBox)

    def globalSpinBoxCallback(self, _value):
        self.preferences.general.traceGlobalScale = self.globalSpinBox.value() / 100

        for spinBox in self.spinBoxes:
            spinBox.update()


def main():
    """Popup test
    """
    from ccpn.ui.gui.widgets.Application import TestApplication

    app = TestApplication()

    popup = TraceScaleBalloon(mainWindow=None)
    popup.exec_()


if __name__ == '__main__':
    main()
