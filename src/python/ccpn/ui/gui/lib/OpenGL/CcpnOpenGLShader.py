"""
Module containing functions for defining GLSL shaders.
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-06-17 13:40:47 +0100 (Fri, June 17, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 13:28:13 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import os
from PyQt5 import QtGui
import numpy as np
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.lib.OpenGL import GL


class ShaderProgramABC(object):
    """
    Class defining a GL shader program
    A shader is defined by the following objects
    vertexShader, a string object containg the code to be compiled for the vertex shader.
    e.g.
    
    vertexShader = '''
                    #version 120
                    
                    varying vec4 _FC;
                    
                    void main()
                    {
                      _FC = gl_Color;
                    }
                    '''
    fragmentShader is similarly defined
    
    attributes is a list of the attributes that can be accessed from the shader
    e.g.
    
    attributes = {'pMatrix' : (16, np.float32),
                  }
                  
                  pMatrix is a block of 16 np.float32 objects


    Version Tags for OpenGL and GLSL Versions
    OpenGL  GLSL        #version tag
    1.2 	none 	    none
    2.0 	1.10.59 	110
    2.1 	1.20.8 	    120 <- should be the lowest needed
    3.0 	1.30.10 	130
    3.1 	1.40.08 	140
    3.2 	1.50.11 	150
    3.3 	3.30.6  	330
    4.0 	4.00.9 	    400
    4.1 	4.10.6 	    410
    4.2 	4.20.6  	420
    4.3 	4.30.6  	430

    (On MacOS, anything above 2.1 causes problems)
    """

    vertexShader = None
    fragmentShader = None

    # dict containing the attributes that can be accessed in the shader
    attributes = {}

    CCPNSHADER = False

    def __init__(self):
        """
        Initialise the shader with a vertex/fragment shader pair, and attributes
        """

        # check that the required fields have been set
        if not (self.vertexShader or self.fragmentShader) or self.attributes == {}:
            raise RuntimeError('ShaderProgram is not correctly defined')

        self.uniformLocations = {}
        try:
            self._shader = shader = QtGui.QOpenGLShaderProgram()
            self.vs_id = shader.addShaderFromSourceCode(QtGui.QOpenGLShader.Vertex, self.vertexShader)
            self.frag_id = shader.addShaderFromSourceCode(QtGui.QOpenGLShader.Fragment, self.fragmentShader)
            shader.link()
            # shader.bind()
            self.program_id = shader.programId()
        except Exception as es:
            esType, esValue, esTraceback = sys.exc_info()
            _ver = QtGui.QOpenGLVersionProfile()
            self._GLVersion = GL.glGetString(GL.GL_VERSION)
            self._GLShaderVersion = GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION)
            _format = QtGui.QSurfaceFormat()
            msg = f"OpenGL: {self._GLVersion.decode('utf-8')}\n" \
                  f"GLSL: {self._GLShaderVersion.decode('utf-8')}\n" \
                  f"Surface: {_format.version()}\n\n" \
                  f"{es}\n" \
                  f"{esType}\n" \
                  f"{esTraceback}"
            raise RuntimeError(msg)

        # define attributes to be passed to the shaders
        for att in self.attributes.keys():
            self.uniformLocations[att] = shader.uniformLocation(att)
            self.uniformLocations['_' + att] = np.zeros((self.attributes[att][0],), dtype=self.attributes[att][1])

    def _addGLShader(self, source, shader_type):
        """Function for compiling a GLSL shader

        :param source: String containing shader source code
        :param shader_type: valid OpenGL shader type: GL_VERTEX_SHADER or GL_FRAGMENT_SHADER
        :return: int; Identifier for shader if compilation is successful
        """
        shader_id = 0
        try:
            shader_id = GL.glCreateShader(shader_type)
            GL.glShaderSource(shader_id, source)
            GL.glCompileShader(shader_id)
            if GL.glGetShaderiv(shader_id, GL.GL_COMPILE_STATUS) != GL.GL_TRUE:
                info = GL.glGetShaderInfoLog(shader_id)

                # raise an error and hard exit
                getLogger().warning(f'Shader compilation failed: {info}')
                getLogger().warning(f'source: {source}')
                os._exit(0)
            return shader_id
        except:
            GL.glDeleteShader(shader_id)
            raise

    @property
    def name(self):
        """Return the name of the shaderProgramABC instance
        """
        return str(self.__name__)

    @classmethod
    def _register(cls):
        """method to register the shader - not required yet
        """
        pass

    def makeCurrent(self):
        """Make self the current shader
        """
        self._shader.bind()
        return self

    def release(self):
        """Unbind the current shader
        """
        self._shader.release()

    def setProjectionAxes(self, attMatrix, left, right, bottom, top, near, far):
        """Set the contents of the projection matrix
        """
        oa = 2.0 / (right - left) if abs(right-left) > 1.0e-7 else 1.0
        ob = 2.0 / (top - bottom) if abs(top-bottom) > 1.0e-7 else 1.0
        oc = -2.0 / (far - near) if abs(far-near) > 1.0e-7 else 1.0
        od = -(far + near) / (far - near) if abs(far-near) > 1.0e-7 else 0.0
        oe = -(top + bottom) / (top - bottom) if abs(top-bottom) > 1.0e-7 else 0.0
        og = -(right + left) / (right - left) if abs(right-left) > 1.0e-7 else 0.0

        attMatrix[0:16] = [oa, 0.0, 0.0, 0.0,
                           0.0, ob, 0.0, 0.0,
                           0.0, 0.0, oc, 0.0,
                           og, oe, od, 1.0]

    def setViewportMatrix(self, viewMatrix, left, right, bottom, top, near, far):
        """Set the contents of the viewport matrix
        """
        # return the viewport transformation matrix - mapping screen to NDC
        #   normalised device coordinates
        #   viewport * NDC_cooord = world_coord
        oa = (right - left) / 2.0  #if abs(right-left) > 1.0e-7 else 1.0
        ob = (top - bottom) / 2.0  #if abs(top-bottom) > 1.0e-7 else 1.0
        oc = (far - near) / 2.0  #if abs(far-near) > 1.0e-7 else 1.0
        og = (right + left) / 2.0
        oe = (top + bottom) / 2.0
        od = (near + far) / 2.0

        viewMatrix[0:16] = [oa, 0.0, 0.0, og,
                            0.0, ob, 0.0, oe,
                            0.0, 0.0, oc, od,
                            0.0, 0.0, 0.0, 1.0]

    # Common attributes sizes

    def setGLUniformMatrix4fv(self, uniformLocation=None, count=1, transpose=GL.GL_FALSE, value=None):
        """Set a 4x4 float32 matrix in the shader
        """
        try:
            self._shader.setUniformValue(self.uniformLocations[uniformLocation],
                                         QtGui.QMatrix4x4(*value) if transpose else QtGui.QMatrix4x4(*value).transposed())
        except Exception as es:
            raise RuntimeError(f'Error setting setGLUniformMatrix4fv: {uniformLocation}   {es}')

    def setGLUniform4fv(self, uniformLocation=None, count=1, value=None):
        """Set a 4x1 float32 vector in the shader
        """
        try:
            self._shader.setUniformValue(self.uniformLocations[uniformLocation], QtGui.QVector4D(*value))

        except Exception as es:
            raise RuntimeError(f'Error setting setGLUniform4fv: {uniformLocation}   {es}')

    def setGLUniform4iv(self, uniformLocation=None, count=1, value=None):
        """Set a 4x1 uint32 vector in the shader
        """
        try:
            self._shader.setUniformValue(self.uniformLocations[uniformLocation], QtGui.QVector4D(*value))
        except Exception as es:
            raise RuntimeError(f'Error setting setGLUniform4iv: {uniformLocation}   {es}')

    def setGLUniform2fv(self, uniformLocation=None, count=1, value=None):
        """Set a 2x1 uint32 vector in the shader
        """
        try:
            self._shader.setUniformValue(self.uniformLocations[uniformLocation], QtGui.QVector2D(*value))
        except Exception as es:
            raise RuntimeError(f'Error setting setGLUniform2fv: {uniformLocation}   {es}')

    def setGLUniform1i(self, uniformLocation=None, value=None):
        """Set a single uint32 attribute in the shader
        """
        try:
            self._shader.setUniformValue(self.uniformLocations[uniformLocation], value)
        except Exception as es:
            raise RuntimeError(f'Error setting setGLUniform1i: {uniformLocation}   {es}')

    def setGLUniform1f(self, uniformLocation=None, value=None):
        """Set a single float32 attribute in the shader
        """
        try:
            self._shader.setUniformValue(self.uniformLocations[uniformLocation], float(value))
        except Exception as es:
            raise RuntimeError(f'Error setting setGLUniform1f: {uniformLocation}   {es}')

    def uniformLocation(self, name):
        """Function to get location of an OpenGL uniform variable

        :param name: String, name of the variable for which location is to be returned
        :return: int; integer describing location
        """
        return GL.glGetUniformLocation(self.program_id, name)

    def attributeLocation(self, name):
        """Function to get location of an OpenGL attribute variable

        :param name: String, name of the variable for which location is to be returned
        :return: int; integer describing location
        """
        return GL.glGetAttribLocation(self.program_id, name)
