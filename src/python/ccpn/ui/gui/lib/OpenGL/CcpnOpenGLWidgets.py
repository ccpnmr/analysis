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

import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from ccpn.util.Logging import getLogger
import numpy as np
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLRENDERMODE_RESCALE, GLRENDERMODE_REBUILD, \
                                                    GLRENDERMODE_DRAW
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLVertexArray
from ccpn.core.Integral import Integral

try:
  from OpenGL import GL, GLU, GLUT
except ImportError:
  app = QtWidgets.QApplication(sys.argv)
  QtWidgets.QMessageBox.critical(None, "OpenGL hellogl",
          "PyOpenGL must be installed to run this example.")
  sys.exit(1)

from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_REGIONSHADE, CCPNGLWIDGET_INTEGRALSHADE

REGION_COLOURS = {
  'green': (0, 1.0, 0.1, CCPNGLWIDGET_REGIONSHADE),
  'yellow': (0.9, 1.0, 0.05, CCPNGLWIDGET_REGIONSHADE),
  'blue': (0.2, 0.1, 1.0, CCPNGLWIDGET_REGIONSHADE),
  'transparent': (1.0, 1.0, 1.0, 0.01),
  'grey': (1.0, 1.0, 1.0, CCPNGLWIDGET_REGIONSHADE),
  'red': (1.0, 0.1, 0.2, CCPNGLWIDGET_REGIONSHADE),
  'purple': (0.7, 0.4, 1.0, CCPNGLWIDGET_REGIONSHADE),
  None: (0.2, 0.1, 1.0, CCPNGLWIDGET_REGIONSHADE),
  'highlight': (0.5, 0.5, 0.5, CCPNGLWIDGET_REGIONSHADE)
}


class GLRegion(QtWidgets.QWidget):

  valuesChanged = pyqtSignal(list)

  def __init__(self, parent, glList, values=(0,0), axisCode=None, orientation='h',
               brush=None, colour='blue',
               movable=True, visible=True, bounds=None,
               obj=None, objectView=None, lineStyle='dashed'):

    super(GLRegion, self).__init__(parent)

    self.parent = parent
    self._glList = glList
    self._values = values
    self._axisCode = axisCode
    self._orientation = orientation
    self._brush = brush
    self._colour = colour
    self.movable = movable
    self._visible = visible
    self._bounds = bounds
    self._object = obj
    self._objectView = objectView
    self.lineStyle = lineStyle
    self.pid = obj.pid if hasattr(obj, 'pid') else None

  def _mouseDrag(self, values):
    self.valuesChanged.emit(list(values))

  @property
  def values(self):
    return list(self._values)

  @values.setter
  def values(self, values):
    self._values = tuple(values)
    try:
      self._glList.renderMode = GLRENDERMODE_RESCALE
    except Exception as es:
      pass

    self.parent.update()
    self.valuesChanged.emit(list(values))

    # TODO:ED change the integral object - should spawn change event
    if self._object and not self._object.isDeleted:
      self._object.limits = [(min(values), max(values))]

  def setValue(self, val):
    # use the region to simulate an infinite line - calls setter above
    self.values = (val, val)
    # self.parent.update()

  @property
  def axisCode(self):
    return self._axisCode

  @axisCode.setter
  def axisCode(self, axisCode):
    self._axisCode = axisCode
    self._glList.renderMode = GLRENDERMODE_REBUILD
    self.parent.update()

  @property
  def orientation(self):
    return self._orientation

  @orientation.setter
  def orientation(self, orientation):
    self._orientation = orientation

    if orientation == 'h':
      self._axisCode = self.parent.axisCodes[1]
    elif orientation == 'v':
      self._axisCode = self.parent.axisCodes[0]
    else:
      if not self._axisCode:
        axisIndex = None
        for ps, psCode in enumerate(self.parent.axisCodes[0:2]):
          if self.parent._preferences.matchAxisCode == 0:  # default - match atom type

            if self._axisCode[0] == psCode[0]:
              axisIndex = ps
          elif self.parent._preferences.matchAxisCode == 1:  # match full code
            if self._axisCode == psCode:
              axisIndex = ps

        if not axisIndex:
          getLogger().warning('Axis code %s not found in current strip' % self._axisCode)

    if self._glList:
      self._glList.renderMode = GLRENDERMODE_REBUILD
    self.parent.update()

  @property
  def brush(self):
    return self._brush

  @brush.setter
  def brush(self, brush):
    self._brush = brush
    self._glList.renderMode = GLRENDERMODE_REBUILD
    self.parent.update()

  @property
  def colour(self):
    return self._colour

  @colour.setter
  def colour(self, colour):
    self._colour = colour
    if colour in REGION_COLOURS.keys():
      self._brush = REGION_COLOURS[colour]

    self._glList.renderMode = GLRENDERMODE_REBUILD
    self.parent.update()

  @property
  def visible(self):
    return self._visible

  @visible.setter
  def visible(self, visible):
    self._visible = visible
    self._glList.renderMode = GLRENDERMODE_REBUILD
    self.parent.update()

  @property
  def bounds(self):
    return self._bounds

  @bounds.setter
  def bounds(self, bounds):
    self._bounds = bounds
    self._glList.renderMode = GLRENDERMODE_REBUILD
    self.parent.update()

  def _rebuildIntegral(self):
    if isinstance(self._object, Integral) and hasattr(self._object, '_1Dregions'):
      intArea = self._integralArea = GLVertexArray(numLists=1,
                                                  renderMode=GLRENDERMODE_DRAW, blendMode=False,
                                                  drawMode=GL.GL_QUAD_STRIP, fillMode=GL.GL_FILL,
                                                  dimension=2, GLContext=self.parent)

      intArea.numVertices = len(self._object._1Dregions[1]) * 2
      intArea.vertices = np.empty(intArea.numVertices * 2)
      intArea.vertices[::4] = self._object._1Dregions[1]
      intArea.vertices[2::4] = self._object._1Dregions[1]
      intArea.vertices[1::4] = self._object._1Dregions[0]
      intArea.vertices[3::4] = self._object._1Dregions[2]

      if self._object and self._object in self._glList.parent.current.integrals:
        solidColour = list(self._glList.parent.highlightColour)
      else:
        solidColour = list(self._brush)
      solidColour[3] = 1.0

      intArea.colors = np.array(solidColour * intArea.numVertices)


class GLIntegralArray(GLVertexArray):
  def __init__(self, project=None, GLContext=None, spectrumView=None, integralListView=None):
    super(GLIntegralArray, self).__init__(renderMode=GLRENDERMODE_REBUILD, blendMode=True,
                                          GLContext=GLContext, drawMode=GL.GL_QUADS,
                                          dimension=2)
    self.project = project
    self._regions = []
    self.spectrumView = spectrumView
    self.integralListView = integralListView
    self.GLContext=GLContext

  def drawIndexArray(self):
    # draw twice top cover the outline
    self.fillMode = GL.GL_LINE
    super(GLIntegralArray, self).drawIndexArray()
    self.fillMode = GL.GL_FILL
    super(GLIntegralArray, self).drawIndexArray()

  def _clearRegions(self):
    self._regions = []

  def addIntegral(self, integral, integralListView, colour='blue', brush=None):
    return self._addRegion(values=integral.limits[0], orientation='v', movable=True,
                           obj=integral, objectView=integralListView, colour=colour, brush=brush)

  def _removeRegion(self, region):
    if region in self._regions:
      self._regions.remove(region)

  def _addRegion(self, values=None, axisCode=None, orientation=None,
                brush=None, colour='blue',
                movable=True, visible=True, bounds=None,
                obj=None, objectView=None,
                **kw):

    if colour in REGION_COLOURS.keys() and not brush:
      brush = REGION_COLOURS[colour]

    if orientation == 'h':
      axisCode = self.parent._axisCodes[1]
    elif orientation == 'v':
      axisCode = self.parent._axisCodes[0]
    else:
      if axisCode:
        axisIndex = None
        for ps, psCode in enumerate(self.parent._axisCodes[0:2]):
          if self.parent._preferences.matchAxisCode == 0:  # default - match atom type

            if axisCode[0] == psCode[0]:
              axisIndex = ps
          elif self.parent._preferences.matchAxisCode == 1:  # match full code
            if axisCode == psCode:
              axisIndex = ps

          if axisIndex == 0:
            orientation = 'v'
          elif axisIndex == 1:
            orientation = 'h'

        if not axisIndex:
          getLogger().warning('Axis code %s not found in current strip' % axisCode)
          return None
      else:
        axisCode = self.parent._axisCodes[0]
        orientation = 'v'

    self._regions.append(GLRegion(self.parent, self,
                                  values=values,
                                  axisCode=axisCode,
                                  orientation=orientation,
                                  brush=brush,
                                  colour=colour,
                                  movable=movable,
                                  visible=visible,
                                  bounds=bounds,
                                  obj=obj,
                                  objectView=objectView))

    axisIndex = 0
    for ps, psCode in enumerate(self.parent.axisOrder[0:2]):
      if self.parent._preferences.matchAxisCode == 0:  # default - match atom type

        if axisCode[0] == psCode[0]:
          axisIndex = ps
      elif self.parent._preferences.matchAxisCode == 1:  # match full code
        if axisCode == psCode:
          axisIndex = ps

    # TODO:ED check axis units - assume 'ppm' for the minute

    if axisIndex == 0:
      # vertical ruler
      pos0 = x0 = values[0]
      pos1 = x1 = values[1]
      y0 = self.parent.axisT+self.parent.pixelY
      y1 = self.parent.axisB-self.parent.pixelY
    else:
      # horizontal ruler
      pos0 = y0 = values[0]
      pos1 = y1 = values[1]
      x0 = self.parent.axisL-self.parent.pixelX
      x1 = self.parent.axisR+self.parent.pixelX

    newRegion = self._regions[-1]

    if obj and obj in self.parent.current.integrals:

      # draw integral bars of in the current list
      colour = list(self.parent.highlightColour)
      colour[3] = CCPNGLWIDGET_INTEGRALSHADE
    # else:
    #   colour = (brush)

      index = self.numVertices
      self.indices = np.append(self.indices, [index, index + 1, index + 2, index + 3,
                                                      index, index + 1, index, index + 1,
                                                      index + 1, index + 2, index + 1, index + 2,
                                                      index + 2, index + 3, index + 2, index + 3,
                                                      index, index + 3, index, index + 3])
      self.vertices = np.append(self.vertices, [x0, y0, x0, y1, x1, y1, x1, y0])
      self.colors = np.append(self.colors, colour * 4)
      self.attribs = np.append(self.attribs, [axisIndex, pos0, axisIndex, pos1, axisIndex, pos0, axisIndex, pos1])

      index += 4
      self.numVertices += 4

      newRegion.setVisible(True)
    else:
      # colour = (brush)
      newRegion.setVisible(False)

    # newRegion = self._regions[-1]

    # add the quads to the region
    if obj and hasattr(obj, '_1Dregions'):
      intArea = newRegion._integralArea = GLVertexArray(numLists=1,
                                              renderMode=GLRENDERMODE_REBUILD, blendMode=True,
                                              drawMode=GL.GL_QUAD_STRIP, fillMode=GL.GL_FILL,
                                              dimension=2, GLContext=self.GLContext)

      intArea.numVertices = len(obj._1Dregions[1]) * 2
      intArea.vertices = np.empty(intArea.numVertices * 2)
      intArea.vertices[::4] = obj._1Dregions[1]
      intArea.vertices[2::4] = obj._1Dregions[1]
      intArea.vertices[1::4] = obj._1Dregions[0]
      intArea.vertices[3::4] = obj._1Dregions[2]

      if obj in self.parent.current.integrals:
        solidColour = list(self.parent.highlightColour)
      else:
        solidColour = list(brush)
      solidColour[3] = 1.0

      # solidColour = list(colour)
      # solidColour[3] = 1.0
      intArea.colors = np.array(solidColour * intArea.numVertices)

    return newRegion

  # def _rebuildIntegral(self, reg):
  #   intArea = reg._integralArea = GLVertexArray(numLists=1,
  #                                               renderMode=GLRENDERMODE_DRAW, blendMode=False,
  #                                               drawMode=GL.GL_QUAD_STRIP, fillMode=GL.GL_FILL,
  #                                               dimension=2, GLContext=self.GLContext)
  #
  #   intArea.numVertices = len(reg._object._1Dregions[1]) * 2
  #   intArea.vertices = np.empty(intArea.numVertices * 2)
  #   intArea.vertices[::4] = reg._object._1Dregions[1]
  #   intArea.vertices[2::4] = reg._object._1Dregions[1]
  #   intArea.vertices[1::4] = reg._object._1Dregions[0]
  #   intArea.vertices[3::4] = reg._object._1Dregions[2]
  #   solidColour = list(reg._brush)
  #   solidColour[3] = 1.0
  #   intArea.colors = np.array(solidColour * intArea.numVertices)

  def _rebuildIntegralAreas(self):
    for reg in self._regions:
      if reg._integralArea.renderMode == GLRENDERMODE_REBUILD:
        reg._integralArea.renderMode = GLRENDERMODE_DRAW
        reg._rebuildIntegral()

  def _rescale(self):
    vertices = self.numVertices
    axisT = self.parent.axisT
    axisB = self.parent.axisB
    axisL = self.parent.axisL
    axisR = self.parent.axisR
    pixelX = self.parent.pixelX
    pixelY = self.parent.pixelY

    if vertices:
      for pp in range(0, 2*vertices, 8):
        axisIndex = int(self.attribs[pp])
        axis0 = self.attribs[pp+1]
        axis1 = self.attribs[pp+3]

        # [x0, y0, x0, y1, x1, y1, x1, y0])

        if axisIndex == 0:
          offsets = [axis0, axisT+pixelY, axis0, axisB-pixelY,
                     axis1, axisB-pixelY, axis1, axisT+pixelY]
        else:
          offsets = [axisL-pixelX, axis0, axisL-pixelX, axis1,
                     axisR+pixelX, axis1, axisR+pixelX, axis0]

        self.vertices[pp:pp+8] = offsets

  def _resize(self):
    axisT = self.parent.axisT
    axisB = self.parent.axisB
    axisL = self.parent.axisL
    axisR = self.parent.axisR
    pixelX = self.parent.pixelX
    pixelY = self.parent.pixelY

    pp = 0
    for reg in self._regions:
      if pp >= len(self.vertices):
        break

      if not reg.isVisible:
        continue

      try:
        axisIndex = int(self.attribs[pp])
      except Exception as es:
        axisIndex = 0

      try:
        values = reg._object.limits[0]
      except Exception as es:
        values = reg.values

      axis0 = values[0]
      axis1 = values[1]
      reg._values = values

      # axis0 = self.attribs[pp + 1]
      # axis1 = self.attribs[pp + 3]

      # [x0, y0, x0, y1, x1, y1, x1, y0])

      if axisIndex == 0:
        offsets = [axis0, axisT + pixelY, axis0, axisB - pixelY,
                   axis1, axisB - pixelY, axis1, axisT + pixelY]
      else:
        offsets = [axisL - pixelX, axis0, axisL - pixelX, axis1,
                   axisR + pixelX, axis1, axisR + pixelX, axis0]

      self.vertices[pp:pp + 8] = offsets
      self.attribs[pp + 1] = axis0
      self.attribs[pp + 3] = axis1
      self.attribs[pp + 5] = axis0
      self.attribs[pp + 7] = axis1
      pp += 8

  def _rebuild(self):
    axisT = self.parent.axisT
    axisB = self.parent.axisB
    axisL = self.parent.axisL
    axisR = self.parent.axisR
    pixelX = self.parent.pixelX
    pixelY = self.parent.pixelY

    self.clearArrays()
    for reg in self._regions:

      axisIndex = 0
      for ps, psCode in enumerate(self.parent.axisOrder[0:2]):
        if self.parent._preferences.matchAxisCode == 0:  # default - match atom type

          if reg.axisCode[0] == psCode[0]:
            axisIndex = ps
        elif self.parent._preferences.matchAxisCode == 1:  # match full code
          if reg.axisCode == psCode:
            axisIndex = ps

      # TODO:ED check axis units - assume 'ppm' for the minute

      if axisIndex == 0:
        # vertical ruler
        pos0 = x0 = reg.values[0]
        pos1 = x1 = reg.values[1]
        y0 = axisT+pixelY
        y1 = axisB-pixelY
      else:
        # horizontal ruler
        pos0 = y0 = reg.values[0]
        pos1 = y1 = reg.values[1]
        x0 = axisL-pixelX
        x1 = axisR+pixelX

      # if self._object in self.current.integrals:
      #   colour = (*self.parent.highlightColour[:3], CCPNGLWIDGET_INTEGRALSHADE)
      # else:
      if reg._object in self.parent.current.integrals:
        solidColour = list(self.parent.highlightColour)
        solidColour[3] = CCPNGLWIDGET_INTEGRALSHADE

      # else:
      #   solidColour = list(reg.brush)

        index = self.numVertices
        self.indices = np.append(self.indices, [index, index + 1, index + 2, index + 3,
                                                        index, index + 1, index, index + 1,
                                                        index + 1, index + 2, index + 1, index + 2,
                                                        index + 2, index + 3, index + 2, index + 3,
                                                        index, index + 3, index, index + 3])
        self.vertices = np.append(self.vertices, [x0, y0, x0, y1, x1, y1, x1, y0])
        self.colors = np.append(self.colors, solidColour * 4)
        self.attribs = np.append(self.attribs, [axisIndex, pos0, axisIndex, pos1, axisIndex, pos0, axisIndex, pos1])

        index += 4
        self.numVertices += 4

        reg.setVisible(True)
      else:
        solidColour = list(reg.brush)
        reg.setVisible(False)

      reg._rebuildIntegral()