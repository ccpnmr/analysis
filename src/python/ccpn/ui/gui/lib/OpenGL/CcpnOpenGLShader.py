"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import sys, os
import math
from threading import Thread
# from queue import Queue
from imageio import imread
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (QPoint, QSize, Qt, pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from ccpn.util.Logging import getLogger
import numpy as np
from pyqtgraph import functions as fn
from ccpn.core.PeakList import PeakList
from ccpn.core.IntegralList import IntegralList

from ccpn.ui.gui.guiSettings import getColours
from ccpn.util.Colour import hexToRgbRatio
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_BACKGROUND, CCPNGLWIDGET_FOREGROUND, CCPNGLWIDGET_PICKCOLOUR, \
                                    CCPNGLWIDGET_GRID, CCPNGLWIDGET_HIGHLIGHT, \
                                    CCPNGLWIDGET_LABELLING, CCPNGLWIDGET_PHASETRACE
from ccpn.ui.gui.lib.GuiPeakListView import _getScreenPeakAnnotation, _getPeakAnnotation    # temp until I rewrite
import ccpn.util.Phasing as Phasing
from ccpn.util.decorators import singleton
from ccpn.ui.gui.lib.mouseEvents import \
              leftMouse, shiftLeftMouse, controlLeftMouse, controlShiftLeftMouse, \
              middleMouse, shiftMiddleMouse, rightMouse, shiftRightMouse, controlRightMouse, PICK
from ccpn.core.lib.Notifiers import Notifier
from ccpn.framework.PathsAndUrls import fontsPath
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLNotifier import GLNotifier
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
      self.uniformLocations['_'+att] = np.zeros((attributes[att][0],), dtype=attributes[att][1])

  def makeCurrent(self):
    GL.glUseProgram(self.program_id)
    return self

  def setBackground(self, col):
    self.setGLUniform4fv('background', 1, col)

  # def setParameterList(self, params):
  #   self.setGLUniform4iv('parameterList', 1, params)

  def setProjectionAxes(self, attMatrix, left, right, bottom, top, near, far):
    # of = 1.0
    # on = -1.0
    # oa = 2.0/(self.axisR-self.axisL)
    # ob = 2.0/(self.axisT-self.axisB)
    # oc = -2.0/(of-on)
    # od = -(of+on)/(of-on)
    # oe = -(self.axisT+self.axisB)/(self.axisT-self.axisB)
    # og = -(self.axisR+self.axisL)/(self.axisR-self.axisL)
    # # orthographic
    # self._uPMatrix[0:16] = [oa, 0.0, 0.0,  0.0,
    #                         0.0,  ob, 0.0,  0.0,
    #                         0.0, 0.0,  oc,  0.0,
    #                         og, oe, od, 1.0]

    oa = 2.0/(right-left)
    ob = 2.0/(top-bottom)
    oc = -2.0/(far-near)
    od = -(far+near)/(far-near)
    oe = -(top+bottom)/(top-bottom)
    og = -(right+left)/(right-left)
    # orthographic
    attMatrix[0:16] = [oa, 0.0, 0.0,  0.0,
                        0.0,  ob, 0.0,  0.0,
                        0.0, 0.0,  oc,  0.0,
                        og, oe, od, 1.0]

  def setViewportMatrix(self, viewMatrix, left, right, bottom, top, near, far):
    # return the viewport transformation matrix - mapping screen to NDC
    #   normalised device coordinates
    #   viewport * NDC_cooord = world_coord
    oa = (right-left)/2.0
    ob = (top-bottom)/2.0
    oc = (far-near)/2.0
    og = (right+left)/2.0
    oe = (top+bottom)/2.0
    od = (near+far)/2.0
    # orthographic
    # viewMatrix[0:16] = [oa, 0.0, 0.0,  0.0,
    #                     0.0,  ob, 0.0,  0.0,
    #                     0.0, 0.0,  oc,  0.0,
    #                     og, oe, od, 1.0]
    viewMatrix[0:16] = [oa, 0.0, 0.0,  og,
                        0.0,  ob, 0.0,  oe,
                        0.0, 0.0,  oc,  od,
                        0.0, 0.0, 0.0, 1.0]

  def setGLUniformMatrix4fv(self, uniformLocation=None, count=1, transpose=GL.GL_FALSE, value=None):
    if uniformLocation in self.uniformLocations:
      GL.glUniformMatrix4fv(self.uniformLocations[uniformLocation]
                            , count, transpose, value)
    else:
      raise RuntimeError('Error setting setGLUniformMatrix4fv: %s' % uniformLocation)

  def setGLUniform4fv(self, uniformLocation=None, count=1, value=None):
    if uniformLocation in self.uniformLocations:
      GL.glUniform4fv(self.uniformLocations[uniformLocation]
                      , count, value)
    else:
      raise RuntimeError('Error setting setGLUniform4fv: %s' % uniformLocation)

  def setGLUniform4iv(self, uniformLocation=None, count=1, value=None):
    if uniformLocation in self.uniformLocations:
      GL.glUniform4iv(self.uniformLocations[uniformLocation]
                      , count, value)
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
        raise RuntimeError('Shader compilation failed: %s' % (info))
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
