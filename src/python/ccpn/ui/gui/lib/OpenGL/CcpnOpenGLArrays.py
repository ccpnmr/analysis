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
from PyQt5 import QtWidgets
import numpy as np
try:
  from OpenGL import GL, GLU, GLUT
except ImportError:
  app = QtWidgets.QApplication(sys.argv)
  QtWidgets.QMessageBox.critical(None, "OpenGL hellogl",
          "PyOpenGL must be installed to run this example.")
  sys.exit(1)

GLRENDERMODE_IGNORE = 0
GLRENDERMODE_DRAW = 1
GLRENDERMODE_RESCALE = 2
GLRENDERMODE_REBUILD = 3

GLREFRESHMODE_NEVER = 0
GLREFRESHMODE_ALWAYS = 1
GLREFRESHMODE_REBUILD = 2


class GLVertexArray():
  def __init__(self, numLists=1,
               renderMode=GLRENDERMODE_IGNORE,
               refreshMode = GLREFRESHMODE_NEVER,
               blendMode=False,
               drawMode=GL.GL_LINES,
               fillMode=None,
               dimension=3,
               GLContext=None):

    self.initialise(numLists=numLists, renderMode=renderMode, refreshMode=refreshMode,
                    blendMode=blendMode, drawMode=drawMode, fillMode=fillMode,
                    dimension=dimension, GLContext=GLContext)

  def initialise(self, numLists=1, renderMode=GLRENDERMODE_IGNORE,
                refreshMode=GLREFRESHMODE_NEVER,
                blendMode=False, drawMode=GL.GL_LINES, fillMode=None,
                dimension=3,
                GLContext=None):

    self.parent = GLContext
    self.renderMode = renderMode
    self.refreshMode = refreshMode
    self.vertices = np.empty(0, dtype=np.float32)
    self.indices = np.empty(0, dtype=np.uint)
    self.colors = np.empty(0, dtype=np.float32)
    self.texcoords= np.empty(0, dtype=np.float32)
    self.attribs = np.empty(0, dtype=np.float32)
    self.offsets = np.empty(0, dtype=np.float32)
    self.pids = np.empty(0, dtype=np.object_)
    self.lineWidths = [0.0, 0.0]
    self.color = None
    self.posColour = None
    self.negColour = None

    self.numVertices = 0

    self.numLists = numLists
    self.blendMode = blendMode
    self.drawMode = drawMode
    self.fillMode = fillMode
    self.dimension = int(dimension)
    self._GLContext = GLContext

  def _close(self):
    # GL.glDeleteLists(self.GLLists, self.numLists)
    pass

  def clearArrays(self):
    self.vertices = np.empty(0, dtype=np.float32)
    self.indices = np.empty(0, dtype=np.uint)
    self.colors = np.empty(0, dtype=np.float32)
    self.texcoords= np.empty(0, dtype=np.float32)
    self.attribs = np.empty(0, dtype=np.float32)
    self.offsets = np.empty(0, dtype=np.float32)
    self.pids = np.empty(0, dtype=np.object_)
    self.numVertices = 0

  def clearVertices(self):
    self.vertices = np.empty(0, dtype=np.float32)
    self.numVertices = 0

  def drawIndexArray(self):
    if self.blendMode:
      GL.glEnable(GL.GL_BLEND)
    if self.fillMode is not None:
      GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self.fillMode)

    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    GL.glEnableClientState(GL.GL_COLOR_ARRAY)

    GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, self.vertices)
    GL.glColorPointer(4, GL.GL_FLOAT, 0, self.colors)
    GL.glDrawElements(self.drawMode, len(self.indices), GL.GL_UNSIGNED_INT, self.indices)

    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    GL.glDisableClientState(GL.GL_COLOR_ARRAY)

    if self.blendMode:
      GL.glDisable(GL.GL_BLEND)

  def drawIndexArrayNoColor(self):
    if self.blendMode:
      GL.glEnable(GL.GL_BLEND)
    if self.fillMode is not None:
      GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self.fillMode)

    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)

    GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, self.vertices)
    GL.glDrawElements(self.drawMode, len(self.indices), GL.GL_UNSIGNED_INT, self.indices)

    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)

    if self.blendMode:
      GL.glDisable(GL.GL_BLEND)

  def drawVertexColor(self):
    if self.blendMode:
      GL.glEnable(GL.GL_BLEND)
    if self.fillMode is not None:
      GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self.fillMode)

    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    GL.glEnableClientState(GL.GL_COLOR_ARRAY)

    GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, self.vertices)
    GL.glColorPointer(4, GL.GL_FLOAT, 0, self.colors)
    GL.glDrawArrays(self.drawMode, 0, self.numVertices)

    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    GL.glDisableClientState(GL.GL_COLOR_ARRAY)

    if self.blendMode:
      GL.glDisable(GL.GL_BLEND)

  def drawVertexNoColor(self):
    if self.blendMode:
      GL.glEnable(GL.GL_BLEND)
    if self.fillMode is not None:
      GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self.fillMode)

    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)

    GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, self.vertices)
    GL.glDrawArrays(self.drawMode, 0, self.numVertices)

    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)

    if self.blendMode:
      GL.glDisable(GL.GL_BLEND)

  def drawTextArray(self):
    if self.blendMode:
      GL.glEnable(GL.GL_BLEND)

    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    GL.glEnableClientState(GL.GL_COLOR_ARRAY)
    GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
    GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, self.vertices)
    GL.glColorPointer(4, GL.GL_FLOAT, 0, self.colors)
    GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, self.texcoords)

    # this is for passing extra attributes in
    GL.glEnableVertexAttribArray(1)
    GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, self.attribs)

    GL.glDrawElements(self.drawMode, len(self.indices), GL.GL_UNSIGNED_INT, self.indices)

    GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    GL.glDisableClientState(GL.GL_COLOR_ARRAY)
    GL.glDisableVertexAttribArray(1)

    if self.blendMode:
      GL.glDisable(GL.GL_BLEND)


class GLPeakListArray(GLVertexArray):
  def __init__(self, GLContext=None, spectrumView=None, peakListView=None):
    super(GLPeakListArray, self).__init__(renderMode=GLRENDERMODE_REBUILD,
                                          blendMode=False, drawMode=GL.GL_LINES,
                                          dimension=2, GLContext=GLContext)
    self.spectrumView = spectrumView
    self.peakListView = peakListView


class GLPeakLabelsArray(GLVertexArray):
  def __init__(self, GLContext=None, spectrumView=None, peakListView=None):
    super(GLPeakLabelsArray, self).__init__(renderMode=GLRENDERMODE_REBUILD,
                                          blendMode=False, drawMode=GL.GL_LINES,
                                          dimension=2, GLContext=GLContext)
    self.spectrumView = spectrumView
    self.peakListView = peakListView
    self.stringList = []
