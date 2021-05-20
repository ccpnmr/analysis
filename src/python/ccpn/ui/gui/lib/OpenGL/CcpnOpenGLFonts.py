"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-05-20 19:34:35 +0100 (Thu, May 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 14:07:55 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys, os
from imageio import imread
from PyQt5 import QtWidgets
import numpy as np
import math
from collections import namedtuple
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLVertexArray, GLRENDERMODE_DRAW
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import LEFTBORDER, RIGHTBORDER, TOPBORDER, BOTTOMBORDER
from ccpn.util.Colour import hexToRgbRatio
from ccpn.util.AttrDict import AttrDict

from ccpn.ui.gui.lib.OpenGL import GL, GLU, GLUT


GlyphXpos = 'Xpos'
GlyphYpos = 'Ypos'
GlyphWidth = 'Width'
GlyphHeight = 'Height'
GlyphXoffset = 'Xoffset'
GlyphYoffset = 'Yoffset'
GlyphOrigW = 'OrigW'
GlyphOrigH = 'OrigH'
GlyphKerns = 'Kerns'
GlyphTX0 = 'tx0'
GlyphTY0 = 'ty0'
GlyphTX1 = 'tx1'
GlyphTY1 = 'ty1'
GlyphPX0 = 'px0'
GlyphPY0 = 'py0'
GlyphPX1 = 'px1'
GlyphPY1 = 'py1'

FONT_FILE = 0
FULL_FONT_NAME = 1

GLGlyphTuple = namedtuple('GLGlyphTuple', 'GlyphXpos GlyphYpos GlyphWidth GlyphHeight '
                                          'GlyphXoffset GlyphYoffset GlyphOrigW GlyphOrigH GlyphKerns '
                                          'GlyphTX0 GlyphTY0 GlyphTX1 GlyphTY1 '
                                          'GlyphPX0 GlyphPY0 GlyphPX1 GlyphPY1')


class CcpnGLFont():
    def __init__(self, fileName=None, base=0, fontTransparency=None, activeTexture=0, scale=None):
        self.fontName = None
        self.fontGlyph = {}  #[None] * 256
        self.base = base
        self.scale = scale

        if scale == None:
            raise Exception('scale must be defined for font %s ' % fileName)
        with open(fileName, 'r') as op:
            self.fontInfo = op.read().split('\n')

        # no checking yet
        self.fontFile = self.fontInfo[FONT_FILE].replace('textures: ', '')
        self.fontPNG = imread(fileName.filepath / self.fontFile)
        self._fontArray = np.array(self.fontPNG * (fontTransparency if fontTransparency is not None else 1.0), dtype=np.uint8)[:, :, 3]

        fontRows = []
        fontID = ()

        for ii, row in enumerate(self.fontInfo):
            if ii and row and row[0].isalpha():
                # assume that this is a font name
                if not row.startswith('kerning'):
                    fontID = (ii, row)
                else:
                    fontID += (ii,)
                    fontRows.append(fontID)
        fontRows.append((len(self.fontInfo) - 1, None, None))

        for _font, _nextFont in zip(fontRows, fontRows[1:]):
            _startRow, _fontName, _kerningRow = _font
            _nextRow = _nextFont[0]

            self._buildFont(_fontName, _startRow, _kerningRow, _nextRow, scale, fontTransparency)

        _foundFonts = [glyph.fontName for glyph in self.fontGlyph.values()]
        if len(set(_foundFonts)) != 1:
            raise Exception('font file should only contain a single font type')
        self.fontName = _foundFonts[0]

        self.activeTexture = GL.GL_TEXTURE0 + activeTexture
        self.activeTextureNum = activeTexture

        self.textureId = GL.glGenTextures(1)
        # GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(self.activeTexture)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureId)

        # need to map ALPHA-ALPHA and use the alpha channel (.w) in the shader
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_ALPHA,
                        self._fontArray.shape[1], self._fontArray.shape[0],
                        0,
                        GL.GL_ALPHA, GL.GL_UNSIGNED_BYTE, self._fontArray)

        # nearest is the quickest gl plotting and gives a slightly brighter image
        # GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        # GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)

        # the following 2 lines generate a multitexture mipmap - shouldn't need here
        # GL.glTexParameteri( GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR )
        # GL.glGenerateMipmap( GL.GL_TEXTURE_2D )
        GL.glDisable(GL.GL_TEXTURE_2D)

    def _buildFont(self, _fontID, _startRow, _kerningRow, _nextRow, scale, fontTransparency):

        fullFontNameString = _fontID
        fontSizeString = fullFontNameString.split()[-1]

        _fontSize = int(int(fontSizeString.replace('pt', '')) / scale)
        _glyphs = self.fontGlyph[_fontSize] = AttrDict()

        _glyphs.fontName = fullFontNameString.replace(fontSizeString, '').strip()
        _glyphs.fontSize = _fontSize

        _glyphs._parent = self
        _glyphs.glyphs = [None] * 256
        _glyphs.width = 0
        _glyphs.height = 0
        _glyphs.spaceWidth = 0
        _glyphs.fontTransparency = fontTransparency

        # texture sizes
        dx = 1.0 / float(self.fontPNG.shape[1])
        dy = 1.0 / float(self.fontPNG.shape[0])

        for row in range(_startRow + 1, _kerningRow):
            line = self.fontInfo[row]

            lineVals = [int(ll) for ll in line.split()]
            if len(lineVals) == 9:
                chrNum, x, y, tx, ty, px, py, gw, gh = lineVals

                # only keep the simple chars for the minute
                if chrNum < 256:
                    w = tx + LEFTBORDER + RIGHTBORDER
                    h = ty + TOPBORDER + BOTTOMBORDER

                    _kerns = [0] * 256
                    _glyphs.glyphs[chrNum] = GLGlyphTuple(x, y, tx, ty, px, py, gw, gh, _kerns,
                                                          # coordinates in the texture
                                                          x * dx,
                                                          (y + h) * dy,
                                                          (x + w) * dx,
                                                          y * dy,
                                                          # coordinates mapped to the quad
                                                          px,
                                                          gh - (py + h),
                                                          px + (w),
                                                          gh - py
                                                          )
                    if chrNum == 65:
                        # use 'A' for the referencing the tab size
                        _glyphs.width = gw
                        _glyphs.height = gh
                        _glyphs.charWidth = gw
                        _glyphs.charHeight = gh

                    if chrNum == 32:
                        # store the width of the space character
                        _glyphs.spaceWidth = gw

        # fill the kerning lists
        for row in range(_kerningRow + 1, _nextRow):
            line = self.fontInfo[row]

            lineVals = [int(ll) for ll in line.split()]
            chrNum, chrNext, val = lineVals

            # set the kerning for valid values
            if (32 < chrNum < 256) and (32 < chrNext < 256):
                _glyphs.glyphs[chrNum].GlyphKerns[chrNext] = val

    def get_kerning(self, fromChar, prevChar, glyphs):
        """Get the kerning required between the characters
        """
        _glyph = glyphs[ord(fromChar)]
        if _glyph:
            return _glyph.GlyphKerns[ord(prevChar)]

        return 0

    def __str__(self):
        """Information string for the font
        """
        string = super().__str__()
        _fontSizes = [','.join(_glyph.fontSize for _glyph in self.fontGlyph.values())]
        string = '%s; name = %s; size = %s; file = %s' % (string, self.fontName, _fontSizes, self.fontFile)
        return string

    def closestFont(self, size):
        """Get the closest font to the required size
        """
        _size = min(list(self.fontGlyph.keys()), key=lambda x: abs(x - size))
        return self.fontGlyph[_size]


class GLString(GLVertexArray):
    def __init__(self, text=None, font=None, obj=None, colour=(1.0, 1.0, 1.0, 1.0),
                 x=0.0, y=0.0,
                 ox=0.0, oy=0.0,
                 angle=0.0, width=None, height=None,
                 GLContext=None, blendMode=True,
                 clearArrays=False, serial=None, pixelScale=None,
                 alias=0):
        """
        Create a GLString object for drawing text to the GL window
        :param text:
        :param font:
        :param obj:
        :param colour:
        :param x:
        :param y:
        :param ox:
        :param oy:
        :param angle: angle in degrees, negative is anti-clockwise
        :param width:
        :param height:
        :param GLContext:
        :param blendMode:
        :param clearArrays:
        :param serial:
        :param pixelScale:
        """
        super().__init__(renderMode=GLRENDERMODE_DRAW, blendMode=blendMode,
                         GLContext=GLContext, drawMode=GL.GL_TRIANGLES,
                         dimension=2, clearArrays=clearArrays)
        if text is None:
            text = ''
        self.text = text
        self.font = font
        self.stringObject = obj
        # self.pid = obj.pid if hasattr(obj, 'pid') else None
        self.serial = serial
        self.colour = colour
        self._position = (x, y)
        self._offset = (ox, oy)
        self._angle = (3.1415926535 / 180) * angle
        self._scale = pixelScale or GLContext.viewports.devicePixelRatio  # add scale here to render from a larger font?
        #                                                                   - may need different offsets
        #                                                                   - also need to modify getSmallFont
        self._alias = alias
        self.buildString()

    def buildString(self):
        """Build the string
        """
        text = self.text
        font = self.font
        colour = self.colour
        x, y = self._position
        ox, oy = self._offset
        # self.pid = self.stringObject.pid if hasattr(self.stringObject, 'pid') else None

        _glyphs = font.glyphs
        self.height = font.height
        self.width = 0

        _validText = [tt for tt in text if _glyphs[ord(tt)] and ord(tt) > 32]
        lenText = len(_validText)

        # allocate space for all the letters, bad are discarded, spaces/tabs are not stored
        self.indices = np.empty(lenText * 6, dtype=np.uint32)
        self.vertices = np.empty(lenText * 8, dtype=np.float32)
        self.texcoords = np.empty(lenText * 8, dtype=np.float32)

        # self.attribs = np.zeros((len(text) * 4, 2), dtype=np.float32)
        # self.offsets = np.zeros((len(text) * 4, 2), dtype=np.float32)

        self.indexOffset = 0
        penX = 0
        penY = 0  # offset the string from (0, 0) and use (x, y) in shader
        prev = None

        if self._angle != 0.0:
            cs, sn = math.cos(self._angle), math.sin(self._angle)
        # rotate = np.matrix([[cs, sn], [-sn, cs]])

        i = 0
        for charCode in text:
            c = ord(charCode)
            glyph = _glyphs[c]

            if not glyph:
                # discard characters that are undefined
                continue

            if (c > 32):  # visible characters

                kerning = font._parent.get_kerning(charCode, prev, _glyphs) if (prev and ord(prev) > 32) else 0

                x0 = penX + glyph.GlyphPX0 + kerning
                y0 = penY + glyph.GlyphPY0
                x1 = penX + glyph.GlyphPX1 + kerning
                y1 = penY + glyph.GlyphPY1
                u0 = glyph.GlyphTX0
                v0 = glyph.GlyphTY0
                u1 = glyph.GlyphTX1
                v1 = glyph.GlyphTY1
                i4 = i * 4
                i6 = i * 6
                i8 = i * 8

                if self._angle == 0.0:
                    # horizontal text
                    self.vertices[i8:i8 + 8] = (x0, y0, x0, y1, x1, y1, x1, y0)  # pixel coordinates in string
                else:
                    # apply rotation to the text
                    xbl, ybl = x0 * cs + y0 * sn, -x0 * sn + y0 * cs
                    xtl, ytl = x0 * cs + y1 * sn, -x0 * sn + y1 * cs
                    xtr, ytr = x1 * cs + y1 * sn, -x1 * sn + y1 * cs
                    xbr, ybr = x1 * cs + y0 * sn, -x1 * sn + y0 * cs

                    self.vertices[i8:i8 + 8] = (xbl, ybl, xtl, ytl, xtr, ytr, xbr, ybr)  # pixel coordinates in string

                self.indices[i6:i6 + 6] = (i4, i4 + 1, i4 + 2, i4, i4 + 2, i4 + 3)
                self.texcoords[i8:i8 + 8] = (u0, v0, u0, v1, u1, v1, u1, v0)

                # # store the attribs and offsets
                # self.attribs[i * 4:i * 4 + 4] = attribs
                # self.offsets[i * 4:i * 4 + 4] = offsets

                penX += glyph.GlyphOrigW + kerning
                i += 1

            elif (c == 32):  # space
                penX += font.spaceWidth

            elif (c == 10):  # newline
                penX = 0
                penY = 0  # penY + font.height
                # for vt in self.vertices:
                #   vt[1] = vt[1] + font.height

                # occasional strange - RuntimeWarning: invalid value encountered in add
                # self.vertices[:, 1] += font.height
                # move all characters up by font height, centred bottom-left
                self.vertices[1:i * 8:2] += font.height
                self.height += font.height

            elif (c == 9):  # tab
                penX += 4 * font.spaceWidth

            self.width = max(self.width, penX)

            # penY = penY + glyph[GlyphHeight]
            prev = charCode

        if not (0.9999 < self._scale < 1.0001):
            # apply font scaling for hi-res displays
            self.vertices /= self._scale
            self.height /= self._scale
            self.width /= self._scale

        # set the offsets for the characters to the desired coordinates
        self.numVertices = len(self.vertices) // 2
        self.attribs = np.array((x + ox, y + oy, self._alias) * self.numVertices, dtype=np.float32)
        self.offsets = np.array((x, y) * self.numVertices, dtype=np.float32)
        self.stringOffset = None  # (ox, oy)

        # set the colour for the whole string
        self.colors = np.array(colour * self.numVertices, dtype=np.float32)

        # create VBOs from the arrays
        self.defineTextArrayVBO()

        # total width of text - probably don't need
        # width = penX - glyph.advance[0] / 64.0 + glyph.size[0]

    def drawTextArray(self):
        # self._GLContext.globalGL._shaderProgramTex.setTextureID(self.font._parent.activeTextureNum)
        super().drawTextArray()

    def drawTextArrayVBO(self, enableClientState=False, disableClientState=False):
        # self._GLContext.globalGL._shaderProgramTex.setTextureID(self.font._parent.activeTextureNum)
        super().drawTextArrayVBO()

    def setStringColour(self, col):
        self.colour = col
        self.colors = np.array(self.colour * self.numVertices, dtype=np.float32)

    def setStringHexColour(self, hexColour, alpha=1.0):
        col = hexToRgbRatio(hexColour)
        self.colour = (*col, alpha)
        self.colors = np.array(self.colour * self.numVertices, dtype=np.float32)

    def setStringOffset(self, attrib):
        for pp in range(0, self.numVertices):
            self.attribs[3 * pp:3 * pp + 2] = self.offsets[2 * pp:2 * pp + 2] + attrib
