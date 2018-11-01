"""
Define routines for a dropable widget
This module is subclassed by widgets.Base and should not be used directly

GWV April-2017: Drived from an earlier version of DropBase

"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:53 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
from ccpn.core.lib.Pid import Pid
from ccpn.util.Logging import getLogger


class DropBase:
  """
  Class to implement drop and drag
  Callback signature on drop: dropEventCallback(dataDict)
  """

  # drop targets
  URLS = 'urls'
  TEXT = 'text'
  PIDS = 'pids'
  IDS  = 'ids'
  _dropTargets = (URLS, TEXT, PIDS, IDS)

  from ccpn.util.Constants import ccpnmrJsonData as JSONDATA

  def __init__(self, acceptDrops, *args, **kw):

    self._dropEventCallback = None
    self._enterEventCallback = None
    self._dragMoveEventCallback = None
    self.setAcceptDrops(acceptDrops)

  def setDropEventCallback(self, callback):
    "Set the callback function for drop event"
    self._dropEventCallback = callback

  def dragEnterEvent(self, event):
    dataDict = self.parseEvent(event)
    if dataDict is not None and len(dataDict) > 1:
      event.accept()
      if self._dragMoveEventCallback is not None:
        self._dragMoveEventCallback(dataDict)
    event.accept()

  def setDragMoveEventCallback(self, callback):
    self._dragMoveEventCallback = callback

  def setDragEnterEventCallback(self, callback):
    self._enterEventCallback = callback

  def dragMoveEvent(self, event):
    dataDict = self.parseEvent(event)
    if dataDict is not None and len(dataDict) > 1:
      if self._dragMoveEventCallback is not None:
        self._dragMoveEventCallback(dataDict)
    event.accept()

  def dropEvent(self, event):
    """
    Catch dropEvent and dispatch to processing callback
    'Native' treatment of CcpnModule instances
    """

    # Needs to be here to prevent circular imports as CcpnModule imports several Widgets which import DropBase
    from ccpn.ui.gui.modules.CcpnModule import CcpnModule

    if isinstance(self, CcpnModule):
      CcpnModule.dropEvent(self, event)
      return

    if self.acceptDrops():

      dataDict = self.parseEvent(event)
      getLogger().debug('Accepted drop with data:%s' % dataDict)
      getLogger().debug('DropBase-event>: %s callback: %s data: %s' % (self, self._dropEventCallback, dataDict))

      if dataDict is not None and len(dataDict) > 1:
        event.accept()
        if self._dropEventCallback is not None:
          self._dropEventCallback(dataDict)

    else:
      getLogger().debug('Widget not droppable')

  def parseEvent(self, event) -> dict:
    """ 
    Interpret drop event; extract urls, text or JSONDATA dicts 
    convert PIDS to Pid object's
    return a dict with 
      - event, source key,values pairs
      - (type, data) key,value pairs,
    """
    data = dict(
      event = event,
      source = event.source()
    )
    mimeData = event.mimeData()

    if mimeData.hasFormat(DropBase.JSONDATA):
      data['isCcpnJson'] = True
      jsonData = json.loads(mimeData.text())
      if jsonData != None and len(jsonData) > 0:
        data.update(jsonData)
      if self.PIDS in data:
        newPids = [Pid(pid) for pid in data[self.PIDS]]
        data[self.PIDS] = newPids

    elif event.mimeData().hasUrls():
      filePaths = [url.path() for url in event.mimeData().urls()]
      data[self.URLS] = filePaths

    elif event.mimeData().hasText():
      data[self.TEXT] = event.mimeData().text()

    return data
