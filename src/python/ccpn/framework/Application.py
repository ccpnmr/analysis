"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-01-21 19:10:48 +0000 (Fri, January 21, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.decorators import singleton
from ccpn.framework.Translation import defaultLanguage

AnalysisAssign = 'AnalysisAssign'
AnalysisScreen = 'AnalysisScreen'
AnalysisMetabolomics = 'AnalysisMetabolomics'
AnalysisStructure = 'AnalysisStructure'
ApplicationNames = [AnalysisAssign, AnalysisScreen, AnalysisMetabolomics, AnalysisStructure]


@singleton
class ApplicationContainer():
    """A singleton class used to register the application (eg AnalysisScreen)
    """
    application = None

    def register(self, application):
        self.application = application


def getApplication():
    """Return the application instance"""
    container = ApplicationContainer()
    return container.application


class Arguments:
    """Class for setting FrameWork input arguments directly"""
    language = defaultLanguage
    interface = 'NoUi'
    nologging = True
    debug = False
    debug2 = False
    debug3 = False
    skipUserPreferences = True
    projectPath = None
    _skipUpdates = False

    def __init__(self, projectPath=None, **kwds):

        # Dummy values; GWV: no idea as to what purpose
        for component in ApplicationNames:
            setattr(self, 'include' + component, None)

        self.projectPath = projectPath
        for tag, val in kwds.items():
            setattr(self, tag, val)
