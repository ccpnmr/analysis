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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-09-20 15:02:11 +0100 (Fri, September 20, 2024) $"
__version__ = "$Revision: 3.2.7 $"
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


_DEBUG = False


class Strip(_CoreClassStrip):

    @classmethod
    def _newInstanceFromApiData(cls, apiObj, project=None):
        """Return a new instance of cls, initialised with data from apiObj.
        Checks for existence, and potential factory function.
        """
        from ccpn.framework.Application import getProject

        # override cls-type - 1D/nD display
        klass = Strip1d if apiObj.spectrumDisplay.is1d else StripNd
        if project is None:
            project = getProject()
        if apiObj in project._data2Obj:
            # This happens with Window, as it get initialised by the Window-Store and then once
            # more as child of Project
            newInstance = project._data2Obj[apiObj]
            if _DEBUG:
                getLogger().debug(_styleBlue(f'==> found  {id(newInstance)}  {newInstance}'
                                             f'\n                     {apiObj}'
                                             ))
        elif (_factoryFunction := klass._factoryFunction) is not None:
            newInstance = _factoryFunction(project, apiObj)
        else:
            newInstance = klass(project, apiObj)

        if newInstance is None:
            raise RuntimeError(f'Error creating new instance of class "{klass.__name__}"')

        return newInstance

    def _postRestore(self):
        """Handle post-initialising children after all children have been restored
        """
        settings = self.spectrumDisplay._getSettingsDict()
        prefs = self._preferences

        # copy values from preferences
        glWidget = self._CcpnGLWidget
        glWidget._aspectRatioMode = settings[AXISASPECTRATIOMODE]
        glWidget._aspectRatios = deepcopy(settings[AXISASPECTRATIOS])
        glWidget._applyXLimit = prefs.zoomXLimitApply
        glWidget._applyYLimit = prefs.zoomYLimitApply

        super()._postRestore()


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
