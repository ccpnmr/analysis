"""
GL routines used to draw vertex buffer objects (VBOs)
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
__dateModified__ = "$dateModified: 2020-07-23 17:10:54 +0100 (Thu, July 23, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 13:28:13 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
from PyQt5 import QtWidgets
import numpy as np
from ccpn.util.Logging import getLogger


try:
    from OpenGL import GL, GLU, GLUT
    import OpenGL.arrays.vbo as VBO

except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL CCPN",
                                   "PyOpenGL must be installed to run this example.")
    sys.exit(1)

GLRENDERMODE_IGNORE = 0
GLRENDERMODE_DRAW = 1
GLRENDERMODE_RESCALE = 2
GLRENDERMODE_REBUILD = 3

GLREFRESHMODE_NEVER = 0
GLREFRESHMODE_ALWAYS = 1
GLREFRESHMODE_REBUILD = 2

ENABLE_VBOS = True

VERTEX_PTR = 0
COLOR_PTR = 1
INDEX_PTR = 2
ATTRIB_PTR = 3
TEXT_PTR = 4


class GLVertexArray():
    def __init__(self, numLists=1,
                 renderMode=GLRENDERMODE_IGNORE,
                 refreshMode=GLREFRESHMODE_NEVER,
                 blendMode=False,
                 drawMode=GL.GL_LINES,
                 fillMode=None,
                 dimension=3,
                 GLContext=None,
                 clearArrays=True):
        """Initialise the vertexArray properties

        :param numLists: deprecated, left over from original glLists, will remove soon
        :param renderMode: rendering type, flag used to determine when to rebuild, refresh or redraw the buffers
        :param refreshMode: currently not used
        :param blendMode: flag to specify whether solid or transparent
        :param drawMode: drawing mode as lines, polygons or filled
        :param fillMode: solid or wireframe
        :param dimension: number of axes required, currently 2 or 3d
        :param GLContext: pointer to the GL context
        :param clearArrays: flag to clear all arrays on initialise
        """
        self.initialise(numLists=numLists, renderMode=renderMode, refreshMode=refreshMode,
                        blendMode=blendMode, drawMode=drawMode, fillMode=fillMode,
                        dimension=dimension, GLContext=GLContext, clearArrays=clearArrays)

    def initialise(self, numLists=1, renderMode=GLRENDERMODE_IGNORE,
                   refreshMode=GLREFRESHMODE_NEVER,
                   blendMode=False, drawMode=GL.GL_LINES, fillMode=None,
                   dimension=3,
                   GLContext=None,
                   clearArrays=True):
        """Initialise the vertexArray object.
        """
        self._parent = GLContext
        self.renderMode = renderMode
        self.refreshMode = refreshMode

        if clearArrays:
            self.clearArrays()

        # self.lineWidths = [0.0, 0.0]
        self.color = None
        self.posColours = None
        self.negColours = None

        self.numLists = numLists
        self.blendMode = blendMode
        self.drawMode = drawMode
        self.fillMode = fillMode
        self.dimension = int(dimension)
        self._GLContext = GLContext

        # if not hasattr(self, 'VBOs'):
        #     self.VBOs = GL.glGenBuffers(3)

    def __del__(self):
        """Delete vertex bufer objects on deletion
        """
        if hasattr(self, 'VBOs'):
            GL.glDeleteBuffers(len(self.VBOs), self.VBOs)

    def clearArrays(self):
        """Clear and reset all arrays
        """
        # set everything to 32 bit for openGL VBOs, indices are uint32s, everything else is float32
        self.indices = np.array([], dtype=np.uint32)
        self.vertices = np.array([], dtype=np.float32)
        self.colors = np.array([], dtype=np.float32)
        self.texcoords = np.array([], dtype=np.float32)
        self.attribs = np.array([], dtype=np.float32)
        self.offsets = np.array([], dtype=np.float32)
        self.pids = np.array([], dtype=np.object_)
        self.numVertices = 0

    def clearVertices(self):
        """Clear the vertex array only.
        """
        self.vertices = np.array([], dtype=np.float32)
        self.numVertices = 0

    def drawIndexArray(self):
        """Draw the vertex buffers in indexed array mode. Arrays are copied from main memory each time.
        Indexed with vertices and colour.
        """

        # getLogger().info('>>>drawIndexArray')

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

    def updateIndexVBOIndices(self, enableVBO=False):
        """Update the buffers on the graphics card.
        Update only the index array.
        """
        if not (ENABLE_VBOS and enableVBO):
            return

        # getLogger().info('>>>defineIndexVBO')

        # if not hasattr(self, 'VAOs'):
        #     self.VAOs = GL.glGenVertexArrays(1)
        # GL.glBindVertexArray(self.VAOs)                # define VAOs

        # check the VBOs, if they don't exist raise error
        if not hasattr(self, 'VBOs'):
            raise RuntimeError('OpenGL Error: cannot update indexArray: %s' % self)

        sizeIndices = self.indices.size * self.indices.itemsize

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.VBOs[INDEX_PTR])
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, sizeIndices, self.indices, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)

    def updateIndexVBO(self, enableVBO=False):
        """Update the buffers on the graphics card.
        Indexed mode with vertices and colour.
        """
        if not (ENABLE_VBOS and enableVBO):
            return

        # getLogger().info('>>>defineIndexVBO')

        # if not hasattr(self, 'VAOs'):
        #     self.VAOs = GL.glGenVertexArrays(1)
        # GL.glBindVertexArray(self.VAOs)                # define VAOs

        # check the VBOs, if they don't exist raise error
        if not hasattr(self, 'VBOs'):
            raise RuntimeError('OpenGL Error: cannot update indexArray: %s' % self)

        sizeVertices = self.vertices.size * self.vertices.itemsize
        sizeColors = self.colors.size * self.colors.itemsize
        sizeIndices = self.indices.size * self.indices.itemsize

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[VERTEX_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeVertices, self.vertices, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[COLOR_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeColors, self.colors, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.VBOs[INDEX_PTR])
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, sizeIndices, self.indices, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def defineIndexVBO(self, enableVBO=False):
        """Define the buffers on the graphics card.
        If undefined, create new VBOs otherwise overwrite existing.
        """
        if not (ENABLE_VBOS and enableVBO):
            return

        # getLogger().info('>>>defineIndexVBO')

        # if not hasattr(self, 'VAOs'):
        #     self.VAOs = GL.glGenVertexArrays(1)
        # GL.glBindVertexArray(self.VAOs)                # define VAOs

        # create the VBOs if they don't exist - reusing will just rewrite the buffers
        if not hasattr(self, 'VBOs'):
            self.VBOs = GL.glGenBuffers(3)

        sizeVertices = self.vertices.size * self.vertices.itemsize
        sizeColors = self.colors.size * self.colors.itemsize
        sizeIndices = self.indices.size * self.indices.itemsize

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[VERTEX_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeVertices, self.vertices, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[COLOR_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeColors, self.colors, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.VBOs[INDEX_PTR])
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, sizeIndices, self.indices, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def drawIndexVBO(self, enableVBO=False):
        """Draw the vertex buffers in indexed array mode. Arrays are drawn from buffers already bound to graphics card memory.
        Indexed mode with vertices and colour.
        """
        if not (ENABLE_VBOS and enableVBO):

            # call the normal drawIndex routine
            self.drawIndexArray()
        else:

            # getLogger().info('>>>drawIndexVBO')
            if not self.indices.size:
                return

            if self.blendMode:
                GL.glEnable(GL.GL_BLEND)
            if self.fillMode is not None:
                GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self.fillMode)

            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glEnableClientState(GL.GL_COLOR_ARRAY)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[VERTEX_PTR])
            GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, None)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[COLOR_PTR])
            GL.glColorPointer(4, GL.GL_FLOAT, 0, None)

            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.VBOs[INDEX_PTR])
            GL.glDrawElements(self.drawMode, len(self.indices), GL.GL_UNSIGNED_INT, None)

            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDisableClientState(GL.GL_COLOR_ARRAY)

            if self.blendMode:
                GL.glDisable(GL.GL_BLEND)

    def drawIndexArrayNoColor(self):
        """Draw the vertex buffers in indexed array mode. Arrays are copied from main memory each time.
        Indexed mode using only vertices, no colour.
        """

        # getLogger().info('>>>drawIndexArrayNoColor')

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
        """Draw the vertex buffers in direct array mode. Arrays are copied from main memory each time.
        Only vertices and colour required.
        """

        # getLogger().info('>>>drawVertexColor')

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

    def updateVertexColorVBO(self, enableVBO=False):
        """Update the buffers on the graphics card.
        Direct mode with vertices and colour.
        """
        if not (ENABLE_VBOS and enableVBO):
            return

        # getLogger().info('>>>defineVertexColorVBO')

        # check the VBOs, if they don't exist raise error
        if not hasattr(self, 'VBOs'):
            raise RuntimeError('OpenGL Error: cannot update vertexColorArray: %s' % self)

        sizeVertices = self.vertices.size * self.vertices.itemsize
        sizeColors = self.colors.size * self.colors.itemsize

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[VERTEX_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeVertices, self.vertices, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[COLOR_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeColors, self.colors, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def defineVertexColorVBO(self, enableVBO=False):
        """Define the buffers on the graphics card.
        If undefined, create new VBOs otherwise overwrite existing.
        """
        if not (ENABLE_VBOS and enableVBO):
            return

        # getLogger().info('>>>defineVertexColorVBO')

        # create the VBOs if they don't exist - reusing will just rewrite the buffers
        if not hasattr(self, 'VBOs'):
            self.VBOs = GL.glGenBuffers(2)

        sizeVertices = self.vertices.size * self.vertices.itemsize
        sizeColors = self.colors.size * self.colors.itemsize

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[VERTEX_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeVertices, self.vertices, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[COLOR_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeColors, self.colors, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def drawVertexColorVBO(self, enableVBO=False):
        """Draw the vertex buffers in direct array mode. Arrays are drawn from buffers already bound to graphics card memory.
        Only vertices and colour required.
        """
        if not (ENABLE_VBOS and enableVBO):

            # call the normal drawVertex routine
            self.drawVertexColor()
        else:

            # getLogger().info('>>>drawVertexColorVBO')

            if self.blendMode:
                GL.glEnable(GL.GL_BLEND)
            if self.fillMode is not None:
                GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self.fillMode)

            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glEnableClientState(GL.GL_COLOR_ARRAY)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[VERTEX_PTR])
            GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, None)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[COLOR_PTR])
            GL.glColorPointer(4, GL.GL_FLOAT, 0, None)

            # GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, self.vertices)
            # GL.glColorPointer(4, GL.GL_FLOAT, 0, self.colors)
            GL.glDrawArrays(self.drawMode, 0, self.numVertices)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDisableClientState(GL.GL_COLOR_ARRAY)

            if self.blendMode:
                GL.glDisable(GL.GL_BLEND)

    def drawVertexNoColor(self):
        """Draw the vertex buffers in direct array mode. Arrays are copied from main memory each time.
        Only vertices are required.
        """

        # getLogger().info('>>>drawVertexNoColor')

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
        """Draw the texture buffers in indexed array mode. Arrays are copied from main memory each time.
        Facilitates drawing of fonts.
        """
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

    def defineTextArrayVBO(self, enableVBO=False):
        """Define the buffers on the graphics card.
        If undefined, create new VBOs otherwise overwrite existing.
        """
        if not (ENABLE_VBOS and enableVBO):
            return

        # create the VBOs if they don't exist - reusing will just rewrite the buffers
        if not hasattr(self, 'VBOs'):
            self.VBOs = GL.glGenBuffers(5)

        sizeVertices = self.vertices.size * self.vertices.itemsize
        sizeColors = self.colors.size * self.colors.itemsize
        sizeText = self.texcoords.size * self.texcoords.itemsize
        sizeAttribs = self.attribs.size * self.attribs.itemsize
        sizeIndices = self.indices.size * self.indices.itemsize

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[VERTEX_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeVertices, self.vertices, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[COLOR_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeColors, self.colors, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[TEXT_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeText, self.texcoords, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[ATTRIB_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeAttribs, self.attribs, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.VBOs[INDEX_PTR])
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, sizeIndices, self.indices, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateTextArrayVBO(self, enableVBO=False):
        """Update the buffers on the graphics card.
        Indexed mode with vertices, colour, texture and attributes.
        """
        if not (ENABLE_VBOS and enableVBO):
            return

        # check the VBOs, if they don't exist raise error
        if not hasattr(self, 'VBOs'):
            raise RuntimeError('OpenGL Error: cannot update textArray: %s' % self)

        sizeVertices = self.vertices.size * self.vertices.itemsize
        sizeColors = self.colors.size * self.colors.itemsize
        sizeText = self.texcoords.size * self.texcoords.itemsize
        sizeAttribs = self.attribs.size * self.attribs.itemsize
        sizeIndices = self.indices.size * self.indices.itemsize

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[VERTEX_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeVertices, self.vertices, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[COLOR_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeColors, self.colors, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[TEXT_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeText, self.texcoords, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[ATTRIB_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeAttribs, self.attribs, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.VBOs[INDEX_PTR])
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, sizeIndices, self.indices, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateTextArrayVBOAttribs(self, enableVBO=False):
        """Update the buffers on the graphics card.
        Only update the attributes, used for moving text.
        """
        if not (ENABLE_VBOS and enableVBO):
            return

        # check the VBOs, if they don't exist raise error
        if not hasattr(self, 'VBOs'):
            raise RuntimeError('OpenGL Error: cannot update attribs: %s' % self)

        sizeAttribs = self.attribs.size * self.attribs.itemsize

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[ATTRIB_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeAttribs, self.attribs, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateTextArrayVBOColour(self, enableVBO=False):
        """Update the buffers on the graphics card.
        Only update the colour, used for highlighting text.
        """
        if not (ENABLE_VBOS and enableVBO):
            return

        # check the VBOs, if they don't exist raise error
        if not hasattr(self, 'VBOs'):
            raise RuntimeError('OpenGL Error: cannot update attribs: %s' % self)

        sizeColors = self.colors.size * self.colors.itemsize

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[COLOR_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeColors, self.colors, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    # def enableTextClientState(self):
    #     GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    #     GL.glEnableClientState(GL.GL_COLOR_ARRAY)
    #     GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
    #     GL.glEnableVertexAttribArray(self._GLContext._glClientIndex)
    #
    # def disableTextClientState(self):
    #     GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
    #     GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    #     GL.glDisableClientState(GL.GL_COLOR_ARRAY)
    #     GL.glDisableVertexAttribArray(self._GLContext._glClientIndex)

    def drawTextArrayVBO(self, enableVBO=False, enableClientState=False, disableClientState=False):
        """Draw the texture buffers in indexed array mode. Arrays are drawn from buffers already bound to graphics card memory.
        Indexed mode with vertices, colour, texture and attributes.
        """
        if not (ENABLE_VBOS and enableVBO):

            # call the normal drawTextArray routine
            self.drawTextArray()
        else:

            if self.blendMode:
                GL.glEnable(GL.GL_BLEND)

            if enableClientState:
                GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
                GL.glEnableClientState(GL.GL_COLOR_ARRAY)
                GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
                GL.glEnableVertexAttribArray(self._GLContext._glClientIndex)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[VERTEX_PTR])
            GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, None)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[COLOR_PTR])
            GL.glColorPointer(4, GL.GL_FLOAT, 0, None)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[TEXT_PTR])
            GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, None)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[ATTRIB_PTR])
            GL.glVertexAttribPointer(self._GLContext._glClientIndex, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)

            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.VBOs[INDEX_PTR])
            GL.glDrawElements(self.drawMode, len(self.indices), GL.GL_UNSIGNED_INT, None)

            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

            if disableClientState:
                GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
                GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
                GL.glDisableClientState(GL.GL_COLOR_ARRAY)
                GL.glDisableVertexAttribArray(self._GLContext._glClientIndex)

            if self.blendMode:
                GL.glDisable(GL.GL_BLEND)


class GLSymbolArray(GLVertexArray):
    """Array class to handle symbols.
    """
    def __init__(self, GLContext=None, spectrumView=None, objListView=None):
        super(GLSymbolArray, self).__init__(renderMode=GLRENDERMODE_REBUILD,
                                            blendMode=False, drawMode=GL.GL_LINES,
                                            dimension=2, GLContext=GLContext)
        self.spectrumView = spectrumView
        self.objListView = objListView


class GLLabelArray(GLVertexArray):
    """Array class to handle labels.
    """
    def __init__(self, GLContext=None, spectrumView=None, objListView=None):
        super(GLLabelArray, self).__init__(renderMode=GLRENDERMODE_REBUILD,
                                           blendMode=False, drawMode=GL.GL_LINES,
                                           dimension=2, GLContext=GLContext)
        self.spectrumView = spectrumView
        self.objListView = objListView
        self.stringList = []
