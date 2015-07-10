"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
from PyQt4 import QtCore, QtGui

import pyqtgraph as pg

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

class GuiPeakListView(QtGui.QGraphicsItem):

  def __init__(self, scene, strip, peakList):
    """ peakList is the CCPN wrapper object
    """

    QtGui.QGraphicsItem.__init__(self, scene=scene)
    self.strip = strip
    self.peakList = peakList
    self.peakItems = {}  # CCPN peak -> Qt peakItem
    self.setFlag(QtGui.QGraphicsItem.ItemHasNoContents, True)
    self._appBase = strip._appBase
    ###self.parent = parent
    # self.displayed = True
    # self.symbolColour = None
    # self.symbolStyle = None
    # self.isSymbolDisplayed = True
    # self.textColour = None
    # self.isTextDisplayed = True
    # self.regionChanged()

  # def showIcons(self, peakItem):
  #
  #   self.assignIcon.syncPeak(peakItem)
  #   self.deleteIcon.syncPeak(peakItem)
  #   self.moveIcon.syncPeak(peakItem)
  #   self.cleanIcon.syncPeak(peakItem)
  #   self.menuIcon.syncPeak(peakItem)
  #
  # def hideIcons(self):
  #
  #   self.assignIcon.hide()
  #   self.deleteIcon.hide()
  #   self.moveIcon.hide()
  #   self.cleanIcon.hide()
  #   self.menuIcon.hide()

  def regionChanged(self):

    parent = self.parent
    xValRange = parent.orderedAxes[0].region
    yValRange = parent.orderedAxes[1].region

    xr1, xr2 = xValRange
    yr1, yr2 = yValRange

    dx = xr1-xr2
    dy = yr1-yr2

    w, h, = self.parent.geometry()[:2]

    self.setTransform(IDENTITY)
    self.scale(-w/dx, h/dy)

    xPos = w * xr1/dx
    yPos = h - (h * yr1/dy)

    inverse, isOk = self.transform().inverted()

    self.setPos(xPos, yPos)

    # for peak in peakList.peaks:
    #   peakItem = Peak1d(scene, parent, peak, peakList)
    #   peakItem.setParentItem(self)
      # scene.addItem(peakItem)
      # self.addToGroup(peakItem)
    # print(self)

  # def createPeakItems(self):
  #   for peak in self.peakList.peaks:
  #     print(peak, peak.pid)
  #     self.peakItems[peak.pid] = PeakItem(self, peak)
  def boundingRect(self):

    return NULL_RECT


  def paint(self, painter, option, widget):

    return

class Peak1d(QtGui.QGraphicsItem):
  """ A GraphicsItem that is not actually drawn itself, but is the parent of the peak symbol and peak annotation.
      TODO: Add hover effect for 1D peaks. """

  def __init__(self, scene, parent, peak, peakList):

    QtGui.QGraphicsItem.__init__(self, scene=scene)

    self.parent = parent
    self.peak = peak
    self.peakList = peakList
    self.spectrum = peakList.spectrum
    self.dim = 0
    self.spectrumDisplay = parent
    # self.spectrumView, spectrumMapping = self.spectrumWindow.getViewMapping(analysisSpectrum)
    # self.setZValue(10)
    self.screenPos = []
    self.press = False
    self.setAcceptHoverEvents(True)
    self.annotationScreenPos = []
    self.bbox  = NULL_RECT
    self.setCacheMode(self.NoCache)
    self.setFlag(QtGui.QGraphicsItem.ItemHasNoContents, True)
    self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
    # self.scene().sigMouseClicked.connect(self.peakClicked)
    self.pointPos = peak.pointPosition
    self.ppm = peak.position[self.dim]
    self.height = self.peak.height
    if not self.height:
      height = self.peak.apiPeak.findFirstPeakIntensity(intensityType = 'height')
      if height:
        self.height = height.value
      else:
        self.height = 0
    # self.height *= self.spectrum.scale

    # if peakDims[dim].numAliasing:
    #   self.isAliased = True
    # else:
    #   self.isAliased = False
    if self.ppm and self.height:
      self.setPos(self.ppm, self.height)

    # try:
    self.annotation = Peak1dAnnotation(scene, self, 'H1')
    self.symbol = Peak1dSymbol(scene, self)
    # except AttributeError:
    #   return

    # group.addToGroup(self)
  #
  def mousePressEvent(self, event):

    self.press = True
    self.hover = True
    print('pressed')

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

  def __init__(self, scene, parent, text):

    QtGui.QGraphicsSimpleTextItem.__init__(self, scene=scene)

    self.setParentItem(parent)
    self.peakItem = parent # When exporting to e.g. PDF the parentItem is temporarily set to None, which means that there must be a separate link to the PeakItem.
    self.setText(text)
    self.scene = scene
    # self.analysisLayout = parent.glWidget.analysisLayout
    font = self.font()
    font.setPointSize(10)
    self.setFont(font)
    # self.setCacheMode(self.DeviceCoordinateCache)
    self.setFlag(self.ItemIgnoresTransformations, True)
    # self.setFlag(self.ItemIsMovable, True)
    # self.setFlag(self.ItemIsSelectable, True)
    # self.setFlag(self.ItemSendsScenePositionChanges, True)
    # if self.isSelected():
    #   print(self)
    self.setColor()

    self.updatePos()

  def sceneEventFilter(self, watched, event):
    print(event)

  def mousePressEvent(self, event):

    if (event.button() == QtCore.Qt.LeftButton) and (
              event.modifiers() & QtCore.Qt.ControlModifier) and not (
              event.modifiers() & QtCore.Qt.ShiftModifier):

      event.accept()
      self.scene.clearSelection()
      self.setFlag(QtGui.QGraphicsSimpleTextItem.ItemIsMovable)
      QtGui.QGraphicsSimpleTextItem.mousePressEvent(self, event)
      self.setSelected(True)
      print(self.peakItem)
      self.update()


  def updatePos(self):

    peakItem = self.peakItem
    if peakItem.height >= 0:
      # Translate first to rotate around bottom left corner
      self.translate(0, -self.boundingRect().height())
      self.setRotation(0)
      self.setPos(0, min(peakItem.pos().y()*0.75, peakItem.spectrum.positiveContourBase * peakItem.spectrum.scale))
      # print(peakItem.height, max(peakItem.pos().y()*0.75, peakItem.spectrum.positiveContourBase * peakItem.spectrum.scale))
    else:
      self.setPos(0, min(peakItem.pos().y()*0.75, -peakItem.spectrum.positiveContourBase * peakItem.spectrum.scale))
      self.setRotation(45)

  def setColor(self):

    color = QtGui.QColor('white')
    textColor = color
    # color.setRgbF(*self.peakItem.glWidget._hexToRgba(textColor))
    self.setBrush(QtGui.QBrush(color))

  def paint(self, painter, option, widget):

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
    # print(left, right)
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
    color = QtGui.QColor('white')
    # lineColor = peakItem.analysisPeakList.symbolColor
    # color.setRgbF(*peakItem.glWidget._hexToRgba(lineColor))
    #
    # if peakItem.peak not in self.analysisLayout.currentPeaks:
    #   color.setAlphaF(0.5)

    pen.setColor(color)
    painter.setPen(pen)

    painter.drawLine(pos, annotationPos)

    self.setBbox()

  def mousePressEvent(self, event):

    if (event.button() == QtCore.Qt.LeftButton) and (
              event.modifiers() & QtCore.Qt.ControlModifier) and not (
              event.modifiers() & QtCore.Qt.ShiftModifier):

      event.accept()
      print(event)
      self.scene.clearSelection()
      self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
      QtGui.QGraphicsSimpleTextItem.mousePressEvent(self, event)
      self.setSelected(True)
      self.update()



class PeakNd(QtGui.QGraphicsItem):

  def __init__(self, peakLayer, peak):

    self._appBase = peakLayer._appBase
    scene = peakLayer.strip.plotWidget.scene()
    #QtGui.QGraphicsItem.__init__(self, scene=scene)
    QtGui.QGraphicsItem.__init__(self, peakLayer, scene=scene)
    ###QtGui.QGraphicsItem.__init__(self, peakLayer)
    ###scene.addItem(self)
    ###strip.plotWidget.plotItem.vb.addItem(self)
    self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable + self.ItemIgnoresTransformations)
    
    self.annotation = PeakNdAnnotation(self, scene)
    self.setupPeakItem(peakLayer, peak)
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
    sz = 20
    hz = sz/2.0
    # self.bbox = QtCore.QRectF(-hz, -hz, sz, sz)
    # self.drawData = (hz, sz, QtCore.QRectF(-hz, -hz, sz, sz))
    """
    self.rectItem = QtGui.QGraphicsRectItem(-hz, -hz, sz, sz, self.peakLayer, scene)
    color = QtGui.QColor('cyan')
    self.rectItem.setBrush(QtGui.QBrush(color))
    self.rectItem.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
    """

    self.drawData = (hz, sz)#, QtCore.QRectF(-hz, -hz, sz, sz))
    ###xDim = strip.spectrumViews[0].dimensionOrdering[0] - 1
    ###yDim = strip.spectrumViews[0].dimensionOrdering[1] - 1
    ###xPpm = peak.position[xDim] # TBD: does a peak have to have a position??
    ###yPpm = peak.position[yDim]
    ###self.setPos(xPpm, yPpm)
    # self.inPlane = self.isInPlane()

    # from ccpncore.gui.Action import Action
    # self.deleteAction = QtGui.QAction(self, triggered=self.deletePeak, shortcut=QtCore.Qt.Key_Delete)
    #peakLayer.peakItems.append(self)
  #
  
  def setupPeakItem(self, peakLayer, peak):

    self.peakLayer = peakLayer
    self.peak = peak
    if not hasattr(peak, 'isSelected'):
      peak.isSelected = False
    self.setSelected(peak.isSelected)
    xDim = peakLayer.strip.spectrumViews[0].dimensionOrdering[0] - 1
    yDim = peakLayer.strip.spectrumViews[0].dimensionOrdering[1] - 1
    xPpm = peak.position[xDim]
    yPpm = peak.position[yDim]
    self.setPos(xPpm, yPpm)
    self.annotation.setupPeakAnnotationItem(self)
    peakLayer.peakItems[self.peak] = self
    
  def isInPlane(self):

    strip = self.peakLayer.strip

    if len(strip.orderedAxes) > 2:
      zDim = strip.spectrumViews[0].dimensionOrdering[2] - 1
      zPlaneSize = strip.spectrumViews[0].zPlaneSize()
      zPosition = self.peak.position[zDim]

      zRegion = strip.orderedAxes[2].region
      if zRegion[0]-zPlaneSize <= zPosition <= zRegion[1]+zPlaneSize:
        return True
      else:
        return False
    else:
      return True

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

  def itemChange(self, change, value):
    
    if change == QtGui.QGraphicsItem.ItemSelectedHasChanged:
      peak = self.peak
      selected = peak.isSelected = self.isSelected()
      current = self._appBase.current
      if selected:
        current.peak = peak
        if peak not in current.peaks:
          current.peaks.append(peak)
      else:
        if current.peak is peak:
          current.peak = None
        if peak in current.peaks:
          current.peaks.remove(peak)
    
    return QtGui.QGraphicsItem.itemChange(self, change, value)
    
  def paint(self, painter, option, widget):

    if self.peak: # TBD: is this ever not true??
      self.setSelected(self.peak.isSelected) # need this because dragging region to select peaks sets peak.isSelected but not self.isSelected()
      if self.isInPlane():
        # r, w, box = self.drawData
        r, w  = self.drawData

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

        if widget:
          painter.setPen(QtGui.QColor('white'))
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
        
        if self.peak.isSelected:
          painter.drawLine(-r,-r,-r,r)
          painter.drawLine(-r,r,r,r)
          painter.drawLine(r,r,r,-r)
          painter.drawLine(r,-r,-r,-r)
        #
        # if self.isSelected:
        #   painter.setPen(QtGui.QColor('white'))
        #   painter.drawRect(-r,-r,w,w)


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
    color = QtGui.QColor('white')
    self.setBrush(color)
    ###self.setColor()
    self.setPos(15, -15)
    # self.updatePos()
        
  def setupPeakAnnotationItem(self, peakItem):
    
    self.peakItem = peakItem # When exporting to e.g. PDF the parentItem is temporarily set to None, which means that there must be a separate link to the PeakItem.
    self.setParentItem(peakItem)
    
    peak = peakItem.peak
    peakLabel = []
    for dimension in range(peak.peakList.spectrum.dimensionCount):
      if len(peak.dimensionNmrAtoms[dimension]) == 0:
        peakLabel.append('-')
      else:
        peakNmrResidues = [atom[0].nmrResidue.id for atom in peak.dimensionNmrAtoms]
        if all(x==peakNmrResidues[0] for x in peakNmrResidues):
          for item in peak.dimensionNmrAtoms[dimension]:
            if len(peakLabel) > 0:
              peakLabel.append(item.name)
            else:
              peakLabel.append(item.pid.id)

        else:
          for item in peak.dimensionNmrAtoms[dimension]:
            label = item.nmrResidue.id+item.name
            peakLabel.append(label)
            print(item, item.name)



    text = ','.join(peakLabel)
    
    self.setText(text)

  """
  def setColor(self):

    color = QtGui.QColor('white')
    textColor = color
    # color.setRgbF(*self.peakItem.glWidget._hexToRgba(textColor))
    self.setBrush(QtGui.QBrush(color))

  def paint(self, painter, option, widget):
    if self.peakItem.isInPlane():
      peakItem = self.peakItem
      peakLabel = []
      for dimension in range(peakItem.peak.peakList.spectrum.dimensionCount):
        if len(peakItem.peak.dimensionNmrAtoms[dimension]) == 0:
          peakLabel.append('-')
        else:
          for item in peakItem.peak.dimensionNmrAtoms[dimension]:

            if len(peakLabel) > 0:
              # print(, peakLabel[-1])
              peakLabel.append(item.pid.id.split('.')[-1])

            else:
              peakLabel.append(item.pid.id)

      text = ','.join(peakLabel)
      painter.setBrush(QtGui.QBrush(QtGui.QColor('white')))

      painter.drawText(0, 0, text)
    # if self.peakItem.peak in self.analysisLayout.currentPeaks:
    # painter.drawRect(self.boundingRect())

  #def sceneEventFilter(self, watched, event):
  #  print(event)
"""
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

# class PeakNdAnnotation(QtGui.QGraphicsItem):
#
#   def __init__(self, peakItem, scene):
#
#     QtGui.QGraphicsItem.__init__(self, scene=scene)
#
#     self.setParentItem(peakItem)
#     self.setCacheMode(self.DeviceCoordinateCache)
#     self.setFlags(self.ItemIgnoresTransformations)
#     self.hover = False
#     self.setAcceptHoverEvents(True)
#     self.color = NULL_COLOR
#     self.brush = NULL_COLOR
#     self.peakItem = peakItem
#     self.text = '-, -, -'
#     self.setZValue(-1)
#     self.bbox = NULL_RECT
#     self.setPos(self.peakItem.pos())
#     # self.show()
#     print(self.pos())
#
#   def hoverEnterEvent(self, event):
#
#     self.hover = True
#     self.update()
#
#   def hoverLeaveEvent(self, event):
#
#     self.hover = False
#     self.update()
#
#   def boundingRect(self):
#
#     return self.bbox
#
#   def syncPeak(self, text, color):
#
#     self.color = color
#     self.text = text
#     rect = FONT_METRIC.boundingRect(self.text)
#     self.bbox = rect.adjusted(-2,-2, 4, 2)
#
#     r,g,b,a = color.getRgb()
#     self.brush = QtGui.QColor('white')
#     self.update()
#
#   def paint(self, painter, option, widget):
#
#     if self.text:
#       painter.setFont(FONT)
#       # if self.hover:
#       self.setZValue(-1)
#         # r, g, b, a = QtGui.QColor('white')
#       painter.setBrush(QtGui.QColor('white'))
#       painter.setPen(QtGui.QColor('white'))
#       painter.drawRect(self.bbox)
#
#       # else:
#       #   painter.setPen(QtGui.QColor('white'))
#       #   self.setZValue(0)
#
#       painter.drawText(0, 0, self.text)
# class PeakItem(QtGui.QGraphicsItem):
#
#   def __init__(self, peak):
#     """ peakListItem is the QGraphicsItem parent
#         peak is the CCPN object
#     """
#
#     QtGui.QGraphicsItem.__init__(self)
#
#     self.peak = peak
#     # TBD: symbol and annotation
#     # self.peakSymbolItem = PeakSymbolItem(self, peak)
#
#     self.peakAnnotationItem = PeakAnnotationItem(peak)  #(this in turn has peakTextItem, peakPointerItem)

# class PeakSymbolItem(QtGui.QGraphicsLineItem):
#
#   def __init__(self, x1, y1, x2, y2):
#     QtGui.QGraphicsLineItem.__init__(self)
#     self.pen = QtGui.QPen()
#     self.pen.setColor(QtGui.QColor('white'))
#     self.pen.setCosmetic(True)
#     self.setPen(self.pen)
#     self.setLine(x1, y1, x2, y2)
#   #   def viewRangeChanged(self):
#   #       self.updatePosition(peakMarker)
#   #
#   #
#   # def updatePosition(self, peakMarker):
#   #   br = peakMarker.boundingRect()
#   #   apos = peakMarker.mapToParent(pg.Point(br.width()*peakMarker.anchor.x(), br.height()*peakMarker.y()))
#   #   print(apos.x(), apos.y())




# class PeakAnnotationItem(QtGui.QGraphicsTextItem):
#
#   def __init__(self, parent, peak):
#
#     super(PeakAnnotationItem, self).__init__()
#
#     if peak.height is not None:
#       peakHeight = peak.height
#     else:
#       peakHeight = peak._wrappedData.findFirstPeakIntensity(intensityType='height').value
#     text=str("%.3f" % peak.position[0])
#     # self.peak = peak
#     self.peakItem = parent
#     self.peakTextItem = pg.TextItem(text=text, color='w', anchor=(-0.9,1.0))#, color='w')
#     # self.peakPointerItem =  pg.ArrowItem(pos=(peak.position[0],peakHeight), angle = -45, headLen=60, tipAngle=5)
#     self.peakTextItem.setPos(pg.Point(peak.position[0]+self.peakTextItem.anchor.x()*0.1, peakHeight+self.peakTextItem.anchor.y()*0.1))
#     # print(self.peakTextItem.sceneBoundingRect())
#     # self.peakSymbolItem = PeakSymbolItem(peak.position[0], peakHeight, peak.position[0], peakHeight+self.peakTextItem.anchor.y()*0.1)
#     # print(peak.position[0], peakHeight, self.peakTextItem.anchor.x(), self.peakTextItem.anchor.y())
#     # self.displayed = True
#
#
#   # def updatePos(self):
#   #
#   #   peakItem = self.peakItem
#   #   if peakItem.height >= 0:
#   #     # Translate first to rotate around bottom left corner
#   #     self.translate(0, -self.boundingRect().height())
#   #     self.setRotation(0)
#   #     self.peakTextItem.setPos(0, min(peakItem.pos().y()*0.75, peakItem.spectrum.positiveContourBase * peakItem.spectrum.scale))
#   #     print(peakItem.height, max(peakItem.pos().y()*0.75, peakItem.spectrum.positiveContourBase * peakItem.spectrum.scale))
#   #   else:
#   #     self.setPos(0, min(peakItem.pos().y()*0.75, -peakItem.spectrum.positiveContourBase * peakItem.spectrum.scale))
#   #     self.setRotation(45)






