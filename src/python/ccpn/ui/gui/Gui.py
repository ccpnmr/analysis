"""
The top-level Gui class for all user interactions
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2025-01-10 16:38:46 +0000 (Fri, January 10, 2025) $"
__version__ = "$Revision: 3.3.0.develop $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Wayne Boucher $"
__date__ = "$Date: 2017-03-16 18:20:01 +0000 (Thu, March 16, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import typing
import re
import json
from PyQt5 import QtWidgets, QtCore, QtGui
from functools import partial

from ccpn.framework.Application import getApplication
from ccpn.framework.PathsAndUrls import CCPN_DIRECTORY_SUFFIX, CCPN_SAVEAS_SUB_DIRECTORIES
from ccpn.framework.lib.DataLoaders.DataLoaderABC import _checkPathForDataLoader
from ccpn.framework.Preferences import getPreferences, USER_WORKING_PATH

from ccpn.core.Project import Project
from ccpn.core.lib.ContextManagers import (
    notificationEchoBlocking, catchExceptions,
    logCommandManager, undoStackBlocking, busyHandler, undoStack
)
from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC

from ccpn.ui.Ui import Ui
from ccpn.ui.gui import Layout
# from ccpn.ui.gui.guiSettings import LIGHT, DARK

from ccpn.ui.gui.modules.CcpnModule import CcpnModule

from ccpn.ui.gui.popups.RegisterPopup import RegisterPopup, NewTermsConditionsPopup
from ccpn.ui.gui.widgets.Application import Application as PyQtApplication
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets import FileDialog
from ccpn.ui.gui.widgets.Font import getSystemFonts
from ccpn.ui.gui.popups.ImportStarPopup import StarImporterPopup

# This import initializes relative paths for QT style-sheets.  Do not remove! GWV ????
from ccpn.ui.gui.guiSettings import (FontSettings, consoleStyle, getTheme,
                                     Theme, setColourScheme)
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.lib.TipOfTheDayManager import TipOfTheDayManager

from ccpn.util.Logging import getLogger
from ccpn.util import Logging, Register
from ccpn.util.Path import aPath, Path
from ccpn.util.decorators import logCommand

from ccpnmodel.ccpncore.memops.ApiError import ApiError

# _Gui_V3_V4 contains code shared between V3 and V4
from ccpn.ui.gui._Gui_V3_V4 import _Gui_V3_V4


#-----------------------------------------------------------------------------------------
# Subclass the exception hook for PyQT
#-----------------------------------------------------------------------------------------

def _ccpnExceptionhook(ccpnType, value, tback):
    """This because PyQT raises and catches exceptions,
    but doesn't pass them along instead makes the program crashing miserably.
    """
    if (application := getApplication()):
        if application._isInDebugMode:
            sys.stderr.write('_ccpnExceptionhook: type = %s\n' % ccpnType)
            sys.stderr.write('_ccpnExceptionhook: value = %s\n' % value)
            sys.stderr.write('_ccpnExceptionhook: tback = %s\n' % tback)

        # # this is crashing on Windows 10 Enterprise :|
        # if application.hasGui:
        #     title = f'{str(ccpnType)[8:-2]}:'
        #     text = str(value)
        #     MessageDialog.showError(title=title, message=text)

        if application.project and not application.project.isReadOnly:
            application.project._updateLoggerState(readOnly=False)

    sys.__excepthook__(ccpnType, value, tback)

sys.excepthook = _ccpnExceptionhook

#-----------------------------------------------------------------------------------------
# un/suppress QT messages
#-----------------------------------------------------------------------------------------
def _qtMessageHandler(*errors):
    for err in errors:
        getLogger().warning(f'{consoleStyle.fg.red}QT error: {err}{consoleStyle.reset}')

QtCore.qInstallMessageHandler(_qtMessageHandler)

#-----------------------------------------------------------------------------------------

MAXITEMLOGGING = 4
MAXITEMLOADING = 5
MAXITEMDEPTH = 5

#-----------------------------------------------------------------------------------------
# Gui Class
#-----------------------------------------------------------------------------------------

# --> to _Gui_V3_V4
# class _MyAppProxyStyle(QtWidgets.QProxyStyle):
#     """Class to handle resizing icons in menus
#     """
#
#     # def drawPrimitive(self, element: QtWidgets.QStyle.PrimitiveElement,
#     #                   option: QtWidgets.QStyleOption,
#     #                   painter: QtGui.QPainter,
#     #                   widget: typing.Optional[QtWidgets.QWidget] = ...) -> None:
#     #     focus = False
#     #     if element in {QtWidgets.QStyle.PE_FrameLineEdit,
#     #                    QtWidgets.QStyle.PE_FrameFocusRect,
#     #                    QtWidgets.QStyle.PE_PanelButtonCommand,
#     #                    }:
#     #         focus = option.state & QtWidgets.QStyle.State_HasFocus
#     #         option.state &= ~(QtWidgets.QStyle.State_HasFocus | QtWidgets.QStyle.State_Selected)
#     #         # Customise the highlight color for a soft background
#     #         if Base._highlightMid is not None:
#     #             option.palette.setColor(option.palette.Highlight, Base._highlightMid)
#     #     if element == QtWidgets.QStyle.PE_FrameFocusRect and isinstance(widget, QtWidgets.QPushButton):
#     #         # replace the QPushButton focus with just a border
#     #         if (efb := getattr(widget, '_enableFocusBorder', None)) is None or efb is True:
#     #             self._drawBorder(element, painter, widget, col=Base._highlightVivid)
#     #         return
#     #     super().drawPrimitive(element, option, painter, widget)
#     #     if focus and element in {QtWidgets.QStyle.PE_FrameLineEdit,
#     #                              }:
#     #         # draw new focus-border
#     #         self._drawBorder(element, painter, widget, col=Base._highlightVivid)
#
#     def drawControl(self, element, option, painter, widget=None):
#         # if element in {QtWidgets.QStyle.CE_TabBarTab,
#         #                }:
#         #     # Customise the highlight color for the tab-widget
#         #     if Base._highlightVivid is not None:
#         #         option.palette.setColor(option.palette.Highlight, Base._highlightVivid)
#         if (element in {QtWidgets.QStyle.CE_MenuItem,} and
#               isinstance(option, QtWidgets.QStyleOptionMenuItem) and
#                 (_actionGeometries := getattr(widget, '_actionGeometries', None)) and
#                 (action := _actionGeometries.get(str(option.rect))) and
#                 (colour := getattr(action, '_foregroundColour', None))):
#             # Customise the foreground colour for the menu-item from the QAction
#             # - menu-items don't have a stylesheet or palette
#             option.palette.setColor(option.palette.Text, colour)
#         super().drawControl(element, option, painter, widget)
#         # if element in {QtWidgets.QStyle.CE_ItemViewItem, } and (option.state & QtWidgets.QStyle.State_HasFocus):
#         #     # draw border inside the listWidget/listView/TreeView
#         #     #   - draws border inside pulldowns though, shame :(
#         #     self._drawBorder(element, painter, widget, col=Base._highlightVivid)
#
#     def drawComplexControl(self, control: QtWidgets.QStyle.ComplexControl,
#                            option: QtWidgets.QStyleOptionComplex,
#                            painter: QtGui.QPainter,
#                            widget: typing.Optional[QtWidgets.QWidget] = ...) -> None:
#         focus = None
#         if control in {QtWidgets.QStyle.CC_ComboBox,
#                        QtWidgets.QStyle.CC_SpinBox,
#                        }:
#             focus = option.state & QtWidgets.QStyle.State_HasFocus
#             option.state &= ~QtWidgets.QStyle.State_HasFocus
#             if control in {QtWidgets.QStyle.CC_ComboBox,}:
#                 # hack to set the drop-arrow colour
#                 # using window-text allows setting the text colour on non-editable combobox
#                 option.palette.setColor(option.palette.ButtonText,
#                                         option.palette.color(QtGui.QPalette.Active,
#                                                              QtGui.QPalette.ColorRole(QtGui.QPalette.WindowText)))
#         # elif control in {QtWidgets.QStyle.CC_Slider,} and Base._highlightVivid is not None:
#         #     option.palette.setColor(option.palette.Highlight, Base._highlightVivid)
#         super().drawComplexControl(control, option, painter, widget)
#         if focus:
#             # draw new focus-border
#             self._drawBorder(control, painter, widget,
#                              col=option.palette.highlight().color())
#
#     @staticmethod
#     def _drawBorder(control, p, widget, col=None):
#         p.save()
#         try:
#             wind = widget.rect()
#             if control == QtWidgets.QStyle.CC_SpinBox:
#                 # not sure why the border is off slightly
#                 wind = wind.adjusted(0, 1, 0, -1)  # x1, y1 - x2, y2
#             elif control == QtWidgets.QStyle.CE_ItemViewItem:
#                 # border is off because the border-width is outside the widget :|
#                 wind = wind.adjusted(-1, -1, -1, -1)
#             # paint the new border
#             p.translate(0.5, 0.5)  # move to pixel-centre
#             p.setRenderHint(QtGui.QPainter.Antialiasing, True)
#             col = col or QtGui.QColor('red')
#             col.setAlpha(40)  # feint must be done first so that QSlider draws correctly
#             p.setPen(col)
#             p.drawRoundedRect(wind.adjusted(1, 1, -2, -2), 1.7, 1.7)
#             col.setAlpha(255)
#             p.setPen(col)
#             p.drawRoundedRect(wind.adjusted(0, 0, -1, -1), 2, 2)
#         except Exception:
#             ...
#         finally:
#             p.translate(-0.5, -0.5)
#             p.restore()
#
#     def standardIcon(self, standardIcon, option=None, widget=None) -> QtGui.QIcon:
#         # change the close-button of the line-edit to a cleaner icon, set by setClearButtonEnabled
#         if standardIcon == QtWidgets.QStyle.SP_LineEditClearButton:
#             return Icon('icons/close-lineedit')
#         return super().standardIcon(standardIcon, option, widget)
#
#
# #=========================================================================================
# # Gui
# #=========================================================================================
#
#
# def getFontSettings():
#     """:return the font settings object, intialised by Gui or None if non-gui
#     """
#     app = getApplication()
#     if app.hasGui:
#         return app.ui._fontSettings
#     else:
#         return None
#
#
# class Gui(Ui, _Gui):
#     """Top class for the GUI interface
#     """
#
#     _hasGui = True
#
#     def __init__(self, application):
#
#         # sets self.mainWindow (None), self.application and self.pluginModules
#         Ui.__init__(self, application)
#
#         self._fontSettings = FontSettings(application.preferences)
#
#         # defined by _changeThemeInstant()
#         self._themeStyle = None
#         self._themeColour = None
#         self._themeSDStyle = None
#
#         # Get menu definitions; subclassed by various application-specific Gui's
#         self._menuDefs = self._getMenuDefs()
#
#         self._initQtApp()
#
#     def _initQtApp(self):
#         # On the Mac (at least) it does not matter what you set the applicationName to be,
#         # it will come out as the executable you are running (e.g. "python3")
#
#         QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
#         QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
#
#         # NOTE:ED - this is essential for multi-window applications
#         QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts, True)
#         # experimental - makes a mess!
#         # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseStyleSheetPropagationInWidgetStyles, True)
#
#         # fm = QtGui.QSurfaceFormat()
#         # fm.setSamples(4)
#         # # NOTE:ED - Do not do this, they cause QT to exhibit strange behaviour
#         # #     - think is QT bug when recompiling :|
#         # # fm.setSwapInterval(0)  # disable VSync
#         # # fm.setSwapBehavior(QtGui.QSurfaceFormat.DoubleBuffer)
#         # QtGui.QSurfaceFormat.setDefaultFormat(fm)
#
#         self.qtApp = Application(self.application.applicationName,
#                                  self.application.applicationVersion,
#                                  organizationName='CCPN', organizationDomain='ccpn.ac.uk')
#         # patch for icon sizes in menus, etc.
#         styles = QtWidgets.QStyleFactory()
#         myStyle = _MyAppProxyStyle(styles.create('fusion'))
#         self.qtApp.setStyle(myStyle)
#
#         # override the dark/light theme
#         self._changeThemeInstant()
#
#         # read the current system-fonts
#         getSystemFonts()
#
#     def _getMenuDefs(self):
#         """:return the MenuDefs instance
#         Subclassed for modification in various AnalysisAssign, AnalysisScreen, ... programmes
#         """
#         from ccpn.ui.gui.Menus import getMenuDefs
#
#         return getMenuDefs()
#
#     def _changeThemeInstant(self, theme: str=None, colour: str=None, themeSD: str=None):
#         """Set the light/dark palette in single step.
#         0 - dark, 1 - light, 2 - default = follow OS/application
#         """
#         prefsApp = self.application.preferences.appearance
#         prefsGen = self.application.preferences.general
#
#         _th, _col, _thSD = getTheme()  # should have been set on creation
#         if theme is None: theme = _th.dataValue
#         if themeSD is None: themeSD = _thSD.dataValue
#         if colour is None: colour = _col
#
#         if not isinstance(theme, Theme) and theme not in Theme.dataValues():
#             raise ValueError(f'{self.__class__.__name__}._changeThemeInstant: theme not in {Theme.dataValues()}')
#         if not isinstance(themeSD, Theme) and themeSD not in Theme.dataValues():
#             raise ValueError(f'{self.__class__.__name__}._changeThemeInstant: themeSD not in {Theme.dataValues()}')
#         if not isinstance(colour, str):
#             raise TypeError(f'{self.__class__.__name__}._changeThemeInstant: colour not of type str')
#         try:
#             # test the colour
#             QtGui.QColor(colour)
#         except Exception:
#             raise ValueError(f'{self.__class__.__name__}._changeThemeInstant: colour {colour!r} not valid')
#
#         getLogger().debug(f'{consoleStyle.fg.darkblue}==> start palette-change event.{consoleStyle.reset}')
#         # set highlight to the required highlighting colour
#         # set the theme in preferences
#         th = Theme.getByDataValue(theme)
#         thSD = Theme.getByDataValue(themeSD)
#         prefsApp.themeStyle = th.dataValue  # application theme
#         prefsApp.themeColour = colour
#         prefsGen.colourScheme = thSD.dataValue  # spectrumDisplay theme
#
#         if pal := setColourScheme(th, colour, thSD):
#             self.qtApp.setPalette(pal)
#             # QtCore.QTimer.singleShot(0, partial(self.qtApp.setPalette, pal))
#             QtCore.QTimer.singleShot(0, partial(self.qtApp.sigPaletteChanged.emit, pal,
#                                               prefsApp.themeStyle,
#                                               prefsApp.themeColour,
#                                               prefsGen.colourScheme)
#                                      )
#         getLogger().debug(f'{consoleStyle.fg.darkblue}==> end palette-change event.{consoleStyle.reset}')
#
#     @staticmethod
#     def _interpolateColor(color1, color2, factor):
#         """Interpolate between two QColor objects.
#         """
#         r = color1.red() + (color2.red() - color1.red()) * factor
#         g = color1.green() + (color2.green() - color1.green()) * factor
#         b = color1.blue() + (color2.blue() - color1.blue()) * factor
#         a = color1.alpha() + (color2.alpha() - color1.alpha()) * factor
#         return QtGui.QColor(int(r), int(g), int(b), int(a))
#
#     def _updatePalette(self):
#         MAXSTEPS = 3
#         if self._paletteStep > MAXSTEPS:
#             self._paletteTimer.stop()
#             self._paletteTimer = None
#             getLogger().debug(f'{consoleStyle.fg.darkblue}==> end palette-change event.{consoleStyle.reset}')
#             return
#         # if self._paletteStep >= MAXSTEPS:
#         #     self.mainWindow._blockPaletteChange = 0
#         # set highlight to the required highlighting colour
#         groups = [QtGui.QPalette.Active, QtGui.QPalette.Inactive, QtGui.QPalette.Disabled]
#         pal = self.qtApp.palette()
#         for role, cols in self._nextPalette.items():
#             for group, col in zip(groups, cols):
#                 newCol = self._interpolateColor(pal.color(group, role),
#                                                 QtGui.QColor(col),
#                                                 self._paletteStep / MAXSTEPS)
#                 pal.setColor(group, role, newCol)
#         self.qtApp.setPalette(pal)
#         self._paletteStep += 1
#
#     @property
#     def theme(self):
#         """Return the current theme as dark/light.
#         """
#         pal = self.qtApp.palette()
#         base = pal.base().color().lightness()  # use as a guide for light/dark theme
#         return 'dark' if base < 127 else 'light'
#
#     def setTheme(self, theme: str | int = 'light'):
#         """Set the new light/dark theme.
#         theme = 0|'dark' for dark, 1|'light' for light.
#         """
#         themeStates = {'dark': 0,
#                        'light': 1,
#                        0 : 0,
#                        1 : 1}
#         if theme not in themeStates:
#             raise ValueError(f'{self.__class__.__name__}.setTheme: '
#                              f'theme must be in {json.dumps(list(themeStates.keys()))}')
#         pal = self.qtApp.palette()
#         base = pal.base().color().lightness()  # use as a guide for light/dark theme
#         if int(base > 127) != themeStates[theme]:
#             self._changeThemeInstant(themeStates[theme])


class Gui(Ui, _Gui_V3_V4):
    """Top class for the GUI interface
    _Gui_V3_V4 contains methods shared between V3 and V4
    """

    _hasGui = True

    def __init__(self, application):

        # sets self.mainWindow (None), self.application and self.pluginModules
        Ui.__init__(self, application)

        self._fontSettings = FontSettings(application.preferences)  # used by getFontSettings in Font.py
        self._colourScheme = self._getColourScheme()
        self._styleSheet = self._getStyleSheet(self._colourScheme)

        # Get menu definitions; _getMenuDefs() subclassed by various application-specific Gui's
        self._menuDefs = self._getMenuDefs()

        self._qtApp = self._initQtApp()

        # referenced by _changeThemeInstant()
        self._themeStyle = None
        self._themeColour = None
        self._themeSDStyle = None

        # override the dark/light theme
        self._changeThemeInstant()

        # read the current system-fonts
        getSystemFonts()

        self._tipOfTheDayManager = TipOfTheDayManager(gui=self, preferences=application.preferences)

    def _initialise(self, mainWindow):
        """UI operations done after every project load/create
        """
        if mainWindow is None:
            raise ValueError('Gui.initialize(): Undefined mainWindow')

        # The super() call sets the linkage to mainWindow
        super()._initialise(mainWindow=mainWindow)

        with notificationEchoBlocking():
            # with undoStackBlocking(debugText='Gui.initialize'):
            # Set up mainWindow
            self._setupMainWindow()
            self._restoreSpectrumDisplayModules()
            self._makeActiveWindow()

    def _restoreSpectrumDisplayModules(self):
        """Code from Framework/Project, restoring spectrumDisplay's
        """
        from ccpn.ui.gui.lib import GuiStrip

        project = self.project
        mainWindow = self.mainWindow
        current = self.application.current
        preferences = self.application.preferences

        _logger = getLogger()
        # 20191113:ED Initial insertion of spectrumDisplays into the moduleArea
        try:
            insertPoint = mainWindow.moduleArea
            for spectrumDisplay in mainWindow.spectrumDisplays:
                # mainWindow.moduleArea.addModule(spectrumDisplay, position='right', relativeTo=insertPoint)
                mainWindow._addModule(module=spectrumDisplay, position='right', relativeTo=insertPoint)
                insertPoint = spectrumDisplay

        except Exception as es:
            _logger.debug(f'Restoring {spectrumDisplay} failed: {es}')
            _logger.warning('Impossible to restore SpectrumDisplays')

        try:
            if preferences.general.restoreLayoutOnOpening:
                Layout.restoreLayout(mainWindow, mainWindow._getLayoutDict(), restoreSpectrumDisplays=False)
        except Exception as e:
            _logger.debug(f'Restoring layout failed: {es}')
            _logger.warning(f'Unable to restore Layout {e}')

        # check that the top moduleArea is correctly formed - strange special case when all modules have
        #   been moved to tempAreas
        mArea = mainWindow.moduleArea
        if mArea.topContainer is not None and mArea.topContainer._container is None:
            _logger.debug('Correcting empty topContainer')
            mArea.topContainer = None

        try:
            # initialise any colour changes before generating gui strips
            self._correctColours()
        except Exception as es:
            _logger.debug(f'Correcting colours failed: {es}')
            _logger.warning(f'Error setting colours - {es}')

        # Initialise Strips
        for spectrumDisplay in mainWindow.spectrumDisplays:
            try:
                _badStrip = False
                for si, strip in enumerate(spectrumDisplay.orderedStrips):

                    # temporary to catch bad strips from ordering bug
                    if not strip:
                        continue

                    # GWV 15/2/24: Adapted from Code in Project._restoreObject
                    if not strip.axes:
                        # set the border to red
                        spectrumDisplay.mainWidget.setStyleSheet('Frame { border: 3px solid #FF1234; }')
                        spectrumDisplay.mainWidget.setEnabled(False)
                        spectrumDisplay.setEnabled(False)

                        _logger.error(
                                f'Strip {strip} contains bad axes - please close SpectrumDisplay {spectrumDisplay} outlined in red.'
                                )
                        _badStrip = True
                        break

                    # get the new tilePosition of the strip - tilePosition is always (x, y) relative to screen stripArrangement
                    #                                       changing screen arrangement does NOT require flipping tilePositions
                    #                                       i.e. Y = (across, down); X = (down, across)
                    #                                       - check delete/undo/redo strips
                    tilePosition = strip.tilePosition

                    # move to the correct place in the widget - check stripDirection to display as row or column
                    if spectrumDisplay.stripArrangement == 'Y':
                        if True:  # tilePosition is None:
                            spectrumDisplay.stripFrame.layout().addWidget(strip, 0, si)  #stripIndex)
                            strip.tilePosition = (0, si)
                        # else:
                        #     spectrumDisplay.stripFrame.layout().addWidget(strip, tilePosition[0], tilePosition[1])

                    elif spectrumDisplay.stripArrangement == 'X':
                        if True:  #tilePosition is None:
                            spectrumDisplay.stripFrame.layout().addWidget(strip, si, 0)  #stripIndex)
                            strip.tilePosition = (0, si)
                        # else:
                        #     spectrumDisplay.stripFrame.layout().addWidget(strip, tilePosition[1], tilePosition[0])

                    elif spectrumDisplay.stripArrangement == 'T':
                        # NOTE:ED - Tiled plots not fully implemented yet
                        getLogger().warning(f'Tiled plots not implemented for spectrumDisplay: {str(spectrumDisplay)}')
                    else:
                        getLogger().warning(
                            f'Strip direction is not defined for spectrumDisplay: {str(spectrumDisplay)}')

                    if not spectrumDisplay.is1D:
                        for _strip in spectrumDisplay.strips:
                            _strip._updatePlaneAxes()

                if spectrumDisplay.isGrouped:
                    # set up the spectrumGroup toolbar

                    spectrumDisplay.spectrumToolBar.hide()
                    spectrumDisplay.spectrumGroupToolBar.show()

                    _spectrumGroups = [project.getByPid(pid) for pid in spectrumDisplay._getSpectrumGroups()]

                    for group in _spectrumGroups:
                        spectrumDisplay.spectrumGroupToolBar._forceAddAction(group)

                else:
                    # set up the spectrum toolbar

                    spectrumDisplay.spectrumToolBar.show()
                    spectrumDisplay.spectrumGroupToolBar.hide()
                    spectrumDisplay._setToolbarButtons()

                # some strips may not be instantiated at this point
                # resize the stripFrame to the spectrumDisplay - ready for first resize event
                # spectrumDisplay.stripFrame.resize(spectrumDisplay.width() - 2, spectrumDisplay.stripFrame.height())
                spectrumDisplay.showAxes(stretchValue=True, widths=True,
                                         minimumWidth=GuiStrip.STRIP_MINIMUMWIDTH)

            except Exception as es:
                getLogger().warning(f'Unable to restore spectrumDisplay(s): {es}')

        try:
            if current.strip is None and len(mainWindow.strips) > 0:
                current.strip = mainWindow.strips[0]
        except Exception as e:
            getLogger().warning(f'Error restoring current.strip: {e}')

    # GWV 07/08/2024: copied from Framework
    def _correctColours(self):
        """Autocorrect all colours that are too close to the background colour
        """
        from ccpn.ui.gui.guiSettings import autoCorrectHexColour, getColours, CCPNGLWIDGET_HEXBACKGROUND

        _app = self.application
        project = _app.project
        if _app.preferences.general.autoCorrectColours:
            # change sp colours
            for sp in project.spectra:
                if len(sp.axisCodes) > 1:
                    if sp.positiveContourColour and sp.positiveContourColour.startswith('#'):
                        sp.positiveContourColour = autoCorrectHexColour(sp.positiveContourColour,
                                                                        getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                    if sp.negativeContourColour and sp.negativeContourColour.startswith('#'):
                        sp.negativeContourColour = autoCorrectHexColour(sp.negativeContourColour,
                                                                        getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                elif sp.sliceColour and sp.sliceColour.startswith('#'):
                    sp.sliceColour = autoCorrectHexColour(sp.sliceColour,
                                                          getColours()[CCPNGLWIDGET_HEXBACKGROUND])
            # change peakList colours
            for objList in project.peakLists:
                objList.textColour = autoCorrectHexColour(objList.textColour,
                                                          getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                objList.symbolColour = autoCorrectHexColour(objList.symbolColour,
                                                            getColours()[CCPNGLWIDGET_HEXBACKGROUND])
            # change integralList colours
            for objList in project.integralLists:
                objList.textColour = autoCorrectHexColour(objList.textColour,
                                                          getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                objList.symbolColour = autoCorrectHexColour(objList.symbolColour,
                                                            getColours()[CCPNGLWIDGET_HEXBACKGROUND])
            # change multipletList colours
            for objList in project.multipletLists:
                objList.textColour = autoCorrectHexColour(objList.textColour,
                                                          getColours()[CCPNGLWIDGET_HEXBACKGROUND])
                objList.symbolColour = autoCorrectHexColour(objList.symbolColour,
                                                            getColours()[CCPNGLWIDGET_HEXBACKGROUND])
            for mark in project.marks:
                mark.colour = autoCorrectHexColour(mark.colour,
                                                   getColours()[CCPNGLWIDGET_HEXBACKGROUND])

    def _changeThemeInstant(self, theme: str=None, colour: str=None, themeSD: str=None):
        """Set the light/dark palette in single step.
        0 - dark, 1 - light, 2 - default = follow OS/application
        """
        prefsApp = self.application.preferences.appearance
        prefsGen = self.application.preferences.general

        _th, _col, _thSD = getTheme()  # should have been set on creation
        if theme is None: theme = _th.dataValue
        if themeSD is None: themeSD = _thSD.dataValue
        if colour is None: colour = _col

        if not isinstance(theme, Theme) and theme not in Theme.dataValues():
            raise ValueError(f'{self.__class__.__name__}._changeThemeInstant: theme not in {Theme.dataValues()}')
        if not isinstance(themeSD, Theme) and themeSD not in Theme.dataValues():
            raise ValueError(f'{self.__class__.__name__}._changeThemeInstant: themeSD not in {Theme.dataValues()}')
        if not isinstance(colour, str):
            raise TypeError(f'{self.__class__.__name__}._changeThemeInstant: colour not of type str')
        try:
            # test the colour
            QtGui.QColor(colour)
        except Exception:
            raise ValueError(f'{self.__class__.__name__}._changeThemeInstant: colour {colour!r} not valid')

        getLogger().debug(f'{consoleStyle.fg.darkblue}==> start palette-change event.{consoleStyle.reset}')
        # set highlight to the required highlighting colour
        # set the theme in preferences
        th = Theme.getByDataValue(theme)
        thSD = Theme.getByDataValue(themeSD)
        prefsApp.themeStyle = th.dataValue  # application theme
        prefsApp.themeColour = colour
        prefsGen.colourScheme = thSD.dataValue  # spectrumDisplay theme

        if pal := setColourScheme(th, colour, thSD):
            self._qtApp.setPalette(pal)
            # QtCore.QTimer.singleShot(0, partial(self.qtApp.setPalette, pal))
            QtCore.QTimer.singleShot(0, partial(self._qtApp.sigPaletteChanged.emit, pal,
                                              prefsApp.themeStyle,
                                              prefsApp.themeColour,
                                              prefsGen.colourScheme)
                                     )
        getLogger().debug(f'{consoleStyle.fg.darkblue}==> end palette-change event.{consoleStyle.reset}')

    # GWV 12/2/24; replaced by other implementation
    # def _updateCheckableMenuItems(self):
    #     # This has to be kept in sync with menu items below which are checkable,
    #     # and also with MODULE_DICT keys
    #     # The code is terrible because Qt has no easy way to get hold of menus / actions
    #
    #     mainWindow = self.mainWindow
    #     if mainWindow is None:
    #         # We have a UI with no mainWindow - nothing to do.
    #         return
    #
    #     menuChildren = mainWindow.menuBar().findChildren(QtWidgets.QMenu)
    #     if not menuChildren:
    #         return
    #
    #     topActionDict = {}
    #     for topMenu in menuChildren:
    #         mainActionDict = {mainAction.text(): mainAction for mainAction in topMenu.actions()}
    #
    #         topActionDict[topMenu.title()] = mainActionDict
    #
    #     openModuleKeys = set(mainWindow.moduleArea.modules.keys())
    #     for key, topActionText, mainActionText in (('SEQUENCE', 'Molecules', 'Show Sequence'),
    #                                                ('PYTHON CONSOLE', 'View', 'Python Console')):
    #         if key in openModuleKeys:
    #             if mainActionDict := topActionDict.get(topActionText):
    #                 if mainAction := mainActionDict.get(mainActionText):
    #                     mainAction.setChecked(True)

    def _makeActiveWindow(self):
        """Show and et self.mainWindow as the active window
        """
        # The next two lines are essential to have the QT main event loop associated
        # with the new mainWindow; without these, the program just terminates
        self.mainWindow.show()
        self._qtApp.setActiveWindow(self.mainWindow)

    def startUi(self):
        """Start the UI
        """
        self._makeActiveWindow()
        self._tipOfTheDayManager.start()

        # check whether to skip the execution loop for testing with mainWindow
        import builtins
        if not (_skip := getattr(builtins, '_skipExecuteLoop', False)):
            self._qtApp.start()

    def _registerDetails(self, registered=False, acceptedTerms=False):
        """Display registration popup"""
        days = Register._graceCounter(Register._fetchGraceFile(self.application))
        # check valid internet connection first
        if not Register.checkInternetConnection():
            msg = 'Could not connect to the registration server, please check your internet connection. ' \
                  'Register within %s day(s) to continue using the software' % str(days)
            MessageDialog.showError('Registration', msg)

        else:
            if registered and not acceptedTerms:
                popup = NewTermsConditionsPopup(self.mainWindow, trial=days,
                                                version=self.application.applicationVersion, modal=True)
            else:
                popup = RegisterPopup(self.mainWindow, trial=days, version=self.application.applicationVersion,
                                      modal=True)

            self.mainWindow.show()
            popup.exec_()
            self._qtApp.processEvents()

    def _setupMainWindow(self):
        """Set up mainWindow
        """
        _sideBar = self.mainWindow._getSideBar()
        _sideBar.buildTree(self.project, clear=True)
        self.mainWindow._setReadOnlyIcon()
        self.mainWindow.namespace['current'] = self.application.current

    def echoCommands(self, commands: typing.List[str]):
        """Echo commands strings, one by one, to logger
        and store them in internal list for perusal
        """
        REMOVEDEBUG = r'\(\S+\.\w+:\d+\)$'

        logger = getLogger()
        for command in commands:
            logger.echoInfo(command)

        if self.application.ui is not None and \
                self.application.ui.mainWindow is not None and \
                self.application._enableLoggingToConsole:

            console = self.application.ui.mainWindow._pythonConsoleWidget
            for command in commands:
                command = re.sub(REMOVEDEBUG, '', command)
                console._write(command + '\n')

    def getByGid(self, gid):

        from ccpn.ui.gui.modules.CcpnModule import PidShortClassName, PidLongClassName
        from ccpn.core.lib.Pid import Pid

        pid = Pid(gid)
        if pid is not None and pid.type in [PidLongClassName, PidShortClassName]:
            # get the GuiModule object By its Gid
            return self.application.mainWindow.moduleArea.modules.get(pid.id)

        return self.application.getByGid(gid)

    def _execUpdates(self):
        """Use the Update popup to execute any updates
        """
        from ccpn.framework.update.UpdatePopup import UpdatePopup
        from ccpn.util import Url

        # check valid internet connection first
        if Url.checkInternetConnection():
            updatePopup = UpdatePopup(parent=self.mainWindow, mainWindow=self.mainWindow)
            updatePopup.exec_()

            # if updates have been installed then popup the quit dialog with no cancel button
            if updatePopup._updatesInstalled:
                self.mainWindow._closeWindowFromUpdate(disableCancel=True)

        else:
            MessageDialog.showWarning('Check For Updates',
                                      'Could not connect to the update server, please check your internet connection.')

    #-----------------------------------------------------------------------------------------
    # Helper methods
    #-----------------------------------------------------------------------------------------

    def _queryChoices(self, dataLoader: DataLoaderABC) -> tuple[DataLoaderABC, bool, bool]:
        """Query the user about his/her choice to import/new/cancel;
        set dataLoader.createNewProject
        :return (dataLoader, createNewProject:bool, ignore:bool) tuple
        """
        if not isinstance(dataLoader, DataLoaderABC):
            raise TypeError(f'Invalid dataLoader; got instance of {type(dataLoader)}')

        choices = ('Import', 'New project', 'Cancel')
        choice = MessageDialog.showMulti(
                f'Load {dataLoader.dataFormat}',
                f'How do you want to handle "{dataLoader.path}":',
                choices,
                parent=self.mainWindow,
                )

        if choice == choices[0]:  # import
            dataLoader.createNewProject = False
            createNewProject = False
            ignore = False

        elif choice == choices[1]:  # new project
            dataLoader.createNewProject = True
            createNewProject = True
            ignore = False

        else:  # cancel
            dataLoader = None
            createNewProject = False
            ignore = True

        return (dataLoader, createNewProject, ignore)

    def _getDataLoader(self, path, formatFilter=None, droppedOnSideBar=False) -> tuple[DataLoaderABC, bool, bool]:
        """Get dataLoader for path (or None if not present), optionally only testing for dataFormats defined in filter.
        Allows for reporting or checking through popups.
        Does not do the actual loading.

        :param path: the path to get a dataLoader for
        :param formatFilter: a list/tuple of optional dataFormat strings; filter optional dataLoaders for this
        :param: droppedOnSideBar: flag to indicate path dropped on the sidebar
        :returns a tuple (dataLoader, createNewProject, ignore)

        :raises RuntimeError in case of failure to define a proper dataLoader
        """
        _path = aPath(path)
        if not _path.exists():
            raise RuntimeError(f'Path "{path}" does not exist')

        # get list of possible loaders;
        _loaders = _checkPathForDataLoader(path=path, formatFilter=formatFilter)
        if len(_loaders) == 0:
            raise RuntimeError(f'Unknown error finding a loader for {path}')

        # check the _loaders for a valid one
        if _loaders[-1].isValid:
            # there is a valid one; use that
            dataLoader = _loaders[-1]
            errMsg = None

        else:
            dataLoader = None
            # We always get a loader back; report it here
            errMsg = f'{_loaders[-1].dataFormat} loader reported:\n\n{_loaders[-1].errorString}'

        # raise error if needed
        if errMsg:
            getLogger().warning(errMsg)
            raise RuntimeError(errMsg)

        return self._checkDataLoader(dataLoader, droppedOnSideBar=droppedOnSideBar)

    def _checkDataLoader(self, dataLoader, droppedOnSideBar=False) -> tuple[DataLoaderABC, bool, bool]:
        """Check dataLoader, reporting or checking through popups.
        Does not do the actual loading.

        :param dataLoader: dataLoader instance to be checked
        :param: droppedOnSideBar: flag to indicate path dropped on the sidebar
        :returns a tuple (dataLoader, createNewProject, ignore)
        :raises RuntimeError in case of failure
        """
        # local import here
        from ccpn.framework.lib.DataLoaders.CcpNmrV2ProjectDataLoader import CcpNmrV2ProjectDataLoader
        from ccpn.framework.lib.DataLoaders.CcpNmrV3ProjectDataLoader import CcpNmrV3ProjectDataLoader
        from ccpn.framework.lib.DataLoaders.NefDataLoader import NefDataLoader
        from ccpn.framework.lib.DataLoaders.SparkyDataLoader import SparkyDataLoader
        from ccpn.framework.lib.DataLoaders.StarDataLoader import StarDataLoader
        from ccpn.framework.lib.DataLoaders.DirectoryDataLoader import DirectoryDataLoader
        from ccpn.framework.lib.DataLoaders.SpectrumDataLoader import NmrPipeSpectrumLoader

        createNewProject = dataLoader.createNewProject
        ignore = False
        path = dataLoader.path

        # Check that the path does not contain a bottom-level space
        if dataLoader.dataFormat in [CcpNmrV2ProjectDataLoader.dataFormat, CcpNmrV3ProjectDataLoader.dataFormat] \
                and ' ' in dataLoader.path.basename:
            MessageDialog.showWarning('Load Project', 'Encountered a problem loading:\n"%s"\n\n'
                                                      'Cannot load project folders where the project-name contains spaces.\n\n'
                                                      'Please rename the folder without spaces and try loading again.' % dataLoader.path)
            # skip loading bad projects
            ignore = True

        elif dataLoader.dataFormat == CcpNmrV2ProjectDataLoader.dataFormat:
            createNewProject = True
            dataLoader.createNewProject = True
            ok = MessageDialog.showYesNoWarning('Load Project',
                                                f'Project "{path.name}" was created with version-2 Analysis.\n'
                                                f'The project will be converted to a version-3 project in a temporary directory,\n'
                                                f'after which you can decide to save it.\n'
                                                '\n'
                                                'Do you want to continue loading? (Conversion may take a bit of time)')

            if not ok:
                # skip loading so that user can back-up/copy project
                getLogger().info(f'==> Cancelled loading ccpn project "{path}"')
                ignore = True

        elif dataLoader.dataFormat == CcpNmrV3ProjectDataLoader.dataFormat and dataLoader.projectNeedsUpgrade:
            createNewProject = True
            dataLoader.createNewProject = True

            DONT_OPEN = "Don't Open"
            CONTINUE = 'Continue'
            MAKE_ARCHIVE = 'Make a backup archive (.tgz) of the project'

            dataLoader.makeArchive = False
            ok = MessageDialog.showMulti(
                    'Load Project',
                    f'You are opening an older project (version {dataLoader.lastSavedVersion}) - {path.name}\n'
                    '\n'
                    f'When you save, it will be upgraded and will no longer be readable by program versions < {Project._LOWEST_COMPATIBLE_VERSION}\n',
                    texts=[DONT_OPEN, CONTINUE],
                    checkbox=MAKE_ARCHIVE, checked=False,
                    )

            if all(ss not in ok for ss in [DONT_OPEN, MAKE_ARCHIVE, CONTINUE]):
                # there was an error from the dialog
                getLogger().debug(f'==> Cancelled loading ccpn project "{path}" - error in dialog')
                ignore = True
            if DONT_OPEN in ok:
                # user selection not to load
                getLogger().info(f'==> Cancelled loading ccpn project "{path}"')
                ignore = True
            elif MAKE_ARCHIVE in ok:
                # flag to make a backup archive
                dataLoader.makeArchive = True

        elif dataLoader.dataFormat == NefDataLoader.dataFormat:
            (_tmp, createNewProject, ignore) = self._queryChoices(dataLoader)
            if _tmp and not createNewProject and not ignore:
                # we are importing; popup the import window
                ok = self.mainWindow._showNefPopup(dataLoader)
                if not ok:
                    ignore = True

        elif dataLoader.dataFormat == SparkyDataLoader.dataFormat:
            (dataLoader, createNewProject, ignore) = self._queryChoices(dataLoader)

        elif dataLoader.isSpectrumLoader and dataLoader.existsInProject():
            ok = MessageDialog.showYesNoWarning('Loading Spectrum',
                                                f'"{dataLoader.dataSource.path}"\n'
                                                f'"{dataLoader.path}"\n'
                                                f'already exists in the project\n'
                                                '\n'
                                                'Do you want to load?'
                                                )

        elif dataLoader.dataFormat == NmrPipeSpectrumLoader.dataFormat:
            # NmrPipe file; check if it is large 3D/4D
            _ds = dataLoader.dataSource
            dims = _ds.dimensionCount
            expectedSize = _ds.expectedFileSizeInBytes / (1024 * 1024)
            if dims > 2 and expectedSize >= _ds.WARNING_FILE_SIZE and not _ds.bufferIsFilled:

                if droppedOnSideBar:
                    _txt1 = f'Loading Spectrum "{dataLoader.path}"'
                    _txt2 = f'The {dims}D NmrPipe file ({expectedSize:.1f} MB) will be automatically buffered when first displayed\n' \
                            f'Consider converting to Hdf5 format (Menu: Spectrum --> Convert to Hdf5)\n'
                    ok = MessageDialog.showOkCancel(_txt1, _txt2)
                    if not ok:
                        ignore = True

                else:
                    _txt1 = f'Displaying Spectrum "{dataLoader.path}"'
                    _txt2 = f'The {dims}D NmrPipe file ({expectedSize:.1f} MB) will be automatically buffered\n' \
                            f'Consider loading first and converting to Hdf5 format (Menu: Spectrum --> Convert to Hdf5)\n' \
                            '\n' \
                            'Do you want to display now? (the buffering may take a -little- while)'
                    ok = MessageDialog.showYesNoWarning(_txt1, _txt2)
                    if not ok:
                        ignore = True

        elif dataLoader.dataFormat == StarDataLoader.dataFormat and dataLoader:
            (_tmp, createNewProject, ignore) = self._queryChoices(dataLoader)
            if _tmp and not ignore:
                title = 'New project from NmrStar' if createNewProject \
                         else 'Import from NmrStar'
                dataLoader.getDataBlock()  # this will read and parse the file
                popup = StarImporterPopup(dataLoader=dataLoader,
                                          parent=self.mainWindow,
                                          size=(700, 1000),
                                          title=title
                                          )
                popup.exec_()
                ignore = (popup.result == popup.CANCEL_PRESSED)

        elif dataLoader.dataFormat == DirectoryDataLoader.dataFormat:

            msg = None
            if dataLoader.count > MAXITEMLOADING or dataLoader.depth > MAXITEMDEPTH:
                _nSpectra = len([dl for dl in dataLoader.dataLoaders if dl.isSpectrumLoader and dl.isValid])
                _spectra = f', of which {_nSpectra} are spectra' if _nSpectra>0 else ''
                msg =  f'CAUTION: You are trying to load {dataLoader.count:d} items{_spectra}.\n'

                if dataLoader.depth > MAXITEMDEPTH:
                    msg += f'The folder is {dataLoader.depth}-subfolders deep.\n\n'

                msg += (f'It may take some time to load.\n\n'
                        f'Do you want to continue?')

            ignore = (bool(msg) and not MessageDialog.showYesNoWarning(f'Directory {dataLoader.path!r}\n', msg))

        dataLoader.createNewProject = createNewProject
        dataLoader.ignore = ignore
        return (dataLoader, createNewProject, ignore)

    #-----------------------------------------------------------------------------------------
    # File, Project and loading data related methods
    #-----------------------------------------------------------------------------------------

    @logCommand('ui.')
    def newProject(self, name: str = 'newProject') -> Project | None:
        """Create a new project instance with name; create default project if name=None
        :return a Project instance or None
        """
        from ccpn.core.lib.ProjectLib import checkProjectName

        oldMainWindowPos = self.mainWindow.pos()
        if self.project and (self.project._undo is None or self.project._undo.isDirty()):
            # if not self.project.isTemporary:
            if self.project._undo is None or self.project._undo.isDirty():
                _CANCEL = 'Cancel'
                _OK = 'Discard and New'
                _SAVE = 'Save'
                msg = (f"The current project has been modified and requires saving. Do you want save the current "
                       f"project first, or discard the changes and continue creating a new project?")
                reply = MessageDialog.showMulti('New Project...', msg,
                                                texts=[_OK, _CANCEL, _SAVE],
                                                okText=_OK, cancelText=_CANCEL,
                                                parent=self.mainWindow)
                if reply == _CANCEL:
                    # cancel the new-operation
                    return
                elif reply == _SAVE:
                    # save first
                    if not self.saveProject():
                        # cancel the new-operation if there was an issue saving
                        return

        if (_name := checkProjectName(name, correctName=True)) != name:
            MessageDialog.showInfo('New Project',
                                   f'Project name changed from "{name}" to "{_name}"\nSee console/log for details',
                                   parent=self)

        newProject = None
        with catchExceptions(errorStringTemplate='Error creating new project: %s'):
            # if self.mainWindow:
            #     self.mainWindow.moduleArea._closeAll()
            newProject = self.application._newProject(name=_name)
            if newProject is None:
                raise RuntimeError('Unable to create new project')
            self.mainWindow.move(oldMainWindowPos)

        return newProject

    def _loadProject(self, dataLoader=None, path=None) -> Project | bool | None:
        """Helper function, loading project from dataLoader instance
        check and query for closing current project
        build the project Gui elements
        attempts to restore on failure to load a project

        :returns project instance or None
        """
        from ccpn.framework.lib.DataLoaders.CcpNmrV3ProjectDataLoader import CcpNmrV3ProjectDataLoader
        from ccpn.framework.lib.DataLoaders.DataLoaderABC import checkPathForDataLoader

        if dataLoader is None and path is not None:
            if (dataLoader := checkPathForDataLoader(path)) is None:
                raise RuntimeError(f'Loading project: No suitable dataLoader found for {path}')
        if dataLoader is None:
            raise RuntimeError('Loading project: No suitable dataLoader')

        if dataLoader is None and path is not None:
            dataLoader = checkPathForDataLoader(path)
        if dataLoader is None:
            getLogger().error('No suitable dataLoader found')
            return None
        if not dataLoader.createNewProject:
            raise RuntimeError(f'DataLoader {dataLoader} does not create a new project')

        oldProjectLoader = None
        oldProjectIsTemporary = True
        oldMainWindowPos = self.mainWindow and self.mainWindow.pos()

        if self.project:
            # if not self.project.isTemporary:
            if self.project._undo is None or self.project._undo.isDirty():
                _CANCEL = 'Cancel'
                _OK = 'Discard and Load'
                _SAVE = 'Save'
                msg = (f"The current project has been modified and requires saving. Do you want save the current "
                       f"project first, or discard the changes and continue loading?")
                reply = MessageDialog.showMulti('Load Project...', msg,
                                                texts=[_OK, _CANCEL, _SAVE],
                                                okText=_OK, cancelText=_CANCEL,
                                                parent=self.mainWindow)
                if reply == _CANCEL:
                    # cancel the load-operation
                    return None
                elif reply == _SAVE:
                    # save first
                    if not self.saveProject():
                        # cancel the load-operation if there was an issue saving
                        return None

            # Some error recovery; store info to re-open the current project (or a new default)
            oldProjectLoader = CcpNmrV3ProjectDataLoader(self.project.path)
            oldProjectIsTemporary = self.project.isTemporary

        error = False
        try:
            if self.project:
                # NOTE:ED - getting a strange QT bug disabling the menu-bar from here
                #  I think because the main-window isn't visible on the first load :|
                with busyHandler(self.mainWindow, title='Loading',
                                 text=f'Loading project {dataLoader.path} ...', closeDelay=1000):
                    _loaded = dataLoader.load()
            else:
                # busy-status not required on the first load
                _loaded = dataLoader.load()

            # NOTE:ED - another one here, if the message-dialog appears BEFORE the window-modal busy popup
            #   then the window containing the busy-popup takes control (but is still mouse-blocked)
            #   and the message-dialog doesn't close or doesn't pass modality back to the parent :|
            #   solution -  make sure busy popups are already visible,
            #               or show dialogs outside the busy context-manager
            if not _loaded:
                MessageDialog.showWarning('Loading Project',
                                          f'There was a problem loading project {dataLoader.path}\n'
                                          f'Please check the log for more information.',
                                          parent=self.mainWindow)
                return None

            newProject = _loaded[0]

            # if the new project contains invalid spectra then open the popup to see them
            self.mainWindow._checkForBadSpectra(newProject)
            if oldMainWindowPos:
                self.mainWindow.move(oldMainWindowPos)

            error = False

        except (RuntimeError, ValueError, ApiError) as es:
            MessageDialog.showError('Error loading Project:', f'{es}', parent=self.mainWindow)
            error = True

        except NotImplementedError as es:
            MessageDialog.showError('Error loading Project:', f'{es}', parent=self.mainWindow)
            error = True

        finally:
            if error:
                # Try to restore the state
                # reload existing or create a new temporary one (as the original temporary
                # get deleted by the closing)
                newProject = None
                if oldProjectIsTemporary:
                    newProject = self.application._newProject()
                elif oldProjectLoader:
                    newProject = oldProjectLoader.load()[0]  # dataLoaders return a list

        return newProject

    # @logCommand('application.') # eventually decorated by  _loadData()
    def loadProject(self, path=None) -> Project | None:
        """Loads project defined by path
        :return a Project instance or None
        """

        if path is None:
            dialog = FileDialog.ProjectFileDialog(parent=self.mainWindow, acceptMode='open')
            dialog._show()

            if (path := dialog.selectedFile()) is None:
                return None

        with self.application.pauseAutoBackups():
            with catchExceptions(errorStringTemplate='Error loading project: %s'):
                dataLoader, createNewProject, ignore = self._getDataLoader(path)

                newProjectUrls = self._scanDataLoaders([dataLoader], func=lambda dl: (dl is not None and
                                                                                    dl.createNewProject))

                if len(newProjectUrls) > 1:
                    # We found more than one dataLoader that would create a new project; not allowed
                    MessageDialog.showError('Load Data',
                                            f'Only one new project can be created at a time;\n'
                                            f'this action will try to create {len(newProjectUrls):d} new projects',
                                            parent=self.mainWindow)

                if ignore or dataLoader is None or not createNewProject:
                    return None

                # load the project using the dataLoader;
                # We'll ask framework who will pass it back to ui._loadProject
                if (objs := self.application._loadData([dataLoader])):
                    if len(objs) == 1:
                        return objs[0]

        return None

    def _scanDataLoaders(self, dataLoaders, func: callable = lambda _: True, result=None, depth=0) -> list:
        """Replace the list comprehension below to allow nested tree of dataLoaders.
        Assumes that recursive==True in the DirectoryDataLoader __init__
        """
        if result is None:
            result = []
        for loader in dataLoaders:
            url, _, createNew, ignore = loader.path, loader, loader.createNewProject, loader.ignore
            if ignore:
                continue
            if getattr(loader, 'dataLoaders', None) is not None and getattr(loader, 'recursive', None) is True:
                self._scanDataLoaders(loader.dataLoaders, result=result, func=func, depth=depth + 1)
            elif loader and func(loader):
                result.append((url, loader, createNew))
        return result

    def _closeProject(self):
        """Do all gui-related stuff when closing a project
        CCPNINTERNAL: called from Framework._closeProject()
        """
        if self.mainWindow:
            # ui/gui cleanup; not undo required
            with undoStack() as _:
                self.mainWindow.deleteAllNotifiers()
                self.mainWindow._stopPythonConsole()
                self.mainWindow._closeMainWindowModules()
                self.mainWindow._closeExtraWindowModules()
                _sideBar = self.mainWindow._getSideBar()
                _sideBar.clearSideBar()
                _sideBar.deleteLater()
                self.mainWindow.deleteLater()
                self._mainWindow = None

    @logCommand('application.')
    def saveProjectAs(self, newPath=None, overwrite: bool = False) -> bool:
        """Opens save Project to newPath.
        Optionally open file dialog.
        :param newPath: new path to save project (str | Path instance)
        :param overwrite: flag to indicate overwriting of existing path
        :return True if successful
        """
        from ccpn.core.lib.ProjectLib import checkProjectName

        title = 'Project SaveAs'
        oldPath = aPath(self.project.path)

        if newPath is None:
            # try to create a new path from the old one
            if self.project.isTemporary:
                _newName = self.project.name
                _newPath = (aPath('~') / _newName).assureSuffix(CCPN_DIRECTORY_SUFFIX)
            else:
                _newName = f'{self.project.name}_new'
                _newPath = oldPath.with_name(_newName).assureSuffix(CCPN_DIRECTORY_SUFFIX)
            # query for this path
            dialog = FileDialog.ProjectSaveFileDialog(parent=self.mainWindow,
                                                      directory=_newPath.parent.asString(),
                                                      selectFile=_newPath.name,
                                                      acceptMode='save')
            dialog._show()
            if (newPath := dialog.selectedFile()) is None:
                return False
        newPath = aPath(newPath).assureSuffix(CCPN_DIRECTORY_SUFFIX)

        if newPath.exists() and \
                (newPath.is_file() or (newPath.is_dir() and len(newPath.listdir(excludeDotFiles=False)) > 0)) and \
                not overwrite:
            msg = f'Path "{newPath}" already exists; overwrite?'
            if not MessageDialog.showYesNo(title, msg):
                return False

        # check the project name derived from path; not all is allowed
        newName = newPath.basename
        if (_nameFromPath := checkProjectName(newName, correctName=True)) != newName:
            MessageDialog.showInfo(title,
                                   f'Project name will be changed from "{newName}" to "{_nameFromPath}"\n'
                                   f'See console/log for details',
                                   parent=self.mainWindow)
            newPath = (newPath.parent / _nameFromPath).assureSuffix(CCPN_DIRECTORY_SUFFIX)
            newName = _nameFromPath

        # Checking copy subdirectories
        _sizeDict = self.project._getSubdirectorySizes(CCPN_SAVEAS_SUB_DIRECTORIES, sizeInMB=True)
        _totalSize = sum(_sizeDict.values())
        _tmp = '%.1f' % _totalSize
        msg = f'Also copy sub-directories (data, archives, scripts, ...) ({_tmp} MB)?\n'

        # Check for any inside spectra
        _insideSpectra = [sp for sp in self.project.spectra if sp._isInside]
        _size = '%.1f' % (sum([sp.dataSource.expectedFileSizeInBytes for sp in _insideSpectra]) / (1024 * 1024))
        if len(_insideSpectra) == 1:
            msg += f'\nNote that the data of {_insideSpectra[0].pid} ({_size} MB) is in "{oldPath.name}/data/spectra"\n'
        elif len(_insideSpectra) > 1:
            msg += f'\nNote that the data of {len(_insideSpectra)} spectra ({_size} MB) are in "{oldPath.name}/data/spectra"\n'

        if self.project.isTemporary:
            copySubDirs = True
        else:
            if (copySubDirs := MessageDialog.showYesNoCancel(title, msg)) is None:
                # pressed "cancel"
                return False

        with catchExceptions(errorStringTemplate='Error saving project: %s'):
            with MessageDialog.progressManager(self.mainWindow, f'Saving project as {newPath} ... '):
                try:
                    if not self.application._saveProjectAs(newPath=newPath, overwrite=True,
                                                           copySubDirectories=copySubDirs):
                        txt = f"Saving project to {newPath} aborted; check log for details"
                        MessageDialog.showError("Project SaveAs", txt, parent=self.mainWindow)
                        return False

                except (PermissionError, FileNotFoundError):
                    msg = f'Folder {newPath} may be read-only'
                    MessageDialog.showWarning('Save project', msg)
                    return False

                except RuntimeWarning as es:
                    msg = f'Error saving {newPath}:\n{es}'
                    MessageDialog.showWarning('Save project', msg)
                    return False

        # NOTE:ED - need to find where this has moved
        # GWV 24/10/2024: MainWindow needs to set a notifier; eg
        # mainWindow.setNotifier(project, ['observe'], 'name', project._testCallback)
        # self.mainWindow._updateWindowTitle()
        # GWV: no longer needed
        # self.application._getRecentProjectFiles()  # this will update the preferences-list
        # self.mainWindow._fillRecentProjectsMenu()  # Update the menu
        #
        # GWV 25/20/2025: Preferences._setWorkingPath method
        #                 Put in Framework.initialiseProject; Framework._saveProjectAs
        # sets working path to current path if required
        # if (genPrefs := self.application.preferences.general).useProjectPath == 'Alongside':
        #     genPrefs.userWorkingPath = self.project.projectPath.parent.asString()
        # elif genPrefs.useProjectPath == 'Inside':
        #     genPrefs.userWorkingPath = self.project.projectPath.asString()
        #
        # successMessage = f'Project successfully saved to "{self.project.path}"'
        # # MessageDialog.showInfo("Project SaveAs", successMessage, parent=self.mainWindow)
        # self.mainWindow.statusBar().showMessage(successMessage)
        # getLogger().info(successMessage)

        return True

    @logCommand('application.')
    def saveProject(self) -> bool:
        """Save project.
        :return True if successful
        """
        if self.project.isTemporary:
            return self.saveProjectAs()

        if self.project.isReadOnly and not MessageDialog.showYesNo(
                'Save Project',
                'The project is marked as read-only.\n'
                'This can be changed by clicking the lock-icon in the bottom-right.\n\n'
                'Do you want to continue saving?\n',
                ):
            return True

        with catchExceptions(errorStringTemplate='Error saving project: %s'):
            with MessageDialog.progressManager(self.mainWindow, 'Saving project ... '):
                try:
                    if not self.application._saveProject():
                        return False
                except (PermissionError, FileNotFoundError):
                    msg = 'Folder may be read-only'
                    MessageDialog.showWarning('Save project', msg)
                    return True

        # ED: 2024/05/03 - logged from notifier
        return True

    def _loadData(self, dataLoader) -> list:
        """Load the data defined by dataLoader instance, catching errors
        and suspending sidebar.
        :return A list of loaded objects, as any dataLoader object returns a list
        """
        from ccpn.framework.lib.DataLoaders.StarDataLoader import StarDataLoader
        from ccpn.framework.lib.DataLoaders.NefDataLoader import NefDataLoader

        result = []  # the load may fail
        errorStringTemplate = f'Loading "{dataLoader.path}" failed:\n\n%s'
        with catchExceptions(errorStringTemplate=errorStringTemplate):
            # For data loads that are possibly time-consuming, use progressManager
            if isinstance(dataLoader, (StarDataLoader, NefDataLoader)):
                with MessageDialog.progressManager(self.mainWindow, 'Importing data ... '):
                    result = dataLoader.load()
            else:
                result = dataLoader.load()
        return result

    # @logCommand('application.') # eventually decorated by  _loadData()
    def loadData(self, *paths, formatFilter: (list, tuple) = None) -> list:
        """Loads data from paths; query if none supplied
        Optionally filter for dataFormat(s)
        :param *paths: argument list of path's (str or Path instances)
        :param formatFilter: list/tuple of dataFormat strings
        :returns list of loaded objects
        """
        if not paths:
            dialog = FileDialog.DataFileDialog(parent=self.mainWindow, acceptMode='load')
            dialog._show()
            if (path := dialog.selectedFile()) is None:
                return []
            paths = [path]

        dataLoaders = []
        for path in paths:

            _path = aPath(path)
            if not _path.exists():
                txt = f'"{path}" does not exist'
                getLogger().warning(txt)
                MessageDialog.showError('Load Data', txt, parent=self)
                continue

            try:
                dataLoader, createNewProject, ignore = self._getDataLoader(path, formatFilter=formatFilter)

            except RuntimeError as es:
                MessageDialog.showError(f'Loading "{_path}"',
                                        f'{es}',
                                        parent=self.mainWindow)
                if len(paths) == 1:
                    return []
                else:
                    continue

            if ignore:
                continue

            dataLoaders.append(dataLoader)

        # load the project using the dataLoaders;
        # We'll ask framework who will pass it back as ui._loadData calls
        objs = self.application._loadData(dataLoaders)
        if len(objs) == 0:
            _pp = ','.join(f'"{p}"' for p in paths)
            txt = f'No objects were loaded from {_pp}'
            getLogger().warning(txt)
            MessageDialog.showError('Load Data', txt, parent=self.mainWindow)

        return objs

    def _loadDataIgnoreExtension(self, dataLoaderClass=None) -> list | None:
        """Load the data defined by dataLoader, provides file dialog.

        :param dataLoaderClass: DataLoader class used to import data
        :return: a list of loaded objects
        """
        from ccpn.ui.gui.widgets import FileDialog
        from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC

        if not issubclass(dataLoaderClass, DataLoaderABC):
            getLogger().debug(f'_loadDataIgnoreExtension(): invalid {dataLoaderClass=}')
            return

        dialog = FileDialog.DataFileDialog(parent=self.mainWindow, acceptMode='load')
        dialog._show()
        if (path := dialog.selectedFile()) is None:
            return []
        paths = [path]

        dataLoaders = []
        for path in paths:
            _path = aPath(path)
            if not _path.exists():
                txt = f'"{path}" does not exist'
                getLogger().warning(txt)
                MessageDialog.showError('Load Data', txt, parent=self)
                continue

            # loads data using the provided dataLoader
            _dataLoader = dataLoaderClass(path)
            _dataLoader, _tmp, ignore = self._checkDataLoader(_dataLoader)
            if _dataLoader and not ignore:
                dataLoaders.append(_dataLoader)

        # load the project using the dataLoaders;
        # We'll ask framework who will pass it back as ui._loadData calls
        objs = self.application._loadData(dataLoaders)
        if len(objs) == 0:
            _pp = ','.join(f'"{p}"' for p in paths)
            txt = f'No objects were loaded from {_pp}'
            getLogger().warning(txt)
            MessageDialog.showError('Load Data', txt, parent=self.mainWindow)

        return objs

    def loadSpectra(self, *paths) -> list:
        """Load all the spectra found in paths.
        Query in case path is empty.

        :param paths: list of paths
        :return a list of Spectra instances
        """
        from ccpn.framework.lib.DataLoaders.DataLoaderABC import getSpectrumLoaders, checkPathForDataLoader
        from ccpn.framework.lib.DataLoaders.DirectoryDataLoader import DirectoryDataLoader

        if not paths:
            # This only works with non-native file dialog; override the default behavior
            dialog = FileDialog.SpectrumFileDialog(parent=self.mainWindow, acceptMode='load',
                                                   useNative=False)
            dialog._show()
            paths = dialog.selectedFiles()

        if not paths:
            return []

        formatFilter = list(getSpectrumLoaders().keys())

        spectrumLoaders = []
        count = 0
        # Recursively search all paths
        for path in paths:
            _path = aPath(path)
            if _path.is_dir():
                dirLoader = DirectoryDataLoader(path, recursive=False, formatFilter=formatFilter)
                spectrumLoaders.append(dirLoader)
                count += len(dirLoader)

            elif (sLoader := checkPathForDataLoader(path, formatFilter=formatFilter)) is not None:
                spectrumLoaders.append(sLoader)
                count += 1

        if count > MAXITEMLOGGING:
            okToOpenAll = MessageDialog.showYesNo('Load data', 'You selected %d items.'
                                                               ' Do you want to open all?' % count)
            if not okToOpenAll:
                return []

        with logCommandManager('application.', 'loadSpectra', *paths):
            result = self.application._loadData(spectrumLoaders)

        return result

    def exportToNef(self):
        """Export project to NEF; query for path.
        Define objects to be exported in the popup
        """
        from ccpn.ui.gui.popups.ExportNefPopup import ExportNefPopup
        from ccpn.framework.lib.ccpnNef.CcpnNefIo import NEFEXTENSION

        _path = aPath(getPreferences().get(USER_WORKING_PATH) or '~') / self.project.name
        _path = _path.withSuffix(NEFEXTENSION)

        dialog = ExportNefPopup(parent=self.mainWindow._widget,
                                mainWindow=self.mainWindow,
                                selectFile=_path,
                                fileFilter='*.nef',
                                minimumSize=(400, 550))

        # an exclusion dict comes out of the dialog as it
        result = dialog.exec_()

        if not result:
            return

        nefPath = result['filename']
        flags = result['flags']
        pidList = result['pidList']

        # flags are skipPrefixes, expandSelection
        skipPrefixes = flags['skipPrefixes']
        expandSelection = flags['expandSelection']
        includeOrphans = flags['includeOrphans']

        self.project.exportNef(nefPath,
                               overwriteExisting=True,
                               skipPrefixes=skipPrefixes,
                               expandSelection=expandSelection,
                               includeOrphans=includeOrphans,
                               pidList=pidList)

    def saveToArchive(self):
        """Make a time-stamped archive of project
        """
        if (path := self.application.saveToArchive()) is None:
            MessageDialog.showInfo('Archive Project',
                                   'Unable to archive Project')
        else:
            MessageDialog.showInfo('Archive Project',
                                   f'Project archived to {path}')

    def restoreFromArchive(self):
        """Restore project from archive.
        """
        from ccpn.ui.gui.widgets.FileDialog import ArchivesFileDialog
        from ccpn.framework.PathsAndUrls import CCPN_ARCHIVES_DIRECTORY

        archivesDirectory = aPath(self.project.path) / CCPN_ARCHIVES_DIRECTORY
        _filter = '*.tgz'
        dialog = ArchivesFileDialog(parent=self.mainWindow._widget,
                                    acceptMode='select',
                                    directory=archivesDirectory,
                                    fileFilter=_filter)
        dialog._show()
        archivePath = dialog.selectedFile()

        if archivePath and \
           (newProject := self.application.restoreFromArchive(archivePath)) is not None:
            MessageDialog.showInfo('Restore from Archive',
                                   f'Project restored as {newProject.path}')

    @logCommand('ui.')
    def saveLayoutToFile(self, path: (str, Path, None) = None):
        """Save the layout to file.
        :param path: path to valid layout file; queried if None
        """
        if path is None:
            path = _getSaveLayoutPath(self.mainWindow)
        if path is None:
            return
        self.mainWindow._saveLayoutToFile(path=path)

    @logCommand('ui.')
    def restoreLayoutFromFile(self, path: (str, Path, None) = None):
        """Restore the layout from file.
        :param path: path to valid layout file; queried if None
        """
        if path is None:
            path = _getOpenLayoutPath(self.mainWindow)
        if path is None:
            return
        self.mainWindow._loadLayoutFromFile(path=path)
        self.mainWindow._restoreLayout()

    @logCommand('ui.')
    def showPreferences(self):
        """Show and edit the preferences.
        """
        from ccpn.ui.gui.popups.PreferencesPopup import PreferencesPopup
        popup = PreferencesPopup(parent=self.mainWindow._widget,
                                 mainWindow=self.mainWindow
                                 )
        popup.exec_()

    #-----------------------------------------------------------------------------------------
    # View
    #-----------------------------------------------------------------------------------------

    def _showModule(self, moduleClass, position: str = 'bottom', relativeTo = None,
                    selection: typing.Any = None, selectFirstItem: bool = True):
        """Helper function to avoid code duplication.
        Initiate and add an instance of moduleClass; optionally call setTable with selection
        :param moduleClass: module class to display an instance
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param selection: optional entry to select
        :param selectFirstItem: flag to select first item
        :return a new ModuleClass instance
        """
        if not issubclass(moduleClass, CcpnModule):
            raise TypeError(f'Expected subclass of {CcpnModule}; got {moduleClass}')

        _module = moduleClass(mainWindow=self.mainWindow, selectFirstItem=selectFirstItem)
        self.mainWindow._addModule(_module, position=position, relativeTo=relativeTo)
        if selection:
            _module.selectTable(selection)
        return _module

    @logCommand('ui.')
    def showChemicalShiftTable(self, position: str = 'bottom', relativeTo = None, chemicalShiftList=None):
        """Show the ChemicalShiftTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param chemicalShiftList: optional ChemicalShiftList to display
        """
        from ccpn.ui.gui.modules.ChemicalShiftTable import ChemicalShiftTableModule
        return self._showModule(ChemicalShiftTableModule, position=position, relativeTo=relativeTo,
                                selection=chemicalShiftList)

    @logCommand('ui.')
    def showNmrResidueTable(self, position='bottom', relativeTo = None, nmrChain=None):
        """Show the NmrResidueTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param nmrChain: optional NmrChain with NmrResidue's to display
        """
        from ccpn.ui.gui.modules.NmrResidueTable import NmrResidueTableModule
        return self._showModule(NmrResidueTableModule, position=position, relativeTo=relativeTo,
                                selection=nmrChain)

    @logCommand('ui.')
    def showResidueTable(self, position='bottom', relativeTo = None, chain=None):
        """Show the ResidueTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
       :param chain: optional chain with Residue's to display
        """
        from ccpn.ui.gui.modules.ResidueTable import ResidueTableModule
        return self._showModule(ResidueTableModule, position=position, relativeTo=relativeTo,
                                selection=chain)

    @logCommand('ui.')
    def showPeakTable(self, position='bottom', relativeTo = None, peakList=None):
        """Show the PeakTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param peakList: optional peakList with Peaks to display; default derived from current.peaks
        """
        from ccpn.ui.gui.modules.PeakTable import PeakTableModule
        _module = self._showModule(PeakTableModule, position=position, relativeTo=relativeTo)
        if not peakList and self.current.peak:
            peakList = self.current.peak.peakList
        if peakList:
            _module.selectTable(peakList)
            _module.selectPeaks(self.current.peaks)

    @logCommand('ui.')
    def showIntegralTable(self, position='bottom', relativeTo = None, integralList=None):
        """Show the IntegralTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param integralList: optional integralList to display
        """
        from ccpn.ui.gui.modules.IntegralTable import IntegralTableModule
        return self._showModule(IntegralTableModule, position=position, selection=integralList)

    @logCommand('ui.')
    def showMultipletTable(self, position='bottom', relativeTo = None, multipletList=None):
        """Show the MultipletTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param multipletList: optional multipletList to display
        """
        from ccpn.ui.gui.modules.MultipletTable import MultipletTableModule
        return self._showModule(MultipletTableModule, position=position, relativeTo=relativeTo,
                                selection=multipletList)

    @logCommand('ui.')
    def showDataTable(self, position='bottom', relativeTo = None, dataTable=None):
        """Show the DataTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param dataTable: optional dataTable to display
        """
        from ccpn.ui.gui.modules.DataTableModule import DataTableModule
        return self._showModule(DataTableModule, position=position, relativeTo=relativeTo,
                                selection=dataTable)

    @logCommand('ui.')
    def showRestraintTable(self, position='bottom', relativeTo=None, restraintTable=None):
        """Show the restraintTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param restraintTable: optional restraintTable to display
        """
        from ccpn.ui.gui.modules.RestraintTableModule import RestraintTableModule
        return self._showModule(RestraintTableModule, position=position, relativeTo=relativeTo,
                                selection=restraintTable)

    @logCommand('ui.')
    def showViolationTable(self, position='bottom', relativeTo=None, violationTable=None):
        """Show the restraintTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param violationTable: optional violationTable to display
        """
        from ccpn.ui.gui.modules.ViolationTableModule import ViolationTableModule
        return self._showModule(ViolationTableModule, position=position, relativeTo=relativeTo,
                                selection=violationTable)

    @logCommand('ui.')
    def showStructureEnsembleTable(self, position='bottom', relativeTo=None, structureEnsemble=None):
        """Show the structureEnsembleTable module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param structureEnsemble: optional structure ensemble to display
        """
        from ccpn.ui.gui.modules.StructureTable import StructureTableModule
        return self._showModule(StructureTableModule, position=position, relativeTo=relativeTo,
                                selection=structureEnsemble)

    @logCommand('ui.')
    def showChemicalShiftMapping(self, position: str = 'top', relativeTo = None):
        """Show the ChemicalShiftMapping module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        """
        from ccpn.ui.gui.modules.experimentAnalysis.ChemicalShiftPerturbationGuiModule import ChemicalShiftPerturbationGuiModule
        return self._showModule(ChemicalShiftPerturbationGuiModule, position=position, relativeTo=relativeTo)

    @logCommand('ui.')
    def showRelaxationModule(self, position: str = 'top', relativeTo = None):
        """Show the Relaxation module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        """
        from ccpn.ui.gui.modules.experimentAnalysis.RelaxationGuiModule import RelaxationGuiModule
        return self._showModule(RelaxationGuiModule, position=position, relativeTo=relativeTo)

    @logCommand('ui.')
    def showNotesEditor(self, position: str = 'top', relativeTo = None, note=None):
        """Show the Notes editor module
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        :param note: optional note to display
        """
        from ccpn.ui.gui.modules.NotesEditor import NotesEditorModule
        _module = self._showModule(NotesEditorModule, position=position, relativeTo=relativeTo)
        if note:
            _module.selectNote(note)
        return _module

    #-----------------------------------------------------------------------------------------
    # Spectra
    #-----------------------------------------------------------------------------------------

    @logCommand('ui.')
    def editSpectrumGroup(self, editMode:bool = True):
        """Show a popup to edit or create a SpectrumGroup
        :param editMode: a flag to set edit (True) or create (False)
        """
        from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor

        if not editMode and not self.project.spectra:
            getLogger().warning('Project contains no Specta. SpectrumGroup cannot be created')
            MessageDialog.showWarning('Project contains no spectra.', 'SpectrumGroup cannot be created')
            return

        if editMode and not self.project.spectrumGroups:
            _txt1, _txt2 = 'Project contains no SpectumGroups', 'SpectrumGroups cannot be edited'
            getLogger().warning(_txt1 + _txt2)
            MessageDialog.showWarning(_txt1, _txt2)
            return

        _mainWindow = self.mainWindow
        _obj = self.project.spectrumGroups[0] if editMode else None
        _popup = SpectrumGroupEditor(parent=_mainWindow._widget, mainWindow=_mainWindow,
                                     editMode=editMode, obj=_obj)
        _popup.exec_()

    @logCommand('ui.')
    def newSpectrumGroupFromPseudoSpectrum(self, spectrum=None):
        """Show a popup to make a new SpectrumGroup from an nD pseudo-spectrum, extracting lower dimensional spectra
        :param spectrum: Optional Spectrum instance
        """
        from ccpn.ui.gui.popups.PseudoToSpectrumGroupPopup import PseudoToSpectrumGroupPopup

        if not self.project.spectra:
            getLogger().warning('Project has no Spectra. Pseudo Spectrum to SpectrumGroup Popup cannot be displayed')
            MessageDialog.showWarning('Project contains no spectra.',
                                      'Pseudo Spectrum to SpectrumGroup Popup cannot be displayed')
            return

        _mainWindow = self.mainWindow
        popup = PseudoToSpectrumGroupPopup(parent=_mainWindow._widget, mainWindow=_mainWindow, spectrum=spectrum)
        popup.exec_()

    @logCommand('ui.')
    def makeStripPlot(self, includePeakLists=True, includeNmrChains=True, includeNmrChainPullSelection=True):
        """Make a strip plot from peaks or nmrChains
        """
        from ccpn.ui.gui.popups.StripPlotPopup import StripPlotPopup

        if not self.project.peaks and not self.project.nmrResidues and not self.project.nmrChains:
            getLogger().warning('Cannot make strip plot, nothing to display')
            MessageDialog.showWarning('Cannot make strip plot,', 'nothing to display')
            return

        if self.current.strip is None or self.current.strip.isDeleted:
            MessageDialog.showWarning('Make Strip Plot', 'No selected spectrumDisplay')
            return

        popup = StripPlotPopup(parent=self.mainWindow, mainWindow=self.mainWindow,
                               spectrumDisplay=self.current.strip.spectrumDisplay,
                               includePeakLists=includePeakLists,
                               includeNmrChains=includeNmrChains,
                               includeNmrChainPullSelection=includeNmrChainPullSelection,
                               includeSpectrumTable=False)
        popup.exec_()

    @logCommand('ui.')
    def makeProjection(self):
        """Make a projection from a spectrum
        """
        from ccpn.ui.gui.popups.SpectrumProjectionPopup import SpectrumProjectionPopup
        if not self.project.spectra:
            getLogger().warning('Project has no Spectra. No Projection can be made')
            MessageDialog.showWarning('Project contains no spectra.', 'No Projection can be made')
            return

        popup = SpectrumProjectionPopup(parent=self.mainWindow._widget, mainWindow=self.mainWindow)
        popup.exec_()

    @logCommand('ui.')
    def setExperimentTypes(self):
        """Set the experiment types of the spectra in the project.
        """
        from ccpn.ui.gui.popups.ExperimentTypePopup import ExperimentTypePopup
        if not self.project.spectra:
            getLogger().warning('Experiment Type Selection: Project has no Spectra.')
            MessageDialog.showWarning('Experiment Type Selection', 'Project has no Spectra.')
            return

        popup = ExperimentTypePopup(parent=self.mainWindow._widget, mainWindow=self.mainWindow)
        popup.exec_()

    @logCommand('ui.')
    def validatePaths(self, spectra: tuple | list =()):
        """Validate the paths of spectra
        :param spectra: the spectra to validate; defaults to all contained in the project.
        """
        from ccpn.ui.gui.popups.ValidateSpectraPopup import ValidateSpectraPopup
        if not self.project.spectra:
            getLogger().warning('Validate Spectrum Paths Selection: Project has no Spectra.')
            MessageDialog.showWarning('Validate Spectrum Paths Selection', 'Project has no Spectra.')
            return

        popup = ValidateSpectraPopup(mainWindow=self.mainWindow, spectra=spectra)
        popup.exec_()

    @logCommand('ui.')
    def pick1DPeaks(self):
        """Pick 1D peaks
        """
        from ccpn.ui.gui.popups.PickPeaks1DPopup import PickPeak1DPopup

        if not self.project.peakLists:
            getLogger().warning('Peak Picking: Project has no peakLists.')
            MessageDialog.showWarning('Peak Picking', 'Project has no peakLists.')
            return

        spectra = [spec for spec in self.project.spectra if spec.dimensionCount == 1]
        if len(spectra) == 0:
            getLogger().warning('Peak Picking: Project has no 1D Spectra.')
            MessageDialog.showWarning('Peak Picking', 'Project has no 1D Spectra.')
            return

        popup = PickPeak1DPopup(parent=self.mainWindow._widget, mainWindow=self.mainWindow)
        popup.exec_()

    @logCommand('ui.')
    def pickNDPeaks(self):
        """Pick nD peaks
        """
        from ccpn.ui.gui.popups.PickNDPeaksPopup import PickNDPeaksPopup

        if not self.project.peakLists:
            getLogger().warning('Peak Picking: Project has no peakLists.')
            MessageDialog.showWarning('Peak Picking', 'Project has no peakLists.')
            return

        spectra = [spec for spec in self.project.spectra if spec.dimensionCount > 1]
        if len(spectra) == 0:
            getLogger().warning('Peak Picking: Project has no nD Spectra.')
            MessageDialog.showWarning('Peak Picking', 'Project has no nD Spectra.')
            return

        popup = PickNDPeaksPopup(parent=self.mainWindow, mainWindow=self.mainWindow)
        popup.exec_()

    @logCommand('ui.')
    def copyPeakList(self):
        """Open a popup to copy a peakList between spectra
        """
        from ccpn.ui.gui.popups.CopyPeakListPopup import CopyPeakListPopup

        if not self.project.peakLists:
            txt = 'Project has no PeakList\'s. Peak Lists cannot be copied'
            getLogger().warning(txt)
            MessageDialog.showWarning('Cannot perform a copy', txt)
            return

        popup = CopyPeakListPopup(parent=self.mainWindow._widget, mainWindow=self.mainWindow)
        popup.exec_()

    @logCommand('ui.')
    def copyPeaks(self, useCurrent: bool = False):
        """Open a popup to select peaks to copy between spectra.
        :param useCurrent: If True, use currently selected peaks.
        """
        from ccpn.ui.gui.popups.CopyPeaksPopup import CopyPeaks

        if not self.project.peaks:
            getLogger().warning('Project has no Peaks: Peaks cannot be copied')
            MessageDialog.showWarning('Project has no Peaks', 'Peaks cannot be copied')
            return

        popup = CopyPeaks(parent=self.mainWindow._widget, mainWindow=self.mainWindow)
        if useCurrent:
            peaks = self.current.peaks
            popup._selectPeaks(peaks)
        popup.exec_()

    @logCommand('ui.')
    def estimateVolumes(self):
        """Open a popup to estimate the volume of peaks in selected peakLists
        """
        from ccpn.ui.gui.popups.EstimateVolumes import EstimatePeakListVolumesPopup

        if not self.project.peakLists:
            getLogger().warning('Estimate Volumes: Project has no peakLists.')
            MessageDialog.showWarning('Estimate Volumes', 'Project has no peakLists.')
            return

        spectra = self.project.spectra
        if spectra:
            popup = EstimatePeakListVolumesPopup(parent=self.mainWindow,
                                                 mainWindow=self.mainWindow,
                                                 spectra=spectra)
            popup.exec_()

    #-----------------------------------------------------------------------------------------
    # Molecules
    #-----------------------------------------------------------------------------------------

    @logCommand('ui.')
    def showResidueInformation(self, position='bottom', relativeTo = None):
        """Displays Residue Information module.
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        """
        from ccpn.ui.gui.modules.ResidueInformation import ResidueInformation

        if not self.project.residues:
            getLogger().warning(
                'No Residues in project. Residue Information Module requires Residues in the project to launch.')
            MessageDialog.showWarning('No Residues in project.',
                                      'Residue Information Module requires Residues in the project to launch.')
            return

        _module = ResidueInformation(mainWindow=self.mainWindow)
        self.mainWindow._addModule(_module, position=position, relativeTo=relativeTo)
        return _module

    @logCommand('ui.')
    def showReferenceChemicalShifts(self, position='left', relativeTo = None):
        """Displays Reference Chemical Shifts module.
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
       """
        from ccpn.ui.gui.modules.ReferenceChemicalShifts import ReferenceChemicalShifts

        _module = ReferenceChemicalShifts(mainWindow=self.mainWindow)
        self.mainWindow._addModule(_module, position=position, relativeTo=relativeTo)
        return _module

    #-----------------------------------------------------------------------------------------
    # Macro
    #-----------------------------------------------------------------------------------------

    @logCommand('ui.')
    def showMacroEditor(self, path=None, position='top', relativeTo = None):
        """Open a the macro editor
        :param path: optional path to python file
        :param position: relative position where to place the module (e.g. 'top', bottom', 'left', 'right')
        :param relativeTo: module relative to which position is applied.
        """
        # local to prevent circular import
        from ccpn.ui.gui.modules.MacroEditor import MacroEditor

        path = str(path) if path is not None else None
        macroEditor = MacroEditor(mainWindow=self.mainWindow, filePath=path, restore=False)
        self.mainWindow._addModule(macroEditor, position=position, relativeTo=relativeTo)
        return macroEditor

    @logCommand('ui.')
    def runMacro(self, path: str | Path = None):
        """
        Runs a python macro if a path is specified, or opens a dialog box for selection of a macro file and then
        runs the selected macro.
        :param path: optional path to python file to run as macro
        """
        if path is None:
            fType = '*.py'
            dialog = FileDialog.MacrosFileDialog(parent=self.mainWindow, acceptMode='run', fileFilter=fType)
            dialog._show()
            path = dialog.selectedFile()
            if not path:
                return

        # use application to run the macro
        self.application.runMacro(path)

    #-----------------------------------------------------------------------------------------
    # help
    #-----------------------------------------------------------------------------------------

    def _showTipOfTheDay(self):
        """Helper function to show tip of the day, called from MenuDefs
        """
        self._tipOfTheDayManager._displayTipOfTheDay(standalone=True)

    def _showKeyConcepts(self):
        """Helper function to show key concepts, called from MenuDefs
        """
        self._tipOfTheDayManager._displayKeyConcepts()

#-----------------------------------------------------------------------------------------
# Helper code
#-----------------------------------------------------------------------------------------

def _getOpenLayoutPath(mainWindow):
    """Opens a saved Layout as dialog box and gets directory specified in the
    file dialog.
    :return selected path or None
    """
    from ccpn.ui.gui.widgets.FileDialog import LayoutsFileDialog

    fType = 'JSON (*.json)'
    dialog = LayoutsFileDialog(parent=mainWindow, acceptMode='open', fileFilter=fType)
    dialog._show()
    path = dialog.selectedFile()
    return path or None


def _getSaveLayoutPath(mainWindow):
    """Opens save Layout as dialog box and gets directory specified in the
    file dialog.
    :return selected path or None
    """
    from ccpn.ui.gui.widgets.FileDialog import LayoutsFileDialog
    from ccpn.ui.gui.Layout import JSON_SUFFIX

    fType = 'JSON (*.json)'
    dialog = LayoutsFileDialog(parent=mainWindow, acceptMode='save', fileFilter=fType)
    dialog._show()
    newPath = dialog.selectedFile()
    if not newPath:
        return None

    newPath = aPath(newPath)
    if newPath.exists():
        # should not really need to check the second and third condition above, only
        # the Qt dialog stupidly insists a directory exists before you can select it
        # so if it exists but is empty then don't bother asking the question
        title = 'Overwrite path'
        msg = 'Path "%s" already exists, continue?' % newPath
        if not MessageDialog.showYesNo(title, msg):
            return None

    newPath.assureSuffix(JSON_SUFFIX)
    return newPath
