"""
This file contains the top-level SpectrumDisplay module code
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2023-01-26 12:48:29 +0000 (Thu, January 26, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2023-01-24 10:28:48 +0000 (Tue, January 24, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Project import Project
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar

## SpectrumDisplay class
from ccpn.ui._implementation.SpectrumDisplay import SpectrumDisplay as _CoreClassSpectrumDisplay
from ccpn.ui.gui.lib.GuiSpectrumDisplay import GuiSpectrumDisplay

from ccpn.util.Logging import getLogger


# NB:
# GWV any coreClass 'name' property creates conflicts as pyqtgraph descendents need name()
# GWV 26Jan2023: Remark still valid??

# Can remove the _SpectrumDisplay1d/Nd intermediate classes as they do very little

class SpectrumDisplay1d(_CoreClassSpectrumDisplay, GuiSpectrumDisplay):
    """1D SpectrumDisplay
    """

    # NB: inherits from AbstractWrapper (and more):
    # shortClassName = 'GD'
    # className = 'SpectrumDisplay'

    MAXPEAKLABELTYPES = 7
    MAXPEAKSYMBOLTYPES = 4

    # NB: 'self' is added to the callback in _fillToolbar using partial
    _toolbarItems = [
        #  action name,        icon,                 tooltip,                                       active, callback

        ('increaseStripWidth', 'icons/range-expand',   'Increase the width of strips in display',   True, GuiSpectrumDisplay.increaseStripSize),
        ('decreaseStripWidth', 'icons/range-contract', 'Decrease the width of strips in display',   True, GuiSpectrumDisplay.decreaseStripSize),
        ('maximiseZoom',       'icons/zoom-full',      'Maximise Zoom (ZA)',                        True, GuiSpectrumDisplay._resetAllZooms),

        ('maximiseHeight',     'icons/zoom-best-fit-1d', 'Maximise Height',                         True, GuiSpectrumDisplay._resetYZooms),
        ('maximiseWidth',      'icons/zoom-full-1d',     'Maximise Width',                          True, GuiSpectrumDisplay._resetXZooms),

        ('storeZoom',          'icons/zoom-store',   'Store Zoom (ZS)',                             True, GuiSpectrumDisplay._storeZoom),
        ('restoreZoom',        'icons/zoom-restore', 'Restore Zoom (ZR)',                           True, GuiSpectrumDisplay._restoreZoom),
        ('undoZoom',           'icons/zoom-undo',    'Previous Zoom (ZP)',                          True, GuiSpectrumDisplay._previousZoom),
        ('redoZoom',           'icons/zoom-redo',    'Next Zoom (ZN)',                              True, GuiSpectrumDisplay._nextZoom),
        # ('addStrip', 'icons/plus', 'Duplicate the rightmost strip', True, self.addStrip),
        # ('removeStrip', 'icons/minus', 'Remove the current strip', True, self.removeCurrentStrip),
        ]

    def __init__(self, project: Project, wrappedData: 'ApiBoundDisplay'):
        """Init for SpectrumDisplay1d;
        Handles CoreClass SpectrumDisplay and GuiSpectrumDisplay
        """
        getLogger().debug('SpectrumDisplay1d>> project: %s, project.application: %s' %
                                  (project, project.application))
        _CoreClassSpectrumDisplay.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application
        self.mainWindow = self.application.ui.mainWindow
        GuiSpectrumDisplay.__init__(self, mainWindow=self.mainWindow, useScrollArea=True)
        i = 0

    def setVisibleAxes(self):
        # Not implemented for 1D
        pass

    def _highlightAxes(self, strip, state):
        """Highlight the last row axis if strip
        """
        # Not implemented for 1D
        pass


class SpectrumDisplayNd(_CoreClassSpectrumDisplay, GuiSpectrumDisplay):
    """nD SpectrumDisplay
    """
    # NB: inherits from AbstractWrapper (and more):
    # shortClassName = 'GD'
    # className = 'SpectrumDisplay'

    MAXPEAKLABELTYPES = 7
    MAXPEAKSYMBOLTYPES = 4

    # NB: 'self' is added to the callback in _fillToolbar using partial
    _toolbarItems = [
        #  action name,         icon,                   tooltip,                                     active, callback

        ('raiseBase',           'icons/contour-base-up', 'Raise Contour Base Level (Shift + Mouse Wheel)', True, GuiSpectrumDisplay._raiseContourBase),
        ('lowerBase',           'icons/contour-base-down', 'Lower Contour Base Level (Shift + Mouse Wheel)', True, GuiSpectrumDisplay._lowerContourBase),

        # not needed now
        # ('increaseTraceScale', 'icons/tracescale-up', 'Increase scale of 1D traces in display (TU)', True, self.increaseTraceScale),
        # ('decreaseTraceScale', 'icons/tracescale-down', 'Decrease scale of 1D traces in display (TD)', True, self.decreaseTraceScale),
        ('addStrip',            'icons/plus',           'Duplicate the rightmost strip',            True, GuiSpectrumDisplay.addStrip),
        ('removeStrip',         'icons/minus',          'Remove the current strip',                 True, GuiSpectrumDisplay.removeCurrentStrip),
        ('increaseStripWidth',  'icons/range-expand',   'Increase the width of strips in display',  True, GuiSpectrumDisplay.increaseStripSize),
        ('decreaseStripWidth',  'icons/range-contract', 'Decrease the width of strips in display',  True, GuiSpectrumDisplay.decreaseStripSize),
        ('maximiseZoom',        'icons/zoom-full',      'Maximise Zoom (ZA)',                       True, GuiSpectrumDisplay._resetAllZooms),
        ('storeZoom',           'icons/zoom-store',     'Store Zoom (ZS)',                          True, GuiSpectrumDisplay._storeZoom),
        ('restoreZoom',         'icons/zoom-restore',   'Restore Zoom (ZR)',                        True, GuiSpectrumDisplay._restoreZoom),
        ('undoZoom',            'icons/zoom-undo',      'Previous Zoom (ZP)',                       True, GuiSpectrumDisplay._previousZoom),
        ('redoZoom',            'icons/zoom-redo',      'Next Zoom (ZN)',                           True, GuiSpectrumDisplay._nextZoom),
        ]

    def __init__(self, project: Project, wrappedData: 'ApiBoundDisplay'):
        """Init for SpectrumDisplayNd;
        Handles CoreClass SpectrumDisplay and GuiSpectrumDisplay
        """
        getLogger().debug('SpectrumDisplayNd>> project: %s, project.application: %s' % (project, project.application))
        _CoreClassSpectrumDisplay.__init__(self, project, wrappedData)

        # hack for now;
        self.application = project.application
        self.mainWindow = self.application.ui.mainWindow
        GuiSpectrumDisplay.__init__(self, mainWindow=self.mainWindow, useScrollArea=True)
        i = 0

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

#=========================================================================================
# Registering
#=========================================================================================

def _factoryFunction(project: Project, wrappedData):
    """create SpectrumDisplay, dispatching to subtype depending on wrappedData"""
    if wrappedData.is1d:
        return SpectrumDisplay1d(project, wrappedData)
    else:
        return SpectrumDisplayNd(project, wrappedData)

_CoreClassSpectrumDisplay._factoryFunction = _factoryFunction
