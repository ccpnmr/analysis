"""
Module Documentation here
"""
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-07-04 09:28:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.SettingsWidgets import StripPlot, STRIPPLOT_PEAKS, STRIPPLOT_NMRRESIDUES, STRIPPLOT_NMRCHAINS, NO_STRIP
from ccpn.ui.gui.widgets.MessageDialog import progressManager
from ccpn.util.decorators import profile

class StripPlotPopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, spectrumDisplay=None, title='StripPlot',
                 includePeakLists=False,
                 includeNmrChains=False,
                 includeNmrChainPullSelection=False,
                 includeSpectrumTable=False, **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        self.spectrumDisplay = spectrumDisplay
        self.spectrumDisplayLabel = Label(self, "Current spectrumDisplay: %s" % spectrumDisplay.id, grid=(0, 0))

        # import the new strip plot widget - also used in backbone assignment and pick and assign module
        self._newStripPlotWidget = StripPlot(parent=self, mainWindow=self.mainWindow,
                                             includePeakLists=includePeakLists,
                                             includeNmrChains=includeNmrChains,
                                             includeNmrChainPullSelection=includeNmrChainPullSelection,
                                             includeSpectrumTable=includeSpectrumTable,
                                             defaultSpectrum=NO_STRIP,
                                             grid=(1, 0), gridSpan=(1, 3))

        ButtonList(self, ['Cancel', 'OK'], [self.reject, self._accept], grid=(2, 1), gridSpan=(1, 2))
        self.setFixedSize(self.sizeHint())

    @profile
    def _accept(self, dummy=None):
        """OK button pressed
        """
        listType = self._newStripPlotWidget.listButtons.getIndex()
        if listType is not None:
            with progressManager(self, 'Making Strip Plot...'):
                buttonType = self._newStripPlotWidget.listButtons.buttonTypes[listType]

                if buttonType == STRIPPLOT_PEAKS:
                    self._buildStrips(peaks=self.current.peaks)
                elif buttonType == STRIPPLOT_NMRRESIDUES:
                    self._buildStrips(nmrResidues=self.current.nmrResidues)
                elif buttonType == STRIPPLOT_NMRCHAINS:
                    if self._newStripPlotWidget.nmrChain:
                        self._buildStrips(nmrResidues=self._newStripPlotWidget.nmrChain.nmrResidues)

        self.accept()

    def _blockEvents(self, specDisplay):
        """Block all updates/signals/notifiers in the scene.
        """
        specDisplay.setUpdatesEnabled(False)
        specDisplay.blockSignals(True)
        # self.setBlankingAllNotifiers(True)

    def _unblockEvents(self, specDisplay):
        """Unblock all updates/signals/notifiers in the scene.
        """
        # self.setBlankingAllNotifiers(False)
        specDisplay.blockSignals(False)
        specDisplay.setUpdatesEnabled(True)

    # @contextmanager
    # def sceneBlocking(self):
    #     """Context manager to handle blocking, unblocking, resizing of the scene.
    #     """
    #     self._blockEvents()
    #     try:
    #         # pass control to the calling function
    #         yield
    #
    #     finally:
    #         self._unblockEvents()

    def _buildStrips(self, spectrumDisplays=None, peaks=None, nmrResidues=None):
        """Build the strips in the selected spectrumDisplays
        """
        spectrumDisplays = self._newStripPlotWidget.displaysWidget._getDisplays()

        autoClearMarks = self._newStripPlotWidget.autoClearMarksWidget.isChecked()
        sequentialStrips = self._newStripPlotWidget.sequentialStripsWidget.isChecked()
        markPositions = self._newStripPlotWidget.markPositionsWidget.isChecked()

        # loop through the spectrumDisplays
        for specDisplay in spectrumDisplays:

            self._blockEvents(specDisplay)      # doesn't make a difference?

            if peaks:
                specDisplay.makeStripPlot(peaks=peaks, nmrResidues=None,
                                          autoClearMarks=autoClearMarks,
                                          sequentialStrips=sequentialStrips,
                                          markPositions=markPositions
                                          )
            elif nmrResidues:
                specDisplay.makeStripPlot(peaks=None, nmrResidues=nmrResidues,
                                          autoClearMarks=autoClearMarks,
                                          sequentialStrips=sequentialStrips,
                                          markPositions=markPositions
                                          )

            self._unblockEvents(specDisplay)
            specDisplay.setColumnStretches(stretchValue=True, widths=True, minimumWidth=100)

    def _cleanupWidget(self):
        """Cleanup the notifiers that are left behind after the widget is closed
        """
        self._newStripPlotWidget._cleanupWidget()
        self.close()
