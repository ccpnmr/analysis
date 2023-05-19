"""Module Documentation here

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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-05-19 16:58:07 +0100 (Fri, May 19, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence

from ccpn.ui.gui.lib.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.util.Logging import getLogger


class SpectrumDisplay1d(GuiSpectrumDisplay):
    MAXPEAKLABELTYPES = 7
    MAXPEAKSYMBOLTYPES = 4
    MAXARROWTYPES = 3

    #GWV 26Jan2023: removed

    # def _fillToolBar(self):
    #     """
    #     Adds specific icons for 1d spectra to the spectrum utility toolbar.
    #     """
    #     tb = self.spectrumUtilToolBar
    #     self._spectrumUtilActions = {}
    #
    #     toolBarItemsFor1d = [
    #         #  action name,        icon,                 tooltip,                                       active, callback
    #
    #         ('increaseStripWidth', 'icons/range-expand',   'Increase the width of strips in display',   True, self.increaseStripSize),
    #         ('decreaseStripWidth', 'icons/range-contract', 'Decrease the width of strips in display',   True, self.decreaseStripSize),
    #         ('maximiseZoom',       'icons/zoom-full',      'Maximise Zoom (ZA)',                        True, self._resetAllZooms),
    #
    #         ('maximiseHeight',     'icons/zoom-best-fit-1d', 'Maximise Height',                         True, self._resetYZooms),
    #         ('maximiseWidth',      'icons/zoom-full-1d',     'Maximise Width',                          True, self._resetXZooms),
    #
    #         ('storeZoom',          'icons/zoom-store',   'Store Zoom (ZS)',                             True, self._storeZoom),
    #         ('restoreZoom',        'icons/zoom-restore', 'Restore Zoom (ZR)',                           True, self._restoreZoom),
    #         ('undoZoom',           'icons/zoom-undo',    'Previous Zoom (ZP)',                          True, self._previousZoom),
    #         ('redoZoom',           'icons/zoom-redo',    'Next Zoom (ZN)',                              True, self._nextZoom),
    #         # ('addStrip', 'icons/plus', 'Duplicate the rightmost strip', True, self.addStrip),
    #         # ('removeStrip', 'icons/minus', 'Remove the current strip', True, self.removeCurrentStrip),
    #         ]
    #
    #     # create the actions from the lists
    #     for aName, icon, tooltip, active, callback in toolBarItemsFor1d:
    #         action = tb.addAction(tooltip, callback)
    #         if icon is not None:
    #             ic = Icon(icon)
    #             action.setIcon(ic)
    #         self._spectrumUtilActions[aName] = action

    # # GWV 26Jan2023: Not used
    # def processSpectra(self, pids: Sequence[str], event):
    #     """Display spectra defined by list of Pid strings
    #     """
    #     for ss in pids:
    #         getLogger().info('processing Spectrum %s' % ss)
    #     getLogger().info(str(self.parent()))

    # def adjustContours(self):
    #     """Initiate a popup to modify  settings
    #     """
    #     #GWV: Very strange and really should not be here; called from GuiMainWindow TODO: move there
    #     from ccpn.ui.gui.popups.SpectrumPropertiesPopup import SpectrumDisplayPropertiesPopup1d
    #
    #     if self.strips:
    #         popup = SpectrumDisplayPropertiesPopup1d(parent=self.mainWindow,
    #                                                  mainWindow=self.mainWindow,
    #                                                  orderedSpectrumViews=self.strips[0].getSpectrumViews())
    #         popup.exec_()
    #         # popup.raise_()

    # def raiseContourBase(self):
    #     """
    #     Increases contour base level for all spectra visible in the display.
    #     """
    #     # Not implemented for 1D
    #     pass
    #
    # def lowerContourBase(self):
    #     """
    #     Decreases contour base level for all spectra visible in the display.
    #     """
    #     # Not implemented for 1D
    #     pass

    # def setVisibleAxes(self):
    #     # Not implemented for 1D
    #     pass
    #
    # def _highlightAxes(self, strip, state):
    #     """Highlight the last row axis if strip
    #     """
    #     # Not implemented for 1D
    #     pass
