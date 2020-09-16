"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-09-16 12:14:33 +0100 (Wed, September 16, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-16 18:20:01 +0000 (Thu, March 16, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui


SYSTEMFONTREQUEST = 'moduleFont'
MONACOFONTREQUEST = 'editorFont'
HELVETICAFONTREQUEST = 'moduleFont'
LUCIDAGRANDEFONTREQUEST = 'messageFont'

DEFAULTFONT = 'defaultFont'
SYSTEMFONT = 'System'
MONACOFONT = 'Monaco'
HELVETICAFONT = 'Helvetica'
LUCIDAGRANDEFONT = 'Lucida Grande'


# This only works when we have a QtApp instance working; hence it need to go somewhere else.
#from ccpn.framework.PathsAndUrls import fontsPath
#QtGui.QFontDatabase.addApplicationFont(os.path.join(fontsPath, 'open-sans/OpenSans-Regular.ttf'))


def _readFontFromPreferences(fontRequest, preferences):
    # read font name from the preferences file
    fontName = preferences.general.get(fontRequest) or SYSTEMFONTREQUEST
    return fontName


class Font(QtGui.QFont):

    def __init__(self, fontName, size, bold=False, italic=False, underline=False, strikeout=False):
        """
        Initialise the font fontName
        :param fontName: font name
        :param size: size of font
        :param bold (optional): make font bold
        :param italic (optional):make fint italic

         to retrieve:
         self.fontName -> fontName
         QFont methods:
         self.pointSize() -> size
         self.italic() -> italic
         self.bold() -> bold
        """

        QtGui.QFont.__init__(self, fontName, size)
        self.fontName = fontName
        self.setBold(bold)
        self.setItalic(italic)
        self.setUnderline(underline)
        self.setStrikeOut(strikeout)


def setWidgetFont(widget, name=DEFAULTFONT, size='MEDIUM', bold=False, italic=False):
    from ccpn.framework.Application import getApplication
    from ccpn.util.Logging import getLogger

    try:
        getApp = getApplication()
        font = getApp._fontSettings.getFont(name, size, bold, italic)
        widget.setFont(font)
    except:
        getLogger().debug('Cannot set font')


def getWidgetFontHeight(name=DEFAULTFONT, size='MEDIUM', bold=False, italic=False):
    from ccpn.framework.Application import getApplication
    from ccpn.util.Logging import getLogger

    try:
        getApp = getApplication()
        font = getApp._fontSettings.getFont(name, size, bold, italic)
        return QtGui.QFontMetrics(font).height()
    except:
        getLogger().debug('Cannot get font')


def getFontHeight(name=DEFAULTFONT, size='MEDIUM'):
    from ccpn.framework.Application import getApplication
    from ccpn.util.Logging import getLogger

    try:
        getApp = getApplication()
        font = getApp._fontSettings.getFont(name, size, False, False)
        return QtGui.QFontMetrics(font).height()
    except:
        getLogger().debug('Cannot get font')
