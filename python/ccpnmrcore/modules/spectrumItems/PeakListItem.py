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

class PeakListItem(QtGui.QGraphicsItem):

  def __init__(self, scene, parent, peakList):
    """ spectrumItem is the QGraphicsItem parent
        peakList is the CCPN object
    """

    QtGui.QGraphicsItem.__init__(self, scene=scene)
    self.peakList = peakList
    self.peakItems = {}  # CCPN peak -> Qt peakItem
    self.displayed = True
    self.symbolColour = None
    self.symbolStyle = None
    self.isSymbolDisplayed = True
    self.textColour = None
    self.isTextDisplayed = True
    for peak in peakList.peaks:
      peakItem = Peak1d(scene, parent, peak, peakList)
      peakItem.setParentItem(self)
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
    #
    if self.ppm and self.height:
      self.setPos(self.ppm, self.height)

    # try:
    self.annotation = Peak1dAnnotation(scene, self, '-, -, -')
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
    painter.drawRect(self.boundingRect())

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
      self.scene.clearSelection()
      self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
      QtGui.QGraphicsSimpleTextItem.mousePressEvent(self, event)
      self.setSelected(True)
      print(self.peakItem)
      self.update()



class PeakNd(QtGui.QGraphicsItem):

  def __init__(self, scene, parent, peak, peakList):

    QtGui.QGraphicsItem.__init__(self, scene=scene)

    # self.glWidget = peakLayer.glWidget
    # self.setParentItem(peakLayer)
    # self.peakLayer = peakLayer
    # self.spectrumWindow = spectrumWindow
    # self.panel = spectrumWindow.panel
    self.setCacheMode(self.NoCache)
    self.setFlags(self.ItemIgnoresTransformations)
    self.hover = False
    self.press = False
    self.setAcceptHoverEvents(True)
    self.bbox  = NULL_RECT
    self.color = 'white'
    self.brush = 'white'
    self.peak = None
    # self.annotation = PeakNdAnnotation(self, scene)

    #peakLayer.peakItems.append(self)

  def hoverEnterEvent(self, event):

    self.hover = True
    self.annotation.hoverEnterEvent(event)
    self.update()

  def hoverLeaveEvent(self, event):

    self.hover = False
    self.press = False
    r, w, box = self.drawData
    self.bbox = box
    self.peakLayer.hideIcons()
    self.annotation.hoverLeaveEvent(event)
    self.update()

  def setPeak(self, spectrum, analysisPeakList, peak, xDim, yDim,
              isAliased=False, isSelected=False, isInPlane=True):

    self.spectrum = spectrum
    self.analysisSpectrum = analysisSpectrum = spectrum.analysisSpectrum
    self.analysisPeakList = analysisPeakList
    self.peak = peak
    self.peakDims = peakDims = peak.sortedPeakDims()
    self.isAliased = isAliased
    self.isSelected = isSelected
    self.isInPlane = isInPlane
    self.axisDims = [xDim, yDim]
    self.color = color = QtGui.QColor('White')
    r,g,b,a = color.getRgb()
    self.brush = QtGui.QColor(r, g, b, 64)

    xPpm = peakDims[xDim].value
    yPpm = peakDims[yDim].value
    self.setPos(xPpm, yPpm)

    self.spectrumView, spectrumMapping = self.spectrumWindow.getViewMapping(analysisSpectrum)

    sz = 20
    hz = sz/2.0
    self.bbox = QtCore.QRectF(-hz, -hz, sz, sz)
    self.drawData = (hz, sz, QtCore.QRectF(-hz, -hz, sz, sz))

    text = ','.join([pd.annotation or '-' for pd in peakDims])
    color = qColor(*hexToRgba(analysisPeakList.textColor))
    self.annotation.syncPeak(text, color)

    if self.press or self.hover:
      self.hoverLeaveEvent(None)

  def mousePressEvent(self, event):

    self.press = True
    self.hover = True
    r, w, box = self.drawData
    self.bbox = box.adjusted(-26,-51, 2, 51)
    self.peakLayer.showIcons(self)
    self.update()

    #return QtGui.QGraphicsItem.mousePressEvent(self, event)

  def boundingRect(self):

    return self.bbox # .adjust(-2,-2, 2, 2)

  def paint(self, painter, option, widget):

    if self.peak:
      r, w, box = self.drawData

      if self.hover:
        self.setZValue(1)

        painter.setBrush(self.brush)

        painter.setPen(self.color)
        if self.press:
          painter.drawRect(self.bbox)

        painter.setPen(self.spectrumWindow.qFgColor)
        painter.drawEllipse(box)

      else:
        painter.setPen(self.color)
        self.setZValue(0)

      painter.drawLine(-r,-r,r,r)
      painter.drawLine(-r,r,r,-r)

      if self.isSelected:
        painter.setPen(self.spectrumWindow.qFgColor)
        painter.drawRect(-r,-r,w,w)


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






