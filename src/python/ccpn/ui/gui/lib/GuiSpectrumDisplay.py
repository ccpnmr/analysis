"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:44 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import importlib, os

from PyQt5 import QtWidgets, QtCore

from ccpn.core.Project import Project
from ccpn.core.Peak import Peak
from ccpn.core.PeakList import PeakList
from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.Sample import Sample

#from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from ccpn.ui.gui.lib.guiDecorators import suspendSideBarNotifications
#import typing

from ccpn.ui.gui.widgets.Frame import Frame  #, ScrollableFrame
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.PhasingFrame import PhasingFrame
from ccpn.ui.gui.widgets.SpectrumToolBar import SpectrumToolBar
from ccpn.ui.gui.widgets.SpectrumGroupToolBar import SpectrumGroupToolBar
#from ccpn.ui.gui.widgets.Widget import ScrollableWidget, Widget
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea

from ccpn.ui.gui.widgets.MessageDialog import showWarning
#from ccpn.ui.gui.widgets.BasePopup import BasePopup
#from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.core.lib.Notifiers import Notifier
from ccpn.core.lib.AssignmentLib import _assignNmrAtomsToPeaks, _assignNmrResiduesToPeaks

from ccpn.util.Logging import getLogger
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.NmrChain import NmrChain
from ccpn.ui.gui.lib.Strip import GuiStrip
from ccpn.ui._implementation.PeakListView import PeakListView
from ccpn.ui._implementation.IntegralListView import IntegralListView
from ccpn.ui._implementation.MultipletListView import MultipletListView
from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.ui.gui.widgets.SettingsWidgets import SpectrumDisplaySettings
from ccpn.ui._implementation.SpectrumView import SpectrumView


AXIS_WIDTH = 30
AXISUNITS = ['ppm', 'Hz', 'points']


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

        # GWV: Not sure what the widget argument is for
        # LM: is the spectrumDisplay, used in the widget to set actions/callbacks to the buttons
        spectrumRow = 0
        toolBarRow = 0
        stripRow = 2
        phasingRow = 3

        self.spectrumToolBar = SpectrumToolBar(parent=self.qtParent, widget=self,
                                               grid=(spectrumRow, 0), gridSpan=(1, 6))
        self.spectrumToolBar.setFixedHeight(30)

        # spectrumGroupsToolBar
        self.spectrumGroupToolBar = SpectrumGroupToolBar(parent=self.qtParent, spectrumDisplay=self,
                                                         grid=(spectrumRow, 0), gridSpan=(1, 6))
        self.spectrumGroupToolBar.setFixedHeight(30)
        self.spectrumGroupToolBar.hide()

        # Utilities Toolbar; filled in Nd/1d classes
        self.spectrumUtilToolBar = ToolBar(parent=self.qtParent, iconSizes=(24, 24),
                                           grid=(toolBarRow, 6), gridSpan=(1, 1),
                                           hPolicy='minimal', hAlign='left')
        self.spectrumUtilToolBar.setFixedHeight(self.spectrumToolBar.height())
        if self.application.preferences.general.showToolbar:
            self.spectrumUtilToolBar.show()
        else:
            self.spectrumUtilToolBar.hide()

        self.stripFrame = Frame(setLayout=True, showBorder=False, spacing=(5, 0), stretch=(1, 1), acceptDrops=True)
        self.stripFrame.layout().setContentsMargins(0, 0, 0, 0)

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

    def _listViewChanged(self, data):
        """Respond to spectrumViews being created/deleted, update contents of the spectrumWidgets frame
        """
        for strip in self.strips:
            strip._updateVisibility()

        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=None)
        GLSignals.emitPaintEvent()

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
            self.mainWindow.sideBar._processDroppedItems(data)

        # for url in data.get('urls',[]):
        #   getLogger().debug('dropped: %s' % url)
        #   objects = self.project.loadData(url)
        #
        #   if objects is not None:
        #     for obj in objects:
        #       if isinstance(obj, Spectrum):
        #         self._handlePid(obj.pid, theObject)  # pass the object as its pid so we use
        #                                   # the same method used to process the pids

        pids = data.get(DropBase.PIDS, [])
        if pids:
            if len(pids) > 0:
                self._handlePids(pids, theObject)
        #
        # for pid in data.get('pids',[]):
        #   getLogger().debug('dropped:', pid)

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

                with suspendSideBarNotifications(self.project):
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
                with suspendSideBarNotifications(self.project):
                    self._handlePeakList(obj)
                success = True
            elif obj is not None and isinstance(obj, SpectrumGroup):
                with suspendSideBarNotifications(self.project):
                    self._handleSpectrumGroup(obj)
                success = True
            elif obj is not None and isinstance(obj, Sample):
                with suspendSideBarNotifications(self.project):
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

            else:
                showWarning('Dropped item "%s"' % obj.pid, 'Wrong kind; drop Spectrum, SpectrumGroup, PeakList,'
                                                           ' NmrChain, NmrResidue, NmrAtom or Strip')
        if nmrChains:
            # with suspendSideBarNotifications(self.project):

            with undoBlock():
                self._handleNmrChains(nmrChains)
        if nmrResidues:
            # with suspendSideBarNotifications(self.project):

            with undoBlock():
                self._handleNmrResidues(nmrResidues)
        if nmrAtoms:
            # with suspendSideBarNotifications(self.project):

            with undoBlock():
                self._handleNmrAtoms(nmrAtoms)

        return success

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
        for chain in nmrChains:
            self._handleNmrResidues(chain.nmrResidues)

    def _handleNmrResidues(self, nmrResidues):
        if not self.current.peak:
            for nmrResidue in nmrResidues:
                self._createNmrResidueMarks(nmrResidue)

        # Assign nmrResidues atoms to peaks
        if self.current.strip:
            _assignNmrResiduesToPeaks(peaks=self.current.peaks, nmrResidues=nmrResidues)

    def _handleNmrAtoms(self, nmrAtoms):
        if not self.current.peak:
            for nmrAtom in nmrAtoms:
                self._markNmrAtom(nmrAtom)

        # Assign nmrAtoms to peaks
        if self.current.strip:
            _assignNmrAtomsToPeaks(nmrAtoms=nmrAtoms, peaks=self.current.peaks)

    def _processDragEnterEvent(self, data):
        pass
        # event = data['event']
        # mousePosition = event.pos()
        # if self.current.strip:
        #   position = list(self.current.strip._CcpnGLWidget.mapMouseToAxis(mousePosition))
        #   orderedAxes = self.current.strip.orderedAxes
        #   if self.current.peak:
        #     peakPosition = self.current.peak.position
        #     minPeakPos = min(peakPosition)
        #     bw = self.current.strip._CcpnGLWidget.boxWidth
        #     bh = self.current.strip._CcpnGLWidget.boxHeight
        #     pW = 0
        #     pH = 0
        #     if len(peakPosition) > 0:
        #       pW = peakPosition[0]
        #     if len(peakPosition)>1:
        #       pH = peakPosition[1]
        #     boxW = (pW + bw, pW - bw)
        #     boxH = (pH + bh, pH - bh)
        #     if pW + bw>position[0]>pW - bw and  pH + bh >position[1]>pH - bh:
        #      print('NOT IMPLEMENTED YET')

    def _createNmrResidueMarks(self, nmrResidue):
        """
        Mark a list of nmrAtoms in the spectrum displays
        """
        # showInfo(title='Mark nmrResidue "%s"' % nmrResidue.pid, message='mark nmrResidue in strips')

        from ccpn.AnalysisAssign.modules.BackboneAssignmentModule import nmrAtomsFromResidue, markNmrAtoms

        # get the strips
        # nmrResidue = nmrResidue.mainNmrResidue
        # nmrResidues = []
        # previousNmrResidue = nmrResidue.previousNmrResidue
        # if previousNmrResidue:
        #   nmrResidues.append(previousNmrResidue)
        # nmrResidues.append(nmrResidue)
        # nextNmrResidue = nmrResidue.nextNmrResidue
        # if nextNmrResidue:
        #   nmrResidues.append(nextNmrResidue)
        #
        # nmrAtoms=[]
        #
        # for nr in nmrResidues:
        #   nmrAtoms.extend(nr.nmrAtoms)

        # ejb - just a test, could pass data: if data['shiftLeftMouse']: then clear marks first

        # the below commented code matches backboneassignment, but don't want to do this
        # want to just show what's actually in the nmrResidue
        # if '-1' in nmrResidue.pid:
        #   # -1 residue so need to split the CA, CB from thr N, H
        #   nmrAtomsMinus = nmrAtomsFromResidue(nmrResidue)
        #   nmrAtomsCentre = nmrAtomsFromResidue(nmrResidue.mainNmrResidue)
        #
        #   nmrAtoms = []
        #   # this should check the experiment type and choose the correct atoms
        #   for nac in nmrAtomsMinus:
        #     if '..CA' in nac.pid or '..CB' in nac.pid:
        #       nmrAtoms.append(nac)
        #   for nac in nmrAtomsCentre:
        #     if '..N' in nac.pid or '..H' in nac.pid:
        #       nmrAtoms.append(nac)
        #
        #   markNmrAtoms(mainWindow=self.mainWindow, nmrAtoms=nmrAtoms)
        # else:
        #   nmrAtoms = nmrAtomsFromResidue(nmrResidue.mainNmrResidue)
        #   markNmrAtoms(mainWindow=self.mainWindow, nmrAtoms=nmrAtoms)

        nmrAtoms = nmrAtomsFromResidue(nmrResidue)
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

    def _unDelete(self, strip):
        _undo = self.project._undo
        self._startCommandEchoBlock('removeStrip')
        try:
            strip._unDelete()
        finally:
            self._endCommandEchoBlock()
            self.showAxes()

    def _removeIndexStrip(self, value):
        self.removeStrip(self.strips[value])

    def removeStrip(self, strip):
        "Remove strip if it belongs to self"

        if strip is None:
            showWarning('Remove strip', 'Invalid strip')
            return

        if strip not in self.strips:
            showWarning('Remove strip', 'Selected strip "%s" is not part of SpectrumDisplay "%s"' \
                        % (strip.pid, self.pid))
            return

        if len(self.orderedStrips) == 1:
            showWarning('Remove strip', 'Last strip of SpectrumDisplay "%s" cannot be removed' \
                        % (self.pid,))
            return

        _undo = self.project._undo
        self._startCommandEchoBlock('removeStrip')

        # if _undo is not None:
        #   _undo.increaseBlocking()

        try:
            # strip._unregisterStrip()
            self.current.strip = None
            self.setColumnStretches(stretchValue=False)  # set to 0 so they disappear
            # this removes it too early
            # strip.setParent(None)           # need to remove the rogue widget from the widgetArea
            strip.deleteStrip()
            self.setColumnStretches(stretchValue=True)  # set to 0 so they disappear

            # update the 'orderedSpectra' list
            # TODO:ED update the orderedSpectra list
            # self.removeSpectrumView(None)

        finally:
            self._endCommandEchoBlock()

        # if _undo is not None:
        #   _undo.decreaseBlocking()
        #
        #   # TODO:ED this may not be the correct strip to Redo:remove
        #   _undo.newItem(self.addStrip, self._removeIndexStrip, redoArgs=(-1,))

        self.showAxes()

    def removeCurrentStrip(self):
        "Remove current.strip if it belongs to self"

        if self.current.strip is None:
            showWarning('Remove current strip', 'Select first in SpectrumDisplay by clicking')
            return
        self.removeStrip(self.current.strip)

        if self.strips:
            self.current.strip = self.strips[-1]

    # def duplicateStrip(self):
    #   """
    #   Creates a new strip identical to the last one created and adds it to right of the display.
    #   """
    #   newStrip = self.strips[-1].clone()

    # def addStrip(self, stripIndex=-1) -> 'GuiStripNd':

    def setLastAxisOnly(self, lastAxisOnly: bool = True):
        self.lastAxisOnly = lastAxisOnly

    def showAxes(self, strips=None, stretchValue=False, widths=True):
        # use the strips as they are ordered in the model
        currentStrips = self.orderedStrips
        # currentStrips = strips if strips else self.strips

        if currentStrips:
            if self.lastAxisOnly:
                for ss in currentStrips[:-1]:
                    # ss.plotWidget.plotItem.axes['right']['item'].hide()
                    try:
                        ss._CcpnGLWidget.setRightAxisVisible(axisVisible=False)
                    except Exception as es:
                        getLogger().debugGL('OpenGL widget not instantiated', strip=ss, error=es)

                        # currentStrips[-1].plotWidget.plotItem.axes['right']['item'].show()

                try:
                    currentStrips[-1]._CcpnGLWidget.setRightAxisVisible(axisVisible=True)
                except Exception as es:
                    getLogger().debugGL('OpenGL widget not instantiated', strip=currentStrips[-1], error=es)

            else:
                for ss in self.strips:
                    ss.plotWidget.plotItem.axes['right']['item'].show()
                    try:
                        ss._CcpnGLWidget.setRightAxisVisible(axisVisible=True)
                    except Exception as es:
                        getLogger().debugGL('OpenGL widget not instantiated', strip=ss, error=es)

            # self.setColumnStretches(True)
            self.setColumnStretches(stretchValue=stretchValue, widths=widths)

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

    def increaseStripWidth(self):
        strips = self.orderedStrips
        currentWidth = strips[0].width() * (100.0 + self.application.preferences.general.stripWidthZoomPercent) / 100.0
        AXIS_WIDTH = strips[0]._CcpnGLWidget.AXIS_MARGINRIGHT

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

    def decreaseStripWidth(self):
        strips = self.orderedStrips
        currentWidth = strips[0].width() * 100.0 / (100.0 + self.application.preferences.general.stripWidthZoomPercent)
        AXIS_WIDTH = strips[0]._CcpnGLWidget.AXIS_MARGINRIGHT

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

    def _copyPreviousStripValues(self, fromStrip, toStrip):
        # try:
        traceScale = fromStrip.spectrumViews[0].traceScale
        toStrip.setTraceScale(traceScale)

        # hTrace = fromStrip._CcpnGLWidget._updateHTrace
        # vTrace = fromStrip._CcpnGLWidget._updateVTrace
        # toStrip._CcpnGLWidget._updateHTrace = hTrace
        # toStrip._CcpnGLWidget._updateVTrace = vTrace
        # toStrip.hTraceAction.setChecked(hTrace)
        # toStrip.vTraceAction.setChecked(vTrace)

        if self.phasingFrame.isVisible():
            toStrip.turnOnPhasing()

    # except Exception as es:
    #   getLogger().warning('>>> ERROR turning on phasing - %s' % str(es))
    #   getLogger().debug('OpenGL widget not instantiated')

    def addStrip(self) -> 'GuiStripNd':
        """
        Creates a new strip by cloning strip with index (default the last) in the display.
        """
        if self.phasingFrame.isVisible():
            showWarning(str(self.windowTitle()), 'Please disable Phasing Console before adding strips')
            return

        stripIndex = -1  # ejb - just here for the minute
        newStrip = self.strips[stripIndex].clone()

        # newStrip.copyOrderedSpectrumViews(self.strips[stripIndex-1])

        self.showAxes()

        # do setColumnStretches here or in Gui.py (422)
        self.setColumnStretches(True)

        mainWindow = self.mainWindow
        mainWindow.pythonConsole.writeConsoleCommand("strip.clone()", strip=newStrip)
        getLogger().info("spectrumDisplay = ui.getByGid(%r); spectrumDisplay.addStrip(%d)" \
                         % (self.pid, stripIndex))

        self.current.strip = newStrip

        # ED: copy traceScale from the previous strips and enable phasing Console
        self._copyPreviousStripValues(self.strips[0], newStrip)

        return newStrip

    def _addObjStrip(self, strip=None) -> 'GuiStripNd':
        """
        Creates a new strip by cloning strip with index (default the last) in the display.
        """
        if self.phasingFrame.isVisible():
            showWarning(str(self.windowTitle()), 'Please disable Phasing Console before adding strips')
            return

        stripIndex = self.strips.index(strip)
        newStrip = strip.clone()

        self.showAxes()

        # do setColumnStretches here or in Gui.py (422)
        self.setColumnStretches(True)

        mainWindow = self.mainWindow
        mainWindow.pythonConsole.writeConsoleCommand("strip.clone()", strip=newStrip)
        getLogger().info("spectrumDisplay = ui.getByGid(%r); spectrumDisplay.addStrip(%d)" \
                         % (self.pid, stripIndex))

        self.current.strip = newStrip

        # ED: copy traceScale from the previous strips and enable phasing Console
        self._copyPreviousStripValues(self.strips[0], newStrip)

        return newStrip

    def setColumnStretches(self, stretchValue=False, scaleFactor=1.0, widths=True):
        # crude routine to set the stretch of all columns upto the last widget to stretchValue
        widgets = self.stripFrame.children()

        if widgets:
            thisLayout = self.stripFrame.layout()
            thisLayoutWidth = self.width()  # self.stripFrame.width()
            # thisLayout = self.layout
            # thisLayoutWidth = self.width()-2

            if not thisLayout.itemAt(0):
                return

            AXIS_WIDTH = 1
            AXIS_PADDING = 5
            if self.strips:
                # add 5% to account for any small borders
                firstStripWidth = thisLayoutWidth / (len(self.strips))  # * 1.025)
                AXIS_WIDTH = self.orderedStrips[0]._CcpnGLWidget.AXIS_MARGINRIGHT
            else:
                firstStripWidth = thisLayout.itemAt(0).widget().width()

            if not self.lastAxisOnly:
                maxCol = 0
                for wid in self.orderedStrips:  #widgets[1:]:
                    index = thisLayout.indexOf(wid)
                    if index >= 0:
                        row, column, cols, rows = thisLayout.getItemPosition(index)
                        maxCol = max(maxCol, column)

                for col in range(0, maxCol + 1):
                    if widths and thisLayout.itemAt(col):
                        thisLayout.itemAt(col).widget().setMinimumWidth(firstStripWidth)
                    thisLayout.setColumnStretch(col, 1 if stretchValue else 0)

                self.stripFrame.setMinimumWidth(self.stripFrame.minimumSizeHint().width())

            else:
                maxCol = 0
                for wid in self.orderedStrips:  #widgets[1:]:
                    index = thisLayout.indexOf(wid)
                    if index >= 0:
                        row, column, cols, rows = thisLayout.getItemPosition(index)
                        maxCol = max(maxCol, column)

                # set the correct widths for the strips
                leftWidth = scaleFactor * (thisLayoutWidth - AXIS_WIDTH - (maxCol * AXIS_PADDING)) / (maxCol + 1)
                endWidth = leftWidth + AXIS_WIDTH

                # # set the widths and column stretches
                # for col in range(0, maxCol):
                #   if widths:
                #     thisLayout.itemAt(col).widget().setMinimumWidth(leftWidth)
                #
                #   print('>>>', col, leftWidth, thisLayout.itemAt(col).widget())
                #   # self.orderedStrips[col].setMinimumWidth(leftWidth)
                #   thisLayout.setColumnStretch(col, leftWidth if stretchValue else 0)
                #
                # if widths and thisLayout.itemAt(maxCol):
                #   thisLayout.itemAt(maxCol).widget().setMinimumWidth(endWidth)
                #   # self.orderedStrips[maxCol].setMinimumWidth(leftWidth)
                #
                # print('>>>', maxCol, thisLayout.itemAt(maxCol).widget())
                # thisLayout.setColumnStretch(maxCol, endWidth if stretchValue else 0)

                # set the widths and column stretches
                for wid in self.orderedStrips:
                    index = thisLayout.indexOf(wid)
                    if index >= 0:
                        row, column, cols, rows = thisLayout.getItemPosition(index)

                        if column == maxCol:
                            thisLayout.setColumnStretch(column, endWidth if stretchValue else 0)
                            if widths:
                                wid.setMinimumWidth(endWidth)
                        else:
                            thisLayout.setColumnStretch(column, leftWidth if stretchValue else 0)
                            if widths:
                                wid.setMinimumWidth(leftWidth)

                # fix the width of the stripFrame
                self.stripFrame.setMinimumWidth(self.stripFrame.minimumSizeHint().width())

            # printWidths = [thisLayout.itemAt(col).widget().width() for col in list(range(maxCol+1))]
            # printWidths = [ss.width() for ss in self.orderedStrips]
            # print('>>>', self, self.width(), thisLayoutWidth, firstStripWidth, leftWidth, printWidths)

    def _maximiseRegions(self):
        """Zooms Y axis of current strip to show entire region"""
        for strip in self.strips:
            strip._maximiseRegions()

    def resetYZooms(self):
        """Zooms Y axis of current strip to show entire region"""
        for strip in self.strips:
            strip.resetYZoom()

    def resetXZooms(self):
        """Zooms X axis of current strip to show entire region"""
        for strip in self.strips:
            strip.resetXZoom()

    def _restoreZoom(self):
        """Restores last saved zoom of current strip."""
        try:
            if not self.strips:
                showWarning('Restore Zoom', 'SpectrumDisplay "%s" does not contain any strips' \
                            % self.pid)
                return

            if self.current.strip not in self.strips:
                strip = self.strips[0]
            else:
                strip = self.current.strip

            strip._restoreZoom()

            # else:
            #     self.current.strip._restoreZoom()

            # if not self.current.strip:
            #     showWarning('Restore Zoom', 'No strip selected')
            #     return
            # if self.current.strip not in self.strips:
            #     showWarning('Restore Zoom', 'Selected strip "%s" is not part of SpectrumDisplay "%s"' \
            #                 % (self.current.strip.pid, self.pid))
            #     return
            # else:
            #     self.current.strip._restoreZoom()
        except Exception as ex:
            getLogger().warning('Error restoring zoom')

    def _storeZoom(self):
        """Saves zoomed region of current strip."""
        try:
            if not self.strips:
                showWarning('Restore Zoom', 'SpectrumDisplay "%s" does not contain any strips' \
                            % self.pid)
                return

            if self.current.strip not in self.strips:
                strip = self.strips[0]
            else:
                strip = self.current.strip

            strip._storeZoom()

            # if not self.current.strip:
            #     showWarning('Store Zoom', 'No strip selected')
            #     return
            # if self.current.strip not in self.strips:
            #     showWarning('Store Zoom', 'Selected strip "%s" is not part of SpectrumDisplay "%s"' \
            #                 % (self.current.strip.pid, self.pid))
            #     return
            # else:
            #     self.current.strip._storeZoom()
        except:
            getLogger().warning('Error storing zoom')

    def _zoomIn(self):
        """zoom in to the current strip."""
        try:
            if not self.strips:
                showWarning('Restore Zoom', 'SpectrumDisplay "%s" does not contain any strips' \
                            % self.pid)
                return

            if self.current.strip not in self.strips:
                strip = self.strips[0]
            else:
                strip = self.current.strip

            strip._zoomIn()

            # if not self.current.strip:
            #     showWarning('Zoom In', 'No strip selected')
            #     return
            # if self.current.strip not in self.strips:
            #     showWarning('Zoom In', 'Selected strip "%s" is not part of SpectrumDisplay "%s"' \
            #                 % (self.current.strip.pid, self.pid))
            #     return
            # else:
            #     self.current.strip._zoomIn()
        except:
            getLogger().warning('Error zooming in')

    def _zoomOut(self):
        """zoom out of current strip."""
        try:
            if not self.strips:
                showWarning('Restore Zoom', 'SpectrumDisplay "%s" does not contain any strips' \
                            % self.pid)
                return

            if self.current.strip not in self.strips:
                strip = self.strips[0]
            else:
                strip = self.current.strip

            strip._zoomOut()

            # if not self.current.strip:
            #     showWarning('Zoom Out', 'No strip selected')
            #     return
            # if self.current.strip not in self.strips:
            #     showWarning('Zoom Out', 'Selected strip "%s" is not part of SpectrumDisplay "%s"' \
            #                 % (self.current.strip.pid, self.pid))
            #     return
            # else:
            #     self.current.strip._zoomOut()
        except:
            getLogger().warning('Error zooming out')

    def toggleCrossHair(self):
        """Toggles whether cross hair is displayed in all strips of spectrum display."""
        # toggle crosshairs for strips in this spectrumDisplay
        for strip in self.strips:
            strip._toggleCrossHair()

    def toggleGrid(self):
        """Toggles whether grid is displayed in all strips of spectrum display."""
        # toggle grid for strips in this spectrumDisplay
        for strip in self.strips:
            strip.toggleGrid()

    def _cyclePeakLabelling(self):
        """toggles peak labelling of current strip."""
        try:
            if not self.current.strip:
                showWarning('Cycle Peak Labelling', 'No strip selected')
                return

            # if self.current.strip not in self.strips:
            #   showWarning('Cycle Peak Labelling', 'Selected strip "%s" is not part of SpectrumDisplay "%s"' \
            #               % (self.current.strip.pid, self.pid))
            #   return
            # else:
            #   self.current.strip.cyclePeakLabelling()

            for strip in self.strips:
                strip.cyclePeakLabelling()

        except:
            getLogger().warning('Error cycling peak labelling')

    def _cyclePeakSymbols(self):
        """toggles peak labelling of current strip."""
        try:
            if not self.current.strip:
                showWarning('Cycle Peak Symbols', 'No strip selected')
                return

            # if self.current.strip not in self.strips:
            #   showWarning('Cycle Peak ymbols', 'Selected strip "%s" is not part of SpectrumDisplay "%s"' \
            #               % (self.current.strip.pid, self.pid))
            #   return
            # else:
            #   self.current.strip.cyclePeakLabelling()

            for strip in self.strips:
                strip.cyclePeakSymbols()
        except:
            getLogger().warning('Error cycling peak symbols')

    def _deletedPeak(self, peak):
        apiPeak = peak._wrappedData
        # NBNB TBD FIXME rewrite this to not use API peaks
        # ALSO move this machinery from subclasses to this class.
        for peakListView in self.activePeakItemDict:
            peakItemDict = self.activePeakItemDict[peakListView]
            peakItem = peakItemDict.get(apiPeak)
            if peakItem:
                # peakListView.spectrumView.strip.plotWidget.scene().removeItem(peakItem)
                del peakItemDict[apiPeak]
                inactivePeakItems = self.inactivePeakItemDict.get(peakListView)
                if inactivePeakItems:
                    inactivePeakItems.add(peakItem)

    def displaySpectrum(self, spectrum, axisOrder: (str,) = ()):
        """Display additional spectrum, with spectrum axes ordered according ton axisOrder
        """
        spectrum = self.getByPid(spectrum) if isinstance(spectrum, str) else spectrum

        self._startCommandEchoBlock('displaySpectrum', spectrum, values=locals(),
                                    defaults={'axisOrder': ()})
        try:
            newSpectrum = self.strips[0].displaySpectrum(spectrum, axisOrder=axisOrder)
            if newSpectrum:
                newInd = self.spectrumViews.index(newSpectrum)
                index = list(self.getOrderedSpectrumViewsIndex())
                index = [(ii + 1) if (ii >= newInd) else ii for ii in index]
                index.append(newInd)

                # index = list(self.getOrderedSpectrumViewsIndex())
                # index.append(len(index))
                self.setOrderedSpectrumViewsIndex(tuple(index))

                # now move the inserted item to the end
                # get index of the new item, update all current indices greater than this + 1
                # add new index to the end

                # self._orderedSpectra.append(spectrum)

                # for strip in self.strips:
                #
                #   # displaySpectrum above creates a new spectrum for each strip in the display
                #   # but only returns the first one
                #   # this loops through the strips and adds each to the strip ordered list
                #   existingViews = set(strip.spectrumDisplay.orderedSpectrumViews(strip.spectrumViews))
                #   newViews = set(strip.spectrumViews)
                #   dSet = set(newViews).difference(existingViews)
                #
                #   # append those not found
                #   for spInDSet in dSet:
                #     strip.appendSpectrumView(spInDSet)

        except Exception as es:
            getLogger().warning('Error appending newSpectrum: %s' % spectrum)
        finally:
            self._endCommandEchoBlock()

    def _removeSpectrum(self, spectrum):
        try:
            # self._orderedSpectra.remove(spectrum)
            self._orderedSpectrumViews.removeSpectrumView(spectrum)
        except:
            getLogger().warning('Error, %s does not exist' % spectrum)

    def makeStripPlot(self, peaks=None, nmrResidues=None,
                      autoClearMarks=True,
                      sequentialStrips=True,
                      markPositions=True,
                      widths=None):
        """Make a list of strips in the current spectrumDisplay based on the list of peaks or
        the list of nmrResidues passing in
        Can only choose either peaks or nmrResidues, peaks chosen will override any selected nmrResidues
        """

        # need to clean up the use of GLNotifier - possibly into AbstractWrapperObject
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
        from functools import partial
        from ccpn.ui.gui.lib.Strip import navigateToPositionInStrip, navigateToNmrAtomsInStrip

        def _updateGl(self, spectrumList):
            GLSignals = GLNotifier(parent=self)
            GLSignals.emitPaintEvent()

        if peaks or nmrResidues:

            GLSignals = GLNotifier(parent=self)
            _undo = self.project._undo

            project = self.project
            project._startCommandEchoBlock('makeStripPlot', peaks, nmrResidues,
                                           autoClearMarks, sequentialStrips,
                                           markPositions, widths)
            try:
                # _undo._newItem(undoPartial=partial(_updateGl, self, []))

                if autoClearMarks:
                    self.mainWindow.clearMarks()

                # Make sure there are enough strips to display nmrAtomPairs
                stripCount = len(peaks) if peaks else len(nmrResidues)
                while len(self.strips) < stripCount:
                    self.addStrip()
                for strip in self.strips[stripCount:]:
                    self.removeStrip(strip)

                # build the strips
                if peaks:
                    for ii, pk in enumerate(peaks):
                        strip = self.strips[ii]

                        newWidths = [0.2] * len(self.axisCodes)
                        if widths == None:
                            # set the width in case of nD (n>2)
                            _widths = {'H': 0.3, 'C': 1.0, 'N': 1.0}
                            _ac = strip.axisCodes[0]
                            _w = _widths.setdefault(_ac[0], 1.0)
                            newWidths = [_w, 'full']

                        navigateToPositionInStrip(strip, pk.position, pk.axisCodes, widths=newWidths)

                elif nmrResidues:
                    for ii, nmr in enumerate(nmrResidues):
                        strip = self.strips[ii]

                        newWidths = ['default'] * len(strip.axisCodes)
                        if widths == None:
                            # set the width in case of nD (n>2)
                            _widths = {'H': 0.3, 'C': 1.0, 'N': 1.0}
                            _ac = strip.axisCodes[0]
                            _w = _widths.setdefault(_ac[0], 1.0)
                            newWidths = [_w, 'full']

                        navigateToNmrAtomsInStrip(strip, nmr.nmrAtoms,
                                                  widths=newWidths, markPositions=markPositions, setNmrResidueLabel=False)

                # _undo._newItem(redoPartial=partial(_updateGl, self, []))

                # repaint - not sure whether needed here
                GLSignals.emitPaintEvent()

            except Exception as es:
                showWarning(str(self.windowTitle()), str(es))
            finally:
                self.project._endCommandEchoBlock()


#=========================================================================================


def _deletedPeak(peak: Peak):
    """Function for notifiers.
    #CCPNINTERNAL
    """

    for spectrumView in peak.peakList.spectrum.spectrumViews:
        spectrumView.strip.spectrumDisplay._deletedPeak(peak)


def _spectrumHasChanged(spectrum: Spectrum):
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


GuiSpectrumDisplay.processSpectrum = GuiSpectrumDisplay.displaySpectrum  # ejb - from SpectrumDisplay
