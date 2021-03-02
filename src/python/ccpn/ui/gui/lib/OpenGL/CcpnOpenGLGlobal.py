"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-03-02 13:57:32 +0000 (Tue, March 02, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 13:28:13 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import sys
import numpy as np
from PyQt5 import QtWidgets


from ccpn.ui.gui.lib.OpenGL import GL, GLU, GLUT

from ccpn.util.decorators import singleton
from ccpn.framework.PathsAndUrls import openGLFontsPath
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLFonts import CcpnGLFont
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLShader import ShaderProgramABC


GLFONT_DEFAULT = 'OpenSans-Regular'
GLFONT_SUBSTITUTE = 'OpenSans-Regular'
GLFONT_DEFAULTSIZE = 13  # moved to preferences.appearance
_OLDGLFONT_SIZES = [10, 11, 12, 13, 14, 16, 18, 20, 22, 24]
GLFONT_DICT = {}

GLFONT_FILE = 0
GLFONT_NAME = 1
GLFONT_SIZE = 2
GLFONT_SCALE = 3

GLFONT_TRANSPARENT = 'Transparent'
GLFONT_DEFAULTFONTFILE = 'glAllFonts.fnt'
GLPIXELSHADER = 'GLPixelShader'
GLTEXTSHADER = 'GLTextShader'


@singleton
class GLGlobalData(QtWidgets.QWidget):
    """
    Class to handle the common information between all the GL widgets
    """

    def __init__(self, parent=None, mainWindow=None):  #, strip=None, spectrumDisplay=None):
        """
        Initialise the global data

        :param parent:
        :param mainWindow:
        :param strip:
        :param spectrumDisplay:
        """

        super(GLGlobalData, self).__init__()
        self._parent = parent
        self.mainWindow = mainWindow
        # self.strip = strip
        # self._spectrumDisplay = spectrumDisplay

        self.fonts = {}
        self.loadFonts()

        self.shaders = None
        self.initialiseShaders()
        self._glClientIndex = 0

    def getNextClientIndex(self):
        self._glClientIndex += 1
        return 1  #self._glClientIndex

    def loadFonts(self):
        """Load all the necessary GLFonts
        """
        self.fonts[GLFONT_DEFAULT] = CcpnGLFont(openGLFontsPath / GLFONT_DEFAULTFONTFILE, activeTexture=0, scale=1.0)

        _foundFonts = self.fonts[GLFONT_DEFAULT].fontGlyph

        # find all the fonts ion the list that have a matching 2* size, for double resolution retina displays
        self.GLFONT_SIZES = [_size for _size in _foundFonts.keys() if _size * 2 in _foundFonts.keys()]

        # set the current size from the preferences
        _size = self.mainWindow.application.preferences.appearance.spectrumDisplayFontSize
        if _size in self.GLFONT_SIZES:
            self.glSmallFontSize = _size
        else:
            self.glSmallFontSize = GLFONT_DEFAULTSIZE

    def initialiseShaders(self):
        """Initialise the shaders
        """
        # add some shaders to the global data
        self.shaders = {}
        for _shader in (PixelShader, TextShader):
            _new = _shader()
            self.shaders[_new.name] = _new

        self._shaderProgram1 = self.shaders['pixelShader']
        self._shaderProgramTex = self.shaders['textShader']


class PixelShader(ShaderProgramABC):
    """
    Main pixel shader

    A very simple shader, uses the projection/viewport matrices to calculate the gl_Position,
    and passes through the gl_Color to set the pixel.
    """

    name = 'pixelShader'
    CCPNSHADER = True

    # simple shader for standard plotting of contours
    # vertex shader to determine the co-ordinates
    vertexShader = """
        #version 120

        uniform mat4 pMatrix;
        uniform mat4 mvMatrix;
        varying vec4 _FC;

        void main()
        {
          // calculate the position
          gl_Position = (pMatrix * mvMatrix) * gl_Vertex;
          _FC = gl_Color;
        }
        """

    # fragment shader to set the colour
    fragmentShader = """
        #version 120

        varying vec4  _FC;

        void main()
        {
          // set the pixel colour
          gl_FragColor = _FC;
        }
        """

    # attribute list for main shader
    attributes = {'pMatrix' : (16, np.float32),
                  'mvMatrix': (16, np.float32),
                  }

    def setPMatrix(self, matrix):
        """Set the contents of projection pMatrix
        :param matrix: consisting of 16 float32 elements
        """
        self.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, matrix)

    def setMVMatrix(self, matrix):
        """Set the contents of viewport mvMatrix
        :param matrix: consisting of 16 float32 elements
        """
        self.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, matrix)


class TextShader(ShaderProgramABC):
    """
    Main Text shader

    Shader for plotting text, uses a billboard technique by using an _offset to determine pixel positions
    Colour of the pixel is set by glColorPointer array.
    Alpha value is grabbed from the texture to give anti-aliasing and modified by the 'alpha' attribute to
    affect overall transparency.
    """

    name = 'textShader'
    CCPNSHADER = True

    # shader for plotting anti-aliased text to the screen
    vertexShader = """
        #version 120

        uniform mat4    pTexMatrix;
        uniform vec4    axisScale;
        uniform vec2    stackOffset;
        varying vec4    _FC;
        varying vec2    _texCoord;
        attribute vec2  _offset;

        void main()
        {
            gl_Position = pTexMatrix * ((gl_Vertex * axisScale) + vec4(_offset + stackOffset, 0.0, 0.0));

            _texCoord = gl_MultiTexCoord0.st;
            _FC = gl_Color;
        }
        """

    # fragment shader to determine shading from the texture alpha value and the 'alpha' attribute
    fragmentShader = """
        #version 120

        uniform sampler2D   texture;
        uniform vec4        background;
        uniform int         blendEnabled;
        uniform float       alpha;
        varying vec4        _FC;
        vec4                _texFilter;
        varying vec2        _texCoord;
        float               _opacity;

        void main()
        {
          _texFilter = texture2D(texture, _texCoord);
          // colour for blending enabled
          _opacity = _texFilter.w * alpha;

          if (blendEnabled != 0)
            // multiply the character fade by the color fade to give the actual transparency
            gl_FragColor = vec4(_FC.xyz, _FC.w * _opacity);

          else   
            // plot a background box around the character
            gl_FragColor = vec4((_FC.xyz * _opacity) + (1.0 - _opacity) * background.xyz, 1.0);
        }
        """

    attributes = {'pTexMatrix'  : (16, np.float32),
                  'axisScale'   : (4, np.float32),
                  'stackOffset' : (2, np.float32),
                  'texture'     : (1, np.uint32),
                  'background'  : (4, np.float32),
                  'blendEnabled': (1, np.uint32),
                  'alpha'       : (1, np.float32),
                  }

    def setPTexMatrix(self, matrix):
        """Set the contents of projection pTexMatrix
        :param matrix: consisting of 16 float32 elements
        """
        self.setGLUniformMatrix4fv('pTexMatrix', 1, GL.GL_FALSE, matrix)

    def setAxisScale(self, axisScale):
        """Set the axisScale values
        :param axisScale: consisting of 4 float32 elements
        """
        self.setGLUniform4fv('axisScale', 1, axisScale)

    def setStackOffset(self, stackOffset):
        """Set the stacking value for the 1d widget
        :param stackOffset: consisting of 2 float32 elements, the stacking offset in thje X, Y dimensions
        """
        self.setGLUniform2fv('stackOffset', 1, stackOffset)

    def setTextureID(self, textureID):
        """Set the texture ID, determines which texture the text bitmaps are taken from
        :param textureID: uint32
        """
        self.setGLUniform1i('texture', textureID)

    def setBackground(self, colour):
        """Set the background colour, for use with the solid text
        :param colour: consisting of 4 float32 elements
        """
        self.setGLUniform4fv('background', 1, colour)

    def setBlendEnabled(self, blendEnabled):
        """Set the blend enabled flag, determines whether the characters are
        surrounded with a solid background block
        :param blendEnabled: single uint32
        """
        self.setGLUniform1i('blendEnabled', blendEnabled)

    def setAlpha(self, alpha):
        """Set the alpha value, a multiplier to the transparency 0 - completely transparent; 1 - solid
        :param alpha: single float32
        """
        self.setGLUniform1f('alpha', alpha)
