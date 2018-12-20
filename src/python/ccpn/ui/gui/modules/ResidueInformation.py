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
__dateModified__ = "$dateModified: 2017-07-07 16:32:46 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets

from ccpn.core.lib.AssignmentLib import CCP_CODES
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea


class ResidueInformation(CcpnModule):
    includeSettingsWidget = False
    maxSettingsState = 2
    settingsPosition = 'top'
    className = 'ResidueInformation'

    def __init__(self, mainWindow, name='Residue Information', **kwds):
        CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self._widgetScrollArea = ScrollArea(parent=self.mainWidget, grid=(0, 0), scrollBarPolicies=('asNeeded', 'asNeeded'), **kwds)
        self._widgetScrollArea.setWidgetResizable(True)
        self._widget = Widget(parent=self._widgetScrollArea, setLayout=True)
        self._widgetScrollArea.setWidget(self._widget)
        self._widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.chainLabel = Label(self._widget, text='Chain', grid=(0, 0))
        # self.layout.addWidget(chainLabel, 0, 0)
        chainPulldown = PulldownList(self._widget, callback=self._setChain, grid=(0, 1))
        chainPulldownData = [chain.pid for chain in self.project.chains]
        chainPulldownData.append('<All>')
        chainPulldown.setData(chainPulldownData)
        self.selectedChain = self.project.getByPid(chainPulldown.currentText())
        self.residueLabel = Label(self._widget, text='Residue ', grid=(0, 3))

        self.colourScheme = self.application.colourScheme
        self.residuePulldown = PulldownList(self._widget, callback=self._setCurrentResidue,
                                            grid=(0, 4))
        self.residuePulldown.setData(CCP_CODES)
        self.selectedResidueType = self.residuePulldown.currentText()
        self.residueWidget = Widget(self._widget, setLayout=True,
                                    grid=(1, 0), gridSpan=(1, 5))

        self.spacer = Spacer(self._widget, 5, 5,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
                             grid=(2, 5), gridSpan=(1, 1))

        # self._setWidgetHeight(35)

        # self.residueWidget = QtWidgets.QWidget(self)
        # self.residueWidget.setLayout(QtWidgets.QGridLayout())
        # self.project = project
        # self.layout.addWidget(self.residueWidget, 1, 0, 1, 5)
        self._getResidues()

    def _setChain(self, value: str):
        """
        Sets the selected chain to the specified value and updates the module.
        """
        if value == '<All>':
            self.selectedChain = 'All'
        else:
            self.selectedChain = self.project.getByPid(value)
        self._getResidues()

    def _setCurrentResidue(self, value: str):
        """
        Sets the selected residue to the specified value and updates the module.
        """
        self.selectedResidueType = value
        self._getResidues()

    def _getResidues(self):
        """
        Finds all residues of the selected type along with one flanking residue either side and displays
        this information in the module.
        """
        if self.colourScheme == 'dark':
            stylesheet = 'Label {background-color: #f7ffff; color: #2a3358;}'
        elif self.colourScheme == 'light':
            stylesheet = 'Label {background-color: #bd8413; color: #fdfdfc;}'
        foundResidues = []
        if self.selectedChain == 'All':
            residues = self.project.residues
        else:
            if self.selectedChain is not None:
                residues = self.selectedChain.residues
            else:
                return

        if residues:
            for residue in residues:
                if residue.residueType == self.selectedResidueType.upper():
                    foundResidues.append([residue.previousResidue, residue, residue.nextResidue])
            layout = self.residueWidget.layout()
            for r in range(layout.rowCount()):
                for n in range(3):
                    item = layout.itemAtPosition(r, n)
                    if item is not None:
                        item.widget().deleteLater()

            j = 0  # why was this introduced (it's not altered below)?
            for i in range(len(foundResidues)):

                if foundResidues[j + i][0] is not None:
                    label1 = Label(self, text=foundResidues[j + i][0].id,
                                   hAlign='c')
                    label1.setMaximumHeight(30)
                    if foundResidues[j + i][0].nmrResidue is not None:
                        label1.setStyleSheet(stylesheet)

                    self.residueWidget.layout().addWidget(label1, j + i, 0)
                if len(foundResidues[j + i]) > 1:
                    label2 = Label(self, text=foundResidues[j + i][1].id,
                                   hAlign='c')
                    if foundResidues[j + i][1].nmrResidue is not None:
                        label2.setStyleSheet(stylesheet)
                    label2.setMaximumHeight(30)
                    self.residueWidget.layout().addWidget(label2, j + i, 1)
                if len(foundResidues[j + i]) > 2:
                    label3 = Label(self, text=foundResidues[j + i][2].id,
                                   hAlign='c')
                    if foundResidues[j + i][2].nmrResidue is not None:
                        label3.setStyleSheet(stylesheet)
                    self.residueWidget.layout().addWidget(label3, j + i, 2)
                    label3.setMaximumHeight(30)
