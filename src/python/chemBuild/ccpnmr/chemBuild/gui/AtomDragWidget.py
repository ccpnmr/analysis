from PyQt4 import QtCore, QtGui
Qt = QtCore.Qt
QPointF = QtCore.QPointF
QRectF = QtCore.QRectF

from ccpnmr.chemBuild.general.Constants import LINK, MIMETYPE, MIMETYPE_ELEMENT, MIMETYPE_COMPOUND
from ccpnmr.chemBuild.general.Constants import ATOM_NAME_FG, ELEMENT_FONT
from ccpnmr.chemBuild.general.Constants import AROMATIC, EQUIVALENT, PROCHIRAL

class AtomDragWidget(QtGui.QWidget):
  
  def __init__(self, parent=None, text='',  mimeType=MIMETYPE,  data=None,
               bgColor=Qt.white, size=(21,21), callback=None ):
    
    QtGui.QWidget.__init__(self,  parent)
    
    self.text = text
    self.mimeType = mimeType
    self.data = data
    self.bgColor = bgColor
    self.setFixedSize(*size)
    self.callback = callback

    gradient = QtGui.QRadialGradient(11,11,9,15,7)
    gradient.setColorAt(1, bgColor.darker())
    gradient.setColorAt(0.5, bgColor)
    gradient.setColorAt(0, bgColor.lighter())
    
    self.brush = QtGui.QBrush(gradient)
    self.brush.setStyle(Qt.RadialGradientPattern)  

  def paintEvent(self,  event):
    
    painter = QtGui.QPainter()
    
    painter.begin(self)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
     
    drawEllipse = painter.drawEllipse
    drawText = painter.drawText
    center = QPointF(self.rect().center())
    
    painter.setPen(Qt.black)
    painter.setBackground(QtGui.QColor(200, 200, 200, 12))
    painter.setFont(ELEMENT_FONT)
    painter.setBrush(self.brush)
    
    r = 9.0
    drawEllipse(center, r, r)
    
    if self.text:
      fontMetric = QtGui.QFontMetricsF(painter.font())
      bbox = fontMetric.tightBoundingRect(self.text)
      h2 = bbox.height()/2.0
      w2 = bbox.width()/2.0 
      textPoint = center + QPointF(-w2, h2)
      drawText(textPoint, self.text)
      
    painter.end()
    
  def dragEnterEvent(self, event):
    
    event.ignore()

  def dragMoveEvent(self, event):
    
    event.ignore()
    
  def mousePressEvent(self, event):
    
    #pos = event.pos()

    pixmap = QtGui.QPixmap(self.size())
    pixmap.fill(QtGui.QColor(64,64,64,64))
    self.render(pixmap, flags=QtGui.QWidget.DrawChildren)
    
    pixmap.setMask(pixmap.createHeuristicMask())
    
    anchor = self.rect().bottomRight()
    
    itemData = QtCore.QByteArray()
    dataStream = QtCore.QDataStream(itemData, QtCore.QIODevice.WriteOnly)
    dataStream << pixmap << anchor

    mimeData = QtCore.QMimeData()
    mimeData.setText(self.data)
    mimeData.setData(self.mimeType, itemData)

    drag = QtGui.QDrag(self)
    drag.setMimeData(mimeData)
    drag.setPixmap(pixmap)
    drag.setHotSpot(anchor)
    
    drag.exec_(QtCore.Qt.CopyAction | QtCore.Qt.MoveAction, QtCore.Qt.CopyAction)
        
  def mouseDoubleClickEvent(self, event):
     
    if self.callback:
      self.callback(self.data)

