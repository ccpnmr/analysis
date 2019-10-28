"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2018-12-20 14:07:59 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.0 $"
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
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLVertexArray, GLRENDERMODE_DRAW
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import LEFTBORDER, RIGHTBORDER, TOPBORDER, BOTTOMBORDER
from ccpn.util.Colour import hexToRgbRatio

try:
    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL CCPN",
                                   "PyOpenGL must be installed to run this example.")
    sys.exit(1)

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

class CcpnGLFont():
    def __init__(self, fileName=None, base=0, fontTransparency=None, activeTexture=0, scale=None):
        self.fontName = None
        self.fontGlyph = [None] * 256
        self.base = base
        self.scale=scale

        if scale == None:
            raise Exception('scale must be defined for font %s ' % fileName)
        # print('open font', fileName)

        with open(fileName, 'r') as op:
            self.fontInfo = op.read().split('\n')

        # no checking yet
        self.fontFile = self.fontInfo[FONT_FILE].replace('textures: ', '')
        self.fontPNG = imread(os.path.join(os.path.dirname(fileName), self.fontFile))

        fullFontNameString = self.fontInfo[FULL_FONT_NAME]
        fontSizeString = fullFontNameString.split()[-1]

        self.fontName = fullFontNameString.replace(fontSizeString,'').strip()
        self.fontSize = int(fontSizeString.replace('pt',''))/scale

        self.width = 0
        self.height = 0
        self.spaceWidth = 0
        self.activeTexture = GL.GL_TEXTURE0 + activeTexture
        self.activeTextureNum = activeTexture
        self.fontTransparency = fontTransparency

        row = 2
        exitDims = False

        # texture sizes
        dx = 1.0 / float(self.fontPNG.shape[1])
        dy = 1.0 / float(self.fontPNG.shape[0])
        hdx = dx / 10.0
        hdy = dy / 10.0

        line = ''
        chrNum = 0

        while exitDims is False and row < len(self.fontInfo):
            line = self.fontInfo[row]
            # print (line)
            if line.startswith('kerning'):
                exitDims = True
            else:
                try:
                    lineVals = [int(ll) for ll in line.split()]
                    if len(lineVals) == 9:
                        chrNum, a0, b0, c0, d0, e0, f0, g0, h0 = lineVals

                        # only keep the simple chars for the minute
                        if chrNum < 256:
                            self.fontGlyph[chrNum] = {}
                            self.fontGlyph[chrNum][GlyphXpos] = a0
                            self.fontGlyph[chrNum][GlyphYpos] = b0
                            self.fontGlyph[chrNum][GlyphWidth] = c0
                            self.fontGlyph[chrNum][GlyphHeight] = d0
                            self.fontGlyph[chrNum][GlyphXoffset] = e0
                            self.fontGlyph[chrNum][GlyphYoffset] = f0
                            self.fontGlyph[chrNum][GlyphOrigW] = g0
                            self.fontGlyph[chrNum][GlyphOrigH] = h0
                            self.fontGlyph[chrNum][GlyphKerns] = {}

                            # TODO:ED okay for now, but need to check for rounding errors

                            # calculate the coordinated within the texture
                            x = a0  # +0.5           # self.fontGlyph[chrNum][GlyphXpos])   # try +0.5 for centre of texel
                            y = b0  # -0.005           # self.fontGlyph[chrNum][GlyphYpos])
                            px = e0  # self.fontGlyph[chrNum][GlyphXoffset]
                            py = f0  # self.fontGlyph[chrNum][GlyphYoffset]
                            w = c0 + LEFTBORDER + RIGHTBORDER  # -1           # self.fontGlyph[chrNum][GlyphWidth]+1       # if 0.5 above, remove the +1
                            h = d0 + TOPBORDER + BOTTOMBORDER  # + 0.5  # self.fontGlyph[chrNum][GlyphHeight]+1
                            gw = g0  # self.fontGlyph[chrNum][GlyphOrigW]
                            gh = h0  # self.fontGlyph[chrNum][GlyphOrigH]

                            # coordinates in the texture
                            self.fontGlyph[chrNum][GlyphTX0] = x * dx
                            self.fontGlyph[chrNum][GlyphTY0] = (y + h) * dy
                            self.fontGlyph[chrNum][GlyphTX1] = (x + w) * dx
                            self.fontGlyph[chrNum][GlyphTY1] = y * dy

                            # coordinates mapped to the quad
                            self.fontGlyph[chrNum][GlyphPX0] = px
                            self.fontGlyph[chrNum][GlyphPY0] = gh - (py + h)
                            self.fontGlyph[chrNum][GlyphPX1] = px + (w)
                            self.fontGlyph[chrNum][GlyphPY1] = gh - py

                            if chrNum == 65:
                                # use 'A' for the referencing the tab size
                                self.width = gw / self.scale
                                self.height = gh /self.scale

                            if chrNum == 32:
                                # store the width of the space character
                                self.spaceWidth = gw /self.scale

                    else:
                        exitDims = True
                except:
                    exitDims = True
            row += 1

        if line.startswith('kerning'):
            # kerning list is included

            exitKerns = False
            while exitKerns is False and row < len(self.fontInfo):
                line = self.fontInfo[row]
                # print(line)

                try:
                    lineVals = [int(ll) for ll in line.split()]
                    chrNum, chrNext, val = lineVals

                    if chrNum < 256 and chrNext < 256:
                        self.fontGlyph[chrNum][GlyphKerns][chrNext] = val
                except:
                    exitKerns = True
                row += 1

        # GST Dead Code
        # width, height, ascender, descender = 0, 0, 0, 0
        # for c in range(0, 256):
        #     if chrNum < 256 and self.fontGlyph[chrNum]:
        #         width = max(width, self.fontGlyph[chrNum][GlyphOrigW])
        #         height = max(height, self.fontGlyph[chrNum][GlyphOrigH])
        #
        # height = height / scale
        # width =  width / scale
        #
        # width, height, ascender, descender = None, None, None, None

        self.textureId = GL.glGenTextures(1)
        # GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(self.activeTexture)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureId)

        if fontTransparency:
            for fontI in self.fontPNG:
                for fontJ in fontI:
                    fontJ[3] = int(fontJ[3] * fontTransparency)

        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA,
                        self.fontPNG.shape[1], self.fontPNG.shape[0],
                        0,
                        GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, self.fontPNG.data)

        # generate a MipMap to cope with smaller text (may not be needed soon)
        # GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        # GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)

        # the following 2 lines generate a multitexture mipmap - improves fonts for retina/non-retina displays
        GL.glTexParameteri( GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR)
        GL.glGenerateMipmap( GL.GL_TEXTURE_2D )
        GL.glDisable(GL.GL_TEXTURE_2D)


    def get_kerning(self, fromChar, prevChar):
        if self.fontGlyph[ord(fromChar)]:
            if prevChar and ord(prevChar) in self.fontGlyph[ord(fromChar)][GlyphKerns]:
                return self.fontGlyph[ord(fromChar)][GlyphKerns][ord(prevChar)]

        return 0

    def __str__(self):
        string = super().__str__()
        string = '%s name = %s size = %i file = %s ' % (string, self.fontName, self.fontSize, self.fontFile)
        return string


class GLString(GLVertexArray):
    def __init__(self, text=None, font=None, obj=None, colour=(1.0, 1.0, 1.0, 1.0),
                 x=0.0, y=0.0,
                 ox=0.0, oy=0.0,
                 angle=0.0, width=None, height=None, GLContext=None, blendMode=True,
                 clearArrays=False, serial=None, scale=2):
        super().__init__(renderMode=GLRENDERMODE_DRAW, blendMode=blendMode,
                         GLContext=GLContext, drawMode=GL.GL_TRIANGLES,
                         dimension=2, clearArrays=clearArrays)
        if text is None:
            text = ''

        self.text = text
        self.font = font
        self.object = obj
        self.pid = obj.pid if hasattr(obj, 'pid') else None
        self.serial = serial
        self.colour = colour
        self._position = (x, y)
        self._offset = (ox, oy)
        self.scale = scale

        self.buildString()

    def buildString(self):
        """Build the string
        """
        text = self.text
        font = self.font
        colour = self.colour
        x, y = self._position
        ox, oy = self._offset
        self.pid = self.object.pid if hasattr(self.object, 'pid') else None

        # each object can have a unique serial number if required
        self.height = font.height
        self.width = 0

        lenText = len(text)

        # allocate space for all the letters
        self.indices = np.zeros(lenText * 6, dtype=np.uint32)
        self.vertices = np.zeros(lenText * 8, dtype=np.float32)
        self.colors = np.empty(lenText * 16, dtype=np.float32)
        self.texcoords = np.empty(lenText * 8, dtype=np.float32)

        # self.attribs = np.zeros((len(text) * 4, 2), dtype=np.float32)
        # self.offsets = np.zeros((len(text) * 4, 2), dtype=np.float32)

        self.indexOffset = 0
        penX = 0
        penY = 0  # offset the string from (0, 0) and use (x, y) in shader
        prev = None

        # cs, sn = math.cos(angle), math.sin(angle)
        # rotate = np.matrix([[cs, sn], [-sn, cs]])

        for i, charCode in enumerate(text):
            c = ord(charCode)
            glyph = font.fontGlyph[c]

            # if glyph or c == 10 or c == 9:  # newline and tab

            if (c > 32):  # visible characters

                kerning = font.get_kerning(charCode, prev)

                x0 = penX + glyph[GlyphPX0] + kerning  # penX + glyph.offset[0] + kerning
                y0 = penY + glyph[GlyphPY0]  # penY + glyph.offset[1]
                x1 = penX + glyph[GlyphPX1] + kerning  # x0 + glyph.size[0]
                y1 = penY + glyph[GlyphPY1]  # y0 - glyph.size[1]
                u0 = glyph[GlyphTX0]  # glyph.texcoords[0]
                v0 = glyph[GlyphTY0]  # glyph.texcoords[1]
                u1 = glyph[GlyphTX1]  # glyph.texcoords[2]
                v1 = glyph[GlyphTY1]  # glyph.texcoords[3]

                # # apply rotation to the text
                # xbl, ybl = x0 * cs + y0 * sn, -x0 * sn + y0 * cs
                # xtl, ytl = x0 * cs + y1 * sn, -x0 * sn + y1 * cs
                # xtr, ytr = x1 * cs + y1 * sn, -x1 * sn + y1 * cs
                # xbr, ybr = x1 * cs + y0 * sn, -x1 * sn + y0 * cs

                # index = i * 4
                i4 = i * 4
                i6 = i * 6
                i8 = i * 8
                i16 = i * 16
                # indices = [index, index + 1, index + 2, index, index + 2, index + 3]
                # vertices = [x0, y0], [x0, y1], [x1, y1], [x1, y0]
                # texcoords = [[u0, v0], [u0, v1], [u1, v1], [u1, v0]]
                # colors = [color, ] * 4

                # attribs = [[x, y], [x, y], [x, y], [x, y]]
                # offsets = [[x, y], [x, y], [x, y], [x, y]]
                self.vertices[i8:i8 + 8] = (x0/self.scale, y0/self.scale, x0/self.scale, y1/self.scale,
                                            x1/self.scale, y1/self.scale, x1/self.scale, y0/self.scale)
                self.indices[i6:i6 + 6] = (i4, i4 + 1, i4 + 2, i4, i4 + 2, i4 + 3)
                self.texcoords[i8:i8 + 8] = (u0, v0, u0, v1, u1, v1, u1, v0)
                self.colors[i16:i16 + 16] = colour * 4

                # self.attribs[i * 4:i * 4 + 4] = attribs
                # self.offsets[i * 4:i * 4 + 4] = offsets

                penX = penX + glyph[GlyphOrigW] + kerning
                self.width = max(self.width, penX)

            if (c == 32):  # space
                # print('space width',font.spaceWidth)
                # print(penX)
                penX += font.spaceWidth
                # print(font.spaceWidth)
                # print(penX)
                # print(self.width)
                self.width = max(self.width, penX)
                # print(self.width)
                # print('end space')

            elif (c == 10):  # newline
                penX = 0
                penY = 0  # penY + font.height
                # for vt in self.vertices:
                #   vt[1] = vt[1] + font.height

                # occasional strange - RuntimeWarning: invalid value encountered in add
                # self.vertices[:, 1] += font.height
                self.vertices[1::2] += font.height
                self.height += font.height

            elif (c == 9):  # tab
                penX = penX + 4 * font.width
                self.width = max(self.width, penX)

            # penY = penY + glyph[GlyphHeight]
            prev = charCode
        # print(text,self.width, len(text))
        # set the offsets for the characters top the desired coordinates
        self.numVertices = len(self.vertices) // 2
        self.attribs = np.array((x + ox, y + oy) * self.numVertices, dtype=np.float32)
        self.offsets = np.array((x, y) * self.numVertices, dtype=np.float32)
        self.stringOffset = None  # (ox, oy)

        # create VBOs from the arrays
        self.defineTextArrayVBO(enableVBO=True)

        # total width of text - probably don't need
        # width = penX - glyph.advance[0] / 64.0 + glyph.size[0]

    def drawTextArray(self):
        self._GLContext.globalGL._shaderProgramTex.setGLUniform1i('texture', self.font.activeTextureNum)
        super().drawTextArray()

    def drawTextArrayVBO(self, enableVBO=False, enableClientState=False, disableClientState=False):
        self._GLContext.globalGL._shaderProgramTex.setGLUniform1i('texture', self.font.activeTextureNum)
        super().drawTextArrayVBO(enableVBO=enableVBO)

    def setStringColour(self, col):
        self.colour = col
        self.colors = np.array(col * self.numVertices, dtype=np.float32)

    def setStringHexColour(self, hexColour, alpha=1.0):
        col = hexToRgbRatio(hexColour)
        self.colour = (*col, alpha)
        self.colors = np.array((*col, alpha) * self.numVertices, dtype=np.float32)

    def setStringOffset(self, attrib):
        self.attribs = self.offsets + np.array(attrib * self.numVertices, dtype=np.float32)
