from PyQt5 import QtCore, QtGui, QtWidgets

QColor = QtGui.QColor

BLANK = QColor()

def inverseGrey(color):

  r, g, b, a = color.getRgb()
  
  m = (11*r + 16*g + 5*b)/32
  
  if (m > 192) or (m < 64):
    m = 255-m
  elif m<128:
    m += 128
  elif m<192:
    m -= 128
  
  return QColor(m, m, m)
 

class ColorDialog(QtWidgets.QColorDialog):

  def __init__(self, parent=None, doAlpha=False, **kw):
    
    QtWidgets.QColorDialog.__init__(self, parent)
       
    self.setOption(self.ShowAlphaChannel, doAlpha)
    self.setOption(QtWidgets.QColorDialog.DontUseNativeDialog,  True)
    self.aborted = False
    self.rejected.connect(self.quit)
  
  def set(self, color):
  
    self.setColor(color)
    
  def setColor(self, color):
    # color can be name, #hex, (r,g,b) or (r,g,b,a)
    
    if isinstance(color, str) and (color[0] == '#'):
      color = color.upper()
    
      if len(color) == 9:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        a = int(color[7:9], 16)
        color = (r, g, b, a)
        
      else:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        color = (r, g, b)
      
      qColor = QtGui.QColor(*color)
   
    else:
      qColor = QtGui.QColor(color)
    
    self.setCurrentColor(qColor)
  
  def quit(self):
    
    self.aborted = True
    
  def get(self):
  
    color = self.currentColor()
    
    if self.aborted:
      return None
    else:
      return color
    
  def getColor(self, initialColor=None):
    
    if initialColor:
      self.setColor(initialColor)
    
    self.exec_()
    
    color = self.currentColor()
    
    if self.aborted:
      return None
    else:
      return color

  def getHexColor(self, initialColor=None):
    
    if initialColor:
      self.setColor(initialColor)
    
    self.exec_()
    
    color = self.currentColor()
    
    if self.aborted:
      return None
    else:
      return '#%02X%02X%02X%02X' % color.getRgb()

from .Base import Base, Icon
from .PulldownList import PulldownList
from .Frame import Frame

DEFAULT_COLORS = [
                  '#400000','#404000','#004000','#004040','#000040','#400040','#000000',
                  '#800000','#808000','#008000','#008080','#000080','#800080','#2B2B2B',
                  '#B00000','#B0B000','#00B000','#00B0B0','#0000B0','#B000B0','#565656',
                  '#FF0000','#FFFF00','#00FF00','#00FFFF','#0000FF','#FF00FF','#808080',
                  '#FF4040','#FFFF40','#40FF40','#40FFFF','#4040FF','#FF40FF','#ABABAB',
                  '#FF8080','#FFFF80','#80FF80','#80FFFF','#8080FF','#FF80FF','#D6D6D6',
                  '#FFB0B0','#FFFFB0','#B0FFB0','#B0FFFF','#B0B0FF','#FFB0FF','#FFFFFF',
                 ]

class ColorPulldown(PulldownList):

  def __init__(self, parent, colors=None, callback=None,
              index=0, numRows=7, **kw):
  
    PulldownList.__init__(self, parent, texts=None, objects=None,
                          icons=None, callback=callback, index=0,
                          **kw)
    
    if not colors:
      colors = DEFAULT_COLORS[:]
    
    self.view = None
    self.dialogItem = None
    self.numRows = numRows
    self.colors = colors
    self.objects = [None] * len(colors)
    
    self.setData(colors, index)
    
    self.object = self.objects[index]
    # self.disconnect(self, QtCore.pyqtSignal('currentIndexChanged(int)'), self._callback)
    # self.connect(self, QtCore.pyqtSignal('activated(int)'), self._callback)
    self.currentIndexChanged.connect(self._callback)
    self.activated.connect(self._callback)

  def addItem(self, text, object=None, icon=None):
    
    i = len(self.objects)
    row = int( i % self.numRows)
    col = int( i // self.numRows)
    model = self.model()
    
    if icon:
      item = QtGui.QStandardItem(icon, text)
    else:
      item = QtGui.QStandardItem(text)
    
    model.setItem(row, col, item)
    
    if object is None:
      object = text
    
    self.texts.append(text)  
    self.objects.append(object)
    
    return item
  
  def setColor(self, color):
    
    color = color.upper()
    self.object = color
    
    if color in self.colors:
      i = self.colors.index(color)
      row = i % self.numRows
      col = int(i // self.numRows)
      self.setModelColumn(col)
      self.setCurrentIndex(row)        
 
    
  def setData(self, colors, index=0):
    
    texts = [''] * len(colors)
    objects = [QtGui.QColor(c) for c in colors]
    icons = [Icon(color=c) for c in colors]
    
    nCols = int(len(objects) // self.numRows) + 1

    self.view = view = QtWidgets.QTableView()
    
    view.setModel(self.model())
    view.horizontalHeader().setVisible(False)
    view.verticalHeader().setVisible(False)

    self.setView(view)
    
    PulldownList.setData(self, texts, objects, index, icons)
    
    view.resizeColumnsToContents()
    view.resizeRowsToContents()
    view.setMinimumWidth(view.horizontalHeader().length())

  def currentObject(self):
    
    if self.objects:
      itemIndex = self.view.selectionModel().currentIndex()
      index = itemIndex.row() + (itemIndex.column() * self.numRows)
      if index >= 0:
        return self.objects[index]
  
  def _callback(self, index):
    
    if index < 0:
      return
    
    itemIndex = self.view.selectionModel().currentIndex()
    index = itemIndex.row() + (itemIndex.column() * self.numRows)
        
    self.index = index
    
    if self.objects:
      object = self.objects[index]
    else:
      object = None        
       
    if object is self.object:
      return
     
    self.object = object
    if self.callback:
      self.callback(self.object)
    
    return True
    
Qt = QtCore.Qt

class GradientWidget(QtWidgets.QWidget, Base):

  def __init__(self, parent, colors=None, **kw):
  
    QtWidgets.QWidget.__init__(self, parent)
    Base.__init__(self, parent, **kw)
  
    if not colors:
      colors = ['#FF0000','#00FF00','#0000FF']
  
    self.colors = colors
    
    self.setMinimumHeight(22)
  
  def paintEvent(self, event):
    
    painter = QtGui.QPainter(self)
    
    w = self.width()
    h = self.height()
    
    p1 = QtCore.QPointF(0.0,h/2.0)
    p2 = QtCore.QPointF(float(w), h/2.0)
    gradient = QtWidgets.QLinearGradient(p1, p2)
    
    n = float(len(self.colors)) - 1.0
    for i, color in enumerate(self.colors):
      gradient.setColorAt(i/n, QtGui.QColor(color))
    
    painter.setBrush(gradient)
    painter.setPen('#000000')
    painter.drawRect(0, 0, w-1, h-1)
    
    return QtWidgets.QWidget.paintEvent(self, event)
  
  def setColors(self, colors):
  
    self.colors = colors
    self.update()
    
  
class GradientEditor(Frame):

  def __init__(self, parent, colors=None, **kw):
   
    Frame.__init__(self, parent, **kw)

    self.gradientWidget = GradientWidget(self, grid=(0,0))
    self.frame = Frame(self, grid=(1,0))
    
    
    self.colorPulldowns = []
    self.colors = []
    
    if not colors:
      colors = self.gradientWidget.colors[:]
    
    self.setColors(colors) 
    
  def setColors(self, colors):
    
    self.colors = colors
    nColors = len(colors)
    nWidgets = len(self.colorPulldowns)
    
    while nWidgets > nColors:
      widget = self.colorPulldowns.pop()
      widget.destroy()
      nWidgets -= 1
    
    while nColors > nWidgets:
      pulldown = ColorPulldown(self.frame, grid=(0,nWidgets),
                               callback=lambda c, i=nWidgets:self.selectColor(c, i))
      self.colorPulldowns.append(pulldown)
      nWidgets += 1
    
    for i, color in enumerate(colors):
      self.colorPulldowns[i].setColor(color)
      
    self.gradientWidget.setColors(self.colors)
   
      
  def selectColor(self, color, index):
    
    self.colors[index] = color
    self.gradientWidget.setColors(self.colors)
    
    
if __name__ == '__main__':

  from .Application import Application
  from .Button import Button
  
  def getColor():
  
    dialog = ColorDialog()
    dialog.setColor('#008000')
    
    print('Colour chosen:', dialog.getHexColor())
    
  def selectColor(color):
  
    print('Selected', color)
  
  app = Application()
  
  window = QtWidgets.QWidget()
  
  button = Button(window, 'Choose color...', callback=getColor, grid=(0,0))
  
  pulldown = ColorPulldown(window, callback=selectColor, grid=(0,1))
  
  pulldown.setColor('#FF8040')
  
  widget = GradientEditor(window, grid=(1,0), gridSpan=(1,2))
  
  window.show()
  
   # opens the dialog
  
  # You don't need to start if the dialog is used alone
  app.start()
