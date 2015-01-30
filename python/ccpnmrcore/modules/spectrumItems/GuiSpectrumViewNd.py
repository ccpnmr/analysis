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

from ccpnmrcore.modules.spectrumItems.GuiSpectrumView import GuiSpectrumView

from ccpncore.util import Colour

from ccpnc.contour import Contourer2d
###from ccpnc.peak import Peak

from ccpn.lib import Spectrum as LibSpectrum  # TEMP (should be direct function call on spectrum object some day)

###from ccpnmrcore.modules.spectrumPane.PeakListNdItem import PeakListNdItem

# TBD: for now ignore fact that apiSpectrumView can override contour colour and/or contour levels

def _getLevels(count, base, factor):
  
  base *= 100  # TEMP
  
  levels = []
  if count > 0:
    levels = [base]
    for n in range(count-1):
      levels.append(factor * levels[-1])
      
  return levels
       
class GuiSpectrumViewNd(GuiSpectrumView):
  
  ###PeakListItemClass = PeakListNdItem
  
  #sigClicked = QtCore.Signal(object, object)

  #def __init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping=None, region=None, **kw):
  def __init__(self, guiSpectrumDisplay, apiSpectrumView, **kw):
    """ guiSpectrumDisplay is the parent
        apiSpectrumView is the (API) SpectrumView object
        region is in units of parent, ordered by spectrum dimensions
        dimMapping is from spectrum numerical dimensions to guiStrip numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """

    self.setAcceptedMouseButtons = QtCore.Qt.LeftButton

    #GuiSpectrumView.__init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping)
    GuiSpectrumView.__init__(self, guiSpectrumDisplay, apiSpectrumView)

    # self.spectralData = self.getSlices()
    
    """ dimensionOrdering not working yet so for now hardwire
    xDim, yDim = apiSpectrumView.dimensionOrdering[:2]
    xDim -= 1  # dimensionOrdering starts at 1
    yDim -= 1
    """
    xDim = 0
    yDim = 1
    # TBD: this is not correct
    apiDataSource = self.apiDataSource
    dimensionCount = apiDataSource.numDim
    self.previousRegion = dimensionCount * [None]

    self.setZValue(-1)  # this is so that the contours are drawn on the bottom
    """
    if dimMapping is not None:
      self.xDim = dimMapping[0]
      self.yDim = dimMapping[1]
"""
    """
    apiStrips = apiSpectrumView.strips
    if apiStrips:
      # just looks at first strip, is that correct idea??
      apiStrip = apiStrips[0]
      guiStrip = apiStrip.guiStrip
      viewBox = guiStrip.viewBox
    else:
      guiStrip = viewBox = None
"""
    """
    for guiStrip in guiSpectrumDisplay.guiStrips:
      viewBox = guiStrip.viewBox
      apiStrip = guiStrip.apiStrip
      for dim, axis in enumerate(apiStrip.getOrderedAxes()[:2]):
        position = axis.position
        width = axis.width
        region = (position-0.5*width, position+0.5*width)
        if dim == 0:
          viewBox.setXRange(*region)
        else: # dim == 1
          viewBox.setYRange(*region)
"""
    """
    if not region:
      # chicken and egg problem, can't know xDim until after dimMapping set up
      # and that is set up in SpectrumItem constructor, but that needs to know
      # region; similar problem with spectrum object itself, which is set up in
      # SpectrumItem constructor but need to have it to hand before that called
      region = guiSpectrumDisplay.region = self.defaultRegion()
      
      if viewBox:
        xDim = self.xDim
        yDim = self.yDim
        # TBD: below assumes axes inverted
        viewBox.setXRange(region[xDim][1], region[xDim][0])
        viewBox.setYRange(region[yDim][1], region[yDim][0])
    if guiStrip: # TBD: HACK, TEMP, should be using guiStrip.positions
      guiStrip.region = region
      """
      
    """
    self.posContoursVisible = True # this block of code TEMP
    self.negContoursVisible = True
    self.baseLevel = 1000000.00
    self.multiplier = 1.4
    self.numberOfLevels = 20
    try:
      self.levels
    except AttributeError:
      self.levels = self.getLevels()
"""
    # self.levels = tuple(self.levels)
    # self.levels = (1000000.0, 200000.0, 400000.0, 500000.0, 700000.0, 10000000.0, 5000000.0, 2000000.0,
    # -1000000.0, -200000.0, -400000.0, -500000.0, -700000.0, -10000000.0, -5000000.0, -2000000.0)

    ###self.contoursValid = False
    self.contourDisplayIndexDict = {} # level -> display list index  # TBD: this is wrong when working with multiple views
            
  """
  def getLevels(self):
    
    levels = [self.baseLevel]
    for n in range(int(self.numberOfLevels-1)):
      levels.append(self.multiplier*levels[-1])
      
    return tuple(numpy.array(levels, dtype=numpy.float32))
"""

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
    
    if not widget:
      return
      
    guiStrip = self.guiSpectrumDisplay.viewportDict[widget]
    self.drawContours(painter, guiStrip)
  
  def boundingRect(self):  # seems necessary to have

    return QtCore.QRectF(-2000, -2000, 2000, 2000)  # TBD: remove hardwiring
  
  ##### functions not to be used externally #####

  def drawContours(self, painter, guiStrip):
    
    apiDataSource = self.apiDataSource
    posLevels = _getLevels(apiDataSource.positiveContourCount, apiDataSource.positiveContourBase, apiDataSource.positiveContourFactor)
    negLevels = _getLevels(apiDataSource.negativeContourCount, apiDataSource.negativeContourBase, apiDataSource.negativeContourFactor)
    ###if not self.posContoursVisible and not self.negContoursVisible:
    if not posLevels and not negLevels:
      return
      
    self.constructContours(guiStrip, posLevels, negLevels)
    
    posColor = Colour.scaledRgba(apiDataSource.positiveContourColour) # TBD: for now assume only one colour
    negColor = Colour.scaledRgba(apiDataSource.negativeContourColour)

    """
    levels = self.levels
    posLevels = sorted([level for level in levels if level >= 0])
    negLevels = sorted([level for level in levels if level < 0], reverse=True)
""" 
    painter.beginNativePainting()  # this puts OpenGL back in its default coordinate system instead of Qt one

    try:
      
      spectrum = self.spectrum
      guiSpectrumDisplay = self.guiSpectrumDisplay
      xTranslate, xScale = self.getTranslateScale(self.xDim)
      yTranslate, yScale = self.getTranslateScale(self.yDim)
      GL.glLoadIdentity()
      GL.glPushMatrix()
      ### do not need the below and if you have them then the axes get zapped as well unless it has positive Z values
      ###GL.glClearColor(1.0, 1.0, 1.0, 1.0)
      ###GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    
      apiStrips = self.apiSpectrumView.strips
      apiStrip = apiStrips[0]
      guiStrip = apiStrip.guiStrip
    
      # the below is because the y axis goes from top to bottom
      GL.glScale(1.0, -1.0, 1.0)
      GL.glTranslate(0.0, -guiStrip.height(), 0.0)
      
      # the below makes sure that spectrum points get mapped to screen pixels correctly
      GL.glTranslate(xTranslate, yTranslate, 0.0)
      GL.glScale(xScale, yScale, 1.0)
      
      for (color, levels) in ((posColor, posLevels), (negColor, negLevels)):
        for n, level in enumerate(levels):
          GL.glColor4f(*color)
          # TBD: scaling, translating, etc.
          GL.glCallList(self.contourDisplayIndexDict[level])
      GL.glPopMatrix()

    finally:
      
      painter.endNativePainting()
      
  def constructContours(self, guiStrip, posLevels, negLevels):
    """ Construct the contours for this spectrum using an OpenGL display list
        The way this is done here, any change in contour level or color needs to call this function.
    """

    """
    oldLevels = set(self.contourDisplayIndexDict)
    levels = set(self.levels)
    zDims = set(range(self.spectrum.dimensionCount)) - {self.xDim, self.yDim}
    self.zDims = zDims
    if len(self.zDims) > 0:
      zDim = zDims.pop()
    else:
      zDim = None
    if zDim is not None and self.previousRegion[zDim] == self.guiSpectrumDisplay.region[zDim]:
      # release unwanted old levels
      removedLevels = oldLevels - levels
    else:
      # release everything if z region changes (could do better)
      removedLevels = oldLevels
      oldLevels = set()
    for level in removedLevels:
      self.releaseDisplayList(level)
    """
    self.releaseDisplayLists()  # TBD: can one do better??
      
    ###self.previousRegion = self.guiSpectrumDisplay.region[:]  # TBD: not quite right, should be looking at the strip(s)

    # create wanted new levels
    """
    levels -= oldLevels
    if not levels:
      return
    """
    
    # do the contouring and store results in display list
    ###if self.posContoursVisible:
    if posLevels:
      ###posLevels = numpy.array(sorted([level for level in levels if level >= 0]), numpy.float32)
      posLevels = numpy.array(posLevels, numpy.float32)
      self.createDisplayLists(posLevels)
    else:
      posLevels = []
      
    #if self.negContoursVisible:
    if negLevels:
      ###negLevels = numpy.array(sorted([level for level in levels if level < 0], reverse=True), numpy.float32)
      negLevels = numpy.array(negLevels, numpy.float32)
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

    levels = list(self.contourDisplayIndexDict.keys()) # need to do it this way else deleting entries while iterating over dict
    for level in levels:
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
    apiSpectrumView = self.apiSpectrumView
    """ dimensionOrdering not working yet so for now hardwire
    xDim, yDim = apiSpectrumView.dimensionOrdering[:2]
    xDim -= 1  # dimensionOrdering starts at 1
    yDim -= 1
    """
    xDim = 0
    yDim = 1
    ###xDim = self.xDim
    ###yDim = self.yDim
    if dimensionCount == 2: # TBD
      # below does not work yet
      #planeData = spectrum.getPlaneData(xDim=xDim, yDim=yDim)
      planeData = LibSpectrum.getPlaneData(spectrum, xDim=xDim, yDim=yDim)
      position = [0, 0]
      yield position, planeData
    elif dimensionCount == 3: # TBD
      ###zDims = set(range(dimensionCount)) - {xDim, yDim}
      ###zDim = zDims.pop()
      zDim = apiSpectrumView.dimensionOrdering[2]
      zregionValue = self.guiSpectrumDisplay.region[zDim]
      zregionPoint = LibSpectrum.getDimPointFromValue(spectrum, zDim, zregionValue)
      zregionPoint = (int(numpy.round(zregionPoint[0])), int(numpy.round(zregionPoint[1])))
      position = dimensionCount * [0]
      for z in range(*zregionPoint):  # TBD
        position[zDim] = z
        # below does not work yet
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
    
    apiStrips = self.apiSpectrumView.strips
    apiStrip = apiStrips[0]
    guiStrip = apiStrip.guiStrip
    
    plotItem = guiStrip.plotItem
    viewBox = guiStrip.viewBox
    isX = (dim == self.xDim)  # assumes that xDim != yDim
    viewRegion = guiStrip.viewRange()
    if isX:
      region1, region0 = viewRegion[0]  # TBD: relies on axes being backwards
      pixelCount = guiStrip.width()
      pixelViewBox0 = plotItem.getAxis('left').width()
      pixelViewBox1 = pixelViewBox0 + viewBox.width()
    else:
      region1, region0 = viewRegion[1]  # TBD: relies on axes being backwards
      pixelCount = guiStrip.height()
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
        
    

