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
import ctypes


try:
    from OpenGL import GL, GLU, GLUT
    import OpenGL.arrays.vbo as VBO

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

ENABLE_VBOS = False


class GLVertexArray():
    def __init__(self, numLists=1,
                 renderMode=GLRENDERMODE_IGNORE,
                 refreshMode=GLREFRESHMODE_NEVER,
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
        self.indices = np.empty(0, dtype=np.uint32)
        self.colors = np.empty(0, dtype=np.float32)
        self.texcoords = np.empty(0, dtype=np.float32)
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

    def __del__(self):
        if hasattr(self, 'VBOs'):
            GL.glDeleteLists(3, self.VBOs)

    def clearArrays(self):
        self.vertices = np.empty(0, dtype=np.float32)
        self.indices = np.empty(0, dtype=np.uint32)
        self.colors = np.empty(0, dtype=np.float32)
        self.texcoords = np.empty(0, dtype=np.float32)
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

    def defineIndexVBO(self):
        if not ENABLE_VBOS:
            return

        # if not hasattr(self, 'VAOs'):
        #     self.VAOs = GL.glGenVertexArrays(1)
        # GL.glBindVertexArray(self.VAOs)                # define VAOs

        if not hasattr(self, 'VBOs'):
            self.VBOs = GL.glGenBuffers(3)

        sizeVertices = GL.arrays.ArrayDatatype.arrayByteCount(self.vertices)
        sizeColors = GL.arrays.ArrayDatatype.arrayByteCount(self.colors)
        sizeIndices = GL.arrays.ArrayDatatype.arrayByteCount(self.indices)

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[0])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeVertices, np.array(self.vertices, dtype=np.float32), GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[1])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeColors, self.colors, GL.GL_STATIC_DRAW)

        # why is this not GL_ELEMENT_ARRAY_BUFFER?
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[2])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeIndices, self.indices, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        return

        self.TESTvertices = np.array([5, 110, 10, 110, 10, 120, 5, 120,
                                      6, 112, 11, 107, 9, 122, 7, 127,
                                      7, 113, 15, 128, 11, 116, 7, 126,
                                      8, 115, 15, 125, 11, 115, 7, 128,
                                      9, 118, 15, 113, 15, 122, 6, 114,
                                      8, 119, 15, 114, 15, 121, 6, 112,
                                      7, 120, 15, 121, 12, 103, 8, 108,
                                      5, 120, 15, 121, 12, 106, 8, 115],
                                     dtype=np.float32)
        self.TESTcolors = np.array([1.0, 0.2, 0.1, 1.0,
                                    0.3, 1.0, 0.1, 1.0,
                                    0.1, 0.2, 1.0, 1.0,
                                    1.0, 0.8, 0.1, 1.0,
                                    1.0, 0.2, 0.1, 1.0,
                                    0.3, 1.0, 0.1, 1.0,
                                    0.1, 0.2, 1.0, 1.0,
                                    1.0, 0.8, 0.1, 1.0,
                                    1.0, 0.2, 0.1, 1.0,
                                    0.3, 1.0, 0.1, 1.0,
                                    0.1, 0.2, 1.0, 1.0,
                                    1.0, 0.8, 0.1, 1.0,
                                    1.0, 0.2, 0.1, 1.0,
                                    0.3, 1.0, 0.1, 1.0,
                                    0.1, 0.2, 1.0, 1.0,
                                    1.0, 0.8, 0.1, 1.0
                                    ],
                                   dtype=np.float32)
        self.TESTindices = np.array([0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 0],
                                    dtype=np.uint32)

        sizeVertices = GL.arrays.ArrayDatatype.arrayByteCount(self.TESTvertices)
        sizeColors = GL.arrays.ArrayDatatype.arrayByteCount(self.TESTcolors)
        sizeIndices = GL.arrays.ArrayDatatype.arrayByteCount(self.TESTindices)
        memVertices = GL.arrays.ArrayDatatype.voidDataPointer(self.TESTvertices)
        memColors = GL.arrays.ArrayDatatype.voidDataPointer(self.TESTcolors)
        memIndices = GL.arrays.ArrayDatatype.voidDataPointer(self.TESTindices)

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[0])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeVertices, memVertices, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[1])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeColors, memColors, GL.GL_STATIC_DRAW)

        # why is this not GL_ELEMENT_ARRAY_BUFFER?
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[2])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeIndices, memIndices, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def drawIndexVBO(self):
        if not ENABLE_VBOS:
            self.drawIndexArray()
        else:

            if self.blendMode:
                GL.glEnable(GL.GL_BLEND)
            if self.fillMode is not None:
                GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self.fillMode)

            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glEnableClientState(GL.GL_COLOR_ARRAY)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[0])
            GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, None)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[1])
            GL.glColorPointer(4, GL.GL_FLOAT, 0, None)

            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.VBOs[2])
            GL.glDrawElements(self.drawMode, len(self.indices), GL.GL_UNSIGNED_INT, None)

            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDisableClientState(GL.GL_COLOR_ARRAY)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)

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

    def drawVertexColorVBO(self):
        if not ENABLE_VBOS:
            self.drawVertexColor()
        else:

            if self.blendMode:
                GL.glEnable(GL.GL_BLEND)
            if self.fillMode is not None:
                GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self.fillMode)

            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glEnableClientState(GL.GL_COLOR_ARRAY)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[0])
            GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, None)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[1])
            GL.glColorPointer(4, GL.GL_FLOAT, 0, None)

            # GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, self.vertices)
            # GL.glColorPointer(4, GL.GL_FLOAT, 0, self.colors)
            GL.glDrawArrays(self.drawMode, 0, self.numVertices)

            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDisableClientState(GL.GL_COLOR_ARRAY)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

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


class GLSymbolArray(GLVertexArray):
    def __init__(self, GLContext=None, spectrumView=None, objListView=None):
        super(GLSymbolArray, self).__init__(renderMode=GLRENDERMODE_REBUILD,
                                            blendMode=False, drawMode=GL.GL_LINES,
                                            dimension=2, GLContext=GLContext)
        self.spectrumView = spectrumView
        self.objListView = objListView


class GLLabelArray(GLVertexArray):
    def __init__(self, GLContext=None, spectrumView=None, objListView=None):
        super(GLLabelArray, self).__init__(renderMode=GLRENDERMODE_REBUILD,
                                           blendMode=False, drawMode=GL.GL_LINES,
                                           dimension=2, GLContext=GLContext)
        self.spectrumView = spectrumView
        self.objListView = objListView
        self.stringList = []
