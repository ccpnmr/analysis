"""
This Module display the "Drop Spectrum here" place holder. It accepts url's to load the various
data and Spectrum and SpectrumGroup pids dragged from the sidebar. Spectra and SpectrumGroups are
subsequently displayed.

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
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.widgets.DropBase import DropBase

from ccpn.util.Logging import getLogger
logger = getLogger()


class BlankDisplay(CcpnModule):

  includeSettingsWidget = False
  className = 'BlankDisplay'

  def __init__(self, mainWindow):

    CcpnModule.__init__(self, parent=mainWindow.moduleArea, mainWindow=mainWindow, name='Blank Display')
    # Derive application, project, and current from mainWindow
    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current

    self.label2 = Label(self.mainWidget, text='Drag Spectrum Here', textColour='#bec4f3', textSize='32',
                                         grid=(0,0), #stretch=(1,1),
                                         hPolicy='minimal', vPolicy='minimal',
                                         hAlign='center', vAlign='center',
                                         acceptDrops=False
                       )

    self.mainWidget.setAcceptDrops(True)
    self.droppedItemNotifier = GuiNotifier(self.mainWidget,
                                          [GuiNotifier.DROPEVENT], [DropBase.URLS, DropBase.PIDS],
                                          self._processDroppedItems)

  #TODO:LUCA: check undo for these actions!
  def _processDroppedItems(self, data):
    """
    This routine processes the items dropped on the canvas
    These are either urls or pids, as the notifier will have filtered for this
    """
    success = False # denote if we got a valid spectrum and should delete BlankDisplay
    # process urls
    for url in data.get('urls',[]):
      print('BlankDisplay._processDroppedItems>>> dropped:', url)
      objects = self.project.loadData(url)

      if objects is not None and len(objects) > 0:
        # NB: In case a new project was dropped, self.project still points to the old project
        # that was deleted first, so that gets corrected!!
        for ii, obj in enumerate(objects):
          if isinstance(obj, Project):
            self.project = obj
          if isinstance(obj, (Spectrum)):
            success = success or self._handlePid(obj.pid)  # pass the object as its pid so we use
                                                           # the same method used to process the pids
    # process pids
    for ii, pid in enumerate(data.get('pids',[])):
      print('BlankDisplay._processDroppedItems>>> dropped:', pid)
      success = success or self._handlePid(pid)

    if success:
      self.mainWindow.deleteBlankDisplay()
      logger.info('application.deleteBlankDisplay()')

  #TODO:LUCA: add handling for SpectrumGroup Pids; also do in GuiSpectrumDisplay
  def _handlePid(self, pid):
    "handle a; return True in case it is a Spectrum or a SpectrumGroup"
    success = False
    obj = self.project.getByPid(pid)
    if obj is not None and isinstance(obj, Spectrum):
      self._createSpectrumDisplay(obj)
      success = True
    elif obj is not None and isinstance(obj, SpectrumGroup):
      self._handleSpectrumGroup(obj)
      success = True
    return success

  def _createSpectrumDisplay(self, spectrum):
    self.mainWindow.createSpectrumDisplay(spectrum)
    # TODO:LUCA: the mainWindow.createSpectrumDisplay should do the reporting to console and log
    # This routine can then be ommitted and the call above replaced by the one remaining line
    self.mainWindow.pythonConsole.writeConsoleCommand(
      "application.createSpectrumDisplay(spectrum)", spectrum=spectrum)
    self.mainWindow.pythonConsole.writeConsoleCommand("application.deleteBlankDisplay()")
    logger.info('spectrum = project.getByPid(%r)' % spectrum.id)
    logger.info('application.createSpectrumDisplay(spectrum)')

  def _handleSpectrumGroup(self, spectrumGroup):
    '''displays spectrumGroup on spectrumDisplay. It creates the display based on the first spectrum of the group.
    Also hides the spectrumToolBar and shows spectrumGroupToolBar '''

    if len(spectrumGroup.spectra) > 0:
      spectrumDisplay = self.mainWindow.createSpectrumDisplay(spectrumGroup.spectra[0])
      for spectrum in spectrumGroup.spectra: # Add the other spectra
        spectrumDisplay.displaySpectrum(spectrum)

      spectrumDisplay.isGrouped = True
      spectrumDisplay.spectrumToolBar.hide()
      spectrumDisplay.spectrumGroupToolBar.show()
      spectrumDisplay.spectrumGroupToolBar._addAction(spectrumGroup)




  def _closeModule(self):
    """
    Re-implementation of closeModule function from CcpnModule.
    """
    CcpnModule._closeModule(self)
    logger.info('Shortcut "ND" to open a new blank display')

