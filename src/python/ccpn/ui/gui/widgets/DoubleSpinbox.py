"""Module Documentation here

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
__dateModified__ = "$dateModified: 2020-06-02 09:52:54 +0100 (Tue, June 02, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import re
from contextlib import contextmanager
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal
from ccpn.ui.gui.widgets.Base import Base
from math import floor, log10


DOUBLESPINBOXSTEP = 10
SCIENTIFICSPINBOXSTEP = 5
KEYVALIDATELIST = (QtCore.Qt.Key_Return,
                   QtCore.Qt.Key_Enter,
                   QtCore.Qt.Key_Tab,
                   QtCore.Qt.Key_Up,
                   QtCore.Qt.Key_Down,
                   QtCore.Qt.Key_Left,
                   QtCore.Qt.Key_Right)


class DoubleSpinbox(QtWidgets.QDoubleSpinBox, Base):
    # # To be done more rigorously later
    # _styleSheet = """
    # DoubleSpinbox {
    #   background-color: #f7ffff;
    #   color: #122043;
    #   margin: 0px 0px 0px 0px;
    #   padding: 2px 2px 2px 2px;
    #   border: 1px solid #182548;
    # }
    #
    # DoubleSpinbox::hover {
    #   background-color: #e4e15b;
    # }
    # """
    returnPressed = pyqtSignal(float)
    wheelChanged = pyqtSignal(float)

    defaultMinimumSizes = (0, 20)

    def __init__(self, parent, value=None, min=None, max=None, step=None, prefix=None, suffix=None,
                 showButtons=True, decimals=None, callback=None, editable=True, **kwds):
        """
        From the QTdocumentation
        Constructs a spin box with a step value of 1.0 and a precision of 2 decimal places.
        Change the default 0.0 minimum value to -sys.float_info.max
        Change the default 99.99  maximum value to sys.float_info.max
        The value is default set to 0.00.

        The spin box has the given parent.
        """
        self.validator = QtGui.QDoubleValidator()
        self.validator.Notation = 1

        super().__init__(parent)
        Base._init(self, **kwds)

        # if value is not None:
        #   value = value
        #   # self.setValue(value)

        if min is not None:
            self.setMinimum(min)
        else:
            self.setMinimum(-1.0 * sys.float_info.max)

        if max is not None:
            self.setMaximum(max)
        else:
            self.setMaximum(sys.float_info.max)

        self.isSelected = False

        if step is not None:
            self.setSingleStep(step)

        if decimals is not None:
            self.setDecimals(decimals)

        if showButtons is False:
            self.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)

        if prefix:
            self.setPrefix(prefix + ' ')

        if suffix:
            self.setSuffix(' ' + suffix)

        self._callback = None
        self.setCallback(callback)

        # self.setMinimumWidth(self.defaultMinimumSizes[0])
        # self.setMinimumHeight(self.defaultMinimumSizes[1])

        if value is not None:
            value = value
            self.setValue(value)

        lineEdit = self.lineEdit()
        lineEdit.returnPressed.connect(self._keyPressed)

        self._internalWheelEvent = True
        self._keyPressed = False

        # change focusPolicy so that spinboxes don't grab focus unless selected
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """Process the wheelEvent for the doubleSpinBox
        """
        # emit the value when wheel event has occurred, only when hasFocus
        if self.hasFocus() or not self._internalWheelEvent:
            super().wheelEvent(event)
            self.wheelChanged.emit(self.value())
        else:
            event.ignore()

    @contextmanager
    def _useExternalWheelEvent(self):
        try:
            self._internalWheelEvent = False
            yield
        finally:
            self._internalWheelEvent = True

    def _externalWheelEvent(self, event):
        with self._useExternalWheelEvent():
            self.wheelEvent(event)

    def stepBy(self, steps: int) -> None:
        if self._internalWheelEvent:
            super().stepBy(min(steps, DOUBLESPINBOXSTEP) if steps > 0 else max(steps, -DOUBLESPINBOXSTEP))
        else:
            # disable multiple stepping for wheelMouse events in a spectrumDisplay
            super().stepBy(1 if steps > 0 else -1 if steps < 0 else steps)

    def _keyPressed(self, *args):
        """emit the value when return has been pressed
        """
        self.returnPressed.emit(self.value())

    def get(self):
        return self.value()

    def set(self, value):
        self.setValue(value)

    def setSelected(self):
        self.isSelected = True

    def focusInEvent(self, QFocusEvent):
        self.setSelected()
        super(DoubleSpinbox, self).focusInEvent(QFocusEvent)

    def setCallback(self, callback):
        """Sets callback; disconnects if callback=None
        """
        if self._callback is not None:
            self.valueChanged.disconnect()
        if callback:
            self.valueChanged.connect(callback)
        self._callback = callback

    def validate(self, text, position):
        # activate the validator when
        if self._keyPressed:
            return self.validator.Intermediate, text, position
        else:
            return self.validator.validate(text, position)

    def keyPressEvent(self, event):
        # allow the typing of other stuff into the box and validate only when required
        self._keyPressed = False if event.key() in KEYVALIDATELIST else True
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self._keyPressed = False
        super().keyReleaseEvent(event)


# Regular expression to find floats. Match groups are the whole string, the
# whole coefficient, the decimal part of the coefficient, and the exponent
# part.
_float_re = re.compile(r'(([+-]?\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)')


def fexp(f):
    return int(floor(log10(abs(f)))) if f != 0 else 0


class ScientificDoubleSpinBox(DoubleSpinbox):
    """Constructs a spinbox in which the values can be set using Sci notation
    """

    def __init__(self, *args, **kwargs):
        super(ScientificDoubleSpinBox, self).__init__(*args, **kwargs)
        self.setDecimals(1000)

    def fixup(self, text):
        return self.validator.fixup(text)

    def valueFromText(self, text):
        """Values in the spinbox are constrained to the correct sign if the min/max values are
        either both positive or both negative
        """
        if self.minimum() <= 0 and self.maximum() <= 0:
            # check for maximum
            val = min(-abs(float(text)), self.maximum())
            self.lineEdit().setText(self.textFromValue(val))
            return val

        elif self.minimum() >= 0 and self.maximum() >= 0:
            # check for minimum
            val = max(abs(float(text)), self.minimum())
            self.lineEdit().setText(self.textFromValue(val))
            return val

        return float(text)

    def textFromValue(self, value):
        return self.formatFloat(value)

    def stepBy(self, steps):
        """Increment the current value.
        Step if 1/10th of the current rounded value * step
        """
        # clip number of steps to SCIENTIFICSPINBOXSTEP as 10* will go directly to zero from 1 when Ctrl/Cmd pressed
        steps = min(steps, SCIENTIFICSPINBOXSTEP) if steps > 0 else max(steps, -SCIENTIFICSPINBOXSTEP)

        text = self.cleanText()
        groups = _float_re.search(text).groups()
        decimal = float(groups[1])
        decimal += steps * 10 ** fexp(decimal / 10)  #     (decimal / 10)
        new_string = '{:g}'.format(decimal) + (groups[3] if groups[3] else '')

        # the double convert ensures number stays to the closest Sci notation
        self.lineEdit().setText(self.textFromValue(self.valueFromText(new_string)))

    def formatFloat(self, value):
        """Modified form of the 'g' format specifier.
        """
        string = "{:g}".format(value).replace("e+", "e")
        string = re.sub("e(-?)0*(\d+)", r"e\1\2", string)
        return string


v = float("{0:.3f}".format(0.024))
v1 = 0.029

if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog
    from ccpn.ui.gui.widgets.Frame import Frame


    app = TestApplication()
    popup = CcpnDialog()
    fr = Frame(popup, setLayout=True)
    sb = DoubleSpinbox(fr, value=v1, decimals=3, step=0.001, grid=(0, 0))
    # print('REAL = ',v, 'SPINBOX =', sb.value())

    sb2 = ScientificDoubleSpinBox(fr, value=v1, decimals=3, grid=(1, 0), min=0.001)

    popup.show()
    popup.raise_()

    app.start()
