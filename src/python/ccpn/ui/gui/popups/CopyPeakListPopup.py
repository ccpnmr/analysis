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
__dateModified__ = "$dateModified: 2022-01-25 16:31:24 +0000 (Tue, January 25, 2022) $"
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
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons, RadioButtonsWithSubCheckBoxes
from ccpn.ui.gui.widgets.RadioButton import CheckBoxCheckedText, CheckBoxCallbacks, CheckBoxTexts, CheckBoxTipTexts
from collections import OrderedDict as od

_OnlyPositionAndAssignments = 'Copy Position and Assignments only'
_IncludeAllPeakProperties   = 'Copy all existing properties'
_SnapToExtremum             = 'Snap to Extremum'
_RefitPeaks                 = 'Refit Peaks'
_RefitPeaksAtPosition       = 'Refit Peaks and preserve position'
_RecalculateVolume          = 'Recalculate Volume'
_tipTextOnlyPos = f'''Copy Peaks and include only the original Position and Assignments (if available).
                     \nAdditionally, execute the selected operations'''
_tipTextIncludeAll = f'''Copy Peaks and include all the original properties: 
                Position, Assignments, Heights, Linewidths, Volumes etc...'''



class CopyPeakListPopup(CcpnDialogMainWidget):
    def __init__(self, parent=None, mainWindow=None, title='Copy PeakList', spectrumDisplay=None,
                       selectItem=None, **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        if mainWindow:
            self.mainWindow = mainWindow
            self.application = self.mainWindow.application
            self.project = self.mainWindow.project
            self.current = self.application.current
        else:
            self.mainWindow = None
            self.application = None
            self.project = None
            self.current = None

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

        checkBoxTexts = [_SnapToExtremum, _RefitPeaks, _RefitPeaksAtPosition, _RecalculateVolume]

        checkBoxesDict = od([
                            (_OnlyPositionAndAssignments,
                             {
                             CheckBoxTexts: checkBoxTexts,
                             CheckBoxCheckedText: [_SnapToExtremum, _RefitPeaks, _RecalculateVolume],
                             CheckBoxTipTexts: [f'Perform the following action {i} on all peaks' for i in checkBoxTexts],
                             CheckBoxCallbacks: [self._subSelectionCallback] * len(checkBoxTexts)
                             }
                            ),
                            ])

        self.copyOptionsRadioButtons = RadioButtonsWithSubCheckBoxes(self.mainWidget,
                                                                     texts=[_OnlyPositionAndAssignments, _IncludeAllPeakProperties],
                                                                     selectedInd=0,
                                                                     tipTexts=[_tipTextOnlyPos, _tipTextIncludeAll],
                                                                     checkBoxesDictionary=checkBoxesDict,
                                                                     grid=(2, 0),
                                                                     )


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
        includeAllProperties = self.copyOptionsRadioButtons.getSelectedText() == _IncludeAllPeakProperties
        if self.sourcePeakList is not None:
            try:
                if self.targetSpectrum is not None:
                    newPeakList = self.sourcePeakList.copyTo(self.targetSpectrum, includeAllPeakProperties=includeAllProperties)
                    # need to execute further operations
                    ddValues = self.copyOptionsRadioButtons.get()
                    extraActionsTexts = ddValues.get(_OnlyPositionAndAssignments, [])
                    if _SnapToExtremum in extraActionsTexts:
                        self._snapPeaksToExtremum(newPeakList)
                    if _RefitPeaks in extraActionsTexts:
                        newPeakList.fitExistingPeaks(newPeakList.peaks)
                    if _RecalculateVolume in extraActionsTexts:
                        newPeakList.estimateVolumes()

            except Exception as es:
                getLogger().warning('Error copying peakList: %s' % str(es))
                showWarning(str(self.windowTitle()), str(es))

    def _populateSourcePeakListPullDown(self):
        """Populate the pulldown with the list of spectra in the project
        """
        if not self.project:
            return

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
        if not self.project:
            return

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
        if not self.current:
            return result

        if self.current.peak is not None:
            result = self.current.peak.peakList

        elif self.current.strip is not None and not self.current.strip.isDeleted:
            _spec = self.current.strip.spectra[0]
            result = _spec.peakLists[-1]

        elif len(self.project.peakLists)>0:
            result = self.project.peakLists[0]

        return result

    def _subSelectionCallback(self, value):
        clickedCheckBox = self.sender()
        ddValues = self.copyOptionsRadioButtons.get()
        extraActionsTexts = ddValues.get(_OnlyPositionAndAssignments, [])
        # if clickedCheckBox.getText() == _RefitPeaksAtPosition:
        #     if _SnapToExtremum in extraActionsTexts:
        #         self.copyOptionsRadioButtons.
        pass


        # if _SnapToExtremum and _RefitPeaksAtPosition in extraActionsTexts:


    def _snapPeaksToExtremum(self, peakList):
        # get the default from the preferences
        minDropFactor = self.application.preferences.general.peakDropFactor
        searchBoxMode = self.application.preferences.general.searchBoxMode
        searchBoxDoFit = self.application.preferences.general.searchBoxDoFit
        fitMethod = self.application.preferences.general.peakFittingMethod
        peaks = peakList.peaks
        with undoBlockWithoutSideBar():
            peaks.sort(key=lambda x: x.position[0], reverse=False)  # reorder peaks by position
            for peak in peaks:
                peak.snapToExtremum(halfBoxSearchWidth=4, halfBoxFitWidth=4,
                                    minDropFactor=minDropFactor, searchBoxMode=searchBoxMode,
                                    searchBoxDoFit=searchBoxDoFit, fitMethod=fitMethod)


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
