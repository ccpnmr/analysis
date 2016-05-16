"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

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

from PyQt4 import QtCore, QtGui

import pyqtgraph as pg

from ccpn.ui.gui.modules.GuiSpectrumView import GuiSpectrumView

from ccpn.util.Colour import spectrumColours
from ccpn.util import Phasing

class GuiSpectrumView1d(GuiSpectrumView):


  #def __init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping=None):
  def __init__(self):
    """ spectrumPane is the parent
        spectrum is the Spectrum name or object
        """
    """ old comment
        region is in units of parent, ordered by spectrum dimensions
        dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """
    #GuiSpectrumView.__init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping)

    GuiSpectrumView.__init__(self)

    # if self.spectrum.sliceColour is None:
    #   self.spectrum.sliceColour = list(spectrumColours.keys())[0]

    self.data = self._apiDataSource.get1dSpectrumData()

    # for strip in self.strips:
    if self.spectrum.sliceColour is None:
      if len(self.strip.spectrumViews) < 12:
        self.spectrum.sliceColour = list(spectrumColours.keys())[len(self.strip.spectrumViews)-1]
      else:
        self.spectrum.sliceColour = list(spectrumColours.keys())[(len(self.strip.spectrumViews) % 12)-1]

    # have to add in two steps because simple plot() command draws all other data even if currently not visible
    ##self.plot = self.strip.plotWidget.plot(self.data[0], self.data[1], pen=self.spectrum.sliceColour)
    self.plot = pg.PlotDataItem(x=self.data[0], y=self.data[1], pen=self.spectrum.sliceColour)
    self.strip.viewBox.addItem(self.plot)

    self.plot.curve.setClickable(True)
    self.plot.sigClicked.connect(self.clicked)
    for peakList in self.spectrum.peakLists:
      self.strip.showPeaks(peakList)
      
    self.hPhaseTrace = None

    # self.strip.viewBox.autoRange()
    # self.strip.zoomYAll()

  def turnOnPhasing(self):

    
    phasingFrame = self.strip.spectrumDisplay.phasingFrame
    if phasingFrame.isVisible():
      if self.hPhaseTrace:
        self.hPhaseTrace.setVisible(True)
      else:
        self.newPhasingTrace()
        
  def turnOffPhasing(self):

    if self.hPhaseTrace:
      self.hPhaseTrace.setVisible(False)
      
  def newPhasingTrace(self):
    
    phasingFrame = self.strip.spectrumDisplay.phasingFrame
    if phasingFrame.isVisible() and not self.hPhaseTrace:
      if not self.strip.haveSetHPhasingPivot:
        viewParams = self._getSpectrumViewParams(0)
        # valuePerPoint, pointCount, minAliasedFrequency, maxAliasedFrequency, dataDim = self._getSpectrumViewParams(0)
        self.strip.hPhasingPivot.setPos(0.5*(viewParams.minAliasedFrequency +
                                             viewParams.maxAliasedFrequency))
        self.strip.hPhasingPivot.setVisible(True)
        self.strip.haveSetHPhasingPivot = True
      trace = pg.PlotDataItem()
      self.strip.plotWidget.scene().addItem(trace)
      self.hPhaseTrace = trace
      self.updatePhasing()
            
  def removePhasingTraces(self):
    
    trace = self.hPhaseTrace
    if trace:
      self.strip.plotWidget.scene().removeItem(trace)
      self.hPhaseTrace = None
    
  def updatePhasing(self):
    if not self.isVisible():
      return
      
    trace = self.hPhaseTrace
    if not trace:
      return
      
    position = [axis.position for axis in self.strip.orderedAxes]
    
    phasingFrame = self.strip.spectrumDisplay.phasingFrame
    ph0 = phasingFrame.slider0.value() if phasingFrame.isVisible() else 0
    ph1 = phasingFrame.slider1.value() if phasingFrame.isVisible() else 0
      
    hPhasingPivot = self.strip.hPhasingPivot
    if hPhasingPivot.isVisible():
      dataDim = self._apiStripSpectrumView.spectrumView.orderedDataDims[0]
      pivot = dataDim.primaryDataDimRef.valueToPoint(hPhasingPivot.getXPos())
    else:
      pivot = 1
      
    positionPoint = QtCore.QPointF(position[0], 0.0)
    positionPixel = self.strip.viewBox.mapViewToScene(positionPoint)
    positionPixel = (positionPixel.x(), positionPixel.y())
    inRange, point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, = self._getTraceParams(position)        
    if inRange:
      self._updateHTraceData(point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, positionPixel, trace, ph0, ph1, pivot)
    
  def _getTraceParams(self, position):
    # position is in ppm (intensity in y)
        
    inRange = True
    point = []
    for n, pos in enumerate(position): # n = 0 is x, n = 1 is y, etc.
      if n != 1:
        valuePerPoint, totalPointCount, minAliasedFrequency, maxAliasedFrequency, dataDim = self._getSpectrumViewParams(n)
        if dataDim:
          if n == 0:
            xDataDim = dataDim
            # -1 below because points start at 1 in data model
            xMinFrequency = int(dataDim.primaryDataDimRef.valueToPoint(maxAliasedFrequency)-1)
            xMaxFrequency = int(dataDim.primaryDataDimRef.valueToPoint(minAliasedFrequency)-1)
            xNumPoints = totalPointCount
          else:
            inRange = (minAliasedFrequency <= pos <= maxAliasedFrequency)
            if not inRange:
              break
          pnt = (dataDim.primaryDataDimRef.valueToPoint(pos)-1) % totalPointCount
          pnt += (dataDim.pointOffset if hasattr(dataDim, "pointOffset") else 0)
          point.append(pnt)
        
    return inRange, point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints
    
  def _updateHTraceData(self, point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, positionPixel, hTrace, ph0=None, ph1=None, pivot=None):
    
    # unfortunately it looks like we have to work in pixels, not ppm, yuck
    strip = self.strip
    plotWidget = strip.plotWidget
    plotItem = plotWidget.plotItem
    viewBox = strip.viewBox
    viewRegion = plotWidget.viewRange()
    
    pointInt = [int(pnt+0.4999) for pnt in point]
    data = self.spectrum.getSliceData(pointInt, sliceDim=xDataDim.dim-1)
    if ph0 is not None and ph1 is not None and pivot is not None:
      data0 = numpy.array(data)
      data = Phasing.phaseRealData(data, ph0, ph1, pivot)
      data1 = numpy.array(data)
    x = numpy.array([xDataDim.primaryDataDimRef.pointToValue(p+1) for p in range(xMinFrequency, xMaxFrequency+1)])
    # scale from ppm to pixels
    pixelViewBox0 = plotItem.getAxis('left').width()
    pixelViewBox1 = pixelViewBox0 + viewBox.width()
    region1, region0 = viewRegion[0]
    x -= region0
    x *= (pixelViewBox1-pixelViewBox0) / (region1-region0)
    x += pixelViewBox0
  
    pixelViewBox1 = plotItem.getAxis('bottom').height()
    pixelViewBox0 = pixelViewBox1 + viewBox.height()
    
    yintensity0, yintensity1 = viewRegion[1]
    #v = positionPixel[1] - (pixelViewBox1-pixelViewBox0) * numpy.array([data[p % xNumPoints] for p in range(xMinFrequency, xMaxFrequency+1)])
    v = pixelViewBox0 + (pixelViewBox1-pixelViewBox0) * (numpy.array([data[p % xNumPoints] for p in range(xMinFrequency, xMaxFrequency+1)]) - yintensity0) / (yintensity1 - yintensity0)
  
    colour = '#e4e15b' if self._appBase.preferences.general.colourScheme == 'dark' else '#000000'
    hTrace.setPen({'color':colour})
    hTrace.setData(x, v)
      
  def clicked(self):
    print(self.plot)
    

  def getSliceData(self, spectrum=None):
    """
    Gets slice data for drawing 1d spectrum using specified spectrum.
    """
    if spectrum is None:
      apiDataSource = self._apiDataSource
    else:
      apiDataSource = spectrum._apiDataSource
    return apiDataSource.get1dSpectrumData()

  def update(self):
    self.plot.curve.setData(self.data[0], self.data[1])

