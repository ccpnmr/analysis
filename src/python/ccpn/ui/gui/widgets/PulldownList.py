"""
PulldownList widget

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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-06-15 15:25:01 -0400 (Thu, June 15, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets

from ccpn.util.Logging import getLogger

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Font import setWidgetFont, getFontHeight
from ccpn.ui.gui.guiSettings import getColours, DIVIDER


NULL = object()


#TODO: clean various methods, removing 'deprecated' ones

class PulldownList(QtWidgets.QComboBox, Base):
    popupAboutToBeShown = QtCore.pyqtSignal()
    pulldownTextEdited = QtCore.pyqtSignal()
    pulldownTextReady = QtCore.pyqtSignal(str)

    def __init__(self, parent, texts=None, objects=None,
                 icons=None, callback=None,
                 clickToShowCallback=None, index=0,
                 backgroundText=None, headerText=None,
                 headerEnabled=False, headerIcon=None,
                 editable=False, maxVisibleItems=16,
                 iconSize=None, toolTips=None,
                 **kwds):
        """

        :param parent:
        :param texts:
        :param objects:
        :param icons:
        :param callback:
        :param index:
        :param backgroundText: a transparent text that will disappear as soon as you click to type.
                                the place-holder or the transparent "backgroundText" will work only if the pulldown is editable.
                                Otherwise, use HeaderText and enabled = False if you need only a title inside the pulldown
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

        # replace with a simple listView - fixes stylesheet hassle; default QComboBox listview can't be changed
        self._list = QtWidgets.QListView()
        self.setView(self._list)
        setWidgetFont(self._list, )
        # add a scrollBar for long lists
        self._list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self._list.setMinimumSize(self.sizeHint())

        self.setEditable(editable)
        self._iconSize = iconSize or getFontHeight() or 16
        self.setIconSize(QtCore.QSize(self._iconSize, self._iconSize))

        self.setData(texts, objects, index, icons,
                     headerText=headerText, headerEnabled=headerEnabled, headerIcon=headerIcon)
        self.setCallback(callback)
        self.clickToShowCallback = clickToShowCallback
        if self.clickToShowCallback:
            self.popupAboutToBeShown.connect(self.clickToShowCallback)

        self.setStyleSheet('PulldownList { padding: 3px 3px 3px 3px; combobox-popup: 0; }')
        # this (or similar) can now be added to the stylesheet if needed
        # 'QListView::item { padding: 12px; }')

        self.setMaxVisibleItems(maxVisibleItems)
        self._editedText = None

        self.currentIndexChanged.connect(self._callback)

        if editable:
            self.currentIndexChanged.connect(self._textReady)
            self.lineEdit().editingFinished.connect(self._textReady)
        if toolTips:
            self.setToolTips(toolTips)

        self._list.setItemDelegate(ComboBoxDividerDelegate())

        # possibly for later if gray 'Select' preferred
        # self.currentIndexChanged.connect(self._highlightCurrentText)
        # self.currentTextChanged.connect(self._highlightCurrentText)

    def setEditable(self, editable: bool) -> None:
        super(PulldownList, self).setEditable(editable)
        if editable:
            if self.backgroundText:
                self.lineEdit().setPlaceholderText(str(self.backgroundText))
            self.lineEdit().textEdited.connect(self._emitPulldownTextEdited)
            #GST this cures a bug where the text background overwrites the popup button...
            self.lineEdit().setStyleSheet('background: transparent')
            # set the font for the placeHolderText (not set by Base)
            setWidgetFont(self.lineEdit(), )

    def focusOutEvent(self, ev) -> None:
        super(PulldownList, self).focusOutEvent(ev)
        if self.isEditable():
            self._textReady()

    def _textReady(self):
        self.pulldownTextReady.emit(self._editedText)

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        self._list.setMinimumSize(self.sizeHint())
        super(PulldownList, self).showPopup()

    def currentIndex(self) -> int:
        ind = super().currentIndex()

        # remove number of preceding separators
        cc = len([filter(None, (self.model().index(rr, 0).data(QtCore.Qt.AccessibleDescriptionRole)
                                for rr in range(ind)))])
        return ind - cc

    def currentObject(self):

        if self.objects:
            index = self.currentIndex()
            if index >= 0:
                return self.objects[index]

    def currentData(self):

        return (self.currentText(), self.currentObject())

    def select(self, item):
        """Select an item or text
        :param item: an item or text of the pulldown list
        """
        indx = None

        if item in self.texts:
            indx = self.getItemIndex(item)

        elif item in self.objects:
            indx = list(self.objects).index(item)

        if indx is not None:
            self.setCurrentIndex(indx)

    def paintEvent(self, e: QtGui.QPaintEvent) -> None:
        """Set the colour of the selected pulldown-text
        """
        try:
            if (model := self.model()):
                palette = self.palette()
                if (item := model.item(self.currentIndex())) is not None and item.text():
                    # use the palette to change the colour of the selection text - may not match for other themes
                    palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.Text, item.foreground().color())
                else:
                    palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.Text, QtGui.QColor('black'))

                self.setPalette(palette)
        except Exception:
            pass

        finally:
            super(PulldownList, self).paintEvent(e)

    def set(self, item):

        self.select(item)

    def setSelected(self, item, doCallback=False):

        getLogger().warning("ccpn.ui.gui.widgets.PulldownList.setSelected is deprecated use; .select()")

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

    def selectValue(self, value, default=0) -> int:
        """Select the item corresponding to value or item with index zero if value is not present
        :return index of selected item
        """
        if default < 0 or default > len(self.texts):
            raise ValueError(f'{self.__class__.__name__}.selectValue: invalid value for default {default!r}')
        idx = self.texts.index(value) if value in self.texts else default
        self.setIndex(idx)
        return idx

    def addItem(self, text, item=NULL, icon=None, ):

        if icon and isinstance(icon, QtGui.QIcon):
            super().addItem(icon, str(text))
        else:
            super().addItem(str(text))

        if item is NULL:
            item = str(text)

        self.texts.append(text)
        self.objects.append(item)

    def insertText(self, index, text):
        """Insert a text-item into the pulldown
        """
        if not (0 <= index < len(self.texts)):
            raise ValueError(f'index not in range [0, {len(self.texts) - 1}]')

        self.insertItem(index, str(text))
        self.texts.insert(index, str(text))
        self.objects.insert(index, str(text))

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
        """ Disable items from pulldown (not selectable, not clickable). And if given, changes the colour """
        for text in texts:
            if text is not None and self.getItemIndex(text) is not None:
                if item := self.model().item(self.getItemIndex(text)):
                    item.setEnabled(False)
                    if colour is not None:
                        item.setForeground(QtGui.QColor(colour))

    def setCallback(self, callback):

        self.callback = callback

    def setToolTips(self, toolTips):
        if len(self.texts) == len(toolTips):
            for text, toolTip in zip(self.texts, toolTips):
                if item := self.model().item(self.getItemIndex(text)):
                    item.setToolTip(toolTip)

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

    def setPulldownColour(self, selectColour='lime'):
        from ccpn.util.Colour import spectrumColours
        import random

        for item in spectrumColours.items():
            pix = QtGui.QPixmap(QtCore.QSize(20, 20))
            pix.fill(QtGui.QColor(item[0]))
            self.addItem(icon=QtGui.QIcon(pix), text=item[1])
        try:
            self.select(selectColour)
        except Exception:
            self.select(random.choice(self.texts))

    def _getSaveState(self):
        """
        Internal. Called for saving/restoring the widget state.
        """
        return self.currentText()

    def _setSavedState(self, value):
        """
        Internal. Called for saving/restoring the widget state.
        """
        return self.set(value)

    # possibly for later if gray 'Select' preferred
    # def _highlightCurrentText(self):
    #     """Highlight the selected text the colour from the current items
    #     """
    #     ind = self.currentIndex()
    #     model = self.model()
    #     item = model.item(ind)
    #     print(f'  select {ind}')
    #
    #     if item is not None:
    #         color = item.foreground().color()
    #         # use the palette to change the colour of the selection text - may not match for other themes
    #         palette = self.palette()
    #         palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.Text, color)
    #         self.setPalette(palette)


#=========================================================================================
# ComboBoxDividerDelegate - adds a visible divider
#=========================================================================================

class ComboBoxDividerDelegate(QtWidgets.QStyledItemDelegate):
    """ComboBox with a visible divider
    """

    _DIVIDERCOLOR = None
    _BORDER = None

    def __init__(self, *args, **kwds):
        super().__init__(*args, *kwds)

        # set the parameters for the divider
        self._DIVIDERCOLOR = QtGui.QColor(getColours()[DIVIDER])
        self._BORDER = getFontHeight() // 4

    def paint(self, painter, option, index) -> None:
        if not index.isValid():
            return

        if index.data(QtCore.Qt.AccessibleDescriptionRole) is not None:
            # draw a dividing line across the pulldown list
            painter.save()
            painter.setPen(QtGui.QPen(self._DIVIDERCOLOR, 2))

            painter.drawLine(option.rect.left() + self._BORDER, option.rect.center().y(),
                             option.rect.right() - self._BORDER, option.rect.center().y())

            painter.restore()

        return super().paint(painter, option, index)


#=========================================================================================
# Testing
#=========================================================================================

def main():
    """A few small tests
    """
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog
    from functools import partial

    app = TestApplication()

    texts = ['Int', 'Float', 'String', '']
    objects = [int, float, str, 'Green']
    icons = [None, None, None, Icon(color='#008000')]

    def callback(obj):
        print('callback', obj)

    def callback2(obj):
        print('HEY')
        print('callback2', obj)

    def callback21():
        print('clicked')
        print('callback2')

    def abts(s):
        print('s', s.texts)

    popup = CcpnDialog(windowTitle='Test PulldownList', setLayout=True)
    #popup.setSize(250,50)
    policyDict = dict(
            vAlign='top',
            )

    pulldownList = PulldownList(parent=popup, texts=texts, icons=icons,
                                objects=objects, callback=callback, clickToShowCallback=callback21, grid=(0, 0), **policyDict
                                )

    pulldownList.popupAboutToBeShown.connect(partial(abts, pulldownList))
    pulldownList.insertSeparator(2)
    pulldownList.clearEditText()

    pulldownList2 = PulldownList(parent=popup, texts=texts, editable=True,
                                 callback=callback2, clickToShowCallback=callback21, grid=(1, 0), **policyDict
                                 )
    pulldownList.clearEditText()

    popup.show()
    popup.raise_()
    app.start()

    # # test - adding a different widget to a combobox
    # import sys
    # from PyQt5.QtCore import Qt, QVariant
    # from PyQt5 import QtGui, QtWidgets
    #
    #
    # app = QtWidgets.QApplication(sys.argv)
    # model = QtGui.QStandardItemModel()
    #
    # items = [("ABC", True),
    #          ("DEF", False),
    #          ("GHI", False)]
    #
    # for text, checked in items:
    #     text_item = QtGui.QStandardItem(text)
    #     checked_item = QtGui.QStandardItem()
    #     checked_item.setData(QVariant(checked), Qt.CheckStateRole)
    #     model.appendRow([text_item, checked_item])
    #
    # view = QtWidgets.QTreeView()
    # view.header().hide()
    # view.setRootIsDecorated(False)
    #
    # combo = QtWidgets.QComboBox()
    # combo.setView(view)
    # combo.setModel(model)
    # combo.show()
    #
    # sys.exit(app.exec_())


if __name__ == '__main__':
    # call testing
    main()
