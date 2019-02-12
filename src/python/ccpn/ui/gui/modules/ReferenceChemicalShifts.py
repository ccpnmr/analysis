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
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pyqtgraph as pg

from ccpn.core.lib.AssignmentLib import CCP_CODES
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.util.Colour import spectrumHexColours
from ccpnmodel.ccpncore.lib.assignment.ChemicalShift import getCcpCodeData
from ccpn.ui.gui.guiSettings import autoCorrectHexColour, getColours, CCPNGLWIDGET_HEXBACKGROUND


class ReferenceChemicalShifts(CcpnModule):  # DropBase needs to be first, else the drop events are not processed

    includeSettingsWidget = False
    maxSettingsState = 2
    settingsPosition = 'top'
    className = 'ReferenceChemicalShifts'

    def __init__(self, mainWindow, name='Reference Chemical Shifts', ):
        CcpnModule.__init__(self, mainWindow=mainWindow, name=name)
        bc = getColours()[CCPNGLWIDGET_HEXBACKGROUND]
        self.plotWidget = pg.PlotWidget(background=bc)
        self.plotWidget.invertX()
        self.mainWindow = mainWindow
        self.project = self.mainWindow.project
        self.addWidget(self.plotWidget, 1, 0, 1, 4)
        self.plotWidget.plotItem.addLegend(offset=[1, 10])
        self.residueTypeLabel = Label(self, "Residue Type")
        self.addWidget(self.residueTypeLabel, 0, 0)
        self.residueTypePulldown = PulldownList(self, callback=self._updateModule)
        self.residueTypePulldown.setData(CCP_CODES)
        self.addWidget(self.residueTypePulldown, 0, 1)
        self.atomTypeLabel = Label(self, 'Atom Type')
        self.addWidget(self.atomTypeLabel, 0, 2)
        self.atomTypePulldown = PulldownList(self, callback=self._updateModule)
        self.atomTypePulldown.setData(['Hydrogen', 'Heavy'])
        self.addWidget(self.atomTypePulldown, 0, 3)
        self._updateModule()

    def _getDistributionForResidue(self, ccpCode: str, atomType: str):
        """
        Takes a ccpCode and an atom type (Hydrogen or Heavy) and returns a dictionary of lists
        containing the chemical shift distribution for each atom of the specified type in the residue
        """
        dataSets = {}
        ccpData = getCcpCodeData(self.project._apiNmrProject, ccpCode, molType='protein', atomType=atomType)

        atomNames = list(ccpData.keys())

        for atomName in atomNames:
            distribution = ccpData[atomName].distribution
            refPoint = ccpData[atomName].refPoint
            refValue = ccpData[atomName].refValue
            valuePerPoint = ccpData[atomName].valuePerPoint
            x = []
            y = []
            colour = spectrumHexColours[atomNames.index(atomName)]
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
