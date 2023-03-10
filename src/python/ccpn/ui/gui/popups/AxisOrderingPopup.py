"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-03-10 18:39:55 +0000 (Fri, March 10, 2023) $"
__version__ = "$Revision: 3.1.1 $"
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
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup


class AxisOrderingPopup(CcpnDialogMainWidget):
    """
    Set the axis ordering for the new spectrumDisplay from a popup
    """

    def __init__(self, parent=None, mainWindow=None, spectrum=None, title='Set Spectrum Axis Ordering', label='', **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.project = self.mainWindow.project
        self.application = self.mainWindow.application
        self.current = self.application.current
        self.spectrum = spectrum

        if self.spectrum:

            row = 0
            Label(self.mainWidget, text=f'{title}: {label} - {str(spectrum.pid)}', bold=True, grid=(row, 0), gridSpan=(1, 3))

            row += 1
            self.preferredAxisOrderPulldown = PulldownListCompoundWidget(self.mainWidget, labelText="Select Axis Ordering",
                                                                         grid=(row, 0), gridSpan=(1, 3), vAlign='t',
                                                                         callback=self._setSpectrumOrdering)
            self.preferredAxisOrderPulldown.setPreSelect(self._fillPreferredWidget)
            self._fillPreferredWidget()

            row += 1
            self.buttonBox = ButtonList(self.mainWidget, grid=(row, 2), gridSpan=(1, 1), texts=['Ok'],
                                        callbacks=[self._accept])

            row += 1
            Spacer(self.mainWidget, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
                   grid=(row, 1), gridSpan=(1, 1))

            self.setFixedSize(self.sizeHint())
        else:
            self.close()

    def _fillPreferredWidget(self):
        """Fill the pullDown with the currently available permutations of the axis codes
        """
        specOrder = tuple(self.spectrum._preferredAxisOrdering) if self.spectrum._preferredAxisOrdering is not None else None

        ll = ['<None>']
        axisPerms = []
        axisOrder = []
        if self.mainWindow:
            # add permutations for the axes
            axisPerms = permutations(list(self.spectrum.axisCodes))
            axisOrder = tuple(permutations(list(range(len(self.spectrum.axisCodes)))))
            ll += [" ".join(perm) for perm in axisPerms]

        self.preferredAxisOrderPulldown.pulldownList.setData(ll)

        if specOrder is not None and self.mainWindow:
            specIndex = axisOrder.index(specOrder) + 1
            self.preferredAxisOrderPulldown.setIndex(specIndex)

    def _setSpectrumOrdering(self, value):
        """Set the preferred axis ordering from the pullDown selection
        """
        index = self.preferredAxisOrderPulldown.getIndex()

        axisOrder = tuple(permutations(list(range(len(self.spectrum.axisCodes)))))
        if index > 0:
            self.spectrum._preferredAxisOrdering = tuple(axisOrder[index - 1])
        else:
            self.spectrum._preferredAxisOrdering = None

    def _accept(self):
        self.accept()


#=========================================================================================
# checkSpectraToOpen
#=========================================================================================

def checkSpectraToOpen(mainWindow, spectra):
    for obj in spectra:
        if isinstance(obj, Spectrum):
            # opening a new spectrumDisplay - check axisOrdering
            axisOption = mainWindow.application.preferences.general.axisOrderingOptions

            # either popup the options window, or use spectrum defaults
            if axisOption == 0:
                # use spectrum defaults - ignore as already set in the spectrum class
                pass

            elif axisOption == 1 and not mainWindow.project.waypointBlocking:

                # always ask
                popup = AxisOrderingPopup(parent=mainWindow, mainWindow=mainWindow, title='Set Spectrum Axis Ordering', spectrum=obj)
                popup.exec_()

                # only do for the first spectrum
                break

        elif isinstance(obj, SpectrumGroup):
            # opening a new spectrumDisplay - check axisOrdering
            axisOption = mainWindow.application.preferences.general.axisOrderingOptions

            # either popup the options window, or use spectrum defaults
            if axisOption == 0:
                # use spectrum defaults - ignore as already set in the spectrum class
                pass

            elif axisOption == 1 and obj.spectra and not mainWindow.project.waypointBlocking:

                # always ask
                popup = AxisOrderingPopup(parent=mainWindow, mainWindow=mainWindow,
                                          title='Set SpectrumGroup Axis Ordering', label=', (first spectrum)', spectrum=obj.spectra[0])
                popup.exec_()

                # only do for the first spectrum
                break
