from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.util.Logging import getLogger
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, notificationEchoBlocking
import ccpn.ui.gui.widgets.CompoundWidgets as cw
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.framework.Application import getApplication
from ccpn.ui.gui.widgets.Frame import Frame


class FlyaPeakCopyPopup(CcpnDialogMainWidget):
    def __init__(self, parent=None, mainWindow=None, title='Quick Flya PeakLists Copy', **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = getApplication()
        self.project = self.application.project if self.application else None

        # Find matching spectrum pairs
        self.spectrumPairs = self._findMatchingSpectra()

        self.setWidgets()
        self._populate()

        # enable the buttons
        self.setOkButton(callback=self._okClicked, tipText='Copy PeakLists')
        self.setCloseButton(callback=self.reject, tipText='Close popup')
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)

    def _findMatchingSpectra(self):
        """Find all FLYA spectra and their matching counterparts"""
        pairs = []
        all_spectra = self.project.spectra

        # Get all FLYA spectra
        flya_spectra = [sp for sp in all_spectra if '@FLYA' in sp.name]

        # For each FLYA spectrum, find its counterpart
        for flya_spec in flya_spectra:
            # Extract base name (e.g., 'nhsqc' from 'N15HSQC_nhsqc_@FLYA_asn')
            base_name = self._extractBaseName(flya_spec.name)

            # Find matching spectrum
            for spec in all_spectra:
                if spec.name.lower() == base_name.lower() and spec != flya_spec:
                    pairs.append((flya_spec, spec))
                    break

        return pairs

    def _extractBaseName(self, flya_name):
        """Extract the base spectrum name from FLYA spectrum name"""
        # Remove FLYA part and anything after it
        base = flya_name.split('@FLYA')[0]
        # Remove any prefixes before the actual spectrum type
        parts = base.split('_')
        for part in reversed(parts):
            if part:  # take the last non-empty part
                return part
        return base

    def setWidgets(self):
        current_row = 0

        # Information label at the top
        info_text = "Note: Copied peaks will be snap to extrema, not fitting will be performed\n"
        cw.Label(self.mainWidget, text=info_text, grid=(current_row, 0), style='italic', gridSpan=(1, 3))
        current_row += 1

        # Add some vertical spacing
        cw.Label(self.mainWidget, text="", grid=(current_row, 0))  # Empty spacer
        current_row += 1

        # Header row
        cw.Label(self.mainWidget, text="Include", grid=(current_row, 0), style='bold')
        cw.Label(self.mainWidget, text="Source Spectrum (@FLYA)", grid=(current_row, 1), style='bold')
        cw.Label(self.mainWidget, text="Target Spectrum", grid=(current_row, 2), style='bold')
        current_row += 1

        # Create widgets for each pair
        self.checkboxes = []
        self.flyaLabels = []
        self.targetPulldowns = []

        for flya_spec, target_spec in self.spectrumPairs:
            # Checkbox
            cb = CheckBox(self.mainWidget, grid=(current_row, 0), checked=True)
            self.checkboxes.append(cb)

            # FLYA spectrum label
            flya_label = cw.Label(self.mainWidget, text=flya_spec.name, grid=(current_row, 1))
            self.flyaLabels.append(flya_label)

            # Target spectrum pulldown with all spectra, but matched one first
            all_spectra = sorted(self.project.spectra,
                                 key=lambda x: x != target_spec)  # Put target_spec first
            target_pulldown = PulldownList(self.mainWidget, grid=(current_row, 2))
            target_pulldown.setData([sp.pid for sp in all_spectra])
            target_pulldown.select(target_spec.pid)
            self.targetPulldowns.append(target_pulldown)

            current_row += 1

            # Add some spacing between rows
            # cw.Label(self.mainWidget, text="", grid=(current_row, 0))  # Empty spacer
            current_row += 1

    def _populate(self):
        pass

    def _okClicked(self):
        if not self.spectrumPairs:
            showWarning("No matches", "No matching FLYA spectra found in project")
            return

        with undoBlockWithoutSideBar():
            errors = []

            for i, (flya_spec, _) in enumerate(self.spectrumPairs):
                if self.checkboxes[i].isChecked():
                    target_spec = self.project.getByPid(self.targetPulldowns[i].getText())

                    try:
                        if not flya_spec.peakLists:
                            raise Exception(f"No peak lists found in {flya_spec.name}")

                        flya_peaklist = flya_spec.peakLists[-1]
                        new_peaklist = flya_peaklist.copyTo(target_spec, includeAllPeakProperties=False)

                        self._snapPeaksToExtremum(new_peaklist)
                        # temporalrly suspended
                        # self._refitPeaks(new_peaklist)

                    except Exception as es:
                        errors.append(f"• {flya_spec.name} → {target_spec.name}: {str(es)}")

            if errors:
                _msg = (f'Some operations failed:\n\n' + '\n'.join(errors))
                showWarning(str(self.windowTitle()), _msg)

        self.accept()

    # temporalrly suspended
    # def _refitPeaks(self, peakList, keepPosition=False):
    #     peaks = peakList.peaks
    #     fitMethod = self.application.preferences.general.peakFittingMethod
    #     getLogger().info('Refitting peaks')
    #     with undoBlockWithoutSideBar():
    #         with notificationEchoBlocking():
    #             for peak in peaks:
    #                 peak.fit(fitMethod=fitMethod, keepPosition=keepPosition)

    def _snapPeaksToExtremum(self, peakList):
        minDropFactor = self.application.preferences.general.peakDropFactor
        searchBoxMode = self.application.preferences.general.searchBoxMode
        searchBoxDoFit = self.application.preferences.general.searchBoxDoFit
        fitMethod = self.application.preferences.general.peakFittingMethod
        peaks = peakList.peaks
        getLogger().info('Snapping Peaks To Extremum.')
        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                peaks.sort(key=lambda x: x.position[0], reverse=False)
                for peak in peaks:
                    peak.snapToExtremum(halfBoxSearchWidth=4, halfBoxFitWidth=4,
                                        minDropFactor=minDropFactor, searchBoxMode=searchBoxMode,
                                        searchBoxDoFit=searchBoxDoFit, fitMethod=fitMethod)


if __name__ == '__main__':
    popup = FlyaPeakCopyPopup()
    popup.exec_()