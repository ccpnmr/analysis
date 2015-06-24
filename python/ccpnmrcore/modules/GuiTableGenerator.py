__author__ = 'simon1'

from ccpncore.gui.Table import ObjectTable, Column
from ccpncore.gui.Widget import Widget
from ccpnmrcore.modules.peakUtils import getPeakPosition, getPeakAnnotation


from PyQt4 import QtGui

class GuiTableGenerator(QtGui.QWidget):

  def __init__(self, parent, objectLists, callback, columns, selector, **kw):

      QtGui.QWidget.__init__(self, parent)

      self.columns = columns
      # self.table = ObjectTable(self, self._getColumns, [], callback=callback, grid=(0, 0))
      self.objectList = objectLists[0]
      self.sampledDims = {}
      self._getColumns(columns)
      self.table = ObjectTable(self, self._getColumns(columns), [], callback=callback)
      self.updateContents()
      selector.setCallback(self.changeObjectList)

  def changeObjectList(self, objectList):

    if objectList is not self.objectList:

      self.objectList = objectList
      self.updateContents()


  def updateContents(self):

    objectList = self.objectList

    if objectList:
      objectsName = objectList._childClasses[0]._pluralLinkName

      columns = self._getColumns(self.columns)
      self.table.setObjectsAndColumns(objectList.get(objectsName), columns)

  def _getColumns(self, columns):

    tableColumns = []
    tableColumns.append(Column(*columns[0]))

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
      c = Column(column[0], column[1])
      tableColumns.append(c)

    return tableColumns




