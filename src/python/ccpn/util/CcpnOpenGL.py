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

from PyQt5 import QtCore, QtGui, QtOpenGL, QtWidgets
from PyQt5.QtCore import (QPoint, QPointF, QRect, QRectF, QSize, Qt, QTime,
        QTimer)
from PyQt5.QtGui import (QBrush, QColor, QFontMetrics, QImage, QPainter,
        QRadialGradient, QSurfaceFormat)
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from ccpn.util.Logging import getLogger
import numpy as np
from pyqtgraph import functions as fn

try:
    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL hellogl",
            "PyOpenGL must be installed to run this example.")
    sys.exit(1)


class CcpnOpenGLWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, parent=None):
      super(QtWidgets.QOpenGLWidget, self).__init__(parent)
      self.trolltechPurple = QtGui.QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)

    def minimumSizeHint(self):
      return QtCore.QSize(100, 300)

    def sizeHint(self):
      return QtCore.QSize(400, 400)

    def initializeGL(self):
      # self.qglClearColor(self.trolltechPurple.dark())
      GL.glClearColor(*self.trolltechPurple.getRgb())

    def paintGL(self):
      GL.glMatrixMode(GL.GL_MODELVIEW)
      GL.glLoadIdentity()
      GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
      GL.glColor3f(1,0,0)
      GL.glRectf(-1,-1,1,0)
      GL.glColor3f(0,1,0)
      GL.glRectf(-1,0,1,1)
      GL.glBegin(GL.GL_TRIANGLES)
      GL.glVertex2f(3.0, 3.0)
      GL.glVertex2f(5.0, 3.0)
      GL.glVertex2f(5.0, 5.0)
      GL.glVertex2f(6.0, 4.0)
      GL.glVertex2f(7.0, 4.0)
      GL.glVertex2f(7.0, 7.0)
      GL.glEnd()
      GL.glFinish()

    def resizeGL(self, w, h):
      GL.glViewport(0, 0, w, h)


class Bubble(object):
  def __init__(self, position, radius, velocity):
    self.position = position
    self.vel = velocity
    self.radius = radius

    self.innerColor = self.randomColor()
    self.outerColor = self.randomColor()
    self.updateBrush()

  def updateBrush(self):
    gradient = QRadialGradient(QPointF(self.radius, self.radius),
                               self.radius, QPointF(self.radius * 0.5, self.radius * 0.5))

    gradient.setColorAt(0, QColor(255, 255, 255, 255))
    gradient.setColorAt(0.25, self.innerColor)
    gradient.setColorAt(1, self.outerColor)
    self.brush = QBrush(gradient)

  def drawBubble(self, painter):
    painter.save()
    painter.translate(self.position.x() - self.radius,
                      self.position.y() - self.radius)
    painter.setBrush(self.brush)
    painter.drawEllipse(0, 0, int(2 * self.radius), int(2 * self.radius))
    painter.restore()

  def randomColor(self):
    red = random.randrange(205, 256)
    green = random.randrange(205, 256)
    blue = random.randrange(205, 256)
    alpha = random.randrange(91, 192)

    return QColor(red, green, blue, alpha)

  def move(self, bbox):
    self.position += self.vel
    leftOverflow = self.position.x() - self.radius - bbox.left()
    rightOverflow = self.position.x() + self.radius - bbox.right()
    topOverflow = self.position.y() - self.radius - bbox.top()
    bottomOverflow = self.position.y() + self.radius - bbox.bottom()

    if leftOverflow < 0.0:
      self.position.setX(self.position.x() - 2 * leftOverflow)
      self.vel.setX(-self.vel.x())
    elif rightOverflow > 0.0:
      self.position.setX(self.position.x() - 2 * rightOverflow)
      self.vel.setX(-self.vel.x())

    if topOverflow < 0.0:
      self.position.setY(self.position.y() - 2 * topOverflow)
      self.vel.setY(-self.vel.y())
    elif bottomOverflow > 0.0:
      self.position.setY(self.position.y() - 2 * bottomOverflow)
      self.vel.setY(-self.vel.y())

  def rect(self):
    return QRectF(self.position.x() - self.radius,
                  self.position.y() - self.radius, 2 * self.radius,
                  2 * self.radius)


class GLWidget(QOpenGLWidget):
  def __init__(self, parent=None):
    super(GLWidget, self).__init__(parent)

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

    self.animationTimer = QTimer()
    self.animationTimer.setSingleShot(False)
    self.animationTimer.timeout.connect(self.animate)
    self.animationTimer.start(25)

    self.setAutoFillBackground(False)
    self.setMinimumSize(200, 200)
    self.setWindowTitle("Overpainting a Scene")

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
    GL = self.context().versionFunctions()
    GL.initializeOpenGLFunctions()

    self.object = self.makeObject()

  def mousePressEvent(self, event):
    self.lastPos = event.pos()

  def mouseMoveEvent(self, event):
    dx = event.x() - self.lastPos.x()
    dy = event.y() - self.lastPos.y()

    if event.buttons() & Qt.LeftButton:
      self.setXRotation(self.xRot + 8 * dy)
      self.setYRotation(self.yRot + 8 * dx)
    elif event.buttons() & Qt.RightButton:
      self.setXRotation(self.xRot + 8 * dy)
      self.setZRotation(self.zRot + 8 * dx)

    self.lastPos = event.pos()

  def paintEvent_WithPainter(self, event):
    self.makeCurrent()

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPushMatrix()

    self.set3DProjection()

    self.setClearColor(self.trolltechPurple.darker())
    GL.glShadeModel(GL.GL_SMOOTH)
    GL.glEnable(GL.GL_DEPTH_TEST)
    # GL.glEnable(GL.GL_CULL_FACE)
    GL.glEnable(GL.GL_LIGHTING)
    GL.glEnable(GL.GL_LIGHT0)
    GL.glEnable(GL.GL_MULTISAMPLE)
    GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION,
                      (0.5, 5.0, 7.0, 1.0))

    self.setupViewport(self.width(), self.height())

    GL.glClear(
      GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    GL.glLoadIdentity()
    GL.glTranslated(0.0, 0.0, -10.0)
    GL.glRotated(self.xRot / 16.0, 1.0, 0.0, 0.0)
    GL.glRotated(self.yRot / 16.0, 0.0, 1.0, 0.0)
    GL.glRotated(self.zRot / 16.0, 0.0, 0.0, 1.0)
    GL.glCallList(self.object)

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glPopMatrix()

    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)

    for bubble in self.bubbles:
      if bubble.rect().intersects(QRectF(event.rect())):
        bubble.drawBubble(painter)

    self.drawInstructions(painter)
    painter.end()

  @QtCore.pyqtSlot(bool)
  def paintGLsignal(self, bool):
    if bool:
      self.paintGL()

  def paintGL(self):
    self.makeCurrent()

    GL.glPushAttrib(GL.GL_ALL_ATTRIB_BITS)

    GL.glClearColor(0.1, 0.1, 0.1, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    self.set2DProjection()

    for spectrumView in self.parent.spectrumViews:
      try:
        # could put a signal on buildContours
        if spectrumView.buildContours:
          spectrumView._buildContours(None)  # need to trigger these changes now
          spectrumView.buildContours = False  # set to false, as we have rebuilt
          # set to True and update() will rebuild the contours
          # can be done with a call to self.rebuildContours()
        spectrumView._paintContours(None, skip=True)
      except:
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
    self.generatePicture()

    GL.glPopAttrib()
    GLUT.glutSwapBuffers()

  def resizeGL(self, width, height):
    self.setupViewport(width, height)
    self.update()

  def showEvent(self, event):
    self.createBubbles(20 - len(self.bubbles))

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

  def createBubbles(self, number):
    for i in range(number):
      position = QPointF(self.width() * (0.1 + 0.8 * random.random()),
                         self.height() * (0.1 + 0.8 * random.random()))
      radius = min(self.width(), self.height()) * (0.0125 + 0.0875 * random.random())
      velocity = QPointF(self.width() * 0.0125 * (-0.5 + random.random()),
                         self.height() * 0.0125 * (-0.5 + random.random()))

      self.bubbles.append(Bubble(position, radius, velocity))

  def animate(self):
    for bubble in self.bubbles:
      bubble.move(self.rect())

    self.update()

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
    GL.glViewport(0, 50, w-50, h)

    GLU.gluOrtho2D(-10, 50, -10, 0)
    GL.glScalef(1, -1, 1);

    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    # GL.glTranslatef(0.1, 0.1, 0.1)


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

  def generatePicture(self):
    # self.picture = QtGui.QPicture()
    # p = QtGui.QPainter()
    # p.begin(self.picture)

    # dt = fn.invertQTransform(self.viewTransform())
    # vr = self.getViewWidget().rect()
    # unit = self.pixelWidth(), self.pixelHeight()
    # dim = [vr.width(), vr.height()]
    # lvr = self.boundingRect()
    # ul = np.array([lvr.left(), lvr.top()])
    # br = np.array([lvr.right(), lvr.bottom()])

    # dt = fn.invertQTransform(self.viewTransform())
    # vr = self.getViewWidget().rect()
    # unit = self.pixelWidth(), self.pixelHeight()
    dim = [self.width(), self.height()]
    # lvr = self.boundingRect()
    ul = np.array([0, self.height()])
    br = np.array([self.width(), 0])

    # texts = []


    GL.glColor3f(128, 128, 128)
    GL.glBegin(GL.GL_LINES)

    if ul[1] > br[1]:
      x = ul[1]
      ul[1] = br[1]
      br[1] = x
    for i in [1,0]:   ## Draw three different scales of grid
      dist = br-ul
      nlTarget = 10.**i
      d = 10. ** np.floor(np.log10(abs(dist/nlTarget))+0.5)
      ul1 = np.floor(ul / d) * d
      br1 = np.ceil(br / d) * d
      dist = br1-ul1
      nl = (dist / d) + 0.5

      for ax in range(0,2):  ## Draw grid for both axes
        ppl = np.array( dim[ax] / nl[ax] )                      # ejb
        c = np.clip(3.*(ppl-3), 0., 30.)
        # if self.parent.gridColour == '#f7ffff':
          # linePen = QtGui.QPen(QtGui.QColor(247, 255, 255, c))

        # GL.glColor3f(247, 255, 255)
        # else:
          # linePen = QtGui.QPen(QtGui.QColor(8, 0, 0, c))
          # GL.glColor3f(8, 0, 0)

        bx = (ax+1) % 2
        for x in range(0, int(nl[ax])):
          # linePen.setCosmetic(False)
          # if ax == 0:
          #     # linePen.setWidthF(self.pixelWidth())
          # #     #print "ax 0 height", self.pixelHeight()
          #
          #   GL.glLineWidth(1)
          # else:
          #     # linePen.setWidthF(self.pixelHeight())
          #   GL.glLineWidth(2)
          #     #print "ax 1 width", self.pixelWidth()
          # p.setPen(linePen)
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

    GL.glEnd()

    # tr = self.deviceTransform()
    # p.setWorldTransform(fn.invertQTransform(tr))
    # for t in texts:
    #     x = tr.map(t[0]) + Point(0.5, 0.5)
    #     p.drawText(x, t[1])
    # p.end()
