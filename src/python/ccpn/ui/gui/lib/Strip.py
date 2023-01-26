"""
This file contains the Strip class
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
__dateModified__ = "$dateModified: 2023-01-26 16:35:00 +0000 (Thu, January 26, 2023) $"
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


class Strip1d(_CoreClassStrip, _GuiStrip1d):
    """1D strip"""

    def __init__(self, project: Project, wrappedData: 'ApiBoundStrip'):
        """Local override init for Qt subclass"""

        _CoreClassStrip.__init__(self, project, wrappedData)

        getLogger().debug('Strip1d>> spectrumDisplay: %s' % self.spectrumDisplay)
        _GuiStrip1d.__init__(self, self.spectrumDisplay)


class StripNd(_CoreClassStrip, _GuiStripNd):
    """ND strip """

    def __init__(self, project: Project, wrappedData: 'ApiBoundStrip'):
        """Local override init for Qt subclass"""

        _CoreClassStrip.__init__(self, project, wrappedData)

        getLogger().debug('StripNd>> spectrumDisplay=%s' % self.spectrumDisplay)
        _GuiStripNd.__init__(self, self.spectrumDisplay)

#=========================================================================================
# Registering
#=========================================================================================

def _factoryFunction(project: Project, wrappedData):
    """create SpectrumDisplay, dispatching to subtype depending on wrappedData
    """
    apiSpectrumDisplay = wrappedData.spectrumDisplay
    if apiSpectrumDisplay.is1d:
        return Strip1d(project, wrappedData)
    else:
        return StripNd(project, wrappedData)

_CoreClassStrip._registerCoreClass(factoryFunction=_factoryFunction)
