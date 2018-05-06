"""
Code for exporting OpenGL stripDisplay to a pdf file.
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

import sys
from PyQt5 import QtWidgets
from reportlab.platypus import SimpleDocTemplate, Paragraph, Flowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import A4
from contextlib import contextmanager
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import SPECTRUM_STACKEDMATRIX, SPECTRUM_MATRIX
from collections import OrderedDict
import io
import numpy as np

try:
  from OpenGL import GL, GLU, GLUT
except ImportError:
  app = QtWidgets.QApplication(sys.argv)
  QtWidgets.QMessageBox.critical(None, "OpenGL hellogl",
          "PyOpenGL must be installed to run this example.")
  sys.exit(1)
from reportlab.lib import colors
from reportlab.graphics import renderSVG, renderPS
from reportlab.graphics.shapes import Drawing, Rect, String, PolyLine, Line, Group, Path
from reportlab.graphics.shapes import definePath
from reportlab.graphics.renderSVG import draw, renderScaledDrawing, SVGCanvas
from reportlab.lib.units import mm
from ccpn.util.Report import Report

PLOTLEFT = 'plotLeft'
PLOTBOTTOM = 'plotBottom'
PLOTWIDTH = 'plotWidth'
PLOTHEIGHT = 'plotHeight'


class CcpnOpenGLExporter():
  """
  Class container for exporting OpenGL stripDisplay to a file or object
  """
  def __init__(self, parent, strip, filename, params):
    """
    Initialise the exporter
    :param fileName - not required:
    :param params - parameter dict from the exporter dialog:
    """
    self.parent = parent
    self.strip = strip
    self.project = self.strip.project
    self.filename = filename
    self.params = params
    self._report = Report(self, self.project, filename)

    # build all the sections of the pdf

    self._buildAll()
    self.addDrawingToStory()

    # this generates the buffer to write to the file
    self._report.buildDocument()

  def _buildAll(self):
    # add a drawing and build it up
    dpi = 72                        # drawing object is hard-coded to this
    pageWidth = A4[0]
    pageHeight = A4[1]

    # keep aspect ratio of the original screen
    self.margin = 2.0 * cm

    self.main = True
    self.rAxis = self.parent._drawRightAxis
    self.bAxis = self.parent._drawBottomAxis

    if not self.rAxis and not self.bAxis:
      # no axes visible
      self.mainH = self.parent.h
      self.mainW = self.parent.w
      self.mainL = 0
      self.mainB = 0

    elif self.rAxis and not self.bAxis:
      # right axis visible
      self.rAxisW = self.parent.AXIS_MARGINRIGHT
      self.rAxisH = self.parent.h
      self.rAxisL = self.parent.w - self.parent.AXIS_MARGINRIGHT
      self.rAxisB = 0
      self.mainW = self.parent.w - self.parent.AXIS_MARGINRIGHT
      self.mainH = self.parent.h
      self.mainL = 0
      self.mainB = 0

    elif not self.rAxis and self.bAxis:
      # bottom axis visible
      self.bAxisW = self.parent.w
      self.bAxisH = self.parent.AXIS_MARGINBOTTOM
      self.bAxisL = 0
      self.bAxisB = 0
      self.mainW = self.parent.w
      self.mainH = self.parent.h - self.parent.AXIS_MARGINBOTTOM
      self.mainL = 0
      self.mainB = self.parent.AXIS_MARGINBOTTOM

    else:
      # both axes visible
      self.rAxisW = self.parent.AXIS_MARGINRIGHT
      self.rAxisH = self.parent.h - self.parent.AXIS_MARGINBOTTOM
      self.rAxisL = self.parent.w - self.parent.AXIS_MARGINRIGHT
      self.rAxisB = self.parent.AXIS_MARGINBOTTOM
      self.bAxisW = self.parent.w - self.parent.AXIS_MARGINRIGHT
      self.bAxisH = self.parent.AXIS_MARGINBOTTOM
      self.bAxisL = 0
      self.bAxisB = 0
      self.mainW = self.parent.w - self.parent.AXIS_MARGINRIGHT
      self.mainH = self.parent.h - self.parent.AXIS_MARGINBOTTOM
      self.mainL = 0
      self.mainB = self.parent.AXIS_MARGINBOTTOM

    # strip axis ratio
    ratio = self.parent.h / self.parent.w

    # translate to size of drawing Flowable
    self.pixWidth = self._report.doc.width
    self.pixHeight = self.pixWidth * ratio
    if self.pixHeight > (self._report.doc.height - 2*cm):

      # TODO:ED check what else is stealing the height
      self.pixHeight = self._report.doc.height - (2*cm)
      self.pixWidth = self.pixHeight / ratio

    # pixWidth/self.pixHeight are now the dimensions in points for the Flowable
    self.displayScale = self.pixHeight / self.parent.h

    # don't think these are needed
    pixBottom = pageHeight - self.pixHeight - self.margin
    pixLeft = self.margin

    # create an object that can be added to a report
    self._mainPlot = Drawing(self.pixWidth, self.pixHeight)
    # self._rAxisPlot = Drawing(self.displayScale*self.rAxisW, self.displayScale*self.rAxisH) \
    #                     if self.rAxis else None
    # self._bAxisPlot = Drawing(self.displayScale*self.bAxisW, self.displayScale*self.bAxisH) \
    #                     if self.bAxis else None


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # grid lines

    colourGroups = OrderedDict()
    self.appendIndexLineGroup(indArray=self.parent.gridList[0],
                              colourGroups=colourGroups,
                              plotDim={PLOTLEFT: self.displayScale * self.mainL,
                                       PLOTBOTTOM: self.displayScale * self.mainB,
                                       PLOTWIDTH: self.displayScale * self.mainW,
                                       PLOTHEIGHT: self.displayScale * self.mainH},
                              name='grid')
    self.appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='grid')

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # spectrumView contours

    colourGroups = OrderedDict()
    for spectrumView in self.strip.orderedSpectrumViews():

      if spectrumView.isDeleted:
        continue

      if spectrumView.isVisible():

        if spectrumView.spectrum.dimensionCount > 1:
          if spectrumView in self.parent._spectrumSettings.keys():
            # self.globalGL._shaderProgram1.setGLUniformMatrix4fv('mvMatrix',
            #                                            1, GL.GL_FALSE,
            #                                            self._spectrumSettings[spectrumView][SPECTRUM_MATRIX])

            mat = np.transpose(self.parent._spectrumSettings[spectrumView][SPECTRUM_MATRIX].reshape((4, 4)))
            # mat = np.transpose(self.parent._spectrumSettings[spectrumView][SPECTRUM_MATRIX].reshape((4, 4)))

            thisSpec = self.parent._contourList[spectrumView]
            # colour = colors.Color(*thisSpec.colors[0:3], alpha=float(thisSpec.colors[3]))

            # drawVertexColor
            # gr = Group()
            for ii in range(0, len(thisSpec.indices), 2):
              ii0 = int(thisSpec.indices[ii])
              ii1 = int(thisSpec.indices[ii + 1])

              vectStart = [thisSpec.vertices[ii0*2], thisSpec.vertices[ii0*2 + 1], 0.0, 1.0]
              vectStart = mat.dot(vectStart)
              vectEnd = [thisSpec.vertices[ii1*2], thisSpec.vertices[ii1*2 + 1], 0.0, 1.0]
              vectEnd = mat.dot(vectEnd)
              newLine = [vectStart[0], vectStart[1], vectEnd[0], vectEnd[1]]

              colour = colors.Color(*thisSpec.colors[ii0*4:ii0 * 4+3], alpha=thisSpec.colors[ii0 * 4+3])
              colourPath = 'spectrumViewContours%s%s%s%s%s' % (spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)
              if colourPath not in colourGroups:
                cc = colourGroups[colourPath] = {}
                cc['lines'] = []
                cc['strokeWidth'] = 0.5
                cc['strokeColor'] = colour
                cc['strokeLineCap'] = 1

              # if self.parent.lineVisible(newLine, x=0, y=0, width=self.pixWidth, height=self.pixHeight):
              if self.parent.lineVisible(newLine,
                                         x=self.displayScale * self.mainL,
                                         y=self.displayScale * self.mainB,
                                         width=self.displayScale * self.mainW,
                                         height=self.displayScale * self.mainH):
                colourGroups[colourPath]['lines'].append(newLine)

        else:

          # assume that the vertexArray is a GL_LINE_STRIP
          if spectrumView in self.parent._contourList.keys():
            if self.parent._stackingValue:
              mat = np.transpose(self.parent._spectrumSettings[spectrumView][SPECTRUM_STACKEDMATRIX].reshape((4, 4)))
            else:
              mat = None

            thisSpec = self.parent._contourList[spectrumView]
            # colour = colors.Color(*thisSpec.colors[0:3], alpha=float(thisSpec.colors[3]))

            # drawVertexColor
            # gr = Group()
            for vv in range(0, len(thisSpec.vertices)-2, 2):

              if mat is not None:

                vectStart = [thisSpec.vertices[vv], thisSpec.vertices[vv + 1], 0.0, 1.0]
                vectStart = mat.dot(vectStart)
                vectEnd = [thisSpec.vertices[vv + 2], thisSpec.vertices[vv + 3], 0.0, 1.0]
                vectEnd = mat.dot(vectEnd)
                newLine = [vectStart[0], vectStart[1], vectEnd[0], vectEnd[1]]
              else:
                newLine = list(thisSpec.vertices[vv:vv+4])

              colour = colors.Color(*thisSpec.colors[vv*2:vv*2 + 3], alpha=float(thisSpec.colors[vv*2 + 3]))
              colourPath = 'spectrumView%s%s%s%s%s' % (spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)
              if colourPath not in colourGroups:
                cc = colourGroups[colourPath] = {}
                cc['lines'] = []
                cc['strokeWidth'] = 0.5
                cc['strokeColor'] = colour
                cc['strokeLineCap'] = 1

              # if self.parent.lineVisible(newLine, x=0, y=0, width=self.pixWidth, height=self.pixHeight):
              if self.parent.lineVisible(newLine,
                                         x=self.displayScale * self.mainL,
                                         y=self.displayScale * self.mainB,
                                         width=self.displayScale * self.mainW,
                                         height=self.displayScale * self.mainH):
                colourGroups[colourPath]['lines'].append(newLine)

          else:
            pass

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # spectrumView peaklists

    self.appendIndexLineGroupFill(indArray=self.parent._GLPeakLists,
                                  colourGroups=colourGroups,
                                  plotDim={PLOTLEFT: self.displayScale * self.mainL,
                                           PLOTBOTTOM: self.displayScale * self.mainB,
                                           PLOTWIDTH: self.displayScale * self.mainW,
                                           PLOTHEIGHT: self.displayScale * self.mainH},
                                  name='PeakLists',
                                  fillMode=None)


    # for spectrumView in self.strip.orderedSpectrumViews():
    #
    #   for peakListView in spectrumView.peakListViews:
    #     if spectrumView.isVisible() and peakListView.isVisible():
    #
    #       if peakListView in self.parent._GLPeakLists.keys():
    #
    #         thisSpec = self.parent._GLPeakLists[peakListView]
    #
    #         mode = thisSpec.fillMode
    #         if not mode:
    #           self.appendIndexLineGroup(indArray=thisSpec,
    #                                     colourGroups=colourGroups,
    #                                     plotDim={PLOTLEFT: self.displayScale * self.mainL,
    #                                              PLOTBOTTOM: self.displayScale * self.mainB,
    #                                              PLOTWIDTH: self.displayScale * self.mainW,
    #                                              PLOTHEIGHT: self.displayScale * self.mainH},
    #                                     name='spectrumViewPeakList%s' % spectrumView.pid)
    #
    #         else:
    #           if thisSpec.drawMode == GL.GL_TRIANGLES:
    #             indexLen = 3
    #           elif thisSpec.drawMode == GL.GL_QUADS:
    #             indexLen = 4
    #           else:
    #             indexLen = 2
    #
    #           for ii in range(0, len(thisSpec.indices), indexLen):
    #             ii0 = [int(ind) for ind in thisSpec.indices[ii:ii+indexLen]]
    #
    #             # vectStart = [thisSpec.vertices[ii0*2], thisSpec.vertices[ii0*2 + 1], 0.0, 1.0]
    #             # vectStart = mat.dot(vectStart)
    #             # vectEnd = [thisSpec.vertices[ii1*2], thisSpec.vertices[ii1*2 + 1], 0.0, 1.0]
    #             # vectEnd = mat.dot(vectEnd)
    #             # newLine = [vectStart[0], vectStart[1], vectEnd[0], vectEnd[1]]
    #             # newLine =
    #             newLine = []
    #             for vv in ii0:
    #               newLine.extend([thisSpec.vertices[vv * 2], thisSpec.vertices[vv * 2 + 1]])
    #             # newLine = [thisSpec.vertices[ii0 * 2], thisSpec.vertices[ii0 * 2 + 1],
    #             #            thisSpec.vertices[ii1 * 2], thisSpec.vertices[ii1 * 2 + 1]]
    #
    #             colour = colors.Color(*thisSpec.colors[ii0[0] * 4:ii0[0] * 4 + 3], alpha=thisSpec.colors[ii0[0] * 4 + 3])
    #             colourPath = 'spectrumViewPeakLists%s%s%s%s%s' % (
    #             spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)
    #             if colourPath not in colourGroups:
    #               cc = colourGroups[colourPath] = {}
    #               cc['lines'] = []
    #               cc['fillColor'] = colour
    #               cc['stroke'] = None
    #               cc['strokeColor'] = None
    #
    #             # if self.parent.lineVisible(newLine, x=0, y=0, width=self.pixWidth, height=self.pixHeight):
    #             if self.parent.lineVisible(newLine,
    #                                        x=self.displayScale * self.mainL,
    #                                        y=self.displayScale * self.mainB,
    #                                        width=self.displayScale * self.mainW,
    #                                        height=self.displayScale * self.mainH):
    #               colourGroups[colourPath]['lines'].append(newLine)

    self.appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='spectra')

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # marks

    colourGroups = OrderedDict()
    self.appendIndexLineGroup(indArray=self.parent._marksList,
                              colourGroups=colourGroups,
                              plotDim={PLOTLEFT: self.displayScale * self.mainL,
                                       PLOTBOTTOM: self.displayScale * self.mainB,
                                       PLOTWIDTH: self.displayScale * self.mainW,
                                       PLOTHEIGHT: self.displayScale * self.mainH},
                              name='marks')
    self.appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='marks')

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # integrals

    colourGroups = OrderedDict()
    self.appendIndexLineGroupFill(indArray=self.parent._GLIntegralLists,
                              colourGroups=colourGroups,
                              plotDim={PLOTLEFT: self.displayScale * self.mainL,
                                       PLOTBOTTOM: self.displayScale * self.mainB,
                                       PLOTWIDTH: self.displayScale * self.mainW,
                                       PLOTHEIGHT: self.displayScale * self.mainH},
                              name='IntegralListsLine',
                              fillMode=None)
    self.appendIndexLineGroupFill(indArray=self.parent._GLIntegralLists,
                              colourGroups=colourGroups,
                              plotDim={PLOTLEFT: self.displayScale * self.mainL,
                                       PLOTBOTTOM: self.displayScale * self.mainB,
                                       PLOTWIDTH: self.displayScale * self.mainW,
                                       PLOTHEIGHT: self.displayScale * self.mainH},
                              name='IntegralListsFill',
                              fillMode=GL.GL_FILL)
    self.appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='integralLists')

    # add an axis mask
    backCol = colors.Color(self.parent.background[0] * 255,
                           self.parent.background[1] * 255,
                           self.parent.background[2] * 255,
                           alpha = self.parent.background[3])
    gr = Group()
    if self.rAxis:
      gr.add(Rect(self.displayScale * self.rAxisL,
                  0.0,
                  self.displayScale * self.rAxisW,
                  self.pixHeight,
                  fillColor=backCol,
                  strokeColor=backCol,
                  fill=True))
    if self.bAxis:
      gr.add(Rect(0.0,
                  0.0,
                  self.pixWidth,
                  self.displayScale * self.bAxisH,
                  fillColor=backCol,
                  strokeColor=backCol,
                  fill=True))
    if self.rAxis or self.bAxis:
      self._mainPlot.add(gr)

  def report(self):
    """
    Return the current report for this Gl object
    This is the vector image for the current strip containing the GL widget,
    and can be added to a report.
    :return reportlab.platypus.Flowable:
    """
    scale = self.displayScale
    return Clipped_Flowable(width=self.pixWidth, height=self.pixHeight,
                            mainPlot=self._mainPlot,
                            mainDim={ PLOTLEFT: 0,                  #scale*self.mainL,
                                      PLOTBOTTOM: 0,                #scale*self.mainB,
                                      PLOTWIDTH: self.pixWidth,     #scale*self.mainW,
                                      PLOTHEIGHT: self.pixHeight    #scale*self.mainH
                                      }
                            )

  def addDrawingToStory(self):
    """
    add the current drawing the story of a document
    """
    self._report.story.append(self.report())

  def writeSVGFile(self):
    """
    Output an SVG file for the GL widget
    """
    renderSVG.drawToFile(self._mainPlot, self.filename, showBoundary=False)

  def writePDFFile(self):
    """
    Output a PDF file for the GL widget
    """
    self._report.writeDocument()

  def appendVertexLineGroup(self, indArray, colourGroups, plotDim, name, mat=None):
    for vv in range(0, len(indArray.vertices) - 2, 2):

      if mat is not None:

        vectStart = [indArray.vertices[vv], indArray.vertices[vv + 1], 0.0, 1.0]
        vectStart = mat.dot(vectStart)
        vectEnd = [indArray.vertices[vv + 2], indArray.vertices[vv + 3], 0.0, 1.0]
        vectEnd = mat.dot(vectEnd)
        newLine = [vectStart[0], vectStart[1], vectEnd[0], vectEnd[1]]
      else:
        newLine = list(indArray.vertices[vv:vv + 4])

      colour = colors.Color(*indArray.colors[vv * 2:vv * 2 + 3], alpha=float(indArray.colors[vv * 2 + 3]))
      colourPath = 'spectrumView%s%s%s%s%s' % (name, colour.red, colour.green, colour.blue, colour.alpha)
      if colourPath not in colourGroups:
        cc = colourGroups[colourPath] = {}
        cc['lines'] = []
        cc['strokeWidth'] = 0.5
        cc['strokeColor'] = colour
        cc['strokeLineCap'] = 1

      # if self.parent.lineVisible(newLine, x=0, y=0, width=self.pixWidth, height=self.pixHeight):
      if self.parent.lineVisible(newLine,
                                 x=plotDim[PLOTLEFT],
                                 y=plotDim[PLOTBOTTOM],
                                 width=plotDim[PLOTWIDTH],
                                 height=plotDim[PLOTHEIGHT]):
        colourGroups[colourPath]['lines'].append(newLine)

  def appendIndexLineGroup(self, indArray, colourGroups, plotDim, name, fillMode=None):
    if indArray.drawMode == GL.GL_TRIANGLES:
      indexLen = 3
    elif indArray.drawMode == GL.GL_QUADS:
      indexLen = 4
    else:
      indexLen = 2

    for ii in range(0, len(indArray.indices), indexLen):
      ii0 = [int(ind) for ind in indArray.indices[ii:ii + indexLen]]

      newLine = []
      for vv in ii0:
        newLine.extend([indArray.vertices[vv * 2], indArray.vertices[vv * 2 + 1]])

      colour = colors.Color(*indArray.colors[ii0[0] * 4:ii0[0] * 4 + 3], alpha=indArray.colors[ii0[0] * 4 + 3])
      colourPath = 'spectrumView%s%s%s%s%s' % (name,
                                               colour.red, colour.green, colour.blue, colour.alpha)
      if colourPath not in colourGroups:
        cc = colourGroups[colourPath] = {}
        if (fillMode or indArray.fillMode or GL.GL_LINE) == GL.GL_LINE:
          cc['lines'] = []
          cc['strokeWidth'] = 0.5
          cc['strokeColor'] = colour
          cc['strokeLineCap'] = 1
        else:
          # assume that it is GL.GL_FILL
          cc['lines'] = []
          cc['fillColor'] = colour
          cc['stroke'] = None
          cc['strokeColor'] = None

      if self.parent.lineVisible(newLine,
                                 x=plotDim[PLOTLEFT],
                                 y=plotDim[PLOTBOTTOM],
                                 width=plotDim[PLOTWIDTH],
                                 height=plotDim[PLOTHEIGHT]):
        colourGroups[colourPath]['lines'].append(newLine)

    # for ii in range(0, len(indArray.indices), 2):
    #   ii0 = int(indArray.indices[ii])
    #   ii1 = int(indArray.indices[ii+1])
    #
    #   newLine = [indArray.vertices[ii0*2],
    #              indArray.vertices[ii0 * 2+1],
    #              indArray.vertices[ii1 * 2],
    #              indArray.vertices[ii1 * 2+1]]
    #
    #   colour = colors.Color(*indArray.colors[ii0*4:ii0 * 4+3], alpha=indArray.colors[ii0 * 4+3])
    #   colourPath = '%s:%s%s%s%s' % (name, colour.red, colour.green, colour.blue, colour.alpha)
    #   if colourPath not in colourGroups:
    #     cc = colourGroups[colourPath] = {}
    #     cc['lines'] = []
    #     cc['strokeWidth'] = 0.5
    #     cc['strokeColor'] = colour
    #     cc['strokeLineCap'] = 1
    #
    #   # if self.parent.lineVisible(newLine, x=0, y=0, width=self.pixWidth, height=self.pixHeight):
    #   if self.parent.lineVisible(newLine,
    #                              x=plotDim[PLOTLEFT],
    #                              y=plotDim[PLOTBOTTOM],
    #                              width=plotDim[PLOTWIDTH],
    #                              height=plotDim[PLOTHEIGHT]):
    #     colourGroups[colourPath]['lines'].append(newLine)

  def appendIndexLineGroupFill(self, indArray, colourGroups, plotDim, name, fillMode=None):
    for spectrumView in self.strip.orderedSpectrumViews():

      for peakListView in spectrumView.peakListViews:
        if spectrumView.isVisible() and peakListView.isVisible():

          if peakListView in indArray.keys():

            thisSpec = indArray[peakListView]

            # mode = fillMode or thisSpec.fillMode
            # if not mode:

            self.appendIndexLineGroup(indArray=thisSpec,
                                      colourGroups=colourGroups,
                                      plotDim=plotDim,
                                      name='spectrumView%s%s' % (name, spectrumView.pid),
                                      fillMode=fillMode)

            # else:
            #   if thisSpec.drawMode == GL.GL_TRIANGLES:
            #     indexLen = 3
            #   elif thisSpec.drawMode == GL.GL_QUADS:
            #     indexLen = 4
            #   else:
            #     indexLen = 2
            #
            #   for ii in range(0, len(thisSpec.indices), indexLen):
            #     ii0 = [int(ind) for ind in thisSpec.indices[ii:ii+indexLen]]
            #
            #     newLine = []
            #     for vv in ii0:
            #       newLine.extend([thisSpec.vertices[vv * 2], thisSpec.vertices[vv * 2 + 1]])
            #
            #     colour = colors.Color(*thisSpec.colors[ii0[0] * 4:ii0[0] * 4 + 3], alpha=thisSpec.colors[ii0[0] * 4 + 3])
            #     colourPath = 'spectrumView%s%s%s%s%s%s' % (name,
            #                   spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)
            #     if colourPath not in colourGroups:
            #       cc = colourGroups[colourPath] = {}
            #       if mode == GL.GL_LINE:
            #         cc['lines'] = []
            #         cc['strokeWidth'] = 0.5
            #         cc['strokeColor'] = colour
            #         cc['strokeLineCap'] = 1
            #       else:
            #         cc['lines'] = []
            #         cc['fillColor'] = colour
            #         cc['stroke'] = None
            #         cc['strokeColor'] = None
            #
            #     if self.parent.lineVisible(newLine,
            #                                x=plotDim[PLOTLEFT],
            #                                y=plotDim[PLOTBOTTOM],
            #                                width=plotDim[PLOTWIDTH],
            #                                height=plotDim[PLOTHEIGHT]):
            #       colourGroups[colourPath]['lines'].append(newLine)


  def appendGroup(self, drawing:Drawing=None, colourGroups:dict=None, name:str=None):
    """
    Append a group of polylines to the current drawing object
    :param drawing - drawing to append groups to:
    :param colourGroups - OrderedDict of polylines:
    :param name - name for the group:
    """
    gr = Group()
    for colourItem in colourGroups.values():
      # pl = PolyLine(ll['lines'], strokeWidth=ll['strokeWidth'], strokeColor=ll['strokeColor'], strokeLineCap=ll['strokeLineCap'])

      wanted_keys = ['strokeWidth',
                     'strokeColor',
                     'strokeLineCap',
                     'fillColor',
                     'fill',
                     'fillMode',
                     'stroke']
      newColour = dict((k, colourItem[k]) for k in wanted_keys if k in colourItem)

      pl = Path(**newColour)    #  strokeWidth=colourItem['strokeWidth'], strokeColor=colourItem['strokeColor'], strokeLineCap=colourItem['strokeLineCap'])
      for ll in colourItem['lines']:
        if len(ll) == 4:
          pl.moveTo(ll[0], ll[1])
          pl.lineTo(ll[2], ll[3])
        else:
          pl.moveTo(ll[0], ll[1])
          for vv in range(2, len(ll), 2):
            pl.lineTo(ll[vv], ll[vv+1])
          pl.closePath()
      gr.add(pl)
    drawing.add(gr, name=name)

class Clipped_Flowable(Flowable):
  def __init__(self, width=0.0, height=0.0, 
               mainPlot=None, mainDim=None):
    Flowable.__init__(self)
    self.mainPlot = mainPlot
    self.mainDim = mainDim
    self.width = width
    self.height = height
    
  def draw(self):
    if self.mainPlot:
      self.canv.saveState()
  
      # make a clippath for the mainPlot
      pl = self.canv.beginPath()
      pl.moveTo(self.mainDim[PLOTLEFT], self.mainDim[PLOTBOTTOM])
      pl.lineTo(self.mainDim[PLOTLEFT], self.mainDim[PLOTHEIGHT]+self.mainDim[PLOTBOTTOM])
      pl.lineTo(self.mainDim[PLOTLEFT]+self.mainDim[PLOTWIDTH], self.mainDim[PLOTHEIGHT]+self.mainDim[PLOTBOTTOM])
      pl.lineTo(self.mainDim[PLOTLEFT]+self.mainDim[PLOTWIDTH], self.mainDim[PLOTBOTTOM])
      pl.close()
      self.canv.clipPath(pl, fill=0, stroke=0)
  
      # draw the drawing into the canvas
      self.mainPlot.drawOn(self.canv, self.mainDim[PLOTLEFT], self.mainDim[PLOTBOTTOM])
    
    # restore preclipping state
    self.canv.restoreState()
    # draw the axes


if __name__ == '__main__':
  buf = io.BytesIO()

  # Setup the document with paper size and margins
  doc = SimpleDocTemplate(
    buf,
    rightMargin=2 * cm,
    leftMargin=2 * cm,
    topMargin=2 * cm,
    bottomMargin=2 * cm,
    pagesize=A4,
  )

  # Styling paragraphs
  styles = getSampleStyleSheet()

  # Write things on the document
  paragraphs = []
  paragraphs.append(
    Paragraph('This is a paragraph testing CCPN pdf generation', styles['Normal']))
  paragraphs.append(
    Paragraph('This is another paragraph', styles['Normal']))

  from reportlab.lib import colors
  from reportlab.graphics.shapes import Drawing, Rect, String, PolyLine, Group
  from reportlab.lib.units import mm
  from reportlab.pdfgen import canvas


  dpi = 72
  mmwidth = 150
  mmheight = 150
  pixWidth = int(mmwidth * mm)
  pixHeight = int(mmheight * mm)

  # the width doesn't mean anything, but the height defines how much space is added to the story
  # co-ordinates are origin bottom-left
  d = Drawing(pixWidth, pixHeight, )

  d.add(Rect(0.0, 0.0, pixWidth, pixHeight, fillColor=colors.yellow, stroke=0, fill=0))
  d.add(String(150.0, 100.0, 'Hello World', fontSize=18, fillColor=colors.red))
  d.add(String(180.0, 86.0, 'Special characters \
                            \xc2\xa2\xc2\xa9\xc2\xae\xc2\xa3\xce\xb1\xce\xb2',
               fillColor=colors.red))

  pl = PolyLine([120, 110, 130, 150],
                strokeWidth=2,
                strokeColor=colors.red)
  d.add(pl)

  # pl = definePath(isClipPath=1)
  # pl.moveTo(30.0, 30.0)
  # pl.lineTo(30.0, pixHeight/2)
  # pl.lineTo(pixWidth/2, pixHeight/2)
  # pl.lineTo(pixWidth/2, 30.0)
  # pl.closePath()
  # d.add(pl)

  gr = Group()
  gr.add(Rect(0.0, 0.0, 20.0, 20.0, fillColor=colors.yellow))
  gr.add(Rect(30.0, 30.0, 20.0, 20.0, fillColor=colors.blue))
  d.add(gr)
  # d.add(Rect(0.0, 0.0, 20.0, 20.0, fillColor=colors.yellow))
  # d.add(Rect(30.0, 30.0, 20.0, 20.0, fillColor=colors.blue))

  # paragraphs.append(d)

  fred = Clipped_Flowable(d)
  paragraphs.append(fred)

  doc.pageCompression = None
  # this generates the buffer to write to the file
  doc.build(paragraphs)

  c = canvas.Canvas(filename='/Users/ejb66/Desktop/testCCPNpdf3.pdf', pagesize=A4)

  # make a clippath
  pl = c.beginPath()
  pl.moveTo(0, 0)
  pl.lineTo(0, 100)
  pl.lineTo(100, 100)
  pl.lineTo(100, 0)
  pl.close()
  c.clipPath(pl, fill=0, stroke=0)

  # draw the drawing to the canvas after clipping defined
  d.drawOn(c, 0, 0)
  c.save()

  # Write the PDF to a file
  with open('/Users/ejb66/Desktop/testCCPNpdf.pdf', 'wb') as fd:
    fd.write(buf.getvalue())

  c = canvas.Canvas(filename='/Users/ejb66/Desktop/testCCPNpdf2.pdf', pagesize=A4)

  # define a clipping path
  pageWidth = A4[0]
  pageHeight = A4[1]

  p = c.beginPath()
  p.moveTo(0,0)
  p.lineTo(0, 200)
  p.lineTo(200, 200)
  p.lineTo(200, 0)
  p.close()
  c.clipPath(p, fill=0, stroke=0)

  red50transparent = colors.Color(100, 0, 0, alpha=0.5)
  c.setFillColor(colors.black)
  c.setFont('Helvetica', 10)
  c.drawString(25, 180, 'solid')
  c.setFillColor(colors.blue)
  c.rect(25, 25, 100, 100, fill=True, stroke=False)
  c.setFillColor(colors.red)
  c.rect(100, 75, 100, 100, fill=True, stroke=False)
  c.setFillColor(colors.black)
  c.drawString(225, 180, 'transparent')
  c.setFillColor(colors.blue)
  c.rect(225, 25, 100, 100, fill=True, stroke=False)
  c.setFillColor(red50transparent)
  c.rect(300, 75, 100, 100, fill=True, stroke=False)

  c.rect(0, 0, 100, 100, fill=True, stroke=False)

  # this is much better as it remembers the transparency and object grouping
  from reportlab.lib.units import inch
  h = inch / 3.0
  k = inch / 2.0
  c.setStrokeColorRGB(0.2, 0.3, 0.5)
  c.setFillColorRGB(0.8, 0.6, 0.2)
  c.setLineWidth(4)
  p = c.beginPath()
  for i in (1, 2, 3, 4):
    for j in (1, 2):
      xc, yc = inch * i, inch * j
      p.moveTo(xc, yc)
      p.arcTo(xc - h, yc - k, xc + h, yc + k, startAng=0, extent=60 * i)
      # close only the first one, not the second one
      if j == 1:
        p.close()
  c.drawPath(p, fill=1, stroke=1)

  c.save()



# class svgFileOutput():
#   def __init__(self, filename):
#     self._code = []
#     self._filename = filename
#     self._useGroups = []
#
#   @property
#   def svgCode(self):
#     return self._code
#
#   def _AKWtoStr(self, *args, **kwargs):
#     fmsg = []
#     if args: fmsg.append(', '.join([str(arg) for arg in args]))
#     if kwargs: fmsg.append(' '.join([str(ky)+'='+str(kwargs[ky]) for ky in kwargs.keys()]))
#     return fmsg
#
#   @contextmanager
#   def newSvgFile(self, *args, **kwargs):
#     try:
#       # initialise the file
#       self._code = []
#
#       fmsg = self._AKWtoStr(args, kwargs)
#       # viewBox="0 0 453 200" width="453" height="200"
#       self._code.append('<?xml version="1.0" encoding="utf-8"?>')
#       self._code.append("<!DOCTYPE svg")
#       self._code.append("  PUBLIC '-//W3C//DTD SVG 1.0//EN'")
#       self._code.append("  'http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd'>")
#       self._code.append('<svg fill-rule="evenodd" height="200.23536165327212" preserveAspectRatio="xMinYMin meet" version="1.0" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">')
#
#       yield
#
#     finally:
#       # write footer to array
#       self._code.append('</svg>')
#
#   @contextmanager
#   def newSvgBlock(self):
#     try:
#       self._code.append('<svg>')    # some more info
#     finally:
#       self._code.append('</svg>')
#
#   @contextmanager
#   def newSvgGroup(self):
#     try:
#       self._code.append('<g>')    # some more info
#     finally:
#       self._code.append('</g>')
#
#   @contextmanager
#   def newSvgSymbol(self):
#     try:
#       self._code.append('<symbol>')    # some more info
#     finally:
#       self._code.append('</symbol>')
#
#   def svgWriteString(self, value):
#     self._code.append(value)
#
#   def svgTitle(self, title):
#     self._code.append('<title>%s</title>' % title)
#
#   def svgDesc(self, desc):
#     self._code.append('<desc>%s</desc>' % desc)
#
#   def writeFile(self):
#     with open(self._filename, 'w') as f:
#       for ll in self._code:
#         f.write(self._code[ll])
