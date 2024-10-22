import os
import subprocess
import platform

from PyQt5 import QtWidgets, QtCore, QtGui

from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.Application import Application as PyQtApplication

# This import initializes relative paths for QT style-sheets.  Do not remove! GWV ????
from ccpn.ui.gui.guiSettings import FontSettings, consoleStyle
from ccpn.ui.gui.widgets.Icon import Icon

from ccpn.util.Logging import getLogger
from ccpn.util.Path import aPath
from ccpn.util.decorators import logCommand

from ccpn.ui.gui.guiSettings import Theme



class _Gui_V3_V4(object):
    """
    All methods, to be retained for a 4.x refactored version
    """

    def _initQtApp(self) -> PyQtApplication:
        # On the Mac (at least) it does not matter what you set the applicationName to be,
        # it will come out as the executable you are running (e.g. "python3")

        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

        # NOTE:ED - this is essential for multi-window applications
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts, True)

        # fm = QtGui.QSurfaceFormat()
        # fm.setSamples(4)
        # # NOTE:ED - Do not do this, they cause QT to exhibit strange behaviour
        # # fm.setSwapInterval(0)  # disable VSync
        # # fm.setSwapBehavior(QtGui.QSurfaceFormat.DoubleBuffer)
        # QtGui.QSurfaceFormat.setDefaultFormat(fm)

        _qtApp = PyQtApplication(self.application.applicationName,
                                 self.application.applicationVersion,
                                 organizationName='CCPN',
                                 organizationDomain='ccpn.ac.uk'
                                )

        # patch for icon sizes in menus, etc.
        styles = QtWidgets.QStyleFactory()
        myStyle = _MyAppProxyStyle(styles.create('fusion'))
        _qtApp.setStyle(myStyle)

        return _qtApp

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
            colourScheme = Theme.DARK
        elif _app.args.lightColourScheme:
            colourScheme = Theme.LIGHT
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


#=========================================================================================
# _MyAppProxyStyle
#=========================================================================================

# class _MyAppProxyStyle(QtWidgets.QProxyStyle):
#     """Class to handle resizing icons in menus
#     """
#
#     def drawControl(self, element, option, painter, widget=None):
#         if (element in {QtWidgets.QStyle.CE_MenuItem} and isinstance(option, QtWidgets.QStyleOptionMenuItem) and
#                 (_actionGeometries := getattr(widget, '_actionGeometries', None)) and
#                 (action := _actionGeometries.get(str(option.rect))) and
#                 (colour := getattr(action, '_foregroundColour', None))):
#             # Customise the foreground colour for the menu-item from the QAction
#             option.palette.setColor(option.palette.Text, colour)
#         return super().drawControl(element, option, painter, widget)
#
#     def standardIcon(self, standardIcon, option=None, widget=None) -> QtGui.QIcon:
#         # change the close-button of the line-edit to a cleaner icon, set by setClearButtonEnabled
#         if standardIcon == QtWidgets.QStyle.SP_LineEditClearButton:
#             return Icon('icons/close-lineedit')
#         return super().standardIcon(standardIcon, option, widget)


class _MyAppProxyStyle(QtWidgets.QProxyStyle):
    """Class to handle resizing icons in menus
    """

    # def drawPrimitive(self, element: QtWidgets.QStyle.PrimitiveElement,
    #                   option: QtWidgets.QStyleOption,
    #                   painter: QtGui.QPainter,
    #                   widget: typing.Optional[QtWidgets.QWidget] = ...) -> None:
    #     focus = False
    #     if element in {QtWidgets.QStyle.PE_FrameLineEdit,
    #                    QtWidgets.QStyle.PE_FrameFocusRect,
    #                    QtWidgets.QStyle.PE_PanelButtonCommand,
    #                    }:
    #         focus = option.state & QtWidgets.QStyle.State_HasFocus
    #         option.state &= ~(QtWidgets.QStyle.State_HasFocus | QtWidgets.QStyle.State_Selected)
    #         # Customise the highlight color for a soft background
    #         if Base._highlightMid is not None:
    #             option.palette.setColor(option.palette.Highlight, Base._highlightMid)
    #     if element == QtWidgets.QStyle.PE_FrameFocusRect and isinstance(widget, QtWidgets.QPushButton):
    #         # replace the QPushButton focus with just a border
    #         if (efb := getattr(widget, '_enableFocusBorder', None)) is None or efb is True:
    #             self._drawBorder(element, painter, widget, col=Base._highlightVivid)
    #         return
    #     super().drawPrimitive(element, option, painter, widget)
    #     if focus and element in {QtWidgets.QStyle.PE_FrameLineEdit,
    #                              }:
    #         # draw new focus-border
    #         self._drawBorder(element, painter, widget, col=Base._highlightVivid)

    def drawControl(self, element, option, painter, widget=None):
        # if element in {QtWidgets.QStyle.CE_TabBarTab,
        #                }:
        #     # Customise the highlight color for the tab-widget
        #     if Base._highlightVivid is not None:
        #         option.palette.setColor(option.palette.Highlight, Base._highlightVivid)
        if (element in {QtWidgets.QStyle.CE_MenuItem,} and
              isinstance(option, QtWidgets.QStyleOptionMenuItem) and
                (_actionGeometries := getattr(widget, '_actionGeometries', None)) and
                (action := _actionGeometries.get(str(option.rect))) and
                (colour := getattr(action, '_foregroundColour', None))):
            # Customise the foreground colour for the menu-item from the QAction
            # - menu-items don't have a stylesheet or palette
            option.palette.setColor(option.palette.Text, colour)
        super().drawControl(element, option, painter, widget)
        # if element in {QtWidgets.QStyle.CE_ItemViewItem, } and (option.state & QtWidgets.QStyle.State_HasFocus):
        #     # draw border inside the listWidget/listView/TreeView
        #     #   - draws border inside pulldowns though, shame :(
        #     self._drawBorder(element, painter, widget, col=Base._highlightVivid)

    def drawComplexControl(self, control: QtWidgets.QStyle.ComplexControl,
                           option: QtWidgets.QStyleOptionComplex,
                           painter: QtGui.QPainter,
                           widget: QtWidgets.QWidget | None = ...) -> None:
        focus = None
        if control in {QtWidgets.QStyle.CC_ComboBox,
                       QtWidgets.QStyle.CC_SpinBox,
                       }:
            focus = option.state & QtWidgets.QStyle.State_HasFocus
            option.state &= ~QtWidgets.QStyle.State_HasFocus
            if control in {QtWidgets.QStyle.CC_ComboBox,}:
                # hack to set the drop-arrow colour
                # using window-text allows setting the text colour on non-editable combobox
                option.palette.setColor(option.palette.ButtonText,
                                        option.palette.color(QtGui.QPalette.Active,
                                                             QtGui.QPalette.ColorRole(QtGui.QPalette.WindowText)))
        # elif control in {QtWidgets.QStyle.CC_Slider,} and Base._highlightVivid is not None:
        #     option.palette.setColor(option.palette.Highlight, Base._highlightVivid)
        super().drawComplexControl(control, option, painter, widget)
        if focus:
            # draw new focus-border
            self._drawBorder(control, painter, widget,
                             col=option.palette.highlight().color())

    @staticmethod
    def _drawBorder(control, p, widget, col=None):
        p.save()
        try:
            wind = widget.rect()
            if control == QtWidgets.QStyle.CC_SpinBox:
                # not sure why the border is off slightly
                wind = wind.adjusted(0, 1, 0, -1)  # x1, y1 - x2, y2
            elif control == QtWidgets.QStyle.CE_ItemViewItem:
                # border is off because the border-width is outside the widget :|
                wind = wind.adjusted(-1, -1, -1, -1)
            # paint the new border
            p.translate(0.5, 0.5)  # move to pixel-centre
            p.setRenderHint(QtGui.QPainter.Antialiasing, True)
            col = col or QtGui.QColor('red')
            col.setAlpha(40)  # feint must be done first so that QSlider draws correctly
            p.setPen(col)
            p.drawRoundedRect(wind.adjusted(1, 1, -2, -2), 1.7, 1.7)
            col.setAlpha(255)
            p.setPen(col)
            p.drawRoundedRect(wind.adjusted(0, 0, -1, -1), 2, 2)
        except Exception:
            ...
        finally:
            p.translate(-0.5, -0.5)
            p.restore()

    def standardIcon(self, standardIcon, option=None, widget=None) -> QtGui.QIcon:
        # change the close-button of the line-edit to a cleaner icon, set by setClearButtonEnabled
        if standardIcon == QtWidgets.QStyle.SP_LineEditClearButton:
            return Icon('icons/close-lineedit')
        return super().standardIcon(standardIcon, option, widget)
