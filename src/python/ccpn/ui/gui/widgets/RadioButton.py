"""
This module implements the Button class
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
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.Base import Base
from ccpn.framework.Translation import translator
from ccpn.ui.gui.widgets.Font import getFontHeight


class RadioButton(QtWidgets.QRadioButton, Base):

    def __init__(self, parent, text='', textColor=None, textSize=None, callback=None, **kwds):

        super().__init__(parent)
        Base._init(self, **kwds)

        text = translator.translate(text)
        self.setText(text)

        if textColor:
            self.setStyleSheet('QRadioButton {color: {}; font-size: 12pt;}'.format(textColor))
        if textSize:
            self.setStyleSheet('QRadioButton {font-size: {};}'.format(textSize))
        if callback:
            self.setCallback(callback)
        if not self.objectName():
            self.setObjectName(text)

        self.setStyleSheet('QRadioButton::disabled { color: #7f88ac; }')

    def get(self):
        return self.text()

    def set(self, text=''):
        if len(text) > 0:
            text = translator.translate(text)
        self.setText(text)

    def getText(self):
        "Get the text of the button"
        return self.get()

    def setCallback(self, callback):
        #
        # if self.callback:
        #   self.disconnect(self, QtCore.SIGNAL('clicked()'), self.callback)

        if callback:
            # self.connect(self, QtCore.SIGNAL('clicked()'), callback)
            self.clicked.connect(callback)
