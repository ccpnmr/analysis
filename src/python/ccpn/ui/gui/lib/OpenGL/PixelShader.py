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
__date__ = "$Date: 2023-12-14 14:18:53 +0100 (Thu, December 14, 2023) $"
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


class PixelShader(ShaderProgramABC):
    """
    Pixel shader for contour plotting

    A very simple shader, uses the projection/viewport matrices to calculate the gl_Position,
    and passes through the gl_Color to set the pixel.
    """

    name = 'pixelShader'
    CCPNSHADER = True

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # shader attributes/uniforms

    _PMATRIX = 'pMatrix'
    _MVMATRIX = 'mvMatrix'

    # attribute/uniform lists for shaders
    attributes = {}
    uniforms = {_PMATRIX : (16, np.float32),
                _MVMATRIX: (16, np.float32),
                }

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

    # # attribute list for shader
    # attributes = {'pMatrix' : (16, np.float32),
    #               'mvMatrix': (16, np.float32),
    #               }

    #=========================================================================================
    # methods available
    #=========================================================================================

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


#=========================================================================================
# Pixel shader for aliased peak plotting
#=========================================================================================

class AliasedPixelShader(PixelShader):
    """
    Pixel shader for aliased peak plotting

    Uses the projection/viewport matrices to calculate the gl_Position,
    and passes through the gl_Color to set the pixel.
    gl_Color is modified for peaks at different aliased positions
    """

    name = 'aliasedPixelShader'
    CCPNSHADER = True

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # additional shader attributes

    _ALIAS = 'alias'
    _ALIASPOSITION = 'aliasPosition'
    _BACKGROUND = 'background'
    _ALIASSHADE = 'aliasShade'
    _ALIASENABLED = 'aliasEnabled'

    # attribute/uniform lists for shaders - needs to be a duplicate
    attributes = {_ALIAS: (1, np.float32)}
    uniforms = {PixelShader._PMATRIX : (16, np.float32),
                PixelShader._MVMATRIX: (16, np.float32),
                _ALIASPOSITION       : (1, np.float32),  # change to a set
                _BACKGROUND          : (4, np.float32),
                _ALIASSHADE          : (1, np.float32),
                _ALIASENABLED        : (1, np.uint32),
                }

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # vertex shader to determine the co-ordinates
    vertexShader = """
        #version 120

        uniform   mat4  pMatrix;
        uniform   mat4  mvMatrix;
        attribute vec4  alias;
        uniform   float aliasPosition;
        varying   float _aliased;
        varying   vec4  _FC;

        void main()
        {
            // calculate the position, set shading value
            gl_Position = pMatrix * mvMatrix * vec4(gl_Vertex.xy, 0.0, 1.0);
            _FC = gl_Color;
            _aliased = (aliasPosition - gl_Vertex.z);
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

    # # additional attribute list for shader
    # _attributes = {
    #     'aliasPosition': (1, np.float32),
    #     'background'   : (4, np.float32),
    #     'aliasShade'   : (1, np.float32),
    #     'aliasEnabled' : (1, np.uint32),
    #     }

    #=========================================================================================
    # methods available
    #=========================================================================================

    # def __init__(self):
    #     self.attributes.update(self._attributes)
    #     super().__init__()

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
