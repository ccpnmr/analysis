"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2018-12-20 15:53:25 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
import re

from PyQt5 import QtGui, QtWidgets
import pandas as pd
from pyqtgraph import TableWidget
import os
from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.core.lib.CallBack import CallBack
from ccpn.core.lib.DataFrameObject import DataFrameObject
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.TableModel import ObjectTableModel
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.TableFilter import ObjectTableFilter
from ccpn.ui.gui.widgets.ColumnViewSettings import ColumnViewSettingsPopup
from ccpn.ui.gui.widgets.TableModel import ObjectTableModel
from ccpn.core.lib.Notifiers import Notifier
from functools import partial
from collections import OrderedDict

from collections import OrderedDict
from ccpn.util.Logging import getLogger


class QuickTableFilter(Frame):
  def __init__(self, table, parent=None, **kwds):
    super().__init__(parent, setLayout=False, **kwds)

    self.table = table
    self._parent = parent

    labelColumn = Label(self,'Search in',)
    self.columnOptions = PulldownList(self,)
    # self.columnOptions.setMinimumWidth(self.columnOptions.sizeHint().width()*2)
    self.columnOptions.setMinimumWidth(40)
    self.searchLabel = Label(self,'Search for',)
    self.edit = LineEdit(self,)
    # self.searchButtons = ButtonList(self, texts=['Close','Reset','Search'], tipTexts=['Close Search','Restore Table','Search'],
    #                                callbacks=[self.hideSearch,
    #                                            partial(self.restoreTable, self.table),
    #                                            partial(self.findOnTable, self.table)])
    self.searchButtons = ButtonList(self, texts=['Search','Reset','Close'], tipTexts=['Search','Restore Table','Close Search'],
                                   callbacks=[partial(self.findOnTable, self.table),
                                              partial(self.restoreTable, self.table),
                                              self.hideSearch])
    self.searchButtons.buttons[1].setEnabled(False)
    self.searchButtons.setFixedHeight(30)

    self.widgetLayout = QtGui.QHBoxLayout()
    self.setLayout(self.widgetLayout)
    ws = [labelColumn,self.columnOptions, self.searchLabel,self.edit, self.searchButtons]
    for w in ws:
      self.widgetLayout.addWidget(w)
    self.setColumnOptions()
    self.widgetLayout.setContentsMargins(0,0,0,0)
    self.setContentsMargins(0,0,0,0)

    self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Minimum)

  def setColumnOptions(self):
    # columns = self.table._dataFrameObject.columns
    # texts = [c.heading for c in columns]
    # objectsRange = range(len(columns))

    texts = self.table._dataFrameObject.userHeadings
    objectsRange = range(len(texts))

    self.columnOptions.clear()
    self.columnOptions.addItem('<Whole Table>', object=None)
    for i, text in enumerate(texts):
      self.columnOptions.addItem(text, objectsRange[i])
    self.columnOptions.setIndex(0)

  def updateSearchWidgets(self, table):
    self.table = table
    self.setColumnOptions()
    self.searchButtons.buttons[1].setEnabled(False)

  def hideSearch(self):
    self.restoreTable(self.table)
    if self.table.searchWidget is not None:
      self.table.searchWidget.hide()

  def restoreTable(self, table):
    self.table.refreshTable()
    self.edit.clear()
    self.searchButtons.buttons[1].setEnabled(False)

  def findOnTable(self, table, matchExactly=False, ignoreNotFound=False):
    if self.edit.text() == '' or None:
      self.restoreTable(table)
      return

    self.table = table
    text = self.edit.text()

    if matchExactly:
      func = lambda x:text == str(x)
    else:
      func = lambda x:text in str(x)

    columns = self.table._dataFrameObject.headings

    if self.columnOptions.currentObject() is None:

      df = self.table._dataFrameObject.dataFrame
      idx = df[columns[0]].apply(func)
      for col in range(1, len(columns)):
        idx = idx | df[columns[col]].apply(func)
      self._searchedDataFrame = df.loc[idx]

    else:
      objCol = columns[self.columnOptions.currentObject()]

      df = self.table._dataFrameObject.dataFrame
      self._searchedDataFrame = df.loc[df[objCol].apply(func)]

    if not self._searchedDataFrame.empty:
      self.table.setData(self._searchedDataFrame.values)
      self.table.refreshHeaders()
      self.searchButtons.buttons[1].setEnabled(True)
    else:
      self.searchButtons.buttons[1].setEnabled(False)
      self.restoreTable(table)
      if not ignoreNotFound:
        MessageDialog.showWarning('Not found', text)

  def selectSearchOption(self, sourceTable, columnObject, value):
    try:
      self.columnOptions.setCurrentText(columnObject.__name__)
      self.edit.setText(value)
      self.findOnTable(self.table, matchExactly=False, ignoreNotFound=True)
    except Exception as es:
      getLogger().debug('column not found in table')

def attachSearchWidget(parent, table):
  """
  Attach the search widget to the bottom of the table widget
  """
  returnVal = False
  try:
    # if table._parent is not None:
    #   parentLayout = None
    #   if isinstance(table._parent, Base):
    #     if hasattr(table.parent, 'getLayout'):
    #       parentLayout = table._parent.getLayout()
    #     else:
    #       # TODO Add the search widget somewhere. Popup?
    #       return False

    parentLayout = table.parent().getLayout()

    if isinstance(parentLayout, QtGui.QGridLayout):
      idx = parentLayout.indexOf(table)
      location = parentLayout.getItemPosition(idx)
      if location is not None:
        if len(location)>0:
          row, column, rowSpan, columnSpan = location
          table.searchWidget = QuickTableFilter(parent=parent, table=table, vAlign='b')
          parentLayout.addWidget(table.searchWidget, row+1, column, 1, columnSpan)
          table.searchWidget.setFixedHeight(30)
          table.searchWidget.hide()

          # TODO:ED move this to the tables
          # parentLayout.setVerticalSpacing(0)
        returnVal = True
  except Exception as es:
    getLogger().warning('Error attaching search widget: %s' % str(es))
  finally:
    return returnVal
