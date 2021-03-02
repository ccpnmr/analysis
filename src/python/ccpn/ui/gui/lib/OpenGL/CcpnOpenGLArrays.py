"""
GL routines used to draw vertex buffer objects (VBOs)
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-03-02 13:57:31 +0000 (Tue, March 02, 2021) $"
__version__ = "$Revision: 3.0.3 $"
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


from ccpn.ui.gui.lib.OpenGL import GL, GLU, GLUT, VBO


GLRENDERMODE_IGNORE = 0
GLRENDERMODE_DRAW = 1
GLRENDERMODE_RESCALE = 2
GLRENDERMODE_REBUILD = 3

GLREFRESHMODE_NEVER = 0
GLREFRESHMODE_ALWAYS = 1
GLREFRESHMODE_REBUILD = 2

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

        self.color = None
        self.posColours = None
        self.negColours = None

        self.numLists = numLists
        self.blendMode = blendMode
        self.drawMode = drawMode
        self.fillMode = fillMode
        self.dimension = int(dimension)
        self._GLContext = GLContext

        # VAO doesn't work on MacOS
        self.VAO = None
        self.VBOs = None

    def __del__(self):
        """Delete vertex buffer objects on deletion
        """
        if self.VBOs is not None:
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

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # indexed VBOs (vertex buffer objects)
    # Index array - Indices/Vertices/Colour
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def drawIndexArray(self):
        """Draw the vertex buffers in indexed array mode. Arrays are copied from main memory each time.
        Indexed with vertices and colour.
        """
        # getLogger().info('>>> drawIndexArray')

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
        """Define the buffers on the graphics card.
        Indexed mode with vertices and colour.
        If undefined, create new VBOs otherwise overwrite existing.

        Includes:
            vertices:       (x, y) * vertices
            colors:         (R, G, B, a) * vertices
            indices:        array of indexes into vertex list
        """
        # getLogger().info('>>> defineIndexVBO')

        # print("OpenGL: " + str(GL.glGetString(GL.GL_VERSION)))
        # print('glGenVertexArrays Available %s' % bool(GL.glGenVertexArrays))
        # if not hasattr(self, 'VAOs'):
        #     self.VAOs = GL.glGenVertexArrays(1)
        # GL.glBindVertexArray(self.VAOs)                # define VAOs - doesn't work MacOS

        # create the VBOs if they don't exist - reusing will just rewrite the buffers
        if self.VBOs is None:
            self.VBOs = GL.glGenBuffers(3)

        self._defineIndexVBO()

    def _defineIndexVBO(self):
        """Push Indices/Colours/Vertices to graphics card
        """
        sizeVertices = self.vertices.size * self.vertices.itemsize
        sizeColors = self.colors.size * self.colors.itemsize
        sizeIndices = self.indices.size * self.indices.itemsize

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[VERTEX_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeVertices, self.vertices, GL.GL_DYNAMIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[COLOR_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeColors, self.colors, GL.GL_DYNAMIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.VBOs[INDEX_PTR])
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, sizeIndices, self.indices, GL.GL_DYNAMIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateIndexVBO(self):
        """Update the buffers on the graphics card.
        Indexed mode with vertices and colour.
        """
        # getLogger().info('>>> updateIndexVBO')

        # check the VBOs, if they don't exist raise error
        if self.VBOs is None:
            raise RuntimeError('OpenGL Error: cannot update indexVBO: %s' % self)

        self._defineIndexVBO()

    def updateIndexVBOIndices(self):
        """Update the buffers on the graphics card.
        Only the index array.
        """
        # getLogger().info('>>> updateIndexVBOIndices')

        # check the VBOs, if they don't exist raise error
        if self.VBOs is None:
            raise RuntimeError('OpenGL Error: cannot update indexArray: %s' % self)

        sizeIndices = self.indices.size * self.indices.itemsize

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.VBOs[INDEX_PTR])
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, sizeIndices, self.indices, GL.GL_DYNAMIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)

    def drawIndexVBO(self):
        """Draw the vertex buffers in indexed array mode. Arrays are drawn from buffers already bound to graphics card memory.
        Indexed mode with vertices and colour.
        """
        # getLogger().info('>>> drawIndexVBO')

        if not self.indices.size:
            return
        if self.VBOs is None:
            raise RuntimeError('OpenGL Error: cannot draw IndexVBO: %s' % self)

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

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Vertex/Colour array
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def drawVertexColor(self):
        """Draw the vertex buffers in direct array mode. Arrays are copied from main memory each time.
        Only vertices and colour required.
        """
        # getLogger().info('>>> drawVertexColor')

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

    def defineVertexColorVBO(self):
        """Define the buffers on the graphics card.
        Not indexed mode with vertices and colour.
        If undefined, create new VBOs otherwise overwrite existing.

        Includes:
            vertices:       (x, y) * vertices
            colors:         (R, G, B, a) * vertices
        """
        # getLogger().info('>>> defineVertexColorVBO')

        # print("OpenGL: " + str(GL.glGetString(GL.GL_VERSION)))
        # print('glGenVertexArrays Available %s' % bool(GL.glGenVertexArrays))
        # if not hasattr(self, 'VAOs'):
        #     self.VAOs = GL.glGenVertexArrays(1)
        # GL.glBindVertexArray(self.VAOs)                # define VAOs - doesn't work MacOS

        # create the VBOs if they don't exist - reusing will just rewrite the buffers
        if self.VBOs is None:
            self.VBOs = GL.glGenBuffers(2)

        self._defineVertexColorVBO()

    def _defineVertexColorVBO(self):
        """Push Colours/Vertices to graphics card
        """
        # getLogger().info('>>> _defineVertexColorVBO')

        sizeVertices = self.vertices.size * self.vertices.itemsize
        sizeColors = self.colors.size * self.colors.itemsize

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[VERTEX_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeVertices, self.vertices, GL.GL_DYNAMIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[COLOR_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeColors, self.colors, GL.GL_DYNAMIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateVertexColorVBO(self):
        """Update the buffers on the graphics card.
        Direct mode with vertices and colour.
        """
        # getLogger().info('>>> updateVertexColorVBO')

        # check the VBOs, if they don't exist raise error
        if self.VBOs is None:
            raise RuntimeError('OpenGL Error: cannot update vertexColorArray: %s' % self)

        self._defineVertexColorVBO()

    def drawVertexColorVBO(self):
        """Draw the vertex buffers in direct array mode. Arrays are drawn from buffers already bound to graphics card memory.
        Only vertices and colour required.
        """
        # getLogger().info('>>> drawVertexColorVBO')

        if self.VBOs is None:
            raise RuntimeError('OpenGL Error: cannot draw VertexColorVBO: %s' % self)

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
        # getLogger().info('>>> drawVertexNoColor')

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

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # indexed VBOs (vertex buffer objects)
    # Index text array - Indices/Vertices/Colour/Texture Co-ordinates/Attributes
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def drawTextArray(self):
        """Draw the texture buffers in indexed array mode. Arrays are copied from main memory each time.
        Facilitates drawing of fonts.
        """
        # getLogger().info('>>> drawTextArray')

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

    def defineTextArrayVBO(self):
        """Define the buffers on the graphics card.
        Indexed mode with vertices/colours/texture co-ordinates/attribs.
        If undefined, create new VBOs otherwise overwrite existing.

        Includes:
            vertices:       (x, y) * vertices
            colors:         (R, G, B, a) * vertices
            indices:        array of indexes into vertex list
            texcoords       (u, v) * vertices
            attribs         (a, b) * vertices
        """

        # create the VBOs if they don't exist - reusing will just rewrite the buffers
        if self.VBOs is None:
            self.VBOs = GL.glGenBuffers(5)

        self._defineTextArrayVBO()

    def _defineTextArrayVBO(self):
        """Push vertices/colours/texture co-ordinates/attribs/indices to graphics card
        """
        # getLogger().info('>>> _defineTextArrayVBO')

        sizeVertices = self.vertices.size * self.vertices.itemsize
        sizeColors = self.colors.size * self.colors.itemsize
        sizeText = self.texcoords.size * self.texcoords.itemsize
        sizeAttribs = self.attribs.size * self.attribs.itemsize
        sizeIndices = self.indices.size * self.indices.itemsize

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[VERTEX_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeVertices, self.vertices, GL.GL_DYNAMIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[COLOR_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeColors, self.colors, GL.GL_DYNAMIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[TEXT_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeText, self.texcoords, GL.GL_DYNAMIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[ATTRIB_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeAttribs, self.attribs, GL.GL_DYNAMIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.VBOs[INDEX_PTR])
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, sizeIndices, self.indices, GL.GL_DYNAMIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateTextArrayVBO(self):
        """Update the buffers on the graphics card.
        Indexed mode with vertices, colour, texture and attributes.
        """
        # getLogger().info('>>> updateTextArrayVBO')

        # check the VBOs, if they don't exist raise error
        if self.VBOs is None:
            raise RuntimeError('OpenGL Error: cannot update textArrayVBO: %s' % self)

        self._defineTextArrayVBO()

    def updateTextArrayVBOAttribs(self):
        """Update the buffers on the graphics card.
        Only update the attributes used for moving text.
        """
        # getLogger().info('>>> updateTextArrayVBOAttribs')

        # check the VBOs, if they don't exist raise error
        if self.VBOs is None:
            raise RuntimeError('OpenGL Error: cannot update textArrayVBOAttribs: %s' % self)

        sizeAttribs = self.attribs.size * self.attribs.itemsize

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[ATTRIB_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeAttribs, self.attribs, GL.GL_DYNAMIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateTextArrayVBOColour(self):
        """Update the buffers on the graphics card.
        Only update the colour, used for highlighting text.
        """
        # getLogger().info('>>> updateTextArrayVBOColour')

        # check the VBOs, if they don't exist raise error
        if self.VBOs is None:
            raise RuntimeError('OpenGL Error: cannot update textArrayVBOColour: %s' % self)

        sizeColors = self.colors.size * self.colors.itemsize

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBOs[COLOR_PTR])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, sizeColors, self.colors, GL.GL_DYNAMIC_DRAW)

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

    def drawTextArrayVBO(self, enableClientState=False, disableClientState=False):
        """Draw the texture buffers in indexed array mode. Arrays are drawn from buffers already bound to graphics card memory.
        Indexed mode with vertices, colour, texture and attributes.
        """
        # getLogger().info('>>> drawTextArrayVBO')

        # check the VBOs, if they don't exist raise error
        if self.VBOs is None:
            raise RuntimeError('OpenGL Error: cannot drawTextArrayVBO: %s' % self)

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
    """
    Array class to handle symbols.
    """

    def __init__(self, GLContext=None, spectrumView=None, objListView=None):
        super(GLSymbolArray, self).__init__(renderMode=GLRENDERMODE_REBUILD,
                                            blendMode=False, drawMode=GL.GL_LINES,
                                            dimension=2, GLContext=GLContext)
        self.spectrumView = spectrumView
        self.objListView = objListView


class GLLabelArray(GLVertexArray):
    """
    Array class to handle labels.
    """

    def __init__(self, GLContext=None, spectrumView=None, objListView=None):
        super(GLLabelArray, self).__init__(renderMode=GLRENDERMODE_REBUILD,
                                           blendMode=False, drawMode=GL.GL_LINES,
                                           dimension=2, GLContext=GLContext)
        self.spectrumView = spectrumView
        self.objListView = objListView
        self.stringList = []
