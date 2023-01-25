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
__dateModified__ = "$dateModified: 2023-01-25 18:04:11 +0000 (Wed, January 25, 2023) $"
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

## SpectrumDisplay class
from ccpn.ui._implementation.SpectrumDisplay import SpectrumDisplay as _coreClassSpectrumDisplay
from ccpn.ui.gui.modules.SpectrumDisplay1d import SpectrumDisplay1d as _SpectrumDisplay1d
from ccpn.ui.gui.modules.SpectrumDisplayNd import SpectrumDisplayNd as _SpectrumDisplayNd

from ccpn.util.Logging import getLogger


#TODO: Need to check on the consequences of hiding name from the wrapper

# NB: GWV had to comment out the name property to make it work
# conflicts existed between the 'name' and 'window' attributes of the two classes
# the pyqtgraph descendents need name(), GuiStripNd had 'window', but that could be replaced with
# mainWindow throughout



class SpectrumDisplay1d(_coreClassSpectrumDisplay, _SpectrumDisplay1d):
    """1D bound display"""

    def __init__(self, project: Project, wrappedData: 'ApiBoundDisplay'):
        """Local override init for Qt subclass
        """
        getLogger().debug('SpectrumDisplay1d>> project: %s, project.application: %s' %
                                  (project, project.application))
        _coreClassSpectrumDisplay.__init__(self, project, wrappedData)

        # hack for now
        self.application = project.application
        self.mainWindow = self.application.ui.mainWindow
        _SpectrumDisplay1d.__init__(self, mainWindow=self.mainWindow)


class SpectrumDisplayNd(_coreClassSpectrumDisplay, _SpectrumDisplayNd):
    """ND bound display"""

    def __init__(self, project: Project, wrappedData: 'ApiBoundDisplay'):
        """Local override init for Qt subclass"""
        getLogger().debug('SpectrumDisplayNd>> project: %s, project.application: %s' % (project, project.application))
        _coreClassSpectrumDisplay.__init__(self, project, wrappedData)

        # hack for now;
        self.application = project.application
        self.mainWindow = self.application.ui.mainWindow
        _SpectrumDisplayNd.__init__(self, mainWindow=self.mainWindow)


def _factoryFunction(project: Project, wrappedData):
    """create SpectrumDisplay, dispatching to subtype depending on wrappedData"""
    if wrappedData.is1d:
        return SpectrumDisplay1d(project, wrappedData)
    else:
        return SpectrumDisplayNd(project, wrappedData)

_coreClassSpectrumDisplay._factoryFunction = _factoryFunction
