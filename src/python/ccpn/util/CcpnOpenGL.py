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
import math, random
import ctypes
from imageio import imread

# import the freetype2 library
# import freetype

from PyQt5 import QtCore, QtGui, QtOpenGL, QtWidgets
from PyQt5.QtCore import (QPoint, QPointF, QRect, QRectF, QSize, Qt, QTime,
        QTimer)
from PyQt5.QtGui import (QBrush, QColor, QFontMetrics, QImage, QPainter,
        QRadialGradient, QSurfaceFormat)
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from ccpn.util.Logging import getLogger
import numpy as np
from pyqtgraph import functions as fn
from ccpn.core.PeakList import PeakList
from ccpn.core.Spectrum import Spectrum
from ccpn.ui.gui.modules.GuiPeakListView import _getScreenPeakAnnotation, _getPeakAnnotation    # temp until I rewrite

try:
    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL hellogl",
            "PyOpenGL must be installed to run this example.")
    sys.exit(1)

AXIS_MARGIN = 35
GLRENDERMODE_DRAW = 0
GLRENDERMODE_RESCALE = 1
GLRENDERMODE_REBUILD = 2


# class CcpnOpenGLWidget(QtWidgets.QOpenGLWidget):
#
#     def __init__(self, parent=None):
#       super(QtWidgets.QOpenGLWidget, self).__init__(parent)
#       self.trolltechPurple = QtGui.QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)
#
#     def minimumSizeHint(self):
#       return QtCore.QSize(100, 300)
#
#     def sizeHint(self):
#       return QtCore.QSize(400, 400)
#
#     def initializeGL(self):
#       # self.qglClearColor(self.trolltechPurple.dark())
#       GL.glClearColor(*self.trolltechPurple.getRgb())
#
#     def paintGL(self):
#       GL.glMatrixMode(GL.GL_MODELVIEW)
#       GL.glLoadIdentity()
#       GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
#       GL.glColor3f(1,0,0)
#       GL.glRectf(-1,-1,1,0)
#       GL.glColor3f(0,1,0)
#       GL.glRectf(-1,0,1,1)
#       GL.glBegin(GL.GL_TRIANGLES)
#       GL.glVertex2f(3.0, 3.0)
#       GL.glVertex2f(5.0, 3.0)
#       GL.glVertex2f(5.0, 5.0)
#       GL.glVertex2f(6.0, 4.0)
#       GL.glVertex2f(7.0, 4.0)
#       GL.glVertex2f(7.0, 7.0)
#       GL.glEnd()
#       GL.glFinish()
#
#     def resizeGL(self, w, h):
#       GL.glViewport(0, 0, w, h)


# class Bubble(object):
#   def __init__(self, position, radius, velocity):
#     self.position = position
#     self.vel = velocity
#     self.radius = radius
#
#     self.innerColor = self.randomColor()
#     self.outerColor = self.randomColor()
#     self.updateBrush()
#
#   def updateBrush(self):
#     gradient = QRadialGradient(QPointF(self.radius, self.radius),
#                                self.radius, QPointF(self.radius * 0.5, self.radius * 0.5))
#
#     gradient.setColorAt(0, QColor(255, 255, 255, 255))
#     gradient.setColorAt(0.25, self.innerColor)
#     gradient.setColorAt(1, self.outerColor)
#     self.brush = QBrush(gradient)
#
#   def drawBubble(self, painter):
#     painter.save()
#     painter.translate(self.position.x() - self.radius,
#                       self.position.y() - self.radius)
#     painter.setBrush(self.brush)
#     painter.drawEllipse(0, 0, int(2 * self.radius), int(2 * self.radius))
#     painter.restore()
#
#   def randomColor(self):
#     red = random.randrange(205, 256)
#     green = random.randrange(205, 256)
#     blue = random.randrange(205, 256)
#     alpha = random.randrange(91, 192)
#
#     return QColor(red, green, blue, alpha)
#
#   def move(self, bbox):
#     self.position += self.vel
#     leftOverflow = self.position.x() - self.radius - bbox.left()
#     rightOverflow = self.position.x() + self.radius - bbox.right()
#     topOverflow = self.position.y() - self.radius - bbox.top()
#     bottomOverflow = self.position.y() + self.radius - bbox.bottom()
#
#     if leftOverflow < 0.0:
#       self.position.setX(self.position.x() - 2 * leftOverflow)
#       self.vel.setX(-self.vel.x())
#     elif rightOverflow > 0.0:
#       self.position.setX(self.position.x() - 2 * rightOverflow)
#       self.vel.setX(-self.vel.x())
#
#     if topOverflow < 0.0:
#       self.position.setY(self.position.y() - 2 * topOverflow)
#       self.vel.setY(-self.vel.y())
#     elif bottomOverflow > 0.0:
#       self.position.setY(self.position.y() - 2 * bottomOverflow)
#       self.vel.setY(-self.vel.y())
#
#   def rect(self):
#     return QRectF(self.position.x() - self.radius,
#                   self.position.y() - self.radius, 2 * self.radius,
#                   2 * self.radius)


class CcpnGLWidget(QOpenGLWidget):
  def __init__(self, parent=None, rightMenu=None):
    super(CcpnGLWidget, self).__init__(parent)

    self._rightMenu = rightMenu
    if not parent:        # don't initialise if nothing there
      return

    self.parent = parent

    for spectrumView in self.parent.spectrumViews:
      spectrumView._buildSignal._buildSignal.connect(self.paintGLsignal)

    midnight = QTime(0, 0, 0)
    random.seed(midnight.secsTo(QTime.currentTime()))

    self.object = 0
    self.xRot = 0
    self.yRot = 0
    self.zRot = 0
    self.image = QImage()
    self.bubbles = []
    self.lastPos = QPoint()

    self.trolltechGreen = QColor.fromCmykF(0.40, 0.0, 1.0, 0.0)
    self.trolltechPurple = QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)

    # TODO:ED need to explicitly call self.update() to refresh after an update
    # self.animationTimer = QTimer()
    # self.animationTimer.setSingleShot(False)
    # self.animationTimer.timeout.connect(self.animate)
    # self.animationTimer.start(25)

    self.setAutoFillBackground(False)
    self.setMinimumSize(100, 50)
    self.setWindowTitle("Overpainting a Scene")

    self._mouseX = 0
    self._mouseY = 0

    # self.eventFilter = self._eventFilter
    # self.installEventFilter(self)   # ejb
    self.setMouseTracking(True)                 # generate mouse events when button not pressed

    self.base = None
    self.spectrumValues = []
    self.gridList = []

    self._drawSelectionBox = False
    self._selectionMode = 0
    self._startCoordinate = None
    self._endCoordinate = None
    self._shift = False
    self._command = False
    self._key = ' '
    self._isSHIFT = ' '
    self._isCTRL = ' '

    # self.installEventFilter(self)
    self.setFocusPolicy(Qt.StrongFocus)

    self.axisL = 12
    self.axisR = 4
    self.axisT = 20
    self.axisB = 80

    self._buildPeakList = True

  def resizeGL(self, w, h):
    GL.glViewport(0, 0, w, h)

    # put stuff in here that will change on a resize
    for li in self.gridList:
      li[1] = GLRENDERMODE_REBUILD
    for pp in self._GLPeakLists.values():
      pp[1] = GLRENDERMODE_RESCALE

  def wheelEvent(self, event):
    def between(val, l, r):
      return (l-val)*(r-val) <= 0

    numPixels = event.pixelDelta()
    numDegrees = event.angleDelta() / 8

    h = self.height()
    w = self.width()

    axisLine = 5
    h = self.height()
    w = self.width()

    # find the correct viewport
    mw = [0, 35, w-36, h-1]
    ba = [0, 0, w - 36, 34]
    ra = [w-36, 35, w, h]
    if between(self._mouseX, mw[0], mw[2]) and between(self._mouseY, mw[1], mw[3]):
      mb = (self._mouseX - mw[0]) / (mw[2] - mw[0])
      mbx = self.axisL + mb * (self.axisR - self.axisL)

      if numDegrees.y() < 0:
        self.axisL = mbx + 1.125 * (self.axisL - mbx)
        self.axisR = mbx - 1.125 * (mbx - self.axisR)
      else:
        self.axisL = mbx + 0.9 * (self.axisL - mbx)
        self.axisR = mbx - 0.9 * (mbx - self.axisR)

      mb = (self._mouseY - mw[1]) / (mw[3] - mw[1])
      mby = self.axisB + mb * (self.axisT - self.axisB)

      if numDegrees.y() < 0:
        self.axisB = mby + 1.125 * (self.axisB - mby)
        self.axisT = mby - 1.125 * (mby - self.axisT)
      else:
        self.axisB = mby + 0.9 * (self.axisB - mby)
        self.axisT = mby - 0.9 * (mby - self.axisT)

      # spawn rebuild event for the grid
      for li in self.gridList:
        li[1] = GLRENDERMODE_REBUILD

    elif between(self._mouseX, ba[0], ba[2]) and between(self._mouseY, ba[1], ba[3]):
      mb = (self._mouseX - ba[0]) / (ba[2] - ba[0])
      mbx = self.axisL + mb * (self.axisR - self.axisL)

      if numDegrees.y() < 0:
        self.axisL = mbx + 1.125 * (self.axisL - mbx)
        self.axisR = mbx - 1.125 * (mbx - self.axisR)
      else:
        self.axisL = mbx + 0.9 * (self.axisL - mbx)
        self.axisR = mbx - 0.9 * (mbx - self.axisR)

      # spawn rebuild event for the grid
      self.gridList[0][1] = GLRENDERMODE_REBUILD
      self.gridList[2][1] = GLRENDERMODE_REBUILD

      # ratios have changed so rescale the peaks symbols
      for pp in self._GLPeakLists.values():
        pp[1] = GLRENDERMODE_RESCALE

    elif between(self._mouseX, ra[0], ra[2]) and between(self._mouseY, ra[1], ra[3]):
      mb = (self._mouseY - ra[1]) / (ra[3] - ra[1])
      mby = self.axisB + mb * (self.axisT - self.axisB)

      if numDegrees.y() < 0:
        self.axisB = mby + 1.125 * (self.axisB - mby)
        self.axisT = mby - 1.125 * (mby - self.axisT)
      else:
        self.axisB = mby + 0.9 * (self.axisB - mby)
        self.axisT = mby - 0.9 * (mby - self.axisT)

      # spawn rebuild event for the grid
      self.gridList[0][1] = GLRENDERMODE_REBUILD
      self.gridList[1][1] = GLRENDERMODE_REBUILD

      # ratios have changed so rescale the peaks symbols
      for pp in self._GLPeakLists.values():
        pp[1] = GLRENDERMODE_RESCALE

    event.accept()
    self.update()

  def eventFilter(self, obj, event):
    self._key = '_'
    if type(event) == QtGui.QKeyEvent and event.key() == Qt.Key_A:
      self._key = 'A'
      event.accept()
      return True
    return super(CcpnGLWidget, self).eventFilter(obj, event)

  def _releaseDisplayLists(self, displayList):
    GL.glDeleteLists(displayList, 1)

  def _createDisplayLists(self, numLists, displayList):
    displayList = GL.glGenLists(numLists)

  def _makeGLPeakList(self, spectrum:Spectrum, num:GL.GLint):
    # clear the list and rebuild
    # GL.glDeleteLists(self._GLPeakLists[num], 1)
    # self._GLPeakLists[num] = (GL.glGenLists(1), True)       # list and rebuild flag

    # this is actually quite old-school for openGL but good for test
    GL.glNewList((self._GLPeakLists[num])[0], GL.GL_COMPILE)
    GL.glColor4f(1.0, 1.0, 1.0, 1.0)

    GL.glBegin(GL.GL_LINES)
    GL.glEnd()

    GL.glEndList()

  def _connectSpectra(self):
    for spectrumView in self.parent.spectrumViews:
      spectrumView._buildSignal._buildSignal.connect(self.paintGLsignal)

  def setXRotation(self, angle):
    angle = self.normalizeAngle(angle)
    if angle != self.xRot:
      self.xRot = angle

  def setYRotation(self, angle):
    angle = self.normalizeAngle(angle)
    if angle != self.yRot:
      self.yRot = angle

  def setZRotation(self, angle):
    angle = self.normalizeAngle(angle)
    if angle != self.zRot:
      self.zRot = angle

  def initializeGL(self):
    self._vertexShader1 = """
#version 120

uniform mat4 u_projTrans;

attribute vec4 a_position;
attribute vec2 a_texCoord0;
attribute vec4 a_color;

varying vec4 v_color;
varying vec2 v_texCoord;

void main() {
  gl_Position = u_projTrans * a_position;
  v_texCoord = a_texCoord0;
  v_color = a_color;
}
"""

    self._fragmentShader1 = """
#version 120

#ifdef GL_ES
precision mediump float;
#endif

uniform sampler2D u_texture;

varying vec4 v_color;
varying vec2 v_texCoord;

const float smoothing = 1.0/16.0;

void main() {
  float distance = texture2D(u_texture, v_texCoord).a;
  float alpha = smoothstep(0.5 - smoothing, 0.5 + smoothing, distance);
  gl_FragColor = vec4(v_color.rgb, v_color.a * alpha);
}
"""

    self._vertexShader2 = """
#version 120

varying vec3 P;

void main()
{
  P = gl_Vertex.xyz;

  gl_Position = vec4(P, 1.0);    //ftransform();
}
"""

    self._fragmentShader2 = """
#version 120

uniform float gsize = 100.0;    //size of the grid
uniform float gwidth = 1.0;     //grid lines'width in pixels
varying vec3 P;

void main()
{
  vec3 f  = abs(fract (P * gsize)-0.5);
  vec3 df = fwidth(P * gsize);
  float mi=max(0.0,gwidth-1.0), ma=max(1.0,gwidth);//should be uniforms
  vec3 g=clamp((f-df*mi)/(df*(ma-mi)),max(0.0,1.0-gwidth),1.0);//max(0.0,1.0-gwidth) should also be sent as uniform
  float c = g.x * g.y * g.z;
  gl_FragColor = vec4(c, c, c, 1.0);
  gl_FragColor = gl_FragColor * gl_Color;
}
"""

    GL = self.context().versionFunctions()
    GL.initializeOpenGLFunctions()
    self._GLVersion = GL.glGetString(GL.GL_VERSION)

    for li in range(3):
      self.gridList.append( [GL.glGenLists(1), GLRENDERMODE_REBUILD, np.array([]), np.array([]), 0] )

    self._GLPeakLists = {}
    self._GLPeakListLabels = {}

    self.object = self.makeObject()
    self.firstFont = CcpnGLFont('/Users/ejb66/Documents/Fonts/myfont.fnt')
    self._buildTextFlag = True

    self._mouseList = GL.glGenLists(1)
    self._buildMouse = True

    self._drawTextList = GL.glGenLists(1)
    self._axisXLabels = GL.glGenLists(1)
    self._axisLabels = GL.glGenLists(1)
    self.peakLabelling = 0

    # image = imread('/Users/ejb66/Documents/Fonts/myfont.png')
    #
    # self.texture = GL.glGenBuffers(1)
    #
    # GL.glActiveTexture(GL.GL_TEXTURE0)
    # GL.glEnable(GL.GL_TEXTURE_2D)
    # GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
    # GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
    # GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
    #
    # GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA
    #                 , image.shape[1], image.shape[0]
    #                 , 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE
    #                 , np.asarray(image).tobytes(order='C'))
    #
    # GL.glDisable(GL.GL_TEXTURE_2D)

    # TODO:ED only have openGL 2.1 installed, so no point yet
    self._shaderProgram1 = ShaderProgram(fragment=self._fragmentShader1, vertex=self._vertexShader1)
    self._shaderProgram2 = ShaderProgram(fragment=self._fragmentShader2, vertex=self._vertexShader2)

  def mousePressEvent(self, ev):
    self.lastPos = ev.pos()

    self._startCoordinate = [ev.pos().x(), self.height() - ev.pos().y()]
    self._endCoordinate = self._startCoordinate
    self._drawSelectionBox = True

  def mouseReleaseEvent(self, ev):
    self._drawSelectionBox = False
    self._lastButtonReleased = ev.button()

    if self._lastButtonReleased == Qt.RightButton:
      # raise right-button context menu
      self.parent.viewBox.menu.exec(self.mapToGlobal(ev.pos()))

  def keyPressEvent(self, event: QtGui.QKeyEvent):
    self._key = event.key()
    keyMod = QApplication.keyboardModifiers()
    if keyMod == Qt.ShiftModifier:
      self._isSHIFT = 'S'
    if keyMod == Qt.ControlModifier:
      self._isCTRL = 'C'

    # if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_A:
    #   self._key = 'A'
    # if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_S:
    #   self._key = 'S'

  def keyReleaseEvent(self, event: QtGui.QKeyEvent):
    self._key = ' '
    self._isSHIFT = ' '
    self._isCTRL = ' '

  def mouseMoveEvent(self, event):
    self.setFocus()
    dx = event.pos().x() - self.lastPos.x()
    dy = event.pos().y() - self.lastPos.y()
    self.lastPos = event.pos()

    # if event.buttons() & Qt.LeftButton:
    #   self.setXRotation(self.xRot + 8 * dy)
    #   self.setYRotation(self.yRot + 8 * dx)
    # elif event.buttons() & Qt.RightButton:
    #   self.setXRotation(self.xRot + 8 * dy)
    #   self.setZRotation(self.zRot + 8 * dx)

    self._mouseX = event.pos().x()
    self._mouseY = self.height() - event.pos().y()

    if event.buttons() & Qt.LeftButton:
      # do the complicated keypresses first
      if (self._key == Qt.Key_Control and self._isSHIFT == 'S') or \
          (self._key == Qt.Key_Shift and self._isCTRL) == 'C':
        self._endCoordinate = [event.pos().x(), self.height() - event.pos().y()]
        self._selectionMode = 3

      elif self._key == Qt.Key_Shift:
        self._endCoordinate = [event.pos().x(), self.height() - event.pos().y()]
        self._selectionMode = 1

      elif self._key == Qt.Key_Control:
        self._endCoordinate = [event.pos().x(), self.height() - event.pos().y()]
        self._selectionMode = 2

      else:
        self.axisL -= dx * self.pixelX
        self.axisR -= dx * self.pixelX
        self.axisT += dy * self.pixelY
        self.axisB += dy * self.pixelY

        # spawn rebuild event for the grid
        for li in self.gridList:
          li[1] = GLRENDERMODE_REBUILD
        for pp in self._GLPeakLists.values():
          pp[1] = GLRENDERMODE_RESCALE

        #   event.modifiers() & QtCore.Qt.ShiftModifier):
    #   position = event.scenePos()
    #   mousePoint = self.mapSceneToView(position)
    #   print(mousePoint)
    #
    #   elif (event.button() == QtCore.Qt.LeftButton) and (
    #   event.modifiers() & QtCore.Qt.ShiftModifier) and not (
    # event.modifiers() & QtCore.Qt.ControlModifier):
    # print('Add Select')
    #
    # elif event.button() == QtCore.Qt.MiddleButton and not event.modifiers():
    # event.accept()
    # print('Pick and Assign')
    #
    # elif event.button() == QtCore.Qt.RightButton and not event.modifiers():
    # event.accept()
    # print('Context Menu to be activated here')

  # def paintEvent_WithPainter(self, event):
  #   self.makeCurrent()
  #
  #   GL.glMatrixMode(GL.GL_MODELVIEW)
  #   GL.glPushMatrix()
  #
  #   self.set3DProjection()
  #
  #   self.setClearColor(self.trolltechPurple.darker())
  #   GL.glShadeModel(GL.GL_SMOOTH)
  #   GL.glEnable(GL.GL_DEPTH_TEST)
  #   # GL.glEnable(GL.GL_CULL_FACE)
  #   GL.glEnable(GL.GL_LIGHTING)
  #   GL.glEnable(GL.GL_LIGHT0)
  #   GL.glEnable(GL.GL_MULTISAMPLE)
  #   GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION,
  #                     (0.5, 5.0, 7.0, 1.0))
  #
  #   self.setupViewport(self.width(), self.height())
  #
  #   GL.glClear(
  #     GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
  #   GL.glLoadIdentity()
  #   GL.glTranslated(0.0, 0.0, -10.0)
  #   GL.glRotated(self.xRot / 16.0, 1.0, 0.0, 0.0)
  #   GL.glRotated(self.yRot / 16.0, 0.0, 1.0, 0.0)
  #   GL.glRotated(self.zRot / 16.0, 0.0, 0.0, 1.0)
  #   GL.glCallList(self.object)
  #
  #   GL.glMatrixMode(GL.GL_MODELVIEW)
  #   GL.glPopMatrix()
  #
  #   painter = QPainter(self)
  #   painter.setRenderHint(QPainter.Antialiasing)
  #
  #   for bubble in self.bubbles:
  #     if bubble.rect().intersects(QRectF(event.rect())):
  #       bubble.drawBubble(painter)
  #
  #   self.drawInstructions(painter)
  #   painter.end()
    self.update()

  @QtCore.pyqtSlot(bool)
  def paintGLsignal(self, bool):
    # my signal to repaint the screen after the spectra have changed
    # if bool:
    #   self.paintGL()
    pass

  def sign(self, x):
    return 1.0 if x >= 0 else -1.0

  def _drawMarks(self):

    if not hasattr(self, 'GLMarkList'):
      self.GLMarkList = [GL.glGenLists(1), GLRENDERMODE_REBUILD, None, None, 0, None]

    if self.GLMarkList[1] == GLRENDERMODE_REBUILD:
      # rebuild the mark list
      self.GLMarkList[1] = False
      GL.glNewList(self.GLMarkList[0], GL.GL_COMPILE)

      # draw some marks in here

      GL.glEnd()
      GL.glEndList()

    elif self.GLMarkList[1] == GLRENDERMODE_REBUILD:
      # rescale the marks here
      pass

    GL.glCallList(self.GLMarkList[0])

  def _rescalePeakList(self, spectrumView):
    drawList = self._GLPeakLists[spectrumView.spectrum.pid]

    x = abs(self.pixelX)
    y = abs(self.pixelY)
    if x <= y:
      r = 0.05
      w = 0.05 * y / x
    else:
      w = 0.05
      r = 0.05 * x / y

    tempVert = []
    for pp in drawList[5]:
      tempVert.append([pp[0] - r, pp[1] - w])
      tempVert.append([pp[0] + r, pp[1] + w])
      tempVert.append([pp[0] + r, pp[1] - w])
      tempVert.append([pp[0] - r, pp[1] + w])

    # rebuild the scaled vertices
    drawList[2] = np.array(tempVert, np.float32)

  def _buildPeakLists(self, spectrumView):
    spectrum = spectrumView.spectrum

    if spectrum.pid not in self._GLPeakLists:
      self._GLPeakLists[spectrum.pid] = [GL.glGenLists(1), GLRENDERMODE_REBUILD, np.array([]), np.array([]), 0, None]

    drawList = self._GLPeakLists[spectrum.pid]

    if drawList[1] == GLRENDERMODE_REBUILD:
      drawList[1] = GLRENDERMODE_DRAW               # back to draw mode
      GL.glNewList(drawList[0], GL.GL_COMPILE)

      drawList[2] = None
      drawList[3] = None
      drawList[4] = 0
      drawList[5] = []

      tempVert = []
      tempCol = []

      # find the correct scale to draw square pixels
      # don't forget to change when the axes change
      x = abs(self.pixelX)
      y = abs(self.pixelY)
      minIndex = 0 if x <= y else 1
      pos = [0.05, 0.05 * y / x]
      w = r = pos[minIndex]

      if x <= y:
        r = 0.05
        w = 0.025 * y / x
      else:
        w = 0.05
        r = 0.025 * x / y

      # GL.glBegin(GL.GL_LINES)
      for pls in spectrum.peakLists:
        for peak in pls.peaks:
          #
          # if hasattr(peak, '_isSelected') and peak._isSelected:
          #   colour = spectrumView.strip.plotWidget.highlightColour
          # else:
          #   colour = pls.symbolColour
          #
          # colR = int(colour.strip('# ')[0:2], 16)/255.0
          # colG = int(colour.strip('# ')[2:4], 16)/255.0
          # colB = int(colour.strip('# ')[4:6], 16)/255.0
          # GL.glColor4f(colR, colG, colB, 1.0)

          # draw a cross
          # TODO:ED need to put scaling in here to keep the cross square at 0.1ppm
          p0 = peak.position
          # GL.glBegin(GL.GL_LINES)
          # GL.glVertex2d(p0[0]-r, p0[1]-w)
          # GL.glVertex2d(p0[0]+r, p0[1]+w)
          # GL.glVertex2d(p0[0]+r, p0[1]-w)
          # GL.glVertex2d(p0[0]-r, p0[1]+w)
          #
          # # append the new points to the end of nparray
          # tempVert.append([p0[0]-r, p0[1]-w])
          # tempVert.append([p0[0]+r, p0[1]+w])
          # tempVert.append([p0[0]+r, p0[1]-w])
          # tempVert.append([p0[0]-r, p0[1]+w])
          #
          # tempCol.append([colR, colG, colB, 1.0])
          # tempCol.append([colR, colG, colB, 1.0])
          # tempCol.append([colR, colG, colB, 1.0])
          # tempCol.append([colR, colG, colB, 1.0])
          #
          # drawList[4] += 4                              # store the number of points
          # drawList[5].append((p0[0], p0[1]))            # store the point for quicker access
          #                                               # required for rescale
          #
          # if hasattr(peak, '_isSelected') and peak._isSelected:
          #   # draw box
          #   GL.glVertex2d(p0[0]-r, p0[1]-w)
          #   GL.glVertex2d(p0[0]+r, p0[1]-w)
          #   GL.glVertex2d(p0[0]+r, p0[1]+w)
          #   GL.glVertex2d(p0[0]-r, p0[1]+w)
          # GL.glEnd()
          #

          # TODO:ED don't delete yet, this is the peak label drawing
          # glut text failure - need something better
          colour = pls.textColour
          colR = int(colour.strip('# ')[0:2], 16)/255.0
          colG = int(colour.strip('# ')[2:4], 16)/255.0
          colB = int(colour.strip('# ')[4:6], 16)/255.0
          GL.glColor4f(colR, colG, colB, 1.0)

          GL.glPushMatrix()
          GL.glTranslated(p0[0]+r, p0[1]-w, 0.0)
          GL.glScaled(self.pixelX, self.pixelY, 1.0)

          if self.peakLabelling == 0:
            text = _getScreenPeakAnnotation(peak, useShortCode=False)
          elif self.parentWidget().strip.peakLabelling == 1:
            text = _getScreenPeakAnnotation(peak, useShortCode=True)
          else:
            text = _getPeakAnnotation(peak)  # original 'pid'

          GL.glCallLists([ord(c) for c in text])

          GL.glPopMatrix()

      # GL.glEnd()
      GL.glEndList()

      drawList[2] = np.array(tempVert, np.float32)
      drawList[3] = np.array(tempCol, np.float32)

    elif drawList[1] == GLRENDERMODE_RESCALE:
      drawList[1] = GLRENDERMODE_DRAW               # back to draw mode
      self._rescalePeakList(spectrumView=spectrumView)

  def _buildPeakListLabels(self, spectrumView):
    spectrum = spectrumView.spectrum

    if spectrum.pid not in self._GLPeakListLabels:
      self._GLPeakListLabels[spectrum.pid] = [GL.glGenLists(1), GLRENDERMODE_REBUILD, np.array([]), np.array([]), 0, None]

    drawList = self._GLPeakListLabels[spectrum.pid]
    if drawList[1] == GLRENDERMODE_REBUILD:
      drawList[1] = GLRENDERMODE_DRAW               # back to draw mode
      drawList[2] = None
      drawList[3] = None
      drawList[4] = 0
      drawList[5] = []

      tempVert = []
      tempCol = []

      # find the correct scale to draw square pixels
      # don't forget to change when the axes change
      x = abs(self.pixelX)
      y = abs(self.pixelY)
      minIndex = 0 if x <= y else 1
      pos = [0.05, 0.05 * y / x]
      w = r = pos[minIndex]

      if x <= y:
        r = 0.05
        w = 0.025 * y / x
      else:
        w = 0.05
        r = 0.025 * x / y

      for pls in spectrum.peakLists:
        for peak in pls.peaks:
          p0 = peak.position
          colour = pls.textColour
          colR = int(colour.strip('# ')[0:2], 16)/255.0
          colG = int(colour.strip('# ')[2:4], 16)/255.0
          colB = int(colour.strip('# ')[4:6], 16)/255.0
          GL.glColor4f(colR, colG, colB, 1.0)

          GL.glPushMatrix()
          GL.glTranslated(p0[0]+r, p0[1]-w, 0.0)
          GL.glScaled(self.pixelX, self.pixelY, 1.0)

          if self.peakLabelling == 0:
            text = _getScreenPeakAnnotation(peak, useShortCode=False)
          elif self.parentWidget().strip.peakLabelling == 1:
            text = _getScreenPeakAnnotation(peak, useShortCode=True)
          else:
            text = _getPeakAnnotation(peak)  # original 'pid'

          # TODO:ED change this to a vertex array
          # GL.glCallLists([ord(c) for c in text])
          for c in text:
            ch = ord(c)

          GL.glPopMatrix()
      GL.glEndList()

      drawList[2] = np.array(tempVert, np.float32)
      drawList[3] = np.array(tempCol, np.float32)

    elif drawList[1] == GLRENDERMODE_RESCALE:
      drawList[1] = GLRENDERMODE_DRAW               # back to draw mode
      self._rescalePeakListLabel(spectrumView=spectrumView)

  def _drawPeakListVertices(self, spectrumView):
    drawList = self._GLPeakLists[spectrumView.spectrum.pid]

    # new bit to use a vertex array to draw the peaks, very fast and easy
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    GL.glEnableClientState(GL.GL_COLOR_ARRAY)

    GL.glVertexPointer(2, GL.GL_FLOAT, 0, drawList[2])
    GL.glColorPointer(4, GL.GL_FLOAT, 0, drawList[3])
    GL.glDrawArrays(GL.GL_LINES, 0, drawList[4])

    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    GL.glDisableClientState(GL.GL_COLOR_ARRAY)

    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glBindTexture(GL.GL_TEXTURE_2D, self.firstFont.textureId)
    GL.glListBase( self.firstFont.base )
    GL.glCallList(drawList[0])        # temporarily call the drawing of the text
    GL.glDisable(GL.GL_TEXTURE_2D)

    GL.glDisable(GL.GL_BLEND)

  def _drawPeakListLabels(self, spectrumView):
    drawList = self._GLPeakListLabels[spectrumView.spectrum.pid]

    # new bit to use a vertex array to draw the peaks, very fast and easy
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    GL.glEnableClientState(GL.GL_COLOR_ARRAY)
    GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

    GL.glVertexPointer(2, GL.GL_FLOAT, 0, drawList[2])
    GL.glColorPointer(4, GL.GL_FLOAT, 0, drawList[3])
    GL.glTexCoordPointer(4, GL.GL_FLOAT, 0, drawList[4])
    GL.glDrawArrays(GL.GL_LINES, 0, drawList[5])

    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    GL.glDisableClientState(GL.GL_COLOR_ARRAY)
    GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)

    GL.glDisable(GL.GL_BLEND)



  def _round_sig(self, x, sig=6, small_value=1.0e-9):
    return 0 if x==0 else round(x, sig - int(math.floor(math.log10(max(abs(x), abs(small_value))))) - 1)

  def paintGL(self):
    self.makeCurrent()

    GL.glPushAttrib(GL.GL_ALL_ATTRIB_BITS)

    GL.glClearColor(0.05, 0.05, 0.05, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    getGLvector = (GL.GLfloat * 2)()
    GL.glGetFloatv(GL.GL_ALIASED_LINE_WIDTH_RANGE, getGLvector)
    linewidths = [i for i in getGLvector]

    self.set2DProjection()

    self.modelViewMatrix = (GL.GLdouble * 16)()
    self.projectionMatrix = (GL.GLdouble * 16)()
    self.viewport = (GL.GLint * 4)()

    GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX, self.modelViewMatrix)
    GL.glGetDoublev(GL.GL_PROJECTION_MATRIX, self.projectionMatrix)
    GL.glGetIntegerv(GL.GL_VIEWPORT, self.viewport)

    self.worldCoordinate = GLU.gluUnProject(
      self._mouseX, self._mouseY, 0,
      self.modelViewMatrix,
      self.projectionMatrix,
      self.viewport,
    )
    self.viewport = [i for i in self.viewport]
    # grab coordinates of the transformed viewport
    self._infiniteLineUL = GLU.gluUnProject(
      0.0,
      self.viewport[3]+self.viewport[1],
      0.0,
      self.modelViewMatrix,
      self.projectionMatrix,
      self.viewport,
    )
    self._infiniteLineBR = GLU.gluUnProject(
      self.viewport[2]+self.viewport[0],
      self.viewport[1],
      0.0,
      self.modelViewMatrix,
      self.projectionMatrix,
      self.viewport,
    )

    # calculate the width of a world pixel on the screen
    origin = GLU.gluUnProject(
      0.0, 0.0, 0.0,
      self.modelViewMatrix,
      self.projectionMatrix,
      self.viewport,
    )
    pointOne = GLU.gluUnProject(
      1.0, 1.0, 0.0,
      self.modelViewMatrix,
      self.projectionMatrix,
      self.viewport,
    )
    self.pixelX = pointOne[0]-origin[0]
    self.pixelY = pointOne[1]-origin[1]

    # GL.glEnable(GL.GL_LINE_SMOOTH)
    # GL.glHint(GL.GL_LINE_SMOOTH_HINT, GL.GL_NICEST)
    # GL.glEnable(GL.GL_BLEND)
    # GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glLineWidth(1.0)
    for spectrumView in self.parent.spectrumViews:
      try:
        # could put a signal on buildContours
        if spectrumView.buildContours:
          spectrumView._buildContours(None)  # need to trigger these changes now
          spectrumView.buildContours = False  # set to false, as we have rebuilt
          # set to True and update() will rebuild the contours
          # can be done with a call to self.rebuildContours()

        self._spectrumValues = spectrumView._getValues()
        dx = self.sign(self._infiniteLineBR[0] - self._infiniteLineUL[0])
        dy = self.sign(self._infiniteLineUL[1] - self._infiniteLineBR[1])

        # get the bounding box of the spectra
        fx0, fx1 = self._spectrumValues[0].maxAliasedFrequency, self._spectrumValues[0].minAliasedFrequency
        fy0, fy1 = self._spectrumValues[1].maxAliasedFrequency, self._spectrumValues[1].minAliasedFrequency
        dxAF = fx0 - fx1
        dyAF = fy0 - fy1
        xScale = dx*dxAF/self._spectrumValues[0].totalPointCount
        yScale = dy*dyAF/self._spectrumValues[1].totalPointCount

        GL.glPushMatrix()
        GL.glTranslate(fx0, fy0, 0.0)
        GL.glScale(xScale, yScale, 1.0)

        # paint the spectrum
        spectrumView._paintContoursNoClip()
        GL.glPopMatrix()

        # draw the bounding box
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glColor4f(*spectrumView.posColour[0:3], 0.5)
        # GL.glLineStipple(1, 0xAAAA)
        # GL.glEnable(GL.GL_LINE_STIPPLE)
        GL.glBegin(GL.GL_LINE_LOOP)
        GL.glVertex2d(fx0, fy0)
        GL.glVertex2d(fx0, fy1)
        GL.glVertex2d(fx1, fy1)
        GL.glVertex2d(fx1, fy0)
        GL.glEnd()
        # GL.glDisable(GL.GL_LINE_STIPPLE)
        GL.glDisable(GL.GL_BLEND)

        # draw the peak List, labelling, marks

        self._buildPeakLists(spectrumView)      # should include rescaling
        self._drawPeakListVertices(spectrumView)

      except:
        raise
        spectrumView._buildContours(None)
        # pass

    # this is needed if it is a paintEvent
    # painter = QPainter(self)
    # painter.setRenderHint(QPainter.Antialiasing)
    #
    # for bubble in self.bubbles:
    #   if bubble.rect().intersects(QRectF(event.rect())):
    #     bubble.drawBubble(painter)
    #
    # self.drawInstructions(painter)
    #
    # painter.end()

    # draw cursor
    # self.set2DProjectionFlat()
    #
    # GL.glColor4f(0.9, 0.9, 1.0, 150)
    # GL.glBegin(GL.GL_LINES)
    # GL.glVertex2f(self._mouseX, 0)
    # GL.glVertex2f(self._mouseX, self.height())
    # GL.glVertex2f(0, self._mouseY)
    # GL.glVertex2f(self.width(), self._mouseY)
    # GL.glEnd()

    self.set2DProjection()
    self.axisLabelling, labelsChanged = self._buildAxes(self.gridList[0], axisList=[0,1], scaleGrid=[2,1,0], r=1.0, g=1.0, b=1.0, transparency=500.0)
    self.set2DProjectionRightAxis()
    self._buildAxes(self.gridList[1], axisList=[1], scaleGrid=[1,0], r=0.2, g=1.0, b=0.3, transparency=64.0)
    self.set2DProjectionBottomAxis()
    self._buildAxes(self.gridList[2], axisList=[0], scaleGrid=[1,0], r=0.2, g=1.0, b=0.3, transparency=64.0)

    # draw axis lines to right and bottom
    self.set2DProjectionFlat()
    h = self.height()
    w = self.width()
    GL.glColor4f(0.2, 1.0, 0.3, 1.0)
    GL.glBegin(GL.GL_LINES)
    GL.glVertex2d(0, 0)         # not sure why 0 doesn't work
    GL.glVertex2d(w-36, 0)      # think I'm drawing over it with the next viewport
    GL.glVertex2d(w-36, 0)
    GL.glVertex2d(w-36, h-36)
    GL.glEnd()


    # draw all the peak GLLists here



    self.set2DProjection()      # set back to the main projection

    if self._drawSelectionBox:
      GL.glEnable(GL.GL_BLEND)
      GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

      self._dragStart = GLU.gluUnProject(
        self._startCoordinate[0], self._startCoordinate[1], 0,
        self.modelViewMatrix,
        self.projectionMatrix,
        self.viewport,
      )
      self._dragEnd = GLU.gluUnProject(
        self._endCoordinate[0], self._endCoordinate[1], 0,
        self.modelViewMatrix,
        self.projectionMatrix,
        self.viewport,
      )

      if self._selectionMode == 1:    # yellow
        GL.glColor4f(0.8, 0.9, 0.2, 0.3)
      elif self._selectionMode == 2:      # purple
        GL.glColor4f(0.8, 0.2, 0.9, 0.3)
      elif self._selectionMode == 3:      # cyan
        GL.glColor4f(0.2, 0.5, 0.9, 0.3)

      GL.glBegin(GL.GL_QUADS)
      GL.glVertex2d(self._dragStart[0], self._dragStart[1])
      GL.glVertex2d(self._dragEnd[0], self._dragStart[1])
      GL.glVertex2d(self._dragEnd[0], self._dragEnd[1])
      GL.glVertex2d(self._dragStart[0], self._dragEnd[1])
      GL.glEnd()

      if self._selectionMode == 1:    # yellow
        GL.glColor4f(0.8, 0.9, 0.2, 0.9)
      elif self._selectionMode == 2:      # purple
        GL.glColor4f(0.8, 0.2, 0.9, 0.9)
      elif self._selectionMode == 3:      # cyan
        GL.glColor4f(0.2, 0.5, 0.9, 0.9)

      GL.glBegin(GL.GL_LINE_STRIP)
      GL.glVertex2d(self._dragStart[0], self._dragStart[1])
      GL.glVertex2d(self._dragEnd[0], self._dragStart[1])
      GL.glVertex2d(self._dragEnd[0], self._dragEnd[1])
      GL.glVertex2d(self._dragStart[0], self._dragEnd[1])
      GL.glVertex2d(self._dragStart[0], self._dragStart[1])
      GL.glEnd()
      GL.glDisable(GL.GL_BLEND)

    # print ('>>>Coords', self._infiniteLineBL, self._infiniteLineTR)
    # this gets the correct mapped coordinates
    GL.glColor4f(0.8, 0.9, 1.0, 1.0)
    GL.glBegin(GL.GL_LINES)
    GL.glVertex2d(self.worldCoordinate[0], self._infiniteLineUL[1])
    GL.glVertex2d(self.worldCoordinate[0], self._infiniteLineBR[1])
    GL.glVertex2d(self._infiniteLineUL[0], self.worldCoordinate[1])
    GL.glVertex2d(self._infiniteLineBR[0], self.worldCoordinate[1])
    GL.glEnd()

    coords = " "+str(self._isSHIFT)+str(self._isCTRL)+str(self._key)+" : "\
              +str(round(self.worldCoordinate[0], 3))\
              +", "+str(round(self.worldCoordinate[1], 3))
    # self.glut_print(self.worldCoordinate[0], self.worldCoordinate[1]
    #                 , GLUT.GLUT_BITMAP_HELVETICA_12
    #                 , coords
    #                 , 1.0, 1.0, 1.0, 1.0)

    if self._buildTextFlag == GLRENDERMODE_REBUILD:
      self._buildTextFlag = GLRENDERMODE_DRAW
      GL.glNewList(self._drawTextList, GL.GL_COMPILE)

      for ti in range(7):
        # GL.glRotate(25.0, 0.0, 0.0, 1.0)      # can rotate if we need to :)

        GL.glPushMatrix()
        GL.glTranslate(ti*50.0, ti*50, 0.0)
        GL.glCallLists([ord(c) for c in 'The Quick\tBrown Fox\n013617@something'])
        GL.glPopMatrix()

      GL.glEndList()


    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glBindTexture(GL.GL_TEXTURE_2D, self.firstFont.textureId)

    GL.glListBase( self.firstFont.base )

    # GL.glPushMatrix()
    # GL.glTranslated(50, 300, 0)
    # # GL.glScalef(-0.5, -3.0, 1.0)        # because the axes are inverted
    # GL.glCallList(self._drawTextList)
    # GL.glPopMatrix()

    # self.set2DProjection()
    # for spectrumView in self.parent.spectrumViews:
    #   self._drawPeakLists(spectrumView)

    # draw the mouse coordinates
    self.set2DProjectionFlat()
    GL.glPushMatrix()
    GL.glTranslate(self._mouseX, self._mouseY-30, 0.0)      # from bottom left of window?
    # GL.glScalef(3.0, 3.0, 1.0)                              # use this for scaling font
    GL.glColor3f(0.9, 0.9, 0.9)
    GL.glCallLists([ord(c) for c in coords])
    GL.glPopMatrix()

    # draw axes labelling
    if labelsChanged:
      GL.glNewList(self._axisLabels, GL.GL_COMPILE)

      self.set2DProjectionBottomAxisBar(axisLimits=[self.axisL, self.axisR, 0, AXIS_MARGIN])
      for axLabel in self.axisLabelling['0']:
        axisX = axLabel[2]
        axisXText = str(int(axisX)) if axLabel[3] >= 1 else str(axisX)

        GL.glPushMatrix()
        # GL.glTranslate(axisX-(5.0*self.pixelX*len(str(axisX))), 15, 0.0)
        GL.glTranslate(axisX-(5.0*self.pixelX), 30, 0.0)
        GL.glScalef(self.pixelX, 1.0, 1.0)
        GL.glRotate(-90.0, 0.0, 0.0, 1.0)

        GL.glColor3f(0.9, 0.9, 0.9)
        GL.glCallLists([ord(c) for c in axisXText])
        GL.glPopMatrix()

      self.set2DProjectionRightAxisBar(axisLimits=[0, AXIS_MARGIN, self.axisB, self.axisT])
      for axLabel in self.axisLabelling['1']:
        axisY = axLabel[2]
        axisYText = str(int(axisY)) if axLabel[3] >= 1 else str(axisY)

        GL.glPushMatrix()
        GL.glTranslate(5.0, axisY-5.0*self.pixelY, 0.0)
        GL.glScalef(1.0, self.pixelY, 1.0)

        GL.glColor3f(0.9, 0.9, 0.9)
        GL.glCallLists([ord(c) for c in axisYText])
        GL.glPopMatrix()

      GL.glEndList()

    GL.glCallList(self._axisLabels)

    GL.glDisable(GL.GL_BLEND)
    GL.glDisable(GL.GL_TEXTURE_2D)


    GL.glUseProgram(self._shaderProgram2.program_id)

    self.set2DProjectionFlat()

    GL.glColor4f(1.0, 1.0, 1.0, 1.0)
    GL.glBegin(GL.GL_QUADS)
    GL.glVertex3f(0.0, 0.0, 0.0)
    GL.glVertex3f(100.0, 0.0, 120.0)
    GL.glVertex3f(100.0, 100.0, 5167.0)
    GL.glVertex3f(0.0, 100.0, 636.0)
    GL.glEnd()

    GL.glUseProgram(0)

    GL.glPopAttrib()
    GLUT.glutSwapBuffers()
    self.doneCurrent()

  # def resizeGL(self, width, height):
  #   self.setupViewport(width, height)
  #   self.update()

  # def showEvent(self, event):
  #   self.createBubbles(20 - len(self.bubbles))

  def sizeHint(self):
    return QSize(400, 400)

  def makeObject(self):
    # list = GL.glGenLists(1)
    list = GL.glGenLists(1)
    GL.glNewList(list, GL.GL_COMPILE)

    GL.glEnable(GL.GL_NORMALIZE)
    GL.glBegin(GL.GL_QUADS)

    GL.glMaterialfv(GL.GL_FRONT, GL.GL_DIFFUSE,
                   (self.trolltechGreen.red() / 255.0,
                    self.trolltechGreen.green() / 255.0,
                    self.trolltechGreen.blue() / 255.0, 1.0))

    x1 = +0.06
    y1 = -0.14
    x2 = +0.14
    y2 = -0.06
    x3 = +0.08
    y3 = +0.00
    x4 = +0.30
    y4 = +0.22

    self.quad(x1, y1, x2, y2, y2, x2, y1, x1)
    self.quad(x3, y3, x4, y4, y4, x4, y3, x3)

    self.extrude(x1, y1, x2, y2)
    self.extrude(x2, y2, y2, x2)
    self.extrude(y2, x2, y1, x1)
    self.extrude(y1, x1, x1, y1)
    self.extrude(x3, y3, x4, y4)
    self.extrude(x4, y4, y4, x4)
    self.extrude(y4, x4, y3, x3)

    NumSectors = 200

    for i in range(NumSectors):
      angle1 = (i * 2 * math.pi) / NumSectors
      x5 = 0.30 * math.sin(angle1)
      y5 = 0.30 * math.cos(angle1)
      x6 = 0.20 * math.sin(angle1)
      y6 = 0.20 * math.cos(angle1)

      angle2 = ((i + 1) * 2 * math.pi) / NumSectors
      x7 = 0.20 * math.sin(angle2)
      y7 = 0.20 * math.cos(angle2)
      x8 = 0.30 * math.sin(angle2)
      y8 = 0.30 * math.cos(angle2)

      self.quad(x5, y5, x6, y6, x7, y7, x8, y8)

      self.extrude(x6, y6, x7, y7)
      self.extrude(x8, y8, x5, y5)

    GL.glEnd()

    GL.glEndList()
    return list

  def quad(self, x1, y1, x2, y2, x3, y3, x4, y4):
    GL.glNormal3d(0.0, 0.0, -1.0)
    GL.glVertex3d(x1, y1, -0.05)
    GL.glVertex3d(x2, y2, -0.05)
    GL.glVertex3d(x3, y3, -0.05)
    GL.glVertex3d(x4, y4, -0.05)

    GL.glNormal3d(0.0, 0.0, 1.0)
    GL.glVertex3d(x4, y4, +0.05)
    GL.glVertex3d(x3, y3, +0.05)
    GL.glVertex3d(x2, y2, +0.05)
    GL.glVertex3d(x1, y1, +0.05)

  def extrude(self, x1, y1, x2, y2):
    self.setColor(self.trolltechGreen.darker(250 + int(100 * x1)))

    GL.glNormal3d((x1 + x2) / 2.0, (y1 + y2) / 2.0, 0.0)
    GL.glVertex3d(x1, y1, +0.05)
    GL.glVertex3d(x2, y2, +0.05)
    GL.glVertex3d(x2, y2, -0.05)
    GL.glVertex3d(x1, y1, -0.05)

  def normalizeAngle(self, angle):
    while angle < 0:
      angle += 360 * 16
    while angle > 360 * 16:
      angle -= 360 * 16
    return angle

  # def createBubbles(self, number):
  #   for i in range(number):
  #     position = QPointF(self.width() * (0.1 + 0.8 * random.random()),
  #                        self.height() * (0.1 + 0.8 * random.random()))
  #     radius = min(self.width(), self.height()) * (0.0125 + 0.0875 * random.random())
  #     velocity = QPointF(self.width() * 0.0125 * (-0.5 + random.random()),
  #                        self.height() * 0.0125 * (-0.5 + random.random()))
  # 
  #     self.bubbles.append(Bubble(position, radius, velocity))

  def setupViewport(self, width, height):
    # side = min(width, height)
    # GL.glViewport((width - side) // 2, (height - side) // 2, side,
    #                    side)
    # GL.glViewport(0, -1, width, height)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glViewport(0, height//2, width//2, height)
    # GL.glMatrixMode(GL.GL_PROJECTION)
    # GL.glLoadIdentity()
    # GL.glOrtho(-0.5, +0.5, +0.5, -0.5, 4.0, 15.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)

  def set3DProjection(self):
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glOrtho(-0.5, +0.5, +0.5, -0.5, 4.0, 15.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()

  def set2DProjection(self):
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()

    # put into a box in the viewport at (50, 50) to (150, 150)
    # GL.glViewport(150, 50, 350, 150)
    h = self.height()
    w = self.width()
    GL.glViewport(0, 35, w-35, h-35)   # leave a 35 width margin for the axes - bottom/right
                                        # (0,0) is bottom-left
    # GLU.gluOrtho2D(-10, 50, -10, 0)

    # testing - grab the coordinates from the plotWidget
    # axisRangeL = self.parent.plotWidget.getAxis('bottom').range
    # axL = axisRangeL[0]
    # axR = axisRangeL[1]
    # axisRangeB = self.parent.plotWidget.getAxis('right').range
    # axB = axisRangeB[0]
    # axT = axisRangeB[1]

    # L/R/B/T   (usually) but 'bottom' is relative to the top-left corner
    # GLU.gluOrtho2D(axL, axR, axB, axT)      # nearly!
    GLU.gluOrtho2D(self.axisL, self.axisR, self.axisB, self.axisT)      # nearly!

    # GL.glScalef(1, 1, 1);

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    # GL.glTranslatef(0.1, 0.1, 0.1)

  def set2DProjectionRightAxis(self):
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()

    axisLine = 5
    h = self.height()
    w = self.width()
    GL.glViewport(w-35-axisLine, 35, axisLine, h-35)   # leave a 35 width margin for the axes - bottom/right
                                        # (0,0) is bottom-left

    # axisRangeL = self.parent.plotWidget.getAxis('bottom').range
    # axL = axisRangeL[0]
    # axR = axisRangeL[1]
    # axisRangeB = self.parent.plotWidget.getAxis('right').range
    # axB = axisRangeB[0]
    # axT = axisRangeB[1]

    # L/R/B/T   (usually) but 'bottom' is relative to the top-left corner
    # GLU.gluOrtho2D(axL, axR, axB, axT)
    GLU.gluOrtho2D(self.axisL, self.axisR, self.axisB, self.axisT)      # nearly!

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()

  def set2DProjectionRightAxisBar(self, axisLimits=None):
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()

    axisLine = 5
    h = self.height()
    w = self.width()
    GL.glViewport(w-AXIS_MARGIN, AXIS_MARGIN, AXIS_MARGIN, h-AXIS_MARGIN)   # leave a 35 width margin for the axes - bottom/right
    GLU.gluOrtho2D(*axisLimits)      # nearly!

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()

  def set2DProjectionBottomAxis(self):
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()

    axisLine = 5
    h = self.height()
    w = self.width()
    GL.glViewport(0, 35, w-35, axisLine)   # leave a 35 width margin for the axes - bottom/right
                                    # (0,0) is bottom-left

    # axisRangeL = self.parent.plotWidget.getAxis('bottom').range
    # axL = axisRangeL[0]
    # axR = axisRangeL[1]
    # axisRangeB = self.parent.plotWidget.getAxis('right').range
    # axB = axisRangeB[0]
    # axT = axisRangeB[1]

    # L/R/B/T   (usually) but 'bottom' is relative to the top-left corner
    # GLU.gluOrtho2D(axL, axR, axB, axT)
    GLU.gluOrtho2D(self.axisL, self.axisR, self.axisB, self.axisT)      # nearly!

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()

  def set2DProjectionBottomAxisBar(self, axisLimits=None):
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()

    axisLine = 5
    h = self.height()
    w = self.width()
    GL.glViewport(0, 0, w-AXIS_MARGIN, AXIS_MARGIN)   # leave a 35 width margin for the axes - bottom/right
    GLU.gluOrtho2D(*axisLimits)

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()

  def set2DProjectionFlat(self):
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()

    # put into a box in the viewport at (50, 50) to (150, 150)
    # GL.glViewport(150, 50, 350, 150)
    h = self.height()
    w = self.width()
    # GL.glViewport(15, 35, w-35, h-50)   # leave a 35 width margin for the axes
    #                                     # '15' is a temporary border at left/top
    GL.glViewport(0, 35, w-35, h-35)      # leave a 35 width margin for the axes
                                         # '15' is a temporary border at left/top

    GLU.gluOrtho2D(0, w-36, -1, h-36)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()

  def drawInstructions(self, painter):
    text = "Click and drag with the left mouse button to rotate the Qt " \
           "logo."
    metrics = QFontMetrics(self.font())
    border = max(4, metrics.leading())

    rect = metrics.boundingRect(0, 0, self.width() - 2 * border,
                                int(self.height() * 0.125), Qt.AlignCenter | Qt.TextWordWrap,
                                text)
    painter.setRenderHint(QPainter.TextAntialiasing)
    painter.fillRect(QRect(0, 0, self.width(), rect.height() + 2 * border),
                     QColor(0, 0, 0, 127))
    painter.setPen(Qt.white)
    painter.fillRect(QRect(0, 0, self.width(), rect.height() + 2 * border),
                     QColor(0, 0, 0, 127))
    painter.drawText((self.width() - rect.width()) / 2, border, rect.width(),
                     rect.height(), Qt.AlignCenter | Qt.TextWordWrap, text)

  def setClearColor(self, c):
    GL.glClearColor(c.redF(), c.greenF(), c.blueF(), c.alphaF())

  def setColor(self, c):
    GL.glColor4f(c.redF(), c.greenF(), c.blueF(), c.alphaF())

  def _buildAxes(self, gridGLList, axisList=None, scaleGrid=None, r=0.0, g=0.0, b=0.0, transparency=256.0):
    dim = [self.width(), self.height()]

    ul = np.array([self._infiniteLineUL[0], self._infiniteLineUL[1]])
    br = np.array([self._infiniteLineBR[0], self._infiniteLineBR[1]])

    labelling = {'0': [], '1': []}
    labelsChanged = False

    if gridGLList[1] == GLRENDERMODE_REBUILD:

      GL.glNewList(gridGLList[0], GL.GL_COMPILE)
      gridGLList[1] = GLRENDERMODE_DRAW
      labelsChanged = True

      gridGLList[2] = None
      gridGLList[3] = None
      gridGLList[4] = 0
      tempList = []
      tempCol = []

      if ul[0] > br[0]:
        x = ul[0]
        ul[0] = br[0]
        br[0] = x
      for i in scaleGrid:       #  [2,1,0]:   ## Draw three different scales of grid
        dist = br-ul
        nlTarget = 10.**i
        d = 10. ** np.floor(np.log10(abs(dist/nlTarget))+0.5)
        ul1 = np.floor(ul / d) * d
        br1 = np.ceil(br / d) * d
        dist = br1-ul1
        nl = (dist / d) + 0.5

        for ax in axisList:           #   range(0,2):  ## Draw grid for both axes
          ppl = np.array( dim[ax] / nl[ax] )                      # ejb
          c = np.clip(3.*(ppl-3), 0., 30.)
          GL.glColor4f(r, g, b, c/transparency)               # make high order lines more transparent
          GL.glBegin(GL.GL_LINES)
          bx = (ax+1) % 2
          for x in range(0, int(nl[ax])):
            p1 = np.array([0.,0.])
            p2 = np.array([0.,0.])
            p1[ax] = ul1[ax] + x * d[ax]
            p2[ax] = p1[ax]
            p1[bx] = ul[bx]
            p2[bx] = br[bx]
            if p1[ax] < min(ul[ax], br[ax]) or p1[ax] > max(ul[ax], br[ax]):
                continue
            # p.drawLine(QtCore.QPointF(p1[0], p1[1]), QtCore.QPointF(p2[0], p2[1]))
            GL.glVertex2f(p1[0], p1[1])
            GL.glVertex2f(p2[0], p2[1])

            if i == 1:            # should be largest scale grid
              if p1[0] == p2[0]:
                labelling[str(ax)].append((i, ax, p1[0], d[0]))
              else:
                labelling[str(ax)].append((i, ax, p1[1], d[1]))

            # append the new points to the end of nparray
            tempList.append([p1[0], p1[1]])
            tempList.append([p2[0], p2[1]])
            tempCol.append([r, g, b, c/transparency])
            tempCol.append([r, g, b, c/transparency])

            gridGLList[4] += 2

          GL.glEnd()

      GL.glEndList()
      gridGLList[2] = np.array(tempList, np.float32)
      gridGLList[3] = np.array(tempCol, np.float32)

    # old drawing of the grid
    # GL.glEnable(GL.GL_BLEND)
    # GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    # GL.glLineWidth(1.0)
    #
    # GL.glCallList(gridGLList[0])
    #
    # GL.glDisable(GL.GL_BLEND)


    # new bit to use a vertex array to draw the peaks, very fast and easy
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    GL.glEnableClientState(GL.GL_COLOR_ARRAY)

    GL.glVertexPointer(2, GL.GL_FLOAT, 0, gridGLList[2])
    GL.glColorPointer(4, GL.GL_FLOAT, 0, gridGLList[3])
    GL.glDrawArrays(GL.GL_LINES, 0, gridGLList[4])

    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    GL.glDisableClientState(GL.GL_COLOR_ARRAY)
    GL.glDisable(GL.GL_BLEND)

    # tr = self.deviceTransform()
    # p.setWorldTransform(fn.invertQTransform(tr))
    # for t in texts:
    #     x = tr.map(t[0]) + Point(0.5, 0.5)
    #     p.drawText(x, t[1])
    # p.end()

    return labelling, labelsChanged


GlyphXpos = 'Xpos'
GlyphYpos = 'Ypos'
GlyphWidth = 'Width'
GlyphHeight = 'Height'
GlyphXoffset = 'Xoffset'
GlyphYoffset = 'Yoffset'
GlyphOrigW = 'OrigW'
GlyphOrigH = 'OrigH'
GlyphKerns = 'Kerns'

class CcpnGLFont():
  def __init__(self, fileName=None, size=12, base=0):
    self.fontName = None
    self.fontGlyph = [None] * 256
    self.base = base

    with open(fileName, 'r') as op:
      self.fontInfo = op.read().split('\n')

    # no checking yet
    self.fontFile = self.fontInfo[0].replace('textures: ', '')
    self.fontPNG = imread('/Users/ejb66/Documents/Fonts/'+self.fontFile)
    self.fontName = self.fontInfo[1].split()[0]
    self.fontSize = self.fontInfo[1].split()[1]

    row = 2
    exitDims = False

    while exitDims is False and row < len(self.fontInfo):
      line = self.fontInfo[row]
      print (line)
      if line.startswith('kerning'):
        exitDims = True
      else:
        try:
          lineVals = [int(ll) for ll in line.split()]
          if len(lineVals) == 9:
            chrNum, a0, b0, c0, d0, e0, f0, g0, h0 = lineVals

            # only keep the simple chars for the minute
            if chrNum < 256:
              self.fontGlyph[chrNum] = {}
              self.fontGlyph[chrNum][GlyphXpos] = a0
              self.fontGlyph[chrNum][GlyphYpos] = b0
              self.fontGlyph[chrNum][GlyphWidth] = c0
              self.fontGlyph[chrNum][GlyphHeight] = d0
              self.fontGlyph[chrNum][GlyphXoffset] = e0
              self.fontGlyph[chrNum][GlyphYoffset] = f0
              self.fontGlyph[chrNum][GlyphOrigW]= g0
              self.fontGlyph[chrNum][GlyphOrigH] = h0
              self.fontGlyph[chrNum][GlyphKerns] = {}
          else:
            exitDims = True
        except:
          exitDims = True
      row += 1

    if line.startswith('kerning'):
      # kerning list is included

      exitKerns = False
      while exitKerns is False and row < len(self.fontInfo):
        line = self.fontInfo[row]
        print(line)

        try:
          lineVals = [int(ll) for ll in line.split()]
          chrNum, chrNext, val = lineVals

          if chrNum < 256 and chrNext < 256:
            self.fontGlyph[chrNum][GlyphKerns][chrNext] = val
        except:
          exitKerns = True
        row += 1

    width, height, ascender, descender = 0, 0, 0, 0
    for c in range(0, 256):
      if chrNum < 256 and self.fontGlyph[chrNum]:
        width = max( width, self.fontGlyph[chrNum][GlyphOrigW] )
        height = max( height, self.fontGlyph[chrNum][GlyphOrigH] )

    self.textureId = GL.glGenTextures(1)
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glBindTexture( GL.GL_TEXTURE_2D, self.textureId )

    GL.glTexImage2D( GL.GL_TEXTURE_2D, 0, GL.GL_RGBA
                     , self.fontPNG.shape[1], self.fontPNG.shape[0]
                     , 0
                     , GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, self.fontPNG )

    # generate a MipMap to cope with smaller text (may not be needed soon)
    GL.glTexParameteri( GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST )
    GL.glTexParameteri( GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST )

    # GL.glTexParameteri( GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR )
    # GL.glGenerateMipmap( GL.GL_TEXTURE_2D )
    GL.glDisable(GL.GL_TEXTURE_2D)

    self.base = GL.glGenLists(256)
    dx = 1.0 / float(self.fontPNG.shape[1])
    dy = 1.0 / float(self.fontPNG.shape[0])
    for i in range(256):
      if self.fontGlyph[i] or i == 10 or i == 9:    # newline and tab
        # c = chr(i)

        GL.glNewList(self.base + i, GL.GL_COMPILE)
        if (i == 10):                                 # newline
          GL.glPopMatrix()
          GL.glTranslatef(0.0, -height, 0.0)
          GL.glPushMatrix()
        elif (i == 9):                                # tab
          GL.glTranslatef(4.0 * width, 0.0, 0.0)
        elif (i >= 32):
          x = float(self.fontGlyph[i][GlyphXpos])   # try +0.5 for centre of texel
          y = float(self.fontGlyph[i][GlyphYpos])
          px = self.fontGlyph[i][GlyphXoffset]
          py = self.fontGlyph[i][GlyphYoffset]
          w = self.fontGlyph[i][GlyphWidth]+1       # if 0.5 above, remove the +1
          h = self.fontGlyph[i][GlyphHeight]+1
          gw = self.fontGlyph[i][GlyphOrigW]
          gh = self.fontGlyph[i][GlyphOrigH]

          GL.glBegin(GL.GL_QUADS)

          # coordinates in the texture
          tx0 = x*dx
          ty0 = (y+h)*dy
          tx1 = (x+w)*dx
          ty1 = y*dy
          # coordinates mapped to the quad
          px0 = px
          py0 = gh-(py+h)
          px1 = px+w
          py1 = gh-py

          # draw the quad
          GL.glTexCoord2f( tx0, ty0);         GL.glVertex(px0, py0)
          GL.glTexCoord2f( tx0, ty1);         GL.glVertex(px0, py1)
          GL.glTexCoord2f( tx1, ty1);         GL.glVertex(px1, py1)
          GL.glTexCoord2f( tx1, ty0);         GL.glVertex(px1, py0)

          GL.glEnd()
          GL.glTranslatef(gw, 0.0, 0.0)
        GL.glEndList()


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# need to use the class below to make everything more generic
GLOptions = {
  'opaque':{
    GL.GL_DEPTH_TEST:True,
    GL.GL_BLEND:False,
    GL.GL_ALPHA_TEST:False,
    GL.GL_CULL_FACE:False,
  },
  'translucent':{
    GL.GL_DEPTH_TEST:True,
    GL.GL_BLEND:True,
    GL.GL_ALPHA_TEST:False,
    GL.GL_CULL_FACE:False,
    'glBlendFunc':(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA),
  },
  'additive':{
    GL.GL_DEPTH_TEST:False,
    GL.GL_BLEND:True,
    GL.GL_ALPHA_TEST:False,
    GL.GL_CULL_FACE:False,
    'glBlendFunc':(GL.GL_SRC_ALPHA, GL.GL_ONE),
  },
}


class CcpnTransform3D(QtGui.QMatrix4x4):
  """
  Extension of QMatrix4x4 with some helpful methods added.
  """

  def __init__(self, *args):
    QtGui.QMatrix4x4.__init__(self, *args)

  def matrix(self, nd=3):
    if nd == 3:
      return np.array(self.copyDataTo()).reshape(4, 4)
    elif nd == 2:
      m = np.array(self.copyDataTo()).reshape(4, 4)
      m[2] = m[3]
      m[:, 2] = m[:, 3]
      return m[:3, :3]
    else:
      raise Exception("Argument 'nd' must be 2 or 3")

  def map(self, obj):
    """
    Extends QMatrix4x4.map() to allow mapping (3, ...) arrays of coordinates
    """
    if isinstance(obj, np.ndarray) and obj.ndim >= 2 and obj.shape[0] in (2, 3):
      return fn.transformCoordinates(self, obj)
    else:
      return QtGui.QMatrix4x4.map(self, obj)

  def inverted(self):
    inv, b = QtGui.QMatrix4x4.inverted(self)
    return CcpnTransform3D(inv), b


class CcpnGLItem():
  _nextId = 0

  def __init__(self, parentItem=None):
    self._id = CcpnGLItem._nextId
    CcpnGLItem._nextId += 1

    self.__parent = None
    self.__view = None
    self.__children = set()
    self.__transform = CcpnTransform3D()
    self.__visible = True
    # self.setParentItem(parentItem)
    # self.setDepthValue(0)
    self.__glOpts = {}

vertex_data = np.array([0.75, 0.75, 0.0,
                        0.75, -0.75, 0.0,
                        -0.75, -0.75, 0.0], dtype=np.float32)

color_data = np.array([1, 0, 0,
                       0, 1, 0,
                       0, 0, 1], dtype=np.float32)


class ShaderProgram(object):
  """ Helper class for using GLSL shader programs
  """

  def __init__(self, vertex, fragment):
    """
    Parameters
    ----------
    vertex : str
        String containing shader source code for the vertex
        shader
    fragment : str
        String containing shader source code for the fragment
        shader
    """
    self.program_id = GL.glCreateProgram()
    vs_id = self.add_shader(vertex, GL.GL_VERTEX_SHADER)
    frag_id = self.add_shader(fragment, GL.GL_FRAGMENT_SHADER)

    GL.glAttachShader(self.program_id, vs_id)
    GL.glAttachShader(self.program_id, frag_id)
    GL.glLinkProgram(self.program_id)

    if GL.glGetProgramiv(self.program_id, GL.GL_LINK_STATUS) != GL.GL_TRUE:
      info = GL.glGetProgramInfoLog(self.program_id)
      GL.glDeleteProgram(self.program_id)
      GL.glDeleteShader(vs_id)
      GL.glDeleteShader(frag_id)
      raise RuntimeError('Error linking program: %s' % (info))

    # detach after successful link
    GL.glDetachShader(self.program_id, vs_id)
    GL.glDetachShader(self.program_id, frag_id)

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

class GLString:
  def __init__(self, text, font, color=(1.0, 1.0, 1.0, 0.0), x=0, y=0,
               width=None, height=None):
    self.text = text
    self.vertices = np.zeros((len(text) * 4, 3), dtype=np.float32)
    self.indices = np.zeros((len(text) * 6,), dtype=np.uint)
    self.colors = np.zeros((len(text) * 4, 4), dtype=np.float32)
    self.texcoords = np.zeros((len(text) * 4, 2), dtype=np.float32)
    self.attrib = np.zeros((len(text) * 4, 1), dtype=np.float32)
    pen = [x, y]
    prev = None

    for i, charcode in enumerate(text):
      glyph = font[charcode]
      kerning = glyph.get_kerning(prev)
      x0 = pen[0] + glyph.offset[0] + kerning
      dx = x0 - int(x0)
      x0 = int(x0)
      y0 = pen[1] + glyph.offset[1]
      x1 = x0 + glyph.size[0]
      y1 = y0 - glyph.size[1]
      u0 = glyph.texcoords[0]
      v0 = glyph.texcoords[1]
      u1 = glyph.texcoords[2]
      v1 = glyph.texcoords[3]

      index = i * 4
      indices = [index, index + 1, index + 2, index, index + 2, index + 3]
      vertices = [[x0, y0, 1], [x0, y1, 1], [x1, y1, 1], [x1, y0, 1]]
      texcoords = [[u0, v0], [u0, v1], [u1, v1], [u1, v0]]
      colors = [color, ] * 4

      self.vertices[i * 4:i * 4 + 4] = vertices
      self.indices[i * 6:i * 6 + 6] = indices
      self.texcoords[i * 4:i * 4 + 4] = texcoords
      self.colors[i * 4:i * 4 + 4] = colors
      self.attrib[i * 4:i * 4 + 4] = dx
      pen[0] = pen[0] + glyph.advance[0] / 64.0 + kerning
      pen[1] = pen[1] + glyph.advance[1] / 64.0
      prev = charcode

    width = pen[0] - glyph.advance[0] / 64.0 + glyph.size[0]


if __name__ == '__main__':

  import sys
  from ccpn.framework.Version import applicationVersion

  qtApp = QtWidgets.QApplication(['CcpnGLWidget_test', ])

  QtCore.QCoreApplication.setApplicationName('CcpnGLWidget_test')
  QtCore.QCoreApplication.setApplicationVersion(applicationVersion)

  myGL = CcpnGLWidget()
  # myGL._loadPNG('~/PycharmProjects/myfont.png')

  # myGL.makefont()

  # popup = UpdateAdmin()
  # popup.show()
  # popup.raise_()

  # sys.exit(qtApp.exec_())
