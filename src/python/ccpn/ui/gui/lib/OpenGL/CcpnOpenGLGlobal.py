"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
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
__dateModified__ = "$dateModified: 2022-01-27 15:24:37 +0000 (Thu, January 27, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 13:28:13 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from PyQt5 import QtWidgets, QtGui
from ccpn.ui.gui.lib.OpenGL import GL
from ccpn.util.decorators import singleton
from ccpn.framework.PathsAndUrls import openGLFontsPath
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLFonts import CcpnGLFont
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLShader import ShaderProgramABC
from ccpn.util.Logging import getLogger


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

    def __init__(self, parent=None, mainWindow=None):
        """
        Initialise the global data

        :param parent:
        :param mainWindow:
        """

        super(GLGlobalData, self).__init__()
        self._parent = parent
        self.mainWindow = mainWindow

        self.fonts = {}
        self.shaders = None

        _ver = QtGui.QOpenGLVersionProfile()
        self._GLVersion = GL.glGetString(GL.GL_VERSION)
        self._GLShaderVersion = GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION)
        getLogger().debug(f"OpenGL: {self._GLVersion.decode('utf-8')}")
        getLogger().debug(f"GLSL: {self._GLShaderVersion.decode('utf-8')}")
        _format = QtGui.QSurfaceFormat()
        getLogger().debug(f"Surface: {_format.version()}")

        self.loadFonts()
        self.initialiseShaders()

        self._texturesBound = False

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

    def bindFonts(self):
        """Bind the font textures to the GL textures
        MUST be called inside GL current context, i.e., after GL.makeCurrent or inside initializeGL, paintGL
        """
        if not self._texturesBound:
            for name, fnt in self.fonts.items():
                fnt._bindFontTexture()
            self._texturesBound = True

    def initialiseShaders(self):
        """Initialise the shaders
        """
        # add some shaders to the global data
        self.shaders = {}
        for _shader in (PixelShader, TextShader, AliasedPixelShader, AliasedTextShader):
            _new = _shader()
            self.shaders[_new.name] = _new

        self._shaderProgram1 = self.shaders['pixelShader']
        self._shaderProgramTex = self.shaders['textShader']
        self._shaderProgramAlias = self.shaders['aliasedPixelShader']
        self._shaderProgramTexAlias = self.shaders['aliasedTextShader']


class PixelShader(ShaderProgramABC):
    """
    Pixel shader for contour plotting

    A very simple shader, uses the projection/viewport matrices to calculate the gl_Position,
    and passes through the gl_Color to set the pixel.
    """

    name = 'pixelShader'
    CCPNSHADER = True

    # vertex shader to determine the co-ordinates
    vertexShader = """
        #version 120

        uniform mat4 pMatrix;
        uniform mat4 mvMatrix;
        varying vec4 _FC;

        void main()
        {
            // calculate the position
            gl_Position = pMatrix * mvMatrix * gl_Vertex;
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

    # attribute list for shader
    attributes = {'pMatrix' : (16, np.float32),
                  'mvMatrix': (16, np.float32),
                  }

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # methods available for shader

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


class AliasedPixelShader(PixelShader):
    """
    Pixel shader for aliased peak plotting

    Uses the projection/viewport matrices to calculate the gl_Position,
    and passes through the gl_Color to set the pixel.
    gl_Color is modified for peaks at different aliased positions
    """

    name = 'aliasedPixelShader'
    CCPNSHADER = True

    # vertex shader to determine the co-ordinates
    vertexShader = """
        #version 120

        uniform   mat4  pMatrix;
        uniform   mat4  mvMatrix;
        attribute float alias;
        uniform   float aliasPosition;
        varying   float _aliased;
        varying   vec4  _FC;
        
        void main()
        {
            // calculate the position, set shading value
            gl_Position = pMatrix * mvMatrix * vec4(gl_Vertex.xy, 0.0, 1.0);
            _FC = gl_Color;
            _aliased = (aliasPosition - alias);
        }
        """

    # fragment shader to set the colour
    fragmentShader = """
        #version 120

        uniform vec4  background;
        uniform float aliasShade;
        uniform int   aliasEnabled;
        varying vec4  _FC;
        varying float _aliased;
        
        void main()
        {
            // set the pixel colour
            if (abs(_aliased) < 0.5) {
                gl_FragColor = _FC;
            }
            else if (aliasEnabled != 0) {
                // set the colour if aliasEnabled (set opaque or set the alpha)
                gl_FragColor = (aliasShade * _FC) + (1 - aliasShade) * background;
                //gl_FragColor = vec4(_FC.xyz, _FC.w * aliasShade);
            }
            else {
                // skip the pixel
                discard;
            }
        }
        """

    # additional attribute list for shader
    _attributes = {
        'aliasPosition': (1, np.float32),
        'background'   : (4, np.float32),
        'aliasShade'   : (1, np.float32),
        'aliasEnabled' : (1, np.uint32),
        }

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # methods available for shader

    def __init__(self):
        self.attributes.update(self._attributes)
        super().__init__()

    def setAliasPosition(self, aliasX, aliasY):
        """Set the alias position:
        Used to calculate whether the current peak is in the aliased region
        :param aliasX: X alias region
        :param aliasY: Y alias region
        """
        self.setGLUniform1f('aliasPosition', getAliasSetting(aliasX, aliasY))

    def setBackground(self, colour):
        """Set the background colour, for use with the solid text
        colour is tuple/list of 4 float/np.float32 elements in range 0.0-1.0
        values outside range will be clipped
        :param colour: tuple/list
        """
        if len(colour) != 4 and not isinstance(colour, (list, tuple, type(np.array))):
            raise TypeError('colour must tuple/list/numpy.array of 4 elements')
        if not all(isinstance(col, (float, np.float32)) for col in colour):
            raise TypeError('colour must be tuple/list/numpy.array of float/np.float32')

        self.setGLUniform4fv('background', 1, np.clip(colour, [0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]))

    def setAliasShade(self, aliasShade):
        """Set the alias shade: a single float in range [0.0, 1.0]
        Used to determine visibility of aliased peaks, 0.0 -> background colour
        :param aliasShade: single float32
        """
        if not isinstance(aliasShade, (float, np.float32)):
            raise TypeError('aliasShade must be a float')
        value = float(np.clip(aliasShade, 0.0, 1.0))

        self.setGLUniform1f('aliasShade', value)

    def setAliasEnabled(self, aliasEnabled):
        """Set the alias enabled: bool True/False
        Used to determine visibility of aliased peaks, using aliasShade
        False = disable visibility of aliased peaks
        :param aliasEnabled: bool
        """
        if not isinstance(aliasEnabled, bool):
            raise TypeError('aliasEnabled must be a bool')
        value = 1 if aliasEnabled else 0

        self.setGLUniform1i('aliasEnabled', value)


def getAliasSetting(aliasX, aliasY):
    """Return the alias setting for alias value (aliasX, aliasY) for insertion into shader
    """
    if not isinstance(aliasX, int):
        raise TypeError('aliasX must be an int')
    if not isinstance(aliasY, int):
        raise TypeError('aliasY must be an int')

    # arbitrary value to pack into a single float
    return (256 * aliasX) + aliasY


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

        uniform   mat4  pTexMatrix;
        uniform   vec4  axisScale;
        uniform   vec2  stackOffset;
        varying   vec4  _FC;
        varying   vec2  _texCoord;
        attribute vec3  _offset;
        
        void main()
        {
            gl_Position = pTexMatrix * ((gl_Vertex * axisScale) + vec4(_offset.xy + stackOffset, 0.0, 0.0));

            _texCoord = gl_MultiTexCoord0.st;
            _FC = gl_Color;
        }
        """

    # fragment shader to determine shading from the texture alpha value and the 'alpha' attribute
    fragmentShader = """
        #version 120

        uniform sampler2D texture;
        uniform vec4      background;
        uniform int       blendEnabled;
        uniform float     alpha;
        varying vec4      _FC;
        varying vec2      _texCoord;
        vec4              _texFilter;
        float             _opacity;

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

    # attribute list for shader
    attributes = {'pTexMatrix'  : (16, np.float32),
                  'axisScale'   : (4, np.float32),
                  'stackOffset' : (2, np.float32),
                  'texture'     : (1, np.uint32),
                  'background'  : (4, np.float32),
                  'blendEnabled': (1, np.uint32),
                  'alpha'       : (1, np.float32),
                  }

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # methods available for shader

    def setPTexMatrix(self, matrix):
        """Set the contents of projection pTexMatrix
        :param matrix: consisting of 16 float32 elements
        """
        self.setGLUniformMatrix4fv('pTexMatrix', 1, GL.GL_FALSE, matrix)

    def setAxisScale(self, axisScale):
        """Set the axisScale values
        :param axisScale: consisting of 4 float32 elements
        """
        if len(axisScale) != 4 and not isinstance(axisScale, (list, tuple, type(np.array))):
            raise TypeError('axisScale must tuple/list/numpy.array of 4 elements')
        if not all(isinstance(val, (float, np.float32)) for val in axisScale):
            raise TypeError('axisScale must be tuple/list/numpy.array of float/np.float32')

        self.setGLUniform4fv('axisScale', 1, axisScale)

    def setStackOffset(self, stackOffset):
        """Set the stacking value for the 1d widget
        :param stackOffset: consisting of 2 float32 elements, the stacking offset in thje X, Y dimensions
        """
        if len(stackOffset) != 2 and not isinstance(stackOffset, (list, tuple, type(np.array))):
            raise TypeError('stackOffset must tuple/list/numpy.array of 2 elements')
        if not all(isinstance(val, (float, np.float32)) for val in stackOffset):
            raise TypeError('stackOffset must be tuple/list/numpy.array of float/np.float32')

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
        if len(colour) != 4 and not isinstance(colour, (list, tuple, type(np.array))):
            raise TypeError('colour must tuple/list/numpy.array of 4 elements')
        if not all(isinstance(col, (float, np.float32)) for col in colour):
            raise TypeError('colour must be tuple/list/numpy.array of float/np.float32')

        self.setGLUniform4fv('background', 1, colour)

    def setBlendEnabled(self, blendEnabled):
        """Set the blend enabled flag, determines whether the characters are
        surrounded with a solid background block
        :param blendEnabled: single uint32
        """
        if not isinstance(blendEnabled, bool):
            raise TypeError('blendEnabled must be a bool')
        value = 1 if blendEnabled else 0

        self.setGLUniform1i('blendEnabled', value)

    def setAlpha(self, alpha):
        """Set the alpha value, a multiplier to the transparency 0 - completely transparent; 1 - solid
        alpha to clipped to value [0.0, 1.0]
        :param alpha: single float32
        """
        if not isinstance(alpha, (float, np.float32)):
            raise TypeError('value must be a float')
        value = float(np.clip(alpha, 0.0, 1.0))

        self.setGLUniform1f('alpha', value)


class AliasedTextShader(TextShader):
    """
    Text shader for displaying text in aliased regions

    Shader for plotting text, uses a billboard technique by using an _offset to determine pixel positions
    Colour of the pixel is set by glColorPointer array.
    Alpha value is grabbed from the texture to give anti-aliasing and modified by the 'alpha' attribute to
    affect overall transparency.
    """

    name = 'aliasedTextShader'
    CCPNSHADER = True

    # shader for plotting smooth text to the screen in aliased Regions
    vertexShader = """
        #version 120

        uniform   mat4  pTexMatrix;
        uniform   mat4  mvMatrix;
        uniform   vec4  axisScale;
        uniform   vec2  stackOffset;
        uniform   float aliasPosition;
        varying   float _aliased;
        varying   vec4  _FC;
        varying   vec2  _texCoord;
        attribute vec3  _offset;

        void main()
        {
            gl_Position = pTexMatrix * mvMatrix * ((gl_Vertex * axisScale) + vec4(_offset.xy + stackOffset, 0.0, 0.0));
            //gl_Position = pTexMatrix * mvMatrix * (gl_Vertex + vec4(_offset.xy + stackOffset, 0.0, 0.0));

            _texCoord = gl_MultiTexCoord0.st;
            _FC = gl_Color;
            _aliased = (aliasPosition - _offset.z);
        }
        """

    # fragment shader to determine shading from the texture alpha value and the 'alpha' attribute
    fragmentShader = """
        #version 120

        uniform sampler2D texture;
        uniform vec4      background;
        uniform int       blendEnabled;
        uniform float     alpha;
        uniform float     aliasShade;
        uniform int       aliasEnabled;
        varying vec4      _FC;
        varying vec2      _texCoord;
        vec4              _texFilter;
        float             _opacity;
        varying float     _aliased;
        
        void main()
        {
            _texFilter = texture2D(texture, _texCoord);
            // colour for blending enabled
            _opacity = _texFilter.w * alpha;
                        
            // set the pixel colour
            if (abs(_aliased) < 0.5)
                if (blendEnabled != 0)
                    // multiply the character fade by the color fade to give the actual transparency
                    gl_FragColor = vec4(_FC.xyz, _FC.w * _opacity);
                
                else   
                    // plot a background box around the character
                    gl_FragColor = vec4((_FC.xyz * _opacity) + (1.0 - _opacity) * background.xyz, 1.0);

            else if (aliasEnabled != 0) {
                // modify the opacity
                _opacity *= aliasShade;
                
                if (blendEnabled != 0)
                    // multiply the character fade by the color fade to give the actual transparency
                    gl_FragColor = vec4(_FC.xyz, _FC.w * _opacity);
    
                else   
                    // plot a background box around the character
                    gl_FragColor = vec4((_FC.xyz * _opacity) + (1.0 - _opacity) * background.xyz, 1.0);
            }
            else
                // skip the pixel
                discard;
        }
        """

    """
    """
    # additional attribute list for shader
    _attributes = {
        'mvMatrix'     : (16, np.float32),
        'aliasPosition': (1, np.float32),
        'aliasShade'   : (1, np.float32),
        'aliasEnabled' : (1, np.uint32),
        }

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # methods available for shader

    def __init__(self):
        self.attributes.update(self._attributes)
        super().__init__()

    def setMVMatrix(self, matrix):
        """Set the contents of viewport mvMatrix
        :param matrix: consisting of 16 float32 elements
        """
        self.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, matrix)

    def setAliasPosition(self, aliasX, aliasY):
        """Set the alias position:
        Used to calculate whether the current peak is in the aliased region
        :param aliasX: X alias region
        :param aliasY: Y alias region
        """
        self.setGLUniform1f('aliasPosition', getAliasSetting(aliasX, aliasY))

    def setAliasShade(self, aliasShade):
        """Set the alias shade: a single float in range [0.0, 1.0]
        Used to determine visibility of aliased peaks, 0.0 -> background colour
        :param aliasShade: single float32
        """
        if not isinstance(aliasShade, (float, np.float32)):
            raise TypeError('aliasShade must be a float')
        value = float(np.clip(aliasShade, 0.0, 1.0))

        self.setGLUniform1f('aliasShade', value)

    def setAliasEnabled(self, aliasEnabled):
        """Set the alias enabled: bool True/False
        Used to determine visibility of aliased peaks, using aliasShade
        False = disable visibility of aliased peaks
        :param aliasEnabled: bool
        """
        if not isinstance(aliasEnabled, bool):
            raise TypeError('aliasEnabled must be a bool')
        value = 1 if aliasEnabled else 0

        self.setGLUniform1i('aliasEnabled', value)
