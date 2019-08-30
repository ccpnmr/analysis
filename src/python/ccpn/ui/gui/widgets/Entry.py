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
__dateModified__ = "$dateModified: 2017-07-07 16:32:54 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.guiSettings import helveticaItalic12

from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label

# Width?
# Allow setting of max lengh based on data model?

import re

SPLIT_REG_EXP = re.compile(',?\s*')
SEPARATOR = ', '
MAXINT = 2 ** 31 - 1
INFINITY = float('Inf')


class Entry(QtWidgets.QLineEdit, Base):

    def __init__(self, parent, text='', callback=None, maxLength=32,
                 listener=None, stripEndWhitespace=True, readOnly=False, **kwds):

        super().__init__(parent)
        Base._init(self, **kwds)

        self.setText(self.convertInput(text))
        self.setMaxLength(maxLength)

        self._isAltered = False
        self._stripEndWhitespace = stripEndWhitespace
        self.callback = callback

        self.textChanged.connect(self._changed)

        # self.connect(self, QtCore.SIGNAL('returnPressed()'), self._callback)
        # self.connect(self, QtCore.SIGNAL('editingFinished()'), self._callback)

        self.returnPressed.connect(self._callback)
        self.editingFinished.connect(self._callback)

        if listener:
            if isinstance(listener, (set, list, tuple)):
                for signal in listener:
                    signal.connect(self.set)

            else:
                listener.connect(self.set)

        self.setFixedHeight(25)

        if readOnly:
            self.setReadOnly(True)
            self.setEnabled(False)
            self.setFont(helveticaItalic12)

    def _callback(self):

        if self.callback and self._isAltered:
            self.callback(self.get())
            self._isAltered = False

    def _changed(self):

        self._isAltered = True

    def convertText(self, text):
        # Overwritten in subclasses to make float, int etc

        if self._stripEndWhitespace:
            text = text.strip()

        return text or None

    def convertInput(self, value):
        # Overwritten in subclasses to convert float, int

        return value or ''

    def get(self):

        return self.convertText(self.text())

    #gwv 20181101; some consistency
    getText = get

    def set(self, value, doCallback=True):

        self.setText(self.convertInput(value))

        if doCallback:
            self._callback()


class IntEntry(Entry):

    def __init__(self, parent, text=0, callback=None,
                 minValue=-MAXINT, maxValue=MAXINT, **kwds):

        Entry.__init__(self, parent, text, callback, **kwds)

        valid = QtGui.QIntValidator(minValue, maxValue, self)
        self.setValidator(valid)

    def convertText(self, text):

        if not text:
            return None
        else:
            return int(text)

    def convertInput(self, value):

        if value is None:
            return ''
        else:
            return str(value)

    def setRange(self, minValue=-MAXINT, maxValue=MAXINT):

        valid = QtGui.QIntValidator(minValue, maxValue, self)
        self.setValidator(valid)


class FloatEntry(Entry):
    decimals = 4

    def __init__(self, parent, text=0.0, callback=None,
                 minValue=-INFINITY, maxValue=INFINITY,
                 decimals=4, **kwds):

        Entry.__init__(self, parent, text, callback, **kwds)

        self.decimals = decimals
        self.setText(self.convertInput(text))

        valid = QtGui.QDoubleValidator(minValue, maxValue, decimals, self)
        self.setValidator(valid)

    def convertText(self, text):

        if not text:
            return None
        else:
            return float(text)

    def convertInput(self, value):

        if value is None:
            text = ''
        elif value == 0:
            text = '0.0'
        elif abs(value) > 999999 or abs(value) < 0.00001:
            format = '%%.%de' % (self.decimals)
            text = format % value
        else:
            format = '%%.%df' % (self.decimals)
            text = format % value

        return text

    def setRange(self, minValue=-INFINITY, maxValue=INFINITY):

        valid = QtGui.QIntValidator(minValue, maxValue, self)
        self.setValidator(valid)


class RegExpEntry(Entry):

    def __init__(self, parent, text='', callback=None, **kwds):
        Entry.__init__(self, parent, text, callback, **kwds)

        self.setValidator(QtGui.QRegExpValidator)


class ArrayEntry(Entry):

    def __init__(self, parent, text='', callback=None, **kwds):
        Entry.__init__(self, parent, text, callback, **kwds)

    def convertText(self, text):
        return re.split(SPLIT_REG_EXP, text) or []

    def convertInput(self, array):
        return SEPARATOR.join(array)


class IntArrayEntry(IntEntry):

    def __init__(self, parent, text='', callback=None, **kwds):
        IntEntry.__init__(self, parent, text, callback, **kwds)

    def convertText(self, text):
        array = re.split(SPLIT_REG_EXP, text) or []
        return [IntEntry.convertText(self, x) for x in array]

    def convertInput(self, values):
        texts = [IntEntry.convertInput(self, x) for x in values]
        return SEPARATOR.join(texts)


class FloatArrayEntry(FloatEntry):

    def __init__(self, parent, text='', callback=None, **kwds):
        FloatEntry.__init__(self, parent, text, callback, **kwds)

    def convertText(self, text):
        array = re.split(SPLIT_REG_EXP, text) or []
        return [FloatEntry.convertText(self, x) for x in array]

    def convertInput(self, values):
        texts = [FloatEntry.convertInput(self, x) for x in values]
        return SEPARATOR.join(texts)


class LabelledEntry(Frame):

    def __init__(self, parent, labelText, entryText='', callback=None, maxLength=32, tipText=None, **kwds):
        Frame.__init__(self, parent, tipText=tipText, **kwds)

        self.label = Label(self, labelText, tipText=tipText, grid=(0, 0))
        self.entry = Entry(self, entryText, callback, maxLength,
                           tipText=tipText, grid=(0, 1))

    def getLabel(self):
        return self.label.get()

    def setLabel(self, text):
        self.label.set(text)

    def getEntry(self):
        return self.entry.get()

    def setEntry(self, text):
        self.entry.set(text)


class LabelledIntEntry(LabelledEntry):

    def __init__(self, parent, labelText, entryText='', callback=None,
                 minValue=-MAXINT, maxValue=MAXINT, tipText=None, **kwds):
        Frame.__init__(self, parent, tipText=tipText, **kwds)

        self.label = Label(self, labelText, tipText=tipText, grid=(0, 0))
        self.entry = IntEntry(self, entryText, callback, minValue,
                              maxValue, tipText=tipText, grid=(0, 1))


class LabelledFloatEntry(LabelledEntry):

    def __init__(self, parent, labelText, entryText='', callback=None,
                 minValue=-MAXINT, maxValue=MAXINT, decimals=4, tipText=None, **kwds):
        Frame.__init__(self, parent, tipText=tipText, **kwds)

        self.label = Label(self, labelText, tipText=tipText, grid=(0, 0))
        self.entry = FloatEntry(self, entryText, callback, minValue,
                                maxValue, decimals, tipText=tipText, grid=(0, 1))


if __name__ == '__main__':
    # from memops.qtgui.Application import Application
    from ccpn.ui.gui.widgets.Application import Application

    app = Application('test', 'test1')

    window = QtWidgets.QWidget()


    def callback(value):
        print("Callback", value)


    Entry(window, 'Start Text', callback)

    ArrayEntry(window, ['A', 'C', 'D', 'C'], callback)

    IntEntry(window, 123, callback)

    IntArrayEntry(window, [4, 5, 6, 7], callback)

    FloatEntry(window, 2.818, callback)

    e = FloatArrayEntry(window, [1, 2, 4], callback, decimals=2)
    e.set([1e12, -0.7e-5, 9.75])

    LabelledEntry(window, 'Text:', 'Initial val', callback)

    LabelledIntEntry(window, 'Int:', 0, callback)

    LabelledFloatEntry(window, 'Float:', 0.7295, callback, decimals=8)

    window.show()

    app.start()
