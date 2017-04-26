"""
Define routines for a dropable widget
This module is subclassed by widgets.Base and should not be used directly

GWV April-2017: Drived from an earlier version of DropBase

"""

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
__dateModified__ = "$dateModified: 2017-04-07 11:40:37 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
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
from ccpnmodel.ccpncore.lib.Constants import ccpnmrJsonData

from ccpn.util.Logging import getLogger
logger = getLogger()


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

  JSONDATA = ccpnmrJsonData #TODO:RASMUS: check why this comes from ccpncore

  def __init__(self, acceptDrops, *args, **kw):

    self._dropEventCallback = None
    self.setAcceptDrops(acceptDrops)

  def setDropEventCallback(self, callback):
    "Set the callback function for drop event"
    self._dropEventCallback = callback

  def dragEnterEvent(self, event):
    event.accept()

  def dropEvent(self, event):
    """
    Catch dropEvent and dispatch to processing callback
    'Native' treatment of CcpnModule instances
    """

    # Needs to be here to prevent circular imports as CcpnModule imports sevral Widgets which import DropBase
    from ccpn.ui.gui.modules.CcpnModule import CcpnModule

    if isinstance(self, CcpnModule):
      CcpnModule.dropEvent(self, event)
      return

    if self.acceptDrops():

      dataDict = self.parseEvent(event)
      logger.debug('Accepted drop with data:%s' % dataDict)
      print('New-DropBase-event>', self, self.accessibleName(), dataDict)

      if dataDict is not None and len(dataDict) > 1:
        event.accept()
        if self._dropEventCallback is not None:
          self._dropEventCallback(dataDict)

    else:
      logger.debug('Widget not droppable')

  def parseEvent(self, event):
    """ 
    Interpret drop event; extract urls, text or JSONDATA dicts 
    convert PIDS to Pid object's
    return a dict with (type, data) key, value pairs
    """
    data = dict(
      event = event
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
      data['urls'] = filePaths

    elif event.mimeData().hasText():
      data['text'] = event.mimeData().text()

    return data
