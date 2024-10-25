"""
This file contains the top-level SpectrumDisplay module code
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
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
__dateModified__ = "$dateModified: 2024-10-25 11:08:18 +0100 (Fri, October 25, 2024) $"
__version__ = "$Revision: 3.2.7.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2023-01-24 10:28:48 +0000 (Tue, January 24, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Project import Project

from ccpn.ui._implementation.SpectrumDisplay import SpectrumDisplay as _SpectrumDisplayCoreClass
from ccpn.ui.gui.lib.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpn.ui.gui.guiSettings import _styleBlue
from ccpn.util.Logging import getLogger


# NB:
# GWV any coreClass 'name' property creates conflicts as pyqtgraph descendants need name()
# GWV 26Jan2023: Remark still valid??


# GWV 24/10/24: Implementation change
def _factoryFunction(project, wrappedData):
    """The factory function used to create 1d or nD versions of the
    SpectrumDisplay module.
    Used in core.__init__ to define the proper instantiation
    """
    klass = SpectrumDisplay1d if wrappedData.is1d else SpectrumDisplayNd
    return klass(project=project, wrappedData=wrappedData)


# class _SpectrumDisplay(_CoreClassSpectrumDisplay):
#


class SpectrumDisplay1d(_SpectrumDisplayCoreClass, GuiSpectrumDisplay):
    """Just a class to combine the "data" coreClass and Gui SpectrumDisplay class
    """

    # NB: inherits from AbstractWrapper (and more):
    # shortClassName = 'GD'
    # className = 'SpectrumDisplay'

    MAXPEAKLABELTYPES = 7
    MAXPEAKSYMBOLTYPES = 4
    MAXARROWTYPES = 3
    MAXMULTIPLETLABELTYPES = 7
    MAXMULTIPLETSYMBOLTYPES = 1

    # NB: 'self' is added to the callback in _fillToolbar using partial
    _toolbarItems = [
        #  action name,        icon,                 tooltip,                                       active, callback
        ('addStrip', 'icons/plus', 'Duplicate the rightmost strip', True, GuiSpectrumDisplay.addStrip),
        ('removeStrip', 'icons/minus', 'Remove the current strip', True, GuiSpectrumDisplay.removeCurrentStrip),
        ('increaseStripWidth', 'icons/range-expand', 'Increase the width of strips in display', True,
         GuiSpectrumDisplay.increaseStripSize),
        ('decreaseStripWidth', 'icons/range-contract', 'Decrease the width of strips in display', True,
         GuiSpectrumDisplay.decreaseStripSize),
        ('maximiseZoom', 'icons/zoom-full', 'Maximise Zoom (ZA)', True, GuiSpectrumDisplay._resetAllZooms),

        ('maximiseHeight', 'icons/zoom-best-fit-1d', 'Maximise Height', True, GuiSpectrumDisplay._resetYZooms),
        ('maximiseWidth', 'icons/zoom-full-1d', 'Maximise Width', True, GuiSpectrumDisplay._resetXZooms),

        ('storeZoom', 'icons/zoom-store', 'Store Zoom (ZS)', True, GuiSpectrumDisplay._storeZoom),
        ('restoreZoom', 'icons/zoom-restore', 'Restore Zoom (ZR)', True, GuiSpectrumDisplay._restoreZoom),
        ('undoZoom', 'icons/zoom-undo', 'Previous Zoom (ZP)', True, GuiSpectrumDisplay._previousZoom),
        ('redoZoom', 'icons/zoom-redo', 'Next Zoom (ZN)', True, GuiSpectrumDisplay._nextZoom),
        ('setZoom', 'icons/zoom-set', 'Set Zoom... (SZ)', True, GuiSpectrumDisplay._setZoom),

        ]

    def __init__(self, project: Project, wrappedData: 'ApiBoundDisplay'):
        """Init for SpectrumDisplay1d;
        Handles CoreClass SpectrumDisplay and GuiSpectrumDisplay
        """
        # project (on restore) or ui (on newSpectrumDisplay) has _mainWindow
        _mainWindow = project._mainWindow or project.application.ui.mainWindow

        getLogger().debug(
             _styleBlue(f'SpectrumDisplay1d.__init__>> {_mainWindow=} (set by project: {bool(project._mainWindow)})')
        )

        _SpectrumDisplayCoreClass.__init__(self, project, wrappedData)
        GuiSpectrumDisplay.__init__(self, mainWindow=_mainWindow, useScrollArea=True)


class SpectrumDisplayNd(_SpectrumDisplayCoreClass, GuiSpectrumDisplay):
    """Just a class to combine the "data" coreClass and Gui SpectrumDisplay class
    """

    # NB: inherits from AbstractWrapper (and more):
    # shortClassName = 'GD'
    # className = 'SpectrumDisplay'

    MAXPEAKLABELTYPES = 7
    MAXPEAKSYMBOLTYPES = 4
    MAXARROWTYPES = 3
    MAXMULTIPLETLABELTYPES = 7
    MAXMULTIPLETSYMBOLTYPES = 1

    # NB: 'self' is added to the callback in _fillToolbar using partial
    _toolbarItems = [
        #  action name,         icon,                   tooltip,                                     active, callback

        ('raiseBase', 'icons/contour-base-up', 'Raise Contour Base Level (Shift + Mouse Wheel)', True,
         GuiSpectrumDisplay._raiseContourBase),
        ('lowerBase', 'icons/contour-base-down', 'Lower Contour Base Level (Shift + Mouse Wheel)', True,
         GuiSpectrumDisplay._lowerContourBase),

        # not needed now
        # ('increaseTraceScale', 'icons/tracescale-up', 'Increase scale of 1D traces in display (TU)', True, self.increaseTraceScale),
        # ('decreaseTraceScale', 'icons/tracescale-down', 'Decrease scale of 1D traces in display (TD)', True, self.decreaseTraceScale),
        ('addStrip', 'icons/plus', 'Duplicate the rightmost strip', True, GuiSpectrumDisplay.addStrip),
        ('removeStrip', 'icons/minus', 'Remove the current strip', True, GuiSpectrumDisplay.removeCurrentStrip),
        ('increaseStripWidth', 'icons/range-expand', 'Increase the width of strips in display', True,
         GuiSpectrumDisplay.increaseStripSize),
        ('decreaseStripWidth', 'icons/range-contract', 'Decrease the width of strips in display', True,
         GuiSpectrumDisplay.decreaseStripSize),
        ('maximiseZoom', 'icons/zoom-full', 'Maximise Zoom (ZA)', True, GuiSpectrumDisplay._resetAllZooms),
        ('storeZoom', 'icons/zoom-store', 'Store Zoom (ZS)', True, GuiSpectrumDisplay._storeZoom),
        ('restoreZoom', 'icons/zoom-restore', 'Restore Zoom (ZR)', True, GuiSpectrumDisplay._restoreZoom),
        ('undoZoom', 'icons/zoom-undo', 'Previous Zoom (ZP)', True, GuiSpectrumDisplay._previousZoom),
        ('redoZoom', 'icons/zoom-redo', 'Next Zoom (ZN)', True, GuiSpectrumDisplay._nextZoom),
        ('setZoom', 'icons/zoom-set', 'Set Zoom... (SZ)', True, GuiSpectrumDisplay._setZoom),

        ]

    def __init__(self, project: Project, wrappedData: 'ApiBoundDisplay'):
        """Init for SpectrumDisplayNd;
        Handles CoreClass SpectrumDisplay and GuiSpectrumDisplay
        """
        # project (on restore) or ui (on newSpectrumDisplay) has _mainWindow
        _mainWindow = project._mainWindow or project.application.ui.mainWindow

        getLogger().debug(
             _styleBlue(f'SpectrumDisplayNd.__init__>> {_mainWindow=} (set by project: {bool(project._mainWindow)})')
        )

        _SpectrumDisplayCoreClass.__init__(self, project, wrappedData)
        GuiSpectrumDisplay.__init__(self, mainWindow=_mainWindow, useScrollArea=True)

    # Expose some methods for the nD case

    # @logCommand(get='self')
    def raiseContourBase(self):
        """
        Increases contour base level for all nD spectra visible in the display.
        """
        self._raiseContourBase()

    # @logCommand(get='self')
    def lowerContourBase(self):
        """
        Decreases contour base level for all nD spectra visible in the display.
        """
        self._lowerContourBase()

    # @logCommand(get='self')
    def addContourLevel(self):
        """
        Increases number of contours by 1 for all nD spectra visible in the display.
        """
        self._addContourLevel()

    # @logCommand(get='self')
    def removeContourLevel(self):
        """
        Decreases number of contours by 1 for all nD spectra visible in the display.
        """
        self._removeContourLevel()
