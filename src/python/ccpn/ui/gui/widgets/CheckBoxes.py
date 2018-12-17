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
__dateModified__ = "$dateModified: 2017-07-07 16:32:55 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
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
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Widget import Widget


CHECKED = QtCore.Qt.Checked
UNCHECKED = QtCore.Qt.Unchecked


class CheckBoxes(Widget):

    def __init__(self, parent, texts=None, selectedInd=None, exclusive=False,
                 callback=None, direction='h', tipTexts=None, **kwds):

        super().__init__(parent, setLayout=True, **kwds)

        if texts is None:
            texts = []

        self.texts = texts
        direction = direction.lower()
        checkBoxGroup = self.checkBoxGroup = QtWidgets.QButtonGroup(self)
        self.isExclusive = exclusive
        checkBoxGroup.setExclusive(self.isExclusive)

        if not tipTexts:
            tipTexts = [None] * len(texts)

        self.checkBoxes = []
        self.setCheckBoxes(texts, selectedInd, direction, tipTexts)

        checkBoxGroup.buttonClicked.connect(self._callback)

        self.setCallback(callback)

    def setCheckBoxes(self, texts=None, selectedInd=None, direction='h', tipTexts=None):
        """Change the checkBoxes in the checkBox group
        """
        # clear the original checkBoxs
        selected = self.getSelectedText()

        for btn in self.checkBoxes:
            self.checkBoxGroup.removeButton(btn)
            btn.deleteLater()
        self.checkBoxes = []

        # exit if there are none to define
        if not texts:
            return

        # rebuild the checkBox list
        for i, text in enumerate(texts):
            if 'h' in direction:
                grid = (0, i)
            else:
                grid = (i, 0)
            checkBox = CheckBox(self, text=text, tipText=tipTexts[i], grid=grid, hAlign='r')
            self.checkBoxes.append(checkBox)

            self.checkBoxGroup.addButton(checkBox)
            self.checkBoxGroup.setId(checkBox, i)

        self.texts = texts
        if selectedInd is not None:
            if selectedInd < len(self.checkBoxes):
                self.checkBoxes[selectedInd].setChecked(True)
        elif selected and selected in self.texts:
            self.set(selected)
        elif self.checkBoxes:
            self.checkBoxes[0].setChecked(True)

    def getCheckBox(self, text):
        for rb in self.checkBoxes:
            if rb.text() == text:
                return rb

    def get(self):

        return self.texts[self.getIndex()]

    def getIndex(self):

        return self.checkBoxes.index(self.checkBoxGroup.checkedCheckBox())

    @property
    def isChecked(self):

        return self.checkBoxGroup.checkedCheckBox() is not None

    def set(self, text):

        i = self.texts.index(text)
        self.setIndex(i)

    def getSelectedIndexes(self):

        return [ii for ii, checkBox in enumerate(self.checkBoxes) if checkBox.isChecked()]

    def getSelectedText(self):

        return [checkBox.text() for checkBox in self.checkBoxes if checkBox.isChecked()]

        # for checkBox in self.checkBoxes:
        #     if checkBox.isChecked():
        #         name = checkBox.text()
        #         if name:
        #             return name

    def setIndex(self, i):

        if len(self.checkBoxes) > i:
            self.checkBoxes[i].setChecked(True)

    def clearIndex(self, i):

        if len(self.checkBoxes) > i:
            self.checkBoxes[i].setChecked(False)

    def deselectAll(self):

        self.checkBoxGroup.setExclusive(False)
        for i in self.checkBoxes:
            i.setChecked(False)
        self.checkBoxGroup.setExclusive(self.isExclusive)

    def selectAll(self):

        self.checkBoxGroup.setExclusive(False)
        for i in self.checkBoxes:
            i.setChecked(True)
        self.checkBoxGroup.setExclusive(self.isExclusive)

    def setChecked(self, value):

        self.checkBoxGroup.setExclusive(False)
        for i in self.checkBoxes:
            i.setChecked(value)
        self.checkBoxGroup.setExclusive(self.isExclusive)

    def setCallback(self, callback):

        self.callback = callback

    def _callback(self, checkBox):

        if self.callback and checkBox:
            # checkBox = self.checkBoxGroup.checkBoxs[ind]
            self.callback()

    def setSelectedByText(self, texts, checkFlag, presetAll=True):

        if presetAll:
            self.setChecked(not checkFlag)

        self.checkBoxGroup.setExclusive(False)
        for checkBox in self.checkBoxes:
            if checkBox.text() in texts:
                checkBox.setChecked(checkFlag)
        self.checkBoxGroup.setExclusive(self.isExclusive)

if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.BasePopup import BasePopup

    from ccpn.ui.gui.popups.Dialog import CcpnDialog


    def testCallback():
        print('TEST')


    app = TestApplication()
    popup = CcpnDialog(windowTitle='Test checkBoxes', setLayout=True)

    checkBoxGroup = QtWidgets.QButtonGroup(popup)
    # checkBoxes = CheckBoxes(parent=popup,
    #              callback=testCallback, grid=(0, 0))
    for i in range(10):
        checkBox = CheckBox(popup, text='TEST', grid=(i, 0),
                            callback=None)  # partial(self.assignSelect
        checkBoxGroup.addCheckBox(checkBox)

    popup.raise_()
    popup.exec()

    app.start()
