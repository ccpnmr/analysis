__author__ = 'simon1'


from ccpncore.gui.Base import Base
from ccpncore.gui.Table import ObjectTable, Column
from application.core.modules.peakUtils import getPeakPosition, getPeakAnnotation


from PyQt4 import QtGui

class GuiTableGenerator(QtGui.QWidget, Base):

  # NBNB TBD FIXME  This should be cleaned up and made less ahcky:
  # Special cases like extra columns for peak tabels should NOT be done in the general class
  # but e.g. by overriding a function in a subclass.
  # You should not do things like 'objectList._childClasses[0]', but pass in the #
  # type of the class ( like PeakList or Peak, and take it from there
  # You should allow for cses where you did not have just a list class and its only child
  #
  # If you make these special assumnptions, you should say them CLEARLY in the class comment

  def __init__(self, parent, objectLists, actionCallback, columns, selector=None, tipTexts=None,
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
      self.sampledDims = {}
      self.unitPulldown = unitPulldown
      self._getColumns(columns, tipTexts)
      self.tipTexts = tipTexts
      self.table = ObjectTable(self, self._getColumns(columns, tipTexts), [], actionCallback=actionCallback,
                               multiSelect=multiSelect, selectionCallback=selectionCallback,
                               grid=(0, 0), gridSpan=(1, 5))


      if selector is not None:
        self.updateContents()
        self.selector = selector
        self.selector.setCallback(self.changeObjectList)
        self.updateSelectorContents()


  def changeObjectList(self, objectList:object):
    """
    Changes the objectList specified in the selector.
    """
    if self.selector.currentText() == '<All>':
      self.table.setObjects(getattr(self.objectList.project, self.objectType))

    elif objectList is not self.objectList:

      self.objectList = objectList
      self.updateContents()


  def updateContents(self):
    """
    Changes the contents of the objectTable based on the objectList specified in the selector.
    """
    objectList = self.objectList

    if objectList:
      if hasattr(objectList, '_childClasses'):
        objectsName = objectList._childClasses[0]._pluralLinkName
        columns = self._getColumns(self.columns, tipTexts=self.tipTexts)
        self.table.setObjectsAndColumns(getattr(objectList,objectsName), columns)
      elif objectList.pid == '<All>':
        columns = self._getColumns(self.columns, tipTexts=self.tipTexts)
        self.table.setObjects(objectList.objects)
      else:
        columns = self._getColumns(self.columns, tipTexts=self.tipTexts)
        self.table.setObjects(columns)

    self.table.resizeColumnsToContents()

  def _getColumns(self, columns, tipTexts):

    tableColumns = []

    if len(columns) > 0:
      # tableColumns.append(Column(*columns[0], tipText=tipTexts[0], orderFunc=self.orderFunc))
      tableColumns.append(Column(*columns[0], tipText=tipTexts[0]))

    if self.objectList and hasattr(self.objectList, 'shortClassName'):
      if self.objectList.shortClassName == 'PL':
        numDim = self.objectList._parent.dimensionCount

        for i in range(numDim):
          j = i + 1
          c = Column('Assign F%d' % j,
                     lambda pk, dim=i:getPeakAnnotation(pk, dim),
                     tipText='Resonance assignments of peak in dimension %d' % j)
          tableColumns.append(c)

        for i in range(numDim):
          j = i + 1

          sampledDim = self.sampledDims.get(i)
          if sampledDim:
            text = 'Sampled\n%s' % sampledDim.conditionVaried
            tipText='Value of sampled plane'
            unit = sampledDim

          else:
            text = 'Pos F%d' % j
            tipText='Peak position in dimension %d' % j
            unit = self.unitPulldown.currentText()
          c = Column(text,

                   lambda pk, dim=i, unit=unit:getPeakPosition(pk, dim, unit),
                   tipText=tipText)
          tableColumns.append(c)

      if len(columns) > 0:
        for column in columns[1:]:
          c = Column(column[0], column[1], tipText=tipTexts[columns.index(column)])
          tableColumns.append(c)

      detailsColumn = Column('Details', lambda obj: self.getCommentText(obj), setEditValue=lambda obj, value: self.setObjectDetails(obj, value))
      tableColumns.append(detailsColumn)
    return tableColumns

  def setObjectDetails(self, obj, value):
    obj.comment = value


  def getCommentText(self, obj):
    if obj.comment == '' or not obj.comment:
      return ' '
    else:
      return obj.comment

  def updateSelectorContents(self):
    """
    Sets the contents of the selector and object table if object list is specified on instatiation.
    """

    if self.objectList is not None:
      self.objectLists = list(set(self.objectLists))
      texts = ['%s' % objectList.pid for objectList in self.objectLists]

      self.selector.setData(texts=texts, objects=self.objectLists)
    if not self.objectList.shortClassName == 'PL':
     if '<All>' not in self.selector.texts:
       self.selector.addItem('<All>')


  def updateTable(self):
    # self.updateSelectorContents()
    self.updateContents()







