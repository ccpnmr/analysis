"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-11-09 18:44:04 +0000 (Wed, November 09, 2022) $"
__version__ = "$Revision: 3.1.0 $"
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
from ccpn.framework.Application import getApplication
from ccpn.util.Logging import getLogger


DEFAULTFONT = 'defaultFont'
CONSOLEFONT = 'fixedFont'
SIDEBARFONT = 'sidebarFont'
TABLEFONT = 'tableFont'
SEQUENCEGRAPHFONT = 'sequenceGraphFont'
DEFAULTFONTNAME = 'Helvetica'
DEFAULTFONTSIZE = 12
DEFAULTFONTREGULAR = 'Regular'


# This only works when we have a QtApp instance working; hence it needs to go somewhere else.
#from ccpn.framework.PathsAndUrls import fontsPath
#QtGui.QFontDatabase.addApplicationFont(os.path.join(fontsPath, 'open-sans/OpenSans-Regular.ttf'))


def _readFontFromAppearances(fontRequest, preferences):
    # read font name from the preferences file
    return preferences.appearance.get(fontRequest)


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
    """Set the font in the specified widget
    """
    try:
        getApp = getApplication()
        font = getApp._fontSettings.getFont(name, size, bold, italic)
        widget.setFont(font)

    except Exception:
        getLogger().debug('setWidgetFont: Cannot set font')


def getWidgetFontHeight(name=DEFAULTFONT, size='MEDIUM', bold=False, italic=False):
    """Get the font height form the specified font
    """
    try:
        getApp = getApplication()
        font = getApp._fontSettings.getFont(name, size, bold, italic)
        return QtGui.QFontMetrics(font).height()

    except Exception:
        getLogger().debug(f'getWidgetFontHeight: Cannot get font, returning default {DEFAULTFONTSIZE}pt')
        return DEFAULTFONTSIZE


def getFontHeight(name=DEFAULTFONT, size='MEDIUM'):
    """Get the font height form the specified font
    """
    try:
        getApp = getApplication()
        font = getApp._fontSettings.getFont(name, size, False, False)
        return QtGui.QFontMetrics(font).height()

    except Exception:
        getLogger().debug(f'getFontHeight: Cannot get font, returning default {DEFAULTFONTSIZE}pt')
        return DEFAULTFONTSIZE


def getFont(name=DEFAULTFONT, size='MEDIUM'):
    """Get the specified font from the fonts dict
    """
    try:
        getApp = getApplication()
        return getApp._fontSettings.getFont(name, size, False, False)

    except Exception:
        getLogger().debug(f'getFont: Cannot get font, returning default font {DEFAULTFONTNAME}')
        return Font(DEFAULTFONTNAME, DEFAULTFONTSIZE)


def getTextDimensionsFromFont(name=DEFAULTFONT, size='MEDIUM', bold=False, italic=False, textList=None):
    """Get the bounding box for the specified text
    """
    try:
        getApp = getApplication()
        font = getApp._fontSettings.getFont(name, size, bold, italic)

    except Exception:
        getLogger().debug(f'getTextDimensionsFromFont: Cannot get font, returning default {DEFAULTFONTSIZE}pt')
        font = Font(DEFAULTFONTNAME, DEFAULTFONTSIZE)

    fontMetrics = QtGui.QFontMetrics(font, )

    if textList and isinstance(textList, (list, tuple)):
        wPoints = []
        hPoints = []

        for text in textList:
            # best estimate for the width of the text, plus a lit extra
            bRect = fontMetrics.boundingRect(f'{text}__')
            wPoints.append(bRect.width())
            hPoints.append(bRect.height())

        minDimensions = QtCore.QSize(np.min(wPoints), np.min(hPoints))
        maxDimensions = QtCore.QSize(np.max(wPoints), np.max(hPoints))
        return minDimensions, maxDimensions

    getLogger().debug('getTextDimensionsFromFont: textList is empty or undefined')
    return QtCore.QSize(0, 0), QtCore.QSize(0, 0)
