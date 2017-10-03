"""
Settings used in gui modules, widgets and popups

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:41 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================

__author__ = "$Author: geertenv $"
__date__ = "$Date: 2016-11-15 21:37:50 +0000 (Tue, 15 Nov 2016) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.Font import Font

# fonts
monaco12              = Font('Monaco', 12)
monaco20              = Font('Monaco', 20)

helvetica10           = Font('Helvetica', 10)
helveticaItalic10     = Font('Helvetica', 10, italic=True)
helveticaBold10       = Font('Helvetica', 10, bold=True)

helvetica12           = Font('Helvetica', 12)
helveticaItalic12     = Font('Helvetica', 12, italic=True)
helveticaBold12       = Font('Helvetica', 12, bold=True)
helveticaUnderline12  = Font('Helvetica', 12, underline=True)
helveticaStrikeout12  = Font('Helvetica', 12, strikeout=True)

helvetica14           = Font('Helvetica', 14)
helveticaBold14       = Font('Helvetica', 14, bold=True)

helvetica20           = Font('Helvetica', 20)
helveticaBold20       = Font('Helvetica', 20, bold=True)

lucidaGrande12        = Font('Lucida Grande', 12)
lucidaGrande14        = Font('Lucida Grande', 14)

# widgets and modules
textFontSmall   = helvetica10        # general text font
textFont        = helvetica12        # general text font
textFontBold    = helveticaBold12    # general text font bold
textFontLarge   = helvetica14        # general text font large
textFontLargeBold = helveticaBold14  # general text font large bold
textFontHuge    = helvetica20        # general text font huge
textFontHugeBold = helveticaBold20   # general text font huge bold

fixedWidthFont  = monaco12           # for TextEditor, ipythonconsole
fixedWidthHugeFont = monaco20
moduleLabelFont = helvetica12        # for text of left-label of modules
sidebarFont     = lucidaGrande12     # sidebar
menuFont        = lucidaGrande14     # Menus
messageFont     = helvetica14        # use in popup messages; does not seem to affect the dialog on OSX

# Colours
LIGHT = 'light'
DARK = 'dark'
COLOUR_SCHEMES = (LIGHT, DARK)

MARK_LINE_COLOUR_DICT = {
  'CA': '#0000FF',
  'CB': '#0024FF',
  'CG': '#0048FF',
  'CD': '#006DFF',
  'CE': '#0091FF',
  'CZ': '#00B6FF',
  'CH': '#00DAFF',
  'C': '#00FFFF',
  'HA': '#FF0000',
  'HB': '#FF0024',
  'HG': '#FF0048',
  'HD': '#FF006D',
  'HE': '#FF0091',
  'HZ': '#FF00B6',
  'HH': '#FF00DA',
  'H': '#FF00FF',
  'N': '#00FF00',
  'ND': '#3FFF00',
  'NE': '#7FFF00',
  'NZ': '#BFFF00',
  'NH': '#FFFF00',
}

def getColourScheme():
  """
  :return: colourScheme
  """
  app = QtCore.QCoreApplication.instance()
  if hasattr(app,'_ccpnApplication'):
    application = getattr(app,'_ccpnApplication')
    colourScheme = application.colourScheme
    if colourScheme not in COLOUR_SCHEMES:
      raise RuntimeError('Undefined colour scheme')
    return colourScheme
  # for now to make the tests run
  else:
    return LIGHT


def getColours():
  """
  Return colour for the different schemes
  :return: colourDict
  """
  colourScheme = getColourScheme()
  colourDict = {}

  if colourScheme == DARK:
    textColour = '#f7ffff'
    colourDict['LabelFG'] = textColour
    colourDict['LabelBG'] = '#2a3358'

  elif colourScheme == LIGHT:
    textColour = '#555D85'
    colourDict['LabelFG'] = textColour
    colourDict['LabelBG'] = '#FBF4CC'

  else:
    raise RuntimeError('Undefined colour scheme')

  return colourDict
