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
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLRENDERMODE_RESCALE, GLRENDERMODE_REBUILD
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLVertexArray
try:
  from OpenGL import GL, GLU, GLUT
except ImportError:
  app = QtWidgets.QApplication(sys.argv)
  QtWidgets.QMessageBox.critical(None, "OpenGL hellogl",
          "PyOpenGL must be installed to run this example.")
  sys.exit(1)

REGION_COLOURS = {
  'green': (0, 1.0, 0.1, 0.15),
  'yellow': (0.9, 1.0, 0.05, 0.15),
  'blue': (0.2, 0.1, 1.0, 0.15),
  'transparent': (1.0, 1.0, 1.0, 0.01),
  'grey': (1.0, 1.0, 1.0, 0.15),
  'red': (1.0, 0.1, 0.2, 0.15),
  'purple': (0.7, 0.4, 1.0, 0.15),
  None: (0.2, 0.1, 1.0, 0.15),
  'highlight': (0.5, 0.5, 0.5, 0.15)
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


class GLIntegralArray(GLVertexArray):
  def __init__(self, GLContext=None, spectrumView=None, integralListView=None):
    super(GLIntegralArray, self).__init__(renderMode=GLRENDERMODE_REBUILD, blendMode=True,
                                          GLContext=GLContext, drawMode=GL.GL_QUADS,
                                          dimension=2)
    self._regions = []
    self.spectrumView = spectrumView
    self.integralListView = integralListView

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

    colour = brush
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

    return self._regions[-1]

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

      colour = reg.brush
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
