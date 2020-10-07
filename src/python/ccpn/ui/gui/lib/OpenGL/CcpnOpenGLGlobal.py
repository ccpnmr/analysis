"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2020-10-07 17:06:41 +0100 (Wed, October 07, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 13:28:13 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from PyQt5 import QtWidgets
import numpy as np
from ccpn.util.decorators import singleton
from ccpn.framework.PathsAndUrls import fontsPath
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLFonts import CcpnGLFont
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLShader import ShaderProgram


GLFONT_DEFAULT = 'OpenSans-Regular'
GLFONT_SUBSTITUTE = 'OpenSans-Regular'
GLFONT_DEFAULTSIZE = 13           # moved to preferences.appearance
GLFONT_DEFAULTSCALE = 1
GLFONT_SCALES = (1, 2)
GLFONT_SIZES = [10, 12, 13, 14, 16, 18, 20, 24]
GLFONT_DICT = {}

GLFONT_FILE = 0
GLFONT_NAME = 1
GLFONT_SIZE = 2
GLFONT_SCALE = 3

GLFONT_TRANSPARENT = 'Transparent'
GLFONT_PATH = 'Fonts'

TRANSPARENCIES = ('', '-%s' % GLFONT_TRANSPARENT)
for size in GLFONT_SIZES:
    for scale in GLFONT_SCALES:
        for transparency in TRANSPARENCIES:
            GLFONT_DICT['%s%s-%i' % (GLFONT_DEFAULT, transparency, size), scale] = ('glFont%i.fnt' % (size * scale), GLFONT_DEFAULT, size, scale, transparency)  # some are double size for retina displays...


@singleton
class GLGlobalData(QtWidgets.QWidget):
    def __init__(self, parent=None, mainWindow=None, strip=None, spectrumDisplay=None):
        super(GLGlobalData, self).__init__()
        self._parent = parent
        self.mainWindow = mainWindow
        self.strip = strip
        self._spectrumDisplay = spectrumDisplay

        self.fonts = {}
        self.loadFonts()

        self.initialiseShaders()
        self._glClientIndex = 0

    def getNextClientIndex(self):
        self._glClientIndex += 1
        return 1  #self._glClientIndex

    def loadFonts(self):
        for key, fontInfo in GLFONT_DICT.items():
            scale = fontInfo[GLFONT_SCALE]
            transparentName = fontInfo[GLFONT_FILE] + GLFONT_TRANSPARENT + str(fontInfo[2])

            self.fonts[key] = CcpnGLFont(os.path.join(fontsPath, GLFONT_PATH, fontInfo[0]),
                                         activeTexture=0, scale=scale)

            key = transparentName, scale
            self.fonts[key] = CcpnGLFont(os.path.join(fontsPath, GLFONT_PATH, fontInfo[0]),
                                         fontTransparency=0.5, activeTexture=1, scale=scale)

        self.glSmallFont = GLFONT_DEFAULT
        self.glSmallTransparentFont = '%s-%s' % (GLFONT_DEFAULT, GLFONT_TRANSPARENT)
        try:
            _size = self.mainWindow.application.preferences.appearance.spectrumDisplayFontSize
            if _size in GLFONT_SIZES:
                self.glSmallFontSize = _size
        except:
            self.glSmallFontSize = GLFONT_DEFAULTSIZE

    def initialiseShaders(self):
        # simple shader for standard plotting of contours
        self._vertexShader1 = """
            #version 120
        
            uniform mat4 pMatrix;
            uniform mat4 mvMatrix;
            varying vec4 _FC;
        
            void main()
            {
              gl_Position = (pMatrix * mvMatrix) * gl_Vertex;
              _FC = gl_Color;
            }
            """

        self._fragmentShader1 = """
            #version 120
        
            varying vec4  _FC;
        
            void main()
            {
              gl_FragColor = _FC;
            }
            """

        # shader for plotting antialiased text to the screen
        self._vertexShaderTex = """
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

        self._fragmentShaderTex = """
            #version 120
        
            uniform sampler2D   texture;
            uniform vec4        background;
            uniform int         blendEnabled;
            varying vec4        _FC;
            vec4                _texFilter;
            varying vec2        _texCoord;
        
            void main()
            {
              _texFilter = texture2D(texture, _texCoord);
              // colour for blending enabled
              if (blendEnabled != 0)
                // multiply the character fade by the color fade to give the actual transparency
                gl_FragColor = vec4(_FC.xyz, _FC.w * _texFilter.w);
                
              else   
                // gives a background box around the character, giving a simple border
                gl_FragColor = vec4((_FC.xyz * _texFilter.w) + (1 - _texFilter.w) * background.xyz, 1.0);
            }
            """

        # main shader for all plotting
        self._shaderProgram1 = ShaderProgram(vertex=self._vertexShader1,
                                             fragment=self._fragmentShader1,
                                             attributes={'pMatrix' : (16, np.float32),
                                                         'mvMatrix': (16, np.float32),
                                                         })

        # main shader for all the text
        self._shaderProgramTex = ShaderProgram(vertex=self._vertexShaderTex,
                                               fragment=self._fragmentShaderTex,
                                               attributes={'pTexMatrix'  : (16, np.float32),
                                                           'axisScale'   : (4, np.float32),
                                                           'stackOffset' : (2, np.float32),
                                                           'texture'     : (1, np.uint32),
                                                           'background'  : (4, np.float32),
                                                           'blendEnabled': (1, np.uint32),
                                                           })

        # NOTE:ED - experimental stuff below, don't delete
        # self._vertexShader1 = """
        #     #version 120
        #
        #     uniform mat4 mvMatrix;
        #     uniform mat4 pMatrix;
        #
        #     // data matrix is column major so dataMatrix[0] is the first 4 elements
        #     uniform mat4 dataMatrix;
        #
        #     varying vec4 FC;
        #     uniform vec4 axisScale;
        #     attribute vec2 offset;
        #
        #     void main()
        #     {
        #       gl_Position = (pMatrix * mvMatrix) * gl_Vertex;
        #
        #     //  float denom = dataMatrix[0].
        #     //  gl_Position = vec4(0.0, 1.0);
        #
        #     //  gl_Position = (pMatrix * gl_Vertex) + vec4(0.2, 0.3, 0.0, 0.0);
        #
        #     //  vec4 pos = pMatrix * gl_Vertex;
        #     //  gl_Position = vec4(pos.xy, 0.0, 1.0);
        #
        #       FC = gl_Color;
        #     }
        #     """
        #
        # self._fragmentShader1 = """
        #     #version 120
        #
        #     varying vec4  FC;
        #     uniform vec4  background;
        #     //uniform ivec4 parameterList;
        #
        #     void main()
        #     {
        #       gl_FragColor = FC;
        #
        #     //  if (FC.w < 0.05)
        #     //    discard;
        #     //  else if (parameterList.x == 0)
        #     //    gl_FragColor = FC;
        #     //  else
        #     //    gl_FragColor = vec4(FC.xyz, 1.0) * FC.w + background * (1-FC.w);
        #     }
        #     """
        #
        # # shader for plotting antialiased text to the screen
        # self._vertexShaderTex = """
        #     #version 120
        #
        #     uniform mat4 mvTexMatrix;
        #     uniform mat4 pTexMatrix;
        #     uniform vec4 axisScale;
        #     uniform vec4 viewport;
        #     varying vec4 FC;
        #     varying vec4 FO;
        #     varying vec2 _texCoord;
        #     attribute vec2 offset;
        #
        #     void main()
        #     {
        #       // viewport is scaled to axis
        #     //      vec4 pos = pTexMatrix * (gl_Vertex * axisScale + vec4(offset, 0.0, 0.0));
        #                                // character_pos        // world_coord
        #
        #       // centre on the nearest pixel in NDC - shouldn't be needed but textures not correct yet
        #     //      gl_Position = pos;       //vec4( pos.x,        //floor(0.5 + viewport.x*pos.x) / viewport.x,
        #                                //pos.y,        //floor(0.5 + viewport.y*pos.y) / viewport.y,
        #                                //pos.zw );
        #
        #       gl_Position = pTexMatrix * ((gl_Vertex * axisScale) + vec4(offset, 0.0, 0.0));
        #
        #     //      gl_Position = (pTexMatrix * vec4(offset, 0.0, 0.0)) + ((pTexMatrix * gl_Vertex) * axisScale);
        #
        #       _texCoord = gl_MultiTexCoord0.st;
        #       FC = gl_Color;
        #     }
        #     """
        #
        # self._fragmentShaderTex = """
        #     #version 120
        #
        #     uniform sampler2D texture;
        #     varying vec4 FC;
        #     vec4    texFilter;
        #     uniform vec4 background;
        #     uniform int  blendEnabled;
        #     varying vec4 FO;
        #     varying vec2 _texCoord;
        #
        #     void main()
        #     {
        #       texFilter = texture2D(texture, _texCoord);
        #       // colour for blending enabled
        #       if (blendEnabled != 0)
        #         // multiply the character fade by the color fade to give the actual transparency
        #         gl_FragColor = vec4(FC.xyz, FC.w * texFilter.w);
        #
        #       else
        #         // gives a background box around the character, giving a simple border
        #         gl_FragColor = vec4((FC.xyz * texFilter.w) + (1 - texFilter.w) * background.xyz, 1.0);
        #
        #       // if (texFilter.w < 0.01)
        #       //   discard;
        #       // gl_FragColor = vec4(FC.xyz, texFilter.w);
        #     }
        #     """
        #
        # self._fragmentShaderTexNoBlend = """
        #     #version 120
        #
        #     uniform sampler2D texture;
        #     varying vec4 FC;
        #     vec4    texFilter;
        #     uniform vec4 background;
        #     uniform uint blendEnabled;
        #     varying vec4 FO;
        #     varying vec4 _texCoord;
        #
        #     void main()
        #     {
        #       texFilter = texture2D(texture, _texCoord.xy);
        #       gl_FragColor = vec4((FC.xyz * texFilter.w) + (1 - texFilter.w) * background.xyz, 1.0);
        #     }
        #     """
        #
        # #     # shader for plotting antialiased text to the screen
        # #     self._vertexShaderTex = """
        # #     #version 120
        # #
        # #     uniform mat4 mvMatrix;
        # #     uniform mat4 pMatrix;
        # #     varying vec4 FC;
        # #     uniform vec4 axisScale;
        # #     attribute vec2 offset;
        # #
        # #     void main()
        # #     {
        # #       gl_Position = pMatrix * mvMatrix * (gl_Vertex * axisScale + vec4(offset, 0.0, 0.0));
        # #       gl_TexCoord[0] = gl_MultiTexCoord0;
        # #       FC = gl_Color;
        # #     }
        # #     """
        # #
        # #     self._fragmentShaderTex = """
        # # #version 120
        # #
        # # #ifdef GL_ES
        # # precision mediump float;
        # # #endif
        # #
        # # uniform sampler2D texture;
        # # varying vec4 FC;
        # # vec4    texFilter;
        # #
        # # varying vec4 v_color;
        # # varying vec2 v_texCoord;
        # #
        # # const float smoothing = 1.0/16.0;
        # #
        # # void main() {
        # #     float distance = texture2D(texture, v_texCoord).a;
        # #     float alpha = smoothstep(0.5 - smoothing, 0.5 + smoothing, distance);
        # #     gl_FragColor = vec4(v_color.rgb, v_color.a * alpha);
        # # }
        # # """
        #
        # # advanced shader for plotting contours
        # self._vertexShader2 = """
        #     #version 120
        #
        #     varying vec4  P;
        #     varying vec4  C;
        #     uniform mat4  mvMatrix;
        #     uniform mat4  pMatrix;
        #     uniform vec4  positiveContour;
        #     uniform vec4  negativeContour;
        #     //uniform float gsize = 5.0;      // size of the grid
        #     //uniform float gwidth = 1.0;     // grid lines' width in pixels
        #     //varying float   f = min(abs(fract(P.z * gsize) - 0.5), 0.2);
        #
        #     void main()
        #     {
        #       P = gl_Vertex;
        #       C = gl_Color;
        #     //  gl_Position = vec4(gl_Vertex.x, gl_Vertex.y, 0.0, 1.0);
        #     //  vec4 glVect = pMatrix * mvMatrix * vec4(P, 1.0);
        #     //  gl_Position = vec4(glVect.x, glVect.y, 0.0, 1.0);
        #       gl_Position = pMatrix * mvMatrix * vec4(P.xy, 0.0, 1.0);
        #     }
        #     """
        #
        # self._fragmentShader2 = """
        #     #version 120
        #
        #     //  uniform float gsize = 50.0;       // size of the grid
        #     uniform float gwidth = 0.5;       // grid lines' width in pixels
        #     uniform float mi = 0.0;           // mi=max(0.0,gwidth-1.0)
        #     uniform float ma = 1.0;           // ma=max(1.0,gwidth);
        #     varying vec4 P;
        #     varying vec4 C;
        #
        #     void main()
        #     {
        #     //  vec3 f  = abs(fract (P * gsize)-0.5);
        #     //  vec3 df = fwidth(P * gsize);
        #     //  float mi=max(0.0,gwidth-1.0), ma=max(1.0,gwidth);//should be uniforms
        #     //  vec3 g=clamp((f-df*mi)/(df*(ma-mi)),max(0.0,1.0-gwidth),1.0);//max(0.0,1.0-gwidth) should also be sent as uniform
        #     //  float c = g.x * g.y * g.z;
        #     //  gl_FragColor = vec4(c, c, c, 1.0);
        #     //  gl_FragColor = gl_FragColor * gl_Color;
        #
        #       float   f = min(abs(fract(P.z)-0.5), 0.2);
        #       float   df = fwidth(P.z);
        #     //  float   mi=max(0.0,gwidth-1.0), ma=max(1.0,gwidth);                 //  should be uniforms
        #       float   g=clamp((f-df*mi)/(df*(ma-mi)),max(0.0,1.0-gwidth),1.0);      //  max(0.0,1.0-gwidth) should also be sent as uniform
        #     //  float   g=clamp((f-df*mi), 0.0, df*(ma-mi));  //  max(0.0,1.0-gwidth) should also be sent as uniform
        #
        #     //  g = g/(df*(ma-mi));
        #     //  float   cAlpha = 1.0-(g*g);
        #     //  if (cAlpha < 0.25)            //  this actually causes branches in the shader - bad
        #     //    discard;
        #     //  gl_FragColor = vec4(0.8-g, 0.3, 0.4-g, 1.0-(g*g));
        #       gl_FragColor = vec4(P.w, P.w, P.w, 1.0-(g*g));
        #     }
        #     """
        #
        # self._vertexShader3 = """
        #     #version 120
        #
        #     uniform mat4 u_projTrans;
        #
        #     attribute vec4 a_position;
        #     attribute vec2 a_texCoord0;
        #     attribute vec4 a_color;
        #
        #     varying vec4 v_color;
        #     varying vec2 v_texCoord;
        #
        #     void main() {
        #       gl_Position = u_projTrans * a_position;
        #       v_texCoord = a_texCoord0;
        #       v_color = a_color;
        #     }
        #     """
        #
        # self._fragmentShader3 = """
        #     #version 120
        #
        #     #ifdef GL_ES
        #     precision mediump float;
        #     #endif
        #
        #     uniform sampler2D u_texture;
        #
        #     varying vec4 v_color;
        #     varying vec2 v_texCoord;
        #
        #     const float smoothing = 1.0/16.0;
        #
        #     void main() {
        #       float distance = texture2D(u_texture, v_texCoord).a;
        #       float alpha = smoothstep(0.5 - smoothing, 0.5 + smoothing, distance);
        #       gl_FragColor = vec4(v_color.rgb, v_color.a * alpha);
        #     }
        #     """
