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
__dateModified__ = "$dateModified: 2017-04-07 11:40:44 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon1 $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Project import Project
from ccpn.core.NmrResidue import NmrResidue

from ccpn.core.lib import Pid

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
    #   DropBase.__init__(self, self.parent().moduleArea.guiWindow._appBase)

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
      nr1 = current.nmrResidue.mainNmrResidue
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
        try:
          nr2 = project.getByPid('NR:%s' % nmrResidue).mainNmrResidue
          if nr1 and nr2:
            if direction == '-1':
              nr1.connectPrevious(nr2)
              current.strip = self.strip.guiSpectrumDisplay.strips[-1]
              current.nmrResidue = nr2.offsetNmrResidues[0]
              current.nmrChain = nr2.nmrChain
            else:
              nr1.connectNext(nr2)
              current.strip = self.strip.guiSpectrumDisplay.strips[sinkIndex]
              current.nmrResidue = nr2
              current.nmrChain = nr2.nmrChain

            # try:
            if hasattr(self.application, 'backboneModule'):
              self.application.backboneModule._navigateTo(current.nmrResidue, strip=current.strip)
              current.strip.planeToolbar.spinSystemLabel.setText(current.nmrResidue._id)
            # except AttributeError:
            #   project._logger.warn('Backbone module is not active')
        except AttributeError:
          project._logger.warn('Cannot connect non-existent Nmr Residues')


def _renameNmrResidueForGraphics(nmrResidue:NmrResidue, oldPid:str):
  """Effect rename for NmrResidue

  For notifiers
  #CCPN INTERNAL"""
  oldId = oldPid.split(Pid.PREFIXSEP, 1)[-1]
  for strip in nmrResidue.project.strips:
    if strip.planeToolbar.spinSystemLabel.text() == oldId:
      strip.planeToolbar.spinSystemLabel.setText(nmrResidue._id)

