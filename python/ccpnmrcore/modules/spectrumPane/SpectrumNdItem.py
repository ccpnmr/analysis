import numpy

from OpenGL import GL

from ccpncore.util.Color import Color

from ccpnmrcore.modules.spectrumPane.SpectrumItem import SpectrumItem

from ccpnc.contour import Contourer2d

from ccpn.lib import Spectrum as LibSpectrum  # TEMP (should be direct function call on spectrum object some day)

class SpectrumNdItem(SpectrumItem):

  def __init__(self, parent, spectrumVar, region=None, dimMapping=None):
    """ spectrumPane is the parent
        spectrumVar is the Spectrum name or object
        region is in units of parent, ordered by spectrum dimensions
        dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """

    self.spectrum = spectrumVar  # TEMP
    
    pointCount = spectrumVar.pointCount # this block of code TEMP
    region = [(0, pointCount[0]), (0, pointCount[1])]
    for i in range(2, len(pointCount)):
      n = pointCount[i] // 2
      region.append((n, n+1))
      
    dimMapping = {} # this block of code TEMP
    for i in range(len(pointCount)):
      dimMapping[i] = i
              
    SpectrumItem.__init__(self, parent, spectrumVar, region, dimMapping)
    
    self.posContoursVisible = True # this block of code TEMP
    self.negContoursVisible = True
    self.levels = (1000000.0, 500000.0, 200000.0)
    self.posColors = (Color('#ff0000').rgba(),)
    self.negColors = (Color('#0000ff').rgba(),)
    
    self.contoursValid = False
    self.contourDisplayIndexDict = {} # level -> display list index
    
  # implements superclass function
  def drawContours(self, painter, rect):
    
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
      
      GL.glLoadIdentity()
      GL.glPushMatrix()
      GL.glClearColor(1.0, 1.0, 1.0, 1.0)
      GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    
      colorsLevels = []
      for (colors, levels) in ((posColors, posLevels), (negColors, negLevels)):
        count = len(colors)
        for n, level in enumerate(levels):
          color = colors[n % count]
          GL.glColor4f(*color)
          # TBD: scaling, translating, etc.
          GL.glCallList(self.contourDisplayIndexDict[level])
      """
      GL.glColor4f(1.0, 0.0, 0.0, 0.5)
      GL.glBegin(GL.GL_LINES)
      GL.glVertex2f(0, 0)
      GL.glVertex2f(0.8, 0.8)
      GL.glVertex2f(0.5, 0.75)
      GL.glVertex2f(0.75, 0.5)
      GL.glVertex2f(0, 0)
      GL.glVertex2f(-1, 1)
      GL.glEnd()
"""
      GL.glPopMatrix()

    finally:
      
      painter.endNativePainting()
    
  ##### functions not to be used externally #####
  
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

  def createDisplayLists(self, levels):

    # could create them in one go but more likely to get fragmentation that way
    for level in levels:
      self.contourDisplayIndexDict[level] = GL.glGenLists(1)
    
  def getPlaneData(self):
    
    spectrum = self.spectrum
    xDim = self.xDim
    yDim = self.yDim
    region = self.region # TBD: in ppm not points, assume in points for now
    if spectrum.dimensionCount == 2: # TBD
      # below does not work yet
      #planeData = spectrum.getPlaneData(xDim=xDim, yDim=yDim)
      planeData = LibSpectrum.getPlaneData(spectrum, xDim=xDim, yDim=yDim)
      position = [0, 0]
      yield position, planeData
    elif spectrum.dimensionCount == 3: # TBD
      # below does not work yet
      #planeData = spectrum.getPlaneData(xDim=xDim, yDim=yDim)
      planeData = LibSpectrum.getPlaneData(spectrum, xDim=xDim, yDim=yDim)
      for z in range(*(region[2])):  # TBD
        position = [0, 0, z]  # TBD
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
