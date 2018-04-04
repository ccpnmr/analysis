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
import numpy as np
from PyQt5 import QtWidgets

try:
    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL hellogl",
            "PyOpenGL must be installed to run this example.")
    sys.exit(1)

from ccpn.core.PeakList import PeakList
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import CcpnGLWidget, GLPeakListArray, GLVertexArray, GLRENDERMODE_DRAW, GLRENDERMODE_RESCALE,\
                                  GLRENDERMODE_REBUILD, GLREFRESHMODE_REBUILD,\
                                  LENCOLORS, LENPID,\
                                  GLString
from ccpn.ui.gui.modules.GuiPeakListView import _getScreenPeakAnnotation, _getPeakAnnotation    # temp until I rewrite
import ccpn.util.Phasing as Phasing

REGION_COLOURS = {
  'green': (0, 1.0, 0.1, 0.15),
  'yellow': (0.9, 1.0, 0.05, 0.15),
  'blue': (0.2, 0.1, 1.0, 0.15),
  'transparent': (1.0, 1.0, 1.0, 0.01),
  'grey': (1.0, 1.0, 1.0, 0.15),
  'red': (1.0, 0.1, 0.2, 0.15),
  'purple': (0.7, 0.4, 1.0, 0.15),
  None: (0.2, 0.1, 1.0, 0.15)
}


class GuiNdWidget(CcpnGLWidget):

  is1D = False
  INVERTXAXIS = True
  INVERTYAXIS = True
  SPECTRUMPOSCOLOUR = 'positiveContourColour'
  SPECTRUMNEGCOLOUR = 'negativeContourColour'

  def __init__(self, parent=None, mainWindow=None, rightMenu=None, stripIDLabel=None):
    super(GuiNdWidget, self).__init__(parent=parent,
                                      mainWindow=mainWindow,
                                      rightMenu=rightMenu,
                                      stripIDLabel=stripIDLabel)


class Gui1dWidget(CcpnGLWidget):

  AXIS_MARGINRIGHT = 65
  YAXISUSEEFORMAT = True
  INVERTXAXIS = True
  INVERTYAXIS = False
  AXISLOCKEDBUTTON = True
  is1D = True
  SPECTRUMPOSCOLOUR = 'sliceColour'

  def __init__(self, parent=None, mainWindow=None, rightMenu=None, stripIDLabel=None):
    super(Gui1dWidget, self).__init__(parent=parent,
                                      mainWindow=mainWindow,
                                      rightMenu=rightMenu,
                                      stripIDLabel=stripIDLabel)

  def _updateHighlightedPeaks(self, spectrumView, peakListView):
    spectrum = spectrumView.spectrum
    strip = self._parent

    symbolType = self._preferences.peakSymbolType
    symbolWidth = self._preferences.peakSymbolSize / 2.0
    lineThickness = self._preferences.peakSymbolThickness / 2.0

    drawList = self._GLPeakLists[peakListView]

    drawList.indices = np.empty(0, dtype=np.uint)

    index = 0
    indexPtr = 0

    if symbolType is not None:
      # for peak in pls.peaks:

      listColour = peakListView.peakList.symbolColour
      if listColour == '#':
        listColour = getattr(peakListView.peakList.spectrum, self.SPECTRUMPOSCOLOUR)
      listColR = int(listColour.strip('# ')[0:2], 16) / 255.0
      listColG = int(listColour.strip('# ')[2:4], 16) / 255.0
      listColB = int(listColour.strip('# ')[4:6], 16) / 255.0

      for pp in range(0, len(drawList.pids), LENPID):

        # check whether the peaks still exists
        peak = drawList.pids[pp]
        offset = drawList.pids[pp+1]
        numPoints = drawList.pids[pp+2]

        if not peak.isDeleted:
          _isSelected = False
          if self._isSelected(peak):
          # if hasattr(peak, '_isSelected') and peak._isSelected:
            _isSelected = True
            colR, colG, colB = self.highlightColour[:3]
            drawList.indices = np.append(drawList.indices, np.array([index, index+1, index+2, index+3,
                                                                    index, index+2, index+2, index+1,
                                                                    index, index+3, index+3, index+1], dtype=np.uint))
          else:
            # colour = peak.peakList.symbolColour
            colR = listColR   #int(colour.strip('# ')[0:2], 16) / 255.0
            colG = listColG   #int(colour.strip('# ')[2:4], 16) / 255.0
            colB = listColB   #int(colour.strip('# ')[4:6], 16) / 255.0

            drawList.indices = np.append(drawList.indices,
                                         np.array([index, index+1, index+2, index+3], dtype=np.uint))
          drawList.colors[offset*4:(offset+numPoints)*4] = [colR, colG, colB, 1.0] * numPoints

          drawList.pids[pp+3:pp+8] = [True, True, _isSelected,
                                      indexPtr, len(drawList.indices)]
          indexPtr = len(drawList.indices)

        index += numPoints

  def _buildPeakLists(self, spectrumView, peakListView):
    spectrum = spectrumView.spectrum

    if peakListView not in self._GLPeakLists:
      self._GLPeakLists[peakListView] = GLPeakListArray(GLContext=self,
                                                      spectrumView=spectrumView,
                                                      peakListView=peakListView)

    drawList = self._GLPeakLists[peakListView]

    if drawList.renderMode == GLRENDERMODE_RESCALE:
      drawList.renderMode = GLRENDERMODE_DRAW               # back to draw mode
      self._rescalePeakList(spectrumView=spectrumView, peakListView=peakListView)
      self._rescalePeakListLabels(spectrumView=spectrumView, peakListView=peakListView,
                                  drawList=self._GLPeakListLabels[peakListView])

    elif drawList.renderMode == GLRENDERMODE_REBUILD:
      drawList.renderMode = GLRENDERMODE_DRAW               # back to draw mode

      # drawList.refreshMode = GLRENDERMODE_DRAW

      drawList.clearArrays()

      # find the correct scale to draw square pixels
      # don't forget to change when the axes change

      symbolType = self._preferences.peakSymbolType
      symbolWidth = self._preferences.peakSymbolSize / 2.0
      # lineThickness = self._preferences.peakSymbolThickness / 2.0

      x = abs(self.pixelX)
      y = abs(self.pixelY)
      # fix the aspect ratio of the cross to match the screen
      # minIndex = 0 if x <= y else 1
      # pos = [symbolWidth, symbolWidth * y / x]
      # w = r = pos[minIndex]

      if x <= y:
        r = symbolWidth
        w = symbolWidth * y / x
      else:
        w = symbolWidth
        r = symbolWidth * x / y

      if symbolType is not None:      #== 0:  # a cross

        # change the ratio on resize
        drawList.refreshMode = GLREFRESHMODE_REBUILD
        drawList.drawMode = GL.GL_LINES
        drawList.fillMode = None

      # elif symbolType == 1:  # draw an ellipse at lineWidth
      #
      #   # fix the size to the axes
      #   drawList.refreshMode = GLREFRESHMODE_NEVER
      #   drawList.drawMode = GL.GL_LINES
      #   drawList.fillMode = None
      #
      # elif symbolType == 2:  # draw a filled ellipse at lineWidth
      #
      #   # fix the size to the axes
      #   drawList.refreshMode = GLREFRESHMODE_NEVER
      #   drawList.drawMode = GL.GL_TRIANGLES
      #   drawList.fillMode = GL.GL_FILL

      # build the peaks VBO
      index = 0
      indexPtr = 0
      # for pls in spectrum.peakLists:

      pls = peakListView.peakList

      listColour = pls.symbolColour
      if listColour == '#':
        listColour = getattr(pls.spectrum, self.SPECTRUMPOSCOLOUR)
      listColR = int(listColour.strip('# ')[0:2], 16) / 255.0
      listColG = int(listColour.strip('# ')[2:4], 16) / 255.0
      listColB = int(listColour.strip('# ')[4:6], 16) / 255.0

      for peak in pls.peaks:

        # TODO:ED display the required peaks - possibly build all then on draw selected later
        strip = spectrumView.strip
        # _isInPlane = strip.peakIsInPlane(peak)
        # if not _isInPlane:
        #   _isInFlankingPlane = strip.peakIsInFlankingPlane(peak)
        # else:
        #   _isInFlankingPlane = None

        # if not _isInPlane and not _isInFlankingPlane:
        #   continue

        if self._isSelected(peak):
        # if hasattr(peak, '_isSelected') and peak._isSelected:
          colR, colG, colB = self.highlightColour[:3]
        else:
          # colour = pls.symbolColour
          colR = listColR   # int(colour.strip('# ')[0:2], 16)/255.0
          colG = listColG   # int(colour.strip('# ')[2:4], 16)/255.0
          colB = listColB   # int(colour.strip('# ')[4:6], 16)/255.0

        # get the correct coordinates based on the axisCodes
        p0 = [0.0] * 2            #len(self.axisOrder)
        for ps, psCode in enumerate(self.axisOrder[0:2]):
          for pp, ppCode in enumerate(peak.axisCodes):

            if self._preferences.matchAxisCode == 0:  # default - match atom type
              if ppCode[0] == psCode[0]:
                p0[ps] = peak.position[pp]
              else:
                p0[ps] = peak.height

            elif self._preferences.matchAxisCode == 1:  # match full code
              if ppCode == psCode:
                p0[ps] = peak.position[pp]
              else:
                p0[ps] = peak.height

        if symbolType is not None:      #== 0:

          # draw a cross
          # keep the cross square at 0.1ppm

          _isSelected = False
          if self._isSelected(peak):
          # if hasattr(peak, '_isSelected') and peak._isSelected:
            _isSelected = True
            drawList.indices = np.append(drawList.indices, [index, index + 1, index + 2, index + 3,
                                                            index, index+2, index+2, index+1,
                                                            index, index+3, index+3, index+1])
          else:
            drawList.indices = np.append(drawList.indices, [index, index + 1, index + 2, index + 3])

          drawList.vertices = np.append(drawList.vertices, [p0[0]-r, p0[1]-w
                                                            , p0[0]+r, p0[1]+w
                                                            , p0[0]+r, p0[1]-w
                                                            , p0[0]-r, p0[1]+w])
          drawList.colors = np.append(drawList.colors, [colR, colG, colB, 1.0] * LENCOLORS)
          drawList.attribs = np.append(drawList.attribs, [p0[0], p0[1]
                                                          ,p0[0], p0[1]
                                                          ,p0[0], p0[1]
                                                          ,p0[0], p0[1]])

          # keep a pointer to the peak
          drawList.pids = np.append(drawList.pids, [peak, index, 4,
                                                    True, True, _isSelected,
                                                    indexPtr, len(drawList.indices)])
          indexPtr = len(drawList.indices)

          index += 4
          drawList.numVertices += 4

  def _rescalePeakList(self, spectrumView, peakListView):
    drawList = self._GLPeakLists[peakListView]

    # if drawList.refreshMode == GLREFRESHMODE_REBUILD:

    symbolType = self._preferences.peakSymbolType
    symbolWidth = self._preferences.peakSymbolSize / 2.0
    x = abs(self.pixelX)
    y = abs(self.pixelY)

    # fix the aspect ratio of the cross to match the screen
    # minIndex = 0 if x <= y else 1
    # pos = [symbolWidth, symbolWidth * y / x]
    # w = r = pos[minIndex]

    if x <= y:
      r = symbolWidth
      w = symbolWidth * y / x
    else:
      w = symbolWidth
      r = symbolWidth * x / y

    if symbolType is not None:      #== 0:  # a cross
      # drawList.clearVertices()
      # drawList.vertices.copy(drawList.attribs)
      offsets = np.array([-r, -w, +r, +w, +r, -w, -r, +w], np.float32)
      for pp in range(0, 2*drawList.numVertices, 8):
        drawList.vertices[pp:pp+8] = drawList.attribs[pp:pp+8] + offsets

  def _appendPeakListItem(self, spectrumView, peakListView, peak):
    spectrum = spectrumView.spectrum
    drawList = self._GLPeakLists[peakListView]

    # find the correct scale to draw square pixels
    # don't forget to change when the axes change

    symbolType = self._preferences.peakSymbolType
    symbolWidth = self._preferences.peakSymbolSize / 2.0
    lineThickness = self._preferences.peakSymbolThickness / 2.0

    x = abs(self.pixelX)
    y = abs(self.pixelY)
    # fix the aspect ratio of the cross to match the screen
    minIndex = 0 if x <= y else 1
    # pos = [symbolWidth, symbolWidth * y / x]
    # w = r = pos[minIndex]

    if x <= y:
      r = symbolWidth
      w = symbolWidth * y / x
    else:
      w = symbolWidth
      r = symbolWidth * x / y

    if symbolType is not None:      #== 0:  # a cross

      # change the ratio on resize
      drawList.refreshMode = GLREFRESHMODE_REBUILD
      drawList.drawMode = GL.GL_LINES
      drawList.fillMode = None

    # elif symbolType == 1:  # draw an ellipse at lineWidth
    #
    #   # fix the size to the axes
    #   drawList.refreshMode = GLREFRESHMODE_NEVER
    #   drawList.drawMode = GL.GL_LINES
    #   drawList.fillMode = None
    #
    # elif symbolType == 2:  # draw a filled ellipse at lineWidth
    #
    #   # fix the size to the axes
    #   drawList.refreshMode = GLREFRESHMODE_NEVER
    #   drawList.drawMode = GL.GL_TRIANGLES
    #   drawList.fillMode = GL.GL_FILL

    # build the peaks VBO
    index = 0
    indexPtr = len(drawList.indices)

    # for pls in spectrum.peakLists:

    pls = peakListView.peakList
    spectrumFrequency = spectrum.spectrometerFrequencies

    listColour = pls.symbolColour
    if listColour == '#':
      listColour = getattr(pls.spectrum, self.SPECTRUMPOSCOLOUR)
    listColR = int(listColour.strip('# ')[0:2], 16) / 255.0
    listColG = int(listColour.strip('# ')[2:4], 16) / 255.0
    listColB = int(listColour.strip('# ')[4:6], 16) / 255.0

    # TODO:ED display the required peaks - possibly build all then on draw selected later
    strip = spectrumView.strip
    _isInPlane = strip.peakIsInPlane(peak)
    if not _isInPlane:
      _isInFlankingPlane = strip.peakIsInFlankingPlane(peak)
    else:
      _isInFlankingPlane = None

    # if not _isInPlane and not _isInFlankingPlane:
    #   continue

    if self._isSelected(peak):
    # if hasattr(peak, '_isSelected') and peak._isSelected:
      colR, colG, colB = self.highlightColour[:3]
    else:
      # colour = pls.symbolColour
      colR = listColR  # int(colour.strip('# ')[0:2], 16)/255.0
      colG = listColG  # int(colour.strip('# ')[2:4], 16)/255.0
      colB = listColB  # int(colour.strip('# ')[4:6], 16)/255.0

    # get the correct coordinates based on the axisCodes
    p0 = [0.0] * 2  # len(self.axisOrder)
    for ps, psCode in enumerate(self.axisOrder[0:2]):
      for pp, ppCode in enumerate(peak.axisCodes):

        if self._preferences.matchAxisCode == 0:  # default - match atom type
          if ppCode[0] == psCode[0]:
            p0[ps] = peak.position[pp]
          else:
            p0[ps] = peak.height

        elif self._preferences.matchAxisCode == 1:  # match full code
          if ppCode == psCode:
            p0[ps] = peak.position[pp]
          else:
            p0[ps] = peak.height

    if symbolType is not None:        #== 0:

      # draw a cross
      # keep the cross square at 0.1ppm

      _isSelected = False
      drawList.indices = np.append(drawList.indices, [index, index + 1, index + 2, index + 3])

      if self._isSelected(peak):
      # if hasattr(peak, '_isSelected') and peak._isSelected:
        _isSelected = True
        drawList.indices = np.append(drawList.indices, [index, index + 2, index + 2, index + 1,
                                                        index, index + 3, index + 3, index + 1])

      drawList.vertices = np.append(drawList.vertices, [p0[0] - r, p0[1] - w
                                                      , p0[0] + r, p0[1] + w
                                                      , p0[0] + r, p0[1] - w
                                                      , p0[0] - r, p0[1] + w])
      drawList.colors = np.append(drawList.colors, [colR, colG, colB, 1.0] * 4)
      drawList.attribs = np.append(drawList.attribs, [p0[0], p0[1]
                                                      , p0[0], p0[1]
                                                      , p0[0], p0[1]
                                                      , p0[0], p0[1]])

      # keep a pointer to the peak
      drawList.pids = np.append(drawList.pids, [peak, drawList.numVertices, 4,
                                                True, True, _isSelected,
                                                indexPtr, len(drawList.indices)])

      index += 4
      drawList.numVertices += 4

  def _removePeakListItem(self, spectrumView, peakListView, delPeak):
    symbolType = self._preferences.peakSymbolType

    drawList = self._GLPeakLists[peakListView]

    index = 0
    indexOffset = 0
    numPoints = 0

    pp = 0
    while (pp < len(drawList.pids)):
      # check whether the peaks still exists
      peak = drawList.pids[pp]

      if peak == delPeak:
        offset = drawList.pids[pp + 1]
        numPoints = drawList.pids[pp + 2]

        # TODO:ED don't like this - should be same code for all
        # if symbolType != 0:
        #   numPoints = 2*numPoints+5

        # _isInPlane = drawList.pids[pp + 3]
        # _isInFlankingPlane = drawList.pids[pp + 4]
        # _isSelected = drawList.pids[pp + 5]
        indexStart = drawList.pids[pp + 6]
        indexEnd = drawList.pids[pp + 7]
        indexOffset = indexEnd-indexStart

        drawList.indices = np.delete(drawList.indices, np.s_[indexStart:indexEnd])
        drawList.vertices = np.delete(drawList.vertices, np.s_[2*offset:2*(offset+numPoints)])
        drawList.attribs = np.delete(drawList.attribs, np.s_[2*offset:2*(offset+numPoints)])
        drawList.colors = np.delete(drawList.colors, np.s_[4*offset:4*(offset+numPoints)])
        drawList.pids = np.delete(drawList.pids, np.s_[pp:pp + LENPID])
        drawList.numVertices -= numPoints
        break
      else:
        pp += LENPID

    # clean up the rest of the list
    while (pp < len(drawList.pids)):
      drawList.pids[pp + 1] -= numPoints
      drawList.pids[pp + 6] -= indexOffset
      drawList.pids[pp + 7] -= indexOffset
      pp += LENPID

  def _appendPeakListLabel(self, spectrumView, peakListView, stringList, peak):
    # get the correct coordinates based on the axisCodes

    spectrum = spectrumView.spectrum
    spectrumFrequency = spectrum.spectrometerFrequencies
    pls = peakListView.peakList

    symbolWidth = self._preferences.peakSymbolSize / 2.0

    # get the correct coordinates based on the axisCodes
    p0 = [0.0] * 2  # len(self.axisOrder)
    for ps, psCode in enumerate(self.axisOrder[0:2]):
      for pp, ppCode in enumerate(peak.axisCodes):

        if self._preferences.matchAxisCode == 0:  # default - match atom type
          if ppCode[0] == psCode[0]:
            p0[ps] = peak.position[pp]
          else:
            p0[ps] = peak.height

        elif self._preferences.matchAxisCode == 1:  # match full code
          if ppCode == psCode:
            p0[ps] = peak.position[pp]
          else:
            p0[ps] = peak.height

    # if lineWidths[0] and lineWidths[1]:
    #   # draw 24 connected segments
    #   r = 0.5 * lineWidths[0] / frequency[0]
    #   w = 0.5 * lineWidths[1] / frequency[1]
    # else:

    # r = symbolWidth
    # w = symbolWidth

    # if axisCount == 2:
      # TODO:ED display the required peaks
      strip = spectrumView.strip
      # _isInPlane = strip.peakIsInPlane(peak)
      # if not _isInPlane:
      #   _isInFlankingPlane = strip.peakIsInFlankingPlane(peak)
      # else:
      #   _isInFlankingPlane = None
      #
      # if not _isInPlane and not _isInFlankingPlane:
      #   return

    if self._isSelected(peak):
    # if hasattr(peak, '_isSelected') and peak._isSelected:
      colR, colG, colB = self.highlightColour[:3]
    else:
      colour = pls.textColour
      if colour == '#':
        colour = getattr(pls.spectrum, self.SPECTRUMPOSCOLOUR)
      colR = int(colour.strip('# ')[0:2], 16) / 255.0
      colG = int(colour.strip('# ')[2:4], 16) / 255.0
      colB = int(colour.strip('# ')[4:6], 16) / 255.0

    if self._parent.peakLabelling == 0:
      text = _getScreenPeakAnnotation(peak, useShortCode=True)
    elif self._parent.peakLabelling == 1:
      text = _getScreenPeakAnnotation(peak, useShortCode=False)
    else:
      text = _getPeakAnnotation(peak)  # original 'pid'

    # # TODO:ED check labelling
    # text = peak.id

    # TODO:ED check axisCodes and ordering
    stringList.append(GLString(text=text,
                                font=self.glSmallFont,
                                x=p0[0], y=p0[1],
                                ox=symbolWidth, oy=symbolWidth,
                                # x=self._screenZero[0], y=self._screenZero[1]
                                color=(colR, colG, colB, 1.0), GLContext=self,
                                object=peak))

  def _rescalePeakListLabels(self, spectrumView=None, peakListView=None, drawList=None):
    # drawList = self._GLPeakListLabels[peakListView]
    # strip = self._parent

    # pls = peakListView.peakList
    symbolType = self._preferences.peakSymbolType
    symbolWidth = self._preferences.peakSymbolSize / 2.0
    x = abs(self.pixelX)
    y = abs(self.pixelY)

    if symbolType is not None:          #== 0:  # a cross
      # fix the aspect ratio of the cross to match the screen
      # minIndex = 0 if x <= y else 1
      # pos = [symbolWidth, symbolWidth * y / x]

      if x <= y:
        r = symbolWidth
        w = symbolWidth * y / x
      else:
        w = symbolWidth
        r = symbolWidth * x / y

      for drawStr in drawList.stringList:
        drawStr.setStringOffset((r * np.sign(self.pixelX), w * np.sign(self.pixelY)))

    # elif symbolType == 1:
    #   for drawStr in drawList.stringList:
    #     r, w = 0.7 * drawStr.lineWidths[0], 0.7 * drawStr.lineWidths[1]
    #     drawStr.setStringOffset((r * np.sign(self.pixelX), w * np.sign(self.pixelY)))
    #
    # elif symbolType == 2:
    #   for drawStr in drawList.stringList:
    #     r, w = 0.7 * drawStr.lineWidths[0], 0.7 * drawStr.lineWidths[1]
    #     drawStr.setStringOffset((r * np.sign(self.pixelX), w * np.sign(self.pixelY)))

  def _selectPeak(self, xPosition, yPosition):
    """
    (de-)Select first peak near cursor xPosition, yPosition
    if peak already was selected, de-select it
    """
    xPeakWidth = abs(self.pixelX) * self.peakWidthPixels
    yPeakWidth = abs(self.pixelY) * self.peakWidthPixels
    xPositions = [xPosition - 0.5*xPeakWidth, xPosition + 0.5*xPeakWidth]
    yPositions = [yPosition - 0.5*yPeakWidth, yPosition + 0.5*yPeakWidth]

    peaks = list(self.current.peaks)
    for spectrumView in self._parent.spectrumViews:

      # TODO:ED could change this to actually use the pids in the drawList
      for peakListView in spectrumView.peakListViews:
        if spectrumView.isVisible() and peakListView.isVisible():
          # for peakList in spectrumView.spectrum.peakLists:
          peakList = peakListView.peakList
          if not isinstance(peakList, PeakList):  # it could be an IntegralList
            continue

          for peak in peakList.peaks:
            if (xPositions[0] < float(peak.position[0]) < xPositions[1]
              and yPositions[0] < float(peak.height) < yPositions[1]):

              # if peak in self.current.peaks:
              #   self.current._peaks.remove(peak)
              # else:
              #   self.current.addPeak(peak)
              if peak in peaks:
                peaks.remove(peak)
              else:
                peaks.append(peak)

    self.current.peaks = peaks

  def _newStatic1DTraceData(self, spectrumView, tracesDict,
                            point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, positionPixel,
                            ph0=None, ph1=None, pivot=None):

    try:
      # ignore for 1D if already in the traces list
      for thisTrace in tracesDict:
        if spectrumView == thisTrace.spectrumView:
          return

      pointInt = [1 + int(pnt + 0.5) for pnt in point]
      # data = spectrumView.spectrum.getSliceData()
      # data = spectrumView.spectrum.get1dSpectrumData()

      # TODO:ED this does not change the data model
      data = spectrumView.spectrum.intensities

      preData = data

      if ph0 is not None and ph1 is not None and pivot is not None:
        preData = Phasing.phaseRealData(data, ph0, ph1, pivot)

      # x = np.array([xDataDim.primaryDataDimRef.pointToValue(p + 1) for p in range(xMinFrequency, xMaxFrequency)])
      x = spectrumView.spectrum.positions

      # y = np.array([preData[p % xNumPoints] for p in range(xMinFrequency, xMaxFrequency + 1)])

      # y = positionPixel[1] + spectrumView._traceScale * (self.axisT-self.axisB) * \
      #     np.array([preData[p % xNumPoints] for p in range(xMinFrequency, xMaxFrequency + 1)])

      colour = spectrumView._getColour(self.SPECTRUMPOSCOLOUR, '#aaaaaa')
      colR = int(colour.strip('# ')[0:2], 16) / 255.0
      colG = int(colour.strip('# ')[2:4], 16) / 255.0
      colB = int(colour.strip('# ')[4:6], 16) / 255.0

      tracesDict.append(GLVertexArray(numLists=1,
                                      renderMode=GLRENDERMODE_REBUILD,
                                      blendMode=False,
                                      drawMode=GL.GL_LINE_STRIP,
                                      dimension=2,
                                      GLContext=self))

      numVertices = len(x)
      hSpectrum = tracesDict[-1]
      hSpectrum.indices = numVertices
      hSpectrum.numVertices = numVertices
      hSpectrum.indices = np.arange(numVertices, dtype=np.uint)
      hSpectrum.colors = np.array((self._phasingTraceColour) * numVertices, dtype=np.float32)
      hSpectrum.vertices = np.zeros((hSpectrum.numVertices * 2), dtype=np.float32)

      # x = np.append(x, [xDataDim.primaryDataDimRef.pointToValue(xMaxFrequency + 1),
      #                   xDataDim.primaryDataDimRef.pointToValue(xMinFrequency)])
      # # y = np.append(y, [positionPixel[1], positionPixel[1]])
      # hSpectrum.colors = np.append(hSpectrum.colors, ((colR, colG, colB, 1.0),
      #                                       (colR, colG, colB, 1.0)))

      hSpectrum.vertices[::2] = x
      hSpectrum.vertices[1::2] = preData

      # store the pre-phase data
      hSpectrum.data = data
      hSpectrum.values = [spectrumView, point, xDataDim,
                          xMinFrequency, xMaxFrequency,
                          xNumPoints, positionPixel]
      hSpectrum.spectrumView = spectrumView

    except Exception as es:
      print ('>>>', str(es))
      tracesDict = []
