"""
GL routines used to draw vertex buffer objects (VBOs)
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-09-15 19:14:27 +0100 (Fri, September 15, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 13:28:13 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import contextlib
import numpy as np
from ccpn.ui.gui.lib.OpenGL import GL
from ccpn.ui.gui.lib.OpenGL import VBO
from ccpn.util.Logging import getLogger
from ccpn.util.Common import isWindowsOS


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
_USAGE = GL.GL_DYNAMIC_DRAW

_DEBUG = False


#=========================================================================================
# _VBOGLVertexArray
#=========================================================================================

class _VBOGLVertexArray:
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

        self._vertexVBO = None
        self._colorVBO = None
        self._attribVBO = None
        self._textureVBO = None
        self._indexVBO = None

    # def __del__(self):
    #     """Delete vertex buffer objects on deletion
    #     """
    #     if self.VBOs is not None:
    #         GL.glDeleteBuffers(len(self.VBOs), self.VBOs)

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

    def _delete(self):
        """Clean up everything for deletion
        """
        del self.indices
        del self.vertices
        del self.colors
        del self.texcoords
        del self.attribs
        del self.offsets
        del self.pids
        self._GLContext = None

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # indexed VBOs (vertex buffer objects)
    # Index array - Indices/Vertices/Colour
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def drawIndexArray(self):
        """Draw the vertex buffers in indexed array mode. Arrays are copied from main memory each time.
        Indexed with vertices and colour.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawIndexArray')

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
            _
            attribs:        array of float for defining aliasPosition
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.defineIndexVBO')

        # create the VBOs if they don't exist - reusing will just rewrite the buffers
        if self._vertexVBO is None:
            _float = np.array([], dtype=np.float32)
            _int = np.array([], dtype=np.uint32)
            self._vertexVBO = VBO(_float, usage=_USAGE)
            self._colorVBO = VBO(_float, usage=_USAGE)
            self._indexVBO = VBO(_int, usage=_USAGE, target=GL.GL_ELEMENT_ARRAY_BUFFER)
        self._defineIndexVBO()

    def _defineIndexVBO(self):
        """Push Indices/Colours/Vertices to graphics card
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}._defineIndexVBO')

        self._vertexVBO.set_array(self.vertices)
        self._vertexVBO.bind()
        self._colorVBO.set_array(self.colors)
        self._colorVBO.bind()
        self._indexVBO.set_array(self.indices)
        self._indexVBO.bind()

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateIndexVBO(self):
        """Update the buffers on the graphics card.
        Indexed mode with vertices and colour.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.updateIndexVBO')

        if self._vertexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.updateIndexVBO: OpenGL Error - {self}')
            return

        self._defineIndexVBO()

    def updateIndexVBOIndices(self):
        """Update the buffers on the graphics card.
        Only the index array.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.updateIndexVBOIndices')

        if self._indexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.updateIndexVBOIndices: OpenGL Error - {self}')
            return

        self._indexVBO.set_array(self.indices)
        self._indexVBO.bind()

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)

    def drawIndexVBO(self):
        """Draw the vertex buffers in indexed array mode. Arrays are drawn from buffers already bound to graphics card memory.
        Indexed mode with vertices and colour.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawIndexVBO')

        if not self.indices.size:
            return
        if self._indexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.drawIndexVBO: OpenGL Error - {self}')
            return

        if self.blendMode:
            GL.glEnable(GL.GL_BLEND)
        if self.fillMode is not None:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self.fillMode)

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)

        self._vertexVBO.bind()
        GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, self._vertexVBO)
        self._colorVBO.bind()
        GL.glColorPointer(4, GL.GL_FLOAT, 0, self._colorVBO)
        self._indexVBO.bind()
        GL.glDrawElements(self.drawMode, len(self.indices), GL.GL_UNSIGNED_INT, self._indexVBO)

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
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawIndexArrayNoColor')

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
    # indexed VBOs (vertex buffer objects)
    # Index array - Indices/Vertices/Colour/Attribs
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def defineAliasedIndexVBO(self):
        """Define the buffers on the graphics card.
        Indexed mode with vertices and colour.
        If undefined, create new VBOs otherwise overwrite existing.

        Includes:
            vertices:       (x, y) * vertices
            colors:         (R, G, B, a) * vertices
            indices:        array of indexes into vertex list
            _
            attribs:        array of float for defining aliasPosition
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.defineAliasedIndexVBO')

        # create the VBOs if they don't exist - reusing will just rewrite the buffers
        if self._vertexVBO is None:
            _float = np.array([], dtype=np.float32)
            _int = np.array([], dtype=np.uint32)
            self._vertexVBO = VBO(_float, usage=_USAGE)
            self._colorVBO = VBO(_float, usage=_USAGE)
            self._attribVBO = VBO(_float, usage=_USAGE)
            self._indexVBO = VBO(_int, usage=_USAGE, target=GL.GL_ELEMENT_ARRAY_BUFFER)
        self._defineAliasedIndexVBO()

    def _defineAliasedIndexVBO(self):
        """Push Indices/Colours/Vertices/attribs to graphics card
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}._defineAliasedIndexVBO')

        if self._vertexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}._defineAliasedIndexVBO: OpenGL Error - {self}')
            return

        self._vertexVBO.set_array(self.vertices)
        self._vertexVBO.bind()
        self._colorVBO.set_array(self.colors)
        self._colorVBO.bind()
        self._attribVBO.set_array(self.attribs)
        self._attribVBO.bind()
        self._indexVBO.set_array(self.indices)
        self._indexVBO.bind()

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateAliasedIndexVBO(self):
        """Update the buffers on the graphics card.
        Indexed mode with vertices and colour.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.updateAliasedIndexVBO')

        if self._vertexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.updateAliasedIndexVBO: OpenGL Error - {self}')
            return

        self._defineAliasedIndexVBO()

    def updateAliasedIndexVBOIndices(self):
        """Update the buffers on the graphics card.
        Only the index array.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.updateAliasedIndexVBOIndices')

        if self._indexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.updateAliasedIndexVBOIndices: OpenGL Error - {self}')
            return

        self._indexVBO.set_array(self.indices)
        self._indexVBO.bind()

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)

    def drawAliasedIndexVBO(self):
        """Draw the vertex buffers in indexed array mode. Arrays are drawn from buffers already bound to graphics card memory.
        Indexed mode with vertices and colour.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawAliasedIndexVBO')

        if not self.indices.size:
            return
        if self._indexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.drawAliasedIndexVBO: OpenGL Error - {self}')
            return

        if self.blendMode:
            GL.glEnable(GL.GL_BLEND)
        if self.fillMode is not None:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self.fillMode)

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)
        GL.glEnableVertexAttribArray(1)

        self._vertexVBO.bind()
        GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, self._vertexVBO)
        self._colorVBO.bind()
        GL.glColorPointer(4, GL.GL_FLOAT, 0, self._colorVBO)
        self._attribVBO.bind()
        GL.glVertexAttribPointer(1, 1, GL.GL_FLOAT, GL.GL_FALSE, 0, self._attribVBO)
        self._indexVBO.bind()
        GL.glDrawElements(self.drawMode, len(self.indices), GL.GL_UNSIGNED_INT, self._indexVBO)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_COLOR_ARRAY)
        GL.glDisableVertexAttribArray(1)

        if self.blendMode:
            GL.glDisable(GL.GL_BLEND)

    def drawAliasedIndexArrayNoColor(self):
        """Draw the vertex buffers in indexed array mode. Arrays are copied from main memory each time.
        Indexed mode using only vertices, no colour.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawAliasedIndexArrayNoColor')

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
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawVertexColor')

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
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.defineVertexColorVBO')

        # create the VBOs if they don't exist - reusing will just rewrite the buffers
        if self._vertexVBO is None:
            _float = np.array([], dtype=np.float32)
            self._vertexVBO = VBO(_float, usage=_USAGE)
            self._colorVBO = VBO(_float, usage=_USAGE)
        self._defineVertexColorVBO()

    def _defineVertexColorVBO(self):
        """Push Colours/Vertices to graphics card
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}._defineVertexColorVBO')

        self._vertexVBO.set_array(self.vertices)
        self._vertexVBO.bind()
        self._colorVBO.set_array(self.colors)
        self._colorVBO.bind()

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateVertexColorVBO(self):
        """Update the buffers on the graphics card.
        Direct mode with vertices and colour.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.updateVertexColorVBO')

        if self._vertexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.updateVertexColorVBO: OpenGL Error - {self}')
            return

        self._defineVertexColorVBO()

    def drawVertexColorVBO(self):
        """Draw the vertex buffers in direct array mode. Arrays are drawn from buffers already bound to graphics card memory.
        Only vertices and colour required.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawVertexColorVBO')

        if self._vertexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.drawVertexColorVBO: OpenGL Error - {self}')
            return

        if self.blendMode:
            GL.glEnable(GL.GL_BLEND)
        if self.fillMode is not None:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self.fillMode)

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)

        self._vertexVBO.bind()
        GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, self._vertexVBO)
        self._colorVBO.bind()
        GL.glColorPointer(4, GL.GL_FLOAT, 0, self._colorVBO)
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
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawVertexNoColor')

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
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawTextArray')

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
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, self.attribs)
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
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.defineTextArrayVBO')

        # create the VBOs if they don't exist - reusing will just rewrite the buffers
        if self._vertexVBO is None:
            _float = np.array([], dtype=np.float32)
            _int = np.array([], dtype=np.uint32)
            self._vertexVBO = VBO(_float, usage=_USAGE)
            self._colorVBO = VBO(_float, usage=_USAGE)
            self._attribVBO = VBO(_float, usage=_USAGE)
            self._textureVBO = VBO(_float, usage=_USAGE)
            self._indexVBO = VBO(_int, usage=_USAGE, target=GL.GL_ELEMENT_ARRAY_BUFFER)
        self._defineTextArrayVBO()

    def _defineTextArrayVBO(self):
        """Push vertices/colours/texture co-ordinates/attribs/indices to graphics card
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}._defineTextArrayVBO')

        self._vertexVBO.set_array(self.vertices)
        self._vertexVBO.bind()
        self._colorVBO.set_array(self.colors)
        self._colorVBO.bind()
        self._textureVBO.set_array(self.texcoords)
        self._textureVBO.bind()
        self._attribVBO.set_array(self.attribs)
        self._attribVBO.bind()
        self._indexVBO.set_array(self.indices)
        self._indexVBO.bind()

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateTextArrayVBO(self):
        """Update the buffers on the graphics card.
        Indexed mode with vertices, colour, texture and attributes.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.updateTextArrayVBO')

        if self._vertexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.updateTextArrayVBO: OpenGL Error - {self}')
            return

        self._defineTextArrayVBO()

    def updateTextArrayVBOAttribs(self):
        """Update the buffers on the graphics card.
        Only update the attributes used for moving text.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.pushTextArrayVBOAttribs')

        if self._attribVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.pushTextArrayVBOAttribs: OpenGL Error - {self}')
            return

        self._attribVBO.set_array(self.attribs)
        self._attribVBO.bind()

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateTextArrayVBOColour(self):
        """Update the buffers on the graphics card.
        Only update the colour, used for highlighting text.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.updateTextArrayVBOColour')

        if self._colorVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.updateTextArrayVBOColour: OpenGL Error - {self}')
            return

        self._colorVBO.set_array(self.colors)
        self._colorVBO.bind()

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    # def enableTextClientState(self):
    #     _attribArrayIndex = 1
    #     GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    #     GL.glEnableClientState(GL.GL_COLOR_ARRAY)
    #     GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
    #     GL.glEnableVertexAttribArray(_attribArrayIndex)
    #
    # def disableTextClientState(self):
    #     _attribArrayIndex = 1
    #     GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
    #     GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    #     GL.glDisableClientState(GL.GL_COLOR_ARRAY)
    #     GL.glDisableVertexAttribArray(_attribArrayIndex)

    def drawTextArrayVBO(self, enableClientState=False, disableClientState=False):
        """Draw the texture buffers in indexed array mode. Arrays are drawn from buffers already bound to graphics card memory.
        Indexed mode with vertices, colour, texture and attributes.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawTextArrayVBO')

        if self._vertexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.drawTextArrayVBO: OpenGL Error - {self}')
            return

        if self.blendMode:
            GL.glEnable(GL.GL_BLEND)

        _attribArrayIndex = 1
        if enableClientState:
            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glEnableClientState(GL.GL_COLOR_ARRAY)
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
            GL.glEnableVertexAttribArray(_attribArrayIndex)

        self._vertexVBO.bind()
        GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, self._vertexVBO)
        self._colorVBO.bind()
        GL.glColorPointer(4, GL.GL_FLOAT, 0, self._colorVBO)
        self._textureVBO.bind()
        GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, self._textureVBO)
        self._attribVBO.bind()
        GL.glVertexAttribPointer(_attribArrayIndex, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, self._attribVBO)
        self._indexVBO.bind()
        GL.glDrawElements(self.drawMode, len(self.indices), GL.GL_UNSIGNED_INT, self._indexVBO)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

        if disableClientState:
            GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDisableClientState(GL.GL_COLOR_ARRAY)
            GL.glDisableVertexAttribArray(_attribArrayIndex)

        if self.blendMode:
            GL.glDisable(GL.GL_BLEND)


#=========================================================================================
# _GLVertexArray
#=========================================================================================

class _GLVertexArray:
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

        self._vertexVBO = None
        self._colorVBO = None
        self._attribVBO = None
        self._textureVBO = None
        self._indexVBO = None

    def __del__(self):
        """Delete vertex buffer objects on deletion
        """
        for vbo in (self._vertexVBO,
                    self._colorVBO,
                    self._attribVBO,
                    self._textureVBO,
                    self._indexVBO,):
            with contextlib.suppress(Exception):
                GL.glDeleteBuffers(1, vbo)

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

    def _delete(self):
        """Clean up everything for deletion
        """
        del self.indices
        del self.vertices
        del self.colors
        del self.texcoords
        del self.attribs
        del self.offsets
        del self.pids
        self._GLContext = None

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # indexed VBOs (vertex buffer objects)
    # Index array - Indices/Vertices/Colour
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def drawIndexArray(self):
        """Draw the vertex buffers in indexed array mode. Arrays are copied from main memory each time.
        Indexed with vertices and colour.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawIndexArray')

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
            _
            attribs:        array of float for defining aliasPosition
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.defineIndexVBO')

        # create the VBOs if they don't exist - reusing will just rewrite the buffers
        if self._vertexVBO is None:
            self._vertexVBO = GL.glGenBuffers(1)
            self._colorVBO = GL.glGenBuffers(1)
            self._indexVBO = GL.glGenBuffers(1)
        self._defineIndexVBO()

    def _defineIndexVBO(self):
        """Push Indices/Colours/Vertices to graphics card
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}._defineIndexVBO')

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vertexVBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, _USAGE)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._colorVBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.colors.nbytes, self.colors, _USAGE)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self._indexVBO)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, _USAGE)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateIndexVBO(self):
        """Update the buffers on the graphics card.
        Indexed mode with vertices and colour.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.updateIndexVBO')

        if self._vertexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.updateIndexVBO: OpenGL Error - {self}')
            return

        self._defineIndexVBO()

    def updateIndexVBOIndices(self):
        """Update the buffers on the graphics card.
        Only the index array.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.updateIndexVBOIndices')

        if self._indexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.updateIndexVBOIndices: OpenGL Error - {self}')
            return

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self._indexVBO)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, _USAGE)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)

    def drawIndexVBO(self):
        """Draw the vertex buffers in indexed array mode. Arrays are drawn from buffers already bound to graphics card memory.
        Indexed mode with vertices and colour.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawIndexVBO')

        if not self.indices.size:
            return
        if self._indexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.drawIndexVBO: OpenGL Error - {self}')
            return

        if self.blendMode:
            GL.glEnable(GL.GL_BLEND)
        if self.fillMode is not None:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self.fillMode)

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vertexVBO)
        GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, None)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._colorVBO)
        GL.glColorPointer(4, GL.GL_FLOAT, 0, None)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self._indexVBO)
        GL.glDrawElements(self.drawMode, self.indices.size, GL.GL_UNSIGNED_INT, None)

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
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawIndexArrayNoColor')

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
    # indexed VBOs (vertex buffer objects)
    # Index array - Indices/Vertices/Colour/Attribs
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def defineAliasedIndexVBO(self):
        """Define the buffers on the graphics card.
        Indexed mode with vertices and colour.
        If undefined, create new VBOs otherwise overwrite existing.

        Includes:
            vertices:       (x, y) * vertices
            colors:         (R, G, B, a) * vertices
            indices:        array of indexes into vertex list
            _
            attribs:        array of float for defining aliasPosition
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.defineAliasedIndexVBO')

        # create the VBOs if they don't exist - reusing will just rewrite the buffers
        if self._vertexVBO is None:
            self._vertexVBO = GL.glGenBuffers(1)
            self._colorVBO = GL.glGenBuffers(1)
            self._attribVBO = GL.glGenBuffers(1)
            self._indexVBO = GL.glGenBuffers(1)
        self._defineAliasedIndexVBO()

    def _defineAliasedIndexVBO(self):
        """Push Indices/Colours/Vertices/attribs to graphics card
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}._defineAliasedIndexVBO')

        if self._vertexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}._defineAliasedIndexVBO: OpenGL Error - {self}')
            return

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vertexVBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, _USAGE)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._colorVBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.colors.nbytes, self.colors, _USAGE)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._attribVBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.attribs.nbytes, self.attribs, _USAGE)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self._indexVBO)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, _USAGE)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateAliasedIndexVBO(self):
        """Update the buffers on the graphics card.
        Indexed mode with vertices and colour.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.updateAliasedIndexVBO')

        if self._vertexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.updateAliasedIndexVBO: OpenGL Error - {self}')
            return

        self._defineAliasedIndexVBO()

    def updateAliasedIndexVBOIndices(self):
        """Update the buffers on the graphics card.
        Only the index array.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.updateAliasedIndexVBOIndices')

        if self._indexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.updateAliasedIndexVBOIndices: OpenGL Error - {self}')
            return

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self._indexVBO)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, _USAGE)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)

    def drawAliasedIndexVBO(self):
        """Draw the vertex buffers in indexed array mode. Arrays are drawn from buffers already bound to graphics card memory.
        Indexed mode with vertices and colour.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawAliasedIndexVBO')

        if not self.indices.size:
            return
        if self._indexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.drawAliasedIndexVBO: OpenGL Error - {self}')
            return

        if self.blendMode:
            GL.glEnable(GL.GL_BLEND)
        if self.fillMode is not None:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self.fillMode)

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)
        GL.glEnableVertexAttribArray(1)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vertexVBO)
        GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, None)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._colorVBO)
        GL.glColorPointer(4, GL.GL_FLOAT, 0, None)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._attribVBO)
        GL.glVertexAttribPointer(1, 1, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self._indexVBO)
        GL.glDrawElements(self.drawMode, self.indices.size, GL.GL_UNSIGNED_INT, None)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_COLOR_ARRAY)
        GL.glDisableVertexAttribArray(1)

        if self.blendMode:
            GL.glDisable(GL.GL_BLEND)

    def drawAliasedIndexArrayNoColor(self):
        """Draw the vertex buffers in indexed array mode. Arrays are copied from main memory each time.
        Indexed mode using only vertices, no colour.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawAliasedIndexArrayNoColor')

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
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawVertexColor')

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
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.defineVertexColorVBO')

        # create the VBOs if they don't exist - reusing will just rewrite the buffers
        if self._vertexVBO is None:
            self._vertexVBO = GL.glGenBuffers(1)
            self._colorVBO = GL.glGenBuffers(1)
        self._defineVertexColorVBO()

    def _defineVertexColorVBO(self):
        """Push Colours/Vertices to graphics card
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}._defineVertexColorVBO')

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vertexVBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, _USAGE)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._colorVBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.colors.nbytes, self.colors, _USAGE)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateVertexColorVBO(self):
        """Update the buffers on the graphics card.
        Direct mode with vertices and colour.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.updateVertexColorVBO')

        if self._vertexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.updateVertexColorVBO: OpenGL Error - {self}')
            return

        self._defineVertexColorVBO()

    def drawVertexColorVBO(self):
        """Draw the vertex buffers in direct array mode. Arrays are drawn from buffers already bound to graphics card memory.
        Only vertices and colour required.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawVertexColorVBO')

        if self._vertexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.drawVertexColorVBO: OpenGL Error - {self}')
            return

        if self.blendMode:
            GL.glEnable(GL.GL_BLEND)
        if self.fillMode is not None:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self.fillMode)

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vertexVBO)
        GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, None)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._colorVBO)
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
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawVertexNoColor')

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
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawTextArray')

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
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, self.attribs)
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
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.defineTextArrayVBO')

        # create the VBOs if they don't exist - reusing will just rewrite the buffers
        if self._vertexVBO is None:
            self._vertexVBO = GL.glGenBuffers(1)
            self._colorVBO = GL.glGenBuffers(1)
            self._attribVBO = GL.glGenBuffers(1)
            self._textureVBO = GL.glGenBuffers(1)
            self._indexVBO = GL.glGenBuffers(1)
        self._defineTextArrayVBO()

    def _defineTextArrayVBO(self):
        """Push vertices/colours/texture co-ordinates/attribs/indices to graphics card
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}._defineTextArrayVBO')

        # bind to the buffers
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vertexVBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, _USAGE)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._colorVBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.colors.nbytes, self.colors, _USAGE)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._textureVBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.texcoords.nbytes, self.texcoords, _USAGE)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._attribVBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.attribs.nbytes, self.attribs, _USAGE)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self._indexVBO)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, _USAGE)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateTextArrayVBO(self):
        """Update the buffers on the graphics card.
        Indexed mode with vertices, colour, texture and attributes.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.updateTextArrayVBO')

        if self._vertexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.updateTextArrayVBO: OpenGL Error - {self}')
            return

        self._defineTextArrayVBO()

    def updateTextArrayVBOAttribs(self):
        """Update the buffers on the graphics card.
        Only update the attributes used for moving text.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.pushTextArrayVBOAttribs')

        if self._attribVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.pushTextArrayVBOAttribs: OpenGL Error - {self}')
            return

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._attribVBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.attribs.nbytes, self.attribs, _USAGE)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    def updateTextArrayVBOColour(self):
        """Update the buffers on the graphics card.
        Only update the colour, used for highlighting text.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.updateTextArrayVBOColour')

        if self._colorVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.updateTextArrayVBOColour: OpenGL Error - {self}')
            return

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._colorVBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.colors.nbytes, self.colors, _USAGE)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    # def enableTextClientState(self):
    #     _attribArrayIndex = 1
    #     GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    #     GL.glEnableClientState(GL.GL_COLOR_ARRAY)
    #     GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
    #     GL.glEnableVertexAttribArray(_attribArrayIndex)
    #
    # def disableTextClientState(self):
    #     _attribArrayIndex = 1
    #     GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
    #     GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    #     GL.glDisableClientState(GL.GL_COLOR_ARRAY)
    #     GL.glDisableVertexAttribArray(_attribArrayIndex)

    def drawTextArrayVBO(self, enableClientState=False, disableClientState=False):
        """Draw the texture buffers in indexed array mode. Arrays are drawn from buffers already bound to graphics card memory.
        Indexed mode with vertices, colour, texture and attributes.
        """
        if _DEBUG:
            getLogger().debug(f'-->  {self.__class__.__name__}.drawTextArrayVBO')

        if self._vertexVBO is None:
            getLogger().debug(f'{self.__class__.__name__}.drawTextArrayVBO: OpenGL Error - {self}')
            return

        if self.blendMode:
            GL.glEnable(GL.GL_BLEND)

        _attribArrayIndex = 1
        if enableClientState:
            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glEnableClientState(GL.GL_COLOR_ARRAY)
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
            GL.glEnableVertexAttribArray(_attribArrayIndex)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vertexVBO)
        GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, None)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._colorVBO)
        GL.glColorPointer(4, GL.GL_FLOAT, 0, None)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._textureVBO)
        GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, None)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._attribVBO)
        GL.glVertexAttribPointer(_attribArrayIndex, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self._indexVBO)
        GL.glDrawElements(self.drawMode, self.indices.size, GL.GL_UNSIGNED_INT, None)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

        if disableClientState:
            GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDisableClientState(GL.GL_COLOR_ARRAY)
            GL.glDisableVertexAttribArray(_attribArrayIndex)

        if self.blendMode:
            GL.glDisable(GL.GL_BLEND)


#=========================================================================================
# Windows again - doesn't appear to correctly accelerate all GL objects
#=========================================================================================

if isWindowsOS():
    GLVertexArray = _GLVertexArray
else:
    GLVertexArray = _VBOGLVertexArray


#=========================================================================================
# GLSymbolArray
#=========================================================================================

class GLSymbolArray(GLVertexArray):
    """
    Array class to handle symbols.
    """

    def __init__(self, GLContext=None, spectrumView=None, objListView=None):
        super().__init__(renderMode=GLRENDERMODE_REBUILD,
                         blendMode=False, drawMode=GL.GL_LINES,
                         dimension=2, GLContext=GLContext)
        self.spectrumView = spectrumView
        self.objListView = objListView


#=========================================================================================
# GLLabelArray
#=========================================================================================

class GLLabelArray(GLVertexArray):
    """
    Array class to handle labels.
    """

    def __init__(self, GLContext=None, spectrumView=None, objListView=None):
        super().__init__(renderMode=GLRENDERMODE_REBUILD,
                         blendMode=False, drawMode=GL.GL_LINES,
                         dimension=2, GLContext=GLContext)
        self.spectrumView = spectrumView
        self.objListView = objListView
        self.stringList = []
