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
__dateModified__ = "$dateModified: 2017-04-07 11:40:38 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.core.Spectrum import Spectrum
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier

from ccpn.util.Logging import getLogger
logger = getLogger()


class BlankDisplay(CcpnModule):

  includeSettingsWidget = False

  def __init__(self):

    CcpnModule.__init__(self, name='Blank Display')
    # project, current, application and mainWindow are inherited from CcpnModule

    self.mainWidget.setAcceptDrops(True)
    self.label2 = Label(self.mainWidget, acceptDrops=True, stretch=(1,1), text='Drag Spectrum Here',
                        textColour='#bec4f3', textSize='32', hPolicy='center', vPolicy='center'
                       )
    self.droppedItemNotifier = GuiNotifier(self.mainWidget,
                                          [GuiNotifier.DROPEVENT], ['urls','pids'],
                                          self._processDroppedItems)

  def _processDroppedItems(self, data):
    """
    This routine processes the items dropped on the canvas
    These are either urls or pids, as the notfier will have filtered for this
    """
    success = False
    for url in data.get('urls',[]):
      print('BlankDisplay._processDroppedItems>>> dropped:', url)
      objects = self.project.loadData(url)

      if objects is not None and len(objects) > 0:
        for ii, obj in enumerate(objects):
          success = success or self._createSpectrumDisplay(obj)

    for ii, pid in enumerate(data.get('pids',[])):
      print('BlankDisplay._processDroppedItems>>> dropped:', pid)
      obj = self.project.getByPid(pid)
      if obj is not None:
        success = success or self._createSpectrumDisplay(obj)

    if success:
      self.mainWindow.deleteBlankDisplay()
      logger.info('application.deleteBlankDisplay()')

  def _createSpectrumDisplay(self, obj):
    """Create a spectrumDisplay if obj is a Spectrum instance
       return True on success
    """
    if isinstance(obj, Spectrum):
      self.mainWindow.createSpectrumDisplay(obj)
      self.mainWindow.pythonConsole.writeConsoleCommand( \
        "application.createSpectrumDisplay(spectrum)", spectrum=obj)
      self.mainWindow.pythonConsole.writeConsoleCommand("application.deleteBlankDisplay()")
      logger.info('spectrum = project.getByPid(%r)' % obj.id)
      logger.info('application.createSpectrumDisplay(spectrum)')
      return True
    
    return False

  def _closeModule(self):
    """
    Re-implementation of closeModule function from CcpnModule.
    """
    CcpnModule._closeModule(self)
    self._appBase.project._logger.info('Shortcut "ND" to open a new blank display')

