"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.decorators import singleton

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