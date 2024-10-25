"""
This file contains the Strip classes (1D and nD versions).
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

from copy import deepcopy

from ccpn.ui._implementation.Strip import Strip as _CoreClassStrip
from ccpn.ui.gui.lib.GuiStrip1d import GuiStrip1d as _GuiStrip1d
from ccpn.ui.gui.lib.GuiStripNd import GuiStripNd as _GuiStripNd
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import AXISASPECTRATIOS, AXISASPECTRATIOMODE
from ccpn.ui.gui.guiSettings import _styleBlue

from ccpn.core.Project import Project
from ccpn.util.Logging import getLogger


# GWV 24/10/24: Implementation change
def _factoryFunction(project, wrappedData):
    """The factory function used to create 1d or nD versions of the
    Strip object.
    Used in core.__init__ to define the proper instantiation
    """
    klass = Strip1d if wrappedData.spectrumDisplay.is1d else StripNd
    return klass(project=project, wrappedData=wrappedData)


# class _Strip(_CoreClassStrip):
#


class Strip1d(_CoreClassStrip, _GuiStrip1d):
    """Just a class to combine the "data" coreClass and Gui1D strip class
    """

    def __init__(self, project: Project, wrappedData: 'ApiBoundStrip'):

        _CoreClassStrip.__init__(self, project, wrappedData)
        _GuiStrip1d.__init__(self, self.spectrumDisplay)

        getLogger().debug(
                    _styleBlue(f'Strip1d.__init__>> spectrumDisplay: {self.spectrumDisplay}')
        )

        # cannot add the Frame until fully done
        strips = self.spectrumDisplay.orderedStrips
        if self in strips:
            stripIndex = strips.index(self)
        else:
            stripIndex = len(strips)
            getLogger().warning(f'Strip ordering not defined for {str(self.pid)} in {str(self.spectrumDisplay.pid)}')

        tilePosition = self.tilePosition

        if self.spectrumDisplay.stripArrangement == 'Y':

            # strips are arranged in a row
            # self.spectrumDisplay.stripFrame.layout().addWidget(self, 0, stripIndex)
            if True:  #tilePosition is None:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, 0, stripIndex)
                self.tilePosition = (0, stripIndex)
            # else:
            #     self.spectrumDisplay.stripFrame.layout().addWidget(self, tilePosition[0], tilePosition[1])

        elif self.spectrumDisplay.stripArrangement == 'X':

            # strips are arranged in a column
            # self.spectrumDisplay.stripFrame.layout().addWidget(self, stripIndex, 0)
            if True:  #tilePosition is None:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, stripIndex, 0)
                self.tilePosition = (0, stripIndex)
            # else:
            #     self.spectrumDisplay.stripFrame.layout().addWidget(self, tilePosition[1], tilePosition[0])

        elif self.spectrumDisplay.stripArrangement == 'T':

            # NOTE:ED - Tiled plots not fully implemented yet
            getLogger().warning(f'Tiled plots not implemented for spectrumDisplay: {str(self.spectrumDisplay.pid)}')

        else:
            getLogger().warning(f'Strip direction is not defined for spectrumDisplay: {str(self.spectrumDisplay.pid)}')


class StripNd(_CoreClassStrip, _GuiStripNd):
    """Just a class to combine the "data" coreClass and Gui nD strip class
    """
    def __init__(self, project: Project, wrappedData: 'ApiBoundStrip'):

        _CoreClassStrip.__init__(self, project, wrappedData)
        _GuiStripNd.__init__(self, self.spectrumDisplay)

        getLogger().debug(
                _styleBlue(f'StripNd.__init__>> spectrumDisplay={self.spectrumDisplay}')
        )

        # cannot add the Frame until fully done
        strips = self.spectrumDisplay.orderedStrips
        if self in strips:
            stripIndex = strips.index(self)
        else:
            stripIndex = len(strips)
            getLogger().warning(f'Strip ordering not defined for {str(self.pid)} in {str(self.spectrumDisplay.pid)}')

        tilePosition = self.tilePosition

        if self.spectrumDisplay.stripArrangement == 'Y':

            # strips are arranged in a row
            # self.spectrumDisplay.stripFrame.layout().addWidget(self, 0, stripIndex)
            if True:  #tilePosition is None:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, 0, stripIndex)
                self.tilePosition = (0, stripIndex)
            # else:
            #     self.spectrumDisplay.stripFrame.layout().addWidget(self, tilePosition[0], tilePosition[1])

        elif self.spectrumDisplay.stripArrangement == 'X':

            # strips are arranged in a column
            # self.spectrumDisplay.stripFrame.layout().addWidget(self, stripIndex, 0)
            if True:  #tilePosition is None:
                self.spectrumDisplay.stripFrame.layout().addWidget(self, stripIndex, 0)
                self.tilePosition = (0, stripIndex)
            # else:
            #     self.spectrumDisplay.stripFrame.layout().addWidget(self, tilePosition[1], tilePosition[0])

        elif self.spectrumDisplay.stripArrangement == 'T':

            # NOTE:ED - Tiled plots not fully implemented yet
            getLogger().warning(f'Tiled plots not implemented for spectrumDisplay: {str(self.spectrumDisplay.pid)}')

        else:
            getLogger().warning(f'Strip direction is not defined for spectrumDisplay: {str(self.spectrumDisplay.pid)}')
