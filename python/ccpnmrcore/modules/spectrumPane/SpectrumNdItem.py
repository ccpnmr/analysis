"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
import numpy

from OpenGL import GL
from PySide import QtGui, QtCore, QtOpenGL

from ccpnmrcore.modules.spectrumPane.SpectrumItem import SpectrumItem

from ccpnc.contour import Contourer2d
###from ccpnc.peak import Peak

from ccpn.lib import Spectrum as LibSpectrum  # TEMP (should be direct function call on spectrum object some day)

###from ccpnmrcore.modules.spectrumPane.PeakListNdItem import PeakListNdItem

class SpectrumNdItem(SpectrumItem):
  
  ###PeakListItemClass = PeakListNdItem
  
  #sigClicked = QtCore.Signal(object, object)

  def __init__(self, spectrumPane, spectrum, dimMapping=None, region=None, posColor=None, negColor=None, **kw):
    """ spectrumPane is the parent
        spectrum is the Spectrum name or object
        region is in units of parent, ordered by spectrum dimensions
        dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """

    self.setAcceptedMouseButtons = QtCore.Qt.LeftButton

    SpectrumItem.__init__(self, spectrumPane, spectrum, dimMapping)

    self.posColor = posColor
    self.negColor = negColor

    # self.spectralData = self.getSlices()
    
    self.previousRegion = spectrum.dimensionCount * [None]

    self.setZValue(-1)  # this is so that the contours are drawn on the bottom

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

    if self.posColor is None:
      self.posColor = 'ff0000' # red

    if self.negColor is None:
      self.negColor = '0000ff' # blue


    self.posContoursVisible = True # this block of code TEMP
    self.negContoursVisible = True
    self.baseLevel = 1000000.00
    self.multiplier = 1.4
    self.numberOfLevels = 20
    try:
      self.levels
    except AttributeError:
      self.levels = self.getLevels()

    # self.levels = tuple(self.levels)
    # self.levels = (1000000.0, 200000.0, 400000.0, 500000.0, 700000.0, 10000000.0, 5000000.0, 2000000.0,
    # -1000000.0, -200000.0, -400000.0, -500000.0, -700000.0, -10000000.0, -5000000.0, -2000000.0)
    self.posColors = (self.getColorTuple(self.posColor),)
    self.negColors = (self.getColorTuple(self.negColor),)

    self.contoursValid = False
    self.contourDisplayIndexDict = {} # level -> display list index
        
  def getColorTuple(self, colorString):
    
    colorTuple = QtGui.QColor(colorString).getRgb()
    colorTuple = tuple([c/255 for c in colorTuple])

    return colorTuple
    
  def getLevels(self):
    
    levels = [self.baseLevel]
    for n in range(int(self.numberOfLevels-1)):
      levels.append(self.multiplier*levels[-1])
      
    return tuple(numpy.array(levels, dtype=numpy.float32))

  def zPlaneSize(self):
    
    spectrum = self.spectrum
    dimensionCount = spectrum.dimensionCount
    if dimensionCount < 3:
      return None
      
    xDim = self.xDim
    yDim = self.yDim
    zDims = set(range(dimensionCount)) - {xDim, yDim}
    self.zDims = zDims
    zDim = zDims.pop()

    point = (0.0, 1.0)
    value = LibSpectrum.getDimValueFromPoint(spectrum, zDim, point)
    size = abs(value[1] - value[0])
    return size
    
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
    if self.previousRegion[2:] == self.spectrumPane.region[2:]:
      # release unwanted old levels
      removedLevels = oldLevels - levels
    else:
      # release everything if z region changes (could do better)
      removedLevels = oldLevels
      oldLevels = set()
    for level in removedLevels:
      self.releaseDisplayList(level)
      
    self.previousRegion = self.spectrumPane.region[:]
      
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

      GL.glDeleteLists(self.contourDisplayIndexDict[level], 1)
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
      zregionValue = self.spectrumPane.region[zDim]
      print(zregionValue)
      zregionPoint = LibSpectrum.getDimPointFromValue(spectrum, zDim, zregionValue)
      zregionPoint = (int(numpy.round(zregionPoint[0])), int(numpy.round(zregionPoint[1])))
      position = dimensionCount * [0]
      for z in range(*zregionPoint):  # TBD
        position[zDim] = z
        # below does not work yet
        #planeData = spectrum.getPlaneData(position, xDim, yDim)
        print(xDim, yDim)
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
    dimensionCount = spectrum.dimensionCount
    pointCounts = spectrum.pointCounts
    pntRegion = dimensionCount * [None]
    for dim in range(dimensionCount):
      if dim in (self.xDim, self.yDim):
        region = (0, pointCounts[dim])
      else:
        n = pointCounts[dim] // 2
        region = (n, n+1)
      pntRegion[dim] = region
    ppmRegion = []
    for dim in range(dimensionCount):
      (firstPpm, lastPpm) = LibSpectrum.getDimValueFromPoint(spectrum, dim, pntRegion[dim])
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
    
    (firstPoint, lastPoint) = LibSpectrum.getDimPointFromValue(self.spectrum, dim, (region0, region1))
    
    scale = (pixelViewBox1-pixelViewBox0) / (lastPoint-firstPoint)
    translate = pixelViewBox0 - firstPoint * scale
    
    return translate, scale

  def raiseBaseLevel(self):
    self.baseLevel*=1.4
    self.levels = self.getLevels()

  def lowerBaseLevel(self):
    self.baseLevel/=1.4
    self.levels = self.getLevels()
        
    

