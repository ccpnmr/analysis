__author__ = 'simon1'


from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Table import ObjectTable, Column
from ccpn.ui.gui.modules.peakUtils import getPeakPosition, getPeakAnnotation


from PyQt4 import QtGui

class GuiTableGenerator(QtGui.QWidget, Base):


  def __init__(self, parent, objectLists, actionCallback, columns=None, getColumnsFunction=None, selector=None, tipTexts=None,
               objectType=None, multiSelect=False, unitPulldown=None, selectionCallback=None, **kw):

      QtGui.QWidget.__init__(self, parent)
      Base.__init__(self, **kw)
      self.columns = columns
      self.objectType = objectType
      self.objectLists = objectLists
      if len(self.objectLists) > 0:
        self.objectList = objectLists[0]
      else:
        self.objectList = None
      self.getColumnsFunction = getColumnsFunction
      self.unitPulldown = unitPulldown
      self._getColumns(columns, tipTexts)
      self.tipTexts = tipTexts
      self.table = ObjectTable(self, self._getColumns(columns, tipTexts), [], actionCallback=actionCallback,
                               multiSelect=multiSelect, selectionCallback=selectionCallback,
                               grid=(0, 0), gridSpan=(1, 5))

      if selector is not None:
        self._updateContents()
        self.selector = selector
        self.selector.setCallback(self._changeObjectList)
        self._updateSelectorContents()


  def _changeObjectList(self, objectList:object):
    """
    Changes the objectList specified in the selector.
    """
    if self.selector.currentText() == '<All>':
      self.table.setObjects(getattr(self.objectList.project, self.objectType))


    elif objectList is not self.objectList:

      self.objectList = objectList
      self._updateContents()


  def _updateContents(self):
    """
    Changes the contents of the objectTable based on the objectList specified in the selector.
    """

    objectList = self.objectList

    if objectList:
      if hasattr(objectList, '_childClasses'):
        objectsName = objectList._childClasses[0]._pluralLinkName
        columns = self._getColumns(self.columns, tipTexts=self.tipTexts)
        self.table.setObjectsAndColumns(getattr(objectList, objectsName), columns)
      # elif objectList.pid == '<All>':
      #   columns = self._getColumns(self.columns, tipTexts=self.tipTexts)
      #   self.table.setObjects(objectList.objects)
      else:
        columns = self._getColumns(self.columns, tipTexts=self.tipTexts)
        self.table.setObjects(objectList.objects)

    self.table.resizeColumnsToContents()

  def _getColumns(self, columns, tipTexts):

    tableColumns = []
    if self.getColumnsFunction:
      columns = self.getColumnsFunction(self.objectList)[0]
      tipTexts = self.getColumnsFunction(self.objectList)[1]

    if len(columns) > 0:
      for column in columns:
        c = Column(column[0], column[1], tipText=tipTexts[columns.index(column)])
        tableColumns.append(c)

      detailsColumn = Column('Details', lambda obj: self._getCommentText(obj), setEditValue=lambda obj, value: self._setObjectDetails(obj, value))
      tableColumns.append(detailsColumn)
    return tableColumns

  def _setObjectDetails(self, obj, value):
    obj.comment = value


  def _getCommentText(self, obj):
    if obj.comment == '' or not obj.comment:
      return ' '
    else:
      return obj.comment

  def _updateSelectorContents(self):
    """
    Sets the contents of the selector and object table if object list is specified on instantiation.
    """

    if self.objectList is not None:
      self.objectLists = list(set(self.objectLists))
      texts = ['%s' % objectList.pid for objectList in self.objectLists]

      self.selector.setData(texts=texts, objects=self.objectLists)
    if not self.objectList.shortClassName == 'PL':
     if '<All>' not in self.selector.texts:
       self.selector.addItem('<All>')


  def updateTable(self):
    """
    Update contents of the table, including addition/deletion of objects.
    """
    # self.updateSelectorContents()
    self._updateContents()







