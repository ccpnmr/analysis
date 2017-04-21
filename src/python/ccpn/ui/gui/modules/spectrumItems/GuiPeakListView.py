"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:41 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Wayne Boucher $"

__date__ = "$Date: 2017-03-22 15:13:45 +0000 (Wed, March 22, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
from PyQt4 import QtCore, QtGui

# import pyqtgraph as pg

from ccpn.core.Project import Project
from ccpn.core.Peak import Peak
# from ccpn.core.NmrAtom import NmrAtom
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import AbstractPeakDimContrib as ApiAbstractPeakDimContrib
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Resonance as ApiResonance
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import ResonanceGroup as ApiResonanceGroup
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import NmrChain as ApiNmrChain
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakDim as ApiPeakDim
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Peak as ApiPeak
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import DataDimRef as ApiDataDimRef
# from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import FreqDataDim as ApiFreqDataDim

NULL_RECT = QtCore.QRectF()
IDENTITY = QtGui.QTransform()
IDENTITY.reset()
# class PeakLayer(QtGui.QGraphicsItem):
#
#   def __init__(self, scene):
#
#     QtGui.QGraphicsItem.__init__(self, scene=scene)
#
#     # self.glWidget = glWidget
#     self.peaks = {}
#     self.setFlag(QtGui.QGraphicsItem.ItemHasNoContents, True)
#
#
#   def boundingRect(self):
#
#     return NULL_RECT
#
#   def paint(self, painter, option, widget):

    # return
#
# def peakItemNotifier(project, apiPeak):
#   apiPeakListViews = apiPeak.PeakList.PeakListViews
#   for apiPeakListView in apiPeakListViews:
#     for apiStripPeakListView in apiPeakListView._apiStripPeakListViews:

def _getPeakAnnotation(peak):
  peakLabel = []
  for dimension in range(peak.peakList.spectrum.dimensionCount):
    pdNA = peak.dimensionNmrAtoms
    if len(pdNA[dimension]) == 0:
      if len(pdNA) == 1:
        peakLabel.append('1H')
      else:
        peakLabel.append('-')
    else:
      peakNmrResidues = [atom[0].nmrResidue.id for atom in pdNA if len(atom) != 0]
      if all(x==peakNmrResidues[0] for x in peakNmrResidues):
        for item in pdNA[dimension]:
          if len(peakLabel) > 0:
            peakLabel.append(item.name)
          else:
            peakLabel.append(item.pid.id)

      else:
        for item in pdNA[dimension]:
          label = item.nmrResidue.id+item.name
          peakLabel.append(label)

  text = ', '.join(peakLabel)
  return text

# @profile
# def _getPeakAnnotation(peak):
#
#   peakLabel = []
#   for dimension in range(peak.peakList.spectrum.dimensionCount):
#     if len(peak.dimensionNmrAtoms[dimension]) == 0:
#       if len(peak.dimensionNmrAtoms) == 1:
#         peakLabel.append('1H')
#       else:
#         peakLabel.append('-')
#     else:
#       peakNmrResidues = [atom[0].nmrResidue.id for atom in peak.dimensionNmrAtoms if len(atom) != 0]
#       if all(x==peakNmrResidues[0] for x in peakNmrResidues):
#         for item in peak.dimensionNmrAtoms[dimension]:
#           if len(peakLabel) > 0:
#             peakLabel.append(item.name)
#           else:
#             peakLabel.append(item.pid.id)
#
#       else:
#         for item in peak.dimensionNmrAtoms[dimension]:
#           label = item.nmrResidue.id+item.name
#           peakLabel.append(label)
#
#   text = ', '.join(peakLabel)
#   return text

class GuiPeakListView(QtGui.QGraphicsItem):

  def __init__(self):
    """ peakList is the CCPN wrapper object
    """

    strip = self.spectrumView.strip
    scene = strip.plotWidget.scene()
    QtGui.QGraphicsItem.__init__(self, scene=scene)
    ###self.strip = strip
    ###self.peakList = peakList
    self.peakItems = {}  # CCPN peak -> Qt peakItem
    self.setFlag(QtGui.QGraphicsItem.ItemHasNoContents, True)
    self.application = self.spectrumView.application

    strip.viewBox.addItem(self)
    ###self.parent = parent
    # self.displayed = True
    # self.symbolColour = None
    # self.symbolStyle = None
    # self.isSymbolDisplayed = True
    # self.textColour = None
    # self.isTextDisplayed = True
    # self.regionChanged()


  def _printToFile(self, printer):
    # CCPN INTERNAL - called in _printToFile method of GuiSpectrumViewNd

    # NOTE: only valid for ND so far

    if not self.isVisible():
      return
    
    width = printer.width
    height = printer.height
    xCount = printer.xCount
    yCount = printer.yCount
    scale = 0.01
    peakHalfSize = scale * max(width, height)
    strip = self.spectrumView.strip
    plotWidget = strip.plotWidget
    viewRegion = plotWidget.viewRange()
    # dataDims = self.spectrumView._wrappedData.spectrumView.orderedDataDims
    spectrumIndices = self.spectrumView._displayOrderSpectrumDimensionIndices
    xAxisIndex = spectrumIndices[0]
    yAxisIndex = spectrumIndices[1]

    x1, x0 = viewRegion[0]  # TBD: relies on axes being backwards
    xScale = width / (x1 - x0) / xCount
    xTranslate = printer.x0 - x0 * xScale

    y1, y0 = viewRegion[1]  # TBD: relies on axes being backwards
    yScale = height / (y1 - y0) / yCount
    yTranslate = printer.y0 - y0 * yScale

    for peak in self.peakList.peaks:
      if strip.peakIsInPlane(peak):
        # xPpm = xScale*peak.position[dataDims[0].dimensionIndex] + xTranslate
        # yPpm = yScale*peak.position[dataDims[1].dimensionIndex] + yTranslate
        xPpm = xScale*peak.position[xAxisIndex] + xTranslate
        yPpm = yScale*peak.position[yAxisIndex] + yTranslate
        a0 = xPpm - peakHalfSize
        b0 = height - (yPpm - peakHalfSize)
        a1 = xPpm + peakHalfSize
        b1 = height - (yPpm + peakHalfSize)
        printer.writeLine(a0, b0, a1, b1)
        printer.writeLine(a0, b1, a1, b0)

        text = _getPeakAnnotation(peak)
        if text:
          offset = 0.5 * peakHalfSize
          printer.writeText(text, a1+offset, b1-offset)

  def boundingRect(self):

    return NULL_RECT

  def paint(self, painter, option, widget):

    return

  # For notifiers - moved from core PeakListView
  def _createdPeakListView(self):
    spectrumView = self.spectrumView
    spectrum = spectrumView.spectrum
    # NBNB TBD FIXME we should get rid of this API-level access
    # But that requires refactoring the spectrumActionDict
    action = spectrumView.strip.spectrumDisplay.spectrumActionDict.get(spectrum._wrappedData)
    if action:
      action.toggled.connect(self.setVisible) # TBD: need to undo this if peakListView removed

    strip = spectrumView.strip
    for peakList in spectrum.peakLists:
      strip.showPeaks(peakList)

  # For notifiers - moved from core PeakListView
  def _deletedStripPeakListView(self):

    from ccpn.core.IntegralList import IntegralList

    if isinstance(self.peakList, IntegralList):
      return

    spectrumView = self.spectrumView
    strip = spectrumView.strip
    spectrumDisplay = strip.spectrumDisplay

    peakItemDict = spectrumDisplay.activePeakItemDict[self]
    peakItems = set(spectrumDisplay.inactivePeakItemDict[self])
    for apiPeak in peakItemDict:
      # NBNB TBD FIXME change to get rid of API peaks here
      peakItem = peakItemDict[apiPeak]
      peakItems.add(peakItem)

    scene = strip.plotWidget.scene()
    for peakItem in peakItems:
      scene.removeItem(peakItem.annotation)
      if spectrumDisplay.is1D:
        scene.removeItem(peakItem.symbol)
      scene.removeItem(peakItem)
    scene.removeItem(self)

    del spectrumDisplay.activePeakItemDict[self]
    del spectrumDisplay.inactivePeakItemDict[self]

  def _changedPeakListView(self):

    for peakItem in self.peakItems.values():
      if isinstance(peakItem, PeakNd):
        peakItem.annotation.setupPeakAnnotationItem(peakItem)

class Peak1d(QtGui.QGraphicsItem):
  """ A GraphicsItem that is not actually drawn itself,
  but is the parent of the peak symbol and peak annotation.
      TODO: Add hover effect for 1D peaks. """

  def __init__(self, peak, peakListView):


    scene = peakListView.spectrumView.strip.plotWidget.scene()
    QtGui.QGraphicsItem.__init__(self, parent=peakListView, scene=scene)

    self.application = peakListView.application

    self.peakHeight = peak.height
    self.peak = peak
    self.peakListView = peakListView
    self.dim = 0
    self.spectrum = peak.peakList.spectrum
    # self.spectrumView, spectrumMapping = self.spectrumWindow.getViewMapping(analysisSpectrum)
    # self.setZValue(10)
    self.screenPos = []
    # print(scene.itemsBoundingRect)

    self.annotation = Peak1dAnnotation(self, scene)
    self.setupPeakItem(peakListView, peak)
    self.press = True
    self.setAcceptHoverEvents(True)
    self.annotationScreenPos = []

    self.bbox = NULL_RECT

    self.setCacheMode(self.NoCache)
    self.setFlag(QtGui.QGraphicsItem.ItemHasNoContents, True)
    self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
    # self.scene().sigMouseClicked.connect(self.peakClicked)
    self.pointPos = peak.pointPosition
    self.ppm = peak.position[self.dim]

    self.height = self.peak.height
    if not self.height:
      height = self.peak._apiPeak.findFirstPeakIntensity(intensityType = 'height')
      if height:
        self.height = height.value
      else:
        self.height = 0
    #self.height *= self.spectrum.scale  # should not need this now
    #
    # # if peakDims[dim].numAliasing:
    # #   self.isAliased = True
    # # else:
    # #   self.isAliased = False
    # if self.ppm and self.height:
    #   self.setPos(self.ppm, self.height)

    # try:
    self.symbol = Peak1dSymbol(scene, self)
    # except AttributeError:
    #   return

    # group.addToGroup(self)
  # def peakClicked(self, event):
  #   print(self, 'click', event)

  def setupPeakItem(self, peakListView, peak):

    self.peakListView = peakListView
    self.peak = peak

    self.setSelected(peak in self.application.current.peaks)

    # dataDims = peakListView.spectrumView._wrappedData.spectrumView.orderedDataDims
    # xPpm = peak.position[dataDims[0].dimensionIndex]
    xAxisIndex = peakListView.spectrumView._displayOrderSpectrumDimensionIndices[0]
    xPpm = peak.position[xAxisIndex]
    self.setPos(xPpm, peak.height or 0)
    self.annotation.setupPeakAnnotation(self)
    peakListView.peakItems[self.peak] = self

  def mousePressEvent(self, event):
    self.press = True
    self.hover = True
    print('pressed', 'GuiPeakListView L 300')

  # def mousePressEvent(self, event):
  #
  #   if (event.button() == QtCore.Qt.LeftButton) and (
  #             event.modifiers() & QtCore.Qt.ControlModifier) and not (
  #             event.modifiers() & QtCore.Qt.ShiftModifier):
  #
  #     event.accept()
  #     self.scene.clearSelection()
  #     self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
  #     QtGui.QGraphicsSimpleTextItem.mousePressEvent(self, event)
  #     self.setSelected(True)
  #     print(self.peak)


  def boundingRect(self):
    return NULL_RECT


  def paint(self, painter, option, widget):

    return

class Peak1dAnnotation(QtGui.QGraphicsSimpleTextItem):
  """ A text annotation of a peak.
      The text rotation is currently always +-45 degrees (depending on peak height). """

  def __init__(self, peakItem, scene):

    QtGui.QGraphicsSimpleTextItem.__init__(self, scene=scene)

    self.application = QtCore.QCoreApplication.instance()._ccpnApplication

    self.setParentItem(peakItem)
    self.peakItem = peakItem # When exporting to e.g. PDF the parentItem is temporarily set to None, which means that there must be a separate link to the PeakItem.
    self.scene = scene
    self.peak = peakItem.peak
    font = self.font()
    font.setPointSize(10)
    self.setFont(font)
    # self.setCacheMode(self.DeviceCoordinateCache)
    self.setFlag(self.ItemIgnoresTransformations, True)
    # self.setFlag(self.ItemIsMovable, True)
    self.setFlag(self.ItemIsSelectable, True)
    # self.setFlag(self.ItemSendsScenePositionChanges, True)
    # if self.isSelected():
    #   print(self)
    self.colourScheme = peakItem.application.colourScheme
    # color.setRgbF(*self.peakItem.glWidget._hexToRgba(textColor))
    self.setColour()
    self.updatePos()
    self.setupPeakAnnotation(peakItem)


  def sceneEventFilter(self, watched, event):
    print(event)

  def mousePressEvent(self, event):
    super(Peak1dAnnotation, self).mousePressEvent(event)


    if event.button() == QtCore.Qt.LeftButton:

    # if (event.button() == QtCore.Qt.LeftButton) and (
    #           event.modifiers() & QtCore.Qt.ControlModifier) and not (
    #           event.modifiers() & QtCore.Qt.ShiftModifier):

      self.scene.clearSelection()
      self.setFlag(QtGui.QGraphicsSimpleTextItem.ItemIsMovable)
      QtGui.QGraphicsSimpleTextItem.mousePressEvent(self, event)
      self.setSelected(True)
      self.peakItem.setSelected(True)
      self.peakItem.application.current.peak = self.peak
      self.update()
      # print('selected:', self.peak)

      # print('peak item:', self.peakItem.pos())


  def setupPeakAnnotation(self, peakItem):
    self.peakItem = peakItem # When exporting to e.g. PDF the parentItem is temporarily set to None, which means that there must be a separate link to the PeakItem.
    self.setParentItem(peakItem)


    peak = peakItem.peak
    spectrumId = peakItem.peak.peakList.spectrum.id

    # NBNB TBD FIXME

    text = _getPeakAnnotation(peak)
    # text = text + "*"
    text = spectrumId
    self.setText(text)

  def updatePos(self):

    peakItem = self.peakItem
    if peakItem.peakHeight and peakItem.peakHeight > 0:
      # Translate first to rotate around bottom left corner
      self.translate(0, -self.boundingRect().height())
      self.setRotation(0)
      #self.setPos(0, min(peakItem.pos().y()*0.75, peakItem.spectrum.positiveContourBase * peakItem.spectrum.scale))
      self.setPos(0, min(peakItem.pos().y()*0.75, peakItem.spectrum.positiveContourBase))
      # print(peakItem.height, max(peakItem.pos().y()*0.75, peakItem.spectrum.positiveContourBase * peakItem.spectrum.scale))
    else:
      #self.setPos(0, min(peakItem.pos().y()*0.75, -peakItem.spectrum.positiveContourBase * peakItem.spectrum.scale))
      self.setPos(0, min(peakItem.pos().y()*0.75, -peakItem.spectrum.positiveContourBase))
      self.setRotation(45)

  def setColour(self):
    if self.colourScheme == 'light':
      colour = QtGui.QColor('#080000')
    else:
      colour = QtGui.QColor('#f7ffff')
    self.setBrush(colour)
    textColor = colour

  def paint(self, painter, option, widget):

    if self.peak: # TBD: is this ever not true??
      self.setSelected(self.peak in self.application.current.peaks)
      # self.setSelected(self.peak.isSelected)
    QtGui.QGraphicsSimpleTextItem.paint(self, painter, option, widget)

    # if self.peakItem.peak in self.analysisLayout.currentPeaks:
    # painter.drawRect(self.boundingRect())

class Peak1dSymbol(QtGui.QGraphicsItem):
  """ A graphical symbol representing the peak.
      Currently only a dashed line from the peak to the peak annotation is used. This can be improved.
      The length of the line is related to the height of the peak. """

  def __init__(self, scene, parent):

    QtGui.QGraphicsItem.__init__(self, scene=scene)



    self.setParentItem(parent)
    self.peakItem = parent
    self.setCacheMode(self.DeviceCoordinateCache)
    # self.setFlag(self.ItemIsMovable, True)
    # self.setFlag(self.ItemIsSelectable, True)
    self.lineWidth = 0
    self.setPos(0, 0)
    self.setBbox()
    self.update()

  def boundingRect(self):

    return self.bbox

  def setBbox(self):

    peakItem = self.peakItem


    if self.pos().x() < peakItem.annotation.pos().x():
      left = self.pos().x()
      right = peakItem.annotation.pos().x()
    else:
      left = peakItem.annotation.pos().x()
      right = self.pos().x()

    if self.pos().y() < peakItem.annotation.pos().y():
      upper = self.pos().y()
      lower = peakItem.annotation.pos().y()
    else:
      upper = peakItem.annotation.pos().y()
      lower = self.pos().y()
    self.bbox = QtCore.QRectF(QtCore.QPointF(left, upper), QtCore.QPointF(right, lower))

  def paint(self, painter, option, widget):

    peakItem = self.peakItem


    pos = QtCore.QPointF(0, 0) # When exporting to e.g. pdf the symbol has no parent item, which means that its position is its screen pos.
                               # To compensate for that the line pos needs to be explicitly (0, 0).
    if self.parentItem():
      annotationPos = peakItem.annotation.pos()
    else:
      annotationPos = peakItem.annotation.scenePos() - self.scenePos() - QtCore.QPointF(5, 5) # Fix for export to e.g. PDF

    pen = painter.pen()
    pen.setStyle(QtCore.Qt.DashLine)
    pen.setWidth(self.lineWidth)
    self.colourScheme = peakItem.application.colourScheme
    if self.colourScheme == 'light':
      colour = QtGui.QColor('#080000')
    else:
      colour = QtGui.QColor('#f7ffff')

    # self.setBrush(colour)
    # lineColor = peakItem.analysisPeakList.symbolColor
    # color.setRgbF(*peakItem.glWidget._hexToRgba(lineColor))
    #
    # if peakItem.peak not in self.analysisLayout.currentPeaks:
    #   color.setAlphaF(0.5)

    pen.setColor(colour)
    painter.setPen(pen)

    painter.drawLine(pos, annotationPos)

    self.setBbox()

  def mousePressEvent(self, event):
    # print('symbol')
    if (event.button() == QtCore.Qt.LeftButton) and (
              event.modifiers() & QtCore.Qt.ControlModifier) and not (
              event.modifiers() & QtCore.Qt.ShiftModifier):

      event.accept()
      # self.scene.clearSelection()
      self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
      QtGui.QGraphicsSimpleTextItem.mousePressEvent(self, event)
      self.setSelected(True)
      self.update()



class PeakNd(QtGui.QGraphicsItem):

  def __init__(self, peakListView, peak):

    self.application = peakListView.application
    scene = peakListView.spectrumView.strip.plotWidget.scene()
    #QtGui.QGraphicsItem.__init__(self, scene=scene)
    self.colourScheme =self.application.colourScheme
    QtGui.QGraphicsItem.__init__(self, parent=peakListView, scene=scene)
    ###QtGui.QGraphicsItem.__init__(self, peakLayer)
    ###scene.addItem(self)
    ###strip.plotWidget.plotItem.vb.addItem(self)
    # turn off ItemIsSelectable because it fails miserably when you zoom in (have to pick exactly in the centre)
    ###self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable + self.ItemIgnoresTransformations)
    self.setFlag(self.ItemIgnoresTransformations)
    self.peakListView = peakListView
    self.annotation = PeakNdAnnotation(self, scene)
    self.setupPeakItem(peakListView, peak)
    # self.glWidget = peakLayer.glWidget
    #self.setParentItem(peakLayer)
    ###self.peakLayer = peakLayer
    # self.spectrumWindow = spectrumWindow
    # self.panel = spectrumWindow.panel
    #self.peakList = peak._parent
    ##self.strip = strip
    #self.parent = strip.plotWidget
    #self.spectrum = self.peakList.spectrum
    #self.setCacheMode(self.NoCache)
    #self.setFlags(self.ItemIgnoresTransformations)
    # self.setSelected(False)
    #self.hover = False
    #self.press = False
    #self.setAcceptHoverEvents(True)
    #self.bbox  = NULL_RECT
    #self.color = NULL_COLOR
    #self.brush = NULL_COLOR
    ###self.peak = peak
    ###xPpm = peak.position[0]
    ###yPpm = peak.position[1]
    # self.setPos(self.parent.viewBox.mapSceneToView
    sz = peakListView.spectrumView.strip.viewBox.peakWidthPixels
    hz = sz/2.0
    # self.bbox = QtCore.QRectF(-hz, -hz, sz, sz)
    # self.drawData = (hz, sz, QtCore.QRectF(-hz, -hz, sz, sz))
    """
    self.rectItem = QtGui.QGraphicsRectItem(-hz, -hz, sz, sz, self.peakLayer, scene)
    color = QtGui.QColor('cyan')
    self.rectItem.setBrush(QtGui.QBrush(color))
    """
    self.drawData = (hz, sz)#, QtCore.QRectF(-hz, -hz, sz, sz))
    ###xDim = strip.spectrumViews[0].dimensionOrdering[0] - 1
    ###yDim = strip.spectrumViews[0].dimensionOrdering[1] - 1
    ###xPpm = peak.position[xDim] # TBD: does a peak have to have a position??
    ###yPpm = peak.position[yDim]
    ###self.setPos(xPpm, yPpm)
    # self.inPlane = self.isInPlane()

    # from ccpn.ui.gui.widgets.Action import Action
    # self.deleteAction = QtGui.QAction(self, triggered=self.deletePeak, shortcut=QtCore.Qt.Key_Delete)
    #peakLayer.peakItems.append(self)
  #

  def setupPeakItem(self, peakListView, peak):

    self.peakListView = peakListView
    self.peak = peak
    if not hasattr(peak, '_isSelected'):
      peak._isSelected = False

    spectrumIndices = peakListView.spectrumView._displayOrderSpectrumDimensionIndices
    xAxisIndex = spectrumIndices[0]
    yAxisIndex = spectrumIndices[1]
    xPpm = peak.position[xAxisIndex]
    yPpm = peak.position[yAxisIndex]
    # dataDims = peakListView.spectrumView._wrappedData.spectrumView.orderedDataDims
    # xPpm = peak.position[dataDims[0].dimensionIndex]
    # yPpm = peak.position[dataDims[1].dimensionIndex]
    self.setPos(xPpm, yPpm)
    self.annotation.setupPeakAnnotationItem(self)
    peakListView.peakItems[self.peak] = self

    self._stripRegionUpdated()

  def _stripRegionUpdated(self):
    """CCPN internal, used in GuiStrip._axisRegionChanged()"""

    strip = self.peakListView.spectrumView.strip
    self._isInPlane = strip.peakIsInPlane(self.peak)
    if not self._isInPlane:
      self._isInFlankingPlane = strip.peakIsInFlankingPlane(self.peak)

  # replaced by Strip.peakIsInPlane
  # def isInPlane(self):
  #
  #   orderedAxes = self.peakListView.spectrumView.strip.orderedAxes
  #   for ii,zDataDim in enumerate(self.peakListView._wrappedData.spectrumView.orderedDataDims[2:]):
  #     zPosition = self.peak.position[zDataDim.dimensionIndex]
  #     zPlaneSize = zDataDim.getDefaultPlaneSize()
  #     zRegion = orderedAxes[2+ii].region
  #     if zPosition < zRegion[0]-zPlaneSize or zPosition > zRegion[1]+zPlaneSize:
  #       return False
  #   #
  #   return True

    # strip = self.peakListView.spectrumView.strip
    #
    # if len(strip.orderedAxes) > 2:
    #   zDim = strip.spectrumViews[0].dimensionOrdering[2] - 1
    #   zPlaneSize = strip.spectrumViews[0].zPlaneSize()
    #   zPosition = self.peak.position[zDim]
    #
    #   zRegion = strip.orderedAxes[2].region
    #   if zRegion[0]-zPlaneSize <= zPosition <= zRegion[1]+zPlaneSize:
    #     return True
    #   else:
    #     return False
    # else:
    #   return True

  # def hoverEnterEvent(self, event):
  #
  #   self.hover = True
  #   self.annotation.hoverEnterEvent(event)
  #   self.update()
  #
  # def hoverLeaveEvent(self, event):
  #
  #   self.hover = False
  #   self.press = False
  #   r, w, box = self.drawData
  #   self.bbox = box
  #   self.peakLayer.hideIcons()
  #   self.annotation.hoverLeaveEvent(event)
  #   self.update()

  ###def mousePressEvent(self, event):

    ###print(event)
    # self.setSelected(True)
    # self.press = True
    # self.hover = True
    ###r, w, box = self.drawData
    ###self.bbox = box.adjusted(-26,-51, 2, 51)
    # # self.peakLayer.showIcons(self)
    # self.update()
    # QtGui.QGraphicsItem.mousePressEvent(self, event)


  def boundingRect(self):

    ###return self.bbox # .adjust(-2,-2, 2, 2)

    r, w  = self.drawData

    return QtCore.QRectF(-r,-r,2*r,2*r)

  """
  def itemChange(self, change, value):

    if change == QtGui.QGraphicsItem.ItemSelectedHasChanged:
      peak = self.peak
      selected = peak.isSelected = self.isSelected()
      current = self.application.current
      if selected:
        if peak not in current.peaks:
          current.addPeak(peak)
      else:
        if peak in current.peaks:
          current.removePeak(peak)

    return QtGui.QGraphicsItem.itemChange(self, change, value)
"""
  #@profile
  def paint(self, painter, option, widget):
    if self.peakListView.isDeleted: # strip has been deleted
      return

    if self.peak: # TBD: is this ever not true??

      if self.peak.isDeleted:
        return

      ###self.setSelected(self.peak in self.application.current.peaks)
      # self.setSelected(self.peak.isSelected) # need this because dragging region to select peaks sets peak.isSelected but not self.isSelected()
      if self._isInPlane:
        # do not ever do the below in paint(), see comment at setupPeakAnnotationItem()
        ###self.annotation.setupPeakAnnotationItem(self)
        # r, w, box = self.drawData
        r, w = self.drawData

        # if self.hover:
        # self.setZValue(10)
        #painter.setBrush(NULL_COLOR)

        # painter.setPen(QtGui.QColor('white'))
        # if self.press:
        #   painter.drawRect(self.bbox)
        ###strip = self.strip
        ###peak = self.peak
        ###xDim = strip.spectrumViews[0].dimensionOrdering[0] - 1
        ###yDim = strip.spectrumViews[0].dimensionOrdering[1] - 1
        ###xPpm = peak.position[xDim] # TBD: does a peak have to have a position??
        ###yPpm = peak.position[yDim]
        ###self.setPos(xPpm, yPpm)
        colour = self.peakListView.symbolColour
        if widget:
          painter.setPen(QtGui.QColor(colour))
          # if self.colourScheme == 'light':
          #   painter.setPen(QtGui.QColor('#080000'))
          # else:
          #   painter.setPen(QtGui.QColor('#f7ffff'))
        else:
          painter.setPen(QtGui.QColor('black'))
        # painter.drawEllipse(box)

        # else:
        #   painter.setPen(self.color)
        #   self.setZValue(0)
        painter.drawLine(-r,-r,r,r)
        painter.drawLine(-r,r,r,-r)
        ###painter.drawLine(xPpm-r,yPpm-r,xPpm+r,yPpm+r)
        ###painter.drawLine(xPpm-r,yPpm+r,xPpm+r,yPpm-r)

        #if self.peak in self.application.current.peaks:
        if self.peak._isSelected:
          painter.drawLine(-r,-r,-r,r)
          painter.drawLine(-r,r,r,r)
          painter.drawLine(r,r,r,-r)
          painter.drawLine(r,-r,-r,-r)
        #
        # if self.isSelected:
        #   painter.setPen(QtGui.QColor('white'))
        #   painter.drawRect(-r,-r,w,w)

      elif self._isInFlankingPlane:
        colour = self.peakListView.symbolColour
        pen = QtGui.QPen(QtGui.QColor(colour))
        pen.setStyle(QtCore.Qt.DotLine)
        painter.setPen(pen)
        # do not ever do the below in paint(), see comment at setupPeakAnnotationItem()
        ###self.annotation.setupPeakAnnotationItem(self)
        r, w = self.drawData

        painter.drawLine(-r,-r,r,r)
        painter.drawLine(-r,r,r,-r)

        #if self.peak in self.application.current.peaks:
        if self.peak._isSelected:
          painter.drawLine(-r,-r,-r,r)
          painter.drawLine(-r,r,r,r)
          painter.drawLine(r,r,r,-r)
          painter.drawLine(r,-r,-r,-r)


###FONT = QtGui.QFont("DejaVu Sans Mono", 9)
###FONT_METRIC = QtGui.QFontMetricsF(FONT)
###NULL_COLOR = QtGui.QColor()
###NULL_RECT = QtCore.QRectF()

class PeakNdAnnotation(QtGui.QGraphicsSimpleTextItem):
  """ A text annotation of a peak.
      The text rotation is currently always +-45 degrees (depending on peak height). """

  def __init__(self, peakItem, scene):

    QtGui.QGraphicsSimpleTextItem.__init__(self, scene=scene)

    ###self.setParentItem(peakItem)
    ###self.peakItem = peakItem # When exporting to e.g. PDF the parentItem is temporarily set to None, which means that there must be a separate link to the PeakItem.
    ###self.setText(text)
    ###self.scene = scene
    ###self.setColor()
    # self.analysisLayout = parent.glWidget.analysisLayout
    font = self.font()
    font.setPointSize(10)
    self.setFont(font)
    # self.setCacheMode(self.DeviceCoordinateCache)
    self.setFlag(self.ItemIgnoresTransformations)#+self.ItemIsMovable+self.ItemIsSelectable)
    # self.setFlag(self.ItemSendsScenePositionChanges, True)

    # self.text = (' , ').join('-' * peakItem.peak.peakList.spectrum.dimensionCount)
    # if self.isSelected():
    #   print(self)
    self.colourScheme = peakItem.peakListView.spectrumView.application.colourScheme
    colour = peakItem.peakListView.textColour
    # if self.colourScheme == 'light':
    #   colour = QtGui.QColor('#080000')
    # else:
    #   colour = QtGui.QColor('#f7ffff')
    self.setBrush(QtGui.QColor(colour))
    ###self.setColor()
    self.setPos(15, -15)
    # self.updatePos()

  # @profile
  # should not ever call setupPeakAnnotationItem in paint()
  # instead make sure that you have appropriate notifiers call _refreshPeakAnnotation()
  def setupPeakAnnotationItem(self, peakItem):

    self.peakItem = peakItem # When exporting to e.g. PDF the parentItem is temporarily set to None, which means that there must be a separate link to the PeakItem.
    self.setParentItem(peakItem)
    colour = peakItem.peakListView.textColour
    self.setBrush(QtGui.QColor(colour))
    text = _getPeakAnnotation(peakItem.peak)

    self.setText(text)
  
  def mousePressEvent(self, event):


    if (event.button() == QtCore.Qt.LeftButton):# and (
              # event.modifiers() & QtCore.Qt.ControlModifier) and not (
              # event.modifiers() & QtCore.Qt.ShiftModifier):
      event.accept()
      # self.scene.clearSelection()
      # self.setFlag(QtGui.QGraphicsSimpleTextItem.ItemIsMovable)
      # QtGui.QGraphicsSimpleTextItem.mousePressEvent(self, event)
      # self.setSelected(True)
      # print(self.peakItem)
      # self.update()

# Notifiers for assignment annotation change
# Needed for:
# AbstractPeakDimContrib init and delete
# Resonance.setImplName, setResonanceGroup
# ResonanceGroup.setResonances, .setAssignedResidue, .setSequenceCode, .setResidueType
#   .setNmrChain
# NmrChain.setCode - NOT setResonanceGroups, as this calls setNmrChain on the other side.

def _refreshPeakAnnotation(peak:Peak):
  for peakListView in peak.peakList.peakListViews:
      peakItem = peakListView.peakItems.get(peak)
      if peakItem:
        peakItem.annotation.setupPeakAnnotationItem(peakItem)

Peak._refreshPeakAnnotation = _refreshPeakAnnotation

def _updateAssignmentsNmrAtom(nmrAtom, oldPid:str):
  """Update Peak assignments when NmrAtom is reassigned"""
  for peak in nmrAtom.assignedPeaks:
    peak._refreshPeakAnnotation()

# NB We could replace this with something like the following line,
# But that would trigger _refreshPeakAnnotation also when the position changes
# Better to keep it like this.
# Peak.setupCoreNotifier('change', _refreshPeakAnnotation)
def _upDateAssignmentsPeakDimContrib(project:Project,
                                     apiPeakDimContrib:Nmr.AbstractPeakDimContrib):
  peak = project._data2Obj[apiPeakDimContrib.peakDim.peak]
  peak._refreshPeakAnnotation()


# NB, This will be triggered whenever anything about the peak (assignment or position) changes
def _refreshPeakPosition(peak:Peak):
  for peakListView in peak.peakList.peakListViews:
    peakItem = peakListView.peakItems.get(peak)
    if peakItem:
      spectrumIndices = peakListView.spectrumView._displayOrderSpectrumDimensionIndices
      xAxisIndex = spectrumIndices[0]
      yAxisIndex = spectrumIndices[1]
      # dataDims = peakListView.spectrumView._wrappedData.spectrumView.orderedDataDims
      # xPpm = peak.position[dataDims[0].dimensionIndex]
      xPpm = peak.position[xAxisIndex]
      if peakListView.spectrumView.spectrum.dimensionCount > 1:
        # yPpm = peak.position[dataDims[1].dimensionIndex]
        yPpm = peak.position[yAxisIndex]
        peakItem.setPos(xPpm, yPpm)
      else:
        peakItem.setPos(xPpm, peak.height or 0)
Peak._refreshPeakPosition = _refreshPeakPosition
