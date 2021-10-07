"""
Module Documentation here
"""
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
__dateModified__ = "$dateModified: 2021-10-07 18:40:33 +0100 (Thu, October 07, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2019-11-27 12:20:27 +0000 (Wed, November 27, 2019) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
from itertools import permutations
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, undoStackBlocking
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.lib.Strip import copyStripPosition


class CopyStripFlippedSpectraPopup(CcpnDialogMainWidget):
    """
    Set the axis ordering for the new spectrumDisplay from a popup
    """

    def __init__(self, parent=None, mainWindow=None, strip=None, title='Copy Strip with Axes Flipped', label='', **kwds):
        # super().__init__(parent, mainWindow=mainWindow, title=title, **kwds)
        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        # make sure there's a strip
        if not strip:
            return

        self.mainWindow = mainWindow
        self.project = self.mainWindow.project
        self.application = self.mainWindow.application
        self.current = self.application.current
        self.strip = strip
        self.axisCodes = strip.axisCodes
        self._axisOrdering = strip.axisCodes

        if strip.axisCodes:
            row = 0
            Label(self.mainWidget, text=label + ' - ' + str(self._axisOrdering), bold=True, grid=(row, 0), gridSpan=(1, 3))

            row += 1
            self.preferredAxisOrderPulldown = PulldownListCompoundWidget(self.mainWidget, labelText="Select Axis Ordering:",
                                                                         grid=(row, 0), gridSpan=(1, 3), vAlign='t',
                                                                         callback=self._setAxisCodeOrdering)
            self.preferredAxisOrderPulldown.setPreSelect(self._fillPreferredWidget)

            # enable the buttons
            self.setOkButton(callback=self._accept)
            self.setCancelButton(callback=self.reject)
            self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)

            self._populate()

            self.__postInit__()
            self._okButton = self.getButton(self.OKBUTTON)
            self._cancelButton = self.getButton(self.CANCELBUTTON)

        else:
            self.close()

    def _populate(self):
        self._fillPreferredWidget()

    def _fillPreferredWidget(self):
        """Fill the pullDown with the currently available permutations of the axis codes
        """
        specOrder = None

        ll = ['<None>']
        axisPerms = []
        axisOrder = []
        if self.mainWindow:
            # add permutations for the axes
            axisPerms = permutations([axisCode for axisCode in self.axisCodes])
            axisOrder = tuple(permutations(list(range(len(self.axisCodes)))))
            ll += [" ".join(ax for ax in perm) for perm in axisPerms]

        self.preferredAxisOrderPulldown.pulldownList.setData(ll)

        # if specOrder is not None and self.mainWindow:
        #     specIndex = axisOrder.index(specOrder) + 1
        self.preferredAxisOrderPulldown.setIndex(1)

    def _setAxisCodeOrdering(self, value):
        """Set the preferred axis ordering from the pullDown selection
        """
        index = self.preferredAxisOrderPulldown.getIndex()

        axisOrder = tuple(permutations(list(range(len(self.axisCodes)))))
        if index > 0:
            self._axisOrdering = tuple(axisOrder[index - 1])
        else:
            self._axisOrdering = None

    def _accept(self):
        self.accept()

        # open new spectrumDisplay here
        # with undoBlockWithoutSideBar():
        with undoStackBlocking() as _:  # Do not add to undo/redo stack
            spectra = self.strip.spectra
            if spectra:
                # create a new spectrum display with the new axis order
                newDisplay = self.mainWindow.createSpectrumDisplay(spectra[0], axisCodes=tuple(self.axisCodes[ii] for ii in self._axisOrdering))
                for spectrum in spectra:
                    newDisplay.displaySpectrum(spectrum)

                # newDisplay.autoRange()
                copyStripPosition(self.strip, newDisplay.strips[0])
