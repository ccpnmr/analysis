"""Module Documentation here

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
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core import Project
from ccpn.core.lib import Util as ccpnUtil
from ccpn.ui.gui.Base import Base as GuiBase
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.MessageDialog import showWarning


class DropBase(GuiBase):

  def __init__(self, appBase, *args, **kw):

    GuiBase.__init__(self, appBase, *args, **kw)

  def dragEnterEvent(self, event):
    event.accept()

  def dropEvent(self, event):
    """Catch dropEvent and dispatch to processing"""
    from ccpn.ui.gui.lib import Qt as qtUtil

    data, dataType = qtUtil.interpretEvent(event)
    if data and dataType:
      event.accept()
      self.processDropData(data, dataType, event)
    else:
      if isinstance(self, CcpnModule):# restore the native  module drop event.
        CcpnModule.dropEvent(self, event)



  def processDropData(self, data, dataType='pids', event=None):
    """ Process dropped-in data
    Separate function so it can be called from command line as well.
    """
    project = self._appBase.project
    if dataType == 'text':
      # data is a text string
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
