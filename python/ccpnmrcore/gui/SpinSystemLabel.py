__author__ = 'simon1'

from ccpncore.gui.Label import Label
from ccpnmrcore.DropBase import DropBase
import json

from PyQt4 import QtGui, QtCore

class SpinSystemLabel(DropBase, Label):


  def __init__(self, parent, text, appBase, strip=None, **kw):

    Label.__init__(self, parent, text, **kw)
    DropBase.__init__(self, appBase)
    self.strip = strip
    self.parent = parent
    # if dragDrop is True:
    #   DropBase.__init__(self, self.parent().dockArea.guiWindow._appBase)

    self.setAcceptDrops(True)

  def mousePressEvent(self, event):
    event.accept()
    mimeData = QtCore.QMimeData()
    # itemData = QtCore.QByteArray(self.strip.pid or 'None')
    if event.modifiers() & QtCore.Qt.ShiftModifier:
      itemData = json.dumps({'pids':[self.strip.pid+'-1']})
    else:
      itemData = json.dumps({'pids':[self.strip.pid+'+1']})
    mimeData.setData('ccpnmr-json', itemData)
    mimeData.setText(itemData)
    drag = QtGui.QDrag(self)
    drag.setMimeData(mimeData)
    if drag.exec_(QtCore.Qt.MoveAction | QtCore.Qt.CopyAction, QtCore.Qt.CopyAction) == QtCore.Qt.MoveAction:
      self.close()
    else:
      self.show()

  def processStrip(self, pid):

    direction = pid[-2:]
    processedPid = pid[:-2]
    wrapperObject = self._appBase.getById(processedPid)

    if direction == '-1':
      sinkIndex = self._appBase.getById(self.strip.pid)._wrappedData.index
    else:
      sinkIndex = self._appBase.getById(self.strip.pid)._wrappedData.index+1
    if wrapperObject.guiSpectrumDisplay.pid.id == self.strip.guiSpectrumDisplay.pid.id:
      wrapperObject.moveTo(sinkIndex)
    else:
      self.strip.guiSpectrumDisplay.copyStrip(wrapperObject, sinkIndex)

