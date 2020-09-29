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
__dateModified__ = "$dateModified: 2020-09-29 09:47:40 +0100 (Tue, September 29, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-16 18:20:01 +0000 (Thu, March 16, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from PyQt5 import QtGui, QtCore


DEFAULTFONT = 'defaultFont'
CONSOLEFONT = 'fixedFont'
SIDEBARFONT = 'sidebarFont'
TABLEFONT = 'tableFont'
DEFAULTFONTNAME = 'Helvetica'
DEFAULTFONTSIZE = 12
DEFAULTFONTREGULAR = 'Regular'


# This only works when we have a QtApp instance working; hence it need to go somewhere else.
#from ccpn.framework.PathsAndUrls import fontsPath
#QtGui.QFontDatabase.addApplicationFont(os.path.join(fontsPath, 'open-sans/OpenSans-Regular.ttf'))


def _readFontFromAppearances(fontRequest, preferences):
    # read font name from the preferences file
    fontName = preferences.appearance.get(fontRequest)
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
        getLogger().debug('Cannot get font, returning default {}pt'.format(DEFAULTFONTSIZE))
        return DEFAULTFONTSIZE


def getFontHeight(name=DEFAULTFONT, size='MEDIUM'):
    from ccpn.framework.Application import getApplication
    from ccpn.util.Logging import getLogger

    try:
        getApp = getApplication()
        font = getApp._fontSettings.getFont(name, size, False, False)
        return QtGui.QFontMetrics(font).height()
    except:
        getLogger().debug('Cannot get font, returning default {}pt'.format(DEFAULTFONTSIZE))
        return DEFAULTFONTSIZE


def getFont(name=DEFAULTFONT, size='MEDIUM'):
    from ccpn.framework.Application import getApplication
    from ccpn.util.Logging import getLogger

    try:
        getApp = getApplication()
        font = getApp._fontSettings.getFont(name, size, False, False)
        return font
    except:
        getLogger().debug('Cannot get font, returning default font'.format(DEFAULTFONTSIZE))
        return Font(DEFAULTFONTNAME, DEFAULTFONTSIZE)


def getTextDimensionsFromFont(name=DEFAULTFONT, size='MEDIUM', bold=False, italic=False, textList=None):
    from ccpn.framework.Application import getApplication
    from ccpn.util.Logging import getLogger

    try:
        getApp = getApplication()
        font = getApp._fontSettings.getFont(name, size, bold, italic)

    except:
        getLogger().debug('Cannot get font, returning default {}pt'.format(DEFAULTFONTSIZE))
        font = Font(DEFAULTFONTNAME, DEFAULTFONTSIZE)

    fontMetrics = QtGui.QFontMetrics(font, )
    wPoints = []
    hPoints = []

    for text in textList:
        # best estimate for the width of the text, plus a lit extra
        bRect = fontMetrics.boundingRect(text + '__')
        wPoints.append(bRect.width())
        hPoints.append(bRect.height())

    if textList:
        minDimensions = QtCore.QSize(np.min(wPoints), np.min(hPoints))
        maxDimensions = QtCore.QSize(np.max(wPoints), np.max(hPoints))
        return minDimensions, maxDimensions

    else:
        return QtCore.QSize(0, 0), QtCore.QSize(0, 0)
