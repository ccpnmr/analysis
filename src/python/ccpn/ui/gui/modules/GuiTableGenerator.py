#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:04 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon1 $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Table import ObjectTable, Column


from PyQt4 import QtGui

class GuiTableGenerator(QtGui.QWidget, Base):


  def __init__(self, parent, objectLists, actionCallback, columns=None, getColumnsFunction=None, selector=None,
               tipTexts=None, objectType=None, multiSelect=False, unitPulldown=None, selectionCallback=None, **kw):

      QtGui.QWidget.__init__(self, parent)
      Base.__init__(self, **kw)
      self.columns = columns
      self.objectType = objectType
      self.objectLists = objectLists
      if len(self.objectLists) > 0:
        self.objectList = objectLists[0]
      else:
        self.objectList = None
        return


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




  def setTableCallback(self, callback):
    self.table.callback = None
    self.table.doubleClicked.connect(callback)


  def _changeObjectList(self, objectList:object):
    """
    Changes the objectList specified in the selector.
    """
    if self.selector.currentText() == '<All>':
      self.table.setObjects(getattr(self.objectList.project, self.objectType))


    elif objectList is not self.objectList:

      self.objectList = objectList
      self._updateContents()

    else:
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
      self.objectLists = sorted(set(self.objectLists))
      texts = ['%s' % objectList.pid for objectList in self.objectLists]

      self.selector.setData(texts=texts, objects=self.objectLists)
      if hasattr(self.selector, 'select'): # wb104: PulldownList has this but not sure if other users do
        self.selector.select(self.objectList)
    if not self.objectList.shortClassName == 'PL':
     if '<All>' not in self.selector.texts:
       self.selector.addItem('<All>')


  def updateTable(self):
    """
    Update contents of the table, including addition/deletion of objects.
    """
    # self.updateSelectorContents()
    self._updateContents()







