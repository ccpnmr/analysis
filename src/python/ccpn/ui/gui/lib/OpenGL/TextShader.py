"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-12-14 16:56:13 +0000 (Thu, December 14, 2023) $"
__version__ = "$Revision: 3.2.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2023-12-14 14:19:05 +0100 (Thu, December 14, 2023) $"
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
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import getAliasSetting
from ccpn.util.Logging import getLogger


class TextShader(ShaderProgramABC):
    """
    Main Text shader

    Shader for plotting text, uses a billboard technique by using an _offset to determine pixel positions
    Colour of the pixel is set by glColorPointer array.
    Alpha value is grabbed from the texture to give antialiasing and modified by the 'alpha' attribute to
    affect overall transparency.
    """

    name = 'textShader'
    CCPNSHADER = True

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # shader attributes

    _PMATRIX = 'pTexMatrix'
    _AXISSCALE = 'axisScale'
    _STACKOFFSET = 'stackOffset'
    _VIEWPORT = 'viewport'
    _GLCOLOR = 'glColor'
    _GLMULTITEXCOORD = 'glMultiTexCoord'
    _OFFSET = 'offset'
    _TEXTURE = 'texture'
    _BACKGROUND = 'background'
    _BLENDENABLED = 'blendEnabled'
    _ALPHA = 'alpha'

    # attribute/uniform lists for shaders - needs to be a duplicate
    attributes = {_GLCOLOR        : None,
                  _GLMULTITEXCOORD: None,
                  _OFFSET         : None,
                  }
    uniforms = {_PMATRIX     : (16, np.float32),
                _AXISSCALE   : (2, np.float32),
                _STACKOFFSET : (2, np.float32),
                _VIEWPORT    : (3, np.float32),
                _TEXTURE     : (1, np.uint32),
                _BACKGROUND  : (4, np.float32),
                _BLENDENABLED: (1, np.uint32),
                _ALPHA       : (1, np.float32),
                }

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # shader for plotting anti-aliased text to the screen
    vertexShader = """
        #version 120

        uniform   mat4  pTexMatrix;
        uniform   vec4  axisScale;
        uniform   vec2  stackOffset;
        varying   vec4  _FC;
        varying   vec2  _texCoord;
        attribute vec4  _offset;

        void main()
        {
            gl_Position = pTexMatrix * vec4(gl_Vertex.xy * axisScale.xy + _offset.xy + stackOffset, 0.0, 1.0);

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
                vec4      _texFilter;
                float     _opacity;

        void main()
        {
            _texFilter = texture2D(texture, _texCoord);  // returns float due to glTexImage2D creation as GL_ALPHA
            // colour for blending enabled
            _opacity = _texFilter.a * alpha;  // only has .alpha component

            if (blendEnabled != 0)
                // multiply the character fade by the color fade to give the actual transparency
                gl_FragColor = vec4(_FC.xyz, _FC.w * _opacity);

            else   
                // plot a background box around the character
                gl_FragColor = vec4((_FC.xyz * _opacity) + (1.0 - _opacity) * background.xyz, 1.0);
        }
        """

    # # attribute list for shader
    # attributes = {'pTexMatrix'  : (16, np.float32),
    #               'axisScale'   : (4, np.float32),
    #               'stackOffset' : (2, np.float32),
    #               'texture'     : (1, np.uint32),
    #               'background'  : (4, np.float32),
    #               'blendEnabled': (1, np.uint32),
    #               'alpha'       : (1, np.float32),
    #               }

    #=========================================================================================
    # methods available
    #=========================================================================================

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


#=========================================================================================
# Text shader for displaying text in aliased regions
#=========================================================================================

class AliasedTextShader(TextShader):
    """
    Text shader for displaying text in aliased regions

    Shader for plotting text, uses a billboard technique by using an _offset to determine pixel positions
    Colour of the pixel is set by glColorPointer array.
    Alpha value is grabbed from the texture to give antialiasing and modified by the 'alpha' attribute to
    affect overall transparency.
    """

    name = 'aliasedTextShader'
    CCPNSHADER = True

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # additional shader attributes

    _MVMATRIX = 'mvMatrix'
    _ALIASPOSITION = 'aliasPosition'
    _ALIASSHADE = 'aliasShade'
    _ALIASENABLED = 'aliasEnabled'

    # additional attribute/uniform lists for shaders - needs to be a duplicate
    uniforms = dict(TextShader.uniforms)

    uniforms |= {_MVMATRIX     : (16, np.float32),
                 _ALIASPOSITION: (1, np.float32),
                 _ALIASSHADE   : (1, np.float32),
                 _ALIASENABLED : (1, np.uint32),
                 }

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
        attribute vec4  _offset;

        void main()
        {
            gl_Position = pTexMatrix * mvMatrix * vec4(gl_Vertex.xy * axisScale.xy + _offset.xy + stackOffset, 0.0, 1.0);

            _texCoord = gl_MultiTexCoord0.st;
            _FC = gl_Color;
            _aliased = (aliasPosition - gl_Vertex.z);
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
                vec4      _texFilter;
                float     _opacity;
        varying float     _aliased;

        void main()
        {
            _texFilter = texture2D(texture, _texCoord);  // returns float due to glTexImage2D creation as GL_ALPHA
            // colour for blending enabled
            _opacity = _texFilter.a * alpha;  // only has .alpha component

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

    # # additional attribute list for shader
    # _attributes = {
    #     'mvMatrix'     : (16, np.float32),
    #     'aliasPosition': (1, np.float32),
    #     'aliasShade'   : (1, np.float32),
    #     'aliasEnabled' : (1, np.uint32),
    #     }

    #=========================================================================================
    # methods available
    #=========================================================================================

    # def __init__(self):
    #     self.attributes.update(self._attributes)
    #     super().__init__()

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
