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
__dateModified__ = "$dateModified: 2022-12-12 17:50:30 +0000 (Mon, December 12, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-16 18:20:01 +0000 (Thu, March 16, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import numpy as np
import glob
from PyQt5 import QtGui, QtCore
from ccpn.framework.Application import getApplication
# from ccpn.framework.PathsAndUrls import fontsPath
from ccpn.util.decorators import singleton
from ccpn.util.Logging import getLogger
from ccpn.util.Common import isLinux, isMacOS, isWindowsOS
from ccpn.util.Path import aPath


DEFAULTFONT = 'defaultFont'
CONSOLEFONT = 'fixedFont'
SIDEBARFONT = 'sidebarFont'
TABLEFONT = 'tableFont'
SEQUENCEGRAPHFONT = 'sequenceGraphFont'
DEFAULTFONTNAME = 'Helvetica'
DEFAULTFONTSIZE = 12
DEFAULTFONTREGULAR = 'Regular'

WINDOWS_FONTPATHS = {"C:/Windows/Fonts"}
MACOS_FONTPATHS = {"/System/Library/Fonts"}
LINUX_FONTPATHS = {"~/.fonts", "~/.local/share/fonts", "/usr/local/share/fonts", "/usr/share/fonts"}


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


#=========================================================================================
# SystemFonts - singleton to hold the currently loaded fonts
#=========================================================================================


@singleton
class _SystemFonts():
    __slots__ = ['_unloadable', '_familyFonts', '_fontDb']
    """Class to hold the currently loaded system-fonts
    """

    def __init__(self):
        """Set up the system-font list/dict/database

        _unloadable is a list of the names of the unloadable fonts due to some error
        _familyFonts is a dict of the form {<name>: list[<path>, ...]}
        where <name> is the name of the font-family, and the list contains the paths of each .ttf file
        _fontDb is the QFontDatabase reference
        """
        # This only works when we have a QtApp instance working; hence it needs to go somewhere else.
        # QtGui.QFontDatabase.addApplicationFont(os.path.join(fontsPath, 'open-sans/OpenSans-Regular.ttf'))

        self._unloadable = []
        self._familyFonts = {}
        self._fontDb = None

        # load the available .ttf fonts - load everytime as user may move/add them
        self._loadFonts()

    def reloadFonts(self):
        """Reload all the system-fonts
        """
        # load the available .ttf fonts - reload as user may move/add them
        self._loadFonts()

    def _loadFonts(self):
        """Load all the system-fonts
        """
        unloadable, familyFonts = self._getFontPaths()

        # update the internal font-lists/dict
        self._unloadable[:] = unloadable
        self._familyFonts.clear()
        self._familyFonts.update(familyFonts)

    @property
    def fonts(self):
        """Return the currently loaded fonts
        """
        return self._familyFonts

    @property
    def fontDb(self):
        """Return the current font-database
        """
        return self._fontDb

    def _getFontPaths(self):
        """Read the system fonts from the OS-specific paths
        """
        font_paths = set(QtCore.QStandardPaths.standardLocations(QtCore.QStandardPaths.FontsLocation))

        if isWindowsOS():
            font_paths = list(font_paths | WINDOWS_FONTPATHS)
        elif isMacOS():
            font_paths = list(font_paths | MACOS_FONTPATHS)
        elif isLinux():
            font_paths = list(font_paths | LINUX_FONTPATHS)

        unloadable = []
        familyPath = {}

        self._fontDb = db = QtGui.QFontDatabase()
        for fpath in font_paths:
            # go through all font paths
            if aPath(fpath).is_dir():
                for filename in glob.glob(f'{fpath}/**/*.ttf', recursive=True):  # go through all files at each path
                    path = os.path.join(fpath, filename)
                    if not path.endswith('.ttf') or path.startswith('.'):
                        # only read the true-type fonts
                        continue

                    idx = db.addApplicationFont(path)  # add font path
                    if idx < 0:
                        unloadable.append(path)  # font wasn't loaded if idx is -1
                    else:
                        names = db.applicationFontFamilies(idx)  # load back font-family name
                        for n in names:
                            _paths = familyPath.setdefault(n, set())
                            _paths.add(path)

        return unloadable, familyPath


def getSystemFonts():
    """Return the currently loaded system-fonts
    """
    return _SystemFonts().fonts


def updateSystemFonts():
    """Reload system-fonts
    """
    _SystemFonts().reloadFonts()


def getSystemFont(name, style=None, pointSize=DEFAULTFONTSIZE):
    """Return the currently loaded system-font from the name
    """
    fnts = _SystemFonts()
    try:
        return fnts._fontDb.font(name, style, pointSize)
    except Exception:
        return fnts._fontDb.font(DEFAULTFONTNAME, None, DEFAULTFONTSIZE)
