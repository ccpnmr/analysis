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
__dateModified__ = "$dateModified: 2021-06-09 18:47:01 +0100 (Wed, June 09, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from functools import partial
from ccpn.ui.gui.widgets.Base import SignalBlocking
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.ColourDialog import ColourDialog
from ccpn.ui.gui.widgets.Entry import Entry
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox, ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.CompoundBaseWidget import CompoundBaseWidget
from ccpn.ui.gui.widgets.CompoundView import CompoundView
from ccpn.ui.gui.widgets.TextEditor import TextEditor, PlainTextEditor
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.util.Colour import spectrumColours
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.guiSettings import getColours, BORDERFOCUS, BORDERNOFOCUS


class ListCompoundWidget(CompoundBaseWidget):
    """
    Compound class comprising a Label, a PulldownList, and a ListWidget, combined in a
    CompoundBaseWidget (i.e.a Frame)

    NB: can also be used as only a Label and a ListWidget by hiding the Pulldown:
          myWidget.showPulldownList(False)

      orientation       widget layout
      ------------      ------------------------
      left:             Label       PullDown
                                    ListWidget

      centreLeft:                   PullDown
                        Label       ListWidget

      right:            PullDown    Label
                        ListWidget

      centreRight:      PullDown
                        ListWidget  Label

      top:              Label
                        PullDown
                        ListWidget

      bottom:           PullDown
                        ListWidget
                        Label

      horizontal:       Label       PullDown  ListWidget

    """
    layoutDict = dict(
            # grid positions for label, pulldown and listWidget for the different orientations
            left=[(0, 0), (0, 1), (1, 1)],
            centreLeft=[(1, 0), (0, 1), (1, 1)],
            right=[(0, 1), (0, 0), (1, 0)],
            centreRight=[(1, 1), (0, 0), (1, 0)],
            top=[(0, 0), (1, 0), (2, 0)],
            bottom=[(2, 0), (0, 0), (1, 0)],
            horizontal=[(0, 0), (0, 1), (0, 2)],
            )

    LIST_BORDER_WIDTH = 1
    LIST_BORDER_COLOR = '#a9a9a9'

    def __init__(self, parent=None, showBorder=False, orientation='left',
                 minimumWidths=None, maximumWidths=None, fixedWidths=None,
                 labelText='', texts=None, callback=None,
                 defaults=None, uniqueList=True, compoundKwds=None,
                 **kwds):
        """
        :param parent: parent widget
        :param showBorder: flag to display the border of Frame (True, False)
        :param orientation: flag to determine the orientation of the labelText relative to the Pulldown/ListWidget.
                            Allowed values: 'left', 'right', 'top', 'bottom', 'centreLeft, centreRight, horizontal
        :param minimumWidths: tuple of three values specifying the minimum width of the Label, Pulldown and ListWidget,
                              respectively
        :param maximumWidths: tuple of three values specifying the maximum width of the Label and Pulldown and ListWidget,
                              respectively
        :param fixedWidths: tuple of three values specifying the maximum width of the Label and Pulldown and ListWidget,
                            respectively
        :param labelText: Text for the Label
        :param texts: (optional) iterable generating text values for the Pulldown
        :param callback: (optional) callback for the Pulldown
        :param defaults: (optional) iterable of initially add elements to the ListWidget (text or index)
        :param uniqueList: (True) only allow unique elements in the ListWidget
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
        """

        CompoundBaseWidget.__init__(self, parent=parent, layoutDict=self.layoutDict, orientation=orientation,
                                    showBorder=showBorder, **kwds)

        self.label = Label(parent=self, text=labelText, vAlign='center')
        self._addWidget(self.label)

        # pulldown
        texts = ['> select-to-add <'] + list(texts) if texts else ['> select-to-add <']
        self.pulldownList = PulldownList(parent=self, texts=texts, callback=self._addToListWidget, index=0)
        self.pulldownList.setObjectName(labelText)
        self._addWidget(self.pulldownList)

        # listWidget
        self.listWidget = ListWidget(parent=self, callback=callback, infiniteHeight=True, **(compoundKwds or {}))
        self.listWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._uniqueList = uniqueList
        if defaults is not None:
            for dft in defaults:
                self.addPulldownItem(dft)
        self._addWidget(self.listWidget)

        styleSheet = '.ListWidget {border: %ipx solid %s; border-radius: 3px}'
        styleSheet = styleSheet % (self.LIST_BORDER_WIDTH, self.LIST_BORDER_COLOR)
        self.listWidget.setStyleSheet(styleSheet)

        if minimumWidths is not None:
            self.setMinimumWidths(minimumWidths)

        if maximumWidths is not None:
            self.setMinimumWidths(maximumWidths)

        if fixedWidths is not None:
            self.setFixedWidths(fixedWidths)

    def minimumSizeHint(self) -> QtCore.QSize:
        result = super().minimumSizeHint()

        margins = self.listWidget.contentsMargins().top() + self.listWidget.contentsMargins().bottom() + \
                  self.pulldownList.contentsMargins().top() + self.pulldownList.contentsMargins().bottom()
        spacing = self.layout().spacing()
        minHeightHint = self.listWidget.minimumSizeHint().height() + self.pulldownList.minimumSizeHint().height() + \
                        margins + spacing
        result.setHeight(minHeightHint)

        return result

    # def setPreSelect(self, callBack=None):
    #     """
    #     Add a user callback to the pulldown that fires on a mouse click.
    #     facilitates populating the pulldown list just before it opens
    #     :param callBack = method to call on click:
    #     """
    #     if callBack:
    #         self.pulldownList.installEventFilter(self)
    #         self._preSelectCallBack = callBack
    #
    # def eventFilter(self, target, event):
    #     """
    #     call the user callback when the pulldown has been clicked
    #     """
    #     if target == self.pulldownList and event.type() == QtCore.QEvent.MouseButtonPress:
    #         self._preSelectCallBack()
    #     return False

    def setLabelText(self, label):
        """Set the text for the list widget label
        """
        self.label.setText(label)

    def setItems(self, list):
        """
        set the list of items in the pulldown
        """
        self.pulldownList.clear()
        self.pulldownList.addItems(list)

    def showPulldownList(self, show):
        if show:
            self.pulldownList.show()
        else:
            self.pulldownList.hide()

    def setTexts(self, ll: list = []):
        self.listWidget.clear()
        for i in ll:
            if isinstance(i, str):
                self.listWidget.addItem(i)

    def getTexts(self):
        """Convenience: Return list of texts in listWidget"""
        return [self.listWidget.item(i).text() for i in range(self.listWidget.count())]

    def addText(self, text):
        """Convenience: Add text to listWidget"""
        if text is None:
            return
        if self._uniqueList and text in self.getTexts():
            return
        self.listWidget.addItem(text)

    def removeTexts(self, texts):
        """Convenience: Remove texts to listWidget"""
        self.listWidget.removeTexts(texts)

    def addPulldownItem(self, item):
        """convenience: add pulldown item (text or index) to list"""
        texts = self.pulldownList.texts
        if item in texts:
            self.addText(item)
            return
        try:
            item = texts[int(item) + 1]  # added "select-to-add" to pulldownlist
            self.addText(item)
        except:
            pass

    def _addToListWidget(self, item):
        """Callback for Pulldown, adding the selcted item to the listWidget"""
        if item is not None and self.pulldownList.getSelectedIndex() != 0:
            self.addText(item)
        # reset to first > select-to-add < entry
        self.pulldownList.setIndex(0)


class EntryCompoundWidget(CompoundBaseWidget):
    """
    Compound class comprising a Label and a Entry widget, combined in a CompoundBaseWidget (i.e. a Frame)

      orientation       widget layout
      ------------      ------------------------
      left:             Label       Entry

      right:            Entry       Label

      top:              Label
                        Entry

      bottom:           Entry
                        Label

    """
    layoutDict = dict(
            # grid positions for label and Entry for the different orientations
            left=[(0, 0), (0, 1)],
            right=[(0, 1), (0, 0)],
            top=[(0, 0), (1, 0)],
            bottom=[(1, 0), (0, 0)],
            )

    def __init__(self, parent=None, mainWindow=None,
                 showBorder=False, orientation='left',
                 minimumWidths=None, maximumWidths=None, fixedWidths=None,
                 labelText='', entryText='', callback=None, default=None, editable=True,
                 sizeAdjustPolicy=None, compoundKwds={}, tipText=None,
                 **kwds):
        """
        :param parent: parent widget
        :param showBorder: flag to display the border of Frame (True, False)
        :param orientation: flag to determine the orientation of the labelText relative to the Entry widget.
                            Allowed values: 'left', 'right', 'top', 'bottom'
        :param minimumWidths: tuple of two values specifying the minimum width of the Label and Entry widget, respectively
        :param maximumWidths: tuple of two values specifying the maximum width of the Label and Entry widget, respectively
        :param labelText: Text for the Label
        :param callback: (optional) callback for the Entry
        :param default: (optional) initial text of the Entry
        :param editable: (optional) set Entry to editable
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
        """

        CompoundBaseWidget.__init__(self, parent=parent, layoutDict=self.layoutDict, orientation=orientation,
                                    showBorder=showBorder, **kwds)

        self.label = Label(parent=self, text=labelText, vAlign='center')
        self._addWidget(self.label)
        if tipText:
            self.label.setToolTip(tipText)

        self.entry = Entry(parent=self, text=entryText, callback=callback, editable=editable, **compoundKwds)
        self._addWidget(self.entry)

        if default is not None:
            self.setText(default)

        if minimumWidths is not None:
            self.setMinimumWidths(minimumWidths)

        if maximumWidths is not None:
            self.setMinimumWidths(maximumWidths)

        if fixedWidths is not None:
            self.setFixedWidths(fixedWidths)

        # if sizeAdjustPolicy is not None:
        #     self.Entry.setSizeAdjustPolicy(sizeAdjustPolicy)

    def getText(self):
        """Convenience: Return text of Entry"""
        return self.entry.getText()

    def setText(self, text):
        """Convenience: set text of Entry"""
        self.entry.setText(text)


class TextEditorCompoundWidget(CompoundBaseWidget):
    """
    Compound class comprising a Label and a Entry widget, combined in a CompoundBaseWidget (i.e. a Frame)

      orientation       widget layout
      ------------      ------------------------
      left:             Label       Entry

      right:            Entry       Label

      top:              Label
                        Entry

      bottom:           Entry
                        Label

    """
    layoutDict = dict(
            # grid positions for label and Entry for the different orientations
            left=[(0, 0), (0, 1)],
            right=[(0, 1), (0, 0)],
            top=[(0, 0), (1, 0)],
            bottom=[(1, 0), (0, 0)],
            )

    def __init__(self, parent=None, mainWindow=None,
                 showBorder=False, orientation='left',
                 minimumWidths=None, maximumWidths=None, fixedWidths=None,
                 labelText='', callback=None, default=None, editable=True,
                 sizeAdjustPolicy=None, compoundKwds=None,
                 **kwds):
        """
        :param parent: parent widget
        :param showBorder: flag to display the border of Frame (True, False)
        :param orientation: flag to determine the orientation of the labelText relative to the Entry widget.
                            Allowed values: 'left', 'right', 'top', 'bottom'
        :param minimumWidths: tuple of two values specifying the minimum width of the Label and Entry widget, respectively
        :param maximumWidths: tuple of two values specifying the maximum width of the Label and Entry widget, respectively
        :param labelText: Text for the Label
        :param callback: (optional) callback for the Entry
        :param default: (optional) initial text of the Entry
        :param editable: (optional) set Entry to editable
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
        """

        CompoundBaseWidget.__init__(self, parent=parent, layoutDict=self.layoutDict, orientation=orientation,
                                    showBorder=showBorder, **kwds)
        _labelFrame = Frame(self, setLayout=True, vAlign='t')
        # self.label = Label(parent=self, text=labelText, vAlign='center')
        # self._addWidget(self.label)

        Spacer(_labelFrame, 4, 4, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed,
               grid=(0, 0))
        self.label = Label(parent=_labelFrame, text=labelText, grid=(1, 0))
        Spacer(_labelFrame, 2, 2, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(2, 0))

        self._addWidget(_labelFrame)

        self.textEditor = TextEditor(parent=self, callback=callback, editable=editable, **compoundKwds)
        self._addWidget(self.textEditor)

        if default is not None:
            self.setText(default)

        if minimumWidths is not None:
            self.setMinimumWidths(minimumWidths)

        if maximumWidths is not None:
            self.setMinimumWidths(maximumWidths)

        if fixedWidths is not None:
            self.setFixedWidths(fixedWidths)

        # if sizeAdjustPolicy is not None:
        #     self.textEditor.setSizeAdjustPolicy(sizeAdjustPolicy)

        if 'fitToContents' in compoundKwds:
            self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

    def getText(self):
        """Convenience: Return text of textEditor
        """
        return self.textEditor.get()

    def setText(self, text):
        """Convenience: set text of textEditor
        """
        self.textEditor.set(text)


class PulldownListCompoundWidget(CompoundBaseWidget):
    """
    Compound class comprising a Label and a PulldownList, combined in a CompoundBaseWidget (i.e. a Frame)

      orientation       widget layout
      ------------      ------------------------
      left:             Label       PullDown

      right:            PullDown    Label

      top:              Label
                        PullDown

      bottom:           PullDown
                        Label

    """

    layoutDict = dict(
            # grid positions for label and pulldown for the different orientations
            left=[(0, 0), (0, 1)],
            right=[(0, 1), (0, 0)],
            top=[(0, 0), (1, 0)],
            bottom=[(1, 0), (0, 0)],
            )

    def __init__(self, parent=None, mainWindow=None,
                 showBorder=False, orientation='left',
                 minimumWidths=None, maximumWidths=None, fixedWidths=None,
                 labelText='', texts=None, callback=None, default=None,
                 sizeAdjustPolicy=None, editable=False, compoundKwds=None,
                 **kwds):
        """
        :param parent: parent widget
        :param showBorder: flag to display the border of Frame (True, False)
        :param orientation: flag to determine the orientation of the labelText relative to the pulldown widget.
                            Allowed values: 'left', 'right', 'top', 'bottom'
        :param minimumWidths: tuple of two values specifying the minimum width of the Label and Pulldown widget, respectively
        :param maximumWidths: tuple of two values specifying the maximum width of the Label and Pulldown widget, respectively
        :param labelText: Text for the Label
        :param texts: (optional) iterable generating text values for the Pulldown
        :param callback: (optional) callback for the Pulldown
        :param default: (optional) initially selected element of the Pulldown (text or index)
        :param editable: If True: allows for editing the value
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
        """

        CompoundBaseWidget.__init__(self, parent=parent, layoutDict=self.layoutDict, orientation=orientation,
                                    showBorder=showBorder, **kwds)

        self.label = Label(parent=self, text=labelText, vAlign='center')
        self._addWidget(self.label)

        # pulldown text
        if texts is not None:
            texts = list(texts)
        # pulldown default index
        index = 0
        if default is not None and texts is not None and len(texts) > 0:
            if default in texts:
                index = texts.index(default)
            else:
                try:
                    index = int(default)
                except:
                    pass
        pulldownKwds = {'texts'   : texts,
                        'index'   : index,
                        'editable': editable,
                        'callback': callback,
                        }
        pulldownKwds.update(compoundKwds or {})
        self.pulldownList = PulldownList(parent=self, **pulldownKwds)
        self._addWidget(self.pulldownList)
        self.pulldownList.setObjectName(labelText)
        if default is not None:
            self.pulldownList.select(default)

        if minimumWidths is not None:
            self.setMinimumWidths(minimumWidths)

        if maximumWidths is not None:
            self.setMinimumWidths(maximumWidths)

        if fixedWidths is not None:
            self.setFixedWidths(fixedWidths)

        if sizeAdjustPolicy is not None:
            self.pulldownList.setSizeAdjustPolicy(sizeAdjustPolicy)

    def getText(self):
        """Convenience: Return selected text in Pulldown"""
        return self.pulldownList.currentText()

    def getIndex(self):
        """Convenience: Return selected text in Pulldown"""
        return self.pulldownList.getSelectedIndex()

    def select(self, item, blockSignals=False):
        """Convenience: Set item in Pulldown; works with text or item"""

        if blockSignals:
            with self.blockWidgetSignals(recursive=False, additionalWidgets=[self.pulldownList,]):
                self.pulldownList.select(item)
        else:
            self.pulldownList.select(item)

        # if blockSignals:
        #     self.pulldownList.blockSignals(True)
        # self.pulldownList.select(item)
        # if blockSignals:
        #     self.pulldownList.blockSignals(False)

    def setIndex(self, index, blockSignals=False):
        """Convenience: set item in Pulldown by index"""

        if blockSignals:
            with self.blockWidgetSignals():
                self.pulldownList.setIndex(index)
        else:
            self.pulldownList.setIndex(index)

        # if blockSignals:
        #     self.pulldownList.blockSignals(True)
        # self.pulldownList.setIndex(index)
        # if blockSignals:
        #     self.pulldownList.blockSignals(False)

    def modifyTexts(self, texts):
        """Modify the pulldown texts, retaining the current selection"""
        current = self.getText()

        self.pulldownList.blockSignals(True)
        self.pulldownList.clear()
        self.pulldownList.setData(texts=texts)
        self.select(current, blockSignals=True)
        self.pulldownList.blockSignals(False)
        self.pulldownList.repaint()

    def getTexts(self):
        return tuple(self.pulldownList.itemText(ii) for ii in range(self.pulldownList.count()))

    def setCallback(self, callback):
        """Set the callback for the doubleSpinBox
        """
        self.pulldownList.setCallback(callback)

    def setLabelText(self, value):
        """Set the text for the label
        """
        self.label.setText(value)


class CheckBoxCompoundWidget(CompoundBaseWidget):
    """
    Compound class comprising a Label and a CheckBox, combined in a CompoundBaseWidget (i.e. a Frame)

      orientation       widget layout
      ------------      ------------------------
      left:             Label       CheckBox

      right:            CheckBox    Label

      top:              Label
                        CheckBox

      bottom:           CheckBox
                        Label

    """
    layoutDict = dict(
            # grid positions for label and checkBox for the different orientations
            left=[(0, 0), (0, 1)],
            right=[(0, 1), (0, 0)],
            top=[(0, 0), (1, 0)],
            bottom=[(1, 0), (0, 0)],
            )

    def __init__(self, parent=None, mainWindow=None,
                 showBorder=False, orientation='left',
                 minimumWidths=None, maximumWidths=None, fixedWidths=None,
                 labelText='', text='', callback=None, checked=False,
                 editable=True, compoundKwds=None,
                 **kwds):
        """
        :param parent: parent widget
        :param showBorder: flag to display the border of Frame (True, False)
        :param orientation: flag to determine the orientation of the labelText relative to the CheckBox widget.
                            Allowed values: 'left', 'right', 'top', 'bottom'
        :param minimumWidths: tuple of two values specifying the minimum width of the Label and CheckBox widget, respectively
        :param maximumWidths: tuple of two values specifying the maximum width of the Label and CheckBox widget, respectively
        :param labelText: Text for the Label
        :param text: (optional) text for the Checkbox
        :param callback: (optional) callback for the CheckBox
        :param checked: (optional) initial state of the CheckBox
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
        """

        CompoundBaseWidget.__init__(self, parent=parent, layoutDict=self.layoutDict, orientation=orientation,
                                    showBorder=showBorder, **kwds)

        self.label = Label(parent=self, text=labelText, vAlign='center')
        self._addWidget(self.label)

        hAlign = orientation if (orientation == 'left' or orientation == 'right') else 'center'
        checkboxKwds = {'checked'  : checked,
                        'text'     : text,
                        'hAlign'   : hAlign,
                        'checkable': editable,
                        'callback' : callback,
                        }
        checkboxKwds.update(compoundKwds or {})
        self.checkBox = CheckBox(parent=self, **checkboxKwds)
        self.checkBox.setObjectName(labelText)
        self.setObjectName(labelText)
        self._addWidget(self.checkBox)

        if minimumWidths is not None:
            self.setMinimumWidths(minimumWidths)

        if maximumWidths is not None:
            self.setMaximumWidths(maximumWidths)

        if fixedWidths is not None:
            self.setFixedWidths(fixedWidths)

    def isChecked(self):
        """Convenience: Return whether checkBox is checked"""
        return self.checkBox.isChecked()

    def get(self):
        return self.checkBox.isChecked()

    def set(self, checked):
        self.checkBox.setChecked(checked)


class SpinBoxCompoundWidget(CompoundBaseWidget):
    """
    Compound class comprising a Label and an integer SpinBox, combined in a CompoundBaseWidget (i.e. a Frame)

      orientation       widget layout
      ------------      ------------------------
      left:             Label           SpinBox

      right:            SpinBox         Label

      top:              Label
                        SpinBox

      bottom:           SpinBox
                        Label

    """
    layoutDict = dict(
            # grid positions for label and checkBox for the different orientations
            left=[(0, 0), (0, 1)],
            right=[(0, 1), (0, 0)],
            top=[(0, 0), (1, 0)],
            bottom=[(1, 0), (0, 0)],
            )

    def __init__(self, parent=None, mainWindow=None,
                 showBorder=False, orientation='left',
                 minimumWidths=None, maximumWidths=None, fixedWidths=None,
                 labelText='', value=None, range=(None, None), step=None, showButtons=True,
                 decimals=None, callback=None, editable=False, compoundKwds=None,
                 **kwds):
        """
        :param parent: parent widget
        :param showBorder: flag to display the border of Frame (True, False)
        :param orientation: flag to determine the orientation of the labelText relative to the SpinBox widget.
                            Allowed values: 'left', 'right', 'top', 'bottom'
        :param minimumWidths: tuple of two values specifying the minimum width of the Label and SpinBox widget, respectively
        :param maximumWidths: tuple of two values specifying the maximum width of the Label and SpinBox widget, respectively
        :param labelText: Text for the Label
        :param value: initial value for the SpinBox
        :param range: (minimumValue, maximumValue) tuple for the SpinBox
        :param step: initial step for the increment of the SpinBox buttons
        :param showButtons: flag to display the SpinBox buttons (True, False)
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
        """

        CompoundBaseWidget.__init__(self, parent=parent, layoutDict=self.layoutDict, orientation=orientation,
                                    showBorder=showBorder, **kwds)

        self.label = Label(parent=self, text=labelText, vAlign='center')
        self._addWidget(self.label)

        hAlign = orientation if (orientation == 'left' or orientation == 'right') else 'center'
        minimumValue = range[0] if range[0] is not None else None
        maximumValue = range[1] if range[1] is not None else None
        spinboxKwds = {'value'      : value,
                       'min'        : minimumValue,
                       'max'        : maximumValue,
                       'step'       : step,
                       'showButtons': showButtons,
                       'hAlign'     : hAlign,
                       'editable'   : editable,
                       'callback'   : callback,
                       }
        spinboxKwds.update(compoundKwds or {})
        self.spinBox = Spinbox(parent=self, **spinboxKwds)
        self._addWidget(self.spinBox)
        self.spinBox.setObjectName(labelText)

        if minimumWidths is not None:
            self.setMinimumWidths(minimumWidths)

        if maximumWidths is not None:
            self.setMinimumWidths(maximumWidths)

        if fixedWidths is not None:
            self.setFixedWidths(fixedWidths)

    def getValue(self) -> float:
        """get the value from the SpinBox"""
        return self.spinBox.value()

    def setValue(self, value: float):
        """set the value in the SpinBox"""
        return self.spinBox.setValue(value if value is not None else 0)

    def setCallback(self, callback):
        """Set the callback for the spinBox
        """
        self.spinBox.setCallback(callback)


class DoubleSpinBoxCompoundWidget(CompoundBaseWidget):
    """
    Compound class comprising a Label and a DoubleSpinBox, combined in a CompoundBaseWidget (i.e. a Frame)

      orientation       widget layout
      ------------      ----------------------------
      left:             Label          DoubleSpinBox

      right:            DoubleSpinBox  Label

      top:              Label
                        DoubleSpinBox

      bottom:           DoubleSpinBox
                        Label

    """
    layoutDict = dict(
            # grid positions for label and checkBox for the different orientations
            left=[(0, 0), (0, 1)],
            right=[(0, 1), (0, 0)],
            top=[(0, 0), (1, 0)],
            bottom=[(1, 0), (0, 0)],
            )

    def __init__(self, parent=None, mainWindow=None,
                 showBorder=False, orientation='left',
                 minimumWidths=None, maximumWidths=None, fixedWidths=None,
                 labelText='', value=None, range=(None, None), step=None, showButtons=True,
                 decimals=None, callback=None, editable=False, compoundKwds=None,
                 **kwds):
        """
        :param parent: parent widget
        :param showBorder: flag to display the border of Frame (True, False)
        :param orientation: flag to determine the orientation of the labelText relative to the DoubleSpinBox widget.
                            Allowed values: 'left', 'right', 'top', 'bottom'
        :param minimumWidths: tuple of two values specifying the minimum width of the Label and DoubleSpinBox widget, respectively
        :param maximumWidths: tuple of two values specifying the maximum width of the Label and DoubleSpinBox widget, respectively
        :param labelText: Text for the Label
        :param value: initial value for the DoubleSpinBox
        :param range: (minimumValue, maximumValue) tuple for the DoubleSpinBox
        :param step: initial step for the increment of the DoubleSpinBox buttons
        :param decimals: number of decimals the DoubleSpinBox to display
        :param showButtons: flag to display the DoubleSpinBox buttons (True, False)
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
        """

        CompoundBaseWidget.__init__(self, parent=parent, layoutDict=self.layoutDict, orientation=orientation,
                                    showBorder=showBorder, **kwds)

        self.label = Label(parent=self, text=labelText, vAlign='center')
        self._addWidget(self.label)

        hAlign = orientation if (orientation == 'left' or orientation == 'right') else 'center'
        minimumValue = range[0] if range[0] is not None else None
        maximumValue = range[1] if range[1] is not None else None
        spinboxKwds = {'value'      : value,
                       'min'        : minimumValue,
                       'max'        : maximumValue,
                       'step'       : step,
                       'showButtons': showButtons,
                       'decimals'   : decimals,
                       'hAlign'     : hAlign,
                       'editable'   : editable,
                       'callback'   : callback,
                       }
        spinboxKwds.update(compoundKwds or {})
        self.doubleSpinBox = DoubleSpinbox(parent=self, **spinboxKwds)
        self._addWidget(self.doubleSpinBox)
        self.doubleSpinBox.setObjectName(labelText)

        if minimumWidths is not None:
            self.setMinimumWidths(minimumWidths)

        if maximumWidths is not None:
            self.setMinimumWidths(maximumWidths)

        if fixedWidths is not None:
            self.setFixedWidths(fixedWidths)

    def getValue(self) -> float:
        """get the value from the DoubleSpinBox"""
        return self.doubleSpinBox.value()

    def setValue(self, value: float):
        """set the value in the DoubleSpinBox"""
        return self.doubleSpinBox.setValue(value if value is not None else 0)

    def setCallback(self, callback):
        """Set the callback for the doubleSpinBox
        """
        self.doubleSpinBox.setCallback(callback)


class ScientificSpinBoxCompoundWidget(CompoundBaseWidget):
    """
    Compound class comprising a Label and a scientificSpinBox, combined in a CompoundBaseWidget (i.e. a Frame)

      orientation       widget layout
      ------------      -------------------------------------
      left:             Label               ScientificSpinBox

      right:            ScientificSpinBox   Label

      top:              Label
                        ScientificSpinBox

      bottom:           ScientificSpinBox
                        Label

    """
    layoutDict = dict(
            # grid positions for label and checkBox for the different orientations
            left=[(0, 0), (0, 1)],
            right=[(0, 1), (0, 0)],
            top=[(0, 0), (1, 0)],
            bottom=[(1, 0), (0, 0)],
            )

    def __init__(self, parent=None, mainWindow=None,
                 showBorder=False, orientation='left',
                 minimumWidths=None, maximumWidths=None, fixedWidths=None,
                 labelText='', value=None, range=(None, None), step=None, showButtons=True,
                 decimals=None, callback=None, editable=False, compoundKwds=None,
                 **kwds):
        """
        :param parent: parent widget
        :param showBorder: flag to display the border of Frame (True, False)
        :param orientation: flag to determine the orientation of the labelText relative to the scientificSpinBox widget.
                            Allowed values: 'left', 'right', 'top', 'bottom'
        :param minimumWidths: tuple of two values specifying the minimum width of the Label and scientificSpinBox widget, respectively
        :param maximumWidths: tuple of two values specifying the maximum width of the Label and scientificSpinBox widget, respectively
        :param labelText: Text for the Label
        :param value: initial value for the scientificSpinBox
        :param range: (minimumValue, maximumValue) tuple for the scientificSpinBox
        :param step: initial step for the increment of the scientificSpinBox buttons
        :param decimals: number of decimals the scientificSpinBox to display
        :param showButtons: flag to display the scientificSpinBox buttons (True, False)
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
        """

        CompoundBaseWidget.__init__(self, parent=parent, layoutDict=self.layoutDict, orientation=orientation,
                                    showBorder=showBorder, **kwds)

        self.label = Label(parent=self, text=labelText, vAlign='center')
        self._addWidget(self.label)

        hAlign = orientation if (orientation == 'left' or orientation == 'right') else 'center'
        minimumValue = range[0] if range[0] is not None else None
        maximumValue = range[1] if range[1] is not None else None
        scientificKwds = {'value'      : value,
                          'min'        : minimumValue,
                          'max'        : maximumValue,
                          'showButtons': showButtons,
                          'hAlign'     : hAlign,
                          'editable'   : editable,
                          'callback'   : callback,
                          }
        scientificKwds.update(compoundKwds or {})
        self.scientificSpinBox = ScientificDoubleSpinBox(parent=self, **scientificKwds)
        self._addWidget(self.scientificSpinBox)
        self.scientificSpinBox.setObjectName(labelText)

        if minimumWidths is not None:
            self.setMinimumWidths(minimumWidths)

        if maximumWidths is not None:
            self.setMinimumWidths(maximumWidths)

        if fixedWidths is not None:
            self.setFixedWidths(fixedWidths)

    def getValue(self) -> float:
        """get the value from the scientificSpinBox"""
        return self.scientificSpinBox.value()

    def setValue(self, value: float):
        """set the value in the scientificSpinBox"""
        return self.scientificSpinBox.setValue(value if value is not None else 0.0)

    def setCallback(self, callback):
        """Set the callback for the scientificSpinBox
        """
        self.scientificSpinBox.setCallback(callback)


class SelectorWidget(Widget):

    def __init__(self, parent=None, label='', data=None, callback=None, **kwds):
        super().__init__(parent, **kwds)

        if data:
            data.insert(0, '')
        label1 = Label(self, text=label, grid=(0, 0))
        self.pulldownList = InputPulldown(self, grid=(0, 1), texts=data, callback=callback)
        self.pulldownList.setObjectName(label)

    def getText(self):
        """Convenience: Return selected text in Pulldown"""
        return self.pulldownList.currentText()

    def select(self, item):
        """Convenience: Set item in Pulldown; works with text or item"""
        return self.pulldownList.select(item)


class InputPulldown(PulldownList):

    def __init__(self, parent=None, callback=None, **kwds):
        PulldownList.__init__(self, parent, **kwds)

        self.setData(['', '<New Item>'])
        if callback:
            self.setCallback(callback)
        else:
            self.setCallback(self.addNewItem)

    def addNewItem(self, item):
        if item == '<New Item>':
            newItemText = LineEditPopup()
            newItemText.exec_()
            newItem = newItemText.inputField.text()
            texts = self.texts
            texts.insert(-2, newItem)
            if '' in texts:
                texts.remove('')
            self.setData(list(set(texts)))
            self.select(newItem)
            return newItem


class LineEditPopup(QtWidgets.QDialog, Base):

    def __init__(self, parent=None, dataType=None, **kwds):
        super().__init__(parent)
        Base._init(self, **kwds)

        inputLabel = Label(self, 'Input', grid=(0, 0))
        self.inputField = LineEdit(self, grid=(0, 1))

        ButtonList(self, grid=(1, 1), callbacks=[self.reject, self.returnItem], texts=['Cancel', 'OK'])

        if dataType:
            inputLabel.setText('New %s name' % dataType)

    def returnItem(self):
        self.accept()

    def get(self):
        return self.inputField.text()

    def set(self, text=''):
        #text = translator.translate(text)
        self.inputField.setText(text)


class ColourSelectionWidget(Widget):

    def __init__(self, parent=None, labelName=None, **kwds):
        super().__init__(parent, **kwds)

        Label(self, labelName, grid=(0, 0))
        self.pulldownList = PulldownList(self, vAlign='t', hAlign='l', grid=(0, 1))
        for item in spectrumColours.items():
            pix = QtGui.QPixmap(QtCore.QSize(20, 20))
            pix.fill(QtGui.QColor(item[0]))
            self.pulldownList.addItem(icon=QtGui.QIcon(pix), text=item[1])
        Button(self, vAlign='t', hAlign='l', grid=(0, 2), hPolicy='fixed',
               callback=partial(self._setColour), icon='icons/colours')

    def _setColour(self):
        dialog = ColourDialog()
        newColour = dialog.getColor()
        pix = QtGui.QPixmap(QtCore.QSize(20, 20))
        pix.fill(QtGui.QColor(newColour))
        newIndex = str(len(spectrumColours.items()) + 1)
        self.pulldownList.addItem(icon=QtGui.QIcon(pix), text='Colour %s' % newIndex)
        spectrumColours[newColour.name()] = 'Colour %s' % newIndex
        self.pulldownList.setCurrentIndex(int(newIndex) - 1)

    def colour(self):
        return list(spectrumColours.keys())[self.pulldownList.currentIndex()]

    def currentText(self):
        self.pulldownList.currentText()

    def setColour(self, value):
        self.pulldownList.select(spectrumColours[value])


class RadioButtonsCompoundWidget(CompoundBaseWidget):
    """
    Compound class comprising a Label and a RadioButtons box, combined in a CompoundBaseWidget (i.e. a Frame)

      orientation       widget layout
      ------------      ----------------------------
      left:             Label           RadioButtons

      right:            RadioButtons    Label

      top:              Label
                        RadioButtons

      bottom:           RadioButtons
                        Label

    """
    layoutDict = dict(
            # grid positions for label and checkBox for the different orientations
            left=[(0, 0), (0, 1)],
            right=[(0, 1), (0, 0)],
            top=[(0, 0), (1, 0)],
            bottom=[(1, 0), (0, 0)],
            )

    def __init__(self, parent=None, mainWindow=None,
                 showBorder=False, orientation='left',
                 minimumWidths=None, maximumWidths=None, fixedWidths=None,
                 labelText='', texts=[], callback=None, selectedInd=0,
                 editable=True, compoundKwds=None,
                 **kwds):
        """
        :param parent: parent widget
        :param showBorder: flag to display the border of Frame (True, False)
        :param orientation: flag to determine the orientation of the labelText relative to the RadioButtons widget.
                            Allowed values: 'left', 'right', 'top', 'bottom'
        :param minimumWidths: tuple of two values specifying the minimum width of the Label and RadioButtons widget, respectively
        :param maximumWidths: tuple of two values specifying the maximum width of the Label and RadioButtons widget, respectively
        :param labelText: Text for the Label
        :param text: (optional) text for the RadioButtons
        :param callback: (optional) callback for the RadioButtons
        :param checked: (optional) initial state of the RadioButtons
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
        """

        CompoundBaseWidget.__init__(self, parent=parent, layoutDict=self.layoutDict, orientation=orientation,
                                    showBorder=showBorder, **kwds)

        self.label = Label(parent=self, text=labelText, vAlign='center')
        self._addWidget(self.label)

        hAlign = orientation if (orientation == 'left' or orientation == 'right') else 'center'
        self.radioButtons = RadioButtons(parent=self, callback=callback, **compoundKwds)
        self.radioButtons.setObjectName(labelText)
        self.setObjectName(labelText)
        self._addWidget(self.radioButtons)

        if minimumWidths is not None:
            self.setMinimumWidths(minimumWidths)

        if maximumWidths is not None:
            self.setMaximumWidths(maximumWidths)

        if fixedWidths is not None:
            self.setFixedWidths(fixedWidths)

    # def get(self):
    #     """Convenience: get the radioButtons text
    #     """
    #     return self.radioButtons.get()

    def getIndex(self):
        """Convenience: get the radioButtons index
        """
        return self.radioButtons.getIndex()

    def setIndex(self, index):
        """Convenience: set the radioButtons index
        """
        self.radioButtons.setIndex(index if index else 0)

    def getByText(self, *args):
        """Convenience: get the radioButtons selected text
        """
        return self.radioButtons.get()

    def setByText(self, value, *args):
        """Convenience: set the radioButtons selected text
        """
        self.radioButtons.set(value)


class CompoundViewCompoundWidget(CompoundBaseWidget):
    """
    Compound class comprising a Label and an compoundView, combined in a CompoundBaseWidget (i.e. a Frame)

      orientation       widget layout
      ------------      ----------------------------
      left:             Label           compoundView

      right:            compoundView    Label

      top:              Label
                        compoundView

      bottom:           compoundView
                        Label

    """
    layoutDict = dict(
            # grid positions for label and checkBox for the different orientations
            left=[(0, 0), (0, 1)],
            right=[(0, 1), (0, 0)],
            top=[(0, 0), (1, 0)],
            bottom=[(1, 0), (0, 0)],
            )

    def __init__(self, parent=None, mainWindow=None,
                 showBorder=False, orientation='left',
                 minimumWidths=None, maximumWidths=None, fixedWidths=None,
                 labelText='',
                 callback=None, editable=False, compoundKwds=None,
                 **kwds):
        """
        :param parent: parent widget
        :param showBorder: flag to display the border of Frame (True, False)
        :param orientation: flag to determine the orientation of the labelText relative to the RadioButtons widget.
                            Allowed values: 'left', 'right', 'top', 'bottom'
        :param minimumWidths: tuple of two values specifying the minimum width of the Label and RadioButtons widget, respectively
        :param maximumWidths: tuple of two values specifying the maximum width of the Label and RadioButtons widget, respectively
        :param labelText: Text for the Label
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
        """
        CompoundBaseWidget.__init__(self, parent=parent, layoutDict=self.layoutDict, orientation=orientation,
                                    showBorder=showBorder, **kwds)

        self.label = Label(parent=self, text=labelText, vAlign='center')
        self._addWidget(self.label)

        hAlign = orientation if (orientation == 'left' or orientation == 'right') else 'center'
        viewKwds = {'hAlign': hAlign,
                    'smiles': '',
                    }
        viewKwds.update(compoundKwds or {})
        self.compoundView = CompoundView(parent=self, **viewKwds)
        self.compoundView.resize(200, 250)
        self._initSize = None

        self._addWidget(self.compoundView)
        self.setObjectName(labelText)

        if minimumWidths is not None:
            self.setMinimumWidths(minimumWidths)

        if maximumWidths is not None:
            self.setMinimumWidths(maximumWidths)

        if fixedWidths is not None:
            self.setFixedWidths(fixedWidths)

    def minimumSizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(200, 250)

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        super().resizeEvent(a0)
        if self._initSize is None:
            view = self.compoundView
            view.updateAll()
            view.scene.setSceneRect(view.scene.itemsBoundingRect())
            view.resetView()
            view.zoomLevel = 1.0
            self._initSize = True


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.BasePopup import BasePopup
    from ccpn.ui.gui.popups.Dialog import CcpnDialog


    app = TestApplication()


    def callback1(obj):
        print('callback1', obj)


    def callback2():
        print('callback2')


    popup = CcpnDialog(windowTitle='Test widget', setLayout=True)

    # policyDict = dict(
    #   vAlign='top',
    #   hPolicy='expanding',
    # )
    policyDict = dict(
            vAlign='top',
            # hAlign='left',
            )
    # policyDict = dict(
    #   hAlign='left',
    # )
    # policyDict = {}

    row = -1

    row += 1
    checkBox1 = CheckBoxCompoundWidget(parent=popup, orientation='left', showBorder=True,
                                       minimumWidths=(150, 100),
                                       labelText='CheckboxCompoundWidget', text="test2",
                                       callback=callback2, grid=(row, 0), checked=True,
                                       **policyDict)

    row += 1
    texts = 'aap noot mies kees'.split()
    pulldownListwidget = PulldownListCompoundWidget(parent=popup, orientation='left', showBorder=True,
                                                    minimumWidths=(150, 100),
                                                    labelText='PulldownListCompoundWidget', texts=texts,
                                                    callback=callback1, grid=(row, 0), default=None,
                                                    **policyDict)

    pulldownListwidget2 = PulldownListCompoundWidget(parent=popup, orientation='top', showBorder=True,
                                                     maximumWidths=(10, 10),
                                                     labelText='test-label on top which is longer', texts=texts,
                                                     callback=callback1, grid=(row, 1), default='kees',
                                                     **policyDict)

    row += 1
    listWidget = ListCompoundWidget(parent=popup, orientation='left', showBorder=True,
                                    labelText='ListCompoundWidget', texts=texts,
                                    callback=callback2, grid=(row, 0), defaults=texts[1:2],
                                    **policyDict)
    listWidget.addPulldownItem(0)
    listWidget2 = ListCompoundWidget(parent=popup, orientation='top', showBorder=True,
                                     labelText='ListCompoundWidget-hidden pulldown', texts=texts,
                                     callback=callback2, grid=(row, 1), defaults=[0, 2],
                                     **policyDict)
    listWidget2.showPulldownList(False)

    row += 1
    doubleSpinBox = DoubleSpinBoxCompoundWidget(parent=popup, labelText='doubleSpinBox: range (-3,10)', grid=(row, 0),
                                                callback=callback1, range=(-3, 10)
                                                )

    row += 1
    doubleSpinBox2 = DoubleSpinBoxCompoundWidget(parent=popup, labelText='doubleSpinBox no buttons', grid=(row, 0),
                                                 showButtons=False, callback=callback1
                                                 )
    #doubleSpinBox2.set(10.3)

    # row += 1
    # selectorWidget = SelectorWidget(parent=popup, label='selectorWidget', grid=(row,0))

    row += 1
    entry = EntryCompoundWidget(parent=popup, labelText="Entry widget", default='test', callback=callback1,
                                grid=(row, 0))

    popup.show()
    popup.raise_()
    app.start()
