"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-05-17 18:57:39 +0100 (Tue, May 17, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2016-09-16 12:30:22 +0100 (Tue, September 16, 2016) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore

from ccpn.ui.gui.widgets.PulldownList import PulldownList


class FilteringPulldownList(PulldownList):
  def __init__(self, parent=None, backgroundText='', **kwds):
      super().__init__(parent, **kwds)

      self.setEditable(True)
      self.setFocusPolicy(QtCore.Qt.StrongFocus)
      self.setInsertPolicy(PulldownList.NoInsert)
      self._proxy=QtCore.QSortFilterProxyModel(self, filterCaseSensitivity=QtCore.Qt.CaseInsensitive)
      self._proxy.setSourceModel(self.model())

      self._completer=QtWidgets.QCompleter(
          self._proxy,
          self,
          activated=self.onCompleterActivated
      )

      self._completer.setCompletionMode(QtWidgets.QCompleter.UnfilteredPopupCompletion)
      self.setCompleter(self._completer)
      self.completer().popup().setObjectName("CompleterList")
      self.lineEdit().textEdited.connect(self._proxy.setFilterFixedString)
      if backgroundText:
          self.lineEdit().setPlaceholderText(str(backgroundText))

  def onCompleterActivated(self, text):
      if not text: return
      self.setCurrentIndex(self.findText(text))
      self.activated[str].emit(self.currentText())
