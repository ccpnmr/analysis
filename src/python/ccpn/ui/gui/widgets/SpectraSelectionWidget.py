"""
A widget to select spectra or spectrum group as input data for modules or popup
"""

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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2019-12-05 09:40:40 +0000 (Thu, December 05, 2019) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets

import decimal
from functools import partial
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from collections import OrderedDict
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb
from ccpn.ui.gui.widgets.Widget import Widget

DEFAULTSPACING = (5, 5)
TABMARGINS = (1, 10, 10, 1)  # l, t, r, b
ZEROMARGINS = (0, 0, 0, 0)  # l, t, r, b


class SpectraSelectionWidget(Widget):

    def __init__(self, parent=None, mainWindow=None, **kwds):
        super().__init__(parent, setLayout=True, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current
        self.allSGCheckBoxes = []
        self.allSpectraCheckBoxes = []
        self._setWidgets()

    def _setWidgets(self):
        i = 0
        self.selectSpectraOption = None
        if len(self.project.spectra) > 0:
            self.selectSpectraOption = RadioButtons(self,
                                                    texts=['Spectra', 'Groups'],
                                                    selectedInd=0,
                                                    callback=self.showSpectraOption,
                                                    tipTexts=None,
                                                    hAlign='l',
                                                    grid=(i, 0))
            i += 1

            self.selectAllButton = ButtonList(self, texts=['All','Clear', 'Add From Current Display'],
                                                    callbacks=[partial(self._toggleAll, True),
                                                               partial(self._toggleAll, False),
                                                               self._selectFromDisplay],
                                                    grid=(i, 0),
                                                    hAlign='l', vAlign='t')

            i += 1
            if not self.current.strip:
                self.selectAllButton.buttons[-1].setEnabled(False)

            self.scrollAreaWidgetContents = ScrollableFrame(self, setLayout=True, spacing=DEFAULTSPACING,
                     scrollBarPolicies=('asNeeded', 'asNeeded'), margins=TABMARGINS, grid=(i, 0))

            self._addSpectrumCheckBoxes()
            self._addSpectrumGroupsCheckBoxes()
            self.showSpectraOption()

    def _addSpectrumCheckBoxes(self):
        self.allSpectraCheckBoxes = []
        if self.project is not None:
            for i, spectrum in enumerate(self.project.spectra, start=2):
                self.spectrumCheckBox = CheckBox(self.scrollAreaWidgetContents, text=str(spectrum.pid), grid=(i, 0),
                                                 hAlign='l', vAlign='t')
                self.allSpectraCheckBoxes.append(self.spectrumCheckBox)

    def _addSpectrumGroupsCheckBoxes(self):
        self.allSGCheckBoxes = []
        if self.project is not None:
            for i, sg in enumerate(self.project.spectrumGroups, start=2):
                self.spectrumGroupCheckBox = CheckBox(self.scrollAreaWidgetContents, text=str(sg.pid),
                                                      grid=(i, 0), hAlign='l', vAlign='t')
                self.allSGCheckBoxes.append(self.spectrumGroupCheckBox)

    def _toggleAll(self, select=True):
        if self.selectSpectraOption:
            if self.selectSpectraOption.getIndex() == 0:
                checkBoxes = self.allSpectraCheckBoxes
            else:
                checkBoxes = self.allSGCheckBoxes
            tt = [checkBox.setChecked(select) for checkBox in checkBoxes]


    def _getSelectedSpectra(self):
        spectra = []
        for cb in self.allSpectraCheckBoxes:
            if cb.isChecked():
                spectrum = self.project.getByPid(str(cb.text()))
                spectra.append(spectrum)
        return spectra

    def _getSpectrumGroupsSpectra(self):
        spectra = []
        for sg in self.allSGCheckBoxes:
            if sg.isChecked():
                spectrumGroup = self.project.getByPid(str(sg.text()))
                spectra += spectrumGroup.spectra
        return spectra

    def getSelections(self):
        if self.selectSpectraOption is not None:
            if self.selectSpectraOption.getIndex() == 0:
                return self._getSelectedSpectra()
            else:
                return self._getSpectrumGroupsSpectra()
        else:
            return []

    def _selectSpectra(self, spectra):
        checkBoxes = [cb for cb in self.allSpectraCheckBoxes if self.project.getByPid(cb.text()) in spectra]
        tt = [checkBox.setChecked(True) for checkBox in checkBoxes]

    def _selectSpectrumGroups(self, spectrumGroups):
        checkBoxes = [cb for cb in self.allSGCheckBoxes if self.project.getByPid(cb.text()) in spectrumGroups]
        tt = [checkBox.setChecked(True) for checkBox in checkBoxes]

    def showSpectraOption(self):
        if self.selectSpectraOption:
            sel = [(sbox.show(), gbox.hide())
                   if self.selectSpectraOption.getIndex() == 0
                   else (sbox.hide(), gbox.show())
                   for gbox in self.allSGCheckBoxes
                   for sbox in self.allSpectraCheckBoxes]

    def _selectFromDisplay(self):
        """ Select spectra from current strip"""
        if self.current.strip:
            if self.selectSpectraOption.getIndex() == 0: # SPECTRA selected
                self._selectSpectra(self.current.strip.spectra)
            if self.selectSpectraOption.getIndex() == 1:
                self._selectSpectrumGroups(self.current.strip.spectrumGroups)
