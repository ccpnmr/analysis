"""Module Documentation here

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:44 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import importlib, os

from PyQt5 import QtWidgets, QtCore, QtGui
from functools import partial
from copy import deepcopy

from ccpn.core.Project import Project
from ccpn.core.Peak import Peak
from ccpn.core.PeakList import PeakList
from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.Sample import Sample

#from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.ToolBar import ToolBar
#import typing

from ccpn.ui.gui.widgets.Frame import Frame  #, ScrollableFrame
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.PhasingFrame import PhasingFrame
from ccpn.ui.gui.widgets.SpectrumToolBar import SpectrumToolBar
from ccpn.ui.gui.widgets.SpectrumGroupToolBar import SpectrumGroupToolBar
#from ccpn.ui.gui.widgets.Widget import ScrollableWidget, Widget
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.MessageDialog import showWarning
#from ccpn.ui.gui.widgets.BasePopup import BasePopup
#from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.core.lib.Notifiers import Notifier
from ccpn.core.lib.AssignmentLib import _assignNmrAtomsToPeaks, _assignNmrResiduesToPeaks
from ccpn.util.Constants import MOUSEDICTSTRIP
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import PEAKSELECT, MULTIPLETSELECT
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import CcpnGLWidget

from ccpn.util.Logging import getLogger
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.NmrChain import NmrChain
from ccpn.ui.gui.lib.Strip import GuiStrip
from ccpn.ui._implementation.PeakListView import PeakListView
from ccpn.ui._implementation.IntegralListView import IntegralListView
from ccpn.ui._implementation.MultipletListView import MultipletListView
from ccpn.ui.gui.widgets.SettingsWidgets import SpectrumDisplaySettings
from ccpn.ui._implementation.SpectrumView import SpectrumView
from ccpn.core.lib.ContextManagers import undoStackBlocking, notificationBlanking, BlankedPartial, undoBlock, notificationEchoBlocking
from ccpn.util.decorators import logCommand
from ccpn.util.Common import makeIterableList
from ccpn.core.lib import Undo
from ccpn.ui.gui.widgets.MessageDialog import showMulti
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject


STRIP_SPACING = 5
AXIS_WIDTH = 30
AXISUNITS = ['ppm', 'Hz', 'points']
SPECTRUMGROUPS = 'spectrumGroups'
SPECTRUMISGROUPED = 'spectrumIsGrouped'
SPECTRUMGROUPLIST = 'spectrumGroupList'
STRIPDIRECTIONS = ['Y', 'X']
SPECTRUMDISPLAY = 'spectrumDisplay'
STRIPARRANGEMENT = 'stripArrangement'

MAXITEMLOGGING = 4


class GuiSpectrumDisplay(CcpnModule):
    """
    Main spectrum display Module object.

    This module inherits the following attributes from the SpectrumDisplay wrapper class:

    title             Name of spectrumDisplay;
                        :return <str>
    stripDirection    Strip axis direction
                        :return <str>:('X', 'Y', None) - None only for non-strip plots
    stripCount        Number of strips
                        :return <str>.
    comment           Free-form text comment
                        comment = <str>
                        :return <str>
    axisCodes         Fixed string Axis codes in original display order
                        :return <tuple>:(X, Y, Z1, Z2, ...)
    axisOrder         String Axis codes in display order, determine axis display order
                        axisOrder = <sequence>:(X, Y, Z1, Z2, ...)
                        :return <tuple>:(X, Y, Z1, Z2, ...)
    is1D              True if this is a 1D display
                        :return <bool>
    window            Gui window showing SpectrumDisplay
                        window = <Window>
                        :return <Window>
    nmrResidue        NmrResidue attached to SpectrumDisplay
                        nmrResidue = <NmrResidue>
                        :return <NmrResidue>
    positions         Axis centre positions, in display order
                        positions = <Tuple>
                        :return <Tuple>
    widths            Axis display widths, in display order
                        widths = <Tuple>
                        :return <Tuple>
    units             Axis units, in display order
                        :return <Tuple>

    parameters        Keyword-value dictionary of parameters.
                        NB the value is a copy - modifying it will not modify the actual data.
                        Values can be anything that can be exported to JSON,
                        including OrderedDict, numpy.ndarray, ccpn.util.Tensor,
                        or pandas DataFrame, Series, or Panel
                        :return <dict>
    setParameter      Add name:value to parameters, overwriting existing entries
                        setParameter(name:str, value)
                          :param name:<str> name of parameter
                          :param value: value to set
    deleteParameter   Delete parameter
                        deleteParameter(name:str)
                          :param name:<str> name of parameter to delete
    clearParameters   Delete all parameters
    updateParameters  Update list of parameters
                        updateParameters(value:dict)
                          :param value:<dict> parameter list

    resetAxisOrder    Reset display to original axis order
    findAxis          Find axis
                        findAxis(axisCode)
                          :param axisCode:
                          :return axis
    """

    # overide in specific module implementations
    includeSettingsWidget = True
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'top'
    settingsMinimumSizes = (250, 50)

    def __init__(self, mainWindow, name, useScrollArea=False):
        """
        Initialise the Gui spectrum display object

        :param mainWindow: MainWindow instance
        :param name: Title-bar name for the Module
        :param useScrollArea: Having a scrolled widget containing OpenGL and PyQtGraph widgets does not seem to work.
                              The leftmost strip is full of random garbage if it's not completely visible.
                              So for now add option below to have it turned off (False) or on (True).
        """

        getLogger().debug('GuiSpectrumDisplay>> mainWindow, name: %s %s' % (mainWindow, name))
        super(GuiSpectrumDisplay, self).__init__(mainWindow=mainWindow, name=name,
                                                 size=(1100, 1300), autoOrientation=False
                                                 )
        self.setMinimumWidth(150)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        # derive current from application
        self.current = mainWindow.application.current
        # cannot set self.project because self is a wrapper object
        # self.project = mainWindow.application.project

        # self.mainWidget will be the parent of all the subsequent widgets
        self.qtParent = self.mainWidget

        # create settings widget
        if not self.is1D:
            self._spectrumDisplaySettings = SpectrumDisplaySettings(parent=self.settingsWidget,
                                                                    mainWindow=self.mainWindow, spectrumDisplay=self,
                                                                    grid=(0, 0),
                                                                    xTexts=AXISUNITS, yTexts=AXISUNITS)
        else:
            self._spectrumDisplaySettings = SpectrumDisplaySettings(parent=self.settingsWidget,
                                                                    mainWindow=self.mainWindow, spectrumDisplay=self,
                                                                    grid=(0, 0),
                                                                    xTexts=AXISUNITS, yTexts=[''],
                                                                    showYAxis=False)

        self._spectrumDisplaySettings.settingsChanged.connect(self._settingsChanged)

        # respond to values changed in the containing spectrumDisplay settings widget
        self._spectrumDisplaySettings.stripArrangementChanged.connect(self._stripDirectionChangedInSettings)

        # GWV: Not sure what the widget argument is for
        # LM: is the spectrumDisplay, used in the widget to set actions/callbacks to the buttons
        spectrumRow = 1
        toolBarRow = 0
        stripRow = 2
        phasingRow = 3

        # self._widgetScrollArea = ScrollArea(parent=self.qtParent, scrollBarPolicies=('asNeeded', 'never'),
        #                                     grid=(spectrumRow, 0), gridSpan=(1,7))
        # self._widgetScrollArea.setWidgetResizable(True)
        #
        # self._spectrumFrame = Frame(parent=self.qtParent, setLayout=True,
        #                             grid=(spectrumRow, 0), gridSpan=(1, 7))
        # self.spectrumToolBar = SpectrumToolBar(parent=self._spectrumFrame, widget=self, grid=(0,0))
        #
        # self._widgetScrollArea.setWidget(self._spectrumFrame)
        # self._widgetScrollArea.setFixedHeight(30)
        # self._spectrumFrame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)
        # # self.spectrumToolBar.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        # self.spectrumToolBar.setFixedSize(self.spectrumToolBar.sizeHint())

        # self._spectrumFrame = Frame(parent=self.qtParent, setLayout=True,
        #                             grid=(spectrumRow, 0), gridSpan=(1, 7))
        #
        # self._leftButton = Button(parent=self._spectrumFrame, vAlign='c', hAlign='l', grid=(0, 0),
        #                          icon='icons/yellow-arrow-left')
        #
        # self.spectrumToolBar = SpectrumToolBar(parent=self._spectrumFrame, widget=self,
        #                                        grid=(0, 1))
        # self.spectrumToolBar.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        #
        # self._spacer = Spacer(self._spectrumFrame, 2, 2,
        #                       QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed, grid=(0, 2))
        #
        # self._rightButton = Button(parent=self._spectrumFrame, grid=(0, 3),
        #                          icon='icons/yellow-arrow-right')
        #
        #
        self.spectrumToolBar = SpectrumToolBar(parent=self.qtParent, widget=self,
                                               grid=(spectrumRow, 0), gridSpan=(1, 7))
        self.spectrumToolBar.setFixedHeight(30)

        # spectrumGroupsToolBar
        self.spectrumGroupToolBar = SpectrumGroupToolBar(parent=self.qtParent, spectrumDisplay=self,
                                                         grid=(spectrumRow, 0), gridSpan=(1, 7))
        self.spectrumGroupToolBar.setFixedHeight(30)
        self.spectrumGroupToolBar.hide()

        # Utilities Toolbar; filled in Nd/1d classes
        self.spectrumUtilToolBar = ToolBar(parent=self.qtParent, iconSizes=(24, 24),
                                           grid=(toolBarRow, 0), gridSpan=(1, 1),
                                           hPolicy='minimal', hAlign='left')
        self.spectrumUtilToolBar.setFixedHeight(self.spectrumToolBar.height())
        if self.application.preferences.general.showToolbar:
            self.spectrumUtilToolBar.show()
        else:
            self.spectrumUtilToolBar.hide()

        self.stripFrame = Frame(setLayout=True, showBorder=False, spacing=(5, 0), stretch=(1, 1), margins=(0, 0, 0, 0),
                                acceptDrops=True)
        # self.stripFrame.layout().setContentsMargins(0, 0, 0, 0)

        if useScrollArea:
            # scroll area for strips
            # This took a lot of sorting-out; better leave as is or test thoroughly
            self._stripFrameScrollArea = ScrollArea(parent=self.qtParent, setLayout=True,
                                                    acceptDrops=False,  # True
                                                    scrollBarPolicies=('asNeeded', 'never'))
            self._stripFrameScrollArea.setWidget(self.stripFrame)
            self._stripFrameScrollArea.setWidgetResizable(True)
            self.qtParent.getLayout().addWidget(self._stripFrameScrollArea, stripRow, 0, 1, 7)
            self._stripFrameScrollArea.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                                     QtWidgets.QSizePolicy.Expanding)
            self.stripFrame.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                          QtWidgets.QSizePolicy.Expanding)
        else:
            self._stripFrameScrollArea = None
            self.qtParent.getLayout().addWidget(self.stripFrame, stripRow, 0, 1, 7)

        includeDirection = not self.is1D
        self.phasingFrame = PhasingFrame(parent=self.qtParent,
                                         showBorder=False,
                                         includeDirection=includeDirection,
                                         callback=self._updatePhasing,
                                         returnCallback=self._updatePivot,
                                         directionCallback=self._changedPhasingDirection,
                                         applyCallback=self._applyPhasing,
                                         grid=(phasingRow, 0), gridSpan=(1, 7), hAlign='top',
                                         margins=(0, 0, 0, 0), spacing=(0, 0))
        self.phasingFrame.setVisible(False)

        # self.stripFrame.setAcceptDrops(True)

        # notifier to respond to items being dropped onto the stripFrame
        self.droppedNotifier = self.setGuiNotifier(self.stripFrame,
                                                   [GuiNotifier.DROPEVENT], [DropBase.URLS, DropBase.PIDS],
                                                   self._processDroppedItems)

        # GWV: This assures that a 'hoverbar' is visible over the strip when dragging
        # the module to another location
        self.hoverEvent = self._hoverEvent
        self.lastAxisOnly = mainWindow.application.preferences.general.lastAxisOnly
        self._phasingTraceScale = 1.0e-7
        self.stripScaleFactor = 1.0

        self._spectrumRenameNotifier = self.setNotifier(self.project,
                                                        [Notifier.RENAME],
                                                        'Spectrum',
                                                        self._spectrumRenameChanged)

        self._toolbarNotifier = self.setNotifier(self.project,
                                                 [Notifier.CHANGE],
                                                 'SpectrumDisplay',
                                                 self._toolbarChange)

        self._spectrumViewNotifier = self.setNotifier(self.project,
                                                      [Notifier.CREATE, Notifier.DELETE, Notifier.CHANGE],
                                                      SpectrumView.className,
                                                      self._spectrumViewChanged,
                                                      onceOnly=True)

        self._peakListViewNotifier = self.setNotifier(self.project,
                                                      [Notifier.CREATE, Notifier.DELETE, Notifier.CHANGE],
                                                      PeakListView.className,
                                                      self._listViewChanged,
                                                      onceOnly=True)

        self._integralListViewNotifier = self.setNotifier(self.project,
                                                          [Notifier.CREATE, Notifier.DELETE],
                                                          IntegralListView.className,
                                                          self._listViewChanged,
                                                          onceOnly=True)

        self._multipletListViewNotifier = self.setNotifier(self.project,
                                                           [Notifier.CREATE, Notifier.DELETE],
                                                           MultipletListView.className,
                                                           self._listViewChanged,
                                                           onceOnly=True)

    # GWV 20181124:
    # def _unRegisterNotifiers(self):
    #     """Unregister notifiers
    #     """
    #     if self._spectrumViewNotifier:
    #         self._spectrumViewNotifier.unRegister()

    def showAllStripHeaders(self, handle=None):
        """Convenience to show headers of all strips
        """
        for strip in self.strips:
            strip.header.headerVisible = True
            if handle:
                strip.header.handle = handle

    def hideAllStripHeaders(self, handle=None):
        """Convenience to hide headers of all strips
        """
        for strip in self.strips:
            # only hide the strips that match the handle or hide all if None
            if handle is None:
                strip.header.headerVisible = False
            elif strip.header.handle == handle:
                strip.header.headerVisible = False

    def _spectrumRenameChanged(self, data):
        """Respond to a change on the name of a spectrum
        """
        self.spectrumToolBar._spectrumRename(data)

    def _spectrumViewChanged(self, data):
        """Respond to spectrumViews being created/deleted, update contents of the spectrumWidgets frame
        """
        for strip in self.strips:
            strip._updateVisibility()

        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=None)
        GLSignals._emitAxisUnitsChanged(source=None, strip=self.strips[0], dataDict={})

    def _spectrumViewVisibleChanged(self):
        """Respond to a visibleChanged in one of the spectrumViews.
        """
        for strip in self.strips:
            strip._updateVisibility()

        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=None)
        GLSignals._emitAxisUnitsChanged(source=None, strip=self.strips[0], dataDict={})

    def _settingsChanged(self, dataDict):
        """Handle changes that occur in the settings widget
        dataDict is a dictionary of settingsWidget contents:
            {
            xUnits: range(0-number of options)
            yUnits: range(0-number of options)
            lockAspectRatio: True/False
            }
        """
        # spawn a redraw of the GL windows
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=None)
        GLSignals._emitAxisUnitsChanged(source=None, strip=self.strips[0], dataDict=dataDict)

    def _stripDirectionChangedInSettings(self, value):
        """Handle changing the stripDirection from the settings widget
        """
        if value not in range(len(STRIPDIRECTIONS)):
            raise ValueError('stripDirection not in ', STRIPDIRECTIONS)

        newDirection = STRIPDIRECTIONS[value]

        # set the new stripDirection, and redraw
        self.stripArrangement = newDirection
        self._redrawLayout(self)

    def _listViewChanged(self, data):
        """Respond to spectrumViews being created/deleted, update contents of the spectrumWidgets frame
        """
        for strip in self.strips:
            strip._updateVisibility()

        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=None)
        GLSignals.emitPaintEvent()

    @property
    def isGrouped(self):
        """Return whether the spectrumDisplay contains grouped spectra
        """
        # Using AbstractWrapperObject because there seems to already be a setParameter
        # belonging to spectrumDisplay
        grouped = AbstractWrapperObject.getParameter(self, SPECTRUMGROUPS, SPECTRUMISGROUPED)
        if grouped is not None:
            return grouped

        # set default to False
        AbstractWrapperObject.setParameter(self, SPECTRUMGROUPS, SPECTRUMISGROUPED, False)
        return False

    @isGrouped.setter
    def isGrouped(self, grouped):
        """Set whether the spectrumDisplay contains grouped spectra
        """
        AbstractWrapperObject.setParameter(self, SPECTRUMGROUPS, SPECTRUMISGROUPED, grouped)

    @property
    def stripArrangement(self):
        """Strip axis direction ('X', 'Y', None) - None only for non-strip plots
        """
        # Using AbstractWrapperObject because there seems to already be a setParameter
        # belonging to spectrumDisplay
        arrangement = AbstractWrapperObject.getParameter(self, SPECTRUMDISPLAY, STRIPARRANGEMENT)
        if arrangement is not None:
            return arrangement

        # set default values in the ccpnInternal store
        arrangement = self._wrappedData.stripDirection  # SHOULD always be 'Y', if it makes a difference
        AbstractWrapperObject.setParameter(self, SPECTRUMDISPLAY, STRIPARRANGEMENT, arrangement)
        return arrangement

    @stripArrangement.setter
    def stripArrangement(self, value):
        """Set the new strip direction ('X', 'Y', None) - None only for non-strip plots
        """
        if not isinstance(value, str):
            raise TypeError('stripArrangement must be a string')
        elif value not in ['X', 'Y']:
            raise ValueError("stripArrangement must be either 'X' or 'Y'")

        AbstractWrapperObject.setParameter(self, SPECTRUMDISPLAY, STRIPARRANGEMENT, value)
        # leave the _wrappedData as it's initialised value

    def _getSpectrumGroups(self):
        """Return the groups contained in the spectrumDisplay
        """
        # Using AbstractWrapperObject because there seems to already be a setParameter
        # belonging to spectrumDisplay
        _spectrumGroups = AbstractWrapperObject.getParameter(self, SPECTRUMGROUPS, SPECTRUMGROUPLIST)
        if _spectrumGroups is not None:
            return _spectrumGroups

        AbstractWrapperObject.setParameter(self, SPECTRUMGROUPS, SPECTRUMGROUPLIST, ())
        return ()

    def _setSpectrumGroups(self, groups):
        """Set the groups in the spectrumDisplay
        """
        AbstractWrapperObject.setParameter(self, SPECTRUMGROUPS, SPECTRUMGROUPLIST, groups)

    def getSettings(self):
        """get the settings dict from the settingsWidget
        """
        return self._spectrumDisplaySettings.getValues()

    def resizeEvent(self, ev):
        if self.isDeleted:
            return

        # resize the contents of the stripFrame
        self.setColumnStretches(stretchValue=True, widths=False)
        super().resizeEvent(ev)

    def _toolbarAddSpectrum(self, data):
        """Respond to a new spectrum being added to the spectrumDisplay; add new toolbar Icon
        """
        print('>>>_toolbarAddSpectrum')

        trigger = data[Notifier.TRIGGER]
        spectrum = data[Notifier.OBJECT]
        # self.spectrumToolBar._addSpectrumViewToolButtons(spectrum.spectrumViews[0])

    def _toolbarChange(self, data):
        """Respond to a change in the spectrum Icon toolbar denoting that clicked or spectrum created/deleted
        """
        trigger = data[Notifier.TRIGGER]
        if trigger == Notifier.CHANGE:
            # self.spectrumToolBar._toolbarChange(self.strips[0].orderedSpectrumViews())

            if data[Notifier.OBJECT] == self:
                specViews = data[Notifier.OBJECT].spectrumViews
                self.spectrumToolBar._toolbarChange(self.orderedSpectrumViews(specViews))

                # flag that the listViews need to be updated
                for strip in self.strips:
                    strip._updateVisibility()

                # spawn a redraw of the GL windows
                from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

                GLSignals = GLNotifier(parent=None)
                GLSignals.emitPaintEvent()

    def _hoverEvent(self, event):
        event.accept()

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events

        CCPN INTERNAL: Also called from GuiStrip
        """
        theObject = data.get('theObject')

        if DropBase.URLS in data:
            # process dropped items but don't open any spectra
            self.mainWindow._processDroppedItems(data)

        # handle Pids, many more items than mainWindow._processPids
        pids = data.get(DropBase.PIDS, [])
        if pids and len(pids) > 0:
            with undoBlock():
                getLogger().info('Handling pids...')
                if len(pids) > MAXITEMLOGGING:
                    with notificationEchoBlocking():
                        self._handlePids(pids, theObject)
                else:
                    self._handlePids(pids, theObject)

    def _handlePids(self, pids, strip=None):
        "handle a; return True in case it is a Spectrum or a SpectrumGroup"
        success = False
        objs = []
        nmrChains = []
        nmrResidues = []
        nmrAtoms = []

        for pid in pids:
            obj = self.project.getByPid(pid)
            if obj:
                objs.append(obj)

        for obj in objs:
            if obj is not None and isinstance(obj, Spectrum):
                if self.isGrouped:
                    showWarning('Forbidden drop', 'A Single spectrum cannot be dropped onto grouped displays.')
                    return success

                with undoBlock():
                    self.displaySpectrum(obj)

                if strip in self.strips:
                    self.current.strip = strip
                elif self.current.strip not in self.strips:
                    self.current.strip = self.strips[0]

                # spawn a redraw of the GL windows
                from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

                GLSignals = GLNotifier(parent=None)
                GLSignals.emitPaintEvent()

                success = True
            elif obj is not None and isinstance(obj, PeakList):
                with undoBlock():
                    self._handlePeakList(obj)
                success = True
            elif obj is not None and isinstance(obj, SpectrumGroup):
                with undoBlock():
                    self._handleSpectrumGroup(obj)
                success = True
            elif obj is not None and isinstance(obj, Sample):
                with undoBlock():
                    self._handleSample(obj)
                success = True
            elif obj is not None and isinstance(obj, NmrAtom):
                nmrAtoms.append(obj)

            elif obj is not None and isinstance(obj, NmrResidue):
                nmrResidues.append(obj)

            elif obj is not None and isinstance(obj, NmrChain):
                nmrChains.append(obj)

            elif obj is not None and isinstance(obj, GuiStrip):
                self._handleStrip(obj, strip)

            elif obj is not None and isinstance(obj, Peak):
                self._handlePeak(obj, strip)

            else:
                showWarning('Dropped item "%s"' % obj.pid, 'Wrong kind; drop Spectrum, SpectrumGroup, PeakList,'
                                                           ' NmrChain, NmrResidue, NmrAtom or Strip')
        if nmrChains:
            with undoBlock():
                self._handleNmrChains(nmrChains)
        if nmrResidues:
            with undoBlock():
                self._handleNmrResidues(nmrResidues)
        if nmrAtoms:
            with undoBlock():
                self._handleNmrAtoms(nmrAtoms)

        return success

    def _handlePeak(self, peak, strip, widths=None):
        """Navigate to the peak position in the strip
        """
        from ccpn.ui.gui.lib.SpectrumDisplay import navigateToPeakInStrip

        # use the library method
        navigateToPeakInStrip(self, strip, peak, widths=None)

    def _handleStrip(self, moveStrip, dropStrip):
        """Move a strip within a spectrumDisplay by dragging the strip label to another strip
        """
        if moveStrip.spectrumDisplay == self:
            strips = self.orderedStrips
            stripInd = strips.index(dropStrip)

            if stripInd != strips.index(moveStrip):
                moveStrip.moveTo(stripInd)

    def _handlePeakList(self, peakList):
        "See if peaklist can be copied"
        spectrum = peakList.spectrum
        #TODO:GEERTEN: Ask rasmus how to match axis codes
        if spectrum.dimensionCount != self.strips[0].spectra[0].dimensionCount or \
                not True:  # peakList.spectrum.axisCodes match
            showWarning('Dropped PeakList "%s"' % peakList.pid, 'Cannot copy: Axes do not match')
            return
        else:
            from ccpn.ui.gui.popups.CopyPeakListPopup import CopyPeakListPopup

            popup = CopyPeakListPopup(parent=self.mainWindow, mainWindow=self.mainWindow)
            popup.sourcePeakListPullDown.select(peakList.pid)
            popup.exec_()
        # showInfo(title='Copy PeakList "%s"' % peakList.pid, message='Copy to selected spectra')

    def _handleSpectrumGroup(self, spectrumGroup):
        """
        Add spectrumGroup on the display and its button on the toolBar
        """
        self.spectrumGroupToolBar._addAction(spectrumGroup)
        for spectrum in spectrumGroup.spectra:
            self.displaySpectrum(spectrum)
        if self.current.strip not in self.strips:
            self.current.strip = self.strips[0]

    def _handleSample(self, sample):
        """
        Add spectra linked to sample and sampleComponent. Used for screening
        """
        for spectrum in sample.spectra:
            self.displaySpectrum(spectrum)
        for sampleComponent in sample.sampleComponents:
            if sampleComponent.substance is not None:
                for spectrum in sampleComponent.substance.referenceSpectra:
                    self.displaySpectrum(spectrum)
        if self.current.strip not in self.strips:
            self.current.strip = self.strips[0]

    def _handleNmrChains(self, nmrChains):
        nmrResidues = []
        for chain in nmrChains:
            nmrResidues += chain.nmrResidues

        # mark all nmrChains.nmrResidues.nmrAtoms to the window
        self._handleNmrResidues(nmrResidues, showDialog=False)

    def _handleNmrResidues(self, nmrResidues, showDialog=True):

        # get the widget that is under the cursor, SHOULD be guiWidget
        point = QtGui.QCursor.pos()
        destStrip = QtWidgets.QApplication.widgetAt(point)

        if destStrip and isinstance(destStrip, CcpnGLWidget):
            objectsClicked = destStrip.getObjectsUnderMouse()

            if objectsClicked is None:
                return

            if PEAKSELECT in objectsClicked or MULTIPLETSELECT in objectsClicked:
                # dropped onto a peak or multiplet
                # dropping onto a multiplet will apply to all attached peaks

                # dialogResult = showMulti('nmrResidue', 'What do you want to do with the nmrResidues?',
                #                          texts=['Mark and Assign', 'Assign NmrResidues to selected peaks/multiplets'])

                # Assign nmrResidues atoms to peaks
                peaks = set(self.current.peaks)
                for mult in self.current.multiplets:
                    peaks = peaks | set(mult.peaks)
                _assignNmrResiduesToPeaks(peaks=list(peaks), nmrResidues=nmrResidues)

                # # mark all nmrResidues.nmrAtoms to the window
                # if 'Mark' in dialogResult:
                #     for nmrResidue in nmrResidues:
                #         self._createNmrResidueMarks(nmrResidue)

            elif not objectsClicked:
                # mark all nmrResidues.nmrAtoms to the window
                for nmrResidue in nmrResidues:
                    self._createNmrResidueMarks(nmrResidue)

    def _handleNmrAtoms(self, nmrAtoms):

        # get the widget that is under the cursor, SHOULD be guiWidget
        point = QtGui.QCursor.pos()
        destStrip = QtWidgets.QApplication.widgetAt(point)

        if destStrip and isinstance(destStrip, CcpnGLWidget):
            objectsClicked = destStrip.getObjectsUnderMouse()

            if objectsClicked is None:
                return

            if PEAKSELECT in objectsClicked or MULTIPLETSELECT in objectsClicked:
                # dropped onto a peak or multiplet
                # dropping onto a multiplet will apply to all attached peaks

                # dialogResult = showMulti('nmrAtoms', 'What do you want to do with the nmrAtoms?',
                #                          texts=['Mark and Assign', 'Assign NmrAtoms to selected peaks/multiplets'])

                # Assign nmrAtoms to peaks
                peaks = set(self.current.peaks)
                for mult in self.current.multiplets:
                    peaks = peaks | set(mult.peaks)
                _assignNmrAtomsToPeaks(nmrAtoms=nmrAtoms, peaks=list(peaks))

                # # mark all nmrAtoms to the window
                # if 'Mark' in dialogResult:
                #     for nmrAtom in nmrAtoms:
                #         self._markNmrAtom(nmrAtom)

            elif not objectsClicked:
                # mark all nmrResidues.nmrAtoms to the window
                for nmrAtom in nmrAtoms:
                    self._markNmrAtom(nmrAtom)

    def _createNmrResidueMarks(self, nmrResidue):
        """
        Mark a list of nmrAtoms in the spectrum displays
        """
        # showInfo(title='Mark nmrResidue "%s"' % nmrResidue.pid, message='mark nmrResidue in strips')

        from ccpn.AnalysisAssign.modules.BackboneAssignmentModule import nmrAtomsFromResidue, nmrAtomsFromOffsets, markNmrAtoms

        nmrAtoms = nmrAtomsFromOffsets(nmrResidue)
        if nmrAtoms:
            markNmrAtoms(self.mainWindow, nmrAtoms)

    def _markNmrAtom(self, nmrAtom):
        """
        Mark an nmrAtom in the spectrum displays with horizontal/vertical bars
        """
        # showInfo(title='Mark nmrAtom "%s"' % nmrAtom.pid, message='mark nmrAtom in strips')

        from ccpn.AnalysisAssign.modules.BackboneAssignmentModule import markNmrAtoms

        markNmrAtoms(self.mainWindow, [nmrAtom])

    def setScrollbarPolicies(self, horizontal='asNeeded', vertical='asNeeded'):
        "Set the scrolbar policies; convenience to expose to the user"
        from ccpn.ui.gui.widgets.ScrollArea import SCROLLBAR_POLICY_DICT

        if horizontal not in SCROLLBAR_POLICY_DICT or \
                vertical not in SCROLLBAR_POLICY_DICT:
            getLogger().warning('Invalid scrollbar policy (%s, %s)' % (horizontal, vertical))
        self.stripFrame.setScrollBarPolicies((horizontal, vertical))

    def _updatePivot(self):
        """Updates pivot in all strips contained in the spectrum display."""
        for strip in self.strips:
            strip._updatePivot()

    def _updatePhasing(self):
        """Updates phasing in all strips contained in the spectrum display."""
        for strip in self.strips:
            strip._updatePhasing()

    def _changedPhasingDirection(self):
        """Changes direction of phasing from horizontal to vertical or vice versa."""
        for strip in self.strips:
            strip._changedPhasingDirection()

    def updateSpectrumTraces(self):
        """Add traces to all strips"""
        for strip in self.strips:
            strip._updateTraces()

    def _applyPhasing(self, phasingValues):
        """apply the phasing values here
        phasingValues is a dict:

        { 'direction': 'horizontal' or 'vertical' - the last direction selected
          'horizontal': {'ph0': float,
                         'ph1': float,
                         'pivot': float},
          'vertical':   {'ph0': float,
                         'ph1': float,
                         'pivot': float}
        }
        """
        pass

    def toggleHTrace(self):
        if not self.is1D and self.current.strip:
            trace = not self.current.strip.hTraceAction.isChecked()
            self.setHorizontalTraces(trace)
        else:
            getLogger().warning('no strip selected')

    def toggleVTrace(self):
        if not self.is1D and self.current.strip:
            trace = not self.current.strip.vTraceAction.isChecked()
            self.setVerticalTraces(trace)
        else:
            getLogger().warning('no strip selected')

    def setHorizontalTraces(self, trace):
        for strip in self.strips:
            strip._setHorizontalTrace(trace)

    def setVerticalTraces(self, trace):
        for strip in self.strips:
            strip._setVerticalTrace(trace)

    def removePhasingTraces(self):
        """
        Removes all phasing traces from all strips.
        """
        for strip in self.strips:
            strip.removePhasingTraces()

    def togglePhaseConsole(self):
        """Toggles whether phasing console is displayed.
        """
        isVisible = not self.phasingFrame.isVisible()
        self.phasingFrame.setVisible(isVisible)

        if self.is1D:
            self.hTraceAction = True
            self.vTraceAction = False

            if not self.phasingFrame.pivotsSet:
                inRange, point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints \
                    = self.spectrumViews[0]._getTraceParams((0.0, 0.0))

                self.phasingFrame.setInitialPivots((xDataDim.primaryDataDimRef.pointToValue((xMinFrequency + xMaxFrequency) / 2.0), 0.0))

        else:
            self.hTraceAction = self.current.strip.hTraceAction.isChecked()
            self.vTraceAction = self.current.strip.vTraceAction.isChecked()

            if not self.phasingFrame.pivotsSet:
                inRange, point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, yDataDim, yMinFrequency, yMaxFrequency, yNumPoints \
                    = self.spectrumViews[0]._getTraceParams((0.0, 0.0))

                self.phasingFrame.setInitialPivots((xDataDim.primaryDataDimRef.pointToValue((xMinFrequency + xMaxFrequency) / 2.0),
                                                    yDataDim.primaryDataDimRef.pointToValue((yMinFrequency + yMaxFrequency) / 2.0)))

        for strip in self.strips:
            if isVisible:
                strip.turnOnPhasing()
            else:
                strip.turnOffPhasing()
        self._updatePhasing()

    def showToolbar(self):
        """show the toolbar"""
        # showing the toolbar, but we need to update the checkboxes of all strips as well.
        self.spectrumUtilToolBar.show()
        for strip in self.strips:
            strip.toolbarAction.setChecked(True)

    def hideToolbar(self):
        """hide the toolbar"""
        # hiding the toolbar, but we need to update the checkboxes of all strips as well.
        self.spectrumUtilToolBar.hide()
        for strip in self.strips:
            strip.toolbarAction.setChecked(False)

    def toggleToolbar(self):
        """Toggle the toolbar """
        if not self.spectrumUtilToolBar.isVisible():
            self.showToolbar()
        else:
            self.hideToolbar()

    def showSpectrumToolbar(self):
        """show the spectrum toolbar"""
        # showing the spectrum toolbar, but we need to update the checkboxes of all strips as well.
        if self.isGrouped:
            self.spectrumGroupToolBar.show()
        else:
            self.spectrumToolBar.show()

        for strip in self.strips:
            strip.spectrumToolbarAction.setChecked(True)

    def hideSpectrumToolbar(self):
        """hide the spectrum toolbar"""
        # hiding the spectrum toolbar, but we need to update the checkboxes of all strips as well.
        if self.isGrouped:
            self.spectrumGroupToolBar.hide()
        else:
            self.spectrumToolBar.hide()

        for strip in self.strips:
            strip.spectrumToolbarAction.setChecked(False)

    def toggleSpectrumToolbar(self):
        """Toggle the spectrum toolbar """
        if self.isGrouped:
            if not self.spectrumGroupToolBar.isVisible():
                self.showSpectrumToolbar()
            else:
                self.hideSpectrumToolbar()
        else:
            if not self.spectrumToolBar.isVisible():
                self.showSpectrumToolbar()
            else:
                self.hideSpectrumToolbar()

    def close(self):
        """
        Close the module from the commandline
        """
        self._closeModule()

    def _closeModule(self):
        """
        CCPN-INTERNAL: used to close the module
        Closes spectrum display and deletes it from the project.
        """
        try:
            if self.current.strip in self.strips:
                self.current.strip = None
            for strip in self.strips:
                getLogger().debug2('unregistering strip: %s' % strip)
                strip.close()
                # strip._unregisterStrip()
            # self.droppedNotifier.unRegister()
            # self._toolbarNotifier.unRegister()
            # self._unRegisterNotifiers()

        finally:
            super()._closeModule()
            self.delete()

    # def _unDelete(self, strip):
    #     """unDelete the strip
    #     """
    #     with undoBlockManager():
    #         strip._unDelete()
    #
    #         self.showAxes()

    def _removeIndexStrip(self, value):
        self.deleteStrip(self.strips[value])

    def _redrawLayout(self, spectrumDisplay):
        """Redraw the stripFrame with the new stripDirection
        """
        layout = spectrumDisplay.stripFrame.getLayout()

        if layout and layout.count() > 1:
            spectrumDisplay.stripFrame.blockSignals(True)
            spectrumDisplay.stripFrame.setUpdatesEnabled(False)

            # clear the layout and rebuild
            _widgets = []

            # need to be removed if not using QObjectCleanupHandler before creating new layout
            while layout.count():
                _widgets.append(layout.takeAt(0).widget())

            # remember necessary layout info and create a new layout - ensures clean for new widgets
            margins = layout.getContentsMargins()
            space = layout.spacing()
            QtWidgets.QWidget().setLayout(layout)
            layout = QtWidgets.QGridLayout()
            spectrumDisplay.stripFrame.setLayout(layout)
            layout.setContentsMargins(*margins)
            layout.setSpacing(space)

            # reinsert strips in new order - reset minimum widths
            if spectrumDisplay.stripArrangement == 'Y':

                # horizontal strip layout
                for m, widgStrip in enumerate(_widgets):
                    layout.addWidget(widgStrip, 0, m)

            elif spectrumDisplay.stripArrangement == 'X':

                # vertical strip layout
                for m, widgStrip in enumerate(_widgets):
                    layout.addWidget(widgStrip, m, 0)

            spectrumDisplay.stripFrame.setUpdatesEnabled(True)
            spectrumDisplay.stripFrame.blockSignals(False)

            self.showAxes()
            self.setColumnStretches(stretchValue=True)

    def _removeStripFromLayout(self, spectrumDisplay, strip):
        """Remove the current strip from the layout
        CCPN Internal
        """
        layout = spectrumDisplay.stripFrame.getLayout()

        if layout and layout.count() > 1:
            spectrumDisplay.stripFrame.blockSignals(True)
            spectrumDisplay.stripFrame.setUpdatesEnabled(False)

            # clear the layout and rebuild
            _widgets = []

            # need to be removed if not using QObjectCleanupHandler before creating new layout
            while layout.count():
                _widgets.append(layout.takeAt(0).widget())
            _widgets.remove(strip)
            strip.hide()
            strip.setParent(None)  # set widget parent to None to hide,
            # was previously handled by addWidget to tempStore

            # remember necessary layout info and create a new layout - ensures clean for new widgets
            margins = layout.getContentsMargins()
            space = layout.spacing()
            QtWidgets.QWidget().setLayout(layout)
            layout = QtWidgets.QGridLayout()
            spectrumDisplay.stripFrame.setLayout(layout)
            layout.setContentsMargins(*margins)
            layout.setSpacing(space)

            # reinsert strips in new order - reset minimum widths
            if spectrumDisplay.stripArrangement == 'Y':

                # horizontal strip layout
                for m, widgStrip in enumerate(_widgets):
                    layout.addWidget(widgStrip, 0, m)

            elif spectrumDisplay.stripArrangement == 'X':

                # vertical strip layout
                for m, widgStrip in enumerate(_widgets):
                    layout.addWidget(widgStrip, m, 0)

            spectrumDisplay.stripFrame.setUpdatesEnabled(True)
            spectrumDisplay.stripFrame.blockSignals(False)
        else:
            raise RuntimeError('Error, stripFrame layout in invalid state')

    def _restoreStripToLayout(self, spectrumDisplay, strip, currentIndex):
        """Restore the current strip to the layout
        CCPN Internal
        """
        layout = spectrumDisplay.stripFrame.layout()

        if layout:
            spectrumDisplay.stripFrame.setUpdatesEnabled(False)
            spectrumDisplay.stripFrame.blockSignals(True)

            # clear the layout and rebuild
            # need to be removed if not using QObjectCleanupHandler before creating new layout
            _widgets = []
            while layout.count():
                _widgets.append(layout.takeAt(0).widget())
            _widgets.insert(currentIndex, strip)
            strip.show()

            # remember necessary layout info and create a new layout - ensures clean for new widgets
            margins = layout.getContentsMargins()
            space = layout.spacing()
            QtWidgets.QWidget().setLayout(layout)
            layout = QtWidgets.QGridLayout()
            spectrumDisplay.stripFrame.setLayout(layout)
            layout.setContentsMargins(*margins)
            layout.setSpacing(space)

            # reinsert strips in new order - reset minimum widths
            if spectrumDisplay.stripArrangement == 'Y':

                # horizontal strip layout
                for m, widgStrip in enumerate(_widgets):
                    layout.addWidget(widgStrip, 0, m)

            elif spectrumDisplay.stripArrangement == 'X':

                # vertical strip layout
                for m, widgStrip in enumerate(_widgets):
                    layout.addWidget(widgStrip, m, 0)

            # put ccpnStrip back into strips using the api
            # if self not in ccpnStrip.spectrumDisplay.strips:
            if self not in spectrumDisplay.strips:
                for order, cStrip in enumerate(_widgets):
                    cStrip._setStripIndex(order)

            spectrumDisplay.stripFrame.blockSignals(False)
            spectrumDisplay.stripFrame.setUpdatesEnabled(True)
        else:
            raise RuntimeError('Error, stripFrame layout in invalid state')

    @logCommand(get='self')
    def deleteStrip(self, strip):
        """Delete a strip from the spectrumDisplay

        :param strip: strip to delete as object or pid
        """
        strip = self.getByPid(strip) if isinstance(strip, str) else strip

        if strip is None:
            showWarning('Delete strip', 'Invalid strip')
            return

        if strip not in self.strips:
            showWarning('Delete strip', 'Selected strip "%s" is not part of SpectrumDisplay "%s"' \
                        % (strip.pid, self.pid))
            return

        if self.stripCount == 1:
            showWarning('Delete strip', 'Last strip of SpectrumDisplay "%s" cannot be removed' \
                        % (self.pid,))
            return

        with undoBlock():
            with undoStackBlocking() as addUndoItem:
                # retrieve list of created items from the api
                # strangely, this modifies _wrappedData.orderedStrips, and 'removes' the boundStrip by changing the indexing
                # if it is at the end of apiBoundStrips then it confuses the indexing
                indexing = [st.stripIndex() for st in self.strips]

                apiObjectsCreated = strip._getApiObjectTree()

                # reset indexing again SHOULD now be okay; i.e. nothing has been 'removed' from apiBoundStrips yet
                for ii, ind in enumerate(indexing):
                    self.strips[ii]._setStripIndex(ind)

                index = strip.stripIndex()

                # add layout handling to the undo stack
                addUndoItem(undo=partial(self._redrawAxes, index))
                addUndoItem(undo=partial(self._restoreStripToLayout, self, strip, index),
                            redo=partial(self._removeStripFromLayout, self, strip))
                # add notifier handling for the strip
                addUndoItem(undo=partial(strip.setBlankingAllNotifiers, False),
                            redo=partial(strip.setBlankingAllNotifiers, True))

                self._removeStripFromLayout(self, strip)
                strip.setBlankingAllNotifiers(True)

                #EJB 20181213: old style delete notifiers
                # # add object delete/undelete to the undo stack
                # addUndoItem(undo=partial(strip._wrappedData.root._unDelete,
                #                          apiObjectsCreated, (strip._wrappedData.topObject,)),
                #             redo=partial(strip._delete)
                #             )
                # # delete the strip
                # strip._delete()

                # add object delete/undelete to the undo stack
                addUndoItem(undo=BlankedPartial(strip._wrappedData.root._unDelete,
                                                topObjectsToCheck=(strip._wrappedData.topObject,),
                                                obj=strip, trigger='create', preExecution=False,
                                                objsToBeUnDeleted=apiObjectsCreated),
                            redo=BlankedPartial(strip._delete,
                                                obj=strip, trigger='delete', preExecution=True)
                            )

                # delete the strip
                strip._finaliseAction('delete')
                with notificationBlanking():
                    strip._delete()

                addUndoItem(redo=self._redrawAxes)

            # do axis redrawing
            self._redrawAxes()

    def _redrawAxes(self, index=-1):
        """Redraw the axes for the stripFrame, and set the new current strip,
        will default to the last strip if not selected.
        """
        self.showAxes()
        self.setColumnStretches(stretchValue=True)
        if self.strips:
            self.current.strip = self.strips[index]

    def removeCurrentStrip(self):
        """Remove current.strip if it belongs to self.
        """
        if self.current.strip is None:
            showWarning('Remove current strip', 'Select first in SpectrumDisplay by clicking')
            return

        self.deleteStrip(self.current.strip)

    # def duplicateStrip(self):
    #   """
    #   Creates a new strip identical to the last one created and adds it to right of the display.
    #   """
    #   newStrip = self.strips[-1].clone()

    # def addStrip(self, stripIndex=-1) -> 'GuiStripNd':

    def setLastAxisOnly(self, lastAxisOnly: bool = True):
        self.lastAxisOnly = lastAxisOnly

    def showAxes(self, strips=None, stretchValue=False, widths=True, minimumWidth=None):
        # use the strips as they are ordered in the model
        currentStrips = self.orderedStrips

        if currentStrips:

            if self.stripArrangement == 'Y':

                # strips are arranged in a row
                if self.lastAxisOnly:
                    for ss in currentStrips[:-1]:
                        ss.setAxesVisible(rightAxisVisible=False, bottomAxisVisible=True)

                    currentStrips[-1].setAxesVisible(rightAxisVisible=True, bottomAxisVisible=True)

                else:
                    for ss in self.strips:
                        ss.setAxesVisible(rightAxisVisible=True, bottomAxisVisible=True)

            elif self.stripArrangement == 'X':

                # strips are arranged in a column
                if self.lastAxisOnly:
                    for ss in currentStrips[:-1]:
                        ss.setAxesVisible(rightAxisVisible=True, bottomAxisVisible=False)

                    currentStrips[-1].setAxesVisible(rightAxisVisible=True, bottomAxisVisible=True)

                else:
                    for ss in self.strips:
                        ss.setAxesVisible(rightAxisVisible=True, bottomAxisVisible=True)

            else:
                getLogger().warning('Strip direction is not defined for spectrumDisplay: %s' % str(self))

            self.setColumnStretches(stretchValue=stretchValue, widths=widths, minimumWidth=minimumWidth)

    def increaseTraceScale(self):
        # self.mainWindow.traceScaleUp(self.mainWindow)
        if not self.is1D:
            for strip in self.strips:
                for spectrumView in strip.spectrumViews:
                    spectrumView.traceScale *= 1.4

                # spawn a redraw of the strip
                strip._updatePivot()

    def decreaseTraceScale(self):
        # self.mainWindow.traceScaleDown(self.mainWindow)
        if not self.is1D:
            for strip in self.strips:
                for spectrumView in strip.spectrumViews:
                    spectrumView.traceScale /= 1.4

                # spawn a redraw of the strip
                strip._updatePivot()

    def increaseStripSize(self):
        """Increase the width/height of the strips depending on the orientation
        """
        if self.stripArrangement == 'Y':

            # strips are arranged in a row
            self._increaseStripWidth()

        elif self.stripArrangement == 'X':

            # strips are arranged in a column
            self._increaseStripHeight()

    def decreaseStripSize(self):
        """Decrease the width/height of the strips depending on the orientation
        """
        if self.stripArrangement == 'Y':

            # strips are arranged in a row
            self._decreaseStripWidth()

        elif self.stripArrangement == 'X':

            # strips are arranged in a column
            self._decreaseStripHeight()

    def _increaseStripWidth(self):
        strips = self.orderedStrips
        currentWidth = strips[0].width() * (100.0 + self.application.preferences.general.stripWidthZoomPercent) / 100.0
        AXIS_WIDTH = strips[0].getRightAxisWidth()

        self.stripFrame.hide()
        if len(strips) > 1:
            for strip in strips[:-1]:
                strip.setMinimumWidth(currentWidth)
            strips[-1].setMinimumWidth(currentWidth + AXIS_WIDTH)
            self.stripFrame.setMinimumWidth(currentWidth * len(strips) + AXIS_WIDTH)
        else:
            strips[0].setMinimumWidth(currentWidth)
            self.stripFrame.setMinimumWidth(currentWidth)

        self.stripFrame.show()

    def _decreaseStripWidth(self):
        strips = self.orderedStrips
        currentWidth = strips[0].width() * 100.0 / (100.0 + self.application.preferences.general.stripWidthZoomPercent)
        AXIS_WIDTH = strips[0].getRightAxisWidth()

        self.stripFrame.hide()
        if len(strips) > 1:
            for strip in strips[:-1]:
                strip.setMinimumWidth(currentWidth)
            strips[-1].setMinimumWidth(currentWidth + AXIS_WIDTH)
            self.stripFrame.setMinimumWidth(currentWidth * len(strips) + AXIS_WIDTH)
        else:
            strips[0].setMinimumWidth(currentWidth)
            self.stripFrame.setMinimumWidth(currentWidth)

        self.stripFrame.show()

    def _increaseStripHeight(self):
        strips = self.orderedStrips
        currentHeight = strips[0].height() * (100.0 + self.application.preferences.general.stripWidthZoomPercent) / 100.0
        AXIS_HEIGHT = strips[0].getBottomAxisHeight()

        self.stripFrame.hide()
        if len(strips) > 1:
            for strip in strips[:-1]:
                strip.setMinimumHeight(currentHeight)
            strips[-1].setMinimumHeight(currentHeight + AXIS_HEIGHT)
            self.stripFrame.setMinimumHeight(currentHeight * len(strips) + AXIS_HEIGHT)
        else:
            strips[0].setMinimumHeight(currentHeight)
            self.stripFrame.setMinimumHeight(currentHeight)

        self.stripFrame.show()

    def _decreaseStripHeight(self):
        strips = self.orderedStrips
        currentHeight = strips[0].height() * 100.0 / (100.0 + self.application.preferences.general.stripWidthZoomPercent)
        AXIS_HEIGHT = strips[0].getBottomAxisHeight()

        self.stripFrame.hide()
        if len(strips) > 1:
            for strip in strips[:-1]:
                strip.setMinimumHeight(currentHeight)
            strips[-1].setMinimumHeight(currentHeight + AXIS_HEIGHT)
            self.stripFrame.setMinimumHeight(currentHeight * len(strips) + AXIS_HEIGHT)
        else:
            strips[0].setMinimumHeight(currentHeight)
            self.stripFrame.setMinimumHeight(currentHeight)

        self.stripFrame.show()

    def _copyPreviousStripValues(self, fromStrip, toStrip):
        """Copy the trace settings to another strip in the spectrumDisplay.
        """
        traceScale = fromStrip.spectrumViews[0].traceScale
        toStrip.setTraceScale(traceScale)

        if self.phasingFrame.isVisible():
            toStrip.turnOnPhasing()

    @logCommand(get='self')
    def addStrip(self, strip=None) -> 'GuiStripNd':
        """Creates a new strip by cloning strip with index (default the last) in the display.
        """
        strip = self.getByPid(strip) if isinstance(strip, str) else strip
        index = strip.stripIndex() if strip else -1

        if self.phasingFrame.isVisible():
            showWarning(str(self.windowTitle()), 'Please disable Phasing Console before adding strips')
            return

        with undoBlock():
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=self._redrawAxes)

                #EJB 20181213: old style delete notifiers
                # result = self.strips[index]._clone()
                # if not isinstance(result, GuiStrip):
                #     raise RuntimeError('Expected an object of class %s, obtained %s' % (GuiStrip, result.__class__))
                # apiObjectsCreated = result._getApiObjectTree()
                # # add object delete/undelete to the undo stack
                # addUndoItem(undo=partial(Undo._deleteAllApiObjects, apiObjectsCreated),
                #             redo=partial(result._wrappedData.root._unDelete,
                #                          apiObjectsCreated, (result._wrappedData.topObject,))
                #             )

                with notificationBlanking():
                    # get the visibility of strip to be copied
                    copyVisible = self.strips[index].header.headerVisible

                    # inserts the strip into the stripFrame here
                    result = self.strips[index]._clone()
                    if not isinstance(result, GuiStrip):
                        raise RuntimeError('Expected an object of class %s, obtained %s' % (GuiStrip, result.__class__))
                result._finaliseAction('create')

                # copy the strip Header if needed
                result.header.headerVisible = copyVisible if copyVisible is not None else False
                result.header.setLabelVisible(visible=copyVisible if copyVisible is not None else False)

                # retrieve list of created items from the api
                # strangely, this modifies _wrappedData.orderedStrips
                apiObjectsCreated = result._getApiObjectTree()
                addUndoItem(undo=BlankedPartial(Undo._deleteAllApiObjects,
                                                obj=result, trigger='delete', preExecution=True,
                                                objsToBeDeleted=apiObjectsCreated),
                            redo=BlankedPartial(result._wrappedData.root._unDelete,
                                                topObjectsToCheck=(result._wrappedData.topObject,),
                                                obj=result, trigger='create', preExecution=False,
                                                objsToBeUnDeleted=apiObjectsCreated)
                            )

                index = result.stripIndex()

                # add notifier handling to the stack
                addUndoItem(undo=partial(result.setBlankingAllNotifiers, True),
                            redo=partial(result.setBlankingAllNotifiers, False))

                # add layout handling to the undo stack
                addUndoItem(undo=partial(self._removeStripFromLayout, self, result),
                            redo=partial(self._restoreStripToLayout, self, result, index))
                addUndoItem(redo=partial(self._redrawAxes, index))

            # do axis redrawing
            self._redrawAxes(index)  # this might be getting confused with the ordering

        return result

    def setColumnStretches(self, stretchValue=False, scaleFactor=1.0, widths=True, minimumWidth=None):
        """Set the column widths of the strips so that the last strip accommodates the axis bar
                if necessary."""

        if self.stripArrangement == 'Y':

            # strips are arranged in a row
            self._setColumnStretches(stretchValue=stretchValue, scaleFactor=scaleFactor, widths=widths, minimumWidth=minimumWidth)

        elif self.stripArrangement == 'X':

            # strips are arranged in a column
            self._setRowStretches(stretchValue=stretchValue, scaleFactor=scaleFactor, heights=widths, minimumHeight=minimumWidth)

        else:
            getLogger().warning('Strip direction is not defined for spectrumDisplay: %s' % str(self))

    def _setColumnStretches(self, stretchValue=False, scaleFactor=1.0, widths=True, minimumWidth=None):
        """Set the column widths of the strips so that the last strip accommodates the axis bar
        if necessary."""
        widgets = self.stripFrame.children()

        # set the strip spacing and the visibility of the scroll bars
        layout = self.stripFrame.getLayout()
        layout.setHorizontalSpacing(STRIP_SPACING)
        layout.setVerticalSpacing(0)
        if self._stripFrameScrollArea:
            # scroll area for strips
            self._stripFrameScrollArea.setScrollBarPolicies(scrollBarPolicies=('asNeeded', 'never'))

        if widgets:
            thisLayout = self.stripFrame.layout()
            # thisLayoutWidth = self._stripFrameScrollArea.width()
            thisLayoutWidth = self.stripFrame.width()

            if not thisLayout.itemAt(0):
                return

            self.stripFrame.hide()

            AXIS_WIDTH = 1
            AXIS_PADDING = STRIP_SPACING

            if self.strips:
                firstStripWidth = thisLayoutWidth / self.stripCount
                AXIS_WIDTH = self.orderedStrips[0].getRightAxisWidth()
            else:
                firstStripWidth = thisLayoutWidth

            if minimumWidth:
                firstStripWidth = max(firstStripWidth, minimumWidth)

            if not self.lastAxisOnly:
                maxCol = 0
                for wid in self.orderedStrips:
                    index = thisLayout.indexOf(wid)
                    if index >= 0:
                        row, column, cols, rows = thisLayout.getItemPosition(index)
                        maxCol = max(maxCol, column)

                for col in range(0, maxCol + 1):
                    if widths and thisLayout.itemAt(col):
                        thisLayout.itemAt(col).widget().setMinimumWidth(firstStripWidth)
                    thisLayout.setColumnStretch(col, 1 if stretchValue else 1)

                if minimumWidth:
                    self.stripFrame.setMinimumWidth((firstStripWidth + STRIP_SPACING) * len(self.orderedStrips) - STRIP_SPACING)
                else:
                    self.stripFrame.setMinimumWidth(self.stripFrame.minimumSizeHint().width())
                self.stripFrame.setMinimumHeight(50)

            else:

                # set the correct widths for the strips
                maxCol = thisLayout.count() - 1
                firstWidth = scaleFactor * (thisLayoutWidth - AXIS_WIDTH - (maxCol * AXIS_PADDING)) / (maxCol + 1)

                if minimumWidth:
                    firstWidth = max(firstWidth, minimumWidth)

                endWidth = firstWidth + AXIS_WIDTH

                # set the minimum widths and stretch values for the strips
                for column in range(thisLayout.count()):
                    thisLayout.setColumnStretch(column, firstWidth if stretchValue else 1)
                    if widths:
                        wid = thisLayout.itemAt(column).widget()
                        wid.setMinimumWidth(firstWidth)

                thisLayout.setColumnStretch(maxCol, endWidth if stretchValue else 1)
                if widths:
                    wid = thisLayout.itemAt(maxCol).widget()
                    wid.setMinimumWidth(endWidth)

                # fix the width of the stripFrame
                if minimumWidth:

                    # this depends on the spacing in stripFrame
                    self.stripFrame.setMinimumWidth((firstWidth + STRIP_SPACING) * len(self.orderedStrips) + AXIS_WIDTH)
                else:
                    self.stripFrame.setMinimumWidth(self.stripFrame.minimumSizeHint().width())
                self.stripFrame.setMinimumHeight(50)

            self.stripFrame.show()

    def _setRowStretches(self, stretchValue=False, scaleFactor=1.0, heights=True, minimumHeight=None):
        """Set the row heights of the strips so that the last strip accommodates the axis bar
        if necessary."""
        widgets = self.stripFrame.children()

        # set the strip spacing and the visibility of the scroll bars
        layout = self.stripFrame.getLayout()
        layout.setHorizontalSpacing(0)
        layout.setVerticalSpacing(STRIP_SPACING)
        if self._stripFrameScrollArea:
            # scroll area for strips
            self._stripFrameScrollArea.setScrollBarPolicies(scrollBarPolicies=('never', 'asNeeded'))

        if widgets:
            thisLayout = self.stripFrame.layout()
            # thisLayoutHeight = self._stripFrameScrollArea.height()
            thisLayoutHeight = self.stripFrame.height()

            if not thisLayout.itemAt(0):
                return

            self.stripFrame.hide()

            AXIS_HEIGHT = 1
            AXIS_PADDING = STRIP_SPACING

            if self.strips:
                firstStripHeight = thisLayoutHeight / self.stripCount
                AXIS_HEIGHT = self.orderedStrips[0].getBottomAxisHeight()
            else:
                firstStripHeight = thisLayoutHeight

            if minimumHeight:
                firstStripHeight = max(firstStripHeight, minimumHeight)

            if not self.lastAxisOnly:
                maxRow = 0
                for wid in self.orderedStrips:
                    index = thisLayout.indexOf(wid)
                    if index >= 0:
                        row, column, cols, rows = thisLayout.getItemPosition(index)
                        maxRow = max(maxRow, row)

                for rr in range(0, maxRow + 1):
                    if heights and thisLayout.itemAt(rr):
                        thisLayout.itemAt(rr).widget().setMinimumHeight(firstStripHeight)
                    thisLayout.setRowStretch(rr, 1 if stretchValue else 1)

                if minimumHeight:
                    self.stripFrame.setMinimumHeight((firstStripHeight + STRIP_SPACING) * len(self.orderedStrips) - STRIP_SPACING)
                else:
                    self.stripFrame.setMinimumHeight(self.stripFrame.minimumSizeHint().height())
                self.stripFrame.setMinimumWidth(50)

            else:

                # set the correct heights for the strips
                maxRow = thisLayout.count() - 1
                firstHeight = scaleFactor * (thisLayoutHeight - AXIS_HEIGHT - (maxRow * AXIS_PADDING)) / (maxRow + 1)

                if minimumHeight:
                    firstHeight = max(firstHeight, minimumHeight)

                endHeight = firstHeight + AXIS_HEIGHT

                # set the minimum heights and stretch values for the strips
                for rr in range(thisLayout.count()):
                    thisLayout.setRowStretch(rr, firstHeight if stretchValue else 1)
                    if heights:
                        wid = thisLayout.itemAt(rr).widget()
                        wid.setMinimumHeight(firstHeight)

                thisLayout.setRowStretch(maxRow, endHeight if stretchValue else 1)
                if heights:
                    wid = thisLayout.itemAt(maxRow).widget()
                    wid.setMinimumHeight(endHeight)

                # fix the height of the stripFrame
                if minimumHeight:
                    # this depends on the spacing in stripFrame
                    self.stripFrame.setMinimumHeight((firstHeight + STRIP_SPACING) * len(self.orderedStrips) + AXIS_HEIGHT)
                else:
                    self.stripFrame.setMinimumHeight(self.stripFrame.minimumSizeHint().height())
                self.stripFrame.setMinimumWidth(50)

            self.stripFrame.show()

    def autoRange(self):
        """Zooms Y axis of current strip to show entire region.
        """
        for strip in self.strips:
            strip.autoRange()

    def _resetYZooms(self):
        """Zooms Y axis of current strip to show entire region.
        """
        for strip in self.strips:
            strip._resetYZoom()

    def _resetXZooms(self):
        """Zooms X axis of current strip to show entire region.
        """
        for strip in self.strips:
            strip._resetXZoom()

    def _resetAllZooms(self):
        """Zooms X/Y axes of current strip to show entire region.
        """
        for strip in self.strips:
            strip._resetAllZoom()

    def _restoreZoom(self):
        """Restores last saved zoom of current strip.
        """
        if not self.strips:
            showWarning('Restore Zoom', 'SpectrumDisplay "%s" does not contain any strips' \
                        % self.pid)
            return

        for strip in self.strips:
            strip._restoreZoom()

    def _storeZoom(self):
        """Saves zoomed region of current strip."""
        if not self.strips:
            showWarning('Store Zoom', 'SpectrumDisplay "%s" does not contain any strips' \
                        % self.pid)
            return

        for strip in self.strips:
            strip._storeZoom()

    def _previousZoom(self):
        """Changes to the previous zoom of current strip."""
        if not self.strips:
            showWarning('Undo Zoom', 'SpectrumDisplay "%s" does not contain any strips' \
                        % self.pid)
            return

        for strip in self.strips:
            strip._previousZoom()

    def _nextZoom(self):
        """Changes to the next zoom of current strip."""
        if not self.strips:
            showWarning('Redo Zoom', 'SpectrumDisplay "%s" does not contain any strips' \
                        % self.pid)
            return

        for strip in self.strips:
            strip._nextZoom()

    def _zoomIn(self):
        """zoom in to the current strip."""
        if not self.strips:
            showWarning('Restore Zoom', 'SpectrumDisplay "%s" does not contain any strips' \
                        % self.pid)
            return

        for strip in self.strips:
            strip._zoomIn()

    def _zoomOut(self):
        """zoom out of current strip."""
        if not self.strips:
            showWarning('Restore Zoom', 'SpectrumDisplay "%s" does not contain any strips' \
                        % self.pid)
            return

        for strip in self.strips:
            strip._zoomOut()

    def toggleCrosshair(self):
        """Toggles whether cross hair is displayed in all strips of spectrum display.
        """
        for strip in self.strips:
            strip._toggleCrosshair()

    def toggleGrid(self):
        """Toggles whether grid is displayed in all strips of spectrum display.
        """
        for strip in self.strips:
            strip.toggleGrid()

    def _cyclePeakLabelling(self):
        """Toggles peak labelling of current strip.
        """
        try:
            if not self.current.strip:
                showWarning('Cycle Peak Labelling', 'No strip selected')
                return

            for strip in self.strips:
                strip.cyclePeakLabelling()

        except:
            getLogger().warning('Error cycling peak labelling')

    def _cyclePeakSymbols(self):
        """toggles peak labelling of current strip.
        """
        try:
            if not self.current.strip:
                showWarning('Cycle Peak Symbols', 'No strip selected')
                return

            for strip in self.strips:
                strip.cyclePeakSymbols()
        except:
            getLogger().warning('Error cycling peak symbols')

    # def _deletedPeak(self, peak):
    #     apiPeak = peak._wrappedData
    #     # NBNB TBD FIXME rewrite this to not use API peaks
    #     # ALSO move this machinery from subclasses to this class.
    #     for peakListView in self.activePeakItemDict:
    #         peakItemDict = self.activePeakItemDict[peakListView]
    #         peakItem = peakItemDict.get(apiPeak)
    #         if peakItem:
    #             # peakListView.spectrumView.strip.plotWidget.scene().removeItem(peakItem)
    #             del peakItemDict[apiPeak]
    #             inactivePeakItems = self.inactivePeakItemDict.get(peakListView)
    #             if inactivePeakItems:
    #                 inactivePeakItems.add(peakItem)
    from ccpn.util.decorators import profile

    @logCommand(get='self')
    def displaySpectrum(self, spectrum, axisOrder: (str,) = ()):
        """Display additional spectrum, with spectrum axes ordered according ton axisOrder
        """
        spectrum = self.getByPid(spectrum) if isinstance(spectrum, str) else spectrum
        if not isinstance(spectrum, Spectrum):
            raise TypeError('spectrum is not of type Spectrum')

        with undoBlock():
            oldIndex = self.getOrderedSpectrumViewsIndex()

            # need set ordering here on undo
            # with undoStackBlocking() as addUndoItem:
            #     addUndoItem(undo=partial(self._listViewChanged, {}))
            #     addUndoItem(undo=partial(self.setOrderedSpectrumViewsIndex, tuple(oldIndex)))

            newSpectrum = self.strips[0].displaySpectrum(spectrum, axisOrder=axisOrder)
            if newSpectrum:
                # index = self.getOrderedSpectrumViewsIndex()
                # self.setOrderedSpectrumViewsIndex(tuple(index))

                # original old code seems to be okay?
                newInd = self.spectrumViews.index(newSpectrum)
                index = self.getOrderedSpectrumViewsIndex()
                index = tuple((ii + 1) if (ii >= newInd) else ii for ii in index)
                index += (newInd,)
                self.setOrderedSpectrumViewsIndex(tuple(index))

    def _removeSpectrum(self, spectrum):
        try:
            # self._orderedSpectra.remove(spectrum)
            self._orderedSpectrumViews.removeSpectrumView(spectrum)
        except:
            getLogger().warning('Error, %s does not exist' % spectrum)

    @logCommand(get='self')
    def makeStripPlot(self, peaks=None, nmrResidues=None,
                      autoClearMarks=True,
                      sequentialStrips=True,
                      markPositions=True,
                      widths=None):
        """Make a list of strips in the current spectrumDisplay based on the list of peaks or
        the list of nmrResidues passing in
        Can only choose either peaks or nmrResidues, peaks chosen will override any selected nmrResidues
        """
        pkList = makeIterableList(peaks)
        pks = []
        for peak in pkList:
            pks.append(self.project.getByPid(peak) if isinstance(peak, str) else peak)

        resList = makeIterableList(nmrResidues)
        nmrs = []
        for nmrRes in resList:
            nmrs.append(self.project.getByPid(nmrRes) if isinstance(nmrRes, str) else nmrRes)

        # need to clean up the use of GLNotifier - possibly into AbstractWrapperObject
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
        # from functools import partial
        # from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip, navigateToNmrAtomsInStrip
        from ccpn.ui.gui.lib.SpectrumDisplay import navigateToPeakInStrip, navigateToNmrResidueInStrip

        def _updateGl(self, spectrumList):
            GLSignals = GLNotifier(parent=self)
            GLSignals.emitPaintEvent()

        if pks or nmrs:

            GLSignals = GLNotifier(parent=self)
            _undo = self.project._undo

            project = self.project
            # with logCommandBlock(get='self') as log:
            #     peakStr = '[' + ','.join(["'%s'" % peak.pid for peak in pks]) + ']'
            #     nmrResidueStr = '[' + ','.join(["'%s'" % nmrRes.pid for nmrRes in nmrs]) + ']'
            #     log('addPeaks', peaks=peakStr, nmrResidues=nmrResidueStr)

            with undoBlock():
                # _undo._newItem(undoPartial=partial(_updateGl, self, []))

                if autoClearMarks:
                    self.mainWindow.clearMarks()

                # Make sure there are enough strips to display nmrAtomPairs
                stripCount = len(pks) if pks else len(nmrs)
                while len(self.strips) < stripCount:
                    self.addStrip()
                for strip in self.strips[stripCount:]:
                    self.deleteStrip(strip)

                # build the strips
                if pks:
                    for ii, pk in enumerate(pks):
                        strip = self.strips[ii]
                        navigateToPeakInStrip(self, strip, pk)

                elif nmrs:
                    for ii, nmr in enumerate(nmrs):
                        strip = self.strips[ii]
                        navigateToNmrResidueInStrip(self, strip, nmr, widths, markPositions)

                # _undo._newItem(redoPartial=partial(_updateGl, self, []))

                # repaint - not sure whether needed here
                GLSignals.emitPaintEvent()


#=========================================================================================

# def _deletedPeak(peak: Peak):
#     """Function for notifiers.
#     #CCPNINTERNAL
#     """
#
#     for spectrumView in peak.peakList.spectrum.spectrumViews:
#         spectrumView.strip.spectrumDisplay._deletedPeak(peak)


def _spectrumHasChanged(data):
    spectrum = data[Notifier.OBJECT]

    project = spectrum.project
    apiDataSource = spectrum._wrappedData
    for spectrumDisplay in project.spectrumDisplays:
        action = spectrumDisplay.spectrumActionDict.get(apiDataSource)
        if action:  # spectrum might not be in all displays
            # update toolbar button name
            action.setText(spectrum.name)

    # force redraw of the spectra
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    for specView in spectrum.spectrumViews:
        specView.buildContours = True

    # fire refresh event to repaint the screen
    GLSignals = GLNotifier(parent=spectrum)
    targets = [objList for objList in spectrum.peakLists] + [objList for objList in spectrum.multipletLists]
    GLSignals.emitEvent(targets=targets, triggers=[GLNotifier.GLPEAKLISTS,
                                                   GLNotifier.GLPEAKLISTLABELS,
                                                   GLNotifier.GLMULTIPLETLISTS,
                                                   GLNotifier.GLMULTIPLETLISTLABELS
                                                   ])


def _deletedSpectrumView(project: Project, apiSpectrumView):
    """tear down SpectrumDisplay when new SpectrumView is deleted - for notifiers"""
    spectrumDisplay = project._data2Obj[apiSpectrumView.spectrumDisplay]
    apiDataSource = apiSpectrumView.dataSource

    # remove toolbar action (button)
    # NBNB TBD FIXME get rid of API object from code
    action = spectrumDisplay.spectrumActionDict.get(apiDataSource)  # should always be not None
    if action:
        spectrumDisplay.spectrumToolBar.removeAction(action)
        del spectrumDisplay.spectrumActionDict[apiDataSource]

    if not spectrumDisplay.is1D:
        for strip in spectrumDisplay.strips:
            strip._setZWidgets(ignoreSpectrumView=apiSpectrumView)


GuiSpectrumDisplay.processSpectrum = GuiSpectrumDisplay.displaySpectrum  # ejb - from SpectrumDisplay
