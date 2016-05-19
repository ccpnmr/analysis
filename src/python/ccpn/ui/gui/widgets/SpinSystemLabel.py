__author__ = 'simon1'

from ccpn.core.Project import Project
from ccpn.core.NmrResidue import NmrResidue

from ccpn.util import Pid

from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import ResonanceGroup as ApiResonanceGroup
# from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import Strip as ApiStrip
from ccpn.ui.gui.widgets.Label import Label
from typing import Sequence
from ccpn.ui.gui.DropBase import DropBase
import json



from PyQt4 import QtGui, QtCore

class SpinSystemLabel(DropBase, Label):


  def __init__(self, parent, text, appBase, strip=None, **kw):

    Label.__init__(self, parent, text, **kw)
    DropBase.__init__(self, appBase)
    self.strip = strip
    self.parent = parent
    self.mousePressEvent = self._mousePressEvent
    # self.project = appBase.project
    # if dragDrop is True:
    #   DropBase.__init__(self, self.parent().dockArea.guiWindow._appBase)

    self.setAcceptDrops(True)

  def _mousePressEvent(self, event:QtGui.QMouseEvent):
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

      current = self._appBase.current
      project = self._appBase.project
      direction = pid[-2:]
      processedPid = pid[:-2]
      wrapperObject = self._appBase.getByPid(processedPid)
      nmrResidue = wrapperObject.planeToolbar.spinSystemLabel.text()
      nr1 = current.nmrResidue
      if wrapperObject.pid == self.strip.pid:
        return
      if direction == '-1':
        sinkIndex = self._appBase.getByPid(self.strip.pid)._wrappedData.index

      else:
        sinkIndex = self._appBase.getByPid(self.strip.pid)._wrappedData.index+1

      if wrapperObject.guiSpectrumDisplay.pid.id == self.strip.guiSpectrumDisplay.pid.id:
        wrapperObject.moveTo(sinkIndex)

      else:
        self.strip.guiSpectrumDisplay.copyStrip(wrapperObject, sinkIndex)
        if direction == '-1':

          nr2 = project.getByPid('NR:%s' % nmrResidue)
          nr1.connectPrevious(nr2)
          current.strip = self.strip.guiSpectrumDisplay.strips[-1]
          current.nmrResidue = nr2.offsetNmrResidues[0]
          current.nmrChain = nr2.nmrChain
        else:
          nr2 = project.getByPid('NR:%s' % nmrResidue)
          nr1.connectNext(nr2)
          current.strip = self.strip.guiSpectrumDisplay.strips[sinkIndex]
          current.nmrResidue = nr2
          current.nmrChain = nr2.nmrChain
        if hasattr(self._appBase.mainWindow, 'bbModule'):
          self._appBase.mainWindow.bbModule._navigateTo(current.nmrResidue, strip=current.strip)
          current.strip.planeToolbar.spinSystemLabel.setText(current.nmrResidue._id)



def _renameNmrResidueForGraphics(nmrResidue:NmrResidue, oldPid:str):
  """Effect rename for NmrResidue"""
  oldId = oldPid.split(Pid.PREFIXSEP, 1)[-1]
  for strip in nmrResidue.project.strips:
    if strip.planeToolbar.spinSystemLabel.text() == oldId:
      strip.planeToolbar.spinSystemLabel.setText(nmrResidue._id)
# Notify PeakListView change when PeakList changes
NmrResidue.setupCoreNotifier('rename', _renameNmrResidueForGraphics)


# def _resetNmrResiduePidForGraphics(project:Project, apiResonanceGroup:ApiResonanceGroup):
#   """Reset pid for NmrResidue and all offset NmrResidues"""
#   getDataObj = project._data2Obj.get
#   obj = getDataObj(apiResonanceGroup)
#   for strip in project.strips:
#     if strip.planeToolbar.spinSystemLabel.text() == obj._old_id:
#       strip.planeToolbar.spinSystemLabel.setText(obj._id)
#
#
# Project._setupApiNotifier(_resetNmrResiduePidForGraphics, ApiResonanceGroup, 'setSequenceCode')
# Project._setupApiNotifier(_resetNmrResiduePidForGraphics, ApiResonanceGroup, 'setDirectNmrChain')
# Project._setupApiNotifier(_resetNmrResiduePidForGraphics, ApiResonanceGroup, 'setResidueType')
# Project._setupApiNotifier(_resetNmrResiduePidForGraphics, ApiResonanceGroup, 'setAssignedResidue')
