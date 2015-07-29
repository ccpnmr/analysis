__author__ = 'simon1'

from ccpncore.gui.Table import ObjectTable, Column
from ccpnmrcore.modules.peakUtils import getPeakPosition, getPeakAnnotation


from PyQt4 import QtGui

class GuiTableGenerator(QtGui.QWidget):

  def __init__(self, parent, callback, columns, selector, tipTexts=None, objects=None, objectLists=None, **kw):

      QtGui.QWidget.__init__(self, parent)

      self.columns = columns

      self.objectList = objects[0]
      self.objectLists = objects
      self.sampledDims = {}
      self._getColumns(columns, tipTexts)
      self.tipTexts = tipTexts
      self.table = ObjectTable(self, columns=self._getColumns(columns, tipTexts), objects=objects, callback=callback)
      if objects:
        self.updateContents(objects)
      else:
        self.updateContents(objectLists[0])
      if selector is not None:
        self.selector = selector
        self.selector.setCallback(self.changeObjectList)
        self.updateSelectorContents()


  def changeObjectList(self, objectList):

    if objectList is not self.objectList:

      self.objectList = objectList
      print(self.objectList)
      self.updateContents()


  def updateContents(self, objects=None, objectList=None):


    if objectList:
      objectsName = objectList._childClasses[0]._pluralLinkName
      # print('objectLists', objectList, objectList._childClasses, objectList._childClasses[0]._pluralLinkName)
      # print(objectsName, 'objectsName')
      print(objectList.sampleComponents)
      print(objectList.get(objectsName), 'get')
      columns = self._getColumns(self.columns, tipTexts=self.tipTexts)
      print(self.columns)
      self.table.setObjectsAndColumns(objectList.get(objectsName), columns)
    elif objects:
      columns = self._getColumns(self.columns, tipTexts=self.tipTexts)
      print(columns)
      self.table.setObjectsAndColumns(objects, columns)


  def _getColumns(self, columns, tipTexts):

    tableColumns = []
    print(*columns[0])
    tableColumns.append(Column(*columns[0], tipText=tipTexts[0]))
    if self.objectList:
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


      for column in columns[1:]:
        c = Column(column[0], column[1], tipText=tipTexts[columns.index(column)])
        tableColumns.append(c)

    return tableColumns

  def updateSelectorContents(self):
    if self.objectList is not None:
      # if self.objectList.shortClassName == 'PL':
      #   texts = ['%s' % peakList.pid for peakList in self.objectLists]
      # else:
      texts = ['%s' % objectList.pid for objectList in self.objectLists]
      print(texts, 'texts')
      self.selector.setData(texts=texts, objects=self.objectLists)

      texts = []
      # texts = ['%s' % (objectList.name for objectList in self.objectLists)]
      for objectList in self.objectLists:
        texts.append(objectList.name)

      objects = [objectList for objectList in self.objectLists]
      self.selector.setData(texts=texts, objects=self.objectLists)



