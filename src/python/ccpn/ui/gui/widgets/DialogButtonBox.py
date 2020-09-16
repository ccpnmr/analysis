"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2020-09-16 12:14:33 +0100 (Wed, September 16, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-05-26 14:50:42 +0000 (Tue, May 26, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Icon import Icon
from operator import or_
from functools import reduce
from ccpn.ui.gui.widgets.Font import setWidgetFont


class DialogButtonBox(QtWidgets.QDialogButtonBox, Base):

    def __init__(self, parent=None, buttons=None, callbacks=None, texts=None, tipTexts=None,
                 icons=None, enabledStates=None, visibleStates=None, defaultButton=None, enableIcons=False,
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
        enabledStates = enabledStates or []
        visibleStates = visibleStates or []

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

        if not isinstance(enabledStates, (tuple, list)):
            raise TypeError('Error, enabledStates must be tuple/list')
        enabledStates = (list(enabledStates) + N * [None])[:N]

        if not isinstance(visibleStates, (tuple, list)):
            raise TypeError('Error, visibleStates must be tuple/list')
        visibleStates = (list(visibleStates) + N * [None])[:N]

        if defaultButton is not None and defaultButton not in buttons:
            raise TypeError("Error, defaultButton not in buttons")

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
                for button, callback, text, tipText, icon, enabledState, visibleState in \
                        zip(buttons, callbacks, texts, tipTexts, icons, enabledStates, visibleStates):

                    thisButton = self.button(button)
                    if callback is not None:
                        thisButton.clicked.connect(callback)
                    if text is not None:
                        thisButton.setText(text)
                        if not text:
                            # reduce the padding to give a better shape
                            thisButton.setStyleSheet('QPushButton { padding: 0px 2px 0px 2px; }')

                    if tipText is not None:
                        thisButton.setToolTip(tipText)

                    if enableIcons and icon is not None:                                # filename or pixmap
                        thisButton.setIcon(Icon(icon))
                        # NOTE: sometimes this causes the button to reset its stylesheet
                        thisButton.setIconSize(QtCore.QSize(22, 22))

                    if enabledState is not None:
                        thisButton.setEnabled(enabledState)
                    if visibleState is not None:
                        thisButton.setVisible(visibleState)

                    thisButton.setMinimumHeight(24)

            if defaultButton is not None:
                self._parent.setDefaultButton(self.button(defaultButton))

            for button in buttons:
                setWidgetFont(self.button(button), 'textFontHuge')
