"""
This module implements the Button class
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-05-19 20:15:00 +0100 (Thu, May 19, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtWidgets

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.framework.Translation import translator
from ccpn.ui.gui.widgets.Font import getFontHeight


CHECKED = QtCore.Qt.Checked
UNCHECKED = QtCore.Qt.Unchecked


class Button(QtWidgets.QPushButton, Base):

    def __init__(self, parent=None, text='', callback=None, icon=None, toggle=None, **kwds):

        #text = translator.translate(text): not needed as it calls setText which does the work

        super().__init__(parent)
        Base._init(self, **kwds)

        self.setText(text)

        if icon:  # filename or pixmap
            self.setIcon(Icon(icon))
            # this causes the button to reset its stylesheet
            fontHeight = (getFontHeight() or 16) + 7
            self.setIconSize(QtCore.QSize(fontHeight, fontHeight))
        else:
            self.setStyleSheet('Button { padding: 3px 2px 3px 2px; }')

        self.toggle = toggle
        if toggle is not None:
            self.setCheckable(True)
            self.setSelected(toggle)
            self.setStyleSheet('Button::checked {background-color: blue }')

        self._callback = None
        self.setCallback(callback)

    def setSelected(self, selected):
        if self.isCheckable():
            self.setChecked(selected)

    def setCallback(self, callback=None):
        """Sets callback; disconnects if callback=None"""
        if self._callback is not None:
            self.clicked.disconnect()
        if callback:
            self.clicked.connect(callback)
            # self.clicked.connect doesn't work with lambda, yet...
        self._callback = callback

    def setText(self, text):
        """Set the text of the button, applying the translator first"""
        self._text = translator.translate(text)
        QtWidgets.QPushButton.setText(self, self._text)

    def getText(self):
        """Get the text of the button"""
        return self._text

    def _getSaveState(self):
        """
        Internal. Called for saving/restoring the widget state.
        """
        if self.toggle:
            return self.isChecked()


    def _setSavedState(self, value):
        """
        Internal. Called for saving/restoring the widget state.
        """
        if not value:
            return

        if self.toggle:
            return self.set(value)


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication


    app = TestApplication()

    window = QtWidgets.QWidget()
    window.setLayout(QtWidgets.QGridLayout())


    def click():
        print("Clicked")


    b1 = Button(window, text='Click Me', callback=click,
                tipText='Click for action',
                grid=(0, 0))

    b2 = Button(window, text='I am inactive', callback=click,
                tipText='Cannot click',
                grid=(0, 1))

    b2.setEnabled(False)

    b3 = Button(window, text='I am green', callback=click,
                tipText='Mmm, green',  #bgColor='#80FF80',
                grid=(0, 2))

    b4 = Button(window, icon='icons/system-help.png', callback=click,
                tipText='A toggled icon button', toggle=True,
                grid=(0, 3))

    window.show()
    window.raise_()

    app.start()
