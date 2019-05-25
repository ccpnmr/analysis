"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.popups.AxisOrderingPopup import AxisOrderingPopup, checkSpectraToOpen
import sys
from PyQt5 import QtWidgets, QtCore
from itertools import permutations
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.util.floatUtils import fRound
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.lib.ContextManagers import undoBlock


class CopyStripFlippedSpectraPopup(AxisOrderingPopup):
    """
    Set the axis ordering for the new spectrumDisplay from a popup
    """

    def __init__(self, parent=None, mainWindow=None, strip=None, title='Copy Strip with Axes Flipped', label='', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

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
            Label(self, text=title + ': ' + label + ' - ' + str(self._axisOrdering), bold=True, grid=(row, 0), gridSpan=(1, 3))

            row += 1
            self.preferredAxisOrderPulldown = PulldownListCompoundWidget(self, labelText="Select Axis Ordering:",
                                                                         grid=(row, 0), gridSpan=(1, 3), vAlign='t',
                                                                         callback=self._setAxisCodeOrdering)
            self.preferredAxisOrderPulldown.setPreSelect(self._fillPreferredWidget)
            self._fillPreferredWidget()

            row += 1
            self.buttonBox = ButtonList(self, grid=(row, 2), gridSpan=(1, 1), texts=['Cancel', 'Ok'],
                                        callbacks=[self.reject, self._accept])
            self.setDefaultButton(self.buttonBox.getButton('Cancel'))

            row += 1
            Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
                   grid=(row, 1), gridSpan=(1, 1))

            self.setFixedSize(self.sizeHint())
        else:
            self.close()

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
        with undoBlock():
            spectra = self.strip.spectra
            if spectra:
                # create a new spectrum display with the new axis order
                newDisplay = self.mainWindow.createSpectrumDisplay(spectra[0], axisOrder=tuple(self.axisCodes[ii] for ii in self._axisOrdering))
                for spectrum in spectra:
                    newDisplay.displaySpectrum(spectrum)
                newDisplay.autoRange()
