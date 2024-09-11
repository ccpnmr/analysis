"""Module Documentation here

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
__dateModified__ = "$dateModified: 2024-08-27 16:07:11 +0100 (Tue, August 27, 2024) $"
__version__ = "$Revision: 3.2.5 $"
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


# from ccpn.ui.gui.guiSettings import helveticaItalic12
# from ccpn.framework.Translation import translator


TextAlignment = {
    'c'     : QtCore.Qt.AlignHCenter,
    'l'     : QtCore.Qt.AlignLeft,
    'r'     : QtCore.Qt.AlignRight,
    'center': QtCore.Qt.AlignHCenter,
    'centre': QtCore.Qt.AlignHCenter,
    'left'  : QtCore.Qt.AlignLeft,
    'right' : QtCore.Qt.AlignRight
    }


class LineEdit(QtWidgets.QLineEdit, Base):
    highlightColour = None

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
        self.setEditable(editable)

        self._setStyle()

    def _setStyle(self):
        _style = """QLineEdit {
                    padding: 3px 3px 3px 3px;
                    background-color: palette(norole);
                }
                QLineEdit:disabled {
                    color: #808080;
                    background-color: palette(midlight);
                }
                QLineEdit:read-only {
                    color: #808080;
                }
                """
        self.setStyleSheet(_style)
        # check for Windows and Linux
        QtWidgets.QApplication.instance()._sigPaletteChanged.connect(self._revalidate)

    def _revalidate(self, palette):
        if val := self.validator():
            if hasattr(val, 'baseColour'):
                # update the base-colour for change of theme
                val.baseColour = palette.base().color()
            # force repaint of the widget
            val.validate(self.text(), 0)

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


# class LineEdit2(LineEdit):
#     """A lineEdit with altered colour scheme for readOnly state
#     """
#
#     def __init__(self, parent, text:str='', textAlignment:str='c', backgroundText:str=None,
#                  textColor:str='black', editable:bool=True, callback=None, **kwds):
#         """
#         :param parent: parent widget
#         :param text: text to display (can be changed with set() method)
#         :param textAlignment: 'l', 'c', or 'r' text alignment identifier
#         :param backgroundText: a transparent text that will disappear as soon as you click to type.
#         :param textColor: Colour of the text
#         :param editable: flag to indicate if content is editable
#         :param callback: optional callback function upon completion; i.e. <return> or loss of focus
#         :param kwds: optional keyword arguments passed to Base for widget management
#         """
#
#         super().__init__(parent=parent, text=text, textAlignment=textAlignment,
#                          backgroundText=backgroundText, textColor=textColor, **kwds)
#
#         self.setEditable(editable)
#         # this callback implements the colouring (editable/non-editable)
#         self.textChanged.connect(self._textChangedCallback)
#
#         # user callback
#         self._callback = None
#         self._qtEditingSlot = None
#         self.setCallback(callback)
#
#     def setEditable(self, flag:bool):
#         """Set widget to be editable; i.e. not readOnly"""
#         self.setReadOnly(not flag)
#
#     def setReadOnly(self, flag:bool):
#         """Change the readonly state; adjust background of the widget
#         """
#         super().setReadOnly(flag)
#         self._readOnly = flag
#         self._updateColours()
#
#     def _testCallback(self):
#         """A testing function for the callback functionality"""
#         print(f'Testing callback: "{self.get()}"')
#
#     def setCallback(self, func):
#         """Define the callback function for the editingFinished QT slot
#         """
#         if func is not None:
#             self._qtEditingSlot = self.editingFinished.connect(func)
#             self._callback = func
#         else:
#             if self._qtEditingSlot:
#                 self.editingFinished.disconnect()
#
#     def _textChangedCallback(self):
#         """A character was entered"""
#         _text = self.get()
#         if len(_text) <= 1:
#             self._updateColours()
#
#     def _updateColours(self):
#         """Update the colours depending on state of the line edit
#         """
#         if self._readOnly:
#             # Readonly: setting background colour of the widget to lightgrey
#             self.setStyleSheet("""
#             QLineEdit {
#                 background-color : #DDDDDD;
#                 color : #666666
#             }""")
#
#         else:
#             # Editable: setting background colour of the widget to white
#             _textColour = 'darkgrey' \
#                            if (self.backgroundText and len(self.get()) == 0) \
#                            else self.textColor
#             self.setStyleSheet("""
#             QLineEdit {
#                 background : white;
#                 color : %s
#             }""" % _textColour)


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


def main():
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.Widget import Widget
    from ccpn.ui.gui.widgets.Spacer import Spacer

    class Popup(QtWidgets.QMainWindow):
        def __init__(self, title):
            super().__init__()
            self.layout().setContentsMargins(9, 9, 9, 9)

            self.setWindowTitle(title)
            mainWidget = Widget(self, setLayout=True)
            self.setCentralWidget(mainWidget)
            LineEdit(parent=mainWidget, name='Widget-1', grid=(0, 0), text='Enabled - text')
            LineEdit(parent=mainWidget, name='Widget-2', grid=(1, 0), text='Disabled - text', enabled=False)
            widget3 = LineEdit(parent=mainWidget, name='Widget-3', grid=(2, 0), text='Read-only - text')
            widget3.setReadOnly(True)
            widget4 = LineEdit(parent=mainWidget, name='Widget-4', grid=(3, 0), text='Disabled|read-only - text',
                               enabled=False)
            widget4.setReadOnly(True)
            Spacer(mainWidget, 1, 1,
                   QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
                   grid=(9, 9))


    app = TestApplication()
    # patch for icon sizes in menus, etc.
    styles = QtWidgets.QStyleFactory()
    app.setStyle(styles.create('fusion'))
    popup = Popup(title='Testing enabled/read-only lineEdits')
    popup.show()

    app.start()


if __name__ == '__main__':
    main()
