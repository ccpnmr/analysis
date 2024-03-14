from PyQt5 import QtGui, QtWidgets, QtCore

from os import path
from memops.universal.Io import getTopDirectory
ICON_DIR = path.join(getTopDirectory(),'python','memops','qtgui') 

"""
Align options

  1 Qt::AlignLeft
  2 Qt::AlignRight
  4 Qt::AlignHCenter
  8 Qt::AlignJustify
 16 Qt::AlignAbsolute
 32 Qt::AlignTop
 64 Qt::AlignBottom
128 Qt::AlignVCenter
"""

class Base(object):

  def __init__(self, parent=None, tipText=None, grid=(None, None), gridSpan=(1,1),
               stretch=(0,0), sticky='', bgColor=None, isFloatWidget=False):
    
    # Tool tips
    
    if tipText:
      self.setToolTip(tipText)
    
    if parent and not isFloatWidget:
      #self.getParent = self.parent
      #self.parent = parent
      self.guiParent = parent
      # Setup gridding within parent
      layout = parent.layout()
 
      if not layout:
        layout = QtWidgets.QGridLayout(parent)
        layout.setSpacing(2)
        layout.setContentsMargins(2,2,2,2)

      if isinstance(layout, QtWidgets.QGridLayout):
        rowSpan, colSpan = gridSpan
        row, col, align = self._getGriddingData(grid, sticky)
        rowStr, colStr = stretch
        layout.setRowStretch(row, rowStr)
        layout.setColumnStretch(col, colStr)
        #layout.setColumnMinimumWidth(col, 30)
        #layout.setRowMinimumHeight(row, 30)
        layout.addWidget(self, row, col, rowSpan, colSpan, align)

    # Setup colour overrides (styles used primarily)
    if bgColor:
      self.setAutoFillBackground(False)
      rgb = QtGui.QColor(bgColor).getRgb()[:3]
      self.setStyleSheet("background-color: rgb(%d, %d, %d);" %  rgb)
  
  def _getGriddingData(self, grid, sticky):
    
    layout = self.guiParent.layout()
    sticky = sticky.lower()
    
    if grid:
      row, col = grid
      
      if row is None:
        row = layout.count()
 
      if col is None:
        col = 0
  
    else:
      row = layout.count()
      col = 0
    
     
    alignment = 0
    if 'w' in sticky:
      if 'e' not in sticky:
        alignment += 1
      
    elif 'e' in sticky:
      alignment += 2
    
    elif 'n' in sticky:
      if 's' not in sticky:
        alignment += 32
    
    elif 's' in sticky:
      alignment += 64
    
    alignment = QtCore.Qt.Alignment(alignment)
    
    return row, col, alignment
  
  #def grid(self, row=None, col=0, rowSpan=None, colSpan=None, sticky=None):
  #  """ Maybe add Yucky Tkinter emulation """
    
  #  row, col, align = self._getGridData((row, col), sticky)
    
    
class Icon(QtGui.QIcon):

  def __init__(self, image=None, color=None):
    
    assert image or color
    
    if color:
      image = QtGui.QPixmap(22, 22)
      painter = QtGui.QPainter(image)
      
      if isinstance(color, str):
        color = QtGui.QColor(color[:7])
        image.fill(color)
      
      elif isinstance(color, (tuple, list)):
        image.fill(color[0][:7])
        dx = 22.0/float(len(color))
        
        x = dx
        for i, c in enumerate(color[1:]):
          col = QtGui.QColor(c[:7])
          painter.setPen(col)
          painter.setBrush(col)
          painter.drawRect(x,0,x+dx,21)
          x += dx
        
      else:  
        image.fill(color)
      
      painter.setPen(QtGui.QColor('#000000'))
      painter.setBrush(QtGui.QBrush())
      painter.drawRect(0,0,21,21)
      painter.end()
    
    elif not isinstance(image, QtGui.QIcon):
      if not path.exists(image):
        image = path.join(ICON_DIR, image)
        
      
    QtGui.QIcon.__init__(self, image)
    
    
  
