"""
This file contains the routines for message dialogues
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-07-30 20:44:26 +0100 (Fri, July 30, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import textwrap
from PyQt5 import QtWidgets, QtCore
from ccpn.ui.gui.widgets.Font import setWidgetFont
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from PyQt5.QtCore import QEvent


# from ccpn.ui.gui.guiSettings import messageFont, messageFontBold

def _isDarwin():
    return 'darwin' in QtCore.QSysInfo().kernelType().lower()


Ok = QtWidgets.QMessageBox.Ok
Cancel = QtWidgets.QMessageBox.Cancel
Yes = QtWidgets.QMessageBox.Yes
No = QtWidgets.QMessageBox.No
Retry = QtWidgets.QMessageBox.Retry
Ignore = QtWidgets.QMessageBox.Ignore
Abort = QtWidgets.QMessageBox.Abort
Close = QtWidgets.QMessageBox.Close
Information = QtWidgets.QMessageBox.Information
Warning = QtWidgets.QMessageBox.Warning
Question = QtWidgets.QMessageBox.Question
Critical = QtWidgets.QMessageBox.Critical
Save = QtWidgets.QMessageBox.Save
Discard = QtWidgets.QMessageBox.Discard

default_icons = (Information, Question, Warning, Critical)

if _isDarwin():
    Question = Warning

LINELENGTH = 120
WRAPBORDER = 5
WRAPSCALE = 1.01


def _wrapString(text, lineLength=LINELENGTH):
    """Wrap a line of text to the desired width of the dialog
    Returns list of individual lines and the concatenated string for dialog
    """
    wrapped = textwrap.wrap(text, width=lineLength, replace_whitespace=False, break_long_words=False)

    newWrapped = []
    for mm in wrapped:
        if len(mm) > LINELENGTH:
            for chPos in range(0, len(mm), lineLength):
                newWrapped.append(mm[chPos:chPos + lineLength])
        else:
            newWrapped.append(mm)

    # merge lines that have now been created by splitting longer lines (if no newlines in first line)
    newWrapped2 = []
    if len(newWrapped) > 1:
        lineNum = 0
        while lineNum < len(newWrapped) - 1:
            l1 = newWrapped[lineNum]
            l2 = newWrapped[lineNum + 1]

            if (len(l1) + len(l2) < LINELENGTH) and '\n' not in l1:
                newWrapped2.append(l1 + ' ' + l2)
                lineNum += 1
            else:
                newWrapped2.append(l1)
                if lineNum == len(newWrapped) - 2:
                    newWrapped2.append(l2)

            lineNum += 1
    else:
        newWrapped2 = newWrapped

    return newWrapped2, '\n'.join(newWrapped2)


class MessageDialog(QtWidgets.QMessageBox):
    """
    Base class for all dialogues
    Using the 'multiline' to emulate the windowTitle, as on Mac the windows do not get their title
    """

    def __init__(self, title, basicText, message, icon=Information, iconPath=None, parent=None):
        QtWidgets.QMessageBox.__init__(self, None)
        self.setWindowModality(QtCore.Qt.WindowModal)

        self._parent = parent
        self.setWindowTitle(title)

        basicTextWrap, basicText = _wrapString(basicText)
        messageWrap, message = _wrapString(message)

        self.setText(basicText)
        self.setInformativeText(message)

        self.setIcon(icon)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)

        # self.setFont(messageFont)  #GWV:  Does not seem to do anything
        # self.setMinimumSize(QtCore.QSize(300, 100))  #GWV:  Does not seem to do anything
        # self.resize(300, 100)  #GWV:  Does not seem to do anything
        # Adapted from best solution so far from: http://apocalyptech.com/linux/qt/qmessagebox/
        layout = self.layout()

        # set the fonts for the labels (pushButtons are set later)
        for widgetLabel in self.findChildren((QtWidgets.QLabel, QtWidgets.QTextEdit)):
            setWidgetFont(widgetLabel, )

        maxTextWidth = 50
        widgetBasic = None
        item = layout.itemAtPosition(0, 2)  # grid position of basic text item
        if item:
            widgetBasic = item.widget()

            # get the bounding rectangle for each line of basicText
            for wrapLine in basicTextWrap:
                tWidth = int((QtGui.QFontMetrics(widgetBasic.font()).boundingRect(wrapLine).width() + WRAPBORDER) * WRAPSCALE)
                maxTextWidth = max(maxTextWidth, tWidth)

        widgetMessage = None
        item = layout.itemAtPosition(1, 2)  # grid position of informative text item
        if item:
            widgetMessage = item.widget()

            # get the bounding rectangle for each line of informativeText
            for wrapLine in messageWrap:
                tWidth = int((QtGui.QFontMetrics(widgetMessage.font()).boundingRect(wrapLine).width() + WRAPBORDER) * WRAPSCALE)
                maxTextWidth = max(maxTextWidth, tWidth)

        if widgetBasic:
            widgetBasic.setFixedWidth(maxTextWidth)
        if widgetMessage:
            widgetMessage.setFixedWidth(maxTextWidth)

        palette = QtGui.QPalette()
        self.setPalette(palette)

        if iconPath:
            image = QtGui.QPixmap(iconPath)
            scaledImage = image.scaled(48, 48, QtCore.Qt.KeepAspectRatio)
            self.setIconPixmap(scaledImage)

        # self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)

    def event(self, event):
        """
        handler to make dialogs proely modal but at the sametime accept the correct keys for default actions
        """

        # accepted events apple-delete, apple-c apple-v, esc, return, spacebar, command period, apple-z apple-y,
        # apple-shift-z  apple-h, apple-option-h, control tab, tab, shift tab, arrow keys, contol arrow keys
        # control-shift-arrows, apple-a

        ACCEPTED_MODAL_KEYS = (
            (Qt.NoModifier, Qt.Key_Space,),
            (Qt.ControlModifier, Qt.Key_Delete),
            (Qt.ControlModifier, Qt.Key_Backspace),
            (Qt.ControlModifier, Qt.Key_C),
            (Qt.ControlModifier, Qt.Key_V),
            (Qt.NoModifier, Qt.Key_Escape,),
            (Qt.NoModifier, Qt.Key_Return,),
            (Qt.NoModifier, Qt.Key_Space,),
            (Qt.ControlModifier, Qt.Key_Period),
            (Qt.ControlModifier, Qt.Key_Z),
            (Qt.ControlModifier, Qt.Key_Y),
            (Qt.ControlModifier | Qt.ShiftModifier, Qt.Key_Z),
            (Qt.ControlModifier, Qt.Key_H),
            (Qt.ControlModifier | Qt.AltModifier, Qt.Key_H),
            (Qt.MetaModifier, Qt.Key_Tab),
            (Qt.NoModifier, Qt.Key_Tab,),
            (Qt.ShiftModifier, Qt.Key_Tab),
            (Qt.NoModifier, Qt.Key_Left,),
            (Qt.NoModifier, Qt.Key_Right,),
            (Qt.NoModifier, Qt.Key_Up,),
            (Qt.NoModifier, Qt.Key_Down,),
            (Qt.MetaModifier, Qt.Key_Left),
            (Qt.MetaModifier, Qt.Key_Right),
            (Qt.MetaModifier, Qt.Key_Up),
            (Qt.MetaModifier, Qt.Key_Down),
            (Qt.MetaModifier | Qt.ShiftModifier, Qt.Key_Left),
            (Qt.MetaModifier | Qt.ShiftModifier, Qt.Key_Right),
            (Qt.MetaModifier | Qt.ShiftModifier, Qt.Key_Up),
            (Qt.MetaModifier | Qt.ShiftModifier, Qt.Key_Down),
            (Qt.ControlModifier, Qt.Key_A)
            )

        result = False
        if event.type() == QEvent.ShortcutOverride:
            test = (event.modifiers(), event.key())
            if test in ACCEPTED_MODAL_KEYS:
                event.accept()
                result = True
        else:
            result = super(MessageDialog, self).event(event)

        return result

    def resizeEvent(self, ev):
        """
        required to set the initial position of the message box on the centre of the screen
        """
        # set the font of the push buttons, must be here after __init__ has completed
        for child in self.findChildren(QtWidgets.QPushButton):
            setWidgetFont(child, )

        # must be the first event outside of the __init__ otherwise frameGeometries are not valid
        super(MessageDialog, self).resizeEvent(ev)

        activeWindow = QtWidgets.QApplication.activeWindow()
        if activeWindow:
            point = activeWindow.rect().center()
            global_point = activeWindow.mapToGlobal(point)
            self.move(global_point
                      - self.frameGeometry().center()
                      + self.frameGeometry().topLeft())


def showInfo(title, message, parent=None, iconPath=None):
    """Display an info message
    """
    dialog = MessageDialog('Information', title, message, Information, iconPath, parent)
    dialog.setStandardButtons(Ok)

    #dialog = QtWidgets.QMessageBox.information(parent, title, message)
    dialog.raise_()
    dialog.exec_()
    return


def showNotImplementedMessage():
    showInfo('Not implemented yet!',
             'This function has not been implemented in the current version')


def showOkCancel(title, message, parent=None, iconPath=None):
    dialog = MessageDialog('Query', title, message, Question, iconPath, parent)

    dialog.setStandardButtons(Ok | Cancel)
    dialog.setDefaultButton(Ok)

    dialog.raise_()
    return dialog.exec_() == Ok


def showYesNo(title, message, parent=None, iconPath=None):
    dialog = MessageDialog('Query', title, message, Question, iconPath, parent)

    dialog.setStandardButtons(Yes | No)
    dialog.setDefaultButton(Yes)

    dialog.raise_()
    return dialog.exec_() == Yes


def showRetryIgnoreCancel(title, message, parent=None, iconPath=None):
    dialog = MessageDialog('Retry', title, message, Question, iconPath, parent)

    dialog.setStandardButtons(Retry | Ignore | Cancel)
    dialog.setDefaultButton(Retry)

    dialog.raise_()
    result = dialog.exec_()

    if result == Retry:
        return True

    elif result == Cancel:
        return False

    else:
        return None


def showSaveDiscardCancel(title, message, parent=None, iconPath=None):
    dialog = MessageDialog('Query', title, message, Question, iconPath, parent)

    dialog.setStandardButtons(Save | Discard | Cancel)
    dialog.setDefaultButton(Save)

    dialog.raise_()
    result = dialog.exec_()

    if result == Save:
        return True

    elif result == Discard:
        return False

    else:
        return None


def showWarning(title, message, parent=None, iconPath=None):
    dialog = MessageDialog('Warning', title, message, Warning, iconPath, parent)

    dialog.setStandardButtons(Close)
    dialog.raise_()
    dialog.exec_()
    return


def showOkCancelWarning(title, message, parent=None, iconPath=None):
    dialog = MessageDialog('Warning', title, message, Warning, iconPath, parent)

    dialog.setStandardButtons(Ok | Cancel)
    dialog.setDefaultButton(Cancel)

    dialog.raise_()
    return dialog.exec_() == Ok


def showYesNoWarning(title, message, parent=None, iconPath=None):
    dialog = MessageDialog('Warning', title, message, Warning, iconPath, parent)

    dialog.setStandardButtons(Yes | No)
    dialog.setDefaultButton(No)

    dialog.raise_()
    return dialog.exec_() == Yes


def showMulti(title, message, texts, objects=None, parent=None, iconPath=None, okText='OK', cancelText='Cancel', destructive=(), checkbox=None, checked=True):
    if objects:
        assert len(objects) == len(texts)

    dialog = MessageDialog('Query', title, message, Question, iconPath, parent)
    dialog.setFocus()

    _checkbox = None

    for text in texts:
        lower_text = text.strip().lower()

        if checkbox and (lower_text in checkbox or checkbox in lower_text):
            raise Exception('Checkboxes and buttons cannot have the same name!')
        else:
            role = QtWidgets.QMessageBox.ActionRole

            if lower_text == 'cancel' or lower_text == cancelText.strip().lower():
                role = QtWidgets.QMessageBox.RejectRole

            if not isinstance(destructive, str):
                destructive = [item.strip().lower() for item in destructive]
            else:
                destructive = destructive.strip().lower()
            if lower_text in destructive:
                role = QtWidgets.QMessageBox.DestructiveRole

            if lower_text == 'ok' or lower_text == okText.strip().lower():
                role = QtWidgets.QMessageBox.AcceptRole

            button = dialog.addButton(text, role)

            if lower_text == 'ok' or lower_text == okText.strip().lower():
                dialog.setDefaultButton(button)

        if checkbox != None:
            _checkbox = CheckBox(parent=dialog, text=checkbox)
            _checkbox.setChecked(checked)
            dialog.setCheckBox(_checkbox)

    if _checkbox != None:
        _checkbox.setFocus()

    dialog.raise_()
    index = dialog.exec_()

    result = ''
    if dialog.clickedButton() != None:
        if objects:
            result = objects[index]

        else:
            result = texts[index]

    if checkbox != None:
        if _checkbox.isChecked():
            result = ' %s %s ' % (result, checkbox)

    return result


def showError(title, message, parent=None, iconPath=None):
    dialog = MessageDialog('Error', title, message, Critical, iconPath, parent)

    dialog.setStandardButtons(Close)
    dialog.raise_()
    dialog.exec_()
    return


def showMessage(title, message, parent=None, iconPath=None):
    dialog = MessageDialog('Message', title, message, Information, iconPath, parent)

    dialog.setStandardButtons(Close)
    dialog.raise_()
    dialog.exec_()
    return


# testing simple progress/busy popup

from PyQt5 import QtCore
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.Label import Label
from contextlib import contextmanager
from time import sleep, time


class progressPopup(CcpnDialog):
    """
    Open a small popup to allow changing the name of a Note
    """

    def __init__(self, parent=None, mainWindow=None, title='busy', busyFunc=None, progressMax=1,
                 **kwds):
        """
        Initialise the widget
        """
        super().__init__(parent, setLayout=True, windowTitle='busy', **kwds)

        # self.mainWindow = mainWindow
        # self.application = mainWindow.application
        # self.project = mainWindow.application.project
        # self.current = mainWindow.application.current

        self.setParent(parent)
        self.busyFunc = busyFunc

        # progress bar
        self.progressbar = QtWidgets.QProgressBar()
        self.progressbar.reset()  # resets the progress bar
        self.progressbar.setAlignment(Qt.AlignCenter)  # centers the text
        # 'valueChanged()' signal
        self.progressbar.valueChanged.connect(self.progress_changed)
        self.progressbar.setMinimum(0)
        self.progressbar.setMaximum(progressMax)
        # # 'start' button
        # self.btn_start = QtWidgets.QPushButton('Start')
        # # 'clicked()' signal
        # self.btn_start.clicked.connect(self.start)
        #
        # timer
        self.timer = QtCore.QTimer()
        # 'timeout()' signal
        self.timer.timeout.connect(self.progress_simulation)

        self.label = Label(self, title, grid=(0, 0))

        # from ccpn.framework.Application import getApplication
        # getApp = getApplication()
        # if getApp and hasattr(getApp, '_fontSettings'):
        #     self.label.setFont(getApp._fontSettings.messageFont)
        #     self.setFont(getApp._fontSettings.messageFont)
        setWidgetFont(self, )

        # self.layout().addWidget(self.progressbar)

        # vlayout.addWidget(self.btn_start)
        # vlayout.addStretch()
        # self.setLayout(vlayout)

        # self.setWindowFlags(QtCore.Qt.WindowTitleHint)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.show()
        self.raise_()
        self.setModal(True)

    # 'progress_simulation()' slot
    @pyqtSlot()
    def progress_simulation(self):
        value = self.progressbar.value()  # gets the current value of the progress bar
        self.progressbar.setValue(value + 1)  # adds 1 to the current value
        self.progressbar.update()

    # 'start()' slot
    # @pyqtSlot()
    # def start(self):
    #     self.progressbar.reset()  # resets the progress bar
    #     self.timer.start(40)  # interval of 40 milliseconds

    # 'progress_changed()' slot
    @pyqtSlot(int)
    def progress_changed(self, value):
        # stops the timer if the progress bar reaches its maximum value
        if value == self.progressbar.maximum():
            self.timer.stop()


@contextmanager
def progressManager(parent, title=None, progressMax=100):
    thisProg = progressPopup(parent=parent, title=title, progressMax=progressMax)

    try:
        thisProg.progress_simulation()
        thisProg.update()
        QtWidgets.QApplication.processEvents()  # still doesn't catch all the paint events
        sleep(0.1)

        yield  # yield control to the main process

    finally:
        thisProg.update()
        QtWidgets.QApplication.processEvents()  # hopefully it will redraw the popup
        thisProg.close()


def _stoppableProgressBar(data, title='Calculating...', buttonText='Cancel'):
    """ Use this for opening a _stoppableProgressBar before time consuming operations. the cancel button allows
     the user to stop the loop manually.
    eg:
    for i in _stoppableProgressBar(range(10), title, buttonText):
        # do stuff
        pass
    for use in a zip loop, wrap with 'list':
    eg for (cs, ts) in _stoppableProgressBar(list(zip(controlSpectra, targetSpectra)))
    """

    widget = QtWidgets.QProgressDialog(title, buttonText, 0, len(data))  # starts = 0, ends = len(data)
    widget.setAutoClose(True)
    widget.raise_()
    c = 0
    for v in iter(data):
        QtCore.QCoreApplication.instance().processEvents()
        if widget.wasCanceled():
            raise RuntimeError('Stopped by user')
        c += 1
        widget.setValue(c)
        yield (v)


import math, sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import *


class busyOverlay(QtWidgets.QWidget):
    def __init__(self, parent=None):

        QtWidgets.QWidget.__init__(self, parent)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)

    def paintEvent(self, event):

        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), QBrush(QColor(255, 255, 255, 127)))
        painter.setPen(QPen(Qt.NoPen))

        for i in range(6):
            if (self.counter / 5) % 6 == i:
                painter.setBrush(QBrush(QColor(127 + (self.counter % 5) * 32, 127, 127)))
            else:
                painter.setBrush(QBrush(QColor(127, 127, 127)))
            painter.drawEllipse(
                    self.width() / 2 + 30 * math.cos(2 * math.pi * i / 6.0) - 10,
                    self.height() / 2 + 30 * math.sin(2 * math.pi * i / 6.0) - 10,
                    20, 20)

            painter.end()

    def showEvent(self, event):
        self.timer = self.startTimer(50)
        self.counter = 0

    def timerEvent(self, event):
        self.counter += 1
        self.update()
        if self.counter == 60:
            self.killTimer(self.timer)
            self.hide()


# class MainWindow(QMainWindow):
#
#   def __init__(self, parent = None):
#
#        QMainWindow.__init__(self, parent)
#
#       widget = QWidget(self)
#       self.editor = QTextEdit()
#       self.editor.setPlainText("0123456789"*100)
#       layout = QGridLayout(widget)
#       layout.addWidget(self.editor, 0, 0, 1, 3)
#       button = QPushButton("Wait")
#       layout.addWidget(button, 1, 1, 1, 1)
#
#       self.setCentralWidget(widget)
#       self.overlay = Overlay(self.centralWidget())
#       self.overlay.hide()
#       button.clicked.connect(self.overlay.show)
#
#   def resizeEvent(self, event):
#
#       self.overlay.resize(event.size())
#       event.accept()

if __name__ == '__main__':
    import sys
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.BasePopup import BasePopup
    from ccpn.ui.gui.widgets.Button import Button
    import time


    app = QtWidgets.QApplication(sys.argv)


    # for i in _stoppableProgressBar([1]*10000):
    #     time.sleep(0.2)

    def callback():
        # print(showInfo('My info window', 'test info'))
        # print(showMulti('Test', 'Multi Choice', ['Apples', 'Bananas', 'Pears']))
        # print(showError('Test', 'This is a test error message'))
        # print(showYesNo('Test', 'Yes or No message'))
        # # print(showOkCancel('Test', 'Ok or Cancel message'))
        # # print(showRetryIgnoreCancel('Test', 'Some message'))
        # # print(showWarning('Test', 'Warning message'))
        # print(showWarning(
        #     'Test for a basic popup with a long line of text as the basic text and a path: /Users/ejb66/PycharmProjects/Git/AnalysisV3/internal/scripts/something/filename.txt',
        #     'Warning message'))

        print(showWarning('Another Warning',
                          'Test for a basic popup with a long line of text as the basic text and a path:\n/Users/ejb66/PycharmProjects/Git/AnalysisV3/internal/scripts/something/filename.txt'))

        print(showWarning('Another Warning and Test for a basic popup with a long line of text as the basic text',
                          'Test for a basic popup with a long line of text as the basic text and a path\n/Users/ejb66/PycharmProjects/Git/AnalysisV3/internal/scripts/something/filename.txt '
                          'and text with no spaces qwertyuiopasdfghjklzxcvbnm0123456789_qwertyuiopasdfghjklzxcvbnm0123456789_qwertyuiopasdfghjklzxcvbnm0123456789_qwertyuiopasdfghjklzxcvbnm0123456789'))

        print(showWarning('Another Warning and Test qwertyuiopasdfghjklzxcvbnm0123456789_qwertyuiopasdfghjklzxcvbnm0123456789_qwertyuiopasdfghjklzxcvbnm0123456789_qwertyuiopasdfghjklzxcvbnm0123456789\n for a basic popup with a long line of text as the basic text',
                          'Test for a basic popup with a long line of text as the basic text and a path\n/Users/ejb66/PycharmProjects/Git/AnalysisV3/internal/scripts/something/filename.txt '
                          'and text with no spaces qwertyuiopasdfghjklzxcvbnm0123456789_qwertyuiopasdfghjklzxcvbnm0123456789_qwertyuiopasdfghjklzxcvbnm0123456789_qwertyuiopasdfghjklzxcvbnm0123456789 something\n else'))


    # app = TestApplication()
    # # popup = BasePopup(title='Test MessageReporter')
    # #popup.setSize(200,30)
    # # button = Button(popup, text='hit me', callback=callback)
    #
    # popup = progressPopup(busyFunc=callback)
    #
    # popup.show()
    # popup.raise_()
    #
    # app.start()
    callback()
