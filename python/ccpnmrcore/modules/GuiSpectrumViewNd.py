"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
import numpy

from OpenGL import GL
from PyQt4 import QtCore, QtGui

###from ccpncore.gui.ToolButton import ToolButton
from ccpncore.util import Colour

from ccpnc.contour import Contourer2d
###from ccpnc.peak import Peak

from ccpnmrcore.modules import GuiStripDisplayNd
from ccpnmrcore.modules.GuiSpectrumView import GuiSpectrumView
###from ccpnmrcore.modules.spectrumPane.PeakListNdItem import PeakListNdItem

# TBD: for now ignore fact that apiSpectrumView can override contour colour and/or contour levels

from ccpncore.memops import Notifiers

def _getLevels(count, base, factor):
  
  levels = []
  if count > 0:
    levels = [base]
    for n in range(count-1):
      levels.append(numpy.float32(factor * levels[-1]))

  return levels
       
class GuiSpectrumViewNd(GuiSpectrumView):
  
  ###PeakListItemClass = PeakListNdItem
  
  #sigClicked = QtCore.Signal(object, object)

  #def __init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping=None, region=None, **kw):
  def __init__(self):
    """ guiSpectrumDisplay is the parent
        apiSpectrumView is the (API) SpectrumView object
    """
    """ old comment
        region is in units of parent, ordered by spectrum dimensions
        dimMapping is from spectrum numerical dimensions to guiStrip numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """

    self.setAcceptedMouseButtons = QtCore.Qt.LeftButton

    #GuiSpectrumView.__init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping)
    self.posLevelsPrev = []
    self.negLevelsPrev = []
    self.xDataDimPrev = None
    self.yDataDimPrev = None
    self.zRegionPrev = None
    self.posDisplayLists = []
    self.negDisplayLists = []


    # self.spectralData = self.getSlices()
    
    ###xDim, yDim = apiSpectrumView.dimensionOrdering[:2]
    ###xDim -= 1  # dimensionOrdering starts at 1
    ###yDim -= 1

    # TBD: this is not correct
    ##apiDataSource = self.apiDataSource
    # I think this fixes it - number of DISPLAY axes, rather than dataSource axes. RHF
    # dimensionCount = apiDataSource.numDim
    dimensionCount = len(self.dimensionOrdering)
    self.previousRegion = dimensionCount * [None]

    #self.setZValue(-1)  # this is so that the contours are drawn on the bottom

    #self.contourDisplayIndexDict = {} # (xDim, yDim) -> level -> display list index
    

        
    apiDataSource = self.apiStripSpectrumView.spectrumView.dataSource
    if not self.positiveContourColour:
      apiDataSource.positiveContourColour = Colour.spectrumHexColours[self._parent._appBase.colourIndex]
      self._parent._appBase.colourIndex += 1
      self._parent._appBase.colourIndex %= len(Colour.spectrumHexColours)

    if not self.negativeContourColour:
    # Changed to guiSpectrumView.negativeContourColour, which picks up from either
    # SpectrumView or DataSource
      apiDataSource.negativeContourColour = Colour.spectrumHexColours[self._parent._appBase.colourIndex]
      self._parent._appBase.colourIndex += 1
      self._parent._appBase.colourIndex %= len(Colour.spectrumHexColours)

    GuiSpectrumView.__init__(self)

    self.setZValue(-1)  # this is so that the contours are drawn on the bottom

    """
    self.visibilityAction = action = self._parent.spectrumDisplay.spectrumToolBar.addAction(self.spectrum.name)
    self.setActionIconColour()
    action.setCheckable(True)
    action.setChecked(True)
    widget = self._parent.spectrumDisplay.spectrumToolBar.widgetForAction(action)
    widget.setFixedSize(60, 30)

    for func in ('setPositiveContourColour', 'setSliceColour'):
      Notifiers.registerNotify(self.changedSpectrumColour, 'ccp.nmr.Nmr.DataSource', func)
"""        
    # for strip in self.strips:
    self.addSpectrumItem(self.strip)


    # Notifiers.registerNotify(self.newPeakListView, 'ccpnmr.gui.Task.PeakListView', '__init__')
    #
    # spectrum = self.spectrum
    # strip = self.strip
    # for peakList in spectrum.peakLists:
    #   strip.showPeaks(peakList)

  """
  def changedSpectrumColour(self, apiDataSource):
    
    if apiDataSource is self.spectrum._wrappedData:
      self.setActionIconColour()
    
  def setActionIconColour(self):
    
    action = self.visibilityAction
    pix=QtGui.QPixmap(60, 10)
    if self.spectrum.dimensionCount < 2:
      pix.fill(QtGui.QColor(self.spectrum.sliceColour))
    else:
      pix.fill(QtGui.QColor(self.spectrum.positiveContourColour))
    action.setIcon(QtGui.QIcon(pix))
"""      
  def addSpectrumItem(self, strip):
    if self not in strip.plotWidget.scene().items():
      strip.plotWidget.scene().addItem(self)
    ###self.visibilityAction.toggled.connect(self.setVisible) # does this ever get set twice??
        
  def removeSpectrumItem(self, strip):
    if self in strip.plotWidget.scene().items():
      strip.plotWidget.scene().removeItem(self)

  ###def connectStrip(self, strip):
  ###  item = self.spectrumItems[strip]
  ###  self.spectrumViewButton.spaction.toggled.connect(item.setVisible)
  """
  def getLevels(self):
    
    levels = [self.baseLevel]
    for n in range(int(self.numberOfLevels-1)):
      levels.append(self.multiplier*levels[-1])
      
    return tuple(numpy.array(levels, dtype=numpy.float32))
"""

  def zPlaneSize(self):  # TBD: Do we need this still?
    
    spectrum = self.spectrum
    dimensionCount = spectrum.dimensionCount
    if dimensionCount < 3:
      return None  # TBD
      
    zDim = self.apiStripSpectrumView.spectrumView.orderedDataDims[2].dim - 1
    point = (0.0, 1.0)
    value = spectrum.getDimValueFromPoint(zDim, point)
    size = abs(value[1] - value[0])
    
    return size

  def newPeakListView(self, peakListView):
    pass
    
  ##### override of superclass function

  def paint(self, painter, option, widget=None):
    
    ##if not widget:
    ##  return

    ##guiStrip = self.spectrumDisplay.viewportDict[widget]
    ##self.drawContours(painter, guiStrip)
    # NBNB TBD this should NEVER be called if self.strip is None (i.e. self is deleted)
    # NBNB FIXME this needs to be fixed.

    if self.isVisible() and self.strip is not None:
      self.drawContours(painter)
    
  def boundingRect(self):  # seems necessary to have


    return QtCore.QRectF(-2000, -2000, 2000, 2000)  # TBD: remove hardwiring
  
  ##### functions not to be used externally #####
  # NBNB TBD internal functoins should start with UNDERSCORE!
  # REFACTOR

  #def drawContours(self, painter, guiStrip):
  def drawContours(self, painter):
    
    apiDataSource = self.apiDataSource
    if apiDataSource.positiveContourBase == 10000.0: # horrid
      # base has not yet been set, so guess a sensible value
      apiDataSource.positiveContourBase = apiDataSource.estimateNoise()
      apiDataSource.negativeContourBase = - apiDataSource.positiveContourBase
      
    if self._wrappedData.spectrumView.displayPositiveContours is True:
      posLevels = _getLevels(apiDataSource.positiveContourCount, apiDataSource.positiveContourBase, apiDataSource.positiveContourFactor)
    else:
      posLevels = []
    if self._wrappedData.spectrumView.displayNegativeContours is True:
      negLevels = _getLevels(apiDataSource.negativeContourCount, apiDataSource.negativeContourBase, apiDataSource.negativeContourFactor)
    else:
      negLevels = []
    if not posLevels and not negLevels:
      return
      
    #contourDict = self.constructContours(guiStrip, posLevels, negLevels)
    try:
      self.constructContours(posLevels, negLevels)
    except FileNotFoundError:
      self._project._logger.warning("No data file found for %s" % self)


    posColour = Colour.scaledRgba(apiDataSource.positiveContourColour) # TBD: for now assume only one colour
    negColour = Colour.scaledRgba(apiDataSource.negativeContourColour)

    painter.beginNativePainting()  # this puts OpenGL back in its default coordinate system instead of Qt one

    try:
      
      xyDataDims = self.apiStripSpectrumView.spectrumView.orderedDataDims[:2]
      xTranslate, xScale = self.getTranslateScale(xyDataDims[0].dim-1, 0) # -1 because API dims start at 1
      yTranslate, yScale = self.getTranslateScale(xyDataDims[1].dim-1, 1)
      
      GL.glLoadIdentity()
      GL.glPushMatrix()

      # the below is because the y axis goes from top to bottom
      GL.glScale(1.0, -1.0, 1.0)
      GL.glTranslate(0.0, -self.strip.plotWidget.height(), 0.0)
      
      # the below makes sure that spectrum points get mapped to screen pixels correctly
      GL.glTranslate(xTranslate, yTranslate, 0.0)
      GL.glScale(xScale, yScale, 1.0)
      
      for (colour, levels, displayLists) in ((posColour, posLevels, self.posDisplayLists), (negColour, negLevels, self.negDisplayLists)):
        for n, level in enumerate(levels):
          GL.glColor4f(*colour)
          # TBD: scaling, translating, etc.
          GL.glCallList(displayLists[n])
      GL.glPopMatrix()

    finally:
      
      painter.endNativePainting()
      
  #def constructContours(self, guiStrip, posLevels, negLevels):
  def constructContours(self, posLevels, negLevels):
    """ Construct the contours for this spectrum using an OpenGL display list
        The way this is done here, any change in contour level or color needs to call this function.
    """
    
    xDataDim, yDataDim = self.apiStripSpectrumView.spectrumView.orderedDataDims[:2]
    
    if xDataDim is not self.xDataDimPrev or yDataDim is not self.yDataDimPrev \
      or self.zRegionPrev != tuple([tuple(axis.region) for axis in self.strip.orderedAxes[2:]]):
      self.releaseDisplayLists(self.posDisplayLists)
      self.releaseDisplayLists(self.negDisplayLists)
      doPosLevels = doNegLevels = True
    else:
      if list(posLevels) == self.posLevelsPrev:
        doPosLevels = False
      else:
        self.releaseDisplayLists(self.posDisplayLists)
        doPosLevels = posLevels and True
      if list(negLevels) == self.negLevelsPrev:
        doNegLevels = False
      else:
        self.releaseDisplayLists(self.negDisplayLists)
        doNegLevels = negLevels and True
      
    ###self.previousRegion = self.guiSpectrumDisplay.region[:]  # TBD: not quite right, should be looking at the strip(s)
    
    # do the contouring and store results in display list
    if doPosLevels:
      posLevels = numpy.array(posLevels, numpy.float32)
      self.createDisplayLists(posLevels, self.posDisplayLists)
      
    if doNegLevels:
      negLevels = numpy.array(negLevels, numpy.float32)
      self.createDisplayLists(negLevels, self.negDisplayLists)
      
    if not doPosLevels and not doNegLevels:
      return
      
    ###GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    
    #for position, dataArray in self.getPlaneData(guiStrip):
    for position, dataArray in self.getPlaneData():
      
      if doPosLevels:
        posContours = Contourer2d.contourer2d(dataArray, posLevels)
        for n, contourData in enumerate(posContours):
          self.addContoursToDisplayList(self.posDisplayLists[n], contourData, posLevels[n])
        
      if doNegLevels:
        negContours = Contourer2d.contourer2d(dataArray, negLevels)
        for n, contourData in enumerate(negContours):
          self.addContoursToDisplayList(self.negDisplayLists[n], contourData, negLevels[n])
        
    ###GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
    
    self.posLevelsPrev = list(posLevels)
    self.negLevelsPrev = list(negLevels)
    self.xDataDimPrev = xDataDim
    self.yDataDimPrev = yDataDim
    self.zRegionPrev = tuple([tuple(axis.region) for axis in self.strip.orderedAxes[2:]])
    
  def releaseDisplayLists(self, displayLists):

    for displayList in displayLists:
      GL.glDeleteLists(displayList, 1)
    displayLists[:] = []

  def createDisplayLists(self, levels, displayLists):

    # could create them in one go but more likely to get fragmentation that way
    for level in levels:
      displayLists.append(GL.glGenLists(1))

  #def getPlaneData(self, guiStrip):
  def getPlaneData(self):
    
    strip = self.strip
    spectrum = self.spectrum
    dimensionCount = spectrum.dimensionCount
    apiStripSpectrumView = self.apiStripSpectrumView

    dataDims = apiStripSpectrumView.spectrumView.orderedDataDims
    xDim = dataDims[0].dim - 1  # -1 because dataDim.dim starts at 1
    yDim = dataDims[1].dim - 1
    if dimensionCount == 2: # TBD
      planeData = spectrum.getPlaneData(xDim=xDim, yDim=yDim)
      position = [0, 0]
      yield position, planeData
    elif dimensionCount == 3: # TBD
      apiStrip = strip.apiStrip
      zAxis = apiStrip.orderedAxes[2]
      position = zAxis.position
      width = zAxis.width
      zregionValue = (position+0.5*width, position-0.5*width) # Note + and - (axis backwards)
      zDim = dataDims[2].dim - 1
      zregionPoint = spectrum.getDimPointFromValue(zDim, zregionValue)
      zregionPoint = (int(numpy.round(zregionPoint[0])), int(numpy.round(zregionPoint[1])))
      strip.planeToolbar.planeLabel.setSingleStep(self.zPlaneSize())
      strip.planeToolbar.planeLabel.setMaximum(spectrum.getDimValueFromPoint(zDim, 1))
      strip.planeToolbar.planeLabel.setMinimum(spectrum.getDimValueFromPoint(zDim, spectrum.pointCounts[zDim]))
      strip.planeToolbar.planeLabel.setValue(position)
      position = dimensionCount * [0]
      for z in range(*zregionPoint):  # TBD
        position[zDim] = z
        planeData = spectrum.getPlaneData(position, xDim=xDim, yDim=yDim)
        yield position, planeData

  def addContoursToDisplayList(self, displayList, contourData, level):
    """ contourData is list of [NumPy array with ndim = 1 and size = twice number of points] """
    
    GL.glNewList(displayList, GL.GL_COMPILE)

    for contour in contourData:
      GL.glBegin(GL.GL_LINE_LOOP)
      n = len(contour) // 2
      contour = contour.reshape((n, 2))
      for (x, y) in contour:
        GL.glVertex2f(x,y)
      GL.glEnd()
    
    GL.glEndList()
    
  def getTranslateScale(self, dim, ind):
        
    strip = self.strip
    plotWidget = strip.plotWidget
    plotItem = plotWidget.plotItem
    viewBox = strip.viewBox
    viewRegion = plotWidget.viewRange()
    region1, region0 = viewRegion[ind]  # TBD: relies on axes being backwards

    if ind == 0:
      pixelCount = plotWidget.width()
      pixelViewBox0 = plotItem.getAxis('left').width()
      pixelViewBox1 = pixelViewBox0 + viewBox.width()
    else:
      pixelCount = plotWidget.height()
      pixelViewBox0 = plotItem.getAxis('bottom').height()
      pixelViewBox1 = pixelViewBox0 + viewBox.height()
    
    (firstPoint, lastPoint) = self.spectrum.getDimPointFromValue(dim, (region0, region1))

    scale = (pixelViewBox1-pixelViewBox0) / (lastPoint-firstPoint)
    translate = pixelViewBox0 - firstPoint * scale
    
    return translate, scale
  def _connectPeakLayerVisibility(self, peakLayer):
    apiDataSource = self._wrappedData.spectrumView.dataSource
    action = self.strip.spectrumDisplay.spectrumActionDict.get(apiDataSource)
    action.toggled.connect(peakLayer.setVisible) # TBD: need to undo this if peakLayer removed
