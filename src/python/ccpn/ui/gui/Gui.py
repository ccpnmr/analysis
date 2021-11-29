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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2021-11-29 15:35:08 +0000 (Mon, November 29, 2021) $"
__version__ = "$Revision: 3.0.4 $"
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
from PyQt5 import QtWidgets, QtCore
from ccpn.core import _coreClassMap
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib.ContextManagers import notificationEchoBlocking
from ccpn.ui.Ui import Ui
from ccpn.ui.gui.popups.RegisterPopup import RegisterPopup, NewTermsConditionsPopup
from ccpn.ui.gui.widgets.Application import Application
from ccpn.ui.gui.widgets.MessageDialog import showError, showWarning
from ccpn.ui.gui.widgets.Font import getFontHeight, setWidgetFont
# This import initializes relative paths for QT style-sheets.  Do not remove!
from ccpn.framework.PathsAndUrls import userPreferencesPath
from ccpn.util import Logging
from ccpn.util import Register


def qtMessageHandler(*errors):
    for err in errors:
        Logging.getLogger().warning('QT error: %s' % err)


# REMOVEDEBUG = r'\(\w+\.\w+:\d+\)$'
REMOVEDEBUG = r'\(\S+\.\w+:\d+\)$'

# un/suppress messages
QtCore.qInstallMessageHandler(qtMessageHandler)


class _MyAppProxyStyle(QtWidgets.QProxyStyle):
    """Class to handle resizing icons in menus
    """

    def pixelMetric(self, QStyle_PixelMetric, option=None, widget=None):
        if QStyle_PixelMetric == QtWidgets.QStyle.PM_SmallIconSize:
            # change the size of the icons in menus - overrides checkBoxes in menus
            return (getFontHeight() or 15) + 3
        elif QStyle_PixelMetric in (QtWidgets.QStyle.PM_IndicatorHeight,
                                    QtWidgets.QStyle.PM_IndicatorWidth,
                                    QtWidgets.QStyle.PM_ExclusiveIndicatorWidth,
                                    QtWidgets.QStyle.PM_ExclusiveIndicatorHeight,
                                    ):
            # change the sizeof checkBoxes and radioButtons
            return (getFontHeight() or 17) - 2
        elif QStyle_PixelMetric == QtWidgets.QStyle.PM_MessageBoxIconSize:
            # change the iconsize in messageDialog
            return getFontHeight(size='MAXIMUM') or 18
        else:
            return super().pixelMetric(QStyle_PixelMetric, option, widget)

    # def drawPrimitive(self, element: QtWidgets.QStyle.PrimitiveElement, option: 'QStyleOption', painter: QtGui.QPainter, widget: typing.Optional[QtWidgets.QWidget] = ...) -> None:
    #     if element == QtWidgets.QStyle.PE_IndicatorBranch:
    #         # draw a scaled image here
    #
    #         # QPixmap
    #         # pixmap;
    #         # pixmap.load(":/res/background.jpg");
    #         # QPainter
    #         # paint(this);
    #         # int
    #         # widWidth = this->ui->centralWidget->width();
    #         # int
    #         # widHeight = this->ui->centralWidget->height();
    #         # pixmap = pixmap.scaled(widWidth, widHeight, Qt::KeepAspectRatioByExpanding);
    #         # paint.drawPixmap(0, 0, pixmap);
    #     else:
    #         return super(_MyAppProxyStyle, self).drawPrimitive(element, option, painter, widget)


class Gui(Ui):
    # Factory functions for UI-specific instantiation of wrapped graphics classes
    _factoryFunctions = {}

    def __init__(self, application):
        Ui.__init__(self, application)
        self._initQtApp()

    def _initQtApp(self):
        # On the Mac (at least) it does not matter what you set the applicationName to be,
        # it will come out as the executable you are running (e.g. "python3")

        # # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
        # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts, True)
        # viewportFormat = QtGui.QSurfaceFormat()
        # viewportFormat.setSwapInterval(0)  #disable VSync
        # viewportFormat.setSwapBehavior(QtGui.QSurfaceFormat.SingleBuffer)
        # QtGui.QSurfaceFormat().setDefaultFormat(viewportFormat)
        # # self._CcpnGLWidget.setFormat(viewportFormat)
        # # viewportFormat = self._CcpnGLWidget.format()

        # styles = QtWidgets.QStyleFactory()
        # myStyle = _MyAppProxyStyle(styles.create('fusion'))
        # QtWidgets.QApplication.setStyle(myStyle)

        self.qtApp = Application(self.application.applicationName,
                                 self.application.applicationVersion,
                                 organizationName='CCPN', organizationDomain='ccpn.ac.uk')

        styles = QtWidgets.QStyleFactory()
        myStyle = _MyAppProxyStyle(styles.create('fusion'))
        # # QtWidgets.QApplication.setStyle(myStyle)
        #
        self.qtApp.setStyle(myStyle)  # styles.create('fusion'))

    def initialize(self, mainWindow):
        """UI operations done after every project load/create"""

        with notificationEchoBlocking():
            # Set up mainWindow
            self.mainWindow = self._setupMainWindow(mainWindow)

            self.application.initGraphics()

            project = self.application.project
            current = self.application.current

    def start(self):
        self.mainWindow._fillRecentMacrosMenu()
        self.mainWindow._updateRestoreArchiveMenu()
        project = self.application.project
        self.application.experimentClassifications = project.getExperimentClassifications()

        self.mainWindow.show()
        QtWidgets.QApplication.setActiveWindow(self.mainWindow)

        # check whether to skip the execution loop for testing with mainWindow
        import builtins

        _skip = getattr(builtins, '_skipExecuteLoop', False)
        if not _skip:
            self.qtApp.start()

    def _registerDetails(self, registered=False, acceptedTerms=False):
        """Display registration popup"""
        days = Register._graceCounter(Register._fetchGraceFile(self.application))
        # check valid internet connection first
        if not Register.checkInternetConnection():
            msg = 'Could not connect to the registration server, please check your internet connection. ' \
                  'Register within %s day(s) to continue using the software' % str(days)
            showError('Registration', msg)

        else:
            if registered and not acceptedTerms:
                popup = NewTermsConditionsPopup(self.mainWindow, trial=days, version=self.application.applicationVersion, modal=True)
            else:
                popup = RegisterPopup(self.mainWindow, trial=days, version=self.application.applicationVersion, modal=True)

            self.mainWindow.show()
            popup.exec_()
            self.qtApp.processEvents()

    def _setupMainWindow(self, mainWindow):
        # Set up mainWindow

        project = self.application.project
        mainWindow.sideBar.buildTree(project, False)

        mainWindow.raise_()
        mainWindow.namespace['current'] = self.application.current
        return mainWindow

    def echoCommands(self, commands: typing.List[str]):
        """Echo commands strings, one by one, to logger
        and store them in internal list for perusal
        """
        logger = Logging.getLogger()
        for command in commands:
            logger.echoInfo(command)

        if self.application.ui is not None and \
           self.application.ui.mainWindow is not None and \
           self.application._enableLoggingToConsole:

            console = self.application.ui.mainWindow.pythonConsole
            for command in commands:
                command = re.sub(REMOVEDEBUG, '', command)
                console._write(command + '\n')

    def getByGid(self, gid):
        return self.application.getByGid(gid)

    def _execUpdates(self):
        sys.stderr.write('==> Gui update\n')
        from ccpn.framework.update.UpdatePopup import UpdatePopup
        from ccpn.util import Url

        # check valid internet connection first
        if Url.checkInternetConnection():
            self.updatePopup = UpdatePopup(parent=self.mainWindow, mainWindow=self.mainWindow)
            self.updatePopup.exec_()

            # if updates have been installed then popup the quit dialog with no cancel button
            if self.updatePopup._numUpdatesInstalled > 0:
                self.mainWindow._closeWindowFromUpdate(disableCancel=True)

        else:
            showWarning('Check For Updates',
                        'Could not connect to the update server, please check your internet connection.')

    def loadProject(self, path):
        """Just a stub for now; calling MainWindow methods as it initialises the Gui
        """
        return self.mainWindow._loadProject(path)

#######################################################################################
#
#  Ui classes that map ccpn.ui._implementation
#
#######################################################################################


## Window class
coreClass = _coreClassMap['Window']
#
from ccpn.ui.gui.lib.GuiMainWindow import GuiMainWindow as _GuiMainWindow


class MainWindow(coreClass, _GuiMainWindow):
    """GUI main window, corresponds to OS window"""

    def __init__(self, project: Project, wrappedData: 'ApiWindow'):
        # AbstractWrapperObject.__init__(self, project, wrappedData)
        super().__init__(project, wrappedData)

        logger = Logging.getLogger()

        logger.debug('MainWindow>> project: %s' % project)
        logger.debug('MainWindow>> project._appBase: %s' % project._appBase)

        application = project._appBase
        _GuiMainWindow.__init__(self, application=application)

        # hide the window here and make visible later
        self.hide()

        # patches for now:
        project._mainWindow = self
        logger.debug('MainWindow>> project._mainWindow: %s' % project._mainWindow)

        application._mainWindow = self
        application.ui.mainWindow = self
        logger.debug('MainWindow>> application: %s' % application)
        logger.debug('MainWindow>> application.project: %s' % application.project)
        logger.debug('MainWindow>> application._mainWindow: %s' % application._mainWindow)
        logger.debug('MainWindow>> application.ui.mainWindow: %s' % application.ui.mainWindow)

        setWidgetFont(self, )


from ccpn.ui.gui.lib.GuiWindow import GuiWindow as _GuiWindow


#TODO: copy from MainWindow
class SideWindow(coreClass, _GuiWindow):
    """GUI side window, corresponds to OS window"""

    def __init__(self, project: Project, wrappedData: 'ApiWindow'):
        AbstractWrapperObject.__init__(self, project, wrappedData)
        _GuiWindow.__init__(self, project.application)


def _factoryFunction(project: Project, wrappedData) -> coreClass:
    """create Window, dispatching to subtype depending on wrappedData"""
    if wrappedData.title == 'Main':
        return MainWindow(project, wrappedData)
    else:
        return SideWindow(project, wrappedData)


Gui._factoryFunctions[coreClass.className] = _factoryFunction

## Task class
# There is no special GuiTask, so nothing needs to be done


## Mark class - put in namespace for documentation
Mark = _coreClassMap['Mark']

## SpectrumDisplay class
coreClass = _coreClassMap['SpectrumDisplay']
from ccpn.ui.gui.modules.SpectrumDisplay1d import SpectrumDisplay1d as _SpectrumDisplay1d


#also change for this class as done for the Nd variant below; this involves
#chaning the init signature of the SpectrumDisplay1d and passing the parameters along to
# GuiSpectrumDisplay

class StripDisplay1d(coreClass, _SpectrumDisplay1d):
    """1D bound display"""

    def __init__(self, project: Project, wrappedData: 'ApiBoundDisplay'):
        """Local override init for Qt subclass"""
        Logging.getLogger().debug('StripDisplay1d>> project: %s, project._appBase: %s' % (project, project._appBase))
        AbstractWrapperObject.__init__(self, project, wrappedData)

        # hack for now
        self.application = project._appBase

        _SpectrumDisplay1d.__init__(self, mainWindow=self.application.ui.mainWindow,
                                    # name=self._id
                                    )

        # 20191113: ED moved to initGraphics
        # if not project._isNew:
        #     # hack for now;  Needs to know this for restoring the GuiSpectrum Module. This has to be removed after decoupling Gui and Data!
        #     # This is a normal guiModule that should be opened in module area from the position
        #     # where is created. E.g. and not hardcoded on the "right" and coupled with api calls!
        #     self.application.ui.mainWindow.moduleArea.addModule(self, position='right',
        #                                                         relativeTo=self.application.ui.mainWindow.moduleArea)


from ccpn.ui.gui.modules.SpectrumDisplayNd import SpectrumDisplayNd as _SpectrumDisplayNd


#TODO: Need to check on the consequences of hiding name from the wrapper
# NB: GWV had to comment out the name property to make it work
# conflicts existed between the 'name' and 'window' attributes of the two classes
# the pyqtgraph decendents need name(), GuiStripNd had 'window', but that could be replaced with
# mainWindow throughout

class SpectrumDisplayNd(coreClass, _SpectrumDisplayNd):
    """ND bound display"""

    def __init__(self, project: Project, wrappedData: 'ApiBoundDisplay'):
        """Local override init for Qt subclass"""
        Logging.getLogger().debug('SpectrumDisplayNd>> project: %s, project._appBase: %s' % (project, project._appBase))
        AbstractWrapperObject.__init__(self, project, wrappedData)

        # hack for now;
        self.application = project._appBase

        _SpectrumDisplayNd.__init__(self, mainWindow=self.application.ui.mainWindow,
                                    # name=self._id)
                                    )

        # 20191113: ED moved to initGraphics
        # if not project._isNew:
        #     # hack for now;  Needs to know this for restoring the GuiSpectrum Module. This has to be removed after decoupling Gui and Data!
        #     # This is a normal guiModule that should be opened in module area from the position
        #     # where is created. E.g. and not hardcoded on the "right" and coupled with api calls!
        #     self.application.ui.mainWindow.moduleArea.addModule(self, position='right',
        #                                                         relativeTo=self.application.ui.mainWindow.moduleArea)


#old name
StripDisplayNd = SpectrumDisplayNd


def _factoryFunction(project: Project, wrappedData) -> coreClass:
    """create SpectrumDisplay, dispatching to subtype depending on wrappedData"""
    if wrappedData.is1d:
        return StripDisplay1d(project, wrappedData)
    else:
        return StripDisplayNd(project, wrappedData)


Gui._factoryFunctions[coreClass.className] = _factoryFunction

## Strip class
coreClass = _coreClassMap['Strip']
from ccpn.ui.gui.lib.GuiStrip1d import GuiStrip1d as _GuiStrip1d


class Strip1d(coreClass, _GuiStrip1d):
    """1D strip"""

    def __init__(self, project: Project, wrappedData: 'ApiBoundStrip'):
        """Local override init for Qt subclass"""

        AbstractWrapperObject.__init__(self, project, wrappedData)

        Logging.getLogger().debug('Strip1d>> spectrumDisplay: %s' % self.spectrumDisplay)
        _GuiStrip1d.__init__(self, self.spectrumDisplay)

        # cannot add the Frame until fully done
        strips = self.spectrumDisplay.orderedStrips
        if self in strips:
            stripIndex = strips.index(self)
        else:
            stripIndex = len(strips)
            Logging.getLogger().warning('Strip ordering not defined for %s in %s' % (str(self.pid), str(self.spectrumDisplay.pid)))

        tilePosition = self.tilePosition

        if self.spectrumDisplay.stripArrangement == 'Y':

            # strips are arranged in a row
            # self.spectrumDisplay.stripFrame.layout().addWidget(self, 0, stripIndex)

            if True:  #tilePosition is None:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, 0, stripIndex)
                self.tilePosition = (0, stripIndex)
            else:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, tilePosition[0], tilePosition[1])

        elif self.spectrumDisplay.stripArrangement == 'X':

            # strips are arranged in a column
            # self.spectrumDisplay.stripFrame.layout().addWidget(self, stripIndex, 0)

            if True:  #tilePosition is None:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, stripIndex, 0)
                self.tilePosition = (0, stripIndex)
            else:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, tilePosition[1], tilePosition[0])

        elif self.spectrumDisplay.stripArrangement == 'T':

            # NOTE:ED - Tiled plots not fully implemented yet
            Logging.getLogger().warning('Tiled plots not implemented for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))

        else:
            Logging.getLogger().warning('Strip direction is not defined for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))


from ccpn.ui.gui.lib.GuiStripNd import GuiStripNd as _GuiStripNd


class StripNd(coreClass, _GuiStripNd):
    """ND strip """

    def __init__(self, project: Project, wrappedData: 'ApiBoundStrip'):
        """Local override init for Qt subclass"""

        AbstractWrapperObject.__init__(self, project, wrappedData)

        Logging.getLogger().debug('StripNd>> spectrumDisplay: %s' % self.spectrumDisplay)
        _GuiStripNd.__init__(self, self.spectrumDisplay)

        # cannot add the Frame until fully done
        strips = self.spectrumDisplay.orderedStrips
        if self in strips:
            stripIndex = strips.index(self)
        else:
            stripIndex = len(strips)
            Logging.getLogger().warning('Strip ordering not defined for %s in %s' % (str(self.pid), str(self.spectrumDisplay.pid)))

        tilePosition = self.tilePosition

        if self.spectrumDisplay.stripArrangement == 'Y':

            # strips are arranged in a row
            # self.spectrumDisplay.stripFrame.layout().addWidget(self, 0, stripIndex)

            if True:  #tilePosition is None:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, 0, stripIndex)
                self.tilePosition = (0, stripIndex)
            else:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, tilePosition[0], tilePosition[1])

        elif self.spectrumDisplay.stripArrangement == 'X':

            # strips are arranged in a column
            # self.spectrumDisplay.stripFrame.layout().addWidget(self, stripIndex, 0)

            if True:  #tilePosition is None:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, stripIndex, 0)
                self.tilePosition = (0, stripIndex)
            else:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, tilePosition[1], tilePosition[0])

        elif self.spectrumDisplay.stripArrangement == 'T':

            # NOTE:ED - Tiled plots not fully implemented yet
            Logging.getLogger().warning('Tiled plots not implemented for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))

        else:
            Logging.getLogger().warning('Strip direction is not defined for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))


def _factoryFunction(project: Project, wrappedData) -> coreClass:
    """create SpectrumDisplay, dispatching to subtype depending on wrappedData"""
    apiSpectrumDisplay = wrappedData.spectrumDisplay
    if apiSpectrumDisplay.is1d:
        return Strip1d(project, wrappedData)
    else:
        return StripNd(project, wrappedData)


Gui._factoryFunctions[coreClass.className] = _factoryFunction

## Axis class - put in namespace for documentation
Axis = _coreClassMap['Axis']

# Any Factory function to _implementation or abstractWrapper
#
## SpectrumView class
coreClass = _coreClassMap['SpectrumView']
from ccpn.ui.gui.lib.GuiSpectrumView1d import GuiSpectrumView1d as _GuiSpectrumView1d


class _SpectrumView1d(coreClass, _GuiSpectrumView1d):
    """1D Spectrum View"""

    def __init__(self, project: Project, wrappedData: 'ApiStripSpectrumView'):
        """Local override init for Qt subclass"""
        AbstractWrapperObject.__init__(self, project, wrappedData)

        # hack for now
        self._appBase = project._appBase
        self.application = project._appBase

        Logging.getLogger().debug('SpectrumView1d>> %s' % self)
        _GuiSpectrumView1d.__init__(self)


from ccpn.ui.gui.lib.GuiSpectrumViewNd import GuiSpectrumViewNd as _GuiSpectrumViewNd


class _SpectrumViewNd(coreClass, _GuiSpectrumViewNd):
    """ND Spectrum View"""

    def __init__(self, project: Project, wrappedData: 'ApiStripSpectrumView'):
        """Local override init for Qt subclass"""
        AbstractWrapperObject.__init__(self, project, wrappedData)

        # hack for now
        self._appBase = project._appBase
        self.application = project._appBase

        Logging.getLogger().debug('SpectrumViewNd>> %s %s' % (self, self.strip))
        _GuiSpectrumViewNd.__init__(self)


def _factoryFunction(project: Project, wrappedData) -> coreClass:
    """create SpectrumView, dispatching to subtype depending on wrappedData"""
    if 'intensity' in wrappedData.strip.spectrumDisplay.axisCodes:
        # 1D display
        return _SpectrumView1d(project, wrappedData)
    else:
        # ND display
        return _SpectrumViewNd(project, wrappedData)


Gui._factoryFunctions[coreClass.className] = _factoryFunction

# Any Factory function to _implementation or abstractWrapper
#

## PeakListView class
coreClass = _coreClassMap['PeakListView']
from ccpn.ui.gui.lib.GuiPeakListView import GuiPeakListView as _GuiPeakListView


class _PeakListView(coreClass, _GuiPeakListView):
    """Peak List View for 1D or nD PeakList"""

    def __init__(self, project: Project, wrappedData: 'ApiStripPeakListView'):
        """Local override init for Qt subclass"""
        AbstractWrapperObject.__init__(self, project, wrappedData)
        # hack for now
        self._appBase = project._appBase
        self.application = project._appBase
        _GuiPeakListView.__init__(self)
        self._init()


Gui._factoryFunctions[coreClass.className] = _PeakListView

## IntegralListView class
coreClass = _coreClassMap['IntegralListView']
from ccpn.ui.gui.lib.GuiIntegralListView import GuiIntegralListView as _GuiIntegralListView


class _IntegralListView(coreClass, _GuiIntegralListView):
    """Integral List View for 1D or nD IntegralList"""

    def __init__(self, project: Project, wrappedData: 'ApiStripIntegralListView'):
        """Local override init for Qt subclass"""
        AbstractWrapperObject.__init__(self, project, wrappedData)
        # hack for now
        self._appBase = project._appBase
        self.application = project._appBase
        _GuiIntegralListView.__init__(self)
        self._init()


Gui._factoryFunctions[coreClass.className] = _IntegralListView

## MultipletListView class
coreClass = _coreClassMap['MultipletListView']
from ccpn.ui.gui.lib.GuiMultipletListView import GuiMultipletListView as _GuiMultipletListView


class _MultipletListView(coreClass, _GuiMultipletListView):
    """Multiplet List View for 1D or nD MultipletList"""

    def __init__(self, project: Project, wrappedData: 'ApiStripMultipletListView'):
        """Local override init for Qt subclass"""
        AbstractWrapperObject.__init__(self, project, wrappedData)
        # hack for now
        self._appBase = project._appBase
        self.application = project._appBase
        _GuiMultipletListView.__init__(self)
        self._init()


Gui._factoryFunctions[coreClass.className] = _MultipletListView

# Delete what we do not want in namespace
del _factoryFunction
del coreClass
