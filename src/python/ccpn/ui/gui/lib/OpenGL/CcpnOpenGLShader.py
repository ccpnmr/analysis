"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import os
from PyQt5 import QtWidgets
import numpy as np
from ccpn.util.Logging import getLogger

try:
    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL hellogl",
                                   "PyOpenGL must be installed to run this example.")
    sys.exit(1)


class ShaderProgram(object):
    def __init__(self, vertex, fragment, attributes):
        self.program_id = GL.glCreateProgram()
        self.vs_id = self.add_shader(vertex, GL.GL_VERTEX_SHADER)
        self.frag_id = self.add_shader(fragment, GL.GL_FRAGMENT_SHADER)
        self.attributes = attributes
        self.uniformLocations = {}

        GL.glAttachShader(self.program_id, self.vs_id)
        GL.glAttachShader(self.program_id, self.frag_id)
        GL.glLinkProgram(self.program_id)

        if GL.glGetProgramiv(self.program_id, GL.GL_LINK_STATUS) != GL.GL_TRUE:
            info = GL.glGetProgramInfoLog(self.program_id)
            GL.glDeleteProgram(self.program_id)
            GL.glDeleteShader(self.vs_id)
            GL.glDeleteShader(self.frag_id)
            raise RuntimeError('Error linking program: %s' % (info))

        # detach after successful link
        GL.glDetachShader(self.program_id, self.vs_id)
        GL.glDetachShader(self.program_id, self.frag_id)

        # define attributes to be passed to the shaders
        for att in attributes.keys():
            self.uniformLocations[att] = GL.glGetUniformLocation(self.program_id, att)
            self.uniformLocations['_' + att] = np.zeros((attributes[att][0],), dtype=attributes[att][1])

    def makeCurrent(self):
        GL.glUseProgram(self.program_id)
        return self

    def setBackground(self, col):
        self.setGLUniform4fv('background', 1, col)

    def setBlendEnabled(self, col):
        self.setGLUniform1i('blendEnabled', col)

    # def setParameterList(self, params):
    #   self.setGLUniform4iv('parameterList', 1, params)

    def setProjectionAxes(self, attMatrix, left, right, bottom, top, near, far):

        oa = 2.0 / (right - left)               #if abs(right-left) > 1.0e-7 else 1.0
        ob = 2.0 / (top - bottom)               #if abs(top-bottom) > 1.0e-7 else 1.0
        oc = -2.0 / (far - near)                #if abs(far-near) > 1.0e-7 else 1.0
        od = -(far + near) / (far - near)       #if abs(far-near) > 1.0e-7 else 0.0
        oe = -(top + bottom) / (top - bottom)   #if abs(top-bottom) > 1.0e-7 else 0.0
        og = -(right + left) / (right - left)   #if abs(right-left) > 1.0e-7 else 0.0
        # orthographic
        attMatrix[0:16] = [oa, 0.0, 0.0, 0.0,
                           0.0, ob, 0.0, 0.0,
                           0.0, 0.0, oc, 0.0,
                           og, oe, od, 1.0]

    def setViewportMatrix(self, viewMatrix, left, right, bottom, top, near, far):
        # return the viewport transformation matrix - mapping screen to NDC
        #   normalised device coordinates
        #   viewport * NDC_cooord = world_coord
        oa = (right - left) / 2.0               #if abs(right-left) > 1.0e-7 else 1.0
        ob = (top - bottom) / 2.0               #if abs(top-bottom) > 1.0e-7 else 1.0
        oc = (far - near) / 2.0                 #if abs(far-near) > 1.0e-7 else 1.0
        og = (right + left) / 2.0
        oe = (top + bottom) / 2.0
        od = (near + far) / 2.0
        # orthographic
        # viewMatrix[0:16] = [oa, 0.0, 0.0,  0.0,
        #                     0.0,  ob, 0.0,  0.0,
        #                     0.0, 0.0,  oc,  0.0,
        #                     og, oe, od, 1.0]
        viewMatrix[0:16] = [oa, 0.0, 0.0, og,
                            0.0, ob, 0.0, oe,
                            0.0, 0.0, oc, od,
                            0.0, 0.0, 0.0, 1.0]

    def setGLUniformMatrix4fv(self, uniformLocation=None, count=1, transpose=GL.GL_FALSE, value=None):
        if uniformLocation in self.uniformLocations:
            try:
                GL.glUniformMatrix4fv(self.uniformLocations[uniformLocation],
                                       count, transpose, value)
            except Exception as es:
                pass

        else:
            raise RuntimeError('Error setting setGLUniformMatrix4fv: %s' % uniformLocation)

    def setGLUniform4fv(self, uniformLocation=None, count=1, value=None):
        if uniformLocation in self.uniformLocations:
            GL.glUniform4fv(self.uniformLocations[uniformLocation],
                             count, value)
        else:
            raise RuntimeError('Error setting setGLUniform4fv: %s' % uniformLocation)

    def setGLUniform4iv(self, uniformLocation=None, count=1, value=None):
        if uniformLocation in self.uniformLocations:
            GL.glUniform4iv(self.uniformLocations[uniformLocation],
                             count, value)
        else:
            raise RuntimeError('Error setting setGLUniform4iv: %s' % uniformLocation)

    def setGLUniform1i(self, uniformLocation=None, value=None):
        if uniformLocation in self.uniformLocations:
            GL.glUniform1i(self.uniformLocations[uniformLocation], value)
        else:
            raise RuntimeError('Error setting setGLUniformMatrix4fv: %s' % uniformLocation)

    def add_shader(self, source, shader_type):
        """ Helper function for compiling a GLSL shader
        Parameters
        ----------
        source : str
            String containing shader source code
        shader_type : valid OpenGL shader type
            Type of shader to compile
        Returns
        -------
        value : int
            Identifier for shader if compilation is successful
        """
        shader_id = 0
        try:
            shader_id = GL.glCreateShader(shader_type)
            GL.glShaderSource(shader_id, source)
            GL.glCompileShader(shader_id)
            if GL.glGetShaderiv(shader_id, GL.GL_COMPILE_STATUS) != GL.GL_TRUE:
                info = GL.glGetShaderInfoLog(shader_id)

                # raise an error and hard exit
                getLogger().warning('Shader compilation failed: %s' % info)
                os._exit(0)
            return shader_id
        except:
            GL.glDeleteShader(shader_id)
            raise

    def uniform_location(self, name):
        """ Helper function to get location of an OpenGL uniform variable
        Parameters
        ----------
        name : str
            Name of the variable for which location is to be returned
        Returns
        -------
        value : int
            Integer describing location
        """
        return GL.glGetUniformLocation(self.program_id, name)

    def attribute_location(self, name):
        """ Helper function to get location of an OpenGL attribute variable
        Parameters
        ----------
        name : str
            Name of the variable for which location is to be returned
        Returns
        -------
        value : int
            Integer describing location
        """
        return GL.glGetAttribLocation(self.program_id, name)
