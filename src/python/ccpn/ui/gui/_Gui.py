import os
import subprocess
import platform

from ccpn.ui.gui.widgets import MessageDialog

# This import initializes relative paths for QT style-sheets.  Do not remove! GWV ????

from ccpn.util.Logging import getLogger
from ccpn.util.Path import aPath
from ccpn.util.decorators import logCommand

from ccpn.ui.gui.guiSettings import LIGHT, DARK



class _Gui(object):
    """
    All methods, to be retained for a 4.x refactored version
    """

    def _getMenuDefs(self):
        """:return the MenuDefs instance
        Subclassed for modification in various AnalysisAssign, AnalysisScreen, ... programmes
        """
        from ccpn.ui.gui.menus.MenuDefs import getMenuDefs
        return getMenuDefs()

    def _getColourScheme(self) -> str:
        """get the colourScheme as determined by arguments --dark, --light or preferences
        """
        _app = self.application
        if _app.args.darkColourScheme:
            colourScheme = DARK
        elif _app.args.lightColourScheme:
            colourScheme = LIGHT
        else:
            colourScheme = _app.preferences.general.colourScheme

        if colourScheme is None:
            raise RuntimeError('invalid colourScheme')

        return colourScheme

    def _getStyleSheet(self, colourScheme: str) -> str:
        """Get the stylesheet
        """
        from ccpn.framework.PathsAndUrls import widgetsPath

        _qssPath = widgetsPath / ('%sStyleSheet.qss' % colourScheme.capitalize())
        with _qssPath.open(mode='r') as fp:
            styleSheet = fp.read()

        if platform.system() == 'Linux':
            _qssPath = widgetsPath / ('%sAdditionsLinux.qss' % colourScheme.capitalize())
            with _qssPath.open(mode='r') as fp:
                additions = fp.read()
            styleSheet += additions

        return styleSheet

    #-----------------------------------------------------------------------------------------
    # Spectrum
    #-----------------------------------------------------------------------------------------

    @logCommand('ui.')
    def makeStripPlot(self, includePeakLists=True, includeNmrChains=True, includeNmrChainPullSelection=True):
        """Make a strip plot from peaks or nmrChains
        """
        if not self.project.peaks and not self.project.nmrResidues and not self.project.nmrChains:
            getLogger().warning('Cannot make strip plot, nothing to display')
            MessageDialog.showWarning('Cannot make strip plot,', 'nothing to display')
            return

        if self.current.strip is None or self.current.strip.isDeleted:
            MessageDialog.showWarning('Make Strip Plot', 'No selected spectrumDisplay')
            return

        from ccpn.ui.gui.popups.StripPlotPopup import StripPlotPopup
        popup = StripPlotPopup(parent=self.mainWindow, mainWindow=self.mainWindow,
                               spectrumDisplay=self.current.strip.spectrumDisplay,
                               includePeakLists=includePeakLists,
                               includeNmrChains=includeNmrChains,
                               includeNmrChainPullSelection=includeNmrChainPullSelection,
                               includeSpectrumTable=False)
        popup.exec_()

    def _flipArbitraryAxes(self, strip, usePosition=False):
        """Flip arbitrary axes of strip (defaults to current.strip)
        :param usePosition: Optionally use current cursor position
        """
        if strip is None:
            strip = self.current.strip

        if strip is None:
            getLogger().warning('Flip axes: No strip')
            MessageDialog.showWarning('Flip axes', 'No strip')
            return

        if strip.spectrumDisplay.is1D:
            getLogger().warning('Flip axes: not permitted on 1D spectra')
            MessageDialog.showWarning('Flip axes', 'Not permitted on 1D spectra')
            return

        from ccpn.ui.gui.popups.CopyStripFlippedAxesPopup import CopyStripFlippedSpectraPopup

        try:
            mDict = usePosition and self.current.mouseMovedDict[1]
            positions = [poss[0] if (poss := mDict.get(ax)) else None
                         for ax in strip.axisCodes] if usePosition else None
            popup = CopyStripFlippedSpectraPopup(parent=self.mainWindow, mainWindow=self.ui.mainWindow,
                                                 strip=strip, label=strip.id,
                                                 positions=positions)
            popup.exec_()

        except Exception as es:
            getLogger().warning(f'Cannot show popup: {es}')

    #-----------------------------------------------------------------------------------------
    # Help
    #-----------------------------------------------------------------------------------------

    def _systemOpen(self, path):
        """Open path to pdf file on system
        """
        from ccpn.util.Common import isWindowsOS, isMacOS
        from ccpn.framework.Preferences import getPreferences

        if isWindowsOS():
            os.startfile(path)
        elif isMacOS():
            subprocess.run(['open', path], check=True)
        else:
            _prefs = getPreferences()
            linuxCommand = _prefs.externalPrograms.PDFViewer
            # assume a linux and use the choice given in the preferences
            if linuxCommand and aPath(linuxCommand).is_file():

                try:
                    # NOTE:ED - this could be quite nasty, but can't think of another way to get Linux to open a pdf
                    subprocess.run([linuxCommand, path])

                except Exception as es:
                    getLogger().warning(f'Error opening PDFViewer. {es}')
                    MessageDialog.showWarning('Open File',
                                              f'Error opening PDFViewer. {es}\n'
                                              f'Check settings in Preferences->External Programs'
                                              )

            else:
                # raise TypeError('PDFViewer not defined for linux')
                MessageDialog.showWarning('Open File',
                                          'Please select PDFViewer in Preferences->External Programs')

    def _showHtmlFile(self, title, urlPath):
        """Display html files
        Optional program QT viewer or native webbrowser (currently disabled)
        depending on useNativeWebbrowser option in preferences
        """
        from ccpn.util.Common import isWindowsOS

        useNative = self.application.preferences.general.useNativeWebbrowser
        if not useNative:
            getLogger().debug('non-native HtmlModule has been disabled due to PyQT bugs')

        if True:
            import webbrowser
            import posixpath

            # may be a Path object
            urlPath = str(urlPath)

            urlPath = urlPath or ''
            if (urlPath.startswith('http://') or urlPath.startswith('https://')):
                pass
            elif urlPath.startswith('file://'):
                urlPath = urlPath[len('file://'):]
                urlPath = urlPath.replace(os.sep, posixpath.sep) if isWindowsOS() else f'file://{urlPath}'

            elif isWindowsOS():
                urlPath = urlPath.replace(os.sep, posixpath.sep)
            else:
                urlPath = f'file://{urlPath}'

            webbrowser.open(urlPath)

    def _showPath(self, path):
        """Show path
        """
        try:
            self._systemOpen(path)
        except Exception as es:
            getLogger().warning(f'Error opening {path}')

    def _showTutorialData(self):
        from ccpn.framework.PathsAndUrls import ccpnTutorials
        self._showHtmlFile("Tutorial Data", ccpnTutorials)

    def _showCCPNVideos(self):
        from ccpn.framework.PathsAndUrls import ccpnVideos
        self._showHtmlFile('Video Tutorials', ccpnVideos)
