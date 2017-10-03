
from PyQt5 import QtGui, QtWidgets, QtCore

from ccpn.ui.gui.widgets.PulldownList import PulldownList


class FilteringPulldownList(PulldownList):
  def __init__(self, parent=None, **kw):
      PulldownList.__init__(self, parent, **kw)

      self.setEditable(True)
      self.setFocusPolicy(QtCore.Qt.StrongFocus)
      self.setInsertPolicy(PulldownList.NoInsert)
      self._proxy=QtGui.QSortFilterProxyModel(self, filterCaseSensitivity=QtCore.Qt.CaseInsensitive)
      self._proxy.setSourceModel(self.model())

      self._completer=QtGui.QCompleter(
          self._proxy,
          self,
          activated=self.onCompleterActivated
      )

      self._completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)
      self.setCompleter(self._completer)
      self.completer().popup().setObjectName("CompleterList")
      self.lineEdit().textEdited.connect(self._proxy.setFilterFixedString)

  def onCompleterActivated(self, text):
      if not text: return
      self.setCurrentIndex(self.findText(text))
      self.activated[str].emit(self.currentText())