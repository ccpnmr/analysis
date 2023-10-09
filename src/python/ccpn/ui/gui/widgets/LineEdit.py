"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2023-10-09 12:09:37 +0100 (Mon, October 09, 2023) $"
__version__ = "$Revision: 3.2.0 $"
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
from ccpn.ui.gui.widgets.ValidatorBase import ValidatorBase

from ccpn.ui.gui.widgets.Font import setWidgetFont, getFontHeight
# from ccpn.ui.gui.guiSettings import helveticaItalic12
# from ccpn.framework.Translation import translator


TextAlignment = {
    'c': QtCore.Qt.AlignHCenter,
    'l': QtCore.Qt.AlignLeft,
    'r': QtCore.Qt.AlignRight,
    'center': QtCore.Qt.AlignHCenter,
    'centre': QtCore.Qt.AlignHCenter,
    'left': QtCore.Qt.AlignLeft,
    'right': QtCore.Qt.AlignRight
    }


class LineEdit(QtWidgets.QLineEdit, Base):

    def __init__(self, parent, text='', textAlignment='c', backgroundText=None,
                 textColor='black', editable=True, **kwds):
        """
        :param parent: parent widget
        :param text: text to display (can be changed with set() method)
        :param textAlignment: 'l', 'c', or 'r' text alignment identifier
        :param backgroundText: a transparent text that will disappear as soon as you click to type.
        :param textColor: Colour of the text
        :param editable: flag to indicate if content is editable
        :param kwds: optional keyword arguments passed to Base for widget management
        """
        #text = translator.translate(text)

        super().__init__(parent)
        Base._init(self, **kwds)

        self.setText(text)

        self.textColor = textColor
        if textColor:
            self.setStyleSheet('QLabel {color: %s;}' % textColor)

        self.backgroundText = backgroundText
        if self.backgroundText:
            self.setPlaceholderText(str(self.backgroundText))

        self.setAlignment(TextAlignment[textAlignment])
        self.setStyleSheet('LineEdit { padding: 3px 3px 3px 3px; }')
        self.setEditable(editable)

    def get(self):
        return self.text()

    def set(self, text=''):
        #text = translator.translate(text)
        self.setText(text)

    def setEditable(self, flag:bool):
        """Set the widget to be editable
        For now implemented using setReadOnly() and setEnabled()
        """
        self.setReadOnly(not flag)
        self.setEnabled(flag)

    def _getSaveState(self):
        """
        Internal. Called for saving/restoring the widget state.
        """
        return self.get()

    def _setSavedState(self, value):
        """
        Internal. Called for saving/restoring the widget state.
        """
        return self.set(value)


    # def paintEvent(self, ev):
    #     #p.setBrush(QtGui.QBrush(QtGui.QColor(100, 100, 200)))
    #     #p.setPen(QtGui.QPen(QtGui.QColor(50, 50, 100)))
    #     #p.drawRect(self.rect().adjusted(0, 0, -1, -1))
    #
    #     #p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
    #     self._text = self.text()
    #     self.setText('')
    #     super(LineEdit, self).paintEvent(ev)
    #
    #     p = QtGui.QPainter(self)
    #     if self.orientation == QtCore.Qt.Vertical:
    #         p.rotate(-90)
    #         rgn = QtCore.QRect(-self.height(), 0, self.height(), self.width())
    #     else:
    #         rgn = self.contentsRect()
    #     align = self.alignment()
    #     #align  = QtCore.Qt.AlignTop|QtCore.Qt.AlignHCenter
    #
    #     self.hint = p.drawText(rgn, align, self._text)
    #     self.setText(self._text)
    #     p.end()
    #
    #     if self.orientation == QtCore.Qt.Vertical:
    #         self.setMaximumWidth(self.hint.height())
    #         self.setMinimumWidth(0)
    #         self.setMaximumHeight(16777215)
    #     else:
    #         self.setMaximumHeight(self.hint.height())
    #         self.setMinimumHeight(0)
    #         self.setMaximumWidth(16777215)
    #
    # def sizeHint(self):
    #     if self.orientation == QtCore.Qt.Vertical:
    #         if hasattr(self, 'hint'):
    #             return QtCore.QSize(self.hint.height(), self.hint.width())
    #         else:
    #             return QtCore.QSize(19, 50)
    #     else:
    #         if hasattr(self, 'hint'):
    #             return QtCore.QSize(self.hint.width(), self.hint.height())
    #         else:
    #             return QtCore.QSize(50, 19)

class LineEdit2(LineEdit):
    """A lineEdit with altered colour scheme for readOnly state
    """

    def __init__(self, parent, text:str='', textAlignment:str='c', backgroundText:str=None,
                 textColor:str='black', editable:bool=True, callback=None, **kwds):
        """
        :param parent: parent widget
        :param text: text to display (can be changed with set() method)
        :param textAlignment: 'l', 'c', or 'r' text alignment identifier
        :param backgroundText: a transparent text that will disappear as soon as you click to type.
        :param textColor: Colour of the text
        :param editable: flag to indicate if content is editable
        :param callback: optional callback function upon completion; i.e. <return> or loss of focus
        :param kwds: optional keyword arguments passed to Base for widget management
        """

        super().__init__(parent=parent, text=text, textAlignment=textAlignment,
                         backgroundText=backgroundText, textColor=textColor, **kwds)

        self.setEditable(editable)
        # this callback implements the colouring (editable/non-editable)
        self.textChanged.connect(self._textChangedCallback)

        # user callback
        self._callback = None
        self._qtEditingSlot = None
        self.setCallback(callback)

    def setEditable(self, flag:bool):
        """Set widget to be editable; i.e. not readOnly"""
        self.setReadOnly(not flag)

    def setReadOnly(self, flag:bool):
        """Change the readonly state; adjust background of the widget
        """
        super().setReadOnly(flag)
        self._readOnly = flag
        self._updateColours()

    def _testCallback(self):
        """A testing function for the callback functionality"""
        print(f'Testing callback: "{self.get()}"')

    def setCallback(self, func):
        """Define the callback function for the editingFinished QT slot
        """
        if func is not None:
            self._qtEditingSlot = self.editingFinished.connect(func)
            self._callback = func
        else:
            if self._qtEditingSlot:
                self.editingFinished.disconnect()

    def _textChangedCallback(self):
        """A character was entered"""
        _text = self.get()
        if len(_text) <= 1:
            self._updateColours()

    def _updateColours(self):
        """Update the colours depending on state of the line edit
        """
        if self._readOnly:
            # Readonly: setting background colour of the widget to lightgrey
            self.setStyleSheet("""
            QLineEdit {
                background-color : #DDDDDD;
                color : #666666
            }""")

        else:
            # Editable: setting background colour of the widget to white
            _textColour = 'darkgrey' \
                           if (self.backgroundText and len(self.get()) == 0) \
                           else self.textColor
            self.setStyleSheet("""
            QLineEdit {
                background : white;
                color : %s
            }""" % _textColour)


class FloatLineEdit(LineEdit):

    def get(self):

        result = LineEdit.get(self)
        if result:
            return float(result)
        else:
            return None

    def set(self, text=''):

        LineEdit.set(str(text))

    def _getSaveState(self):
        """
        Internal. Called for saving/restoring the widget state.
        """
        return self.get()

    def _setSavedState(self, value):
        """
        Internal. Called for saving/restoring the widget state.
        """
        return self.set(value)


class ValidatedLineEdit(LineEdit, ValidatorBase):
    """A class that implements a validated LineEdit
    """
    WIDGET_VALUE_FUNCTION = LineEdit.get

    def __init__(self, parent, validatorCallback, **kwds):
        """
        :param parent: parent widget
        :param validatorCallback: a function def validatorCallback(value) -> bool
                                  which is called upon changes to the value of the Widget.
                                  It should return True/False.
        """
        LineEdit.__init__(self, parent=parent, **kwds)
        ValidatorBase.__init__(self, widget=self, validatorCallback=validatorCallback)


class PasswordEdit(LineEdit):
    """Subclass of LineEdit to handle passwords to be shown as **
    """
    def __init__(self, parent, text='', textAlignment='c', backgroundText=None,
                 minimumWidth=100, textColor=None, editable=True, **kwds):
        """
        Initialise the lineEdit to password mode
        """
        super().__init__(parent, text=text, textAlignment=textAlignment, backgroundText=backgroundText,
                         minimumWidth=minimumWidth, textColor=textColor, editable=editable, **kwds)
        Base._init(self, **kwds)

        # set password mode
        self.setEchoMode(QtWidgets.QLineEdit.Password)
