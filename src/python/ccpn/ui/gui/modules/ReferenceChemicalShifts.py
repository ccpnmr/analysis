"""
Module documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-01-22 15:44:49 +0000 (Fri, January 22, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pyqtgraph as pg
from PyQt5 import QtWidgets
from ccpn.core.lib.AssignmentLib import CCP_CODES
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.util.Colour import spectrumHexDarkColours, spectrumHexLightColours
from ccpn.ui.gui.guiSettings import getColours, CCPNGLWIDGET_HEXBACKGROUND
from ccpn.ui.gui.widgets.Frame import Frame


class ReferenceChemicalShifts(CcpnModule):  # DropBase needs to be first, else the drop events are not processed

    includeSettingsWidget = False
    maxSettingsState = 2
    settingsPosition = 'top'
    className = 'ReferenceChemicalShifts'

    def __init__(self, mainWindow, name='Reference Chemical Shifts', ):
        super().__init__(mainWindow=mainWindow, name=name)

        self.preferences = self.mainWindow.application.preferences

        self.mainWindow = mainWindow
        self.project = self.mainWindow.project

        self._RCwidgetFrame = Frame(self.mainWidget, setLayout=True,
                                    grid=(0, 0), gridSpan=(1, 1),
                                    hPolicy='ignored'
                                    )
        self._RCwidget = Frame(self._RCwidgetFrame, setLayout=True,
                               grid=(0, 0), gridSpan=(1, 1),
                               hPolicy='minimumExpanding',
                               hAlign='l', margins=(5, 5, 5, 5))
        self._RCwidget.getLayout().setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)

        bc = getColours()[CCPNGLWIDGET_HEXBACKGROUND]
        self.plotWidget = pg.PlotWidget(background=bc)
        self.plotWidget.invertX()
        self.mainWidget.getLayout().addWidget(self.plotWidget, 1, 0, 1, 1)
        self.plotWidget.plotItem.addLegend(offset=[1, 10])

        self.residueTypeLabel = Label(self._RCwidget, "Residue Type:", grid=(0, 0))
        self.residueTypePulldown = PulldownList(self._RCwidget, callback=self._updateModule, grid=(0, 1))
        self.residueTypePulldown.setData(CCP_CODES)
        self.atomTypeLabel = Label(self._RCwidget, 'Atom Type:', grid=(0, 2))
        self.atomTypePulldown = PulldownList(self._RCwidget, callback=self._updateModule, grid=(0, 3))
        self.atomTypePulldown.setData(['Hydrogen', 'Heavy'])

        self._updateModule()

    def _getDistributionForResidue(self, ccpCode: str, atomType: str):
        """
        Takes a ccpCode and an atom type (Hydrogen or Heavy) and returns a dictionary of lists
        containing the chemical shift distribution for each atom of the specified type in the residue
        """
        dataSets = {}
        ccpData = self.project.getCcpCodeData(ccpCode, molType='protein', atomType=atomType)

        atomNames = list(ccpData.keys())

        for atomName in atomNames:
            distribution = ccpData[atomName].distribution
            refPoint = ccpData[atomName].refPoint
            refValue = ccpData[atomName].refValue
            valuePerPoint = ccpData[atomName].valuePerPoint
            x = []
            y = []
            if self.preferences.general.colourScheme == 'dark':
                col = (11 + 7 * atomNames.index(atomName)) % len(spectrumHexLightColours) - 1
                colour = spectrumHexLightColours[col]
            else:
                col = (11 + 7 * atomNames.index(atomName)) % len(spectrumHexDarkColours) - 1
                colour = spectrumHexDarkColours[col]
            for i in range(len(distribution)):
                x.append(refValue + valuePerPoint * (i - refPoint))
                y.append(distribution[i])
            dataSets[atomName] = [x, y, colour]

        return dataSets

    def _updateModule(self, item=None):
        """
        Updates the information displayed in the module when either the residue type or the atom type
        selectors are changed.
        """
        self.plotWidget.clear()
        while self.plotWidget.plotItem.legend.layout.count() > 0:
            self.plotWidget.plotItem.legend.layout.removeAt(0)
        self.plotWidget.plotItem.legend.items = []

        self.plotWidget.showGrid(x=True, y=True)
        atomType = self.atomTypePulldown.currentText()
        ccpCode = self.residueTypePulldown.currentText()
        dataSets = self._getDistributionForResidue(ccpCode, atomType)
        for atomName, dataSet in dataSets.items():
            self.plotWidget.plot(dataSet[0], dataSet[1], pen=dataSet[2], name=atomName, kargs={'clear': True})

    def close(self):
        self._closeModule()

    def _closeModule(self):
        super()._closeModule()
