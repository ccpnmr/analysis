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
__dateModified__ = "$dateModified: 2021-09-17 15:54:56 +0100 (Fri, September 17, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-12-03 18:38:18 +0000 (Thu, December 03, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict
from functools import partial
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget, handleDialogApply
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
from ccpn.ui.gui.lib.SpectrumDisplay import navigateToCurrentPeakPosition
from ccpn.core.Spectrum import MAXALIASINGRANGE
from ccpn.core.lib.ContextManagers import undoStackBlocking


DEFAULTALIASING = MAXALIASINGRANGE
COLWIDTH = 140


class SetPeakAliasingPopup(CcpnDialogMainWidget):
    """
    Open a small popup to allow setting aliasing value of selected 'current' items
    """
    FIXEDWIDTH = True
    FIXEDHEIGHT = True

    # internal namespace
    _NAVIGATETO = '_navigateTo'

    def __init__(self, parent=None, mainWindow=None, title='Set Aliasing', items=None, **kwds):
        """
        Initialise the widget
        """
        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.spectra = OrderedDict()
        self.spectraPulldowns = OrderedDict()
        self.spectraCheckBoxes = OrderedDict()

        # setup the widgets
        self._setWidgets()

        # set up the required buttons for the dialog
        self.setCloseButton(callback=self.reject, enabled=True, text='Close', tipText='Close Dialog')
        self.setOkButton(callback=self._okButton, enabled=True, text='Set Aliasing', tipText='Set Aliasing and Close')
        self.setDefaultButton(self.CLOSEBUTTON)

        # populate the widgets
        self._populate()

        # set the links to the buttons
        self.__postInit__()
        self._okButton = self.dialogButtons.button(self.OKBUTTON)
        self._closeButton = self.dialogButtons.button(self.CLOSEBUTTON)

        self.GLSignals = GLNotifier(parent=self)

    def _setWidgets(self):
        """Setup the widgets for the dialog
        """
        row = 0
        Label(self.mainWidget, text='Set aliasing for currently selected peaks', grid=(row, 0), gridSpan=(1, 2))
        row += 1

        spectrumFrame = Frame(self.mainWidget, setLayout=True, showBorder=False, grid=(row, 0), gridSpan=(1, 2))
        row += 1

        specRow = 0
        for peak in self.current.peaks:

            if peak.peakList.spectrum not in self.spectra:

                spectrum = peak.peakList.spectrum
                self.spectra[spectrum] = set()
                dims = spectrum.dimensionCount

                if specRow > 0:
                    # add divider
                    HLine(spectrumFrame, grid=(specRow, 0), gridSpan=(1, dims + 2), colour=getColours()[DIVIDER], height=15)
                    specRow += 1

                # add pulldown widget
                Label(spectrumFrame, text='Spectrum: %s' % str(spectrum.pid), grid=(specRow, 0), bold=True)
                Label(spectrumFrame, text=' axisCodes:', grid=(specRow, 1))

                for dim in range(dims):
                    Label(spectrumFrame, text=spectrum.axisCodes[dim], grid=(specRow, dim + 2))
                specRow += 1

                self.spectraPulldowns[spectrum] = []
                Label(spectrumFrame, text=' aliasing:', grid=(specRow, 1))

                aliasInds = spectrum.aliasingIndexes

                for dim in range(dims):
                    aliasRange = list(range(aliasInds[dim][1], aliasInds[dim][0] - 1, -1))
                    aliasText = [str(aa) for aa in aliasRange]

                    self.spectraPulldowns[spectrum].append(PulldownList(spectrumFrame, texts=aliasText,
                                                                        grid=(specRow, dim + 2)))

                    # may cause a problem if the peak dimension does not correspond to a visible XY axis
                    # peaks could disappear from all views

                specRow += 1

            self.spectra[peak.peakList.spectrum].add(peak)

        self.navigateToPeaks = CheckBoxCompoundWidget(
                self.mainWidget,
                grid=(row, 0), gridSpan=(1, 2), hAlign='left',
                orientation='left',
                labelText='Navigate to new peak position',
                checked=False
                )

    def _populate(self):
        """Populate the widgets
        """
        for spectrum in self.spectra.keys():
            dims = spectrum.dimensionCount
            aliasCount = []
            dimAlias = []
            for dim in range(dims):
                dimAlias.append(set())
                aliasCount.append({})

            for peak in self.spectra[spectrum]:
                pa = peak.aliasing
                for dim in range(dims):
                    dimAlias[dim].add(pa[dim])

                    if pa[dim] not in aliasCount[dim]:
                        aliasCount[dim][pa[dim]] = 0
                    aliasCount[dim][pa[dim]] += 1

            for dim in range(dims):
                if len(dimAlias[dim]) == 1:
                    self.spectraPulldowns[spectrum][dim].select(str(dimAlias[dim].pop()))

                elif len(dimAlias[dim]) > 1:
                    self.spectraPulldowns[spectrum][dim].select('0')

                    # set to the most common aliasing
                    maxAlias = max(aliasCount[dim].values())
                    maxKey = [k for k, v in aliasCount[dim].items() if v == maxAlias]
                    if maxKey:
                        self.spectraPulldowns[spectrum][dim].select(str(maxKey[0]))

                else:
                    # just set to 0
                    self.spectraPulldowns[spectrum][dim].select('0')

    def _okButton(self):
        """
        When ok button pressed: update and exit
        """
        with handleDialogApply(self):
            for spec in self.spectra.keys():
                # set the aliasing for the peaks
                newAlias = tuple([int(pullDown.get()) for pullDown in self.spectraPulldowns[spec]])

                for peak in self.spectra[spec]:
                    peak.aliasing = newAlias

        if self.navigateToPeaks.isChecked():
            navigateToCurrentPeakPosition(self.application, selectFirstPeak=True)

        self.accept()

    def storeWidgetState(self):
        """Store the state of the checkBoxes between popups
        """
        nav = self.navigateToPeaks.isChecked()
        SetPeakAliasingPopup._storedState[self._NAVIGATETO] = nav

    def restoreWidgetState(self):
        """Restore the state of the checkBoxes
        """
        self.navigateToPeaks.set(SetPeakAliasingPopup._storedState.get(self._NAVIGATETO, False))

    def reject(self):
        super().reject()

        # store the state of any required widgets
        self.storeWidgetState()
