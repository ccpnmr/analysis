"""
A class to manage theme's and resulting colours
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
__dateModified__ = "$dateModified: 2024-10-27 14:16:42 +0000 (Sun, October 27, 2024) $"
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
from PyQt5 import QtGui

from ccpn.framework.Application import getApplication

def getThemeManager():
    """get the themeManager instance from MainWindow
    """
    _app = getApplication()
    if _app.ui.hasGui:
        return _app.ui.mainWindow._themeManager
    else:
        raise RuntimeError("ThemeManager not initialized")


class ThemeManager():
    """Class to manage theme related settings and actions
    """
    def __init__(self, mainWindow, theme=None):
        """Initialise the themeManager instance; set theme from
        :param mainWindow: The mainWindow instance
        :param theme: The optional theme to set, e.g. light, dark
        """
        self.mainWindow = mainWindow
        self.theme = None
        if theme:
            self.setTheme(theme)

        # more here

    def setTheme(self, theme):
        """Sets the theme.
        :param theme: The theme to set, e.g. light or dark
        """
        self.theme = theme
        # more action required

    def getColour(self, role) -> QtGui.QPalette:
        """Get the colour of the given role
        :param role: The role
        :return: The colour of the given role
        """

# # in MainWindow.__init__
# _theme = getPreferences().get(THEME)
# self._themeManager = ThemeManager(mainWindow=self, theme=_theme)
#
# # elsewhere in code
# self.mainWindow._themeManager.getColour(LABEL_FOREGROUND)
