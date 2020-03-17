"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-03-17 01:02:52 +0000 (Tue, March 17, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-03-16 17:34:13 +0000 (Mon, March 16, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Spectrum import Spectrum
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.PulldownListsForObjects import SpectrumPulldown
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar
from ccpn.ui.gui.widgets.MessageDialog import showWarning


SHOWALLSPECTRA = True


class EstimateVolumes(CcpnDialog):
    """
    Popup to estimate volumes of peaks in peakList from selected spectrum.
    Spectra are all those in the project.
    A spectrum is selected from the spectra in the current.strip if current.strip exists.
    """
    def __init__(self, parent=None, mainWindow=None, title='Estimate Volumes', spectra=None, **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        if mainWindow:
            self.mainWindow = mainWindow
            self.application = mainWindow.application
            self.current = self.application.current
            self.project = mainWindow.project
            self.spectra = spectra if spectra else self.project.spectra
        else:
            self.mainWindow = None
            self.application = None
            self.current = None
            self.project = None

        self._createWidgets()

        if self.current is not None and self.current.strip is not None and \
                not self.current.strip.isDeleted and len(self.current.strip.spectra) > 0:
            self.spectrumPullDown.select(self.current.strip.spectra[0].pid)

        self._changePeakLists()
        self.setFixedSize(self.sizeHint())

    def _createWidgets(self):
        """Create the widgets for the popup
        """
        row = 0
        self.spectrumPullDown = SpectrumPulldown(self, self.mainWindow, grid=(row, 0), gridSpan=(1, 3),
                                                 callback=self._changePeakLists,
                                                 filterFunction=self._filterToStrip)

        row += 1
        self._label = Label(self, grid=(row, 0), gridSpan=(1, 3), text='Select peakLists:')

        row += 1
        self.peakListWidget = ListWidget(self, multiSelect=True, callback=self._selectPeakLists, tipText='Select PeakLists',
                                         grid=(row, 0), gridSpan=(1, 3))
        self.peakListWidget.setSelectContextMenu()

        row += 1
        self.buttonBox = ButtonList(self, grid=(row, 1), gridSpan=(1, 2), texts=['Close', 'Estimate Volumes'],
                                    callbacks=[self.accept, self._estimateVolumes])

    def _changePeakLists(self, *args):
        """Update the peakLists in the table from the current spectrum in the pulldown.
        """
        obj = self.spectrumPullDown.getSelectedObject()

        if isinstance(obj, Spectrum):
            self.peakListWidget.setObjects(obj.peakLists, name='pid')

    def _filterToStrip(self, values):
        """Filter the pulldown list to the spectra in the current strip;
        however, need to be able to select all spectra
        (this is currently overriding self.spectra)
        """
        if not SHOWALLSPECTRA and self.current.strip:
            return [specView.spectrum.pid for specView in self.current.strip.spectrumDisplay.spectrumViews]
        else:
            return values

    def _selectPeakLists(self, *args):
        # nothing required yet
        pass

    def _estimateVolumes(self):
        """Estimate the volumes for the peaks in the peakLists highlighted in the listWidget
        """
        peakLists = self.peakListWidget.getSelectedObjects()
        if not peakLists:
            showWarning('Estimate Volumes', 'No peakLists selected')

        else:
            volumeIntegralLimit = self.application.preferences.general.volumeIntegralLimit

            # estimate the volumes for the peakLists
            with undoBlockWithoutSideBar(self.application):
                for peakList in peakLists:
                    peakList.estimateVolumes(volumeIntegralLimit=volumeIntegralLimit)

