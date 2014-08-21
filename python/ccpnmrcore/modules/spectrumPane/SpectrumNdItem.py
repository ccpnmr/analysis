import numpy

from OpenGL import GL
from PySide import QtGui, QtCore, QtOpenGL

from ccpncore.util.Color import Color

from ccpnmrcore.modules.spectrumPane.SpectrumItem import SpectrumItem

from ccpnc.contour import Contourer2d

from ccpn.lib import Spectrum as LibSpectrum  # TEMP (should be direct function call on spectrum object some day)

class SpectrumNdItem(SpectrumItem):

  def __init__(self, spectrumPane, spectrum, dimMapping=None, region=None):
    """ spectrumPane is the parent
        spectrum is the Spectrum name or object
        region is in units of parent, ordered by spectrum dimensions
        dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """

    SpectrumItem.__init__(self, spectrumPane, spectrum, dimMapping)
        
    if not region:
      # chicken and egg problem, can't know xDim until after dimMapping set up
      # and that is set up in SpectrumItem constructor, but that needs to know
      # region; similar problem with spectrum object itself, which is set up in
      # SpectrumItem constructor but need to have it to hand before that called
      xDim = self.xDim
      yDim = self.yDim
      region = spectrumPane.region = self.defaultRegion()
      viewBox = spectrumPane.viewBox
      # TBD: below assumes axes inverted
      viewBox.setXRange(region[xDim][1], region[xDim][0])
      viewBox.setYRange(region[yDim][1], region[yDim][0])
    
    self.posContoursVisible = True # this block of code TEMP
    self.negContoursVisible = True
    self.levels = (10000000.0, 5000000.0, 2000000.0)
    self.posColors = (Color('#ff0000').rgba(),)
    self.negColors = (Color('#0000ff').rgba(),)
    
    self.contoursValid = False
    self.contourDisplayIndexDict = {} # level -> display list index
    
  ##### override of superclass function
  
  def paint(self, painter, option, widget=None):
    
    self.drawContours(painter)
  
  def boundingRect(self):  # seems necessary to have

    return QtCore.QRectF(-2000, -2000, 2000, 2000)  # TBD: remove hardwiring
  
  ##### functions not to be used externally #####

  def drawContours(self, painter):
    
    if not self.posContoursVisible and not self.negContoursVisible:
      return
      
    self.constructContours()
    
    posColors = self.posColors
    negColors = self.negColors
    
    levels = self.levels
    posLevels = sorted([level for level in levels if level >= 0])
    negLevels = sorted([level for level in levels if level < 0], reverse=True)
 
    painter.beginNativePainting()  # this puts OpenGL back in its default coordinate system instead of Qt one

    try:
      
      spectrum = self.spectrum
      spectrumPane = self.spectrumPane
      xTranslate, xScale = self.getTranslateScale(self.xDim)
      yTranslate, yScale = self.getTranslateScale(self.yDim)
      GL.glLoadIdentity()
      GL.glPushMatrix()
      ### do not need the below and if you have them then the axes get zapped as well unless it has positive Z values
      ###GL.glClearColor(1.0, 1.0, 1.0, 1.0)
      ###GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    
      # the below is because the y axis goes from top to bottom
      GL.glScale(1.0, -1.0, 1.0)
      GL.glTranslate(0.0, -self.spectrumPane.height(), 0.0)
      
      # the below makes sure that spectrum points get mapped to screen pixels correctly
      GL.glTranslate(xTranslate, yTranslate, 0.0)
      GL.glScale(xScale, yScale, 1.0)
      
      colorsLevels = []
      for (colors, levels) in ((posColors, posLevels), (negColors, negLevels)):
        count = len(colors)
        for n, level in enumerate(levels):
          color = colors[n % count]
          GL.glColor4f(*color)
          # TBD: scaling, translating, etc.
          GL.glCallList(self.contourDisplayIndexDict[level])
      GL.glPopMatrix()

    finally:
      
      painter.endNativePainting()
      
  def constructContours(self):
    """ Construct the contours for this spectrum using an OpenGL display list
        The way this is done here, any change in contour level or color needs to call this function.
    """
    
    oldLevels = set(self.contourDisplayIndexDict)
    levels = set(self.levels)
    
    # release unwanted old levels
    removedLevels = oldLevels - levels
    for level in removedLevels:
      self.releaseDisplayList(level)
      
    # create wanted new levels
    levels -= oldLevels
    if not levels:
      return
      
    # do the contouring and store results in display list
    if self.posContoursVisible:
      posLevels = numpy.array(sorted([level for level in levels if level >= 0]), numpy.float32)
      self.createDisplayLists(posLevels)
    else:
      posLevels = []
      
    if self.negContoursVisible:
      negLevels = numpy.array(sorted([level for level in levels if level < 0], reverse=True), numpy.float32)
      self.createDisplayLists(negLevels)
    else:
      negLevels = []
      
    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    
    for position, dataArray in self.getPlaneData():
      
      if len(posLevels): # posLevels is a numpy array so cannot just do "if posLevels":
        posContours = Contourer2d.contourer2d(dataArray, posLevels)
        for n, contourData in enumerate(posContours):
          self.addContoursToDisplayList(contourData, posLevels[n])
        
      if len(negLevels):
        negContours = Contourer2d.contourer2d(dataArray, negLevels)
        for n, contourData in enumerate(negContours):
          self.addContoursToDisplayList(contourData, negLevels[n])
        
    GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    
  def releaseDisplayLists(self):

    for level in self.contourDisplayIndexDict:
      self.releaseDisplayList(level)

  def releaseDisplayList(self, level):

    if level in self.contourDisplayIndexDict:
      GL.deleteLists(self.contourDisplayIndexDict[level], 1)
      del self.contourDisplayIndexDict[level]

  def createDisplayLists(self, levels):

    # could create them in one go but more likely to get fragmentation that way
    for level in levels:
      self.contourDisplayIndexDict[level] = GL.glGenLists(1)
    
  def getPlaneData(self):
    
    spectrum = self.spectrum
    dimensionCount = spectrum.dimensionCount
    xDim = self.xDim
    yDim = self.yDim
    if dimensionCount == 2: # TBD
      # below does not work yet
      #planeData = spectrum.getPlaneData(xDim=xDim, yDim=yDim)
      planeData = LibSpectrum.getPlaneData(spectrum, xDim=xDim, yDim=yDim)
      position = [0, 0]
      yield position, planeData
    elif dimensionCount == 3: # TBD
      zDims = set(range(dimensionCount)) - {xDim, yDim}
      zDim = zDims.pop()
      zregion = self.region[zDim] # TBD: should be in ppm not points, assume in points for now
      position = dimCount * [0]
      # below does not work yet
      #planeData = spectrum.getPlaneData(xDim=xDim, yDim=yDim)
      planeData = LibSpectrum.getPlaneData(spectrum, xDim=xDim, yDim=yDim)
      for z in range(*zregion):  # TBD
        position[zDim] = z
        #planeData = spectrum.getPlaneData(position, xDim, yDim)
        planeData = LibSpectrum.getPlaneData(spectrum, position, xDim=xDim, yDim=yDim)
        yield position, planeData
    
  def addContoursToDisplayList(self, contourData, level):
    """ contourData is list of [NumPy array with ndim = 1 and size = twice number of points] """
    
    GL.glNewList(self.contourDisplayIndexDict[level], GL.GL_COMPILE)
    
    for contour in contourData:
      GL.glVertexPointer(2, GL.GL_FLOAT, 0, contour)
      GL.glDrawArrays(GL.GL_LINE_LOOP, 0, len(contour)//2)
      
    GL.glEndList()

  def defaultRegion(self):
    spectrum = self.spectrum
    ccpnSpectrum = spectrum.ccpnSpectrum
    pointCounts = spectrum.pointCounts
    dimCount = len(pointCounts)
    pntRegion = [(0, pointCounts[0]), (0, pointCounts[1])]
    for i in range(2, dimCount):
      n = pointCounts[i] // 2
      pntRegion.append((n, n+1))
    ppmRegion = []
    for i in range(dimCount):
      dataDim = ccpnSpectrum.findFirstDataDim(dim=i+1)
      dataDimRef = dataDim.findFirstDataDimRef()
      firstPpm = dataDimRef.pointToValue(0)
      pointCount = pointCounts[i]
      lastPpm = dataDimRef.pointToValue(pointCount)
      ppmRegion.append((firstPpm, lastPpm))
      
    return ppmRegion
    
  def getTranslateScale(self, dim):
    
    spectrumPane = self.spectrumPane
    plotItem = spectrumPane.plotItem
    viewBox = spectrumPane.viewBox
    isX = (dim == self.xDim)  # assumes that xDim != yDim
    viewRegion = spectrumPane.viewRange()
    if isX:
      region1, region0 = viewRegion[0]  # TBD: relies on axes being backwards
      pixelCount = spectrumPane.width()
      pixelViewBox0 = plotItem.getAxis('left').width()
      pixelViewBox1 = pixelViewBox0 + viewBox.width()
    else:
      region1, region0 = viewRegion[1]  # TBD: relies on axes being backwards
      pixelCount = spectrumPane.height()
      pixelViewBox0 = plotItem.getAxis('bottom').height()
      pixelViewBox1 = pixelViewBox0 + viewBox.height()
    
    spectrum = self.spectrum
    ccpnSpectrum = spectrum.ccpnSpectrum
    dataDim = ccpnSpectrum.findFirstDataDim(dim=dim+1)
    dataDimRef = dataDim.findFirstDataDimRef()
    firstPoint = dataDimRef.valueToPoint(region0) - 1  # -1 because points in API start from 1
    lastPoint = dataDimRef.valueToPoint(region1) - 1
    
    scale = (pixelViewBox1-pixelViewBox0) / (lastPoint-firstPoint)
    translate = pixelViewBox0 - firstPoint * scale
    
    return translate, scale 
