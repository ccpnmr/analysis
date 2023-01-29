"""
This file contains the SpectrumView classes (1D and nD versions)
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
__dateModified__ = "$dateModified: 2023-01-29 20:36:02 +0000 (Sun, January 29, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2023-01-24 10:28:48 +0000 (Tue, January 24, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui._implementation.SpectrumView import SpectrumView as _CoreClassSpectrumView
from ccpn.ui.gui.lib.GuiSpectrumView1d import GuiSpectrumView1d as _GuiSpectrumView1d
from ccpn.ui.gui.lib.GuiSpectrumViewNd import GuiSpectrumViewNd as _GuiSpectrumViewNd

from ccpn.core.Project import Project
from ccpn.util.Logging import getLogger


class SpectrumView(_CoreClassSpectrumView):

    @classmethod
    def _newInstanceFromApiData(cls, project, apiObj):
        """Return a new instance of cls, initialised with data from apiObj
        """
        if 'intensity' in apiObj.strip.spectrumDisplay.axisCodes:
            # 1D display
            return SpectrumView1d(project, apiObj)

        else:
            # ND display
            return SpectrumViewNd(project, apiObj)


class SpectrumView1d(SpectrumView, _GuiSpectrumView1d):
    """1D Spectrum View
    """

    def __init__(self, project: Project, wrappedData: 'ApiStripSpectrumView'):

        # _CoreClassSpectrumView.__init__(self, project, wrappedData)
        SpectrumView.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application

        getLogger().debug('SpectrumView1d>> %s' % self)
        _GuiSpectrumView1d.__init__(self)


class SpectrumViewNd(SpectrumView, _GuiSpectrumViewNd):
    """nD Spectrum View
    """

    def __init__(self, project: Project, wrappedData: 'ApiStripSpectrumView'):

        # _CoreClassSpectrumView.__init__(self, project, wrappedData)
        SpectrumView.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application

        getLogger().debug('SpectrumViewNd>> self=%s strip=%s' % (self, self.strip))
        _GuiSpectrumViewNd.__init__(self)


#=========================================================================================
# For Registering
#=========================================================================================



def _factoryFunction(project: Project, wrappedData):
    """create SpectrumView, dispatching to subtype depending on wrappedData
    """
    if 'intensity' in wrappedData.strip.spectrumDisplay.axisCodes:
        # 1D display
        return SpectrumView1d(project, wrappedData)
    else:
        # ND display
        return SpectrumViewNd(project, wrappedData)


# _CoreClassSpectrumView._registerCoreClass(factoryFunction=_factoryFunction)
