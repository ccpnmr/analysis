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
__version__ = "$Revision: 3.0.b4 $"
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
from PyQt5.QtCore import pyqtSignal
from ccpn.util.Logging import getLogger
import numpy as np
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLRENDERMODE_RESCALE, GLRENDERMODE_REBUILD, \
    GLRENDERMODE_DRAW
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLVertexArray
from ccpn.core.Integral import Integral
# spawn a redraw of the GL windows
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import GLREGIONTYPE, GLLINETYPE


try:
    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL CCPN",
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

    def __init__(self, parent, glList, values=(0, 0), axisCode=None, orientation='h',
                 brush=None, colour='blue',
                 movable=True, visible=True, bounds=None,
                 obj=None, objectView=None, lineStyle='dashed', lineWidth=1.0,
                 regionType=GLREGIONTYPE):

        super(GLRegion, self).__init__(parent)

        self._parent = parent
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
        self._lineStyle = lineStyle
        self._lineWidth = lineWidth
        self.regionType = regionType
        self.pid = obj.pid if hasattr(obj, 'pid') else None

        # create a notifier for updating
        self.GLSignals = GLNotifier(parent=None)

    # def _mouseDrag(self, values):
    #     self.valuesChanged.emit(list(values))

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

        self.valuesChanged.emit(list(values))

        # change the limits in the integral object
        if self._object and not self._object.isDeleted:
            self._object.limits = [(min(values), max(values))]

        # emit notifiers to repaint the GL windows
        self.GLSignals.emitPaintEvent()

    def setValue(self, val):
        # use the region to simulate an infinite line - calls setter above
        self.values = (val, val)

    @property
    def axisCode(self):
        return self._axisCode

    @axisCode.setter
    def axisCode(self, axisCode):
        self._axisCode = axisCode
        self._glList.renderMode = GLRENDERMODE_REBUILD

        # emit notifiers to repaint the GL windows
        self.GLSignals.emitPaintEvent()

    @property
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, orientation):
        self._orientation = orientation

        if orientation == 'h':
            self._axisCode = self._parent.axisCodes[1]
        elif orientation == 'v':
            self._axisCode = self._parent.axisCodes[0]
        else:
            if not self._axisCode:
                axisIndex = None
                for ps, psCode in enumerate(self._parent.axisCodes[0:2]):
                    if self._parent._preferences.matchAxisCode == 0:  # default - match atom type

                        if self._axisCode[0] == psCode[0]:
                            axisIndex = ps
                    elif self._parent._preferences.matchAxisCode == 1:  # match full code
                        if self._axisCode == psCode:
                            axisIndex = ps

                if not axisIndex:
                    getLogger().warning('Axis code %s not found in current strip' % self._axisCode)

        if self._glList:
            self._glList.renderMode = GLRENDERMODE_REBUILD

        # emit notifiers to repaint the GL windows
        self.GLSignals.emitPaintEvent()

    @property
    def brush(self):
        return self._brush

    @brush.setter
    def brush(self, brush):
        self._brush = brush
        self._glList.renderMode = GLRENDERMODE_REBUILD

        # emit notifiers to repaint the GL windows
        self.GLSignals.emitPaintEvent()

    @property
    def colour(self):
        return self._colour

    @colour.setter
    def colour(self, colour):
        self._colour = colour
        if colour in REGION_COLOURS.keys():
            self._brush = REGION_COLOURS[colour]

        self._glList.renderMode = GLRENDERMODE_REBUILD

        # emit notifiers to repaint the GL windows
        self.GLSignals.emitPaintEvent()

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, visible):
        self._visible = visible
        self._glList.renderMode = GLRENDERMODE_REBUILD

        # emit notifiers to repaint the GL windows
        self.GLSignals.emitPaintEvent()

    @property
    def lineStyle(self):
        return self._lineStyle

    @lineStyle.setter
    def lineStyle(self, style):
        self._lineStyle = style
        self._glList.renderMode = GLRENDERMODE_REBUILD

        # emit notifiers to repaint the GL windows
        self.GLSignals.emitPaintEvent()

    @property
    def lineWidth(self):
        return self._lineWidth

    @lineWidth.setter
    def lineWidth(self, width):
        self._lineWidth = width
        self._glList.renderMode = GLRENDERMODE_REBUILD

        # emit notifiers to repaint the GL windows
        self.GLSignals.emitPaintEvent()

    @property
    def bounds(self):
        return self._bounds

    @bounds.setter
    def bounds(self, bounds):
        self._bounds = bounds
        self._glList.renderMode = GLRENDERMODE_REBUILD

        # emit notifiers to repaint the GL windows
        self.GLSignals.emitPaintEvent()

    def _rebuildIntegral(self):
        if isinstance(self._object, Integral) and hasattr(self._object, '_1Dregions'):
            intArea = self._integralArea = GLVertexArray(numLists=1,
                                                         renderMode=GLRENDERMODE_DRAW, blendMode=False,
                                                         drawMode=GL.GL_QUAD_STRIP, fillMode=GL.GL_FILL,
                                                         dimension=2, GLContext=self._parent)

            intArea.numVertices = len(self._object._1Dregions[1]) * 2
            intArea.vertices = np.empty(intArea.numVertices * 2)
            intArea.vertices[::4] = self._object._1Dregions[1]
            intArea.vertices[2::4] = self._object._1Dregions[1]
            intArea.vertices[1::4] = self._object._1Dregions[0]
            intArea.vertices[3::4] = self._object._1Dregions[2]

            if self._object and self._object in self._glList._parent.current.integrals:
                solidColour = list(self._glList._parent.highlightColour)
            else:
                solidColour = list(self._brush)
            solidColour[3] = 1.0

            intArea.colors = np.array(solidColour * intArea.numVertices)


class GLInfiniteLine(GLRegion):
    valuesChanged = pyqtSignal(float)

    def __init__(self, parent, glList, values=(0, 0), axisCode=None, orientation='h',
                 brush=None, colour='blue',
                 movable=True, visible=True, bounds=None,
                 obj=None, objectView=None, lineStyle='dashed', lineWidth=1.0,
                 regionType=GLLINETYPE):

        super(GLInfiniteLine, self).__init__(parent, glList, values=values, axisCode=axisCode, orientation=orientation,
                                             brush=brush, colour=colour,
                                             movable=movable, visible=visible, bounds=bounds,
                                             obj=obj, objectView=objectView, lineStyle=lineStyle, lineWidth=lineWidth,
                                             regionType=regionType)

    # same as GLRegion, but _values is a singular item
    @property
    def values(self):
        return self._values

    @values.setter
    def values(self, value):
        self._values = value
        try:
            self._glList.renderMode = GLRENDERMODE_RESCALE
        except Exception as es:
            pass

        self.valuesChanged.emit(value)

        # change the limits in the integral object
        if self._object and not self._object.isDeleted:
            self._object.limits = [(value, value)]

        # emit notifiers to repaint the GL windows
        self.GLSignals.emitPaintEvent()

    def setValue(self, val):
        # use the region to simulate an infinite line - calls setter above
        # raise RuntimeError('Deprecated, please us values = <value>')
        self.values = val


class GLExternalRegion(GLVertexArray):
    def __init__(self, project=None, GLContext=None, spectrumView=None, integralListView=None):
        super().__init__(renderMode=GLRENDERMODE_REBUILD, blendMode=True,
                                               GLContext=GLContext, drawMode=GL.GL_QUADS,
                                               dimension=2)
        self.project = project
        self._regions = []
        self.spectrumView = spectrumView
        self.integralListView = integralListView
        self.GLContext = GLContext

    def drawIndexArray(self):
        # draw twice top cover the outline
        self.fillMode = GL.GL_LINE
        super().drawIndexArray()
        self.fillMode = GL.GL_FILL
        super().drawIndexArray()

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
                   obj=None, objectView=None):

        if colour in REGION_COLOURS.keys() and not brush:
            brush = REGION_COLOURS[colour]

        if orientation == 'h':
            axisCode = self._parent._axisCodes[1]
        elif orientation == 'v':
            axisCode = self._parent._axisCodes[0]
        else:
            if axisCode:
                axisIndex = None
                for ps, psCode in enumerate(self._parent._axisCodes[0:2]):
                    if self._parent._preferences.matchAxisCode == 0:  # default - match atom type

                        if axisCode[0] == psCode[0]:
                            axisIndex = ps
                    elif self._parent._preferences.matchAxisCode == 1:  # match full code
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
                axisCode = self._parent._axisCodes[0]
                orientation = 'v'

        self._regions.append(GLRegion(self._parent, self,
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
        for ps, psCode in enumerate(self._parent.axisOrder[0:2]):
            if self._parent._preferences.matchAxisCode == 0:  # default - match atom type

                if axisCode[0] == psCode[0]:
                    axisIndex = ps
            elif self._parent._preferences.matchAxisCode == 1:  # match full code
                if axisCode == psCode:
                    axisIndex = ps

        # TODO:ED check axis units - assume 'ppm' for the minute
        if axisIndex == 0:
            # vertical ruler
            pos0 = x0 = values[0]
            pos1 = x1 = values[1]
            y0 = self._parent.axisT + self._parent.pixelY
            y1 = self._parent.axisB - self._parent.pixelY
        else:
            # horizontal ruler
            pos0 = y0 = values[0]
            pos1 = y1 = values[1]
            x0 = self._parent.axisL - self._parent.pixelX
            x1 = self._parent.axisR + self._parent.pixelX

        colour = brush
        index = self.numVertices
        self.indices = np.append(self.indices, (index, index + 1, index + 2, index + 3,
                                                index, index + 1, index, index + 1,
                                                index + 1, index + 2, index + 1, index + 2,
                                                index + 2, index + 3, index + 2, index + 3,
                                                index, index + 3, index, index + 3))
        self.vertices = np.append(self.vertices, (x0, y0, x0, y1, x1, y1, x1, y0))
        self.colors = np.append(self.colors, colour * 4)
        self.attribs = np.append(self.attribs, (axisIndex, pos0, axisIndex, pos1, axisIndex, pos0, axisIndex, pos1))

        index += 4
        self.numVertices += 4

        return self._regions[-1]

    def _rebuildIntegralAreas(self):
        self._rebuild(checkBuild=True)

        return

        for reg in self._regions:
            if reg._integralArea.renderMode == GLRENDERMODE_REBUILD:
                reg._integralArea.renderMode = GLRENDERMODE_DRAW
                reg._rebuildIntegral()

    def _rescale(self):
        vertices = self.numVertices
        axisT = self._parent.axisT
        axisB = self._parent.axisB
        axisL = self._parent.axisL
        axisR = self._parent.axisR
        pixelX = self._parent.pixelX
        pixelY = self._parent.pixelY

        if vertices:
            for pp in range(0, 2 * vertices, 8):
                axisIndex = int(self.attribs[pp])
                axis0 = self.attribs[pp + 1]
                axis1 = self.attribs[pp + 3]

                if axisIndex == 0:
                    offsets = [axis0, axisT + pixelY, axis0, axisB - pixelY,
                               axis1, axisB - pixelY, axis1, axisT + pixelY]
                else:
                    offsets = [axisL - pixelX, axis0, axisL - pixelX, axis1,
                               axisR + pixelX, axis1, axisR + pixelX, axis0]

                self.vertices[pp:pp + 8] = offsets

    def _resize(self):
        axisT = self._parent.axisT
        axisB = self._parent.axisB
        axisL = self._parent.axisL
        axisR = self._parent.axisR
        pixelX = self._parent.pixelX
        pixelY = self._parent.pixelY

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

    def _rebuild(self, checkBuild=False):
        axisT = self._parent.axisT
        axisB = self._parent.axisB
        axisL = self._parent.axisL
        axisR = self._parent.axisR
        pixelX = self._parent.pixelX
        pixelY = self._parent.pixelY

        self.clearArrays()
        for reg in self._regions:

            axisIndex = 0
            for ps, psCode in enumerate(self._parent.axisOrder[0:2]):
                if self._parent._preferences.matchAxisCode == 0:  # default - match atom type

                    if reg.axisCode[0] == psCode[0]:
                        axisIndex = ps
                elif self._parent._preferences.matchAxisCode == 1:  # match full code
                    if reg.axisCode == psCode:
                        axisIndex = ps

            # TODO:ED check axis units - assume 'ppm' for the minute
            if axisIndex == 0:
                # vertical ruler
                pos0 = x0 = reg.values[0]
                pos1 = x1 = reg.values[1]
                y0 = axisT + pixelY
                y1 = axisB - pixelY
            else:
                # horizontal ruler
                pos0 = y0 = reg.values[0]
                pos1 = y1 = reg.values[1]
                x0 = axisL - pixelX
                x1 = axisR + pixelX

            colour = reg.brush
            index = self.numVertices
            self.indices = np.append(self.indices, (index, index + 1, index + 2, index + 3,
                                                    index, index + 1, index, index + 1,
                                                    index + 1, index + 2, index + 1, index + 2,
                                                    index + 2, index + 3, index + 2, index + 3,
                                                    index, index + 3, index, index + 3))
            self.vertices = np.append(self.vertices, (x0, y0, x0, y1, x1, y1, x1, y0))
            self.colors = np.append(self.colors, colour * 4)
            self.attribs = np.append(self.attribs, (axisIndex, pos0, axisIndex, pos1, axisIndex, pos0, axisIndex, pos1))

            index += 4
            self.numVertices += 4


class GLIntegralRegion(GLExternalRegion):
    def __init__(self, project=None, GLContext=None, spectrumView=None, integralListView=None):
        super().__init__(project=project, GLContext=GLContext,
                                               spectrumView=spectrumView, integralListView=integralListView)

    def _addRegion(self, values=None, axisCode=None, orientation=None,
                   brush=None, colour='blue',
                   movable=True, visible=True, bounds=None,
                   obj=None, objectView=None):

        if colour in REGION_COLOURS.keys() and not brush:
            brush = REGION_COLOURS[colour]

        if orientation == 'h':
            axisCode = self._parent._axisCodes[1]
        elif orientation == 'v':
            axisCode = self._parent._axisCodes[0]
        else:
            if axisCode:
                axisIndex = None
                for ps, psCode in enumerate(self._parent._axisCodes[0:2]):
                    if self._parent._preferences.matchAxisCode == 0:  # default - match atom type

                        if axisCode[0] == psCode[0]:
                            axisIndex = ps
                    elif self._parent._preferences.matchAxisCode == 1:  # match full code
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
                axisCode = self._parent._axisCodes[0]
                orientation = 'v'

        self._regions.append(GLRegion(self._parent, self,
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
        for ps, psCode in enumerate(self._parent.axisOrder[0:2]):
            if self._parent._preferences.matchAxisCode == 0:  # default - match atom type

                if axisCode[0] == psCode[0]:
                    axisIndex = ps
            elif self._parent._preferences.matchAxisCode == 1:  # match full code
                if axisCode == psCode:
                    axisIndex = ps

        # TODO:ED check axis units - assume 'ppm' for the minute
        if axisIndex == 0:
            # vertical ruler
            pos0 = x0 = values[0]
            pos1 = x1 = values[1]
            y0 = self._parent.axisT + self._parent.pixelY
            y1 = self._parent.axisB - self._parent.pixelY
        else:
            # horizontal ruler
            pos0 = y0 = values[0]
            pos1 = y1 = values[1]
            x0 = self._parent.axisL - self._parent.pixelX
            x1 = self._parent.axisR + self._parent.pixelX

        # get the new added region
        newRegion = self._regions[-1]

        if obj and obj in self._parent.current.integrals:

            # draw integral bars if in the current list
            colour = list(self._parent.highlightColour)
            colour[3] = CCPNGLWIDGET_INTEGRALSHADE

            index = self.numVertices
            self.indices = np.append(self.indices, (index, index + 1, index + 2, index + 3,
                                                    index, index + 1, index, index + 1,
                                                    index + 1, index + 2, index + 1, index + 2,
                                                    index + 2, index + 3, index + 2, index + 3,
                                                    index, index + 3, index, index + 3))
            self.vertices = np.append(self.vertices, (x0, y0, x0, y1, x1, y1, x1, y0))
            self.colors = np.append(self.colors, colour * 4)
            self.attribs = np.append(self.attribs, (axisIndex, pos0, axisIndex, pos1, axisIndex, pos0, axisIndex, pos1))

            index += 4
            self.numVertices += 4

            newRegion.visible = True
            newRegion._pp = (self.numVertices - 4) * 2
        else:

            # Need to put the normal regions in here
            newRegion.visible = False
            newRegion._pp = None

        newRegion._rebuildIntegral()

        return newRegion

    def _resize(self):
        axisT = self._parent.axisT
        axisB = self._parent.axisB
        axisL = self._parent.axisL
        axisR = self._parent.axisR
        pixelX = self._parent.pixelX
        pixelY = self._parent.pixelY

        for reg in self._regions:
            pp = reg._pp
            if not pp:
                continue

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

    def _rebuild(self, checkBuild=False):
        axisT = self._parent.axisT
        axisB = self._parent.axisB
        axisL = self._parent.axisL
        axisR = self._parent.axisR
        pixelX = self._parent.pixelX
        pixelY = self._parent.pixelY

        self.clearArrays()
        for reg in self._regions:

            axisIndex = 0
            for ps, psCode in enumerate(self._parent.axisOrder[0:2]):
                if self._parent._preferences.matchAxisCode == 0:  # default - match atom type

                    if reg.axisCode[0] == psCode[0]:
                        axisIndex = ps
                elif self._parent._preferences.matchAxisCode == 1:  # match full code
                    if reg.axisCode == psCode:
                        axisIndex = ps

            # TODO:ED check axis units - assume 'ppm' for the minute
            if axisIndex == 0:
                # vertical ruler
                pos0 = x0 = reg.values[0]
                pos1 = x1 = reg.values[1]
                y0 = axisT + pixelY
                y1 = axisB - pixelY
            else:
                # horizontal ruler
                pos0 = y0 = reg.values[0]
                pos1 = y1 = reg.values[1]
                x0 = axisL - pixelX
                x1 = axisR + pixelX

            if reg._object in self._parent.current.integrals:
                solidColour = list(self._parent.highlightColour)
                solidColour[3] = CCPNGLWIDGET_INTEGRALSHADE

                index = self.numVertices
                self.indices = np.append(self.indices, (index, index + 1, index + 2, index + 3,
                                                        index, index + 1, index, index + 1,
                                                        index + 1, index + 2, index + 1, index + 2,
                                                        index + 2, index + 3, index + 2, index + 3,
                                                        index, index + 3, index, index + 3))
                self.vertices = np.append(self.vertices, (x0, y0, x0, y1, x1, y1, x1, y0))
                self.colors = np.append(self.colors, solidColour * 4)
                self.attribs = np.append(self.attribs, (axisIndex, pos0, axisIndex, pos1, axisIndex, pos0, axisIndex, pos1))

                index += 4
                self.numVertices += 4

                reg.visible = True
                reg._pp = (self.numVertices - 4) * 2
            else:
                reg.visible = False
                reg._pp = None

            if checkBuild == False:
                reg._rebuildIntegral()
            else:
                if hasattr(reg, '_integralArea') and reg._integralArea.renderMode == GLRENDERMODE_REBUILD:
                    reg._integralArea.renderMode = GLRENDERMODE_DRAW
                    reg._rebuildIntegral()
