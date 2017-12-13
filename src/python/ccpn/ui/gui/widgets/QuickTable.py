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

import re

from PyQt4 import QtGui, QtCore
import pandas as pd
from pyqtgraph import TableWidget
import os
from ccpn.core.lib.CcpnSorting import universalSortKey
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
from functools import partial

from collections import OrderedDict
from ccpn.util.Logging import getLogger

# BG_COLOR = QtGui.QColor('#E0E0E0')


class QuickTable(TableWidget, Base):

  def __init__(self, parent, columns,
               objects=None,
               actionCallback=None, selectionCallback=None,
               multiSelect=False, selectRows=True, numberRows=False, autoResize=False,
               enableExport=True, enableDelete=True,
               **kw):

    TableWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    self.setHorizontalScrollMode(self.ScrollPerItem)
    self.setVerticalScrollMode(self.ScrollPerItem)
    self._hiddenColumns = []

    self.multiSelect = multiSelect
    if multiSelect:
      self.setSelectionMode(self.ExtendedSelection)
    else:
      self.setSelectionMode(self.SingleSelection)

    self.selectRows = selectRows
    if selectRows:
      self.setSelectionBehavior(self.SelectRows)
    else:
      self.setSelectionBehavior(self.SelectItems)
