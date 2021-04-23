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
__dateModified__ = "$dateModified: 2021-04-23 14:36:21 +0100 (Fri, April 23, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-04-22 11:01:59 +0000 (Thu, April 22, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from collections import OrderedDict
from functools import partial
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.popups.Dialog import CcpnDialog, handleDialogApply
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
from ccpn.core.Spectrum import MAXALIASINGRANGE
from ccpn.core.lib.ContextManagers import undoStackBlocking


DEFAULTALIASING = MAXALIASINGRANGE
COLWIDTH = 140


class SetPeakAliasingPopup(CcpnDialog):
    """
    Open a small popup to allow setting aliasing value of selected 'current' items
    """

    def __init__(self, parent=None, mainWindow=None, title='Set Aliasing', items=None, **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        row = 0
        self.spectra = OrderedDict()
        self.spectraPulldowns = OrderedDict()
        self.spectraCheckBoxes = OrderedDict()

        Label(self, text='Set aliasing for currently selected peaks', grid=(row, 0), gridSpan=(1, 2))
        row += 1

        spectrumFrame = Frame(self, setLayout=True, showBorder=False, grid=(row, 0), gridSpan=(1, 2))

        specRow = 0
        aliasRange = list(range(MAXALIASINGRANGE, -MAXALIASINGRANGE - 1, -1))
        aliasText = [str(aa) for aa in aliasRange]

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
                for dim in range(dims):
                    self.spectraPulldowns[spectrum].append(PulldownList(spectrumFrame, texts=aliasText,
                                                                        grid=(specRow, dim + 2)))  #, index=DEFAULTALIASING))

                    # may cause a problem if the peak dimension does not correspond to a visible XY axis
                    # peaks could disappear from all views

                specRow += 1

            self.spectra[peak.peakList.spectrum].add(peak)

        row += 1
        # add close buttons at the bottom
        self.buttonList = ButtonList(self, ['Close', 'OK'], [self.reject, self._okButton], grid=(row, 1))
        self.buttonList.buttons[1].setFocus()

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

        self.setFixedSize(self.sizeHint())

        self.GLSignals = GLNotifier(parent=self)

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

        self.accept()
