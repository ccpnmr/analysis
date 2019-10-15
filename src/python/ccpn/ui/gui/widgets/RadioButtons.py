#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:55 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
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
from ccpn.ui.gui.widgets.RadioButton import RadioButton
from ccpn.ui.gui.widgets.Icon import Icon

CHECKED = QtCore.Qt.Checked
UNCHECKED = QtCore.Qt.Unchecked


class RadioButtons(QtWidgets.QWidget, Base):

    def __init__(self, parent, texts=None, selectedInd=None, exclusive=True,
                 callback=None, direction='h', tipTexts=None, objectNames=None,
                 icons=None,
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
        self.setButtons(texts, selectedInd, direction, tipTexts, objectNames,
                        icons=icons)

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

                            if isinstance(iconSize, (list,tuple)) and len(iconSize) == 2 and \
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

        return self.texts[self.getIndex()]

    def getIndex(self):
        if self.buttonGroup.checkedButton() is not None:
            return self.radioButtons.index(self.buttonGroup.checkedButton())

    @property
    def isChecked(self):

        return self.buttonGroup.checkedButton() is not None

    def set(self, text, silent=False):

        i = self.texts.index(text)
        self.setIndex(i)
        if self.callback and not silent:
            self.callback()

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
            self.callback()


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.BasePopup import BasePopup

    from ccpn.ui.gui.popups.Dialog import CcpnDialog


    def testCallback():
        print('TEST')


    app = TestApplication()
    popup = CcpnDialog(windowTitle='Test radioButtons', setLayout=True)

    buttonGroup = QtWidgets.QButtonGroup(popup)
    # radioButtons = RadioButtons(parent=popup,
    #              callback=testCallback, grid=(0, 0))
    for i in range(10):
        button = RadioButton(popup, text='TEST', grid=(i, 0),
                             callback=None)  # partial(self.assignSelect
        buttonGroup.addButton(button)

    popup.raise_()
    popup.exec()

    app.start()
