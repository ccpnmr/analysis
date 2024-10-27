"""
A convenience class
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-10-27 11:52:37 +0000 (Sun, October 27, 2024) $"
__version__ = "$Revision: 3.2.7.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2024-10-27 11:20:30 +0100 (Sun, October 27, 2024) $"
#=========================================================================================
# Start of code
#=========================================================================================
#

class _FrameworkProperties(object):
    """Convenience class to have easy Framework derived properties
    """
    def __init__(self):
        from ccpn.framework.Application import getApplication
        self._application = getApplication()

    @property
    def application(self):
        """:return the Application instance
        """
        if self._application is None:
            raise RuntimeError(f'Unable to retrieve application from {self}')
        return self._application

    @property
    def project(self):
        """:return the Project instance
        """
        if self._application is None:
            raise RuntimeError(f'Unable to retrieve application from {self}')
        return self._application.project

    @property
    def current(self):
        """:return the Current instance
        """
        if self._application is None:
            raise RuntimeError(f'Unable to retrieve application from {self}')
        return self._application.current

    @property
    def mainWindow(self):
        """:return the MainWindow instance or None
        """
        if self._application is None:
            raise RuntimeError(f'Unable to retrieve application from {self}')
        if self._application.hasGui:
            return self.application.mainWindow
        else:
            return None

    @property
    def ui(self):
        """:return the Ui instance
        """
        if self._application is None:
            raise RuntimeError(f'Unable to retrieve application from {self}')
        return self._application.ui
