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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
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

AXIS_MARGINRIGHT = 35
AXIS_MARGINBOTTOM = 35
AXIS_LINE = 5

GLRENDERMODE_IGNORE = 0
GLRENDERMODE_DRAW = 1
GLRENDERMODE_RESCALE = 2
GLRENDERMODE_REBUILD = 3


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

    # midnight = QTime(0, 0, 0)
    # random.seed(midnight.secsTo(QTime.currentTime()))
    #
    # self.object = 0
    # self.xRot = 0
    # self.yRot = 0
    # self.zRot = 0
    # self.image = QImage()
    # self.bubbles = []
    self.lastPos = QPoint()
    #
    # self.trolltechGreen = QColor.fromCmykF(0.40, 0.0, 1.0, 0.0)
    # self.trolltechPurple = QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)

    # TODO:ED need to explicitly call self.update() to refresh after an update
    # self.animationTimer = QTimer()
    # self.animationTimer.setSingleShot(False)
    # self.animationTimer.timeout.connect(self.animate)
    # self.animationTimer.start(25)

    # self.setAutoFillBackground(False)
    # self.setMinimumSize(100, 50)
    # self.setWindowTitle("Overpainting a Scene")

    self._mouseX = 0
    self._mouseY = 0

    # self.eventFilter = self._eventFilter
    # self.installEventFilter(self)   # ejb
    self.setMouseTracking(True)                 # generate mouse events when button not pressed

    self.base = None
    self.spectrumValues = []

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

  def resizeGL(self, w, h):
    # GL.glViewport(0, 0, w, h)
    # self.set2DProjectionFlat()


    # put stuff in here that will change on a resize
    for li in self.gridList:
      li.renderMode = GLRENDERMODE_REBUILD
    for pp in self._GLPeakLists.values():
      pp.renderMode = GLRENDERMODE_RESCALE

    # self.update()

  def wheelEvent(self, event):
    def between(val, l, r):
      return (l-val)*(r-val) <= 0

    zoomScale = 25.0
    zoomIn = (100.0+zoomScale)/100.0
    zoomOut = 100.0/(100.0+zoomScale)

    numDegrees = event.angleDelta() / 8
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
        self.axisL = mbx + zoomIn * (self.axisL - mbx)
        self.axisR = mbx - zoomIn * (mbx - self.axisR)
      else:
        self.axisL = mbx + zoomOut * (self.axisL - mbx)
        self.axisR = mbx - zoomOut * (mbx - self.axisR)

      mb = (self._mouseY - mw[1]) / (mw[3] - mw[1])
      mby = self.axisB + mb * (self.axisT - self.axisB)

      if numDegrees.y() < 0:
        self.axisB = mby + zoomIn * (self.axisB - mby)
        self.axisT = mby - zoomIn * (mby - self.axisT)
      else:
        self.axisB = mby + zoomOut * (self.axisB - mby)
        self.axisT = mby - zoomOut * (mby - self.axisT)

      # spawn rebuild event for the grid
      for li in self.gridList:
        li.renderMode = GLRENDERMODE_REBUILD

    elif between(self._mouseX, ba[0], ba[2]) and between(self._mouseY, ba[1], ba[3]):
      mb = (self._mouseX - ba[0]) / (ba[2] - ba[0])
      mbx = self.axisL + mb * (self.axisR - self.axisL)

      if numDegrees.y() < 0:
        self.axisL = mbx + zoomIn * (self.axisL - mbx)
        self.axisR = mbx - zoomIn * (mbx - self.axisR)
      else:
        self.axisL = mbx + zoomOut * (self.axisL - mbx)
        self.axisR = mbx - zoomOut * (mbx - self.axisR)

      # spawn rebuild event for the grid
      self.gridList[0].renderMode = GLRENDERMODE_REBUILD
      self.gridList[2].renderMode = GLRENDERMODE_REBUILD

      # ratios have changed so rescale the peaks symbols
      for pp in self._GLPeakLists.values():
        pp.renderMode = GLRENDERMODE_RESCALE

    elif between(self._mouseX, ra[0], ra[2]) and between(self._mouseY, ra[1], ra[3]):
      mb = (self._mouseY - ra[1]) / (ra[3] - ra[1])
      mby = self.axisB + mb * (self.axisT - self.axisB)

      if numDegrees.y() < 0:
        self.axisB = mby + zoomIn * (self.axisB - mby)
        self.axisT = mby - zoomIn * (mby - self.axisT)
      else:
        self.axisB = mby + zoomOut * (self.axisB - mby)
        self.axisT = mby - zoomOut * (mby - self.axisT)

      # spawn rebuild event for the grid
      self.gridList[0].renderMode = GLRENDERMODE_REBUILD
      self.gridList[1].renderMode = GLRENDERMODE_REBUILD

      # ratios have changed so rescale the peaks symbols
      for pp in self._GLPeakLists.values():
        pp.renderMode = GLRENDERMODE_RESCALE

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

    # simple shader for standard plotting of contours
    self._vertexShader1 = """
#version 120

uniform mat4 mvMatrix;
uniform mat4 pMatrix;
varying vec4 FC;

void main()
{
  gl_Position = pMatrix * mvMatrix * gl_Vertex;
  FC = gl_Color;
}
"""

    self._fragmentShader1 = """
#version 120

varying vec4  FC;

void main()
{
  gl_FragColor = FC;
}
"""

    # shader for plotting antialiased text to the screen
    self._vertexShaderTex = """
#version 120

uniform mat4 mvMatrix;
uniform mat4 pMatrix;
varying vec4 FC;
attribute vec2 offset;

void main()
{
  gl_Position = pMatrix * mvMatrix * (gl_Vertex + vec4(offset, 0.0, 0.0));
  gl_TexCoord[0] = gl_MultiTexCoord0;
  FC = gl_Color;
}
"""

    self._fragmentShaderTex = """
#version 120

uniform sampler2D texture;
varying vec4 FC;
vec4         filter;

void main()
{
  // vec4 current = texture2D(texture, uv);
  filter = texture2D(texture, gl_TexCoord[0].xy);
  gl_FragColor = vec4(FC.xyz, filter.w);
}
"""

    # advanced shader for plotting contours
    self._vertexShader2 = """
#version 120

varying vec4  P;
varying vec4  C;
uniform mat4  mvMatrix;
uniform mat4  pMatrix;
uniform vec4  positiveContour;
uniform vec4  negativeContour;
//uniform float gsize = 5.0;      // size of the grid
//uniform float gwidth = 1.0;     // grid lines' width in pixels
//varying float   f = min(abs(fract(P.z * gsize)-0.5), 0.2);

void main()
{
  P = gl_Vertex;
  C = gl_Color;
//  gl_Position = vec4(gl_Vertex.x, gl_Vertex.y, 0.0, 1.0);
//  vec4 glVect = pMatrix * mvMatrix * vec4(P, 1.0);
//  gl_Position = vec4(glVect.x, glVect.y, 0.0, 1.0);
  gl_Position = pMatrix * mvMatrix * vec4(P.xy, 0.0, 1.0);
}
"""

    self._fragmentShader2 = """
#version 120

//  uniform float gsize = 50.0;       // size of the grid
uniform float gwidth = 0.5;       // grid lines' width in pixels
uniform float mi = 0.0;           // mi=max(0.0,gwidth-1.0)
uniform float ma = 1.0;           // ma=max(1.0,gwidth);
varying vec4 P;
varying vec4 C;

void main()
{
//  vec3 f  = abs(fract (P * gsize)-0.5);
//  vec3 df = fwidth(P * gsize);
//  float mi=max(0.0,gwidth-1.0), ma=max(1.0,gwidth);//should be uniforms
//  vec3 g=clamp((f-df*mi)/(df*(ma-mi)),max(0.0,1.0-gwidth),1.0);//max(0.0,1.0-gwidth) should also be sent as uniform
//  float c = g.x * g.y * g.z;
//  gl_FragColor = vec4(c, c, c, 1.0);
//  gl_FragColor = gl_FragColor * gl_Color;

  float   f = min(abs(fract(P.z)-0.5), 0.2);
  float   df = fwidth(P.z);
//  float   mi=max(0.0,gwidth-1.0), ma=max(1.0,gwidth);                 //  should be uniforms
  float   g=clamp((f-df*mi)/(df*(ma-mi)),max(0.0,1.0-gwidth),1.0);      //  max(0.0,1.0-gwidth) should also be sent as uniform
//  float   g=clamp((f-df*mi), 0.0, df*(ma-mi));  //  max(0.0,1.0-gwidth) should also be sent as uniform

//  g = g/(df*(ma-mi));
//  float   cAlpha = 1.0-(g*g);
//  if (cAlpha < 0.25)            //  this actually causes branches in the shader - bad
//    discard;
//  gl_FragColor = vec4(0.8-g, 0.3, 0.4-g, 1.0-(g*g));
  gl_FragColor = vec4(P.w, P.w, P.w, 1.0-(g*g));
}
"""

    self._vertexShader3 = """
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

    self._fragmentShader3 = """
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

    GL = self.context().versionFunctions()
    GL.initializeOpenGLFunctions()
    self._GLVersion = GL.glGetString(GL.GL_VERSION)

    self.gridList = []
    for li in range(3):
      self.gridList.append(GLVertexArray(numLists=1
                                         , renderMode=GLRENDERMODE_REBUILD
                                         , blendMode=True
                                         , drawMode=GL.GL_LINES
                                         , dimension=2
                                         , GLContext=self))

    self._GLPeakLists = {}
    self._GLPeakListLabels = {}

    self.firstFont = CcpnGLFont('/Users/ejb66/Documents/Fonts/myfont.fnt')
    self._buildTextFlag = True

    self._mouseList = GL.glGenLists(1)
    self._buildMouse = True

    self._drawTextList = GL.glGenLists(1)
    self._axisXLabels = GL.glGenLists(1)
    self._axisLabels = GL.glGenLists(1)
    self.peakLabelling = 0

    self._contourList = GLVertexArray(numLists=1
                                      , renderMode=GLRENDERMODE_REBUILD
                                      , blendMode=True
                                      , drawMode=GL.GL_TRIANGLES
                                      , dimension=3
                                      , GLContext=self)

    # self._axisLabels = GLVertexArray(numLists=1
    #                                   , renderMode=GLRENDERMODE_REBUILD
    #                                   , blendMode=True
    #                                   , drawMode=GL.GL_TRIANGLES)

    # TODO:ED only have openGL 2.1 installed, so no point yet
    self._shaderProgram1 = ShaderProgram(vertex=self._vertexShader1
                                        , fragment=self._fragmentShader1
                                        , attributes={'pMatrix':(16, np.float32)
                                                      , 'mvMatrix':(16, np.float32)})
                                                      # , 'useTexture':(1, np.uint)})
    self._shaderProgram2 = ShaderProgram(vertex=self._vertexShader2
                                        , fragment=self._fragmentShader2
                                        , attributes={'pMatrix':(16, np.float32)
                                                      , 'mvMatrix':(16, np.float32)
                                                      , 'positiveContours':(4, np.float32)
                                                      , 'negativeContours':(4, np.float32)})
    self._shaderProgram3 = ShaderProgram(vertex=self._vertexShader3
                                        , fragment=self._fragmentShader3
                                        , attributes={'pMatrix':(16, np.float32)
                                                      , 'mvMatrix':(16, np.float32)})
    self._shaderProgramTex = ShaderProgram(vertex=self._vertexShaderTex
                                        , fragment=self._fragmentShaderTex
                                        , attributes={'pMatrix':(16, np.float32)
                                                      , 'mvMatrix':(16, np.float32)})

    # these are the links to the GL projection.model matrices
    # self.uPMatrix = GL.glGetUniformLocation(self._shaderProgram2.program_id, 'pMatrix')
    # self.uMVMatrix = GL.glGetUniformLocation(self._shaderProgram2.program_id, 'mvMatrix')
    # self.positiveContours = GL.glGetUniformLocation(self._shaderProgram2.program_id, 'positiveContour')
    # self.negativeContours = GL.glGetUniformLocation(self._shaderProgram2.program_id, 'negativeContour')

    self._uPMatrix = np.zeros((16,), dtype=np.float32)
    self._uMVMatrix = np.zeros((16,), dtype=np.float32)
    self._uVMatrix = np.zeros((16,), dtype=np.float32)
    self._aMatrix = np.zeros((16,), dtype=np.float32)
    self._useTexture = np.zeros((1,), dtype=np.int)
    self.worldCoordinate = np.zeros((4,), dtype=np.float32)

    # self._positiveContours = np.zeros((4,), dtype=np.float32)
    # self._negativeContours = np.zeros((4,), dtype=np.float32)

    self._testSpectrum = GLVertexArray(numLists=1
                                       , renderMode=GLRENDERMODE_REBUILD
                                       , blendMode=True
                                       , drawMode=GL.GL_TRIANGLES
                                       , dimension=4
                                       , GLContext=self)

    self.viewports = GLViewports()
    self.viewports.addViewport('mainView', self, (0, 'a'), (AXIS_MARGINBOTTOM, 'a')
                                                , (-AXIS_MARGINRIGHT, 'w'), (0, 'h'))

    self.viewports.addViewport('mainViewFullWidth', self, (0, 'a'), (AXIS_MARGINBOTTOM, 'a')
                                                        , (-AXIS_MARGINRIGHT, 'w'), (0, 'h'))

    self.viewports.addViewport('rightAxis', self, (-(AXIS_MARGINRIGHT+AXIS_LINE), 'w')
                                                  , (AXIS_MARGINBOTTOM, 'a')
                                                  , (AXIS_LINE, 'a'), (0, 'h'))

    self.viewports.addViewport('rightAxisBar', self, (-AXIS_MARGINRIGHT, 'w'), (AXIS_MARGINBOTTOM, 'a')
                                                    , (0, 'w'), (0, 'h'))

    self.viewports.addViewport('bottomAxis', self, (0, 'a'), (AXIS_MARGINBOTTOM, 'a')
                                                  , (-AXIS_MARGINRIGHT, 'w'), (AXIS_LINE, 'a'))

    self.viewports.addViewport('bottomAxisBar', self, (0, 'a'), (0, 'a')
                                                    , (-AXIS_MARGINRIGHT, 'w'), (AXIS_MARGINBOTTOM, 'a'))

    self.viewports.addViewport('fullView', self, (0, 'a'), (0, 'a'), (0, 'w'), (0, 'h'))

    # def set2DProjection                GL.glViewport(0, 35, w - 35, h - 35)
    # def set2DProjectionRightAxis       GL.glViewport(w - 35 - axisLine, 35, axisLine, h - 35)
    # def set2DProjectionRightAxisBar    GL.glViewport(w - AXIS_MARGIN, AXIS_MARGIN, AXIS_MARGIN, h - AXIS_MARGIN)
    # def set2DProjectionBottomAxis      GL.glViewport(0, 35, w - 35, axisLine)
    # def set2DProjectionBottomAxisBar   GL.glViewport(0, 0, w - AXIS_MARGIN, AXIS_MARGIN)
    # def set2DProjectionFlat            GL.glViewport(0, 35, w - 35, h - 35)

    self._testString = GLString(text='The quick brown fox jumped over the lazy dog.', font=self.firstFont, x=63, y=117
                                , color=(0.15, 0.6, 0.25, 1.0), GLContext=self)

  def mousePressEvent(self, ev):
    self.lastPos = ev.pos()

    # self._startCoordinate = [ev.pos().x(), self.height() - ev.pos().y()]

    vect = self.vInv.dot([ev.pos().x(), self.height() - ev.pos().y(), 0.0, 1.0])
    self._startCoordinate = self._aMatrix.reshape((4, 4)).dot(vect)

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

    # print ('INV~~~~~~~')

    # translate mouse to NDC
    vect = self.vInv.dot([self._mouseX, self._mouseY, 0.0, 1.0])

    # translate to axis coordinates
    self.worldCoordinate = self._aMatrix.reshape((4, 4)).dot(vect)

    # self._pointZero = self._aMatrix.reshape((4, 4)).dot(self.vInv.dot([0,0,0,1]))
    # self._pointOne = self._aMatrix.reshape((4, 4)).dot(self.vInv.dot([1,1,0,1]))
    # self.pixelX = self._pointOne[0]-self._pointZero[0]
    # self.pixelY = self._pointOne[1]-self._pointZero[1]

    # print (self._mouseX, self._mouseY, " : ", vect[0:2], self.worldCoordinate)
    # print (self._mouseX, self._mouseY, " : ", np.array([self._mouseX, self._mouseY, 0.0, 0.0], dtype=np.float32).dot(self._invTransform))

    if event.buttons() & Qt.LeftButton:
      # do the complicated keypresses first
      if (self._key == Qt.Key_Control and self._isSHIFT == 'S') or \
          (self._key == Qt.Key_Shift and self._isCTRL) == 'C':
        self._endCoordinate = self.worldCoordinate      #[event.pos().x(), self.height() - event.pos().y()]
        self._selectionMode = 3

      elif self._key == Qt.Key_Shift:
        self._endCoordinate = self.worldCoordinate      #[event.pos().x(), self.height() - event.pos().y()]
        self._selectionMode = 1

      elif self._key == Qt.Key_Control:
        self._endCoordinate = self.worldCoordinate      #[event.pos().x(), self.height() - event.pos().y()]
        self._selectionMode = 2

      else:
        self.axisL -= dx * self.pixelX
        self.axisR -= dx * self.pixelX
        self.axisT += dy * self.pixelY
        self.axisB += dy * self.pixelY

        # spawn rebuild event for the grid
        for li in self.gridList:
          li.renderMode = GLRENDERMODE_REBUILD
        for pp in self._GLPeakLists.values():
          pp.renderMode = GLRENDERMODE_RESCALE

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
    # my signal to update the screen after the spectra have changed
    if bool:
      self.update()

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

  def _rescalePeakListLabels(self, spectrumView):
    drawList = self._GLPeakLists[spectrumView.spectrum.pid]

    x = abs(self.pixelX)
    y = abs(self.pixelY)
    if x <= y:
      r = 0.05
      w = 0.05 * y / x
    else:
      w = 0.05
      r = 0.05 * x / y

    # drawList.clearVertices()
    # drawList.vertices = drawList.attribs
    offsets = np.array([-r, -w, +r, +w, +r, -w, -r, +w], np.float32)
    for pp in range(0, 2*drawList.numVertices, 8):
      drawList.vertices[pp:pp+8] = drawList.attribs[pp:pp+8] + offsets

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

    # drawList.clearVertices()
    # drawList.vertices = drawList.attribs
    offsets = np.array([-r, -w, +r, +w, +r, -w, -r, +w], np.float32)
    for pp in range(0, 2*drawList.numVertices, 8):
      drawList.vertices[pp:pp+8] = drawList.attribs[pp:pp+8] + offsets

      # drawList.vertices = np.append(drawList.vertices, [pp[0] - r, pp[1] - w
      #   , pp[0] + r, pp[1] + w
      #   , pp[0] + r, pp[1] - w
      #   , pp[0] - r, pp[1] + w])
      # drawList.numVertices += 4

      # tempVert.append([pp[0] - r, pp[1] - w])
      # tempVert.append([pp[0] + r, pp[1] + w])
      # tempVert.append([pp[0] + r, pp[1] - w])
      # tempVert.append([pp[0] - r, pp[1] + w])

    # rebuild the scaled vertices
    # drawList[2] = np.array(tempVert, np.float32)

  def _buildPeakLists(self, spectrumView):
    spectrum = spectrumView.spectrum

    if spectrum.pid not in self._GLPeakLists:
      self._GLPeakLists[spectrum.pid] = GLVertexArray(numLists=1, renderMode=GLRENDERMODE_REBUILD
                                                      , blendMode=False, drawMode=GL.GL_LINES
                                                      , dimension=2, GLContext=self)

      # self._GLPeakLists[spectrum.pid] = [GL.glGenLists(1), GLRENDERMODE_REBUILD, np.array([]), np.array([]), 0, None]

    drawList = self._GLPeakLists[spectrum.pid]

    if drawList.renderMode == GLRENDERMODE_REBUILD:
      drawList.renderMode = GLRENDERMODE_DRAW               # back to draw mode

      # GL.glNewList(drawList[0], GL.GL_COMPILE)
      #
      # drawList[2] = None
      # drawList[3] = None
      # drawList[4] = 0
      # drawList[5] = []
      #
      # tempVert = []
      # tempCol = []

      drawList.clearArrays()

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
      index=0
      for pls in spectrum.peakLists:
        for peak in pls.peaks:
          #
          if hasattr(peak, '_isSelected') and peak._isSelected:
            colour = spectrumView.strip.plotWidget.highlightColour
          else:
            colour = pls.symbolColour

          colR = int(colour.strip('# ')[0:2], 16)/255.0
          colG = int(colour.strip('# ')[2:4], 16)/255.0
          colB = int(colour.strip('# ')[4:6], 16)/255.0

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

          drawList.indices = np.append(drawList.indices, [index, index+1, index+2, index+3])
          drawList.vertices = np.append(drawList.vertices, [p0[0]-r, p0[1]-w
                                                            , p0[0]+r, p0[1]+w
                                                            , p0[0]+r, p0[1]-w
                                                            , p0[0]-r, p0[1]+w])
          drawList.colors = np.append(drawList.colors, [colR, colG, colB, 1.0] * 4)
          drawList.attribs = np.append(drawList.attribs, [p0[0], p0[1]
                                                          ,p0[0], p0[1]
                                                          ,p0[0], p0[1]
                                                          ,p0[0], p0[1]])
          index += 4
          drawList.numVertices += 4

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

      #     # TODO:ED don't delete yet, this is the peak label drawing
      #     # glut text failure - need something better
      #     colour = pls.textColour
      #     colR = int(colour.strip('# ')[0:2], 16)/255.0
      #     colG = int(colour.strip('# ')[2:4], 16)/255.0
      #     colB = int(colour.strip('# ')[4:6], 16)/255.0
      #     GL.glColor4f(colR, colG, colB, 1.0)
      #
      #     GL.glPushMatrix()
      #     GL.glTranslated(p0[0]+r, p0[1]-w, 0.0)
      #     GL.glScaled(self.pixelX, self.pixelY, 1.0)
      #
      #     if self.peakLabelling == 0:
      #       text = _getScreenPeakAnnotation(peak, useShortCode=False)
      #     elif self.parentWidget().strip.peakLabelling == 1:
      #       text = _getScreenPeakAnnotation(peak, useShortCode=True)
      #     else:
      #       text = _getPeakAnnotation(peak)  # original 'pid'
      #
      #     GL.glCallLists([ord(c) for c in text])
      #
      #     GL.glPopMatrix()
      #
      # # GL.glEnd()
      # GL.glEndList()

      # drawList[2] = np.array(tempVert, np.float32)
      # drawList[3] = np.array(tempCol, np.float32)

    elif drawList.renderMode == GLRENDERMODE_RESCALE:
      drawList.renderMode = GLRENDERMODE_DRAW               # back to draw mode
      self._rescalePeakList(spectrumView=spectrumView)

  def _buildPeakListLabels(self, spectrumView):
    spectrum = spectrumView.spectrum

    if spectrum.pid not in self._GLPeakListLabels:
      self._GLPeakListLabels[spectrum.pid] = GLVertexArray(numLists=1, renderMode=GLRENDERMODE_REBUILD
                                                      , blendMode=False, drawMode=GL.GL_LINES
                                                      , dimension=2, GLContext=self)

    drawList = self._GLPeakListLabels[spectrum.pid]
    if drawList.renderMode == GLRENDERMODE_REBUILD:
      drawList.renderMode = GLRENDERMODE_DRAW               # back to draw mode

      # drawList[1] = GLRENDERMODE_DRAW               # back to draw mode
      # drawList[2] = None
      # drawList[3] = None
      # drawList[4] = 0
      # drawList[5] = []
      drawList.clearArrays()
      drawList.stringList = []

      # tempVert = []
      # tempCol = []

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

          # need to map world coordinate to screen for drawing text

          colour = pls.textColour
          colR = int(colour.strip('# ')[0:2], 16)/255.0
          colG = int(colour.strip('# ')[2:4], 16)/255.0
          colB = int(colour.strip('# ')[4:6], 16)/255.0
          # GL.glColor4f(colR, colG, colB, 1.0)
          #
          # GL.glPushMatrix()
          # GL.glTranslated(p0[0]+r, p0[1]-w, 0.0)
          # GL.glScaled(self.pixelX, self.pixelY, 1.0)

          if self.peakLabelling == 0:
            text = _getScreenPeakAnnotation(peak, useShortCode=False)
          elif self.parentWidget().strip.peakLabelling == 1:
            text = _getScreenPeakAnnotation(peak, useShortCode=True)
          else:
            text = _getPeakAnnotation(peak)  # original 'pid'

          # TODO:ED change this to a vertex array
          # GL.glCallLists([ord(c) for c in text])
          # for c in text:
          #   ch = ord(c)

          # TODO:ED concatenate all strings into a single list
          # add a new string to the list

          self._screenZero = self._uVMatrix.reshape((4, 4)).dot(self.aInv.dot([p0[0], p0[1], 0, 1]))

          drawList.stringList.append(GLString(text=text
                                      , font=self.firstFont
                                      , x=self._screenZero[0], y=self._screenZero[1]
                                      , color=(colR, colG, colB, 1.0), GLContext=self
                                      , pid=peak.pid))

          # GL.glPopMatrix()
      # GL.glEndList()
      # drawList[2] = np.array(tempVert, np.float32)
      # drawList[3] = np.array(tempCol, np.float32)

    elif drawList.renderMode == GLRENDERMODE_RESCALE:
      drawList.renderMode = GLRENDERMODE_DRAW               # back to draw mode

      # self._rescalePeakListLabels(spectrumView=spectrumView)

  def _drawVertexColor(self, drawList):
    # new bit to use a vertex array to draw the peaks, very fast and easy
    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    GL.glEnableClientState(GL.GL_COLOR_ARRAY)

    GL.glVertexPointer(2, GL.GL_FLOAT, 0, drawList[2])
    GL.glColorPointer(4, GL.GL_FLOAT, 0, drawList[3])
    GL.glDrawArrays(GL.GL_LINES, 0, drawList[4])

    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    GL.glDisableClientState(GL.GL_COLOR_ARRAY)

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

    # GL.glEnable(GL.GL_TEXTURE_2D)
    # GL.glBindTexture(GL.GL_TEXTURE_2D, self.firstFont.textureId)
    # GL.glListBase( self.firstFont.base )
    # GL.glCallList(drawList[0])        # temporarily call the drawing of the text
    # GL.glDisable(GL.GL_TEXTURE_2D)

    GL.glDisable(GL.GL_BLEND)

  def _drawPeakListLabels(self, spectrumView):
    drawList = self._GLPeakListLabels[spectrumView.spectrum.pid]

    for drawString in drawList.stringList:
      drawString.drawTextArray()

    return

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

  # TODO:ED the blending isn't working when the dock is popped out of the mainwindow
  # def paintEvent(self, event):
  #   self.makeCurrent()
  # 
  #   painter = QPainter(self)
  #   painter.setRenderHint(QPainter.Antialiasing)
  #   painter.end()

  def paintGL(self):
    
    def between(val, l, r):
      return (l-val)*(r-val) <= 0

    GL.glPushAttrib(GL.GL_ALL_ATTRIB_BITS)

    GL.glColorMask(GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE)
    GL.glDisable(GL.GL_BLEND)
    # GL.glDisable(GL.GL_ALPHA_TEST)
    GL.glClearColor(0.05, 0.05, 0.05, 1.0)
    GL.glBlendColor(0.0, 0.0, 0.0, 1.0)
    # GL.glClearIndex()
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)  # | GL.GL_DEPTH_BUFFER_BIT)

    GL.glColorMask(GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE, GL.GL_TRUE)
    GL.glDisable(GL.GL_BLEND)

    # getGLvector = (GL.GLfloat * 2)()
    # GL.glGetFloatv(GL.GL_ALIASED_LINE_WIDTH_RANGE, getGLvector)
    # linewidths = [i for i in getGLvector]

    # setup projection matrix based on the axis limits
    # need to move it, doesn't need to be done every frame

    w = self.width()
    h = self.height()

    # self.set2DProjection()

    GL.glUseProgram(self._shaderProgram1.program_id)
    # self.viewports.setViewport('mainView')
    # GL.glViewport(0, 35, w-35, h-35)   # leave a 35 width margin for the axes - bottom/right

    self._shaderProgram1.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, self.axisB,
                                           self.axisT, -1.0, 1.0)

    # TODO:ED check why this is h+35 and not h
    self._shaderProgram1.setViewportMatrix(self._uVMatrix, 0, w-35, 35, h+35, -1.0, 1.0)
    self._shaderProgram1.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uPMatrix)

    # self._useTexture = 0
    # self._shaderProgram1.setGLUniform1i('useTexture', self._useTexture)

    self._uMVMatrix[0:16] = [1.0, 0.0, 0.0, 0.0,
                            0.0, 1.0, 0.0, 0.0,
                            0.0, 0.0, 1.0, 0.0,
                            0.0, 0.0, 0.0, 1.0]     # set to identity matrix
    self._shaderProgram1.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._uMVMatrix)

    # TODO:ED check why this isn't working
    self._shaderProgram1.setViewportMatrix(self._aMatrix, self.axisL, self.axisR, self.axisB,
                                           self.axisT, -1.0, 1.0)

    self.pInv = np.linalg.inv(self._uPMatrix.reshape((4, 4)))     # projection
    self.mvInv = np.linalg.inv(self._uMVMatrix.reshape((4, 4)))   # modelView
    self.vInv = np.linalg.inv(self._uVMatrix.reshape((4, 4)))     # viewport
    self.aInv = np.linalg.inv(self._aMatrix.reshape((4, 4)))      # axis scale

    # calculate the size of the screen pixels in axis coordinates
    self._pointZero = self._aMatrix.reshape((4, 4)).dot(self.vInv.dot([0,0,0,1]))
    self._pointOne = self._aMatrix.reshape((4, 4)).dot(self.vInv.dot([1,1,0,1]))
    self.pixelX = self._pointOne[0]-self._pointZero[0]
    self.pixelY = self._pointOne[1]-self._pointZero[1]

    # set to the mainView and draw the grid
    self.viewports.setViewport('mainView')
    self.axisLabelling, labelsChanged = self._buildAxes(self.gridList[0], axisList=[0,1], scaleGrid=[2,1,0], r=1.0, g=1.0, b=1.0, transparency=500.0)
    self.gridList[0].drawIndexArray()

    # draw the grid marks for the right axis
    self.viewports.setViewport('rightAxis')
    self._buildAxes(self.gridList[1], axisList=[1], scaleGrid=[1,0], r=0.2, g=1.0, b=0.3, transparency=64.0)
    self.gridList[1].drawIndexArray()

    # draw the grid marks for the bottom axis
    self.viewports.setViewport('bottomAxis')
    self._buildAxes(self.gridList[2], axisList=[0], scaleGrid=[1,0], r=0.2, g=1.0, b=0.3, transparency=64.0)
    self.gridList[2].drawIndexArray()

    self.modelViewMatrix = (GL.GLdouble * 16)()
    self.projectionMatrix = (GL.GLdouble * 16)()
    self.viewport = (GL.GLint * 4)()

    # GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX, self.modelViewMatrix)
    # GL.glGetDoublev(GL.GL_PROJECTION_MATRIX, self.projectionMatrix)
    # GL.glGetIntegerv(GL.GL_VIEWPORT, self.viewport)

    # self.worldCoordinate = GLU.gluUnProject(
    #   self._mouseX, self._mouseY, 0,
    #   self.modelViewMatrix,
    #   self.projectionMatrix,
    #   self.viewport,
    # )

    # self.worldCoordinate = [0, 0]   #invTransform.dot([self._mouseX, self._mouseY, 0.0, 0.0])
    # mw = [0, 35, w-36, h-1]
    # if between(self._mouseX, mw[0], mw[2]) and between(self._mouseY, mw[1], mw[3]):
    #   mb = (self._mouseX - mw[0]) / (mw[2] - mw[0])
    #   mbx = self.axisL + mb * (self.axisR - self.axisL)
    #   mb = (self._mouseY - mw[1]) / (mw[3] - mw[1])
    #   mby = self.axisB + mb * (self.axisT - self.axisB)
    #   self.worldCoordinate = [mbx, mby]

    # self.viewport = [i for i in self.viewport]
    # grab coordinates of the transformed viewport
    # self._infiniteLineUL = GLU.gluUnProject(
    #   0.0,
    #   self.viewport[3]+self.viewport[1],
    #   0.0,
    #   self.modelViewMatrix,
    #   self.projectionMatrix,
    #   self.viewport,
    # )
    # self._infiniteLineBR = GLU.gluUnProject(
    #   self.viewport[2]+self.viewport[0],
    #   self.viewport[1],
    #   0.0,
    #   self.modelViewMatrix,
    #   self.projectionMatrix,
    #   self.viewport,
    # )

    # calculate the width of a world pixel on the screen
    # origin = GLU.gluUnProject(
    #   0.0, 0.0, 0.0,
    #   self.modelViewMatrix,
    #   self.projectionMatrix,
    #   self.viewport,
    # )
    # pointOne = GLU.gluUnProject(
    #   1.0, 1.0, 0.0,
    #   self.modelViewMatrix,
    #   self.projectionMatrix,
    #   self.viewport,
    # )
    # self.pixelX = pointOne[0]-origin[0]
    # self.pixelY = pointOne[1]-origin[1]

    # GL.glEnable(GL.GL_LINE_SMOOTH)
    # GL.glHint(GL.GL_LINE_SMOOTH_HINT, GL.GL_NICEST)
    GL.glDisable(GL.GL_BLEND)

    self.viewports.setViewport('mainView')

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
        # dx = self.sign(self._infiniteLineBR[0] - self._infiniteLineUL[0])
        # dy = self.sign(self._infiniteLineUL[1] - self._infiniteLineBR[1])

        dx = self.sign(self.axisR - self.axisL)
        dy = self.sign(self.axisT - self.axisB)

        # get the bounding box of the spectra
        fx0, fx1 = self._spectrumValues[0].maxAliasedFrequency, self._spectrumValues[0].minAliasedFrequency
        fy0, fy1 = self._spectrumValues[1].maxAliasedFrequency, self._spectrumValues[1].minAliasedFrequency
        dxAF = fx0 - fx1
        dyAF = fy0 - fy1
        xScale = dx*dxAF/self._spectrumValues[0].totalPointCount
        yScale = dy*dyAF/self._spectrumValues[1].totalPointCount

        # create modelview matrix for the spectrum to be drawn
        self._uMVMatrix[0:16] = [xScale, 0.0, 0.0, 0.0,
                                 0.0, yScale, 0.0, 0.0,
                                 0.0, 0.0, 1.0, 0.0,
                                 fx0, fy0, 0.0, 1.0]
        self._shaderProgram1.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._uMVMatrix)

        # draw the spectrum - call the existing glCallList
        spectrumView._paintContoursNoClip()

        # if self._testSpectrum.renderMode == GLRENDERMODE_REBUILD:
        #   self._testSpectrum.renderMode = GLRENDERMODE_DRAW
        #
        #   self._makeSpectrumArray(spectrumView, self._testSpectrum)

      except Exception as es:
        raise es

    # reset the modelview matrix
    self._uMVMatrix[0:16] = [1.0, 0.0, 0.0, 0.0,
                             0.0, 1.0, 0.0, 0.0,
                             0.0, 0.0, 1.0, 0.0,
                             0.0, 0.0, 0.0, 1.0]
    self._shaderProgram1.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._uMVMatrix)

    for spectrumView in self.parent.spectrumViews:
      try:
        self._spectrumValues = spectrumView._getValues()
        # dx = self.sign(self._infiniteLineBR[0] - self._infiniteLineUL[0])
        # dy = self.sign(self._infiniteLineUL[1] - self._infiniteLineBR[1])

        # get the bounding box of the spectra
        fx0, fx1 = self._spectrumValues[0].maxAliasedFrequency, self._spectrumValues[0].minAliasedFrequency
        fy0, fy1 = self._spectrumValues[1].maxAliasedFrequency, self._spectrumValues[1].minAliasedFrequency

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
        self._GLPeakLists[spectrumView.spectrum.pid].drawIndexArray()
        # self._drawPeakListVertices(spectrumView)

        # self._buildPeakListLabels(spectrumView)      # should include rescaling
        # self._drawPeakListLabels(spectrumView)

      except Exception as es:
        raise es

    # GL.glUseProgram(0)
    # self.set2DProjection()

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

    # self.set2DProjection()

    # self.viewports.setViewport('mainView')
    # self.axisLabelling, labelsChanged = self._buildAxes(self.gridList[0], axisList=[0,1], scaleGrid=[2,1,0], r=1.0, g=1.0, b=1.0, transparency=500.0)
    # self.gridList[0].drawIndexArray()
    #
    # # self.set2DProjectionRightAxis()
    # self.viewports.setViewport('rightAxis')
    # self._buildAxes(self.gridList[1], axisList=[1], scaleGrid=[1,0], r=0.2, g=1.0, b=0.3, transparency=64.0)
    # self.gridList[1].drawIndexArray()
    #
    # # self.set2DProjectionBottomAxis()
    # self.viewports.setViewport('bottomAxis')
    # self._buildAxes(self.gridList[2], axisList=[0], scaleGrid=[1,0], r=0.2, g=1.0, b=0.3, transparency=64.0)
    # self.gridList[2].drawIndexArray()

    # draw axis lines to right and bottom
    # self.set2DProjectionFlat()
    # h = self.height()
    # w = self.width()
    # GL.glColor4f(0.2, 1.0, 0.3, 1.0)
    # GL.glBegin(GL.GL_LINES)
    # GL.glVertex2d(0, 0)         # not sure why 0 doesn't work
    # GL.glVertex2d(w-36, 0)      # think I'm drawing over it with the next viewport
    # GL.glVertex2d(w-36, 0)
    # GL.glVertex2d(w-36, h-36)
    # GL.glEnd()

    # draw all the peak GLLists here

    # self.set2DProjection()      # set back to the main projection
    # self.viewports.setViewport('mainView')

    if self._drawSelectionBox:
      GL.glEnable(GL.GL_BLEND)
      GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

      # self._dragStart = GLU.gluUnProject(
      #   self._startCoordinate[0], self._startCoordinate[1], 0,
      #   self.modelViewMatrix,
      #   self.projectionMatrix,
      #   self.viewport,
      # )
      # self._dragEnd = GLU.gluUnProject(
      #   self._endCoordinate[0], self._endCoordinate[1], 0,
      #   self.modelViewMatrix,
      #   self.projectionMatrix,
      #   self.viewport,
      # )

      self._uMVMatrix[0:16] = [1.0, 0.0, 0.0, 0.0,
                               0.0, 1.0, 0.0, 0.0,
                               0.0, 0.0, 1.0, 0.0,
                               0.0, 0.0, 0.0, 1.0]
      self._shaderProgram1.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._uMVMatrix)

      self._dragStart = self._startCoordinate
      self._dragEnd = self._endCoordinate

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
    # GL.glVertex2d(self.worldCoordinate[0], self._infiniteLineUL[1])
    # GL.glVertex2d(self.worldCoordinate[0], self._infiniteLineBR[1])
    # GL.glVertex2d(self._infiniteLineUL[0], self.worldCoordinate[1])
    # GL.glVertex2d(self._infiniteLineBR[0], self.worldCoordinate[1])

    GL.glVertex2d(self.worldCoordinate[0], self.axisT)
    GL.glVertex2d(self.worldCoordinate[0], self.axisB)
    GL.glVertex2d(self.axisL, self.worldCoordinate[1])
    GL.glVertex2d(self.axisR, self.worldCoordinate[1])

    GL.glEnd()

    coords = " "+str(self._isSHIFT)+str(self._isCTRL)+str(self._key)+" : "\
              +str(round(self.worldCoordinate[0], 3))\
              +", "+str(round(self.worldCoordinate[1], 3))

    coords = 'F'
    # self.glut_print(self.worldCoordinate[0], self.worldCoordinate[1]
    #                 , GLUT.GLUT_BITMAP_HELVETICA_12
    #                 , coords
    #                 , 1.0, 1.0, 1.0, 1.0)

    # if self._buildTextFlag == GLRENDERMODE_REBUILD:
    #   self._buildTextFlag = GLRENDERMODE_DRAW
    #   GL.glNewList(self._drawTextList, GL.GL_COMPILE)
    #
    #   for ti in range(7):
    #     # GL.glRotate(25.0, 0.0, 0.0, 1.0)      # can rotate if we need to :)
    #
    #     GL.glPushMatrix()
    #     GL.glTranslate(ti*50.0, ti*50, 0.0)
    #     GL.glCallLists([ord(c) for c in 'The Quick\tBrown Fox\n013617@something'])
    #     GL.glPopMatrix()
    #
    #   GL.glEndList()

    # self._useTexture = 1
    # self._shaderProgram1.setGLUniform1i('useTexture', self._useTexture)

    GL.glUseProgram(self._shaderProgramTex.program_id)

    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glBindTexture(GL.GL_TEXTURE_2D, self.firstFont.textureId)

    # GL.glListBase( self.firstFont.base )

    # GL.glPushMatrix()
    # GL.glTranslated(50, 300, 0)
    # # GL.glScalef(-0.5, -3.0, 1.0)        # because the axes are inverted
    # GL.glCallList(self._drawTextList)
    # GL.glPopMatrix()

    # self.set2DProjection()
    # for spectrumView in self.parent.spectrumViews:
    #   self._drawPeakLists(spectrumView)

    # draw the mouse coordinates
    # self.set2DProjectionFlat()

    # TODO:ED now change all the texts to drawList with coordinates as screen(x,y)
    # rescale needs to keep the lists but offset the characters from the first in the list
    # each string can be id'ed by a pid and attrib array keeps the world coordinate of the first character

    # GL.glPushMatrix()
    # GL.glTranslate(self.worldCoordinate[0], self.worldCoordinate[1], 0.0)      # from bottom left of window?
    # GL.glScalef(3.0, 3.0, 1.0)                              # use this for scaling font
    GL.glColor3f(0.9, 0.9, 0.9)
    self._uMVMatrix[0:16] = [self.pixelX*3.0, 0.0, 0.0, 0.0,
                             0.0, self.pixelY*3.0, 0.0, 0.0,
                             0.0, 0.0, 1.0, 0.0,
                             self.worldCoordinate[0]+(25*self.pixelX)
                                  , self.worldCoordinate[1]+(25*self.pixelY), 0.0, 1.0]
    self._shaderProgramTex.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._uMVMatrix)
    GL.glCallLists([ord(c) for c in coords])
    # GL.glPopMatrix()

    # draw axes labelling
    if labelsChanged:
      GL.glNewList(self._axisLabels, GL.GL_COMPILE)

      # put the axis labels into the bottom bar
      self.viewports.setViewport('bottomAxisBar')
      self._shaderProgramTex.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, 0, AXIS_MARGINBOTTOM, -1.0, 1.0)
      self._shaderProgramTex.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uPMatrix)

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

      # put the axis labels into the right bar
      self.viewports.setViewport('rightAxisBar')
      self._shaderProgramTex.setProjectionAxes(self._uPMatrix, 0, AXIS_MARGINRIGHT, self.axisB, self.axisT, -1.0, 1.0)
      self._shaderProgramTex.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uPMatrix)

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

    # # testing text boundaries
    # GL.glDisable(GL.GL_BLEND)

    # draw the testString to the screen
    self.viewports.setViewport('mainView')

    # TODO:ED check that this is the correct dimensions of the window
    self._shaderProgramTex.setProjectionAxes(self._uPMatrix, 0, w-35, 35, h, -1.0, 1.0)
    # self._shaderProgramTex.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, self.axisB, self.axisT, -1.0, 1.0)

    self._shaderProgramTex.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uPMatrix)
    self._uMVMatrix[0:16] = [1.0, 0.0, 0.0, 0.0,
                             0.0, 1.0, 0.0, 0.0,
                             0.0, 0.0, 1.0, 0.0,
                             0.0, 0.0, 0.0, 1.0]
    self._shaderProgramTex.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._uMVMatrix)

    # draw the string
    self._testString.drawTextArray()

    for spectrumView in self.parent.spectrumViews:
      try:
        self._buildPeakListLabels(spectrumView)      # should include rescaling
        self._drawPeakListLabels(spectrumView)

      except Exception as es:
        raise es


    GL.glDisable(GL.GL_BLEND)
    GL.glDisable(GL.GL_TEXTURE_2D)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # new bit
    # fov = math.radians(45.0)
    # f = 1.0 / math.tan(fov / 2.0)
    # zNear = 0.1
    # zFar = 100.0
    # aspect = glutGet(GLUT_WINDOW_WIDTH) / float(glutGet(GLUT_WINDOW_HEIGHT))
    # aspect = w / float(h)
    # perspective
    # pMatrix = np.array([
    #   f / aspect, 0.0, 0.0, 0.0,
    #   0.0, f, 0.0, 0.0,
    #   0.0, 0.0, (zFar + zNear) / (zNear - zFar), -1.0,
    #   0.0, 0.0, 2.0 * zFar * zNear / (zNear - zFar), 0.0], np.float32)

    # GL.glViewport(0, 0, self.width(), self.height())
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
    #
    # # create modelview matrix
    # self._uMVMatrix[0:16] = [1.0, 0.0, 0.0, 0.0,
    #                         0.0, 1.0, 0.0, 0.0,
    #                         0.0, 0.0, 1.0, 0.0,
    #                         0.0, 0.0, 0.0, 1.0]
    #
    # if (self._contourList.renderMode == GLRENDERMODE_REBUILD):
    #   self._contourList.renderMode = GLRENDERMODE_DRAW
    #
    #   # GL.glNewList(self._contourList[0], GL.GL_COMPILE)
    #   #
    #   # # GL.glUniformMatrix4fv(self.uPMatrix, 1, GL.GL_FALSE, pMatrix)
    #   # # GL.glUniformMatrix4fv(self.uMVMatrix, 1, GL.GL_FALSE, mvMatrix)
    #   #
    #   # GL.glEnable(GL.GL_BLEND)
    #   # GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    #   #
    #   # # pastel pink - # df2950
    #   # GL.glColor4f(0.8745, 0.1608, 0.3137, 1.0)
    #   #
    #   # GL.glBegin(GL.GL_TRIANGLES)
    #
    #   step = 0.05
    #   ii=0
    #   elements = (2.0/step)**2
    #   self._contourList.indices = np.zeros(int(elements*6), dtype=np.uint)
    #   self._contourList.vertices = np.zeros(int(elements*12), dtype=np.float32)
    #   self._contourList.colors = np.zeros(int(elements*16), dtype=np.float32)
    #
    #   for x0 in np.arange(-1.0, 1.0, step):
    #     for y0 in np.arange(-1.0, 1.0, step):
    #       x1 = x0+step
    #       y1 = y0+step
    #
    #       index = ii*4
    #       indices = [index, index + 1, index + 2, index, index + 2, index + 3]
    #       vertices = [x0, y0, self.mathFun(x0, y0)
    #                   , x0, y1, self.mathFun(x0, y1)
    #                   , x1, y1, self.mathFun(x1, y1)
    #                   , x1, y0, self.mathFun(x1, y0)]
    #       # texcoords = [[u0, v0], [u0, v1], [u1, v1], [u1, v0]]
    #       colors = [0.8745, 0.1608, 0.3137, 1.0] * 4
    #
    #       self._contourList.indices[ii * 6:ii * 6 + 6] = indices
    #       self._contourList.vertices[ii * 12:ii * 12 + 12] = vertices
    #       self._contourList.colors[ii * 16:ii * 16 + 16] = colors
    #       ii += 1
    #
    #       # self._contourList.indices = np.append(self._contourList.indices, indices)
    #       # self._contourList.vertices = np.append(self._contourList.vertices, vertices)
    #       # self._contourList.colors = np.append(self._contourList.colors, colors)
    #
    #       # GL.glVertex3f(ii,     jj,     self.mathFun(ii,jj))
    #       # GL.glVertex3f(ii+step, jj,     self.mathFun(ii+step, jj))
    #       # GL.glVertex3f(ii+step, jj+step, self.mathFun(ii+step, jj+step))
    #       #
    #       # GL.glVertex3f(ii,     jj,     self.mathFun(ii,jj))
    #       # GL.glVertex3f(ii+step, jj+step, self.mathFun(ii+step, jj+step))
    #       # GL.glVertex3f(ii,     jj+step, self.mathFun(ii, jj+step))
    #   self._contourList.numVertices = index
    #   # self._contourList.bindBuffers()
    #
    #   # GL.glEnd()
    #   # GL.glDisable(GL.GL_BLEND)
    #   # GL.glEndList()

    # don't need the above bit
    if self._testSpectrum.renderMode == GLRENDERMODE_DRAW:
      GL.glUseProgram(self._shaderProgram2.program_id)

      # must be called after glUseProgram
      # GL.glUniformMatrix4fv(self.uPMatrix, 1, GL.GL_FALSE, self._uPMatrix)
      # GL.glUniformMatrix4fv(self.uMVMatrix, 1, GL.GL_FALSE, self._uMVMatrix)

      of = 1.0
      on = -1.0
      oa = 2.0 / (self.axisR - self.axisL)
      ob = 2.0 / (self.axisT - self.axisB)
      oc = -2.0 / (of - on)
      od = -(of + on) / (of - on)
      oe = -(self.axisT + self.axisB) / (self.axisT - self.axisB)
      og = -(self.axisR + self.axisL) / (self.axisR - self.axisL)
      # orthographic
      self._uPMatrix[0:16] = [oa, 0.0, 0.0, 0.0,
                              0.0, ob, 0.0, 0.0,
                              0.0, 0.0, oc, 0.0,
                              og, oe, od, 1.0]

      # create modelview matrix
      self._uMVMatrix[0:16] = [1.0, 0.0, 0.0, 0.0,
                               0.0, 1.0, 0.0, 0.0,
                               0.0, 0.0, 1.0, 0.0,
                               0.0, 0.0, 0.0, 1.0]

      self._shaderProgram2.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uPMatrix)
      self._shaderProgram2.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._uMVMatrix)

      self.set2DProjectionFlat()
      self._testSpectrum.drawIndexArray()
      GL.glUseProgram(0)
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    GL.glPopAttrib(GL.GL_ALL_ATTRIB_BITS)

  def _makeSpectrumArray(self, spectrumView, drawList):
    drawList.renderMode = GLRENDERMODE_DRAW
    spectrum = spectrumView.spectrum
    drawList.clearArrays()

    for position, dataArray in spectrumView._getPlaneData():
      ma = np.amax(dataArray)
      mi = np.amin(dataArray)
      # min(  abs(  fract(P.z * gsize) - 0.5), 0.2);
      # newData = np.clip(np.absolute(np.remainder((50.0*dataArray/ma), 1.0)-0.5), 0.2, 50.0)
      dataScale = 15.0
      newData = dataScale*dataArray/ma
      npX = dataArray.shape[0]
      npY = dataArray.shape[1]

      indexing = (npX-1)*(npY-1)
      elements = npX*npY
      drawList.indices = np.zeros(int(indexing * 6), dtype=np.uint)
      drawList.vertices = np.zeros(int(elements * 4), dtype=np.float32)
      drawList.colors = np.zeros(int(elements * 4), dtype=np.float32)

      ii = 0
      for y0 in range(0, npY):
        for x0 in range(0, npX):
          vertex = [y0, x0, newData[x0,y0], 0.5+newData[x0,y0]/(2.0*dataScale)]
          color = [0.5, 0.5, 0.5, 1.0]
          drawList.vertices[ii * 4:ii * 4 + 4] = vertex
          drawList.colors[ii * 4:ii * 4 + 4] = color
          ii += 1
      drawList.numVertices = elements

      ii = 0
      for y0 in range(0, npY-1):
        for x0 in range(0, npX-1):
          corner = x0+(y0*npX)
          indices = [corner, corner+1, corner+npX
                    , corner+1, corner+npX, corner+1+npX]
          drawList.indices[ii * 6:ii * 6 + 6] = indices
          ii += 1
      break

  # lrLengthx = (int)((xmax - xmin) / xres + 1); // how
  # many
  # points in the
  # x
  # direction
  # lrLengthz = (int)((zmax - zmin) / zres + 1); // how
  # many
  # points
  # needed in z
  # direction
  # points = new
  # Vector3[lrLengthx * lrLengthz];
  # uvs = new
  # Vector2[lrLengthx * lrLengthz];
  # triangles = new
  # int[points.Length * 6];
  # // generate
  # triangles
  # int
  # index = 0;
  # for (int z = 0; z < lrLengthz-1;z++){
  # for (int x = 0; x < lrLengthx-1;x++){
  # uvs[x+z * lrLengthx] = new Vector2(x / (lrLengthx-1.0f), z / (lrLengthz-1.0f));
  # triangles[index+2]   = x+z * lrLengthx;
  # triangles[index+1] = x+1+z * lrLengthx;
  # triangles[index+0] = x+z * lrLengthx+lrLengthx;
  #
  # triangles[index+3] = x+z * lrLengthx+lrLengthx;
  # triangles[index+4] = x+1+z * lrLengthx+lrLengthx;
  # triangles[index+5] = x+1+z * lrLengthx;
  # index += 6;
  # }
  # }
  #
  #
  def mathFun(self, aa, bb):
    return math.sin(5.0*aa)*math.cos(5.0*bb**2)
  # def resizeGL(self, width, height):
  #   self.setupViewport(width, height)
  #   self.update()

  # def showEvent(self, event):
  #   self.createBubbles(20 - len(self.bubbles))

  def sizeHint(self):
    return QSize(400, 400)

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
    GL.glViewport(0, 0, w-AXIS_MARGINRIGHT, AXIS_MARGINBOTTOM)   # leave a 35 width margin for the axes - bottom/right
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

    # ul = np.array([self._infiniteLineUL[0], self._infiniteLineUL[1]])
    # br = np.array([self._infiniteLineBR[0], self._infiniteLineBR[1]])

    ul = np.array([self.axisL, self.axisT])
    br = np.array([self.axisR, self.axisB])

    labelling = {'0': [], '1': []}
    labelsChanged = False

    if gridGLList.renderMode == GLRENDERMODE_REBUILD:

      # GL.glNewList(gridGLList[0], GL.GL_COMPILE)
      gridGLList.renderMode = GLRENDERMODE_DRAW
      labelsChanged = True

      # gridGLList[2] = None
      # gridGLList[3] = None
      # gridGLList[4] = 0

      gridGLList.clearArrays()

      tempList = []
      tempCol = []

      index = 0
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
          # GL.glColor4f(r, g, b, c/transparency)               # make high order lines more transparent
          # GL.glBegin(GL.GL_LINES)
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
            # GL.glVertex2f(p1[0], p1[1])
            # GL.glVertex2f(p2[0], p2[1])

            if i == 1:            # should be largest scale grid
              if p1[0] == p2[0]:
                labelling[str(ax)].append((i, ax, p1[0], d[0]))
              else:
                labelling[str(ax)].append((i, ax, p1[1], d[1]))

            # append the new points to the end of nparray
            gridGLList.indices = np.append(gridGLList.indices, [index, index+1])
            gridGLList.vertices = np.append(gridGLList.vertices, [p1[0], p1[1], p2[0], p2[1]])
            gridGLList.colors = np.append(gridGLList.colors, [r, g, b, c/transparency, r, g, b, c/transparency])
            gridGLList.numVertices += 2
            index += 2

      #     GL.glEnd()
      #
      # GL.glEndList()
      # gridGLList[2] = np.array(tempList, np.float32)
      # gridGLList[3] = np.array(tempCol, np.float32)

    # old drawing of the grid
    # GL.glEnable(GL.GL_BLEND)
    # GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    # GL.glLineWidth(1.0)
    #
    # GL.glCallList(gridGLList[0])
    #
    # GL.glDisable(GL.GL_BLEND)


    # new bit to use a vertex array to draw the peaks, very fast and easy
    # GL.glEnable(GL.GL_BLEND)
    # GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    # GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    # GL.glEnableClientState(GL.GL_COLOR_ARRAY)
    #
    # GL.glVertexPointer(2, GL.GL_FLOAT, 0, gridGLList[2])
    # GL.glColorPointer(4, GL.GL_FLOAT, 0, gridGLList[3])
    # GL.glDrawArrays(GL.GL_LINES, 0, gridGLList[4])
    #
    # GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    # GL.glDisableClientState(GL.GL_COLOR_ARRAY)
    # GL.glDisable(GL.GL_BLEND)

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
GlyphTX0 = 'tx0'
GlyphTY0 = 'ty0'
GlyphTX1 = 'tx1'
GlyphTY1 = 'ty1'
GlyphPX0 = 'px0'
GlyphPY0 = 'py0'
GlyphPX1 = 'px1'
GlyphPY1 = 'py1'


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
    self.width = 0
    self.height = 0

    row = 2
    exitDims = False

    # texture sizes
    dx = 1.0 / float(self.fontPNG.shape[1])
    dy = 1.0 / float(self.fontPNG.shape[0])
    hdx = dx / 2.0
    hdy = dy / 2.0

    while exitDims is False and row < len(self.fontInfo):
      line = self.fontInfo[row]
      # print (line)
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

              # calculate the coordinated within the texture
              x = a0+0.5           # self.fontGlyph[chrNum][GlyphXpos])   # try +0.5 for centre of texel
              y = b0+0.5           # self.fontGlyph[chrNum][GlyphYpos])
              px = e0           # self.fontGlyph[chrNum][GlyphXoffset]
              py = f0           # self.fontGlyph[chrNum][GlyphYoffset]
              w = c0-1           # self.fontGlyph[chrNum][GlyphWidth]+1       # if 0.5 above, remove the +1
              h = d0-1           # self.fontGlyph[chrNum][GlyphHeight]+1
              gw = g0           # self.fontGlyph[chrNum][GlyphOrigW]
              gh = h0           # self.fontGlyph[chrNum][GlyphOrigH]

              # coordinates in the texture
              self.fontGlyph[chrNum][GlyphTX0] = x*dx
              self.fontGlyph[chrNum][GlyphTY0] = (y+h)*dy
              self.fontGlyph[chrNum][GlyphTX1] = (x+w)*dx
              self.fontGlyph[chrNum][GlyphTY1] = y*dy

              # coordinates mapped to the quad
              self.fontGlyph[chrNum][GlyphPX0] = px
              self.fontGlyph[chrNum][GlyphPY0] = gh-(py+h+1)
              self.fontGlyph[chrNum][GlyphPX1] = px+w+1
              self.fontGlyph[chrNum][GlyphPY1] = gh-py

              # draw the quad
              # GL.glTexCoord2f( tx0, ty0);         GL.glVertex(px0, py0)
              # GL.glTexCoord2f( tx0, ty1);         GL.glVertex(px0, py1)
              # GL.glTexCoord2f( tx1, ty1);         GL.glVertex(px1, py1)
              # GL.glTexCoord2f( tx1, ty0);         GL.glVertex(px1, py0)

              if chrNum == 65:
                # use 'A' for the referencing the tab size
                self.width = gw
                self.height = gh

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
        # print(line)

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

    # the following 2 lines generate a multitexture mipmap
    GL.glTexParameteri( GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR )
    GL.glGenerateMipmap( GL.GL_TEXTURE_2D )
    GL.glDisable(GL.GL_TEXTURE_2D)

    # create a list of GLdisplayLists to handle each character - deprecated, changing to VBOs
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

  def get_kerning(self, fromChar, prevChar):
    if self.fontGlyph[ord(fromChar)]:
      if prevChar and ord(prevChar) in self.fontGlyph[ord(fromChar)][GlyphKerns]:
        return self.fontGlyph[ord(fromChar)][GlyphKerns][ord(prevChar)]

    return 0


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

    self._parent = None
    self._view = None
    self._children = set()
    self._transform = CcpnTransform3D()
    self._visible = True
    # self.setParentItem(parentItem)
    # self.setDepthValue(0)
    self._glOpts = {}

vertex_data = np.array([0.75, 0.75, 0.0,
                        0.75, -0.75, 0.0,
                        -0.75, -0.75, 0.0], dtype=np.float32)

color_data = np.array([1, 0, 0,
                       0, 1, 0,
                       0, 0, 1], dtype=np.float32)

class GLViewports(object):
  # Class to handle the different viewports in the display
  def __init__(self):
    # define a new empty list
    self._viewports = {}

  def addViewport(self, name, parent, left, bottom, rightOffset, topOffset):
    # add a new viewport
    # parent points to the containing widget
    # left, bottom - coordinates of bottom-left corner
    # rightOffset   - offset from the right border
    # topOffset     - offset from the top border
    self._viewports[name] = (parent, left, bottom, rightOffset, topOffset)

    # e.g., GL.glViewport(0, 35, w-35, h-35)   # leave a 35 width margin for the axes - bottom/right
    #                      0, 35, -35, 0

  def setViewport(self, name):
    # change to the named viewport
    def setVal(offsetType, w, h):
      if offsetType[1] in 'alb':
        return offsetType[0]
      elif offsetType[1] == 'w':
        return w+offsetType[0]
      elif offsetType[1] == 'h':
        return h+offsetType[0]

    if name in self._viewports:
      thisView = self._viewports[name]
      w=thisView[0].width()
      h=thisView[0].height()
      l = setVal(thisView[1], w, h)
      b = setVal(thisView[2], w, h)
      wi = setVal(thisView[3], w, h)
      he = setVal(thisView[4], w, h)

      GL.glViewport(l, b, wi, he)
                    # , w-thisView[3]-thisView[1], h-thisView[4]-thisView[2])
    else:
      raise RuntimeError('Error: viewport %s does not exist' % name)

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

  def setGLUniform1i(self, uniformLocation=None, count=1, value=None):
    if uniformLocation in self.uniformLocations:
      GL.glUniform1i(self.uniformLocations[uniformLocation]
                      , count, value)
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


class GLVertexArray():
  def __init__(self, numLists=1, renderMode=GLRENDERMODE_IGNORE
               , blendMode=False, drawMode=GL.GL_LINES, dimension=3, GLContext=None):
    self.initialise(numLists=numLists, renderMode=renderMode
                    , blendMode=blendMode, drawMode=drawMode, dimension=dimension, GLContext=GLContext)

  def initialise(self, numLists=1, renderMode=GLRENDERMODE_IGNORE
                , blendMode=False, drawMode=GL.GL_LINES, dimension=3
                , GLContext=None):
    self.renderMode = renderMode
    self.vertices = np.array([], dtype=np.float32)    #np.zeros((len(text)*4,3), dtype=np.float32)
    self.indices = np.array([], dtype=np.uint)        #np.zeros((len(text)*6, ), dtype=np.uint)
    self.colors = np.array([], dtype=np.float32)      #np.zeros((len(text)*4,4), dtype=np.float32)
    self.texcoords= np.array([], dtype=np.float32)    #np.zeros((len(text)*4,2), dtype=np.float32)
    self.attribs = np.array([], dtype=np.float32)     #np.zeros((len(text)*4,1), dtype=np.float32)
    self.numVertices = 0
    self.GLLists = GL.glGenLists(numLists)
    self.numLists = numLists
    self.blendMode = blendMode
    self.drawMode = drawMode
    self.dimension = int(dimension)
    self._GLContext = GLContext

  def _close(self):
    GL.glDeleteLists(self.GLLists, self.numLists)

  def clearArrays(self):
    self.vertices = np.array([], dtype=np.float32)
    self.indices = np.array([], dtype=np.uint)
    self.colors = np.array([], dtype=np.float32)
    self.texcoords= np.array([], dtype=np.float32)
    self.attribs = np.array([], dtype=np.float32)
    self.numVertices = 0

  def clearVertices(self):
    self.vertices = np.array([], dtype=np.float32)
    self.numVertices = 0

  def drawIndexArray(self):
    self._GLContext.makeCurrent()

    if self.blendMode:
      GL.glEnable(GL.GL_BLEND)
      GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    GL.glEnableClientState(GL.GL_COLOR_ARRAY)
    # GL.glEnableClientState(GL.GL_TEXTURE_2D_ARRAY)
    GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, self.vertices)
    GL.glColorPointer(4, GL.GL_FLOAT, 0, self.colors)
    # GL.glTexCoordPointer(2, gl.GL_FLOAT, 0, self.texcoords)

    # this is for passing extra attributes in
    # GL.glEnableVertexAttribArray(1)
    # GL.glVertexAttribPointer(1, 1, GL.GL_FLOAT, GL.GL_FALSE, 0, self.attribs)

    GL.glDrawElements(self.drawMode, len(self.indices), GL.GL_UNSIGNED_INT, self.indices)

    # GL.glDisableVertexAttribArray(1)
    # GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    GL.glDisableClientState(GL.GL_COLOR_ARRAY)

    if self.blendMode:
      GL.glDisable(GL.GL_BLEND)

    # self._GLContext.doneCurrent()

  def drawVertexColor(self):
    if self.blendMode:
      GL.glEnable(GL.GL_BLEND)
      GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    GL.glEnableClientState(GL.GL_COLOR_ARRAY)

    GL.glVertexPointer(self.dimension, GL.GL_FLOAT, 0, self.vertices)
    GL.glColorPointer(4, GL.GL_FLOAT, 0, self.colors)
    GL.glDrawArrays(self.drawMode, 0, self.numVertices)

    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    GL.glDisableClientState(GL.GL_COLOR_ARRAY)

    if self.blendMode:
      GL.glDisable(GL.GL_BLEND)

  def drawTextArray(self):
    self._GLContext.makeCurrent()

    if self.blendMode:
      GL.glEnable(GL.GL_BLEND)
      GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

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

    # GL.glDisableVertexAttribArray(1)
    GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    GL.glDisableClientState(GL.GL_COLOR_ARRAY)
    GL.glDisableVertexAttribArray(1)

    if self.blendMode:
      GL.glDisable(GL.GL_BLEND)

  # def bindBuffers(self):
  #   return
  #   # self._vertexBuffer = GL.glGenBuffers(1)
  #   # GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vertexBuffer)
  #   # GL.glBufferData(GL.GL_ARRAY_BUFFER, len(self.vertices), self.vertices, GL.GL_STATIC_DRAW)
  #   # GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
  #   #
  #   # self._colorBuffer = GL.glGenBuffers(1)
  #   # GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._colorBuffer)
  #   # GL.glBufferData(GL.GL_ARRAY_BUFFER, len(self.colors), self.colors, GL.GL_STATIC_DRAW)
  #   # GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
  #
  #   self._indexBuffer = GL.glGenBuffers(1)
  #   GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self._indexBuffer)
  #   GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, len(self.indices), self.indices, GL.GL_STATIC_DRAW)
  #   GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)


class GLString(GLVertexArray):
  def __init__(self, text=None, font=None, pid=None, color=(1.0, 1.0, 1.0, 1.0), x=0, y=0,
               width=None, height=None, GLContext=None):
    super(GLString, self).__init__(renderMode=GLRENDERMODE_DRAW, blendMode=False
                                   , GLContext=GLContext, drawMode=GL.GL_TRIANGLES
                                   , dimension=2)

    self.text = text
    self.font = font
    self.pid = pid
    self.vertices = np.zeros((len(text) * 4, 2), dtype=np.float32)
    self.indices = np.zeros((len(text) * 6,), dtype=np.uint)
    self.colors = np.zeros((len(text) * 4, 4), dtype=np.float32)
    self.texcoords = np.zeros((len(text) * 4, 2), dtype=np.float32)
    self.attribs = np.zeros((len(text) * 4, 2), dtype=np.float32)
    self.indexOffset = 0
    pen = [0, 0]              # [x, y]
    prev = None

    for i, charCode in enumerate(text):
      c = ord(charCode)
      glyph = font.fontGlyph[c]

      if glyph or c == 10 or c == 9:    # newline and tab

        if (c == 10):                                 # newline
          pen[0] = 0
          pen[1] = pen[1] + font.height

        elif (c == 9):                                # tab
          pen[0] = pen[0] + 4 * font.width

        elif (c >= 32):

          # kerning = 0
          # if prev and glyph[GlyphKerns]:
          #
          # kerning = glyph._kerning(prev)
          kerning = font.get_kerning(charCode, prev)

          x0 = pen[0] + glyph[GlyphPX0] + kerning     # pen[0] + glyph.offset[0] + kerning
          y0 = pen[1] + glyph[GlyphPY0]               # pen[1] + glyph.offset[1]
          # x1 = x0 + glyph[GlyphPX1]                 # x0 + glyph.size[0]
          # y1 = y0 + glyph[GlyphPY1]                 # y0 - glyph.size[1]
          x1 = pen[0] + glyph[GlyphPX1] + kerning     # x0 + glyph.size[0]
          y1 = pen[1] + glyph[GlyphPY1]               # y0 - glyph.size[1]
          u0 = glyph[GlyphTX0]          # glyph.texcoords[0]
          v0 = glyph[GlyphTY0]          # glyph.texcoords[1]
          u1 = glyph[GlyphTX1]          # glyph.texcoords[2]
          v1 = glyph[GlyphTY1]          # glyph.texcoords[3]

          index = i * 4
          indices = [index, index + 1, index + 2, index, index + 2, index + 3]
          vertices = [[x0, y0], [x0, y1], [x1, y1], [x1, y0]]
          texcoords = [[u0, v0], [u0, v1], [u1, v1], [u1, v0]]
          colors = [color, ] * 4
          attribs = [[x, y], [x, y], [x, y], [x, y]]

          self.vertices[i * 4:i * 4 + 4] = vertices
          self.indices[i * 6:i * 6 + 6] = indices
          self.texcoords[i * 4:i * 4 + 4] = texcoords
          self.colors[i * 4:i * 4 + 4] = colors
          self.attribs[i * 4:i * 4 + 4] = attribs
          pen[0] = pen[0] + glyph[GlyphOrigW] + kerning
          # pen[1] = pen[1] + glyph[GlyphHeight]
          prev = charCode

    pass
    # total width of text - probably don't need
    # width = pen[0] - glyph.advance[0] / 64.0 + glyph.size[0]


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
