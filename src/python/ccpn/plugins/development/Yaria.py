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
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-08-22 10:28:42 +0000 (Tue, Aug 22, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from PyQt5 import QtCore
from ccpn.framework.lib.Plugin import Plugin
from ccpn.ui.gui.modules.PluginModule import PluginModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning, showWarning
from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import ProjectTreeCheckBoxes

class YariaGuiPlugin(PluginModule):


  def __init__(self, mainWindow=None, plugin=None, application=None, **kw):
    super(YariaGuiPlugin, self)
    PluginModule.__init__(self,mainWindow=mainWindow, plugin=plugin, application=application)
    # self.userPluginPath = self.application.preferences.general.userPluginPath
    self.outputPath = self.application.preferences.general.dataPath
    self.mainWidget.setContentsMargins(20,20,20,20)
    # Run name
    row = 0
    self.runNameLabel = Label(self.mainWidget, 'Run Name', grid=(row,0))
    self.runNameLineEdit = LineEdit(self.mainWidget, 'Run 1', grid=(row, 1))

    # Mode
    row += 1
    self.modeLabel = Label(self.mainWidget, 'Mode', grid=(row, 0))
    self.modeButtons = RadioButtons(self.mainWidget, texts=['Structure Calculation','Candid'], callback=self._manageWidgets,
                                    grid=(row, 1))
    row += 1
    self.inputLabel = Label(self.mainWidget, 'Input', grid=(row, 0))
    ProjectTreeCheckBoxes.checkList = ProjectTreeCheckBoxes.checkList[:4]
    self.treeView = ProjectTreeCheckBoxes(self.mainWidget, project=self.project, grid=(row, 1))
    self.treeView.itemChanged.connect(self._restrictChemicalShiftListSelection)
    self.treeView._uncheckAll()

    # Tolerances
    row += 1
    self.tolerancesLabel = Label(self.mainWidget, 'Tolerances', grid=(row, 0))
    self.tolerancesSpinBoxes1 = DoubleSpinbox(self.mainWidget, value=0.030, decimals=3, grid=(row, 1))
    row += 1
    self.tolerancesSpinBoxes2 = DoubleSpinbox(self.mainWidget, value=0.030, decimals=3, grid=(row, 1))
    row += 1
    self.tolerancesSpinBoxes3 = DoubleSpinbox(self.mainWidget, value=0.300, decimals=3, grid=(row, 1))

    # Steps
    row += 1
    self.stepsLabel = Label(self.mainWidget, 'Steps', grid=(row, 0))
    self.stepsSpinBox = Spinbox(self.mainWidget, value=1e5, max=1e10, grid=(row, 1))

    # Assignments
    row += 1
    self.assignmentsLabel = Label(self.mainWidget, 'ReAssign Peaks', grid=(row, 0))
    self.modeButtons = RadioButtons(self.mainWidget, texts=['Yes', 'No'], grid=(row, 1))

    # Notes
    row += 1
    self.notesLabel = Label(self.mainWidget, 'Notes', grid=(row, 0))
    self.notes = LineEdit(self.mainWidget,  grid=(row, 1))

    # Buttons

    row += 1
    self.buttons = ButtonList(self.mainWidget, texts=['Run'], callbacks=[self._run], grid=(row, 1))



  # def _checkYariaPath(self):
  #   self.YariaPath = self.userPluginPath+'Yaria/'
  #   if not os.path.exists(self.YariaPath):
  #     os.makedirs(self.YariaPath)

  def _run(self):
    pids = self.treeView.getSelectedObjectsPids()
    try:
      self.project.exportNef(str(self.YariaPath+self.runNameLineEdit.get()), pidList=pids)
      self.plugin.run(**self.widgetsState)
    except Exception as e:
      showWarning(message=str(e), title='Error')

  def _manageWidgets(self):
    pass



  def _restrictChemicalShiftListSelection(self, item):
    '''Restrict selection of one chemical shift list per Calculation. Remove this when Yaria can handle multiple CSL '''
    from ccpn.core.ChemicalShiftList import ChemicalShiftList
    if item:
      if item.parent():
        if item.parent().text(0) == str(ChemicalShiftList._pluralLinkName):
          for itemTree in self.treeView.findItems(str(ChemicalShiftList._pluralLinkName),
                                              QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
            for i in range(itemTree.childCount()):
              if itemTree.child(i) != item:
                itemTree.child(i).setCheckState(0, QtCore.Qt.Unchecked)



class YariaPlugin(Plugin):
  PLUGINNAME = 'Yaria'
  guiModule = YariaGuiPlugin

  def run(self, **kwargs):
    ''' Insert here the script for running Yaria '''
    print('Running Yaria', kwargs)




YariaPlugin.register() # Registers the pipe in the pluginList