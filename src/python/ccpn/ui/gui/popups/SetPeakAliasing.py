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

                self.spectraCheckBoxes[spectrum] = CheckBoxCompoundWidget(spectrumFrame,
                                                                          grid=(specRow, 0), gridSpan=(1, dims + 2),  #vAlign='top', hAlign='left',
                                                                          # fixedWidths=(COLWIDTH, 30),
                                                                          orientation='left',
                                                                          labelText='Update spectrum aliasing parameters:',
                                                                          checked=spectrum._updateAliasingRangeFlag,
                                                                          callback=partial(self._updateAliasingRangeFlag, spectrum)
                                                                          )
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

    def _updateAliasingRangeFlag(self, spectrum, updateValue):
        """Set the upateAliasingRange flag for spectra
        """
        if spectrum:
            spectrum._updateAliasingRangeFlag = updateValue

    def _refreshGLItems(self, spectrumUpdateList):
        """update the display for the changed aliasing range
        """
        for spectrum, updateFlag in spectrumUpdateList:
            if updateFlag:
                alias = spectrum._getAliasingRange()
                if alias is not None:

                    # notifier handles spectrumDisplay change
                    spectrum.visibleAliasingRange = alias

        # for spectrum in self.project.spectra:
        #
        #     # check whether the visibleAliasingRange needs to be updated
        #     if not spectrum._updateAliasingRangeFlag:
        #         continue
        #
        #     alias = spectrum._getAliasingRange()
        #     if alias is not None:
        #         spectrum.visibleAliasingRange = alias
        #         spectrum.displayFoldedContours = True

            # # calculate the min/max aliasing values for the spectrum
            # dims = spectrum.dimensionCount
            #
            # aliasMin = [0] * dims
            # aliasMax = [0] * dims
            #
            # alias = None
            # for peakList in spectrum.peakLists:
            #     for peak in peakList.peaks:
            #         alias = peak.aliasing
            #         aliasMax = np.maximum(aliasMax, alias)
            #         aliasMin = np.minimum(aliasMin, alias)
            #
            # if alias:
            #     # set min/max in spectrum here if a peak has been found
            #     aliasRange = tuple((int(mn), int(mx)) for mn, mx in zip(aliasMin, aliasMax))
            #     spectrum.visibleAliasingRange = aliasRange
            #     spectrum.displayFoldedContours = True

        # emit a signal to rebuild all peaks
        # self.GLSignals.emitEvent(triggers=[GLNotifier.GLALLPEAKS, GLNotifier.GLALLMULTIPLETS])

    def _okButton(self):
        """
        When ok button pressed: update and exit
        """
        with handleDialogApply(self):

            spectrumUpdateList = tuple((spec,
                                        spec._updateAliasingRangeFlag) for spec in self.spectra.keys())

            # add item here to redraw items
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=partial(self._refreshGLItems, spectrumUpdateList))

            for spec in self.spectra.keys():
                # set the aliasing for the peaks
                newAlias = tuple([int(pullDown.get()) for pullDown in self.spectraPulldowns[spec]])

                for peak in self.spectra[spec]:
                    peak.aliasing = newAlias

            # add item here to redraw items
            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(self._refreshGLItems, spectrumUpdateList))

            # redraw the items
            self._refreshGLItems(spectrumUpdateList)

        self.accept()
