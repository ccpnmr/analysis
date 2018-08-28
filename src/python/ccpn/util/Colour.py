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


def rgbaRatioToHex(r, g, b, a=1.0):
    return '#' + ''.join([hex(x)[2:] for x in (int(255.0 * r),
                                               int(255.0 * g),
                                               int(255.0 * b),
                                               int(255.0 * a))])


def rgbRatioToHex(r, g, b):
    return '#' + ''.join([hex(x)[2:] for x in (int(255.0 * r),
                                               int(255.0 * g),
                                               int(255.0 * b))])


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

allColours = OrderedDict([('#000000', 'black'),
                          ('#696969', 'dimgray'),
                          ('#696969', 'dimgrey'),
                          ('#808080', 'gray'),
                          ('#808080', 'grey'),
                          ('#A9A9A9', 'darkgray'),
                          ('#A9A9A9', 'darkgrey'),
                          ('#C0C0C0', 'silver'),
                          ('#D3D3D3', 'lightgray'),
                          ('#D3D3D3', 'lightgrey'),
                          ('#DCDCDC', 'gainsboro'),
                          ('#F5F5F5', 'whitesmoke'),
                          ('#FFFFFF', 'white'),
                          ('#FFFAFA', 'snow'),
                          ('#BC8F8F', 'rosybrown'),
                          ('#F08080', 'lightcoral'),
                          ('#CD5C5C', 'indianred'),
                          ('#A52A2A', 'brown'),
                          ('#B22222', 'firebrick'),
                          ('#800000', 'maroon'),
                          ('#8B0000', 'darkred'),
                          ('#FF0000', 'red'),
                          ('#FFE4E1', 'mistyrose'),
                          ('#FA8072', 'salmon'),
                          ('#FF6347', 'tomato'),
                          ('#E9967A', 'darksalmon'),
                          ('#FF7F50', 'coral'),
                          ('#FF4500', 'orangered'),
                          ('#FFA07A', 'lightsalmon'),
                          ('#A0522D', 'sienna'),
                          ('#FFF5EE', 'seashell'),
                          ('#D2691E', 'chocolate'),
                          ('#8B4513', 'saddlebrown'),
                          ('#F4A460', 'sandybrown'),
                          ('#FFDAB9', 'peachpuff'),
                          ('#CD853F', 'peru'),
                          ('#FAF0E6', 'linen'),
                          ('#FFE4C4', 'bisque'),
                          ('#FF8C00', 'darkorange'),
                          ('#DEB887', 'burlywood'),
                          ('#FAEBD7', 'antiquewhite'),
                          ('#D2B48C', 'tan'),
                          ('#FFDEAD', 'navajowhite'),
                          ('#FFEBCD', 'blanchedalmond'),
                          ('#FFEFD5', 'papayawhip'),
                          ('#FFE4B5', 'moccasin'),
                          ('#FFA500', 'orange'),
                          ('#F5DEB3', 'wheat'),
                          ('#FDF5E6', 'oldlace'),
                          ('#FFFAF0', 'floralwhite'),
                          ('#B8860B', 'darkgoldenrod'),
                          ('#DAA520', 'goldenrod'),
                          ('#FFF8DC', 'cornsilk'),
                          ('#FFD700', 'gold'),
                          ('#FFFACD', 'lemonchiffon'),
                          ('#F0E68C', 'khaki'),
                          ('#EEE8AA', 'palegoldenrod'),
                          ('#BDB76B', 'darkkhaki'),
                          ('#FFFFF0', 'ivory'),
                          ('#F5F5DC', 'beige'),
                          ('#FFFFE0', 'lightyellow'),
                          ('#FAFAD2', 'lightgoldenrodyellow'),
                          ('#808000', 'olive'),
                          ('#FFFF00', 'yellow'),
                          ('#6B8E23', 'olivedrab'),
                          ('#9ACD32', 'yellowgreen'),
                          ('#556B2F', 'darkolivegreen'),
                          ('#ADFF2F', 'greenyellow'),
                          ('#7FFF00', 'chartreuse'),
                          ('#7CFC00', 'lawngreen'),
                          ('#F0FFF0', 'honeydew'),
                          ('#8FBC8F', 'darkseagreen'),
                          ('#98FB98', 'palegreen'),
                          ('#90EE90', 'lightgreen'),
                          ('#228B22', 'forestgreen'),
                          ('#32CD32', 'limegreen'),
                          ('#006400', 'darkgreen'),
                          ('#008000', 'green'),
                          ('#00FF00', 'lime'),
                          ('#2E8B57', 'seagreen'),
                          ('#3CB371', 'mediumseagreen'),
                          ('#00FF7F', 'springgreen'),
                          ('#F5FFFA', 'mintcream'),
                          ('#00FA9A', 'mediumspringgreen'),
                          ('#66CDAA', 'mediumaquamarine'),
                          ('#7FFFD4', 'aquamarine'),
                          ('#40E0D0', 'turquoise'),
                          ('#20B2AA', 'lightseagreen'),
                          ('#48D1CC', 'mediumturquoise'),
                          ('#F0FFFF', 'azure'),
                          ('#E0FFFF', 'lightcyan'),
                          ('#AFEEEE', 'paleturquoise'),
                          ('#2F4F4F', 'darkslategray'),
                          ('#2F4F4F', 'darkslategrey'),
                          ('#008080', 'teal'),
                          ('#008B8B', 'darkcyan'),
                          ('#00FFFF', 'aqua'),
                          ('#00FFFF', 'cyan'),
                          ('#00CED1', 'darkturquoise'),
                          ('#5F9EA0', 'cadetblue'),
                          ('#B0E0E6', 'powderblue'),
                          ('#ADD8E6', 'lightblue'),
                          ('#00BFFF', 'deepskyblue'),
                          ('#87CEEB', 'skyblue'),
                          ('#87CEFA', 'lightskyblue'),
                          ('#4682B4', 'steelblue'),
                          ('#F0F8FF', 'aliceblue'),
                          ('#1E90FF', 'dodgerblue'),
                          ('#778899', 'lightslategray'),
                          ('#778899', 'lightslategrey'),
                          ('#708090', 'slategray'),
                          ('#708090', 'slategrey'),
                          ('#B0C4DE', 'lightsteelblue'),
                          ('#6495ED', 'cornflowerblue'),
                          ('#4169E1', 'royalblue'),
                          ('#F8F8FF', 'ghostwhite'),
                          ('#E6E6FA', 'lavender'),
                          ('#191970', 'midnightblue'),
                          ('#000080', 'navy'),
                          ('#00008B', 'darkblue'),
                          ('#0000CD', 'mediumblue'),
                          ('#0000FF', 'blue'),
                          ('#6A5ACD', 'slateblue'),
                          ('#483D8B', 'darkslateblue'),
                          ('#7B68EE', 'mediumslateblue'),
                          ('#9370DB', 'mediumpurple'),
                          ('#663399', 'rebeccapurple'),
                          ('#8A2BE2', 'blueviolet'),
                          ('#4B0082', 'indigo'),
                          ('#9932CC', 'darkorchid'),
                          ('#9400D3', 'darkviolet'),
                          ('#BA55D3', 'mediumorchid'),
                          ('#D8BFD8', 'thistle'),
                          ('#DDA0DD', 'plum'),
                          ('#EE82EE', 'violet'),
                          ('#800080', 'purple'),
                          ('#8B008B', 'darkmagenta'),
                          ('#FF00FF', 'fuchsia'),
                          ('#FF00FF', 'magenta'),
                          ('#DA70D6', 'orchid'),
                          ('#C71585', 'mediumvioletred'),
                          ('#FF1493', 'deeppink'),
                          ('#FF69B4', 'hotpink'),
                          ('#FFF0F5', 'lavenderblush'),
                          ('#DB7093', 'palevioletred'),
                          ('#DC143C', 'crimson'),
                          ('#FFC0CB', 'pink'),
                          ('#FFB6C1', 'lightpink')
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


if __name__ == '__main__':
    """Simple routine to plot all th enamed colors in the matplotlib colorspace
    """
    import matplotlib.pyplot as plt
    from matplotlib import colors as mcolors


    colors = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)

    # Sort colors by hue, saturation, value and name.
    by_hsv = sorted((tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name)
                    for name, color in colors.items())
    sorted_names = [name for hsv, name in by_hsv]

    n = len(sorted_names)
    ncols = 4
    nrows = n // ncols + 1

    # print the colors to generate full colorList
    for col in sorted_names:
        if isinstance(colors[col], str):
            print('(' + repr(colors[col]) + ', ' + repr(col) + '),')

    fig, ax = plt.subplots(figsize=(16, 9))

    # Get height and width
    X, Y = fig.get_dpi() * fig.get_size_inches()
    h = Y / (nrows + 1)
    w = X / ncols

    for i, name in enumerate(sorted_names):
        col = i % ncols
        row = i // ncols
        y = Y - (row * h) - h

        xi_line = w * (col + 0.05)
        xf_line = w * (col + 0.25)
        xi_text = w * (col + 0.3)

        ax.text(xi_text, y, name, fontsize=(h * 0.5),
                horizontalalignment='left',
                verticalalignment='center')

        ax.hlines(y + h * 0.1, xi_line, xf_line,
                  color=colors[name], linewidth=(h * 0.6))

    ax.set_xlim(0, X)
    ax.set_ylim(0, Y)
    ax.set_axis_off()

    fig.subplots_adjust(left=0, right=1,
                        top=1, bottom=0,
                        hspace=0, wspace=0)
    plt.show()
