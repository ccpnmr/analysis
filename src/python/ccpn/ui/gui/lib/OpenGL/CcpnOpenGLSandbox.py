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
  #
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
  #   self._contourList.indices = np.zeros(int(elements*6), dtype=np.uint32)
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
  #       vertices = [x0, y0, self.mathFun(x0, y0),
  #                    x0, y1, self.mathFun(x0, y1),
  #                    x1, y1, self.mathFun(x1, y1),
  #                    x1, y0, self.mathFun(x1, y0)]
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
  #
  # don't need the above bit
  # if self._testSpectrum.renderMode == GLRENDERMODE_DRAW:
  #   GL.glUseProgram(self.globalGL._shaderProgram2.program_id)
  #
  #   # must be called after glUseProgram
  #   # GL.glUniformMatrix4fv(self.uPMatrix, 1, GL.GL_FALSE, self._uPMatrix)
  #   # GL.glUniformMatrix4fv(self.uMVMatrix, 1, GL.GL_FALSE, self._uMVMatrix)
  #
  #   of = 1.0
  #   on = -1.0
  #   oa = 2.0 / (self.axisR - self.axisL)
  #   ob = 2.0 / (self.axisT - self.axisB)
  #   oc = -2.0 / (of - on)
  #   od = -(of + on) / (of - on)
  #   oe = -(self.axisT + self.axisB) / (self.axisT - self.axisB)
  #   og = -(self.axisR + self.axisL) / (self.axisR - self.axisL)
  #   # orthographic
  #   self._uPMatrix[0:16] = [oa, 0.0, 0.0, 0.0,
  #                           0.0, ob, 0.0, 0.0,
  #                           0.0, 0.0, oc, 0.0,
  #                           og, oe, od, 1.0]
  #
  #   # create modelview matrix
  #   self._uMVMatrix[0:16] = [1.0, 0.0, 0.0, 0.0,
  #                            0.0, 1.0, 0.0, 0.0,
  #                            0.0, 0.0, 1.0, 0.0,
  #                            0.0, 0.0, 0.0, 1.0]
  #
  #   self.globalGL._shaderProgram2.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uPMatrix)
  #   self.globalGL._shaderProgram2.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._uMVMatrix)
  #
  #   self.set2DProjectionFlat()
  #   self._testSpectrum.drawIndexArray()
  #   # GL.glUseProgram(0)
  # #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  #
  # self.swapBuffers()
  # GLUT.glutSwapBuffers()

def mathFun(self, aa, bb):
  return math.sin(5.0 * aa) * math.cos(5.0 * bb ** 2)


