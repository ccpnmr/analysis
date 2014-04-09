from ccpnmrcore.modules.spectrumPane.SpectrumItem import SpectrumItem

class SpectrumNdItem(SpectrumItem):

  def __init__(self, parent, spectrumVar, region=None, dimMapping=None):
    """ spectrumPane is the parent
        spectrumVar is the Spectrum name or object
        region is in units of parent, ordered by spectrum dimensions
        dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """

    SpectrumItem.__init__(self, parent, spectrumVar, region, dimMapping):
    
    self.posContoursVisible = True # this block of code TEMP
    self.negContoursVisible = True
    self.levels = (100000.0, -50000.0)
    self.posColors = (Color('#ff0000').rgba(),)
    self.negColors = (Color('#0000ff').rgba(),)
    
    self.contoursValid = False
    self.contourDisplayIndexDict = {} # level -> display list index
    
  # implements superclass function
  def drawSpectrum(self, painter, rect):
    
    self.constructContours()
    
    posColors = self.posColors
    posColorsCount = len(posColors)
    negColors = self.negColors
    negColorsCount = len(negColors)
    
    levels = self.levels
    posLevels = sorted([level for level in levels if level >= 0])
    negLevels = sorted([level for level in levels if level < 0], reverse=True)
    
    for level in posLevels:
      color = posColors()
    
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
      
    self.createDisplayLists(levels)
      
    # do the contouring and store results in display list
    posLevels = numpy.array(sorted([level for level in levels if level >= 0]), numpy.float32)
    negLevels = numpy.array(sorted([level for level in levels if level < 0], reverse=True), numpy.float32)

    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    
    for dataArray in self.getPlaneData():
      
      if posLevels:
        posContours = contourer2d(data, posLevels)
        for n, contourData in enumerate(posContours):
          self.addContoursToDisplayList(contourData, posLevels[n])
        
      if negLevels:
        negContours = contourer2d(data, negLevels)
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
    
    region = self.region
    
  def addContoursToDisplayList(self, contourData, level):
  """ contourData is list of [NumPy array with ndim = 1 and size = twice number of points] """
    
    GL.glNewList(self.contourDisplayIndexDict[level], GL.GL_COMPILE)
    
    for contour in contourData:
      GL.glVertexPointer(2, GL.GL_FLOAT, 0, contour)
      GL.glDrawArrays(GL.GL_LINE_LOOP, 0, len(contour)/2)
      
    GL.glEndList()
