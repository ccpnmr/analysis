"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-01-24 19:33:14 +0000 (Mon, January 24, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar


class CopyPeakListPopup(CcpnDialogMainWidget):
    def __init__(self, parent=None, mainWindow=None, title='Copy PeakList', spectrumDisplay=None,
                       selectItem=None, **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        if mainWindow:
            self.mainWindow = mainWindow
            self.application = self.mainWindow.application
            self.project = self.mainWindow.project
        else:
            self.mainWindow = None
            self.application = None
            self.project = None

        self.spectrumDisplay = spectrumDisplay
        self.sourcePeakList = None
        self.targetSpectrum = None
        self.defaultPeakList = self._getDefaultPeakList() if selectItem is None else \
                               self.application.get(selectItem)

        self.setWidgets()
        self._populate()

        # enable the buttons
        self.setOkButton(callback=self._okClicked, tipText='Copy PeakList')
        self.setCloseButton(callback=self.reject, tipText='Close popup')
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)
        self.__postInit__()

    def setWidgets(self):
        self.sourcePeakListLabel = Label(self.mainWidget, 'Source PeakList', grid=(0, 0))
        self.sourcePeakListPullDown = PulldownList(self.mainWidget, grid=(0, 1),
                                                   callback=self._populateTargetSpectraPullDown)
        self.targetSpectraLabel = Label(self.mainWidget, 'Target Spectrum', grid=(1, 0))
        self.targetSpectraPullDown = PulldownList(self.mainWidget, grid=(1, 1))

    def _populate(self):
        self._populateSourcePeakListPullDown()
        self._populateTargetSpectraPullDown()

    def _okClicked(self):
        with undoBlockWithoutSideBar():
            self.sourcePeakList = self.project.getByPid(self.sourcePeakListPullDown.getText())
            self.targetSpectrum = self.project.getByPid(self.targetSpectraPullDown.getText())
            self._copyPeakListToSpectrum()
        self.accept()

    def _copyPeakListToSpectrum(self):
        if self.sourcePeakList is not None:
            try:
                if self.targetSpectrum is not None:
                    self.sourcePeakList.copyTo(self.targetSpectrum)

            except Exception as es:
                getLogger().warning('Error copying peakList: %s' % str(es))
                showWarning(str(self.windowTitle()), str(es))

    def _populateSourcePeakListPullDown(self):
        """Populate the pulldown with the list of spectra in the project
        """
        if len(self.project.peakLists) == 0:
            raise RuntimeError('Project has no PeakList\'s')

        sourcePullDownData = [str(pl.pid) for pl in self.project.peakLists]
        self.sourcePeakListPullDown.setData(sourcePullDownData)
        if self.defaultPeakList is not None:
           self.sourcePeakListPullDown.select(self.defaultPeakList.pid)
           self.sourcePeakList = self.defaultPeakList
        # self._selectDefaultPeakList()

    def _populateTargetSpectraPullDown(self, *args):
        """Populate the pulldown with the list of spectra on the selected spectrumDisplay and select the
        first visible spectrum
        """
        sourcePeakList = self.application.get(args[0]) if len(args)>0 else self.sourcePeakList
        if sourcePeakList is None:
            visibleSpectra = spectra = self.project.spectra
        else:
            _dimCount = sourcePeakList.spectrum.dimensionCount
            visibleSpectra = spectra = [spec for spec in self.project.spectra if spec.dimensionCount <= _dimCount]

            if self.spectrumDisplay is not None:
                _tmp = self.spectrumDisplay.strips[0].getVisibleSpectra()
                visibleSpectra = [spec for spec in _tmp if spec.dimensionCount <= _dimCount]

        #
        # if self.spectrumDisplay and self.spectrumDisplay.strips:
        #     orderedSpectra = self.spectrumDisplay.strips[0].getSpectra()
        #     visibleSpectra = self.spectrumDisplay.strips[0].getVisibleSpectra()

        if spectra:
            targetPullDownData = [str(sp.pid) for sp in spectra]
            self.targetSpectraPullDown.setData(targetPullDownData)

            if visibleSpectra:
                self.targetSpectraPullDown.select(visibleSpectra[0].pid)

    def _getDefaultPeakList(self):
        """:return the default PeakList based on current settings, or None
        """
        result = None

        if self.application.current.peak is not None:
            result = self.application.current.peak.peakList

        elif self.application.current.strip is not None and not self.application.current.strip.isDeleted:
            _spec = self.application.current.strip.spectra[0]
            result = _spec.peakLists[-1]

        elif len(self.project.peakLists)>0:
            result = self.project.peakLists[0]

        return result

    #GWV 11/12/2022: implementation change
    # def _selectDefaultPeakList(self):
    #     if self.application.current.peak is not None:
    #         defaultPeakList = self.application.current.peak.peakList
    #         self.sourcePeakListPullDown.select(defaultPeakList.pid)
    #         # print('Selected defaultPeakList: "current.peak.peakList" ',defaultPeakList) #Testing statement to be deleted
    #         return
    #     if self.application.current.strip is not None and not self.application.current.strip.isDeleted:
    #         if len(self.application.current.strip.spectra[0].peakLists)>0:
    #             defaultPeakList = self.application.current.strip.spectra[0].peakLists[-1]
    #         else:
    #             defaultPeakList = self.application.current.strip.spectra[0].newPeakList()
    #         self.sourcePeakListPullDown.select(defaultPeakList.pid)
    #         # print('Selected defaultPeakList: "current.strip.spectra[0].peakLists[-1]" ', defaultPeakList)  #Testing statement to be deleted
    #         return
    #     else:
    #         # why this else!
    #         if len(self.project.peakLists)>0:
    #             defaultPeakList = self.project.peakLists[0]
    #             self.sourcePeakListPullDown.select(defaultPeakList.pid)
    #         # print('Selected defaultPeakList: "self.project.spectra[0].peakLists[-1]" ', defaultPeakList) #Testing statement to be deleted
    #         return


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    import ccpn.core.testing.WrapperTesting as WT


    app = TestApplication()
    app.colourScheme = 'dark'

    thisWT = WT.WrapperTesting()
    thisWT.setUp()

    app.project = thisWT.project

    popup = CopyPeakListPopup()  # too many errors for testing here...

    popup.show()
    popup.raise_()

    app.start()

    WT.WrapperTesting.tearDown(thisWT)
