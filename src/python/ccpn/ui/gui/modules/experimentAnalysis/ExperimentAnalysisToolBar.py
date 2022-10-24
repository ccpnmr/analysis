#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-10-24 17:06:24 +0100 (Mon, October 24, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtWidgets
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.util.DataEnum import DataEnum


class PanelUpdateState(DataEnum):
    """
    updateState = 0 # status: done, no need to update. icon Green
    updateState = 1 # status: to be done, on the queue and need to update. icon Orange
    updateState = 2 # status: suspended, Might be updates. icon red
    """

    DONE        = 0, 'icons/update_done'
    DETECTED    = 1, 'icons/update_detected'
    SUSPENDED   = 2, 'icons/update_suspended'


class ToolBarPanel(GuiPanel):
    """
    A GuiPanel containing the ToolBar Widgets for the Experimental Analysis Module
    """

    position = 0
    panelName = guiNameSpaces.ToolbarPanel
    toolButtons = {}

    updateRequested = QtCore.pyqtSignal(object)

    updateState = 0

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, *args , **Framekwargs)
        self.setMaximumHeight(100)
        self._updateState = PanelUpdateState.DONE

    def initWidgets(self):

        toolButtonsDefs = {
            guiNameSpaces.FilterButton: {
                'text': '',
                'icon': 'icons/filter',
                'tipText': 'Apply filters as defined in settings',
                'toggle': True,
                'callback': f'_{guiNameSpaces.FilterButton}{guiNameSpaces.Callback}',  # the exact name as the function def
                'objectName': guiNameSpaces.FilterButton,
                'enabled': False,
            },

            guiNameSpaces.UpdateButton: {
                'text': '',
                'icon': 'icons/update',
                'tipText': 'Update all data and GUI',
                'toggle': None,
                'callback': f'_{guiNameSpaces.UpdateButton}{guiNameSpaces.Callback}',
                'objectName': guiNameSpaces.UpdateButton,
            },
            guiNameSpaces.ShowStructureButton: {
                'text': '',
                'icon': 'icons/showStructure',
                'tipText': 'Show on Molecular Viewer',
                'toggle': None,
                'callback': f'_{guiNameSpaces.ShowStructureButton}{guiNameSpaces.Callback}',
                'objectName':guiNameSpaces.ShowStructureButton,
                'enabled': True,
            }}

        colPos = 0
        for i, buttonName in enumerate(toolButtonsDefs, start=1):
            colPos+=i
            callbackAtt = toolButtonsDefs.get(buttonName).pop('callback')
            button = Button(self, **toolButtonsDefs.get(buttonName), grid=(0, colPos))
            callback = getattr(self, callbackAtt or '', None)
            button.setCallback(callback)
            button.setMaximumHeight(25)
            button.setMaximumWidth(25)
            setattr(self, buttonName, button)
            self.toolButtons.update({buttonName:button})

        self.getLayout().setAlignment(QtCore.Qt.AlignLeft)

    def getButton(self, name):
        return self.toolButtons.get(name)

    def _filterButtonCallback(self):
        getLogger().warn('Not implemented. Clicked _filterButtonCallback')

    def _updateButtonCallback(self):
        """ Update all panels."""
        self.guiModule.updateAll()

    def _showStructureButtonCallback(self):
        from ccpn.ui.gui.modules.PyMolUtil import _CSMSelection2PyMolFileNew
        import subprocess
        import os
        from ccpn.util.Path import aPath, fetchDir
        from ccpn.ui.gui.widgets.MessageDialog import showOkCancelWarning, showWarning
        scriptsPath = self.application.scriptsPath
        pymolScriptsPath = fetchDir(scriptsPath, guiNameSpaces.PYMOL)
        settingsDict = self.guiModule.settingsPanelHandler.getAllSettings().get(guiNameSpaces.Label_GeneralAppearance,
                                                                                {})
        barPanel = self.guiModule.panelHandler.getPanel(guiNameSpaces.BarPlotPanel)
        barGraph = barPanel.barGraphWidget
        moleculeFilePath = settingsDict.get(guiNameSpaces.WidgetVarName_MolStructureFile, '')
        moleculeFilePath = aPath(moleculeFilePath)
        pymolScriptsPath = aPath(pymolScriptsPath)
        scriptFilePath = pymolScriptsPath.joinpath(guiNameSpaces.PymolScriptName)

        pymolPath = self.application.preferences.externalPrograms.pymol
        moleculeFilePath.assureSuffix('.pdb')
        if not os.path.exists(moleculeFilePath):
            ok = showWarning('Molecular file not Set',
                             f'Provide a {guiNameSpaces.Label_MolStructureFile} on the Settings - Appearance Panel')

        if not os.path.exists(pymolPath):
            ok = showOkCancelWarning('Molecular Viewer not Set', 'Select the executable file on preferences')
            if ok:
                from ccpn.ui.gui.popups.PreferencesPopup import PreferencesPopup
                pp = PreferencesPopup(parent=self.mainWindow, mainWindow=self.mainWindow)
                pp.tabWidget.setCurrentIndex(pp.tabWidget.count() - 1)
                pp.exec_()
                return

        coloursDict = barGraph.getPlottedColoursDict()
        import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
        # get the match  index-residueCode so that can be mapped to the PDB and pymol
        df = self.guiModule.getGuiResultDataFrame()
        if df is None or df.empty:
            showWarning('No Data available', f'To start calculations, set the input Data from the Settings Panel')
            return
        sequenceCodeColoursDict = {}
        for i, row in df.iterrows():
            num = row[sv.ASHTAG]
            code = row[sv.NMRRESIDUECODE]
            vv = coloursDict.get(num, '')
            sequenceCodeColoursDict[code] = vv
        selection = "+".join([str(x.sequenceCode) for x in self.current.nmrResidues])  # FIXME this is broken
        scriptPath = _CSMSelection2PyMolFileNew(scriptFilePath, moleculeFilePath, sequenceCodeColoursDict, selection)
        try:
            self.pymolProcess = subprocess.Popen(str(pymolPath) + ' -r ' + str(scriptPath),
                                                 shell=True,
                                                 stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE)
        except Exception as e:
            getLogger().warning('Pymol not started. Check executable.', e)

    def getUpdateState(self):
        return self._updateState

    def setUpdateState(self, value):

        dataEnum = None
        if isinstance(value, DataEnum):
            dataEnum = value
        else:
            for i in PanelUpdateState:
                if i.value == value:
                    dataEnum = value

        if dataEnum:
            self._updateState = dataEnum.value
            updateButton = self.getButton(guiNameSpaces.UpdateButton)
            if updateButton:
                iconValue = dataEnum.description
                updateButton.setIcon(Icon(iconValue))


