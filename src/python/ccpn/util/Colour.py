"""Module Documentation here

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:57 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
"""Color specification"""

from collections import OrderedDict
from PyQt5 import QtGui, QtCore


def rgbaToHex(r, g, b, a=255):
    return '#' + ''.join([hex(x)[2:] for x in (r, g, b, a)])


def rgbToHex(r, g, b):
    return '#' + ''.join([hex(x)[2:] for x in (r, g, b)])


def hexToRgb(hex):
    hex = hex.lstrip('#')
    lv = len(hex)
    return tuple(int(hex[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def hexToRgbRatio(hex):
    hex = hex.lstrip('#')
    lv = len(hex)
    return tuple(float(int(hex[i:i + lv // 3], 16)) / 255 for i in range(0, lv, lv // 3))


def hexToRgba(hex):
    hex = hex.lstrip('#')
    lv = len(hex)
    cols = [int(hex[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)]
    return tuple(cols.append(1.0))


colourNameToHexDict = {
    'red': '#ff0000',
    'green': '#00ff00',
    'blue': '#0000ff',
    'yellow': '#ffff00',
    'magenta': '#ff00ff',
    'cyan': '#ffff00',
}

spectrumColours = OrderedDict([('#cb1400', 'red'),
                               ('#860700', 'dark red'),
                               ('#933355', 'burgundy'),
                               ('#947676', 'bazaar'),

                               ('#d231cb', 'pink'),
                               ('#df2950', 'pastel pink'),
                               ('#f9609c', 'mid pink'),
                               ('#ff8eff', 'light pink'),
                               ('#f9609c', 'mid pink'),

                               ('#d24c23', 'dark orange'),
                               ('#fe6c11', 'orange'),
                               ('#ff932e', 'light pastel orange'),
                               ('#ecfc00', 'yellow'),
                               ('#ffff5a', 'light yellow'),

                               ('#50ae56', 'mid green'),
                               ('#3fe945', 'light green'),
                               ('#097a27', 'pastel green'),
                               ('#064a1a', 'dark green'),
                               ('#80ff00', 'chartreuse'),

                               ('#1530ff', 'blue'),
                               ('#1020aa', 'dark blue'),
                               ('#4080ff', 'light blue'),
                               ('#318290', 'pastel blue'),
                               ('#2d5175', 'mid blue'),
                               ('#4f9caa', 'light pastel blue'),
                               ('#957eff', 'heliotrope'),

                               ('#2f2373', 'dark purple'),
                               ('#5846d6', 'purple'),
                               ('#7866f8', 'light purple'),
                               ('#d8e1cf', 'light seashell'),

                               ('#3a4e5c', 'dark grey'),
                               ('#7a7a7a', 'mid grey'),
                               ('#b0b0b0', 'light grey'),

                               ('#ffffff', 'white'),
                               ('#000000', 'black')])

allColours = OrderedDict([('#F0F8FF', 'aliceblue'),
                          ('#FAEBD7', 'antiquewhite'),
                          ('#00FFFF', 'aqua'),
                          ('#7FFFD4', 'aquamarine'),
                          ('#F0FFFF', 'azure'),
                          ('#F5F5DC', 'beige'),
                          ('#FFE4C4', 'bisque'),
                          ('#000000', 'black'),
                          ('#FFEBCD', 'blanchedalmond'),
                          ('#0000FF', 'blue'),
                          ('#8A2BE2', 'blueviolet'),
                          ('#A52A2A', 'brown'),
                          ('#DEB887', 'burlywood'),
                          ('#5F9EA0', 'cadetblue'),
                          ('#7FFF00', 'chartreuse'),
                          ('#D2691E', 'chocolate'),
                          ('#FF7F50', 'coral'),
                          ('#6495ED', 'cornflowerblue'),
                          ('#FFF8DC', 'cornsilk'),
                          ('#DC143C', 'crimson'),
                          ('#00FFFF', 'cyan'),
                          ('#00008B', 'darkblue'),
                          ('#008B8B', 'darkcyan'),
                          ('#B8860B', 'darkgoldenrod'),
                          ('#A9A9A9', 'darkgray'),
                          ('#006400', 'darkgreen'),
                          ('#BDB76B', 'darkkhaki'),
                          ('#8B008B', 'darkmagenta'),
                          ('#556B2F', 'darkolivegreen'),
                          ('#FF8C00', 'darkorange'),
                          ('#9932CC', 'darkorchid'),
                          ('#8B0000', 'darkred'),
                          ('#E9967A', 'darksalmon'),
                          ('#8FBC8F', 'darkseagreen'),
                          ('#483D8B', 'darkslateblue'),
                          ('#2F4F4F', 'darkslategray'),
                          ('#00CED1', 'darkturquoise'),
                          ('#9400D3', 'darkviolet'),
                          ('#FF1493', 'deeppink'),
                          ('#00BFFF', 'deepskyblue'),
                          ('#696969', 'dimgray'),
                          ('#1E90FF', 'dodgerblue'),
                          ('#B22222', 'firebrick'),
                          ('#FFFAF0', 'floralwhite'),
                          ('#228B22', 'forestgreen'),
                          ('#FF00FF', 'fuchsia'),
                          ('#DCDCDC', 'gainsboro'),
                          ('#F8F8FF', 'ghostwhite'),
                          ('#FFD700', 'gold'),
                          ('#DAA520', 'goldenrod'),
                          ('#808080', 'gray'),
                          ('#008000', 'green'),
                          ('#ADFF2F', 'greenyellow'),
                          ('#F0FFF0', 'honeydew'),
                          ('#FF69B4', 'hotpink'),
                          ('#CD5C5C', 'indianred'),
                          ('#4B0082', 'indigo'),
                          ('#FFFFF0', 'ivory'),
                          ('#F0E68C', 'khaki'),
                          ('#E6E6FA', 'lavender'),
                          ('#FFF0F5', 'lavenderblush'),
                          ('#7CFC00', 'lawngreen'),
                          ('#FFFACD', 'lemonchiffon'),
                          ('#ADD8E6', 'lightblue'),
                          ('#F08080', 'lightcoral'),
                          ('#E0FFFF', 'lightcyan'),
                          ('#FAFAD2', 'lightgoldenrodyellow'),
                          ('#90EE90', 'lightgreen'),
                          ('#D3D3D3', 'lightgray'),
                          ('#FFB6C1', 'lightpink'),
                          ('#FFA07A', 'lightsalmon'),
                          ('#20B2AA', 'lightseagreen'),
                          ('#87CEFA', 'lightskyblue'),
                          ('#778899', 'lightslategray'),
                          ('#B0C4DE', 'lightsteelblue'),
                          ('#FFFFE0', 'lightyellow'),
                          ('#00FF00', 'lime'),
                          ('#32CD32', 'limegreen'),
                          ('#FAF0E6', 'linen'),
                          ('#FF00FF', 'magenta'),
                          ('#800000', 'maroon'),
                          ('#66CDAA', 'mediumaquamarine'),
                          ('#0000CD', 'mediumblue'),
                          ('#BA55D3', 'mediumorchid'),
                          ('#9370DB', 'mediumpurple'),
                          ('#3CB371', 'mediumseagreen'),
                          ('#7B68EE', 'mediumslateblue'),
                          ('#00FA9A', 'mediumspringgreen'),
                          ('#48D1CC', 'mediumturquoise'),
                          ('#C71585', 'mediumvioletred'),
                          ('#191970', 'midnightblue'),
                          ('#F5FFFA', 'mintcream'),
                          ('#FFE4E1', 'mistyrose'),
                          ('#FFE4B5', 'moccasin'),
                          ('#FFDEAD', 'navajowhite'),
                          ('#000080', 'navy'),
                          ('#FDF5E6', 'oldlace'),
                          ('#808000', 'olive'),
                          ('#6B8E23', 'olivedrab'),
                          ('#FFA500', 'orange'),
                          ('#FF4500', 'orangered'),
                          ('#DA70D6', 'orchid'),
                          ('#EEE8AA', 'palegoldenrod'),
                          ('#98FB98', 'palegreen'),
                          ('#AFEEEE', 'paleturquoise'),
                          ('#DB7093', 'palevioletred'),
                          ('#FFEFD5', 'papayawhip'),
                          ('#FFDAB9', 'peachpuff'),
                          ('#CD853F', 'peru'),
                          ('#FFC0CB', 'pink'),
                          ('#DDA0DD', 'plum'),
                          ('#B0E0E6', 'powderblue'),
                          ('#800080', 'purple'),
                          ('#FF0000', 'red'),
                          ('#BC8F8F', 'rosybrown'),
                          ('#4169E1', 'royalblue'),
                          ('#8B4513', 'saddlebrown'),
                          ('#FA8072', 'salmon'),
                          ('#FAA460', 'sandybrown'),
                          ('#2E8B57', 'seagreen'),
                          ('#FFF5EE', 'seashell'),
                          ('#A0522D', 'sienna'),
                          ('#C0C0C0', 'silver'),
                          ('#87CEEB', 'skyblue'),
                          ('#6A5ACD', 'slateblue'),
                          ('#708090', 'slategray'),
                          ('#FFFAFA', 'snow'),
                          ('#00FF7F', 'springgreen'),
                          ('#4682B4', 'steelblue'),
                          ('#D2B48C', 'tan'),
                          ('#008080', 'teal'),
                          ('#D8BFD8', 'thistle'),
                          ('#FF6347', 'tomato'),
                          ('#40E0D0', 'turquoise'),
                          ('#EE82EE', 'violet'),
                          ('#F5DEB3', 'wheat'),
                          ('#FFFFFF', 'white'),
                          ('#F5F5F5', 'whitesmoke'),
                          ('#FFFF00', 'yellow'),
                          ('#9ACD32', 'yellowgreen')
                          ])

spectrumHexColours = tuple(ky for ky in spectrumColours.keys() if ky != '#')


# Note that Colour strings are not re-used

class Colour(str):
    """ A class to make colour manipulation easier and more transparent.
        Assumes that r, g, b values are 8-bit so between 0 and 255 and have optional a.

    >>> c = Colour('magenta')
    >>> c = Colour('#ff00ff')
    >>> c = Colour((255, 0, 255))
    """

    def __init__(self, value):
        """ value can be name or #rrggbb or #rrggbbaa or (r, g, b) or (r, g, b, a) tuple/list """
        # print(value, 'color init')
        if not value:
            raise Exception('not allowed blank colour')

        if isinstance(value, str):
            value = value.lower()
            name = value
            if value[0] != '#':
                value = colourNameToHexDict[name]

            assert len(value) in (7, 9), 'len(value) = %d, should be 7 or 9' % len(value)

            r = int(value[1:3], 16)
            g = int(value[3:5], 16)
            b = int(value[5:7], 16)
            a = int(value[7:9], 16) if len(value) == 9 else 255
        else:
            assert isinstance(value, list) or isinstance(value,
                                                         tuple), 'value must be list or tuple if it is not a string, was %s' % (
                value,)
            assert len(value) in (3, 4), 'value=%s, len(value) = %d, should be 3 or 4' % (value, len(value))
            r, g, b = value[:3]
            if len(value) == 4:
                a = value[3]
                name = rgbaToHex(r, g, b, a)
            else:
                a = 255
                name = rgbToHex(r, g, b)

        ###str.__init__(self)
        self.r = r
        self.g = g
        self.b = b
        self.a = a
        self.name = name

    def rgba(self):
        """Returns 4-tuple of (r, g, b, a) where each one is in range 0 to 255"""

        return (self.r, self.g, self.b, self.a)

    def scaledRgba(self):
        """Returns 4-tuple of (r, g, b, a) where each one is in range 0.0 to 1.0"""

        return (self.r / 255.0, self.g / 255.0, self.b / 255.0, self.a / 255.0)

    def hex(self):

        return '#' + ''.join([hex(x)[2:] for x in (self.r, self.g, self.b)])

    def __repr__(self):

        return self.name

    def __str__(self):

        return self.__repr__()


def rgba(value):
    return Colour(value).rgba()


def scaledRgba(value):
    # print(value, 'scaledRgba')
    return Colour(value).scaledRgba()


def addNewColour(newColour):
    newIndex = str(len(spectrumColours.items()) + 1)
    spectrumColours[newColour.name()] = 'Colour %s' % newIndex


def addNewColourString(colourString):
    # '#' is reserved for auto colour so shouldn't ever be added
    if colourString != '#':
        newIndex = str(len(spectrumColours.items()) + 1)
        spectrumColours[colourString] = 'Colour %s' % newIndex


# def _setNewColour(colList, newCol:str):
#
#   # check if the colour is in the spectrumColours list
#
#   # check if colour is in you colList
#
#
#   pix = QtGui.QPixmap(QtCore.QSize(20, 20))
#   pix.fill(QtGui.QColor(newCol))
#
#   # add the new colour to the spectrumColours dict
#   newIndex = str(len(spectrumColours.items()) + 1)
#   # spectrumColours[newColour.name()] = 'Colour %s' % newIndex
#   addNewColourString(newCol)
#   if newCol not in colList.texts:
#     colList.addItem(icon=QtGui.QIcon(pix), text='Colour %s' % newIndex)
#     colList.setCurrentIndex(int(newIndex) - 1)

def selectPullDownColour(pulldown, colourString, allowAuto=False):
    try:
        pulldown.setCurrentText(spectrumColours[colourString])
    except:
        if allowAuto and '#' in pulldown.texts:
            pulldown.setCurrentText('#')


def fillColourPulldown(pulldown, allowAuto=False):
    currText = pulldown.currentText()
    # currIndex = pulldown.currentIndex()
    # print ('>>>', currText, currIndex)
    pulldown.clear()
    if allowAuto:
        pulldown.addItem(text='<auto>')
    for item in spectrumColours.items():
        # if item[1] not in pulldown.texts:
        if item[0] != '#':
            pix = QtGui.QPixmap(QtCore.QSize(20, 20))
            pix.fill(QtGui.QColor(item[0]))
            pulldown.addItem(icon=QtGui.QIcon(pix), text=item[1])
        elif allowAuto:
            pulldown.addItem(text=item[1])

    pulldown.setCurrentText(currText)


def getSpectrumColour(colourName, defaultReturn=None):
    """
    return the hex colour of the named colour
    """
    try:
        col = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourName)]
        return col
    except:
        # colour not found in the list
        return defaultReturn


def getAutoColourRgbRatio(inColour=None, sourceObject=None, colourAttribute=None, defaultColour=None):
    listColour = inColour
    if listColour == '#':
        listColour = getattr(sourceObject, colourAttribute, defaultColour)
    return hexToRgbRatio(listColour)
