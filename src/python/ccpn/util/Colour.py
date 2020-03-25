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
__dateModified__ = "$dateModified: 2020-03-25 14:47:21 +0000 (Wed, March 25, 2020) $"
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

    rgbprimeOut = np.dot(COLORMATRIXJPEGINV, ycbcr)
    # rgbprimeOut = np.add(rgbprimeOut, COLORMATRIXJPEGINVCONST) / 256

    # return tuple([255*inv_gam_sRGB(col) for col in rgbprimeOut])

    # clip the colours
    rgbprimeOut = np.clip(rgbprimeOut, [0, 0, 0], [255, 255, 255])
    return tuple([float(col) for col in rgbprimeOut])


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

    rgbprimeOut = np.dot(COLORMATRIXJPEGINV, ycbcr)
    # rgbprimeOut = np.add(rgbprimeOut, COLORMATRIXJPEGINVCONST) / 256

    # return tuple([255*inv_gam_sRGB(col) for col in rgbprimeOut])

    # clip the colours
    rgbprimeOut = np.clip(rgbprimeOut, [0, 0, 0], [255, 255, 255])
    return tuple([float(col) for col in rgbprimeOut])


def _getRandomColours(numberOfColors):
    import random

    return ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)]) for i in range(numberOfColors)]


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
    try:
        pulldown.setCurrentText(spectrumColours[colourString])
    except:
        if allowAuto and '#' in pulldown.texts:
            pulldown.setCurrentText('#')


def fillColourPulldown(pulldown, allowAuto=False):
    currText = pulldown.currentText()
    # currIndex = pulldown.currentIndex()
    # print ('>>>', currText, currIndex)
    with pulldown.blockWidgetSignals():
        pulldown.clear()
        if allowAuto:
            pulldown.addItem(text='<auto>')
        for item in spectrumColours.items():
            # if item[1] not in pulldown.texts:

            colName = item[1]  # colourNameWithSpace(item[1])

            if item[0] != '#':
                pix = QtGui.QPixmap(QtCore.QSize(20, 20))
                pix.fill(QtGui.QColor(item[0]))
                pulldown.addItem(icon=QtGui.QIcon(pix), text=colName)
            elif allowAuto:
                pulldown.addItem(text=colName)

        pulldown.setCurrentText(currText)


def _setColourPulldown(pulldown, attrib):
    """Populate colour pulldown and set to the current colour
    """
    spectrumColourKeys = list(spectrumColours.keys())
    fillColourPulldown(pulldown, allowAuto=False)
    c = attrib.upper() if attrib.startswith('#') else attrib
    if c in spectrumColourKeys:
        col = spectrumColours[c]
        pulldown.setCurrentText(col)
    else:
        addNewColourString(c)
        fillColourPulldown(pulldown, allowAuto=False)
        col = spectrumColours[c]
        pulldown.setCurrentText(col)


def getSpectrumColour(colourName, defaultReturn=None):
    """
    return the hex colour of the named colour
    """
    try:
        colName = colourName  # colourNameNoSpace(colourName)

        col = list(spectrumColours.keys())[list(spectrumColours.values()).index(colName)]
        return col.upper() if col.startswith('#') else col
    except:
        # colour not found in the list
        return defaultReturn


def getAutoColourRgbRatio(inColour=None, sourceObject=None, colourAttribute=None, defaultColour=None):
    listColour = inColour
    if listColour == '#':
        listColour = getattr(sourceObject, colourAttribute, defaultColour)
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
