"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Widget import Widget
from functools import partial
from ccpn.util.Logging import getLogger


class ObjectTableFilter(Widget):
  def __init__(self, table, parent=None, **kwds):
    super().__init__(parent, setLayout=False, **kwds)
    self.table = table
    self.origObjects = self.table._objects

    labelColumn = Label(self,'Search in',)
    self.columnOptions = PulldownList(self,)
    self.columnOptions.setMinimumWidth(self.columnOptions.sizeHint().width()*2)
    self.searchLabel = Label(self,'Search for',)
    self.edit = LineEdit(self,)
    self.searchButtons = ButtonList(self, texts=['Close','Reset','Search'], tipTexts=['Close Search','Restore Table','Search'],
                                   callbacks=[self.hideSearch, partial(self.restoreTable, self.table),
                                              partial(self.findOnTable, self.table)])
    self.searchButtons.buttons[1].setEnabled(False)

    self.widgetLayout = QtWidgets.QHBoxLayout()
    self.setLayout(self.widgetLayout)
    ws = [labelColumn,self.columnOptions, self.searchLabel,self.edit, self.searchButtons]
    for w in ws:
      self.widgetLayout.addWidget(w)
    self.setColumnOptions()

  def setColumnOptions(self):
    columns = self.table._columns
    texts = [c.heading for c in columns]
    objectsRange = range(len(columns))

    self.columnOptions.clear()
    self.columnOptions.addItem('Whole Table', object=None)
    for i, text in enumerate(texts):
      self.columnOptions.addItem(text, objectsRange[i])
    self.columnOptions.setIndex(0)

  def updateSearchWidgets(self, table):
    self.table = table
    self.origObjects = self.table._objects
    self.setColumnOptions()
    self.searchButtons.buttons[1].setEnabled(False)

  def hideSearch(self):
    self.restoreTable(self.table)
    if self.table.searchWidget is not None:
      self.table.searchWidget.hide()

  def restoreTable(self, table):
    #TODO:ED this works for all objects in the project EXCEPT PandasDataframes which
    # don't have _parent

      if len(self.table._objects)>0:
        if hasattr(self.table._objects[0], '_parent'):
          parentObjects = self.table._objects[0]._parent
          if parentObjects is not  None:
            if hasattr(parentObjects, '_childClasses'):
              cC = parentObjects._childClasses
              if len(cC)>0:
                if hasattr(parentObjects._childClasses[0], '_pluralLinkName'):
                  names = parentObjects._childClasses[0]._pluralLinkName
                  originalObjects = getattr(parentObjects, names)
                  table.setObjects(originalObjects)

      self.edit.clear()
      self.searchButtons.buttons[1].setEnabled(False)

  def findOnTable(self, table):

    if self.edit.text() == '' or None:
      self.restoreTable(table)
      return

    self.table = table
    self.origObjects = self.table._objects
    self.table.setObjects(self.origObjects, filterApplied=True)

    text = self.edit.text()
    columns = self.table._columns

    if self.columnOptions.currentObject() is None:
      allMatched = []
      for i in range(len(columns)):
        objCol = columns[i]
        matched = self.searchMatches(objCol, text)
        allMatched.append(matched)
      matched = set([i for m in allMatched for i in m])   #making a single list of matching objs

    else:
      objCol = columns[self.columnOptions.currentObject()]
      matched = self.searchMatches(objCol, text)

    if matched:
      self.table.setObjects(matched, filterApplied=True)
      self.searchButtons.buttons[1].setEnabled(True)
    else:
      self.searchButtons.buttons[1].setEnabled(False)
      self.restoreTable(table)
      MessageDialog.showWarning('Not found', '')

  def searchMatches(self, objCol, text):
    matched = []
    objs = self.table._objects
    for obj in objs:
      value = u'%s' % (objCol.getValue(obj))
      if str(text) in str(value):
        matched.append(obj)
      elif str(text) == str(value):
        matched.append(obj)
    return  matched

  def setFilteredObjects(self):
    selected = self.table.getSelectedObjects()
    self.table.setObjects(selected)
