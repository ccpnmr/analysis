"""
Settings used in gui modules, widgets and popups

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
__dateModified__ = "$dateModified: 2020-03-17 00:13:56 +0000 (Tue, March 17, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2016-11-15 21:37:50 +0000 (Tue, 15 Nov 2016) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.Font import Font, HELVETICAFONTREQUEST, MONACOFONTREQUEST, LUCIDAGRANDEFONTREQUEST, _readFontFromPreferences
from ccpn.util.decorators import singleton
from ccpn.util.Logging import getLogger
from ccpn.util.Colour import allColours, hexToRgbRatio, autoCorrectHexColour, \
    spectrumHexDarkColours, spectrumHexLightColours, spectrumHexMediumColours, \
    spectrumHexDefaultLightColours, spectrumHexDefaultDarkColours, rgbRatioToHex


class fontSettings():

    def __init__(self, preferences):

        MONACOFONT = _readFontFromPreferences(MONACOFONTREQUEST, preferences)
        HELVETICAFONT = _readFontFromPreferences(HELVETICAFONTREQUEST, preferences)
        LUCIDAGRANDEFONT = _readFontFromPreferences(LUCIDAGRANDEFONTREQUEST, preferences)

        # fonts
        self.monaco12 = Font(MONACOFONT, 12)
        self.monaco16 = Font(MONACOFONT, 16)
        self.monaco20 = Font(MONACOFONT, 20)

        self.helvetica8 = Font(HELVETICAFONT, 8)
        self.helveticaItalic8 = Font(HELVETICAFONT, 8, italic=True)
        self.helveticaBold8 = Font(HELVETICAFONT, 8, bold=True)

        self.helvetica10 = Font(HELVETICAFONT, 10)
        self.helveticaItalic10 = Font(HELVETICAFONT, 10, italic=True)
        self.helveticaBold10 = Font(HELVETICAFONT, 10, bold=True)

        self.helvetica12 = Font(HELVETICAFONT, 12)
        self.helveticaItalic12 = Font(HELVETICAFONT, 12, italic=True)
        self.helveticaBold12 = Font(HELVETICAFONT, 12, bold=True)
        self.helveticaUnderline12 = Font(HELVETICAFONT, 12, underline=True)
        self.helveticaStrikeout12 = Font(HELVETICAFONT, 12, strikeout=True)

        self.helvetica14 = Font(HELVETICAFONT, 14)
        self.helveticaBold14 = Font(HELVETICAFONT, 14, bold=True)

        self.helvetica20 = Font(HELVETICAFONT, 20)
        self.helveticaBold20 = Font(HELVETICAFONT, 20, bold=True)

        self.helveticaBold36 = Font(HELVETICAFONT, 36, bold=True)

        self.lucidaGrande12 = Font(LUCIDAGRANDEFONT, 12)
        self.lucidaGrande14 = Font(LUCIDAGRANDEFONT, 14)

        # widgets and modules
        self.textFontTiny = self.helvetica8  # general text font
        self.textFontTinyBold = self.helveticaBold8  # general text font
        self.textFontSmall = self.helvetica10  # general text font
        self.textFontSmallBold = self.helveticaBold10  # general text font
        self.textFont = self.helvetica12  # general text font
        self.textFontBold = self.helveticaBold12  # general text font bold
        self.textFontLarge = self.helvetica14  # general text font large
        self.textFontLargeBold = self.helveticaBold14  # general text font large bold
        self.textFontHuge = self.helvetica20  # general text font huge
        self.textFontHugeBold = self.helveticaBold20  # general text font huge bold

        self.textFontTinySpacing = 7
        self.textFontSmallSpacing = 9
        self.textFontSpacing = 11
        self.textFontLargeSpacing = 13
        self.textFontHugeSpacing = 18

        self.fixedWidthFont = self.monaco12  # for TextEditor, ipythonconsole
        self.fixedWidthLargeFont = self.monaco16
        self.fixedWidthHugeFont = self.monaco20
        self.moduleLabelFont = self.helvetica12  # for text of left-label of modules
        self.sidebarFont = self.lucidaGrande12  # sidebar
        self.menuFont = self.lucidaGrande14  # Menus
        self.messageFont = self.helvetica14  # used in popup messages;
        self.messageFontBold = self.helveticaBold14  # used in popup messages;


# Colours
LIGHT = 'light'
DARK = 'dark'
DEFAULT = 'default'
MARKS_COLOURS = 'marksColours'
COLOUR_SCHEMES = (LIGHT, DARK, DEFAULT)

SPECTRUM_HEXCOLOURS = 'spectrumHexColours'
SPECTRUM_HEXDEFAULTCOLOURS = 'spectrumHexDefaultColours'
SPECTRUM_HEXMEDIUMCOLOURS = 'spectrumHexMediumColours'
SPECTRUMCOLOURS = 'spectrumColours'

MARK_LINE_COLOUR_DICT = {
    'CA'   : '#0080FF',  # aqua
    'CB'   : '#6666FF',  # orchid
    'CG'   : '#0048FF',
    'CD'   : '#006DFF',
    'CE'   : '#0091FF',
    'CZ'   : '#00B6FF',
    'CH'   : '#00DAFF',
    'C'    : '#00FFFF',
    'Cn'   : '#00FFFF',
    'HA'   : '#FF0000',
    'HB'   : '#FF0024',
    'HG'   : '#FF0048',
    'HD'   : '#FF006D',
    'HE'   : '#FF0091',
    'HZ'   : '#FF00B6',
    'HH'   : '#FF00DA',
    'H'    : '#FF00FF',
    'Hn'   : '#FF00FF',
    'N'    : '#00FF00',
    'Nh'   : '#00FF00',
    'ND'   : '#3FFF00',
    'NE'   : '#7FFF00',
    'NZ'   : '#BFFF00',
    'NH'   : '#FFFF00',
    DEFAULT: '#e0e0e0'
    }

# Widget definitions
CCPNMODULELABEL_FOREGROUND = 'CCPNMODULELABEL_FOREGROUND'
CCPNMODULELABEL_BACKGROUND = 'CCPNMODULELABEL_BACKGROUND'
CCPNMODULELABEL_BORDER = 'CCPNMODULELABEL_BORDER'
CCPNMODULELABEL_FOREGROUND_ACTIVE = 'CCPNMODULELABEL_FOREGROUND_ACTIVE'
CCPNMODULELABEL_BACKGROUND_ACTIVE = 'CCPNMODULELABEL_BACKGROUND_ACTIVE'
CCPNMODULELABEL_BORDER_ACTIVE = 'CCPNMODULELABEL_BORDER_ACTIVE'

# Spectrum GL base class
CCPNGLWIDGET_HEXFOREGROUND = 'CCPNGLWIDGET_HEXFOREGROUND'
CCPNGLWIDGET_HEXBACKGROUND = 'CCPNGLWIDGET_HEXBACKGROUND'
CCPNGLWIDGET_HEXHIGHLIGHT = 'CCPNGLWIDGET_HEXHIGHLIGHT'
CCPNGLWIDGET_FOREGROUND = 'CCPNGLWIDGET_FOREGROUND'
CCPNGLWIDGET_BACKGROUND = 'CCPNGLWIDGET_BACKGROUND'

CCPNGLWIDGET_PICKCOLOUR = 'CCPNGLWIDGET_PICKCOLOUR'
CCPNGLWIDGET_GRID = 'CCPNGLWIDGET_GRID'
CCPNGLWIDGET_HIGHLIGHT = 'CCPNGLWIDGET_HIGHLIGHT'
CCPNGLWIDGET_LABELLING = 'CCPNGLWIDGET_LABELLING'
CCPNGLWIDGET_PHASETRACE = 'CCPNGLWIDGET_PHASETRACE'
CCPNGLWIDGET_MULTIPLETLINK = 'CCPNGLWIDGET_MULTIPLETLINK'

CCPNGLWIDGET_ZOOMAREA = 'CCPNGLWIDGET_ZOOMAREA'
CCPNGLWIDGET_PICKAREA = 'CCPNGLWIDGET_PICKAREA'
CCPNGLWIDGET_SELECTAREA = 'CCPNGLWIDGET_SELECTAREA'
CCPNGLWIDGET_ZOOMLINE = 'CCPNGLWIDGET_ZOOMLINE'
CCPNGLWIDGET_MOUSEMOVELINE = 'CCPNGLWIDGET_MOUSEMOVELINE'
CCPNGLWIDGET_HARDSHADE = 0.9

GUICHAINLABEL_TEXT = 'GUICHAINLABEL_TEXT'

GUICHAINRESIDUE_UNASSIGNED = 'GUICHAINRESIDUE_UNASSIGNED'
GUICHAINRESIDUE_ASSIGNED = 'GUICHAINRESIDUE_ASSIGNED'
GUICHAINRESIDUE_POSSIBLE = 'GUICHAINRESIDUE_POSSIBLE'
GUICHAINRESIDUE_WARNING = 'GUICHAINRESIDUE_WARNING'
GUICHAINRESIDUE_DRAGENTER = 'GUICHAINRESIDUE_DRAGENTER'
GUICHAINRESIDUE_DRAGLEAVE = 'GUICHAINRESIDUE_DRAGLEAVE'

GUINMRATOM_SELECTED = 'GUINMRATOM_SELECTED'
GUINMRATOM_NOTSELECTED = 'GUINMRATOM_NOTSELECTED'

GUINMRRESIDUE = 'GUINMRRESIDUE'

GUISTRIP_PIVOT = 'GUISTRIP_PIVOT'

LABEL_FOREGROUND = 'LABEL_FOREGROUND'
LABEL_BACKGROUND = 'LABEL_BACKGROUND'
LABEL_SELECTEDBACKGROUND = 'LABEL_SELECTEDBACKGROUND'
LABEL_SELECTEDFOREGROUND = 'LABEL_SELECTEDFOREGROUND'
LABEL_HIGHLIGHT = 'LABEL_HIGHLIGHT'
DIVIDER = 'DIVIDER'
SOFTDIVIDER = 'SOFTDIVIDER'

SEQUENCEGRAPHMODULE_LINE = 'SEQUENCEGRAPHMODULE_LINE'
SEQUENCEGRAPHMODULE_TEXT = 'SEQUENCEGRAPHMODULE_TEXT'

SEQUENCEMODULE_DRAGMOVE = 'SEQUENCEMODULE_DRAGMOVE'
SEQUENCEMODULE_TEXT = 'SEQUENCEMODULE_TEXT'

# used in GuiTable stylesheet (cannot change definition)
GUITABLE_BACKGROUND = 'GUITABLE_BACKGROUND'
GUITABLE_ALT_BACKGROUND = 'GUITABLE_ALT_BACKGROUND'
GUITABLE_ITEM_FOREGROUND = 'GUITABLE_ITEM_FOREGROUND'
GUITABLE_SELECTED_FOREGROUND = 'GUITABLE_SELECTED_FOREGROUND'
GUITABLE_SELECTED_BACKGROUND = 'GUITABLE_SELECTED_BACKGROUND'

# strip header colours
STRIPHEADER_FOREGROUND = 'STRIPHEADER_FOREGROUND'
STRIPHEADER_BACKGROUND = 'STRIPHEADER_BACKGROUND'

# border for focus/noFocus - QPlainTextEdit
BORDERNOFOCUS = 'BORDER_NOFOCUS'
BORDERFOCUS = 'BORDER_FOCUS'

# Colours
TEXT_COLOUR = '#555D85'
SOFT_DIVIDER_COLOUR = '#888DA5'
LIGHT_GREY = 'rgb(250,250,250)'
STEEL = 'rgb(102,102,102)'  # from apple
MARISHINO = '#004D81'  # rgb(0,77,129) ; red colour (from apple)
MEDIUM_BLUE = '#7777FF'
GREEN1 = '#009a00'
WARNING_RED = '#e01010'
FIREBRICK = hexToRgbRatio([k for k, v in allColours.items() if v == 'firebrick'][0])
LIGHTCORAL = hexToRgbRatio([k for k, v in allColours.items() if v == 'lightcoral'][0])

BORDERNOFOCUS_COLOUR = '#A9A9A9'
BORDERFOCUS_COLOUR = '#4E86F6'

# Shades
CCPNGLWIDGET_REGIONSHADE = 0.30
CCPNGLWIDGET_INTEGRALSHADE = 0.1

# Colour schemes definitions
colourSchemes = {
    # all colours defined here
    DEFAULT: {

        CCPNGLWIDGET_HEXFOREGROUND       : '#070707',
        CCPNGLWIDGET_HEXBACKGROUND       : '#FFFFFF',
        CCPNGLWIDGET_HEXHIGHLIGHT        : rgbRatioToHex(0.23, 0.23, 1.0),

        CCPNGLWIDGET_FOREGROUND          : (0.05, 0.05, 0.05, 1.0),  #'#080000'
        CCPNGLWIDGET_BACKGROUND          : (1.0, 1.0, 1.0, 1.0),

        CCPNGLWIDGET_PICKCOLOUR          : (0.2, 0.5, 0.9, 1.0),
        CCPNGLWIDGET_GRID                : (0.5, 0.0, 0.0, 1.0),  #'#080000'
        CCPNGLWIDGET_HIGHLIGHT           : (0.23, 0.23, 1.0, 1.0),  #'#3333ff'
        CCPNGLWIDGET_LABELLING           : (0.05, 0.05, 0.05, 1.0),
        CCPNGLWIDGET_PHASETRACE          : (0.2, 0.2, 0.2, 1.0),
        CCPNGLWIDGET_ZOOMAREA            : (0.8, 0.9, 0.2, 0.3),
        CCPNGLWIDGET_PICKAREA            : (0.2, 0.5, 0.9, 0.3),
        CCPNGLWIDGET_SELECTAREA          : (0.8, 0.2, 0.9, 0.3),
        CCPNGLWIDGET_ZOOMLINE            : (0.6, 0.7, 0.2, 1.0),
        CCPNGLWIDGET_MOUSEMOVELINE       : (0.8, 0.2, 0.9, 1.0),

        CCPNGLWIDGET_MULTIPLETLINK       : FIREBRICK,

        CCPNMODULELABEL_BACKGROUND       : '#5858C0',
        CCPNMODULELABEL_FOREGROUND       : '#E0E0E0',
        CCPNMODULELABEL_BORDER           : '#5858C0',
        CCPNMODULELABEL_BACKGROUND_ACTIVE: '#7080EE',
        CCPNMODULELABEL_FOREGROUND_ACTIVE: '#FFFFFF',
        CCPNMODULELABEL_BORDER_ACTIVE    : '#7080EE',

        GUICHAINLABEL_TEXT               : TEXT_COLOUR,

        GUICHAINRESIDUE_UNASSIGNED       : 'black',
        GUICHAINRESIDUE_ASSIGNED         : GREEN1,
        GUICHAINRESIDUE_POSSIBLE         : 'orange',
        GUICHAINRESIDUE_WARNING          : WARNING_RED,
        GUICHAINRESIDUE_DRAGENTER        : MARISHINO,
        GUICHAINRESIDUE_DRAGLEAVE        : 'black',  # '#666e98',

        GUINMRATOM_SELECTED              : TEXT_COLOUR,
        GUINMRATOM_NOTSELECTED           : '#FDFDFC',

        GUINMRRESIDUE                    : TEXT_COLOUR,

        GUISTRIP_PIVOT                   : MARISHINO,

        LABEL_FOREGROUND                 : TEXT_COLOUR,
        DIVIDER                          : '#a9a9a9',  # could be could CCPN_WIDGET_BORDER_COLOUR, was TEXT_COLOUR
        SOFTDIVIDER                      : SOFT_DIVIDER_COLOUR,
        LABEL_SELECTEDBACKGROUND         : 'mediumseagreen',
        LABEL_SELECTEDFOREGROUND         : 'black',
        LABEL_HIGHLIGHT                  : 'palegreen',

        SEQUENCEGRAPHMODULE_LINE         : 'black',
        SEQUENCEGRAPHMODULE_TEXT         : TEXT_COLOUR,

        SEQUENCEMODULE_DRAGMOVE          : MEDIUM_BLUE,
        SEQUENCEMODULE_TEXT              : TEXT_COLOUR,

        GUITABLE_BACKGROUND              : 'white',
        GUITABLE_ALT_BACKGROUND          : LIGHT_GREY,
        GUITABLE_ITEM_FOREGROUND         : TEXT_COLOUR,
        GUITABLE_SELECTED_FOREGROUND     : 'black',
        GUITABLE_SELECTED_BACKGROUND     : '#FFFCBA',

        STRIPHEADER_FOREGROUND           : TEXT_COLOUR,
        STRIPHEADER_BACKGROUND           : '#ebebeb',

        BORDERFOCUS                      : BORDERFOCUS_COLOUR,
        BORDERNOFOCUS                    : BORDERNOFOCUS_COLOUR,

        MARKS_COLOURS                    : MARK_LINE_COLOUR_DICT,
        SPECTRUM_HEXCOLOURS              : spectrumHexDarkColours,
        SPECTRUM_HEXMEDIUMCOLOURS        : spectrumHexMediumColours,
        SPECTRUM_HEXDEFAULTCOLOURS       : spectrumHexDefaultDarkColours,
        },

    # Overridden for dark colour scheme
    DARK   : {

        CCPNGLWIDGET_HEXFOREGROUND: '#F0FFFF',
        CCPNGLWIDGET_HEXBACKGROUND: '#0F0F0F',
        CCPNGLWIDGET_HEXHIGHLIGHT : rgbRatioToHex(0.2, 1.0, 0.3),

        CCPNGLWIDGET_FOREGROUND   : (0.9, 1.0, 1.0, 1.0),  #'#f0ffff'
        CCPNGLWIDGET_BACKGROUND   : (0.1, 0.1, 0.1, 1.0),

        CCPNGLWIDGET_PICKCOLOUR   : (0.2, 0.5, 0.9, 1.0),
        CCPNGLWIDGET_GRID         : (0.9, 1.0, 1.0, 1.0),  #'#f7ffff'
        CCPNGLWIDGET_HIGHLIGHT    : (0.2, 1.0, 0.3, 1.0),  #'#00ff00'
        CCPNGLWIDGET_LABELLING    : (1.0, 1.0, 1.0, 1.0),
        CCPNGLWIDGET_PHASETRACE   : (0.8, 0.8, 0.8, 1.0),
        CCPNGLWIDGET_ZOOMLINE     : (1.0, 0.9, 0.2, 1.0),
        CCPNGLWIDGET_MULTIPLETLINK: LIGHTCORAL,

        SPECTRUM_HEXCOLOURS       : spectrumHexLightColours,
        SPECTRUM_HEXMEDIUMCOLOURS : spectrumHexMediumColours,
        SPECTRUM_HEXDEFAULTCOLOURS: spectrumHexDefaultLightColours,

        LABEL_SELECTEDBACKGROUND  : 'mediumseagreen',
        LABEL_SELECTEDFOREGROUND  : 'black',
        LABEL_HIGHLIGHT           : 'palegreen',
        },

    # Overridden for light colour scheme
    LIGHT  : {

        }
    }

# adjust the default marks for the light/dark colour schemes
MARK_LINE_COLOUR_DICT_LIGHT = dict([(k, autoCorrectHexColour(v, colourSchemes[DEFAULT][CCPNGLWIDGET_HEXBACKGROUND],
                                                             addNewColour=False)) for k, v in MARK_LINE_COLOUR_DICT.items()])
MARK_LINE_COLOUR_DICT_DARK = dict([(k, autoCorrectHexColour(v, colourSchemes[DARK][CCPNGLWIDGET_HEXBACKGROUND],
                                                            addNewColour=False)) for k, v in MARK_LINE_COLOUR_DICT.items()])

# insert the marks colours into colourScheme
colourSchemes[LIGHT][MARKS_COLOURS] = MARK_LINE_COLOUR_DICT_LIGHT
colourSchemes[DARK][MARKS_COLOURS] = MARK_LINE_COLOUR_DICT_DARK


def getColourScheme():
    """
    :return: colourScheme
    """
    app = QtCore.QCoreApplication.instance()
    if hasattr(app, '_ccpnApplication'):
        application = getattr(app, '_ccpnApplication')
        colourScheme = application.colourScheme
        if colourScheme not in COLOUR_SCHEMES:
            raise RuntimeError('Undefined colour scheme')
            return DEFAULT
        return colourScheme
    # for now to make the tests run
    else:
        return DEFAULT


def setColourScheme(colourScheme):
    """set the current colourScheme
    """
    app = QtCore.QCoreApplication.instance()
    if hasattr(app, '_ccpnApplication'):
        application = getattr(app, '_ccpnApplication')
        # colourScheme = application.colourScheme
        if colourScheme not in COLOUR_SCHEMES:
            raise RuntimeError('Undefined colour scheme')

        application.colourScheme = colourScheme
        ColourDict(colourScheme).setColourScheme(colourScheme)


@singleton
class ColourDict(dict):
    """
    Singleton Class to store colours;
    """

    def __init__(self, colourScheme=None):
        super(dict, self).__init__()
        # assure always default values
        self.setColourScheme(DEFAULT)
        if colourScheme is not None:
            self.setColourScheme(colourScheme)
        else:
            self.setColourScheme(getColourScheme())

    def setColourScheme(self, colourScheme):
        if colourScheme in COLOUR_SCHEMES:
            self.update(colourSchemes[DEFAULT])
            self.update(colourSchemes[colourScheme])
            self.colourScheme = colourScheme
        else:
            getLogger().warning('undefined colourScheme "%s", retained "%s"' % (colourScheme, self.colourScheme))


#end class


def getColours():
    """
    Return colour for the different schemes
    :return: colourDict
    """
    colourScheme = getColourScheme()
    colourDict = ColourDict(colourScheme)
    return colourDict
