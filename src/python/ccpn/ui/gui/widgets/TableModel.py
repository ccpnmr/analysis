"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-02-17 15:38:10 +0000 (Fri, February 17, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from os import path
from PyQt5 import QtCore

from ccpn.ui.gui.widgets.ColourDialog import inverseGrey
from ccpn.ui.gui.widgets.table._TableCommon import USER_ROLE, EDIT_ROLE, \
    TOOLTIP_ROLE, STATUS_ROLE, BACKGROUND_ROLE, FOREGROUND_ROLE, CHECK_ROLE, \
    ICON_ROLE, SIZE_ROLE, NO_PROPS, ALIGNMENT_ROLE, CHECKABLE, ENABLED, \
    SELECTABLE, EDITABLE, CHECKED, UNCHECKED, HORIZONTAL, \
    QColor, QIcon, QSize


ICON_FILE = path.join(path.dirname(__file__), 'icons', 'editable.png')
HEAD_ADJUST = QSize(50, 0)


class TableModel(QtCore.QAbstractTableModel):

    ############################################################
    # functions which need to be implemented in subclass
    ############################################################

    def numberRows(self):
        raise RuntimeError(f'{self.__class__}: should be implemented in subclass')

    def numberCols(self):
        raise RuntimeError(f'{self.__class__}: should be implemented in subclass')

    def dataForCell(self, row, col):
        raise RuntimeError(f'{self.__class__}: should be implemented in subclass')

    ############################################################
    # functions which could be overridden in subclass
    ############################################################

    @staticmethod
    def headerForCol(col):
        return 1 + col

    @staticmethod
    def headerForRow(row):
        return 1 + row

    def sortRows(self, col, isDescending=False):
        pass

    @staticmethod
    def setDataForCell(row, col, value):
        return False

    @staticmethod
    def isEditableCell(row, col):
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
                self.emit(QtCore.pyqtSignal("dataChanged(QModelIndex,QModelIndex)"), index, index)

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

        self.emit(QtCore.pyqtSignal("layoutAboutToBeChanged()"))
        isDescending = (order == QtCore.Qt.DescendingOrder)
        self.sortRows(column, isDescending)
        self.emit(QtCore.pyqtSignal("layoutChanged()"))


class ObjectTableModel(TableModel):

    def __init__(self, table):

        super().__init__()
        # self.setSupportedDragActions(QtCore.Qt.MoveAction)

        self.editIcon = ICON_FILE
        self.table = table
        self.columns = table.columns
        self.objects = table.objects

    def removeRows(self, start, num, parent):

        return start + num < len(self.objects)

    def insertRows(self, start, num, parent):

        return True

    def removeColumns(self, start, num, parent):

        return start + num < len(self.columns)

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

        return self.objects[row]

    def headerData(self, i, orientation, role):

        if role == QtCore.Qt.DisplayRole:
            return self.columns[i].heading if orientation == HORIZONTAL else i + 1

        elif role == ICON_ROLE:
            if orientation == HORIZONTAL and self.columns[i].setEditValue:
                return QIcon(self.editIcon)

        elif role == TOOLTIP_ROLE:
            if orientation == HORIZONTAL:
                return self.columns[i].tipText

        elif role == SIZE_ROLE:
            if orientation == HORIZONTAL:
                texts = self.columns[i].heading.split('\n')
                texts.sort(key=len)
                bbox = self.table.bbox(texts[-1])
                size = max(30, bbox.width() + 32)
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
            icon = None  # QIcon(icon)

        color = QColor(objCol.getColor(obj))
        dataDict = {QtCore.Qt.DisplayRole: objCol.getFormatValue(obj),
                    ICON_ROLE            : icon,
                    USER_ROLE            : obj,
                    TOOLTIP_ROLE         : objCol.tipText,
                    ALIGNMENT_ROLE       : objCol.alignment,
                    STATUS_ROLE          : None,
                    BACKGROUND_ROLE      : color,
                    FOREGROUND_ROLE      : inverseGrey(color)}

        return dataDict

    def data(self, index, role):

        #self.objects = self.table.objects

        if role == QtCore.Qt.DisplayRole:
            obj = self.objects[index.row()]
            objCol = self.columns[index.column()]
            value = objCol.getFormatValue(obj)

            return None if isinstance(value, bool) else value

        elif role == ICON_ROLE:
            obj = self.objects[index.row()]
            objCol = self.columns[index.column()]
            if icon := objCol.getIcon(obj):
                return QIcon(icon)

        elif role == EDIT_ROLE:
            obj = self.objects[index.row()]
            objCol = self.columns[index.column()]
            return objCol.getEditValue(obj)

        elif role == USER_ROLE:
            return self.objects[index.row()]

        elif role == TOOLTIP_ROLE:
            objCol = self.columns[index.column()]
            return objCol.tipText

        elif role == STATUS_ROLE:
            objCol = self.columns[index.column()]
            return objCol.tipText

        elif role == FOREGROUND_ROLE:
            obj = self.objects[index.row()]
            objCol = self.columns[index.column()]
            # color = objCol.getColor(obj)
            # if color:
            #   return inverseGrey(color)

        elif role == BACKGROUND_ROLE:
            obj = self.objects[index.row()]
            objCol = self.columns[index.column()]
            if color := objCol.getColor(obj):
                return QColor(color)

        elif role == CHECK_ROLE:
            obj = self.objects[index.row()]
            objCol = self.columns[index.column()]
            value = objCol.getValue(obj)
            if isinstance(value, bool):
                return CHECKED if value else UNCHECKED
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
