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
__dateModified__ = "$dateModified: 2020-11-02 18:41:24 +0000 (Mon, November 02, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.RadioButton import RadioButton, EditableRadioButton
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Font import setWidgetFont
from functools import partial
from ccpn.ui.gui.widgets.Widget import Widget

CHECKED = QtCore.Qt.Checked
UNCHECKED = QtCore.Qt.Unchecked


class RadioButtons(QtWidgets.QWidget, Base):

    def __init__(self, parent, texts=None, selectedInd=None, exclusive=True,
                 callback=None, direction='h', tipTexts=None, objectNames=None,
                 icons=None, initButtons=True,
                 **kwds):

        super().__init__(parent)
        Base._init(self, setLayout=True, **kwds)

        if texts is None:
            texts = []

        self.texts = texts
        direction = direction.lower()
        buttonGroup = self.buttonGroup = QtWidgets.QButtonGroup(self)
        self.isExclusive = exclusive
        buttonGroup.setExclusive(self.isExclusive)

        if not tipTexts:
            tipTexts = [None] * len(texts)
        if not objectNames:
            objectNames = [None] * len(texts)

        # added functionality for icons
        # icons is a list of str/tuple
        #
        #   e.g. icons = ('icons/strip-row', 'strip-column')
        #       icons = ( ('icons/strip-row', (24,24)),
        #                 ('strip-column', (24,24))
        #               )
        #       where (24,24) is the size of the bounding box containing the icon

        if not icons:
            icons = [None] * len(texts)

        self.radioButtons = []
        if initButtons:
            self.setButtons(texts, selectedInd, direction, tipTexts, objectNames, icons=icons)

        # for i, text in enumerate(texts):
        #   if 'h' in direction:
        #     grid = (0, i)
        #   else:
        #     grid = (i, 0)
        #   button = RadioButton(self, text, tipText=tipTexts[i], grid=grid, hAlign='l')
        #   self.radioButtons.append(button)
        #
        #   buttonGroup.addButton(button)
        #   buttonGroup.setId(button, i)
        #
        # if selectedInd is not None:
        #   self.radioButtons[selectedInd].setChecked(True)

        # buttonGroup.connect(buttonGroup, QtCore.SIGNAL('buttonClicked(int)'), self._callback)
        buttonGroup.buttonClicked.connect(self._callback)
        self.setCallback(callback)


    def setButtons(self, texts=None, selectedInd=None, direction='h', tipTexts=None, objectNames=None, silent=False,
                   icons=None):
        """Change the buttons in the button group
        """
        # clear the original buttons
        selected = self.getSelectedText()

        for btn in self.radioButtons:
            self.buttonGroup.removeButton(btn)
            btn.deleteLater()
        self.radioButtons = []

        # rebuild the button list
        for i, text in enumerate(texts):
            if 'h' in direction:
                grid = (0, i)
            else:
                grid = (i, 0)
            button = RadioButton(self, text, tipText=tipTexts[i], grid=grid, hAlign='l')
            self.radioButtons.append(button)

            self.buttonGroup.addButton(button)
            self.buttonGroup.setId(button, i)
            if objectNames and objectNames[i]:
                button.setObjectName(objectNames[i])

            # set icons if required - these will automatically go to the left of the text
            if icons and icons[i]:
                thisIcon = icons[i]

                if isinstance(thisIcon, str):
                    # icon list item only contains a name
                    button.setIcon(Icon(thisIcon))

                elif isinstance(thisIcon, (list, tuple)):

                    # icon item contains a list/tuple
                    if thisIcon and isinstance(thisIcon[0], str):
                        #first item is a string name
                        button.setIcon(Icon(thisIcon[0]))

                        # second value must be tuple of integer, length == 2
                        if len(thisIcon) == 2:
                            iconSize = thisIcon[1]

                            if isinstance(iconSize, (list, tuple)) and len(iconSize) == 2 and \
                                    all(isinstance(iconVal, int) for iconVal in iconSize):
                                # set the iconSize
                                button.setIconSize(QtCore.QSize(*iconSize))

        self.texts = texts
        if selectedInd is not None:
            self.radioButtons[selectedInd].setChecked(True)
        elif selected and selected in self.texts:
            self.set(selected, silent=silent)
        else:
            self.radioButtons[0].setChecked(True)

    def getRadioButton(self, text):
        for rb in self.radioButtons:
            if rb.text() == text:
                return rb
        else:
            raise ValueError('radioButton %s not found in the list' % text)

    def get(self):
        texts = []
        for i in self.radioButtons:
            if i.isChecked():
                texts.append(i.text())
        if self.isExclusive:
            return texts[-1]
        else:
            return texts


    def getIndex(self):
        ixs = []
        for i, rb in enumerate(self.radioButtons):
            if rb.isChecked():
                ixs.append(i)
        if self.isExclusive:
            # if exclusive then one-and-only-one MUST be set
            return ixs[-1] if ixs else 0
        else:
            return ixs

    @property
    def isChecked(self):

        return self.buttonGroup.checkedButton() is not None

    def set(self, text, silent=False):
        if text in self.texts:
            i = self.texts.index(text)
            self.setIndex(i)
            if self.callback and not silent:
                self.callback()
        else:
            self.deselectAll()

    def getSelectedText(self):
        for radioButton in self.radioButtons:
            if radioButton.isChecked():
                name = radioButton.text()
                if name:
                    return name

    def setIndex(self, i):
        self.radioButtons[i].setChecked(True)

    def deselectAll(self):
        self.buttonGroup.setExclusive(False)
        for i in self.radioButtons:
            i.setChecked(False)
        self.buttonGroup.setExclusive(self.isExclusive)

    def setCallback(self, callback):

        self.callback = callback

    def _callback(self, button):

        if self.callback and button:
            # button = self.buttonGroup.buttons[ind]
            # FIXME the callback should also pass in the selected value. like pulldown checkbox etc...
            #  e.g. self.callback(self.get())
            self.callback()

def _fillMissingValuesInSecondList(aa, bb, value):
    if not value:
        value = ''
    if bb is None:
        bb = [value] * len(aa)
    if len(aa) != len(bb):
        if len(aa) > len(bb):
            m = len(aa) - len(bb)
            bb += [value] * m
        else:
            raise NameError('Lists are not of same length.')
    return aa, bb

class EditableRadioButtons(Widget, Base):
    """
    Re-implementation of RadioButtons with the option to edit a selection
    """

    def __init__(self, parent, texts=None, backgroundTexts=None, editables=None, selectedInd=None,
                 callback=None, direction='h', tipTexts=None, objectNames=None, icons=None, exclusive=True,
                 **kwds):
        super().__init__(parent, setLayout=True, **kwds)

        if texts is None:
            texts = []

        self.texts = texts
        direction = direction.lower()
        self.direction = direction
        self.isExclusive = exclusive

        texts, editables = _fillMissingValuesInSecondList(texts, editables, value=False)
        texts, tipTexts = _fillMissingValuesInSecondList(texts, tipTexts, value='')
        texts, backgroundTexts = _fillMissingValuesInSecondList(texts, backgroundTexts, value='')
        texts, icons = _fillMissingValuesInSecondList(texts, icons, value=None)

        self.radioButtons = []
        self.callback = callback

        self._setButtons(texts=texts, editables=editables, selectedInd=selectedInd, direction=direction,
                        tipTexts=tipTexts, backgroundTexts=backgroundTexts, objectNames=objectNames, icons=icons,)

    def setButtons(self,  *args, **kwargs):
        self._setButtons(*args, **kwargs)

    def _setButtons(self, texts=None, editables=None, selectedInd=None, direction='h', tipTexts=None,
                   objectNames=None, backgroundTexts=None, silent=False, icons=None):
        """Change the buttons in the button group """
        texts, editables = _fillMissingValuesInSecondList(texts, editables, value=False)
        texts, tipTexts = _fillMissingValuesInSecondList(texts, tipTexts, value='')
        texts, backgroundTexts = _fillMissingValuesInSecondList(texts, backgroundTexts, value='')
        selected = self.getSelectedText()
        for btn in self.radioButtons:
            btn.deleteLater()
        self.radioButtons = []
        # rebuild the button list
        for i, text in enumerate(texts):
            if 'h' in direction: grid = (0, i)
            else: grid = (i, 0)
            button = EditableRadioButton(self, text=text, editable=editables[i], tipText=tipTexts[i],
                                          backgroundText = backgroundTexts[i],
                                          callbackOneditingFinished=False) #callback=self.callback,
            button.lineEdit.editingFinished.connect(partial(self._editingFinishedCallback, button, i))
            button.radioButton.clicked.connect(partial(self._buttonClicked, button, i))
            self.radioButtons.append(button)
            layout = self.getLayout()
            layout.addWidget(button, *grid)
            if objectNames and objectNames[i]:
                button.setObjectName(objectNames[i])
            if icons and icons[i]:
                thisIcon = icons[i]
                if isinstance(thisIcon, str):
                    button.setIcon(Icon(thisIcon))
                elif isinstance(thisIcon, (list, tuple)):
                    if thisIcon and isinstance(thisIcon[0], str):
                        button.setIcon(Icon(thisIcon[0]))
                        if len(thisIcon) == 2:
                            iconSize = thisIcon[1]
                            if isinstance(iconSize, (list, tuple)) and len(iconSize) == 2 and \
                                    all(isinstance(iconVal, int) for iconVal in iconSize):
                                button.setIconSize(QtCore.QSize(*iconSize))
        self.texts = texts
        if selectedInd is not None:
            self.radioButtons[selectedInd].setChecked(True)
        elif selected and selected in self.texts:
            self.set(selected, silent=silent)
        else:
            self.radioButtons[0].setChecked(True)

    def getRadioButton(self, text):
        for rb in self.radioButtons:
            if rb.text() == text:
                return rb
        else:
            raise ValueError('radioButton %s not found in the list' % text)

    def get(self):
        texts = []
        for i in self.radioButtons:
            if i.isChecked():
                texts.append(i.text())
        if self.isExclusive:
            return texts[-1]
        else:
            return texts


    def getIndex(self):
        ixs = []
        for i, rb in enumerate(self.radioButtons):
            if rb.isChecked():
                ixs.append(i)
        if self.isExclusive:
            # if exclusive then one-and-only-one MUST be set
            return ixs[-1] if ixs else 0
        else:
            return ixs

    def set(self, text, silent=False):
        if self.isExclusive:
            self.deselectAll()
        if text in self.texts:
            i = self.texts.index(text)
            self.setIndex(i)
            if self.callback and not silent:
                self.callback()



    def setExclusive(self, value):
        # raise ValueError('Not implemented yet')
        self.isExclusive = value

    def getSelectedText(self):
        for radioButton in self.radioButtons:
            if radioButton.isChecked():
                name = radioButton.text()
                if name:
                    return name

    def setIndex(self, i):
        if self.isExclusive:
            self.deselectAll()
        self.radioButtons[i].setChecked(True)

    def _buttonClicked(self, button, index):
        if not self.isExclusive:
            self.radioButtons[index].setChecked(button.isChecked())
            self._callback(button)
        else:
            self.setIndex(index)
            self._callback(button)

    def deselectAll(self):
        for i in self.radioButtons:
            i.setChecked(False)

    def setCallback(self, callback):
        self.callback = callback

    def _callback(self, button):

        if self.callback and button:
            self.callback(self.get())

    def _editingFinishedCallback(self, button, index):
        if button:
            self._buttonClicked(button, index)


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.BasePopup import BasePopup

    from ccpn.ui.gui.popups.Dialog import CcpnDialog

    def testCallback(self, *args):
        print('GET:', self.get())
        print('INDEX',self.getIndex())
        print('SELECTED:', self.getSelectedText())

    def testCall(*args):
        print('ddd', args)
    app = TestApplication()
    popup = CcpnDialog(windowTitle='Test radioButtons', setLayout=True)

    buttonGroup = QtWidgets.QButtonGroup(popup)
    radioButtons = EditableRadioButtons(parent=popup, texts=['a', ''], tipTexts=['',''],
                                        editables=[False, True], grid=(0, 0),
                                        callback=testCall, direction='v')

    # radioButtons.setCallback(partial(testCallback, radioButtons))
    # for i in range(10):
    #     button = RadioButton(popup, text='TEST', grid=(i, 0),
    #                          callback=testCall)  # partial(self.assignSelect
    #     buttonGroup.addButton(button)

    popup.raise_()
    popup.exec()

    app.start()
