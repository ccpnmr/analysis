"""Module Documentation here

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
__dateModified__ = "$dateModified: 2020-09-14 13:54:21 +0100 (Mon, September 14, 2020) $"
__version__ = "$Revision: 3.0.1 $"
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
import numpy as np


def _ccpnHex(val):
    """Generate hex value with padded leading zeroes
    """
    val = '{0:#0{1}x}'.format(int(val), 4)
    return '0x' + val[2:].upper()


def rgbaToHex(r, g, b, a=255):
    return '#' + ''.join([_ccpnHex(x)[2:] for x in (r, g, b, a)])


def rgbToHex(r, g, b):
    return '#' + ''.join([_ccpnHex(x)[2:] for x in (r, g, b)])


def rgbaRatioToHex(r, g, b, a=1.0):
    return '#' + ''.join([_ccpnHex(x)[2:] for x in (int(255.0 * r),
                                                    int(255.0 * g),
                                                    int(255.0 * b),
                                                    int(255.0 * a))])


def rgbRatioToHex(r, g, b):
    return '#' + ''.join([_ccpnHex(x)[2:] for x in (int(255.0 * r),
                                                    int(255.0 * g),
                                                    int(255.0 * b))])


def hexToRgb(hx):
    if not hx:
        pass

    hx = hx.lstrip('#')
    lv = len(hx)
    return tuple(int(hx[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def hexToRgbRatio(hx):
    if not hx:
        pass

    hx = hx.lstrip('#')
    lv = len(hx)
    return tuple(float(int(hx[i:i + lv // 3], 16)) / 255 for i in range(0, lv, lv // 3))


def hexToRgba(hx):
    if not hx:
        pass

    hx = hx.lstrip('#')
    lv = len(hx)
    cols = [int(hx[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)]
    return tuple(cols.append(1.0))


# sRGB luminance(Y) values
rY = 0.212655
gY = 0.715158
bY = 0.072187
COLOUR_LIGHT_THRESHOLD = 80
COLOUR_DARK_THRESHOLD = 190  #(256 - COLOUR_LIGHT_THRESHOLD)
COLOUR_THRESHOLD = 60


# Inverse of sRGB "gamma" function. (approx 2.2)
def inv_gam_sRGB(ic):
    c = ic / 255.0
    if (c <= 0.04045):
        return c / 12.92
    else:
        return pow(((c + 0.055) / (1.055)), 1.6)


# sRGB "gamma" function (approx 2.2)
def gam_sRGB(v):
    if (v <= 0.0031308):
        v *= 12.92
    else:
        v = 1.055 * pow(v, 0.625) - 0.055
    return int(v * 255)


# GRAY VALUE ("brightness")
def gray(r, g, b, a=1.0):
    return gam_sRGB(
            rY * inv_gam_sRGB(r) +
            gY * inv_gam_sRGB(g) +
            bY * inv_gam_sRGB(b)
            )


COLORMATRIX256CONST = [16.0, 128.0, 128.0]
COLORMATRIX256 = [[65.738, 129.057, 25.064],
                  [-37.945, -74.494, 112.439],
                  [112.439, -94.154, -18.285]]

COLORMATRIX256INVCONST = [-222.921, 135.576, -276.836]
COLORMATRIX256INV = [[298.082, 0.0, 408.583],
                     [298.082, -100.291, -208.120],
                     [298.082, 516.412, 0.0]]

# Y  = 0.299 R    + 0.587 G  + 0.114 B
# Cb = - 0.1687 R - 0.3313 G + 0.5 B     + 128
# Cr = 0.5 R      - 0.4187 G - 0.0813 B  + 128

COLORMATRIXJPEGCONST = [0, 128, 128]
COLORMATRIXJPEG = [[0.299, 0.587, 0.114],
                   [-0.168736, -0.331264, 0.5],
                   [0.5, -0.418688, -0.081312]]

# R = Y                    + 1.402 (Cr-128)
# G = Y - 0.34414 (Cb-128) - 0.71414 (Cr-128)
# B = Y + 1.772 (Cb-128)

COLORMATRIXJPEGINVCONST = [0, 0, 0]
COLORMATRIXJPEGINVOFFSET = [0, -128, -128]
COLORMATRIXJPEGINV = [[1.0, 0.0, 1.402],
                      [1.0, -0.344136, -0.714136],
                      [1.0, 1.772, 0.0]]


def colourNameNoSpace(name):
    """remove spaces from the colourname
    """
    return name  # currently no effect until sorted

    # return ''.join(name.split())


def colourNameWithSpace(name):
    """insert spaces into the colourname
    """

    # list of all possible words that are in the colour names
    nounList = ['dark', 'dim', 'medium', 'light', 'pale', 'white', 'rosy', 'indian', 'misty',
                'red', 'orange', 'burly', 'antique', 'navajo', 'blanched', 'papaya', 'floral',
                'lemon', 'olive', 'yellow', 'green', 'lawn', 'sea', 'forest', 'lime', 'spring',
                'slate', 'cadet', 'powder', 'sky', 'steel', 'royal', 'ghost', 'midnight', 'navy', 'rebecca', 'blue',
                'violet', 'deep', 'hot', 'lavender', 'cornflower', 'dodger', 'alice',
                'sandy', 'saddle'
                ]
    subsetNouns = ['goldenrod', 'golden', 'old']

    # insert spaces after found nouns
    colName = name
    for noun in nounList:
        if noun in colName:
            colName = colName.replace(noun, noun + ' ')

    # check for nouns that also contain shorter nouns
    for noun in subsetNouns:
        if noun in colName:
            colName = colName.replace(noun, noun + ' ')
            break

    # return the new name without trailing spaces, too many spaces
    return " ".join(colName.split())


def invertRGBLuma(r, g, b):
    """Invert the rgb colour using the ycbcr method by inverting the luma
    rgb input r, g, b in range 0-255
    """
    # rgbprimeIn = [gam_sRGB(r/255.0),gam_sRGB(g/255.0),gam_sRGB(b/255.0)]
    rgbprimeIn = [r, g, b]

    # rgbprimeIn r, g, b in range 0-255
    cie = np.dot(COLORMATRIXJPEG, rgbprimeIn)
    ycbcr = np.add(cie, COLORMATRIXJPEGCONST)
    ycbcr = np.clip(ycbcr, [0, 0, 0], [255, 255, 255])

    # invert the luma - reverse y
    ycbcr[0] = 255 - ycbcr[0]
    ycbcr = np.add(ycbcr, COLORMATRIXJPEGINVOFFSET)

    rgbPrimeOut = np.dot(COLORMATRIXJPEGINV, ycbcr)
    # rgbPrimeOut = np.add(rgbPrimeOut, COLORMATRIXJPEGINVCONST) / 256

    # return tuple([255*inv_gam_sRGB(col) for col in rgbPrimeOut])

    # clip the colours
    rgbPrimeOut = np.clip(rgbPrimeOut, [0, 0, 0], [255, 255, 255])
    return tuple([float(col) for col in rgbPrimeOut])


def invertRGBHue(r, g, b):
    """Invert the rgb colour using the ycbcr method by finding the opposite hue
    rgb input r, g, b in range 0-255
    """
    # rgbprimeIn = [gam_sRGB(r/255.0),gam_sRGB(g/255.0),gam_sRGB(b/255.0)]
    rgbprimeIn = [r, g, b]

    # rgbprimeIn r, g, b in range 0-255
    cie = np.dot(COLORMATRIXJPEG, rgbprimeIn)
    ycbcr = np.add(cie, COLORMATRIXJPEGCONST)
    ycbcr = np.clip(ycbcr, [0, 0, 0], [255, 255, 255])

    # get opposite hue - reverse cb and cr
    ycbcr[1] = 255 - ycbcr[1]
    ycbcr[2] = 255 - ycbcr[2]
    ycbcr = np.add(ycbcr, COLORMATRIXJPEGINVOFFSET)

    rgbPrimeOut = np.dot(COLORMATRIXJPEGINV, ycbcr)
    # rgbPrimeOut = np.add(rgbPrimeOut, COLORMATRIXJPEGINVCONST) / 256

    # return tuple([255*inv_gam_sRGB(col) for col in rgbPrimeOut])

    # clip the colours
    rgbPrimeOut = np.clip(rgbPrimeOut, [0, 0, 0], [255, 255, 255])
    return tuple([float(col) for col in rgbPrimeOut])


def _getRandomColours(numberOfColors):
    import random

    return ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)]) for i in range(numberOfColors)]


ERRORCOLOUR = '#FF0000'

colourNameToHexDict = {
    'red'    : '#ff0000',
    'green'  : '#00ff00',
    'blue'   : '#0000ff',
    'yellow' : '#ffff00',
    'magenta': '#ff00ff',
    'cyan'   : '#00ffff',
    }

# small set of colours
shortSpectrumColours = OrderedDict([('#cb1400', 'red'),
                                    ('#860700', 'dark red'),
                                    ('#933355', 'burgundy'),
                                    ('#947676', 'bazaar'),

                                    ('#d231cb', 'pink'),
                                    ('#df2950', 'pastel pink'),
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

# set of colours for spectra on light background
darkDefaultSpectrumColours = OrderedDict([('#008080', 'teal'),
                                          ('#DA70D6', 'orchid'),
                                          ('#800080', 'purple'),
                                          ('#808000', 'olive'),
                                          ('#1E90FF', 'dodgerblue'),
                                          ('#FFA500', 'orange'),
                                          ('#FF0000', 'red'),
                                          ('#4682B4', 'steelblue'),
                                          ('#008000', 'green'),
                                          ('#8A2BE2', 'blueviolet'),
                                          ('#800000', 'maroon'),
                                          ('#00CED1', 'darkturquoise'),
                                          ('#000080', 'navy'),
                                          ('#FF4500', 'orangered'),
                                          ('#FF1493', 'deeppink'),
                                          ('#32CD32', 'limegreen'),
                                          ])

# set of colours for spectra on dark background
lightDefaultSpectrumColours = OrderedDict([('#6B8E23', 'olivedrab'),
                                           ('#DA70D6', 'orchid'),
                                           ('#8A2BE2', 'blueviolet'),
                                           ('#808000', 'olive'),
                                           ('#1E90FF', 'dodgerblue'),
                                           ('#FFA500', 'orange'),
                                           ('#FF0000', 'red'),
                                           ('#4682B4', 'steelblue'),
                                           ('#7FFF00', 'chartreuse'),
                                           ('#9932CC', 'darkorchid'),
                                           ('#A0522D', 'sienna'),
                                           ('#00CED1', 'darkturquoise'),
                                           ('#00FFFF', 'cyan'),
                                           ('#FFFF00', 'yellow'),
                                           ('#FF1493', 'deeppink'),
                                           ('#32CD32', 'limegreen'),
                                           ])

# set of colours that have higher saturation
brightColours = OrderedDict([('#000000', 'black'),
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
                             ('#F08080', 'lightcoral'),
                             ('#CD5C5C', 'indianred'),
                             ('#A52A2A', 'brown'),
                             ('#B22222', 'firebrick'),
                             ('#800000', 'maroon'),
                             ('#8B0000', 'darkred'),
                             ('#FF0000', 'red'),
                             ('#FA8072', 'salmon'),
                             ('#FF6347', 'tomato'),
                             ('#E9967A', 'darksalmon'),
                             ('#FF7F50', 'coral'),
                             ('#FF4500', 'orangered'),
                             ('#FFA07A', 'lightsalmon'),
                             ('#A0522D', 'sienna'),
                             ('#D2691E', 'chocolate'),
                             ('#8B4513', 'saddlebrown'),
                             ('#F4A460', 'sandybrown'),
                             ('#CD853F', 'peru'),
                             ('#FF8C00', 'darkorange'),
                             ('#DEB887', 'burlywood'),
                             ('#D2B48C', 'tan'),
                             ('#FFDEAD', 'navajowhite'),
                             ('#FFA500', 'orange'),
                             ('#B8860B', 'darkgoldenrod'),
                             ('#DAA520', 'goldenrod'),
                             ('#FFD700', 'gold'),
                             ('#F0E68C', 'khaki'),
                             ('#BDB76B', 'darkkhaki'),
                             ('#808000', 'olive'),
                             ('#FFFF00', 'yellow'),
                             ('#6B8E23', 'olivedrab'),
                             ('#9ACD32', 'yellowgreen'),
                             ('#556B2F', 'darkolivegreen'),
                             ('#ADFF2F', 'greenyellow'),
                             ('#7FFF00', 'chartreuse'),
                             ('#7CFC00', 'lawngreen'),
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
                             ('#00FA9A', 'mediumspringgreen'),
                             ('#66CDAA', 'mediumaquamarine'),
                             ('#7FFFD4', 'aquamarine'),
                             ('#40E0D0', 'turquoise'),
                             ('#20B2AA', 'lightseagreen'),
                             ('#48D1CC', 'mediumturquoise'),
                             ('#2F4F4F', 'darkslategray'),
                             ('#2F4F4F', 'darkslategrey'),
                             ('#008080', 'teal'),
                             ('#008B8B', 'darkcyan'),
                             ('#00FFFF', 'aqua'),
                             ('#00FFFF', 'cyan'),
                             ('#00CED1', 'darkturquoise'),
                             ('#5F9EA0', 'cadetblue'),
                             ('#00BFFF', 'deepskyblue'),
                             ('#87CEEB', 'skyblue'),
                             ('#87CEFA', 'lightskyblue'),
                             ('#4682B4', 'steelblue'),
                             ('#1E90FF', 'dodgerblue'),
                             ('#6495ED', 'cornflowerblue'),
                             ('#4169E1', 'royalblue'),
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
                             ('#EE82EE', 'violet'),
                             ('#800080', 'purple'),
                             ('#8B008B', 'darkmagenta'),
                             ('#FF00FF', 'fuchsia'),
                             ('#FF00FF', 'magenta'),
                             ('#DA70D6', 'orchid'),
                             ('#C71585', 'mediumvioletred'),
                             ('#FF1493', 'deeppink'),
                             ('#FF69B4', 'hotpink'),
                             ('#DB7093', 'palevioletred'),
                             ('#DC143C', 'crimson'),
                             ])

# all colours defined in the matplotlib colourspace
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

# default color schemes
colorSchemeTable = OrderedDict([('redshade', ('#FFC0C0', '#FF9A9A', '#FF7373', '#FF4D4D', '#FF2626', '#FF0000', '#D90000', '#B30000', '#8C0000', '#660000')),
                                ('orangeshade', ('#FFE0C0', '#FFC890', '#FFB060', '#FF9830', '#FF8000', '#E17100', '#C26100', '#A35200', '#854200', '#663300')),
                                ('yellowshade', ('#FFFF99', '#FFFF4C', '#FFFF00', '#E7E700', '#CFCF00', '#B6B600', '#9E9E00', '#868600', '#6D6D00', '#555500')),
                                ('greenshade', ('#99FF99', '#73F073', '#4CE04C', '#26D026', '#00C000', '#00AE00', '#009C00', '#008A00', '#007800', '#006600')),
                                ('blueshade', ('#C0C0FF', '#9A9AFF', '#7373FF', '#4D4DFF', '#2626FF', '#0000FF', '#0000D9', '#0000B3', '#00008C', '#000066')),
                                ('cyanshade', ('#00FFFF', '#00ECEC', '#00D8D8', '#00C4C4', '#00B0B0', '#009C9C', '#008888', '#007474', '#006060', '#004C4C')),
                                ('purpleshade', ('#E6CCFF', '#D399F0', '#C066E0', '#AC33D0', '#9900C0', '#8500AC', '#700097', '#5C0082', '#47006E', '#330059')),
                                ('greyshade', ('#CCCCCC', '#BBBBBB', '#AAAAAA', '#999999', '#888888', '#777777', '#666666', '#555555', '#444444', '#333333')),
                                ('redshade2', ('#660000', '#8C0000', '#B30000', '#D90000', '#FF0000', '#FF2626', '#FF4D4D', '#FF7373', '#FF9A9A', '#FFC0C0')),
                                ('orangeshade2',
                                 ('#663300', '#854200', '#A35200', '#C26100', '#E17100', '#FF8000', '#FF9830', '#FFB060', '#FFC890', '#FFE0C0')),
                                ('yellowshade2',
                                 ('#555500', '#6D6D00', '#868600', '#9E9E00', '#B6B600', '#CFCF00', '#E7E700', '#FFFF00', '#FFFF4C', '#FFFF99')),
                                ('greenshade2', ('#006600', '#007800', '#008A00', '#009C00', '#00AE00', '#00C000', '#26D026', '#4CE04C', '#73F073', '#99FF99')),
                                ('blueshade2', ('#000066', '#00008C', '#0000B3', '#0000D9', '#0000FF', '#2626FF', '#4D4DFF', '#7373FF', '#9A9AFF', '#C0C0FF')),
                                ('cyanshade2', ('#004C4C', '#006060', '#007474', '#008888', '#009C9C', '#00B0B0', '#00C4C4', '#00D8D8', '#00ECEC', '#00FFFF')),
                                ('purpleshade2',
                                 ('#330059', '#47006E', '#5C0082', '#700097', '#8500AC', '#9900C0', '#AC33D0', '#C066E0', '#D399F0', '#E6CCFF')),
                                ('greyshade2', ('#333333', '#444444', '#555555', '#666666', '#777777', '#888888', '#999999', '#AAAAAA', '#BBBBBB', '#CCCCCC')),

                                ('rainbow', (
                                    '#FF00FF', '#FF0080', '#FF0000', '#FF8000', '#FFFF00', '#80FF00', '#00FF00', '#00FF80', '#00FFFF', '#0080FF', '#0000FF',
                                    '#8000FF')),
                                ('rainbow2',
                                 ('#8000FF', '#0000FF', '#0080FF', '#00FFFF', '#00FF80', '#00FF00', '#80FF00', '#FFFF00', '#FF8000', '#FF0000', '#FF0080',
                                  '#FF00FF')),
                                ('wimbledon', ('#008000', '#1C8E00', '#389C00', '#55AB00', '#71B900', '#8EC700', '#AAD500', '#C7E300', '#E3F100', '#FFFF00')),
                                ('wimbledon2', ('#FFFF00', '#E3F100', '#C7E300', '#AAD500', '#8EC700', '#71B900', '#55AB00', '#389C00', '#1C8E00', '#008000')),
                                ('toothpaste', ('#C0C0FF', '#9A9AFF', '#7373FF', '#4D4DFF', '#2626FF', '#0000FF', '#0040FF', '#0080FF', '#00C0FF', '#00FFFF')),
                                ('toothpaste2', ('#00FFFF', '#00C0FF', '#0080FF', '#0040FF', '#0000FF', '#2626FF', '#4D4DFF', '#7373FF', '#9A9AFF', '#C0C0FF')),
                                ('cmy',
                                 ('#00FFFF', '#33CCFF', '#6699FF', '#9966FF', '#CC33FF', '#FF00FF', '#FF33CC', '#FF6699', '#FF9966', '#FFCC33', '#FFFF00')),
                                ('cmy2',
                                 ('#FFFF00', '#FFCC33', '#FF9966', '#FF6699', '#FF33CC', '#FF00FF', '#CC33FF', '#9966FF', '#6699FF', '#33CCFF', '#00FFFF')),
                                ('steel', ('#C0C0C0', '#ABABB9', '#9595B2', '#8080AB', '#6B6BA4', '#55559D', '#404095', '#2A2A8E', '#151587', '#000080')),
                                ('steel2', ('#000080', '#151587', '#2A2A8E', '#404095', '#55559D', '#6B6BA4', '#8080AB', '#9595B2', '#ABABB9', '#C0C0C0')),
                                ('rgb',
                                 ('#FF0000', '#CC1900', '#993300', '#664D00', '#336600', '#008000', '#006633', '#004D66', '#003399', '#0019CC', '#0000FF')),
                                ('rgb2',
                                 ('#0000FF', '#0019CC', '#003399', '#004D66', '#006633', '#008000', '#336600', '#664D00', '#993300', '#CC1900', '#FF0000')),
                                ('tropicana', ('#FFFF00', '#FFE30E', '#FFC71C', '#FFAA2A', '#FF8E39', '#FF7147', '#FF5555', '#FF3863', '#FF1C72', '#FF0080')),
                                ('tropicana2', ('#FF0080', '#FF1C72', '#FF3863', '#FF5555', '#FF7147', '#FF8E39', '#FFAA2A', '#FFC71C', '#FFE30E', '#FFFF00')),
                                ('sunset', ('#FFC0C0', '#FF9A9A', '#FF7373', '#FF4D4D', '#FF2626', '#FF0000', '#FF4000', '#FF8000', '#FFC000', '#FFFF00')),
                                ('sunset2', ('#FFFF00', '#FFC000', '#FF8000', '#FF4000', '#FF0000', '#FF2626', '#FF4D4D', '#FF7373', '#FF9A9A', '#FFC0C0')),
                                ('magma', ('#000000', '#400000', '#800000', '#C00000', '#FF0000', '#FF3300', '#FF6600', '#FF9900', '#FFCC00', '#FFFF00')),
                                ('magma2', ('#FFFF00', '#FFCC00', '#FF9900', '#FF6600', '#FF3300', '#FF0000', '#C00000', '#800000', '#400000', '#000000')),
                                ('holly', ('#80FF80', '#66E666', '#4DCD4D', '#33B333', '#199A19', '#008000', '#FF0000', '#D50000', '#AB0000', '#800000')),
                                ('holly2', ('#800000', '#AB0000', '#D50000', '#FF0000', '#008000', '#199A19', '#33B333', '#4DCD4D', '#66E666', '#80FF80')),
                                ('glacier', ('#000000', '#000040', '#000080', '#0000C0', '#0000FF', '#2626FF', '#4D4DFF', '#7373FF', '#9A9AFF', '#C0C0FF')),
                                ('glacier2', ('#C0C0FF', '#9A9AFF', '#7373FF', '#4D4DFF', '#2626FF', '#0000FF', '#0000C0', '#000080', '#000040', '#000000')),
                                ('monarchy', ('#C0C0FF', '#6060FF', '#0000FF', '#3300CC', '#660099', '#990066', '#CC0033', '#FF0000', '#C00000', '#800000')),
                                ('monarchy2', ('#800000', '#C00000', '#FF0000', '#CC0033', '#990066', '#660099', '#3300CC', '#0000FF', '#6060FF', '#C0C0FF')),
                                ('contrast', ('#FF0000', '#008000', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF')),
                                ('contrast2', ('#00FFFF', '#FF00FF', '#FFFF00', '#0000FF', '#008000', '#FF0000')),
                                ('lightspectrum', (
                                    '#6B8E23', '#DA70D6', '#8A2BE2', '#808000', '#1E90FF', '#FFA500', '#FF0000', '#4682B4', '#7FFF00', '#9932CC',
                                    '#A0522D', '#00CED1', '#00FFFF', '#FFFF00', '#FF1493', '#32CD32')),
                                ('lightspectrum2', (
                                    '#32CD32', '#FF1493', '#FFFF00', '#00FFFF', '#00CED1', '#A0522D', '#9932CC', '#7FFF00', '#4682B4', '#FF0000', '#FFA500',
                                    '#1E90FF', '#808000', '#8A2BE2', '#DA70D6', '#6B8E23')),

                                ('red-orange', ('#ff2010', '#ff3414', '#ff4818', '#ff5c1c', '#ff7020', '#ff8424', '#ff9828', '#ffac2c', '#ffc030')),
                                ('orange-yellow', ('#ffc030', '#fcc72c', '#facf28', '#f8d724', '#f6df20', '#f4e71c', '#f2ef18', '#f0f714', '#eeff10')),
                                ('yellow-green', ('#eeff10', '#d2f812', '#b6f214', '#9aeb16', '#7fe518', '#63df1a', '#47d81c', '#2bd21e', '#10cc20')),
                                ('green-blue', ('#10cc20', '#12b43b', '#149d57', '#168573', '#186e8f', '#1a56ab', '#1c3fc7', '#1e27e3', '#2010ff')),
                                ('blue-cyan', ('#2010ff', '#202bff', '#2047ff', '#2063ff', '#207fff', '#209aff', '#20b6ff', '#20d2ff', '#20eeff')),
                                ('blue-purple', ('#2010ff', '#3912ff', '#5314ff', '#6d16ff', '#8718ff', '#a01aff', '#ba1cff', '#d41eff', '#ee20ff')),
                                ('orange-red', ('#ffc030', '#ffac2c', '#ff9828', '#ff8424', '#ff7020', '#ff5c1c', '#ff4818', '#ff3414', '#ff2010')),
                                ('yellow-orange', ('#eeff10', '#f0f714', '#f2ef18', '#f4e71c', '#f6df20', '#f8d724', '#facf28', '#fcc72c', '#ffc030')),
                                ('green-yellow', ('#10cc20', '#2bd21e', '#47d81c', '#63df1a', '#7fe518', '#9aeb16', '#b6f214', '#d2f812', '#eeff10')),
                                ('blue-green', ('#2010ff', '#1e27e3', '#1c3fc7', '#1a56ab', '#186e8f', '#168573', '#149d57', '#12b43b', '#10cc20')),
                                ('cyan-blue', ('#20eeff', '#20d2ff', '#20b6ff', '#209aff', '#207fff', '#2063ff', '#2047ff', '#202bff', '#2010ff')),
                                ('purple-blue', ('#ee20ff', '#d41eff', '#ba1cff', '#a01aff', '#8718ff', '#6d16ff', '#5314ff', '#3912ff', '#2010ff')),
                                ('black-white', ('#000000', '#1f1f1f', '#3f3f3f', '#5f5f5f', '#7f7f7f', '#9f9f9f', '#bfbfbf', '#dfdfdf', '#ffffff')),
                                ('white-black', ('#ffffff', '#dfdfdf', '#bfbfbf', '#9f9f9f', '#7f7f7f', '#5f5f5f', '#3f3f3f', '#1f1f1f', '#000000')),
                                ('black-gray', ('#000000', '#0f0f0f', '#1f1f1f', '#2f2f2f', '#3f3f3f', '#4f4f4f', '#5f5f5f', '#6f6f6f', '#7f7f7f')),
                                ('gray-black', ('#7f7f7f', '#6f6f6f', '#5f5f5f', '#4f4f4f', '#3f3f3f', '#2f2f2f', '#1f1f1f', '#0f0f0f', '#000000')),

                                ])

allColoursWithSpaces = OrderedDict([(k, colourNameWithSpace(v)) for k, v in allColours.items()])

# set the spectrum colours to all, override minimum set above
spectrumColours = brightColours

# split the colour palettes into light and dark for different colour schemes
spectrumDarkColours = OrderedDict()
spectrumLightColours = OrderedDict()
spectrumMediumColours = OrderedDict()

for k, v in spectrumColours.items():
    h = hexToRgb(k)

    # colour can belong to both sets
    if gray(*h) > COLOUR_LIGHT_THRESHOLD:
        spectrumLightColours[k] = v
    if gray(*h) < COLOUR_DARK_THRESHOLD:
        spectrumDarkColours[k] = v
    if gray(*h) > COLOUR_LIGHT_THRESHOLD and gray(*h) < COLOUR_DARK_THRESHOLD:
        spectrumMediumColours[k] = v

allDarkColours = OrderedDict()
allLightColours = OrderedDict()
allMediumColours = OrderedDict()

for k, v in allColours.items():
    h = hexToRgb(k)

    # colour can belong to both sets
    if gray(*h) > COLOUR_LIGHT_THRESHOLD:
        allLightColours[k] = v
    if gray(*h) < COLOUR_DARK_THRESHOLD:
        allDarkColours[k] = v
    if gray(*h) > COLOUR_LIGHT_THRESHOLD and gray(*h) < COLOUR_DARK_THRESHOLD:
        allMediumColours[k] = v

spectrumHexLightColours = tuple(ky for ky in spectrumLightColours.keys() if ky != '#')
spectrumHexDarkColours = tuple(ky for ky in spectrumDarkColours.keys() if ky != '#')
spectrumHexMediumColours = tuple(ky for ky in spectrumMediumColours.keys() if ky != '#')

spectrumHexDefaultLightColours = tuple(ky for ky in lightDefaultSpectrumColours.keys() if ky != '#')
spectrumHexDefaultDarkColours = tuple(ky for ky in darkDefaultSpectrumColours.keys() if ky != '#')

# override this with spectrumLight/DarkColours when colourScheme is changed
spectrumHexColours = tuple(ky for ky in spectrumColours.keys() if ky != '#')


# Note that Colour strings are not re-used


class Colour(str):
    """ A class to make colour manipulation easier and more transparent.
        Assumes that r, g, b values are 8-bit so between 0 and 255 and have optional a.

    >>> c = Colour('magenta')
    >>> c = Colour('#FF00FF')
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

        return '#' + ''.join([_ccpnHex(x)[2:] for x in (self.r, self.g, self.b)])

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


def isSpectrumColour(colourString):
    """Return true if the colourString is in the list
    """
    return colourString in list(spectrumColours.keys())


def addNewColourString(colourString):
    """Add a new Hex colour to the colourlist
    New colour has the name 'Colour <n>' where n is the next free number
    """
    # '#' is reserved for auto colour so shouldn't ever be added
    if colourString != '#' and colourString not in spectrumColours:
        newIndex = str(len(spectrumColours.items()) + 1)
        spectrumColours[colourString] = 'Colour %s' % newIndex


def autoCorrectHexColour(colour, referenceHexColour='#ffffff', addNewColour=True):
    """Autocorrect colours if too close to the reference value
    """
    if colour == '#':
        return colour

    g = gray(*hexToRgb(colour))

    rgb = hexToRgb(referenceHexColour)
    gRef = gray(*rgb)

    if abs(g - gRef) < COLOUR_THRESHOLD:
        newCol = invertRGBLuma(*hexToRgb(colour))
        hx = rgbToHex(*newCol)

        if addNewColour:
            addNewColourString(hx)
        return hx

    return colour


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
    # try:
    #     pulldown.setCurrentText(spectrumColours[colourString])
    # except:
    #     if allowAuto and '#' in pulldown.texts:
    #         pulldown.setCurrentText('#')

    if colourString in spectrumColours:
        pulldown.setCurrentText(spectrumColours[colourString])
    elif colourString in colorSchemeTable:
        pulldown.setCurrentText(colourString)
    elif allowAuto and '#' in pulldown.texts:
        pulldown.setCurrentText('#')


ICON_SIZE = 20


def fillColourPulldown(pulldown, allowAuto=False, allowNone=False, includeGradients=True):
    currText = pulldown.currentText()
    # currIndex = pulldown.currentIndex()
    # print ('>>>', currText, currIndex)
    with pulldown.blockWidgetSignals():
        pulldown.clear()
        if allowAuto:
            pulldown.addItem(text='<auto>')
        if allowNone:
            pulldown.addItem(text='')

        for item in spectrumColours.items():
            # if item[1] not in pulldown.texts:

            colName = item[1]  # colourNameWithSpace(item[1])

            if item[0] != '#':
                pix = QtGui.QPixmap(QtCore.QSize(ICON_SIZE, ICON_SIZE))
                pix.fill(QtGui.QColor(item[0]))
                pulldown.addItem(icon=QtGui.QIcon(pix), text=colName)
            elif allowAuto:
                pulldown.addItem(text=colName)

        if includeGradients:
            for colName, colourList in colorSchemeTable.items():
                pix = QtGui.QPixmap(QtCore.QSize(ICON_SIZE, ICON_SIZE))
                step = ICON_SIZE
                stepX = ICON_SIZE
                stepY = len(colourList) - 1
                jj = 0
                painter = QtGui.QPainter(pix)

                for ii in range(ICON_SIZE):
                    _interp = (stepX - step) / stepX
                    _intCol = interpolateColourHex(colourList[min(jj, stepY)], colourList[min(jj + 1, stepY)],
                                                   _interp)

                    painter.setPen(QtGui.QColor(_intCol))
                    painter.drawLine(ii, 0, ii, ICON_SIZE)
                    step -= stepY
                    while step < 0:
                        step += stepX
                        jj += 1

                painter.end()
                pulldown.addItem(icon=QtGui.QIcon(pix), text=colName)

        pulldown.setCurrentText(currText)


def _setColourPulldown(pulldown, attrib, allowAuto=False, includeGradients=True, allowNone=False):
    """Populate colour pulldown and set to the current colour
    """
    spectrumColourKeys = list(spectrumColours.keys())
    fillColourPulldown(pulldown, allowAuto=allowAuto, includeGradients=includeGradients, allowNone=allowNone)
    c = attrib.upper() if attrib and attrib.startswith('#') else attrib
    if c in spectrumColourKeys:
        col = spectrumColours[c]
        pulldown.setCurrentText(col)
    elif attrib in colorSchemeTable:
        pulldown.setCurrentText(attrib)
    elif c is None:
        if allowNone:
            pulldown.setCurrentText('')
    else:
        addNewColourString(c)
        fillColourPulldown(pulldown, allowAuto=allowAuto, includeGradients=includeGradients, allowNone=allowNone)
        if c != '#' or allowAuto is True:
            col = spectrumColours[c]
            pulldown.setCurrentText(col)


def getSpectrumColour(colourName, defaultReturn=None):
    """
    return the hex colour of the named colour
    """
    try:
        colName = colourName  # colourNameNoSpace(colourName)

        if colName in spectrumColours.values():
            col = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
            return col.upper() if col.startswith('#') else col
        elif colName in colorSchemeTable:
            return colName
        else:
            return defaultReturn

    except:
        # colour not found in the list
        return defaultReturn


def getAutoColourRgbRatio(inColour=None, sourceObject=None, colourAttribute=None, defaultColour=None):
    listColour = inColour
    if listColour == '#':
        listColour = getattr(sourceObject, colourAttribute, defaultColour)
        if listColour in colorSchemeTable:
            # get the first item from the colour gradient
            listColour = colorSchemeTable[listColour][0]

    return hexToRgbRatio(listColour)


def findNearestHex(hexCol, colourHexList):
    weights = (0.3, 0.59, 0.11)  # assuming rgb
    rgbIn = hexToRgb(hexCol)

    lastCol = None
    for col in colourHexList:

        rgbTest = hexToRgb(col)

        # use euclidean to find closest colour
        num = 0.0
        for a, b, w in zip(rgbIn, rgbTest, weights):
            num += pow((a - b) * w, 4)

        if lastCol is None or num < lastDiff:
            lastDiff = num
            lastCol = (col, num)

    return lastCol[0]


if __name__ == '__main__':
    """Simple routine to plot all the named colors in the matplotlib colorspace
    """
    import matplotlib.pyplot as plt
    from matplotlib import colors as mcolors


    colors = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)


    def colourPlot(names, title='ColourPlot'):
        """make a colour plot of the names
        """
        n = len(names)
        ncols = 4
        nrows = n // ncols + 1

        fig, ax = plt.subplots(figsize=(16, 9))

        # Get height and width
        X, Y = fig.get_dpi() * fig.get_size_inches()

        Y0 = Y - fig.get_dpi() * 1.0  # remove an inch from the size
        h = Y0 // max((nrows + 1), 15)
        w = X // ncols

        for i, name in enumerate(names):
            row = i % nrows
            col = i // nrows

            y = Y0 - (row * h) - h

            xi_line = w * (col + 0.05)
            xf_line = w * (col + 0.25)
            xi_text = w * (col + 0.3)

            ax.text(xi_text, y, name, fontsize=(h * 0.5),
                    horizontalalignment='left',
                    verticalalignment='center')

            ax.hlines(y + h * 0.1, xi_line, xf_line,
                      color=colors[name] if name in colors else name,
                      linewidth=(h * 0.6))

        ax.set_xlim(0, X)
        ax.set_ylim(0, Y)
        ax.set_axis_off()

        ax.text(fig.get_dpi() * 0.25, Y - fig.get_dpi() * 0.5,
                title, fontsize=fig.get_dpi() * 0.25,
                horizontalalignment='left',
                verticalalignment='center')

        fig.subplots_adjust(left=0, right=1,
                            top=1, bottom=0,
                            hspace=0, wspace=0)
        plt.show()


    # Sort colors by hue, saturation, value and name.
    by_hsv = sorted((tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name)
                    for name, color in colors.items())
    sorted_names = [name for hsv, name in by_hsv
                    if (hsv[0] == 0.0 and hsv[1] == 0.0) or hsv[1] > 0.3]

    # print the colors to generate full colorList
    for col in sorted_names:
        if isinstance(colors[col], str):
            # col = colourNameWithSpace(col)

            print('(' + repr(colors[col]) + ', ' + repr(col) + '),')

    colourPlot(spectrumDarkColours.values(), title='Dark Spectrum Colours')
    colourPlot(spectrumMediumColours.values(), title='Medium Spectrum Colours')
    colourPlot(spectrumLightColours.values(), title='Light Spectrum Colours')

    thisPalette = spectrumLightColours
    colourPlot(thisPalette.values(), title='Light Default Spectrum Colours')
    opposites = []
    for col in thisPalette.keys():
        rgbIn = hexToRgb(col)
        negRGB = invertRGBHue(*rgbIn)
        oppCol = rgbToHex(*negRGB)

        oppCol = findNearestHex(oppCol, thisPalette.keys())
        opposites.append(thisPalette[oppCol])

    colourPlot(opposites, title='Light Inverted Colours')

    thisPalette = spectrumDarkColours
    colourPlot(thisPalette.values(), title='Dark Default Spectrum Colours')
    opposites = []
    for col in thisPalette.keys():
        rgbIn = hexToRgb(col)
        negRGB = invertRGBHue(*rgbIn)
        oppCol = rgbToHex(*negRGB)

        oppCol = findNearestHex(oppCol, thisPalette.keys())
        opposites.append(thisPalette[oppCol])

    colourPlot(opposites, title='Dark Inverted Colours')


def interpolateColourRgba(colour1, colour2, value, alpha=1.0):
    result = [(col1 + (col2 - col1) * value) for col1, col2 in zip(colour1, colour2)]
    while len(result) < 4:
        result.append(alpha)
    return tuple(result[:4])


def interpolateColourHex(hexColor1, hexColor2, value, alpha=1.0):
    if hexColor1 is None or hexColor2 is None:
        return None
    value = np.clip(value, 0.0, 1.0)

    r1 = int('0x' + hexColor1[1:3], 16)
    g1 = int('0x' + hexColor1[3:5], 16)
    b1 = int('0x' + hexColor1[5:7], 16)
    r2 = int('0x' + hexColor2[1:3], 16)
    g2 = int('0x' + hexColor2[3:5], 16)
    b2 = int('0x' + hexColor2[5:7], 16)
    colour1 = (r1, g1, b1)
    colour2 = (r2, g2, b2)

    result = [(col1 + (col2 - col1) * value) for col1, col2 in zip(colour1, colour2)]
    return '#%02x%02x%02x' % (int(result[0]), int(result[1]), int(result[2]))

# ('darkredshade', ('#7f6060', '#7f4d4d', '#7f3939', '#7f2626', '#7f1313', '#7f0000', '#6c0000', '#590000', '#460000', '#330000')),
# ('darkorangeshade', ('#7f7060', '#7f6448', '#7f5830', '#7f4c18', '#7f4000', '#703800', '#613000', '#512900', '#422100', '#331900')),
# ('darkyellowshade', ('#7f7f4c', '#7f7f26', '#7f7f00', '#737300', '#676700', '#5b5b00', '#4f4f00', '#434300', '#363600', '#2a2a00')),
# ('darkgreenshade', ('#4c7f4c', '#397839', '#267026', '#136813', '#006000', '#005700', '#004e00', '#004500', '#003c00', '#003300')),
# ('darkblueshade', ('#60607f', '#4d4d7f', '#39397f', '#26267f', '#13137f', '#00007f', '#00006c', '#000059', '#000046', '#000033')),
# ('darkcyanshade', ('#007f7f', '#007676', '#006c6c', '#006262', '#005858', '#004e4e', '#004444', '#003a3a', '#003030', '#002626')),
# ('darkpurpleshade', ('#73667f', '#694c78', '#603370', '#561968', '#4c0060', '#420056', '#38004b', '#2e0041', '#230037', '#19002c')),
# ('darkgreyshade', ('#666666', '#5d5d5d', '#555555', '#4c4c4c', '#444444', '#3b3b3b', '#333333', '#2a2a2a', '#222222', '#191919')),
# ('darkredshade2', ('#330000', '#460000', '#590000', '#6c0000', '#7f0000', '#7f1313', '#7f2626', '#7f3939', '#7f4d4d', '#7f6060')),
# ('darkorangeshade2', ('#331900', '#422100', '#512900', '#613000', '#703800', '#7f4000', '#7f4c18', '#7f5830', '#7f6448', '#7f7060')),
# ('darkyellowshade2', ('#2a2a00', '#363600', '#434300', '#4f4f00', '#5b5b00', '#676700', '#737300', '#7f7f00', '#7f7f26', '#7f7f4c')),
# ('darkgreenshade2', ('#003300', '#003c00', '#004500', '#004e00', '#005700', '#006000', '#136813', '#267026', '#397839', '#4c7f4c')),
# ('darkblueshade2', ('#000033', '#000046', '#000059', '#00006c', '#00007f', '#13137f', '#26267f', '#39397f', '#4d4d7f', '#60607f')),
# ('darkcyanshade2', ('#002626', '#003030', '#003a3a', '#004444', '#004e4e', '#005858', '#006262', '#006c6c', '#007676', '#007f7f')),
# ('darkpurpleshade2', ('#19002c', '#230037', '#2e0041', '#38004b', '#420056', '#4c0060', '#561968', '#603370', '#694c78', '#73667f')),
# ('darkgreyshade2', ('#191919', '#222222', '#2a2a2a', '#333333', '#3b3b3b', '#444444', '#4c4c4c', '#555555', '#5d5d5d', '#666666')),
#
# ('darkrainbow',
#  ('#7f007f', '#7f0040', '#7f0000', '#7f4000', '#7f7f00', '#407f00', '#007f00', '#007f40', '#007f7f', '#00407f', '#00007f', '#40007f')),
# ('darkrainbow2',
#  ('#40007f', '#00007f', '#00407f', '#007f7f', '#007f40', '#007f00', '#407f00', '#7f7f00', '#7f4000', '#7f0000', '#7f0040', '#7f007f')),
# ('darkwimbledon', ('#004000', '#0e4700', '#1c4e00', '#2a5500', '#385c00', '#476300', '#556a00', '#637100', '#717800', '#7f7f00')),
# ('darkwimbledon2', ('#7f7f00', '#717800', '#637100', '#556a00', '#476300', '#385c00', '#2a5500', '#1c4e00', '#0e4700', '#004000')),
# ('darktoothpaste', ('#60607f', '#4d4d7f', '#39397f', '#26267f', '#13137f', '#00007f', '#00207f', '#00407f', '#00607f', '#007f7f')),
# ('darktoothpaste2', ('#007f7f', '#00607f', '#00407f', '#00207f', '#00007f', '#13137f', '#26267f', '#39397f', '#4d4d7f', '#60607f')),
# ('darkcmy', ('#007f7f', '#19667f', '#334c7f', '#4c337f', '#66197f', '#7f007f', '#7f1966', '#7f334c', '#7f4c33', '#7f6619', '#7f7f00')),
# ('darkcmy2', ('#7f7f00', '#7f6619', '#7f4c33', '#7f334c', '#7f1966', '#7f007f', '#66197f', '#4c337f', '#334c7f', '#19667f', '#007f7f')),
# ('darksteel', ('#606060', '#55555c', '#4a4a59', '#404055', '#353552', '#2a2a4e', '#20204a', '#151547', '#0a0a43', '#000040')),
# ('darksteel2', ('#000040', '#0a0a43', '#151547', '#20204a', '#2a2a4e', '#353552', '#404055', '#4a4a59', '#55555c', '#606060')),
# ('darkrgb', ('#7f0000', '#660c00', '#4c1900', '#332600', '#193300', '#004000', '#003319', '#002633', '#00194c', '#000c66', '#00007f')),
# ('darkrgb2', ('#00007f', '#000c66', '#00194c', '#002633', '#003319', '#004000', '#193300', '#332600', '#4c1900', '#660c00', '#7f0000')),
# ('darktropicana', ('#7f7f00', '#7f7107', '#7f630e', '#7f5515', '#7f471c', '#7f3823', '#7f2a2a', '#7f1c31', '#7f0e39', '#7f0040')),
# ('darktropicana2', ('#7f0040', '#7f0e39', '#7f1c31', '#7f2a2a', '#7f3823', '#7f471c', '#7f5515', '#7f630e', '#7f7107', '#7f7f00')),
# ('darksunset', ('#7f6060', '#7f4d4d', '#7f3939', '#7f2626', '#7f1313', '#7f0000', '#7f2000', '#7f4000', '#7f6000', '#7f7f00')),
# ('darksunset2', ('#7f7f00', '#7f6000', '#7f4000', '#7f2000', '#7f0000', '#7f1313', '#7f2626', '#7f3939', '#7f4d4d', '#7f6060')),
# ('darkmagma', ('#000000', '#200000', '#400000', '#600000', '#7f0000', '#7f1900', '#7f3300', '#7f4c00', '#7f6600', '#7f7f00')),
# ('darkmagma2', ('#7f7f00', '#7f6600', '#7f4c00', '#7f3300', '#7f1900', '#7f0000', '#600000', '#400000', '#200000', '#000000')),
# ('darkholly', ('#407f40', '#337333', '#266626', '#195919', '#0c4d0c', '#004000', '#7f0000', '#6a0000', '#550000', '#400000')),
# ('darkholly2', ('#400000', '#550000', '#6a0000', '#7f0000', '#004000', '#0c4d0c', '#195919', '#266626', '#337333', '#407f40')),
# ('darkglacier', ('#000000', '#000020', '#000040', '#000060', '#00007f', '#13137f', '#26267f', '#39397f', '#4d4d7f', '#60607f')),
# ('darkglacier2', ('#60607f', '#4d4d7f', '#39397f', '#26267f', '#13137f', '#00007f', '#000060', '#000040', '#000020', '#000000')),
# ('darkmonarchy', ('#60607f', '#30307f', '#00007f', '#190066', '#33004c', '#4c0033', '#660019', '#7f0000', '#600000', '#400000')),
# ('darkmonarchy2', ('#400000', '#600000', '#7f0000', '#660019', '#4c0033', '#33004c', '#190066', '#00007f', '#30307f', '#60607f')),
# ('darkcontrast', ('#7f0000', '#004000', '#00007f', '#7f7f00', '#7f007f', '#007f7f')),
# ('darkcontrast2', ('#007f7f', '#7f007f', '#7f7f00', '#00007f', '#004000', '#7f0000')),
# ('darkspectrum', (
#     '#004040', '#6d386b', '#400040', '#404000', '#0f487f', '#7f5200', '#7f0000', '#23415a', '#004000', '#451571', '#400000', '#006768', '#000040',
#     '#7f2200', '#7f0a49', '#196619')),
# ('darkspectrum2', (
#     '#196619', '#7f0a49', '#7f2200', '#000040', '#006768', '#400000', '#451571', '#004000', '#23415a', '#7f0000', '#7f5200', '#0f487f', '#404000',
#     '#400040', '#6d386b', '#004040')),
# ('darkred-orange', ('#7f1008', '#7f1a0a', '#7f240c', '#7f2e0e', '#7f3810', '#7f4212', '#7f4c14', '#7f5616', '#7f6018')),
# ('darkorange-yellow', ('#7f6018', '#7e6316', '#7d6714', '#7c6b12', '#7b6f10', '#7a730e', '#79770c', '#787b0a', '#777f08')),
# ('darkyellow-green', ('#777f08', '#697c09', '#5b790a', '#4d750b', '#3f720c', '#316f0d', '#236c0e', '#15690f', '#086610')),
# ('darkgreen-blue', ('#086610', '#095a1d', '#0a4e2b', '#0b4239', '#0c3747', '#0d2b55', '#0e1f63', '#0f1371', '#10087f')),
# ('darkblue-cyan', ('#10087f', '#10157f', '#10237f', '#10317f', '#103f7f', '#104d7f', '#105b7f', '#10697f', '#10777f')),
# ('darkblue-purple', ('#10087f', '#1c097f', '#290a7f', '#360b7f', '#430c7f', '#500d7f', '#5d0e7f', '#6a0f7f', '#77107f')),
# ('darkorange-red', ('#7f6018', '#7f5616', '#7f4c14', '#7f4212', '#7f3810', '#7f2e0e', '#7f240c', '#7f1a0a', '#7f1008')),
# ('darkyellow-orange', ('#777f08', '#787b0a', '#79770c', '#7a730e', '#7b6f10', '#7c6b12', '#7d6714', '#7e6316', '#7f6018')),
# ('darkgreen-yellow', ('#086610', '#15690f', '#236c0e', '#316f0d', '#3f720c', '#4d750b', '#5b790a', '#697c09', '#777f08')),
# ('darkblue-green', ('#10087f', '#0f1371', '#0e1f63', '#0d2b55', '#0c3747', '#0b4239', '#0a4e2b', '#095a1d', '#086610')),
# ('darkcyan-blue', ('#10777f', '#10697f', '#105b7f', '#104d7f', '#103f7f', '#10317f', '#10237f', '#10157f', '#10087f')),
# ('darkpurple-blue', ('#77107f', '#6a0f7f', '#5d0e7f', '#500d7f', '#430c7f', '#360b7f', '#290a7f', '#1c097f', '#10087f')),
#
# ('darkspectrum', (
#     '#008080', '#DA70D6', '#800080', '#808000', '#1E90FF', '#FFA500', '#FF0000', '#4682B4', '#008000', '#8A2BE2', '#800000',
#     '#00CED1', '#000080', '#FF4500', '#FF1493', '#32CD32')),
# ('darkspectrum2', (
#     '#32CD32', '#FF1493', '#FF4500', '#000080', '#00CED1', '#800000', '#8A2BE2', '#008000', '#4682B4', '#FF0000', '#FFA500',
#     '#1E90FF', '#808000', '#800080', '#DA70D6', '#008080')),
