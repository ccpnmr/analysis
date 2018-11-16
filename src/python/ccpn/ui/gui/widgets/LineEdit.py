"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:54 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
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


TextAlignment = {
    'c': QtCore.Qt.AlignHCenter,
    'l': QtCore.Qt.AlignLeft,
    'r': QtCore.Qt.AlignRight
    }


class LineEdit(QtWidgets.QLineEdit, Base):

    def __init__(self, parent, text='', textAlignment='c', backgroundText=None, minimumWidth=100, textColor=None, **kwds):
        """

        :param parent:
        :param text:
        :param textAlignment:
        :param backgroundText: a transparent text that will disapear as soon as you click to type.
        :param minimumWidth:
        :param textColor:
        :param kwds:
        """
        #text = translator.translate(text)

        super().__init__(parent)
        Base._init(self, **kwds)

        self.setText(text)

        if textColor:
            self.setStyleSheet('QLabel {color: %s;}' % textColor)
        self.backgroundText = backgroundText
        if self.backgroundText:
            self.setPlaceholderText(str(self.backgroundText))

        self.setAlignment(TextAlignment[textAlignment])
        self.setMinimumWidth(minimumWidth)
        self.setFixedHeight(25)

    def get(self):

        return self.text()

    def set(self, text=''):

        #text = translator.translate(text)
        self.setText(text)


class FloatLineEdit(LineEdit):

    def get(self):

        result = LineEdit.get(self)
        if result:
            return float(result)
        else:
            return None

    def set(self, text=''):

        LineEdit.set(str(text))
