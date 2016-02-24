__author__ = 'simon1'


from ccpncore.gui.Entry import Entry
from ccpncore.gui.Table import ObjectTable, Column
from application.core.modules.peakUtils import getPeakPosition, getPeakAnnotation


from PyQt4 import QtGui

# class All(object):
#   def __init__(self, project, objectType):
#     self.pid = '<ALL>'
#     setattr(self, objectType, getattr(project, objectType))
#     self.objects = getattr(project, objectType)



class GuiTableGenerator(QtGui.QWidget):

  def __init__(self, parent, objectLists, callback, columns, selector=None, tipTexts=None, objectType=None,
               multiSelect=False, **kw):

      QtGui.QWidget.__init__(self, parent)
      self.project = objectLists[0].project
      # allList = All(self.project, objectType)
      # objectLists.append(allList)
      self.columns = columns
      self.objectType = objectType
      # self.detailsEntry = Entry(self, text='',
      #                          callback=self.setPeakDetails)
      self.objectLists = objectLists
      if len(self.objectLists) > 0:
        self.objectList = objectLists[0]
      else:
        self.objectList = None
      self.sampledDims = {}
      self._getColumns(columns, tipTexts)
      self.tipTexts = tipTexts
      layout = QtGui.QGridLayout()
      self.setLayout(layout)
      self.table = ObjectTable(self, self._getColumns(columns, tipTexts), [], callback=callback,
                               multiSelect=multiSelect)
      layout.addWidget(self.table, 0, 0, 1, 5)
      self.updateContents()
      if selector is not None:
        self.selector = selector
        self.selector.setCallback(self.changeObjectList)
        self.updateSelectorContents()


  def changeObjectList(self, objectList:object):
    """
    Changes the objectList specified in the selector.
    """
    if self.selector.currentText() == '<ALL>':
      self.table.setObjects(getattr(self.project, self.objectType))

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
        self.table.setObjectsAndColumns(objectList.get(objectsName), columns)
      elif objectList.pid == '<ALL>':
        columns = self._getColumns(self.columns, tipTexts=self.tipTexts)
        self.table.setObjects(objectList.objects)
      else:
        columns = self._getColumns(self.columns, tipTexts=self.tipTexts)
        self.table.setObjects(columns)


  def orderFunc(self, objA, objB):
    list1 = sorted([objA.id, objB.id], key=self._natural_key)
    return list1[0] > list1[1]

  def _natural_key(self, string_):
    import re
    """See http://www.codinghorror.com/blog/archives/001018.html"""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]

  def _getColumns(self, columns, tipTexts):

    tableColumns = []

    if len(columns) > 0:
      tableColumns.append(Column(*columns[0], tipText=tipTexts[0], orderFunc=self.orderFunc))

    if self.objectList and hasattr(self.objectList, 'shortClassName'):
      if self.objectList.shortClassName == 'PL':
        numDim = self.objectList._parent.dimensionCount
        for i in range(numDim):
          j = i + 1
          c = Column('Assign\nF%d' % j,
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
            text = 'Pos\nF%d' % j
            tipText='Peak position in dimension %d' % j
            unit = 'ppm'
          c = Column(text,

                   lambda pk, dim=i, unit=unit:getPeakPosition(pk, dim, unit),
                   tipText=tipText)
          tableColumns.append(c)

      if len(columns) > 0:
        for column in columns[1:]:
          c = Column(column[0], column[1], tipText=tipTexts[columns.index(column)], orderFunc=self.orderFunc)
          tableColumns.append(c)

      detailsColumn = Column('Details', 'comment', setEditValue=lambda pk, value: self.setPeakDetails(pk, value))
      tableColumns.append(detailsColumn)
    return tableColumns

  def setPeakDetails(self, peak, value):
    peak.comment = value

  def updateSelectorContents(self):
    """
    Sets the contents of the selector and object table if object list is specified on instatiation.
    """
    if self.objectList is not None:

      self.objectLists += getattr(self.project, self.objectLists[0]._pluralLinkName)
      self.objectLists = list(set(self.objectLists))
      # if self.objectList.shortClassName == 'PL':
      #   texts = ['%s' % peakList.pid for peakList in self.objectLists]
      # else:
      # texts = ['<ALL>']
      texts = ['%s' % objectList.pid for objectList in self.objectLists]
      self.selector.setData(texts=texts, objects=self.objectLists)


  def updateTable(self):
    self.updateSelectorContents()
    self.updateContents()







