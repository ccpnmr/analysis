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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-08-22 16:32:26 +0100 (Tue, Aug 22, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-08-22 10:28:42 +0000 (Tue, Aug 22, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.framework.lib.Plugin import Plugin
from ccpn.ui.gui.modules.PluginModule import PluginModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning, showWarning
from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import ProjectTreeCheckBoxes

class CyanaGuiPlugin(PluginModule):



  def __init__(self, mainWindow=None, plugin=None, application=None, **kw):
    super(CyanaGuiPlugin, self)
    PluginModule.__init__(self,mainWindow=mainWindow, plugin=plugin, application=application)

    self.treeView = ProjectTreeCheckBoxes(self.mainWidget, project=self.project, grid=(0,0))






class CyanaPlugin(Plugin):
  PLUGINNAME = 'Cyana'
  guiModule = CyanaGuiPlugin

  def run(self, **kwargs):
    ''' Insert here the script for running Cyana '''
    print('Running Cyana')




CyanaPlugin.register() # Registers the pipe in the pluginList