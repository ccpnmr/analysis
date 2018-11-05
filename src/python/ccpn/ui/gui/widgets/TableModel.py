"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:56 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from os import path

from PyQt5 import QtCore, QtGui, QtWidgets

from ccpn.ui.gui.widgets.ColourDialog import inverseGrey

ICON_FILE = path.join(path.dirname(__file__), 'icons', 'editable.png')

USER_ROLE = QtCore.Qt.UserRole
EDIT_ROLE = QtCore.Qt.EditRole
QtCore.Qt.DisplayRole = QtCore.Qt.DisplayRole
TOOLTIP_ROLE = QtCore.Qt.ToolTipRole
STATUS_ROLE = QtCore.Qt.StatusTipRole
BG_ROLE = QtCore.Qt.BackgroundRole
FG_ROLE = QtCore.Qt.ForegroundRole
CHECK_ROLE = QtCore.Qt.CheckStateRole
ICON_ROLE = QtCore.Qt.DecorationRole
SIZE_ROLE = QtCore.Qt.SizeHintRole
ALIGNMENT_ROLE = QtCore.Qt.TextAlignmentRole

NO_PROPS = QtCore.Qt.NoItemFlags
CHECKABLE = QtCore.Qt.ItemIsUserCheckable
ENABLED = QtCore.Qt.ItemIsEnabled
SELECTABLE = QtCore.Qt.ItemIsSelectable
EDITABLE = QtCore.Qt.ItemIsEditable

CHECKED = QtCore.Qt.Checked
UNCHECKED = QtCore.Qt.Unchecked
HORIZONTAL = QtCore.Qt.Horizontal
VERTICAL = QtCore.Qt.Vertical

QColor = QtGui.QColor
QIcon = QtGui.QIcon
QSize = QtCore.QSize
HEAD_ADJUST = QSize(50, 0)

class TableModel(QtCore.QAbstractTableModel):


  ############################################################
  # functions which need to be implemented in subclass
  ############################################################

  def numberRows(self):
    raise Exception('%s: should be implemented in subclass' % self.__class__)

  def numberCols(self):
    raise Exception('%s: should be implemented in subclass' % self.__class__)

  def dataForCell(self, row, col):
    raise Exception('%s: should be implemented in subclass' % self.__class__)

  ############################################################
  # functions which could be overridden in subclass
  ############################################################

  def headerForCol(self, col):
    return 1+col

  def headerForRow(self, row):
    return 1+row

  def sortRows(self, col, isDescending=False):
    pass

  def setDataForCell(self, row, col, value):
    return False

  def isEditableCell(self, row, col):
    return False

  ############################################################
  # implementation
  ############################################################

  def rowCount(self, parent):
    return self.numberRows()

  def columnCount(self, parent):
    return self.numberCols()

  def data(self, index, role):
    if not index.isValid():
      #return QtCore.QVariant()
      return None
    elif role != QtCore.Qt.DisplayRole:
      #return QtCore.QVariant()
      return None
    #return QtCore.QVariant(self.dataForCell(index.row(), index.column()))
    return self.dataForCell(index.row(), index.column())

  def setData(self, index, value, role):

    if role != QtCore.Qt.EditRole:
      return False

    result = False

    #TODO: this is probably not good enough
    if value.typeName() == 'QString':
      value = str(value.toString())
      result = self.setDataForCell(index.row(), index.column(), value)

      if result:
        self.emit(QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index)

    return result
    
  def headerData(self, section, orientation, role):

    if role != QtCore.Qt.DisplayRole:
      #return QtCore.QVariant()
      return None

    if orientation == HORIZONTAL:
      #return QtCore.QVariant(self.headerForCol(section))
      return self.headerForCol(section)
    else:
      #return QtCore.QVariant(self.headerForRow(section))
      return self.headerForRow(section)

  def flags(self, index):

    if not index.isValid():
      #return QtCore.QVariant(0)
      return 0

    if self.isEditableCell(index.row(), index.column()):
      return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
    else:
      return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

  def sort(self, column, order):

    self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
    isDescending = (order == QtCore.Qt.DescendingOrder)
    self.sortRows(column, isDescending)
    self.emit(QtCore.SIGNAL("layoutChanged()"))

class ObjectTableModel(TableModel):

  def __init__(self, table):
    
    super().__init__()
    # self.setSupportedDragActions(QtCore.Qt.MoveAction)
    
    self.editIcon = ICON_FILE
    self.table = table
    self.columns = table.columns
    self.objects = table.objects
  
  def removeRows(self, start, num, parent):
  
    if start+num < len(self.objects):
      return True
    
    else:
      return False  
  
  def insertRows(self, start, num, parent):
  
    return True

  def removeColumns(self, start, num, parent):
  
    if start+num < len(self.columns):
      return True
    
    else:
      return False  
  
  def insertColumns(self, start, num, parent):
  
    return True

  def rowCount(self, parent):
  
    return len(self.objects)

  def columnCount(self, parent):
    return len(self.columns)
  
  def numberRows(self):

    return len(self.objects)
  
  def numberCols(self):
  
    return len(self.columns)

  def flags(self, index):

    if not index.isValid():
      return False
    
    col = index.column()
    objCol = self.columns[col]
    
    if objCol.setEditValue:
      row = index.row()
      value = objCol.getEditValue(self.objects[row])
      
      if isinstance(value, bool):
        return CHECKABLE | ENABLED | SELECTABLE
      
      elif value is None:
        return NO_PROPS
      
      else:  
        return EDITABLE | ENABLED | SELECTABLE
    
    else:  
      return ENABLED | SELECTABLE


  def dataForCell(self, row, col):
  
    obj = self.objects[row]
    return obj
    
  def headerData(self, i, orientation, role):

    if role == QtCore.Qt.DisplayRole:
      if orientation == HORIZONTAL:
        return self.columns[i].heading
      else:
        return i+1

    elif role == ICON_ROLE:
      if orientation == HORIZONTAL:
        if self.columns[i].setEditValue:
          return QIcon(self.editIcon)

    elif role == TOOLTIP_ROLE:
      if orientation == HORIZONTAL:
        return self.columns[i].tipText

    elif role == SIZE_ROLE:
      if orientation == HORIZONTAL:
        texts = self.columns[i].heading.split('\n')
        texts.sort(key=len)
        bbox = self.table.bbox(texts[-1])
        size = max(30, bbox.width() + 32 )
        return QSize(size, 4 + bbox.height() * 2)
      
  def sortRows(self, col, isDescending=False):
    
    getValue = self.columns[col].getValue
    self.objects.sort(key=getValue, reverse=isDescending)

  
  def itemData(self, index):
  
    if not index.isValid():
      return None
    
    obj = self.objects[index.row()]
    objCol = self.columns[index.column()]
     
    icon = objCol.getIcon(obj)
    if icon:
      icon = None # QIcon(icon)
    
    color = QColor(objCol.getColor(obj))
    dataDict = {QtCore.Qt.DisplayRole:objCol.getFormatValue(obj), 
                ICON_ROLE:icon,
                USER_ROLE:obj,
                TOOLTIP_ROLE:objCol.tipText,
                ALIGNMENT_ROLE:objCol.alignment,
                STATUS_ROLE:None,
                BG_ROLE:color,
                FG_ROLE:inverseGrey(color)}
    
    return dataDict
  
  def data(self, index, role):
    
    #self.objects = self.table.objects
     
    if role == QtCore.Qt.DisplayRole:
      obj = self.objects[index.row()]
      objCol = self.columns[index.column()]
      value = objCol.getFormatValue(obj)
      
      if isinstance(value, bool):
        return None
      else:
        return value
    
    elif role == ICON_ROLE:
      obj = self.objects[index.row()]
      objCol = self.columns[index.column()]
      icon = objCol.getIcon(obj)
      if icon:
        return QIcon(icon)
           
    elif role == EDIT_ROLE:
      obj = self.objects[index.row()]
      objCol = self.columns[index.column()]
      return objCol.getEditValue(obj)
      
    elif role == USER_ROLE:
      obj = self.objects[index.row()]
      return obj
    
    elif role == TOOLTIP_ROLE:
      objCol = self.columns[index.column()]
      return objCol.tipText
      
    elif role == STATUS_ROLE:
      objCol = self.columns[index.column()]
      return objCol.tipText
    
    elif role == FG_ROLE:
      obj = self.objects[index.row()]
      objCol = self.columns[index.column()]
      # color = objCol.getColor(obj)
      # if color:
      #   return inverseGrey(color)

    elif role == BG_ROLE:
      obj = self.objects[index.row()]
      objCol = self.columns[index.column()]
      color = objCol.getColor(obj)
      
      if color:
        return QColor(color)

    elif role == CHECK_ROLE:
      obj = self.objects[index.row()]
      objCol = self.columns[index.column()]
      value = objCol.getValue(obj)
      if isinstance(value, bool):
        if value:
          return CHECKED
        else:
          return UNCHECKED
          
      else:
        return None

    elif role == ALIGNMENT_ROLE:
      objCol = self.columns[index.column()]
      return objCol.alignment

  def setData(self, index, value, role):
    
    if role == EDIT_ROLE:
      obj = self.objects[index.row()]
      objCol = self.columns[index.column()]
      
      if value != objCol.getEditValue(obj):
        objCol.setEditValue(obj, value)
      
      self.table.viewport().update()
        
      return True

    elif role == CHECK_ROLE:
      obj = self.objects[index.row()]
      objCol = self.columns[index.column()]
      if value == CHECKED:
        objCol.setEditValue(obj, True)
      else:
        objCol.setEditValue(obj, False)
     
      self.table.viewport().update()
       
      return True
    
    return False
    
  def getObject(self, row, col=0):
    
    index = self.index(row, col)
    
    return self.data(index, 32)

  # def dragMoveEvent(self, event):
  #   event.setDropAction(QtCore.Qt.MoveAction)
  #   event.accept()
 
# http://doc.qt.nokia.com/4.7-snapshot/qtableview.html
# http://doc.qt.nokia.com/4.7-snapshot/qtableview.html
# http://doc.qt.nokia.com/4.7-snapshot/qabstractitemview.html#setItemDelegate
# http://doc.qt.nokia.com/4.7-snapshot/qstyleditemdelegate.html
# http://doc.qt.nokia.com/4.7-snapshot/itemviews-coloreditorfactory.html
# http://doc.qt.nokia.com/4.7-snapshot/qabstractitemdelegate.html
  
if __name__ == '__main__':

  data = (('apple', 100), ('pear', 200), ('orange', 300))
  header = ('fruit', 'weight')

  class MyTableModel(TableModel):

    def __init__(self, *args, **kwds):
      TableModel.__init__(self, *args, **kwds)

    def numberRows(self):
      return len(data)

    def numberCols(self):
      return len(data[0])

    def dataForCell(self, row, col):
      return data[row][col]

    def headerForCol(self, col):
      return header[col]

  model = MyTableModel()

  print('number of rows', model.numberRows())
  print('number of cols', model.numberCols())
  print('headers', [model.headerForCol(col) for col in range(model.numberCols())])

