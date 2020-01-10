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
__dateModified__ = "$dateModified: 2020-01-10 11:21:55 +0000 (Fri, January 10, 2020) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
from pyqtgraph.widgets.VerticalLabel import VerticalLabel as pyqtVerticalLabel
from ccpn.ui.gui.widgets.Base import Base
from ccpn.framework.Translation import translator
import ccpn.ui.gui.guiSettings as guiSettings


class Label(QtWidgets.QLabel, Base):
    _styleSheet = """
    QLabel {
            font-size: %spt;
            font-weight: %s;
            color: %s;
            margin-left: %dpx;
            margin-top: %dpx;
            margin-right: %dpx;
            margin-bottom: %dpx;
            border: 0px;
            }
    """

    def __init__(self, parent=None, text='', textColour=None, textSize=12, bold=False,
                 margins=[2, 1, 2, 1], **kwds):
        super().__init__(parent)
        Base._init(self, **kwds)

        text = translator.translate(text)
        self.setText(text)

        # if textColor:
        #   self.setStyleSheet('QLabel {color: %s}' % textColor)
        # if textSize and textColor:
        #   self.setStyleSheet('QLabel {font-size: %s; color: %s;}' % (textSize, textColor))
        # if bold:
        #   self.setStyleSheet('QLabel {font-weight: bold;}')

        self._textSize = textSize
        self._bold = 'bold' if bold else 'normal'
        self._margins = margins

        # this appears not to pick up the colour as set by the stylesheet!
        # self._colour = textColor if textColor else self.palette().color(QtGui.QPalette.WindowText).name()

        colours = guiSettings.getColours()
        self._colour = textColour if textColour else colours[guiSettings.LABEL_FOREGROUND]
        self._setStyleSheet()

    def get(self):
        """get the label text
        """
        return self.text()

    def set(self, text=''):
        """set label text, applying translator
        """
        text = translator.translate(text)
        self.setText(text)

    def _setStyleSheet(self):
        self.setStyleSheet(self._styleSheet % (self._textSize,
                                               self._bold,
                                               self._colour,
                                               self._margins[0],
                                               self._margins[1],
                                               self._margins[2],
                                               self._margins[3],
                                               )
                           )


class ActiveLabel(Label):

    def __init__(self, parent=None, mainWindow=None,
                 text='', textColour=None, textSize=12, bold=False,
                 margins=[2, 1, 2, 1], selectionCallback=None, actionCallback=None, **kwds):
        super().__init__(parent=parent, text=text, textColour=textColour, textSize=textSize, bold=bold,
                         margins=margins, **kwds)

        self.mainWindow = mainWindow
        self._selectionCallback = selectionCallback
        self._actionCallback = actionCallback
        self._enterCallback = None
        self._leaveCallback = None

        # required highlighting flag for changing colour themes
        self.highlighted = False

    def setSelectionCallback(self, callback=None):
        """Sets callback on mouse click
        """
        self._selectionCallback = callback

    def setActionCallback(self, callback=None):
        """Sets callback on mouse double click
        """
        self._actionCallback = callback

    def mouseReleaseEvent(self, ev):
        """Handle double click and call _selectionCallback if set
        """
        if self._selectionCallback:
            self._selectionCallback()
        super().mouseReleaseEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        """Handle double click and call _actionCallback if set
        """
        if self._actionCallback:
            self._actionCallback()
        super().mouseDoubleClickEvent(ev)

    def setEnterLeaveCallback(self, enterCallback, leaveCallback):
        self._enterCallback = enterCallback
        self._leaveCallback = leaveCallback

    def enterEvent(self, ev) -> None:
        super().enterEvent(ev)
        if self._enterCallback:
            self._enterCallback()

    def leaveEvent(self, ev) -> None:
        super().leaveEvent(ev)
        if self._leaveCallback:
            self._leaveCallback()


class VerticalLabel(pyqtVerticalLabel, Base):
    _styleSheet = """
    QLabel {
            font-size: %spt;
            font-weight: %s;
            color: %s;
            margin-left: %dpx;
            margin-top: %dpx;
            margin-right: %dpx;
            margin-bottom: %dpx;
            border: 0px;
            }
    """

    def __init__(self, parent=None, text='', textColour=None, textSize=12, bold=False,
                 margins=[2, 1, 2, 1], orientation='horizontal', **kwds):
        super().__init__(parent, orientation=orientation, forceWidth=False)
        Base._init(self, **kwds)

        text = translator.translate(text)
        self.setText(text)

        # if textColor:
        #   self.setStyleSheet('QLabel {color: %s}' % textColor)
        # if textSize and textColor:
        #   self.setStyleSheet('QLabel {font-size: %s; color: %s;}' % (textSize, textColor))
        # if bold:
        #   self.setStyleSheet('QLabel {font-weight: bold;}')

        self._textSize = textSize
        self._bold = 'bold' if bold else 'normal'
        self._margins = margins

        # this appears not to pick up the colour as set by the stylesheet!
        # self._colour = textColor if textColor else self.palette().color(QtGui.QPalette.WindowText).name()

        colours = guiSettings.getColours()
        self._colour = textColour if textColour else colours[guiSettings.LABEL_FOREGROUND]
        self._setStyleSheet()

    def get(self):
        "get the label text"
        return self.text()

    def set(self, text=''):
        "set label text, applying translator"
        text = translator.translate(text)
        self.setText(text)

    def _setStyleSheet(self):
        self.setStyleSheet(self._styleSheet % (self._textSize,
                                               self._bold,
                                               self._colour,
                                               self._margins[0],
                                               self._margins[1],
                                               self._margins[2],
                                               self._margins[3],
                                               )
                           )


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.Button import Button


    msg = 'Hello world'
    count = 0


    def func():
        global count
        count += 1
        label.set(msg + ' ' + str(count))
        print(label.get())


    app = TestApplication()

    window = QtWidgets.QWidget()

    label = Label(window, text=msg, textColor='red', grid=(0, 0))
    button = Button(window, text='Click me', callback=func, grid=(0, 1))

    window.show()

    app.start()
