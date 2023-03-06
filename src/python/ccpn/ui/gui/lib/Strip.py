"""
This file contains the Strip classes (1D and nD versions).
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
__dateModified__ = "$dateModified: 2023-03-06 13:14:30 +0000 (Mon, March 06, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2023-01-24 10:28:48 +0000 (Tue, January 24, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui._implementation.Strip import Strip as _CoreClassStrip
from ccpn.ui.gui.lib.GuiStrip1d import GuiStrip1d as _GuiStrip1d
from ccpn.ui.gui.lib.GuiStripNd import GuiStripNd as _GuiStripNd

from ccpn.core.Project import Project
from ccpn.util.Logging import getLogger


class Strip(_CoreClassStrip):

    @classmethod
    def _newInstanceFromApiData(cls, project, apiObj):
        """Return a new instance of cls, initialised with data from apiObj
        """
        apiSpectrumDisplay = apiObj.spectrumDisplay
        if apiSpectrumDisplay.is1d:
            return Strip1d(project, apiObj)
        else:
            return StripNd(project, apiObj)


class Strip1d(Strip, _GuiStrip1d):
    """1D strip"""

    def __init__(self, project: Project, wrappedData: 'ApiBoundStrip'):

        # _CoreClassStrip.__init__(self, project, wrappedData)
        Strip.__init__(self, project, wrappedData)

        getLogger().debug(f'Strip1d>> spectrumDisplay: {self.spectrumDisplay}')
        _GuiStrip1d.__init__(self, self.spectrumDisplay)

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


class StripNd(Strip, _GuiStripNd):
    """ND strip """

    def __init__(self, project: Project, wrappedData: 'ApiBoundStrip'):

        # _CoreClassStrip.__init__(self, project, wrappedData)
        Strip.__init__(self, project, wrappedData)

        getLogger().debug(f'StripNd>> spectrumDisplay={self.spectrumDisplay}')
        _GuiStripNd.__init__(self, self.spectrumDisplay)

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

# #=========================================================================================
# # For Registering
# #=========================================================================================
#
#
#
#
# def _factoryFunction(project: Project, wrappedData):
#     """create Strip, dispatching to subtype depending on wrappedData
#     """
#     apiSpectrumDisplay = wrappedData.spectrumDisplay
#     if apiSpectrumDisplay.is1d:
#         return Strip1d(project, wrappedData)
#     else:
#         return StripNd(project, wrappedData)
#
# # _CoreClassStrip._registerCoreClass(factoryFunction=_factoryFunction)
