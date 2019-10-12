"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Icon import Icon
from operator import or_
from functools import reduce


class DialogButtonBox(QtWidgets.QDialogButtonBox, Base):

    def __init__(self, parent=None, buttons=None, callbacks=None, texts=None, tipTexts=None, icons=None,
                 orientation='horizontal', **kwds):

        super().__init__(parent)
        Base._init(self, **kwds)

        self._parent = parent

        buttons = buttons or []
        if not isinstance(buttons, (tuple, list)):
            raise TypeError('Error, buttons must be tuple/list')
        N = len(buttons)
        callbacks = callbacks or []
        texts = texts or []
        tipTexts = tipTexts or []
        icons = icons or []

        if not isinstance(callbacks, (tuple, list)):
            raise TypeError('Error, callbacks must be tuple/list')
        callbacks = (list(callbacks) + N * [None])[:N]

        if not isinstance(texts, (tuple, list)):
            raise TypeError('Error, texts must be tuple/list')
        texts = (list(texts) + N * [None])[:N]

        if not isinstance(tipTexts, (tuple, list)):
            raise TypeError('Error, tipTexts must be tuple/list')
        tipTexts = (list(tipTexts) + N * [None])[:N]

        if not isinstance(icons, (tuple, list)):
            raise TypeError('Error, icons must be tuple/list')
        icons = (list(icons) + N * [None])[:N]

        if not isinstance(orientation, str):
            raise TypeError("Error, orientation must be str: 'h' or 'v'")

        self.setStyleSheet('QPushButton { padding: 0px 8px 0px 8px; }')

        if 'h' in orientation.lower():
            self.setOrientation(QtCore.Qt.Horizontal)
        else:
            self.setOrientation(QtCore.Qt.Vertical)

        if buttons:
            buttonTypes = reduce(or_, buttons)
            self.setStandardButtons(buttonTypes)

            if callbacks:
                for button, callback, text, tipText, icon in zip(buttons, callbacks, texts, tipTexts, icons):
                    thisButton = self.button(button)
                    if callback:
                        thisButton.clicked.connect(callback)
                    if text:
                        thisButton.setText(text)
                    if tipText:
                        thisButton.setToolTip(tipText)
                    if icon:  # filename or pixmap
                        thisButton.setIcon(Icon(icon))
                        # this causes the button to reset its stylesheet
                        thisButton.setIconSize(QtCore.QSize(22, 22))
                    thisButton.setFixedHeight(24)
