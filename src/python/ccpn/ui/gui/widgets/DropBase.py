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
from PyQt4 import QtGui, QtCore

from ccpn.core import Project
from ccpn.core.lib.Pid import Pid
from ccpn.core.lib import Util as ccpnUtil
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpnmodel.ccpncore.lib.Constants import ccpnmrJsonData

from ccpn.util.Logging import getLogger
logger = getLogger()


class DropBase():
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
    # for now: set 'old-style' behavior
    self.setDropEventCallback(self._dropCallback)

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
        # restore the native module drop event.
        # NB: This has to be after the parseEvent (in the 'old' DropBase); do not know why (GWV)
        if isinstance(self, CcpnModule):
          CcpnModule.dropEvent(self, event)
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


  # 'old-style' drag and drop;
  # TODO: refactor below to be defined in objects receiving the drops via appropriate callback
  # TODO as a GuiNotifier instance

  def _dropCallback(self, data):
    "just a stub for now to call the old processDropData"
    for dataType, datum in data.items():
      if dataType in self._dropTargets:
        print('New-DropBase-event: calling old style>', dataType, datum)
        self.processDropData(datum, dataType)

  def processDropData(self, data, dataType='pids', event=None):
    """ Process dropped-in data
    Separate function so it can be called from command line as well.
    """
    project = self._appBase.project
    if dataType == 'text':
      # data is a text string
      # THIS is so UGLY! and prone to errors!
      if hasattr(self, 'processText'):
        self.processText(data)

    else:
      pids = []
      if dataType == 'pids':
        pids = data

      elif dataType == 'urls':
        # data is list-of-urls
        # Load Urls one by one with normal loaders
        for url in data:
          loaded = project.loadData(url)

          if loaded and isinstance(loaded[0], Project.Project):
            # We have loaded a new project
            return

          # if loaded and loaded[0] is self._appBase.project:
          #   # We have loaded a new project
          #   return

          if self._appBase.ui.mainWindow is not None:
            self._appBase.ui.mainWindow.pythonConsole.writeConsoleCommand("project.loadData('%s')" % url)
          else:
            self._appBase._mainWindow.pythonConsole.writeConsoleCommand("project.loadData('%s')" % url)

          project._logger.info("project.loadData('%s')" % url)

          if loaded:
            if isinstance(loaded, str):
              if hasattr(self, 'processText'):
                self.processText(loaded, event)

            else:
              newPids = [x.pid for x in loaded]
              projects = [x for x in newPids if x.startswith('PR:')]
              if projects:
                pids = projects[:1]
                if len(data) > 1 or len(newPids) > 1:
                  showWarning('Incorrect data load',
                              "Attempt to load project together with other data. Other data ignored")
                break
              else:
                pids.extend(newPids)

          else:
            if isinstance(self, CcpnModule):
              self.overlay.hide()

        for pid in pids:
          pluralClassName = ccpnUtil.pid2PluralName(pid)

          # NBNB Code to put other data types in side bar must go here

          if pluralClassName == 'spectra':
            spectrum = self.getByPid(pid)
            # self._appBase.mainWindow.sideBar.addSpectrum(spectrum)

      else:
        raise ValueError("processDropData does not recognise dataType %s" % dataType)

      # process pids
      if pids:

        # THIS is so UGLY! and prone to errors!

        tags = [ccpnUtil.pid2PluralName(x) for x in pids]
        tags = [x[0].upper() + x[1:] for x in tags]
        if  len(set(tags)) == 1:
          # All pids of same type - process entire list with a single process call
          funcName = 'process' + tags[0]
          if hasattr(self, funcName):
            getattr(self,funcName)(pids, event)
          elif funcName == 'processProjects':
            # We never need to process a project
            pass
          elif dataType != 'urls':
            # Added RHF 16/2/2016. If we have loaded data that is OK, and no warning needed.
            # Why warn if we drop a spectrum file on the side bar?
            project._logger.warning("Dropped data not processed - no %s function defined for %s"
            % (funcName, self))

        else:
          # Treat each Pid separately (but still pass it in a list - NBNB)
          # If we need special functions for multi-type processing they must go here.
          for ii,tag in enumerate(tags):
            funcName = 'process' + tag
            if hasattr(self, funcName):
              getattr(self,funcName)([pids[ii]], event)
            elif dataType != 'urls':
              # Added RHF 16/2/2016. If we have loaded data that is OK, and no warning needed.
              # Why warn if we drop a spectrum file on the side bar?
              project._logger.warning("Dropped data %s not processed - no %s function defined for %s"
              % (pid, funcName, self))
