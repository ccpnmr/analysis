__author__ = 'simon1'

from ccpncore.gui.Label import Label
from ccpncore.util.Types import Sequence
from application.core.DropBase import DropBase
import json

from PyQt4 import QtGui, QtCore

class SpinSystemLabel(DropBase, Label):


  def __init__(self, parent, text, appBase, strip=None, **kw):

    Label.__init__(self, parent, text, **kw)
    DropBase.__init__(self, appBase)
    self.strip = strip
    self.parent = parent
    # self.project = appBase.project
    # if dragDrop is True:
    #   DropBase.__init__(self, self.parent().dockArea.guiWindow._appBase)

    self.setAcceptDrops(True)

  def mousePressEvent(self, event:QtGui.QMouseEvent):
    """
    Re-implementation of the mouse press event to enable a strip to be dragged as a json object
    containing its pid and a modifier key to encode the direction to drop the strip.
    """
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
      pass
      # self.close()
    else:
      self.show()

  def processStrips(self, pids:Sequence[str], event:QtGui.QMouseEvent):
    """
    Takes a sequence of pids and if the correspond to strip pids, a new strip is created in the correct
    direction specified in the sequence and the data of the source strip is displayed in the new strip.
    """

    for pid in pids:
      if wrapperObject.guiSpectrumDisplay.pid == self.strip.guiSpectrumDisplay.pid:
        return
      current = self._appBase.current
      project = self._appBase.project
      direction = pid[-2:]
      processedPid = pid[:-2]
      wrapperObject = self._appBase.getByPid(processedPid)
      nmrResidue = wrapperObject.planeToolbar.spinSystemLabel.text()

      if direction == '-1':
        sinkIndex = self._appBase.getByPid(self.strip.pid)._wrappedData.index

      else:
        sinkIndex = self._appBase.getByPid(self.strip.pid)._wrappedData.index+1

      if wrapperObject.guiSpectrumDisplay.pid.id == self.strip.guiSpectrumDisplay.pid.id:
        wrapperObject.moveTo(sinkIndex)

      else:
        self.strip.guiSpectrumDisplay.copyStrip(wrapperObject, sinkIndex)
        if direction == '-1':
          current.strip = self.strip.guiSpectrumDisplay.strips[-1]
          current.nmrResidue = project.getByPid('NR:@-.'+nmrResidue+'-1.')
        else:
          current.strip = self.strip.guiSpectrumDisplay.strips[sinkIndex]
          current.nmrResidue = project.getByPid('NR:@-.'+nmrResidue+'.')
        if hasattr(self._appBase.mainWindow, 'bbModule'):
          self._appBase.mainWindow.bbModule.navigateTo(current.nmrResidue, strip=current.strip)
          current.strip.planeToolbar.spinSystemLabel.setText(nmrResidue)



