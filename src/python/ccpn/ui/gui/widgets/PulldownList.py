"""
PulldownList widget

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
__dateModified__ = "$dateModified: 2020-06-02 09:52:54 +0100 (Tue, June 02, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from contextlib import contextmanager
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Icon import Icon


NULL = object()


#TODO: clean various methods, removing 'depreciated' ones

class PulldownList(QtWidgets.QComboBox, Base):
    popupAboutToBeShown = QtCore.pyqtSignal()
    pulldownTextEdited = QtCore.pyqtSignal()
    pulldownTextReady = QtCore.pyqtSignal(str)

    def __init__(self, parent, texts=None, objects=None,
                 icons=None, callback=None,
                 clickToShowCallback= None, index=0,
                 backgroundText=None, headerText=None,
                 headerEnabled=False, headerIcon=None,
                 editable=False, maxVisibleItems=16,
                 **kwds):
        """

        :param parent:
        :param texts:
        :param objects:
        :param icons:
        :param callback:
        :param index:
        :param backgroundText: a transparent text that will disappear as soon as you click to type.
                                the place holder or the transparent "backgroundText" will work only if the pulldown is editable.
                                Otherwise use HeaderText and enabled = False if you need only a title inside the pulldown
        :param headerText: text of first item of the pullDown. E.g. '-- Select Item --'
        :param headerEnabled: True to be selectable, False to disable and be grayed out
        :param editable: If True: allows for editing the value
        :param clickToShowCallback: callback when click to open the pulldown. Used to populate pulldown only when clicked the first time
        :param kwds:
        """
        super().__init__(parent)
        Base._init(self, **kwds)

        # focus can be set with the tab keys and mouse
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.text = None
        self.object = None
        self.texts = []
        self.objects = []
        self.headerText = headerText
        self.headerEnabled = headerEnabled
        self.headerIcon = headerIcon
        self.backgroundText = backgroundText

        if editable:
            self.setEditable(editable)
            if self.backgroundText:
                self.lineEdit().setPlaceholderText(str(self.backgroundText))
            self.lineEdit().textEdited.connect(self._emitPulldownTextEdited)
            #GST this cures a bug where the text background overwrites the popup button...
            self.lineEdit().setStyleSheet('background: transparent')

        # self.setIconSize(QtCore.QSize(22,22))

        PulldownList.setData(self, texts, objects, index, icons,
                             headerText=headerText, headerEnabled=headerEnabled, headerIcon=headerIcon)
        self.setCallback(callback)
        self.clickToShowCallback = clickToShowCallback
        if self.clickToShowCallback:
            self.popupAboutToBeShown.connect(self.clickToShowCallback)

        self.setStyleSheet("""
    PulldownList {
      padding-top: 3px;
      padding-bottom: 3px;
      padding-left: 2px;
      combobox-popup: 0;
    }
    """)

        self.setMaxVisibleItems(maxVisibleItems)
        self._editedText = None

        # self.connect(self, QtCore.SIGNAL('currentIndexChanged(int)'), self._callback)
        self.currentIndexChanged.connect(self._callback)

        if editable:
            self.currentIndexChanged.connect(self._textReady)
            self.lineEdit().editingFinished.connect(self._textReady)

    def setEditable(self, editable: bool) -> None:
        super(PulldownList, self).setEditable(editable)
        if editable:
            if self.backgroundText:
                self.lineEdit().setPlaceholderText(str(self.backgroundText))
            self.lineEdit().textEdited.connect(self._emitPulldownTextEdited)
            #GST this cures a bug where the text background overwrites the popup button...
            self.lineEdit().setStyleSheet('background: transparent')

    def focusOutEvent(self, ev) -> None:
        super(PulldownList, self).focusOutEvent(ev)
        if self.isEditable():
            self._textReady()

    def _textReady(self):
        self.pulldownTextReady.emit(self._editedText)

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super(PulldownList, self).showPopup()

    def currentObject(self):

        if self.objects:
            index = self.currentIndex()
            if index >= 0:
                return self.objects[index]

    def currentData(self):

        return (self.currentText(), self.currentObject())

    def select(self, item):
        # Works with an object or a text

        index = None

        if item in self.texts:
            index = list(self.texts).index(item)

        elif item in self.objects:
            index = list(self.objects).index(item)

        if index is not None:
            self.setCurrentIndex(index)

    def set(self, item):

        self.select(item)

    def setSelected(self, item, doCallback=False):

        print("ccpn.ui.gui.widgets.PulldownList.setSelected is deprecated use; .select()")

        self.select(item)

    def setIndex(self, index):

        self.setCurrentIndex(index)

    def get(self):

        return self.currentObject()

    def getSelected(self):

        # print("ccpn.ui.gui.widgets.PulldownList.getSelected is deprecated use; .currentData()")

        return self.currentData()

    def getObject(self):

        # print("ccpn.ui.gui.widgets.PulldownList.getObject is deprecated use; .currentObject()")

        return self.currentObject()

    def getText(self):

        # print("ccpn.ui.gui.widgets.PulldownList.getText is deprecated use; .currentText()")

        return self.currentText()

    def getItemIndex(self, text):
        for i in range(self.count()):
            if self.itemText(i) == text:
                return i

    def getSelectedIndex(self):

        # print("ccpn.ui.gui.widgets.PulldownList.getSelectedIndex is deprecated use; .currentIndex()")

        return self.currentIndex()

    def setup(self):

        print("ccpn.ui.gui.widgets.PulldownList.setup is deprecated use; .setData")

        return self.currentIndex()

    def _clear(self):
        if self.headerText is not None:
            self.clear()
            self._addHeaderLabel(self.headerText, self.headerEnabled, icon=self.headerIcon)
        else:
            self.clear()

    def _addHeaderLabel(self, headerText, headerEnabled, icon=None):
        self.addItem(text=headerText, icon=icon)
        headerIndex = self.getItemIndex(headerText)
        headerItem = self.model().item(headerIndex)
        headerItem.setEnabled(headerEnabled)

    def setData(self, texts=None, objects=None, index=None, icons=None, clear=True, headerText=None, headerEnabled=False, headerIcon=None):

        texts = texts or []
        objects = objects or []

        self.texts = []
        self.objects = []
        self.icons = []

        n = len(texts)
        if objects:
            msg = 'len(texts) = %d, len(objects) = %d'
            assert n == len(objects), msg % (n, len(objects))

        else:
            objects = texts[:]

        if icons:
            while len(icons) < n:
                icons.append(None)

        else:
            icons = [None] * n
        if clear:
            self.clear()

        if headerText:
            self._addHeaderLabel(headerText, headerEnabled, headerIcon)

        for i, text in enumerate(texts):
            self.addItem(text, objects[i], icons[i])

        if index is not None:
            self.setCurrentIndex(index)

    def addItem(self, text, object=NULL, icon=None, ):

        if icon:
            QtWidgets.QComboBox.addItem(self, Icon(icon), str(text))
        else:
            QtWidgets.QComboBox.addItem(self, str(text))

        if object is NULL:
            object = str(text)

        self.texts.append(text)
        self.objects.append(object)

    def setItemText(self, index, text):

        QtWidgets.QComboBox.setItemText(self, index, text)

        self.text[index] = text

    def removeItem(self, index):

        QtWidgets.QComboBox.removeItem(self, index)

        if index is self.index:
            self.index = None
            self.text = None
            self.object = None

        self.texts.pop(index)
        self.objects.pop(index)

    def disable(self):

        self.setDisabled(True)

    def enable(self):

        self.setEnabled(True)

    def disableLabelsOnPullDown(self, texts, colour=None):
        ''' Disable items from pulldown (not selectable, not clickable). And if given, changes the colour '''
        for text in texts:
            if text is not None:
                item = self.model().item(self.getItemIndex(text))
                if item:
                    item.setEnabled(False)
                    if colour is not None:
                        item.setForeground(QtGui.QColor(colour))

    def setCallback(self, callback):

        self.callback = callback

    def _callback(self, index):

        if index < 0:
            return
        self.index = index

        if self.objects and index < len(self.objects):
            self.object = self.objects[index]
        else:
            self.object = None

        if self.callback:
            if self.objects:
                self.callback(self.objects[index])
            elif self.texts:
                self.callback(self.texts[index])

    def setMaxVisibleItems(self, maxItems: int = 16):
        """Set the maximum height of the combobox when opened
        """
        super(PulldownList, self).setMaxVisibleItems(maxItems)

        # qt bug fix - maxVisible only works if the following is set in the stylesheet
        # self.setStyleSheet("combobox-popup: 0;")
        # This is currently set at the top but added here so I remember, Ed

    @QtCore.pyqtSlot()
    def _emitPulldownTextEdited(self):
        self._editedText = self.getText()
        self.pulldownTextEdited.emit()

    # def _blockEvents(self, blanking=False):
    #     """Block all updates/signals/notifiers in the widget.
    #     """
    #     # block on first entry
    #     if self._blockingLevel == 0:
    #         self.blockSignals(True)
    #         self.setUpdatesEnabled(False)
    #         if blanking:
    #             self.project.blankNotification()
    #
    #     self._blockingLevel += 1
    #
    # def _unblockEvents(self, blanking=False):
    #     """Unblock all updates/signals/notifiers in the widget.
    #     """
    #     if self._blockingLevel > 0:
    #         self._blockingLevel -= 1
    #
    #         # unblock all signals on last exit
    #         if self._blockingLevel == 0:
    #             if blanking:
    #                 self.project.unblankNotification()
    #             self.setUpdatesEnabled(True)
    #             self.blockSignals(False)
    #     else:
    #         raise RuntimeError('Error: PullDownList already at 0')
    #
    # @contextmanager
    # def _blockWidgetSignals(self, blanking=False):
    #     """Block all signals from the table
    #     """
    #     self._blockEvents(blanking)
    #     try:
    #         yield  # yield control to the calling process
    #
    #     except Exception as es:
    #         raise es
    #     finally:
    #         self._unblockEvents(blanking)


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog
    from functools import partial

    app = TestApplication()

    texts = ['Int', 'Float', 'String', '']
    objects = [int, float, str, 'Green']
    icons = [None, None, None, Icon(color='#008000')]


    def callback(object):
        print('callback', object)


    def callback2(object):
        print('HEY')
        print('callback2', object)

    def callback21():
        print('clciked')
        print('callback2')

    def abts(s):
        print('s',s.texts)


    popup = CcpnDialog(windowTitle='Test PulldownList', setLayout=True)
    #popup.setSize(250,50)
    policyDict = dict(
            vAlign='top',
            hPolicy='expanding',
            )
    policyDict = dict(
            vAlign='top',
            # hAlign='left',
            )
    #policyDict = dict(
    #   hAlign='left',
    # )
    #policyDict = {}

    pulldownList = PulldownList(parent=popup, texts=texts, icons=icons,
                                objects=objects, callback=callback, clickToShowCallback=callback21, grid=(0, 0), **policyDict
                                )
    pulldownList.popupAboutToBeShown.connect(partial(abts,pulldownList ))
    pulldownList.insertSeparator(2)
    pulldownList.clearEditText()

    pulldownList2 = PulldownList(parent=popup, texts=texts, editable=True,
                                 callback=callback2, clickToShowCallback=callback21, grid=(1, 0), **policyDict
                                 )
    pulldownList.clearEditText()

    popup.show()
    popup.raise_()
    app.start()
